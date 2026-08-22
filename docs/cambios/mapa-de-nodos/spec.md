# El mapa de nodos del código

**Estado:** especificado · **Fecha:** 2026-08-22

`dev-iniciador-code` recorre el código y escribe una ficha por módulo. Cada ficha describe sus
dependencias en prosa y **no enlaza a ninguna**. Este cambio convierte esas menciones en aristas,
y dibuja el grafo que forman.

## Qué problema resuelve

La carpeta del índice existe por una razón medible: que la sesión lea una línea y después una
ficha, en vez de grepear el repo entero. Esa promesa se corta en la primera dependencia. Hoy el
agente abre `install.md`, lee *"depende de los checks"* y tiene que salir a buscar dónde están los
checks — que es exactamente el trabajo que la ficha venía a evitar. Lo pagó igual, una ficha más
tarde.

El número: en las **13 fichas** de este repo hay **cero** enlaces entre fichas. Los únicos 13
enlaces del directorio están en `indice.md`. El grafo está descrito y no está tejido.

La segunda mitad es que nadie puede *ver* la forma del código. Un índice de trece líneas dice qué
hay; no dice qué depende de qué, ni cuál es el módulo del que cuelga todo, ni cuál no usa nadie.
Esa pregunta se contesta con un dibujo o no se contesta.

Las dos herramientas que resolvían esto están descartadas, y por motivos que no cambiaron:
graphify por decisión del 2026-08-21, `codebase-memory-mcp` por un binario sin firma Authenticode
que Defender marca — y pip no lo destraba, porque el paquete de PyPI es un descargador de 0,01 MB
del mismo binario. El mapa se hace acá adentro o no se hace.

## Qué queda afuera

- **Los `[[wikilink]]`.** GitHub no los renderiza: los muestra con los corchetes, como texto. La
  documentación se lee en el navegador, y un enlace que solo funciona adentro de un programa que
  hay que instalar es peor que el que ya teníamos. El enlace relativo funciona en los tres lados:
  GitHub, el editor y —sin pedirlo— la vista de grafo de Obsidian.
- **Nodos por función o por símbolo.** Eso es lo que hacían las herramientas bloqueadas. Acá el
  nodo es la ficha, y la ficha es el módulo. Bajar de granularidad exige parsear el código, y
  parsear el código es un tree-sitter que no tenemos dónde instalar.
- **Cualquier herramienta externa, binario o MCP.** ADR-0008, las tres condiciones.
- **Cualquier librería JS, fuente o recurso de un CDN.** El `mapa.html` de un proyecto es un
  archivo local que se abre con doble clic, a veces sin red y casi siempre en una máquina donde no
  se instala nada. Se distingue de `docs/mapa/*.html`, que son de la fábrica y se publican.
- **Interactividad más allá de recorrer y leer.** Sin filtros, sin buscador, sin agrupar por
  carpeta. 🔴 **Esta exclusión se abrió el 2026-08-22**, por su propia cláusula —*"se agrega cuando
  alguien lo pida sobre un mapa que ya exista"*—: el mapa existía y Nahue lo pidió. Entró lo que se
  pidió y nada más: desplazar, acercar, arrastrar un nodo y abrir su ficha en un panel.
- **Guardar el acomodo.** Un archivo local no escribe en disco: si arrastrás un nodo, al recargar
  vuelve donde lo puso el script. Se evaluó un botón que copiara las posiciones para pegarlas en un
  `posiciones.json` que el generador leyera como semilla. Queda afuera: es un contrato nuevo y un
  paso manual, y un botón que promete guardar y no guarda es peor que no tenerlo.
- **Tocar el aviso de `SessionStart`.** Ya avisa por `indice.md` y eso alcanza para disparar el
  recorrido. Un segundo aviso por el mapa es el ruido que 0.14.0 sacó a propósito.
- **Extender `install.ps1` para copiar `bin` de los harness.** El motivo está abajo.
- **Un corte por tamaño.** Trece nodos se dibujan. Trescientos no se van a leer, y este cambio no
  define qué hacer con eso: se anota como riesgo, no se resuelve de prepo.

## Las decisiones, y por qué

### El enlace es markdown relativo

`[checks](checks.md)`, no `[[checks]]`. Funciona donde se lee la documentación —GitHub— y donde la
lee el agente, y la vista de grafo de Obsidian se arma igual con enlaces markdown comunes. El
wikilink cambiaría un enlace que sirve en todos lados por uno que sirve en uno solo, a cambio de
nada que no tengamos ya.

### El dibujo lo hace un script, no el agente

Un modelo escribiendo coordenadas de SVG es caro, no es reproducible, y cada regeneración produce
un diff distinto sobre un archivo que nadie va a leer en el diff. Un script determinista da el
mismo byte para las mismas fichas: cuando el mapa cambia, cambió el código.

El agente ya tiene el trabajo que solo él puede hacer —decidir qué es un módulo y qué depende de
qué—. Dibujar no es de esa familia.

### El generador vive en `comun/bin/`

Lo natural sería `harnesses/desarrollo/bin/`, porque el recorrido es del harness de desarrollo. No
se puede sin tocar el instalador: `install.ps1:1099` copia `bin` **solo** de `comun`, con la ruta
escrita a mano, y los manifiestos de los harness no declaran `bin`. Generalizar eso es un cambio al
contrato del manifiesto y al instalador para mover un archivo de lugar.

Se acepta el costo de que un proyecto de análisis se lleve un script que nunca va a correr —un
archivo de texto que nadie invoca— y se anota: **cuando aparezca la segunda herramienta propia de
un harness, ahí se generaliza `aporta.bin`.** Una sola no lo paga.

### El nodo es la ficha, y la arista es el enlace

No hay una segunda fuente de verdad. El grafo no infiere, no lee código y no deduce: dibuja
exactamente lo que las fichas dicen. Si una arista falta en el dibujo es porque falta en la ficha,
y se arregla en la ficha. Un generador que dedujera aristas por su cuenta pondría en el mapa cosas
que ninguna ficha afirma, y nadie sabría cuál de los dos está mal.

### El layout es determinista y sin librerías

Posiciones calculadas por el script, SVG en línea, sin azar. Un grafo que se acomoda distinto en
cada corrida convierte cada regeneración en un diff de mil líneas y esconde el cambio real adentro
del ruido.

### La página se recorre, y por eso lleva un script propio en línea

Un grafo de trece nodos entra en una pantalla; uno de ochenta, no. Desplazar y acercar es lo que
hace que el mapa siga sirviendo cuando el proyecto crece, y abrir la ficha desde el nodo es lo que
lo convierte en la puerta al índice en vez de una ilustración al costado.

Eso obliga a mover E-09, y conviene decirlo derecho: **el escenario prohibía `<script`, que es más
estricto que su propia intención.** Lo que no puede haber es un recurso **externo** —una librería,
una fuente, un archivo aparte—, porque la página se abre desde `file://`, a veces sin red y casi
siempre en una máquina donde no se instala nada. Un script en línea no sale a buscar nada. E-09
pasa a prohibir `http://`, `https://` y cualquier `src=`, que es lo que siempre quiso decir.

Por el mismo motivo **el texto de cada ficha va embebido en la página**. No es una preferencia: en
`file://` un `fetch` lo bloquea CORS, así que un panel que fuera a buscar el `.md` al disco no
mostraría nada. Son 42,8 KB de fichas y la página pasa de 10 KB a 75 KB.

Y el nodo va adentro de un `<a href>` que apunta a su ficha. Si el script no corre, el clic lleva
igual a algún lado: el panel es mejor, pero no puede ser la única puerta. Una página que sin
JavaScript no hace nada está rota, no degradada.

### El markdown de la ficha lo renderiza el generador, no el navegador

Para llenar el panel hay que convertir la ficha a HTML, y traer una librería para eso sería
exactamente el requisito externo que ADR-0008 no deja agregar. Se escribe el subconjunto que las
fichas usan —cuatro títulos, listas, negrita, código y enlaces—, que es acotado justamente porque
`dev-codebase-forma` garantiza la forma de la ficha.

Se escapa **antes** de armar el marcado. La ficha la escribe un modelo mirando código ajeno: un
`<script>` copiado de un archivo del proyecto no puede terminar ejecutándose al abrir el mapa.

### El check de enlaces se suma al que ya existe

`dev-codebase-forma.py` ya tiene la regex `ENLACE`, ya lista las fichas del disco y ya verifica el
ida y vuelta del índice. Le falta una función. Un check nuevo duplicaría las tres cosas para
agregar una comparación.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/agents/dev-iniciador-code.md` | Regla de escritura: en `Qué expone` y `De qué depende`, todo módulo con ficha propia va enlazado. Paso nuevo del procedimiento: regenerar el mapa, después del índice |
| `harnesses/desarrollo/checks/dev-codebase-forma.py` | Se le suma `_revisar_enlaces`: un enlace de una ficha a un `.md` que no existe es un hallazgo |
| `comun/bin/mapa-codigo.py` | Lee las fichas, extrae las aristas de los enlaces, escribe `mapa.html`. Solo biblioteca estándar |
| `<rutaCodebase>/mapa.html` | El grafo, con el texto de las fichas adentro. Se recorre, se acerca y se lee sin salir de la página. Generado, versionado, se regenera entero |
| `tests/casos/` | Los casos de los escenarios que van por suite |
| `docs/codebase/` de este repo | Las 13 fichas regeneradas con sus enlaces, y su `mapa.html` |

## Escenarios verificables

### Los enlaces entre fichas

- **E-01** — En una ficha escrita por `dev-iniciador-code`, todo módulo del proyecto nombrado en
  `Qué expone` o `De qué depende` que tenga ficha propia aparece como enlace relativo a esa ficha.
  · verificación: lectura · rojo visto: no consta
- **E-02** — Una dependencia que no tiene ficha —Python, `git`, una librería externa— se nombra sin
  enlace, y eso no produce ningún hallazgo. · rojo visto: si
- **E-03** — Ninguna ficha usa un `[[wikilink]]` fuera de un span de código.
  · rojo visto: si
- **E-03b** — Un `[[...]]` adentro de comillas invertidas o de un bloque cercado es
  documentación sobre wikilinks, no un wikilink: no produce hallazgo. · rojo visto: si

### El check

- **E-04** — Un enlace de una ficha a un `.md` que no existe en el directorio produce un hallazgo
  que nombra la ficha de origen y el destino roto. · rojo visto: si
- **E-05** — Ese hallazgo no bloquea: el archivo queda escrito en disco y el hook sale con código 0.
  · rojo visto: si
- **E-06** — Un enlace de una ficha a `indice.md` no produce hallazgo. · rojo visto: si
- **E-07** — Una escritura de `.md` fuera del directorio de fichas no produce ninguno de estos
  hallazgos. · rojo visto: si

### El generador

- **E-08** — Dos corridas sobre las mismas fichas producen dos `mapa.html` byte a byte idénticos.
  · rojo visto: si
- **E-09** — `mapa.html` no referencia ningún recurso externo: no contiene `http://`, `https://`
  ni ningún atributo `src=`. El script propio va en línea. · rojo visto: si
- **E-10** — El HTML tiene exactamente un nodo por ficha del directorio, sin contar `indice.md`.
  · rojo visto: si
- **E-11** — Dos enlaces de la ficha A a la ficha B producen una sola arista. · rojo visto: si
- **E-12** — Una ficha que ninguna otra enlaza queda marcada como huérfana en el dibujo.
  · rojo visto: si
- **E-13** — Un ciclo A→B→A se dibuja y el generador termina. · rojo visto: si
- **E-14** — Con el directorio vacío o sin fichas no escribe `mapa.html`, y lo dice por stdout.
  · rojo visto: si
- **E-15** — El generador no abre ningún archivo fuera del directorio de fichas. · rojo visto: si
- **E-16** — El generador no escribe ningún archivo que no sea `<rutaCodebase>/mapa.html`.
  · rojo visto: si
- **E-17** — Corre con Python 3.9 sin instalar nada: solo biblioteca estándar. · rojo visto: si

### El panel y lo que se recorre

- **E-21** — El HTML trae el texto de cada ficha embebido: un `<article class="ficha">` por nodo, y
  ninguno para `indice.md`. · rojo visto: si
- **E-22** — Cada nodo está adentro de un `<a href>` que apunta a su ficha, así el clic lleva a algún
  lado aunque el script no corra. · rojo visto: si
- **E-23** — El texto de una ficha sale escapado: un `<script>` escrito adentro de una ficha aparece
  como texto y no se ejecuta. · rojo visto: si
- **E-24** — Un enlace a una ficha hermana se marca para abrirse en el panel; uno con ruta —un ADR,
  una spec— queda como enlace común y sale de la página. · rojo visto: si

- **E-25** — El mapa no atrapa el desplazamiento de la página: la rueda sola la desplaza, el zoom
  pide Ctrl, y hay botones para acercar y alejar sin atajo. · rojo visto: si
- **E-26** — El script no captura el puntero en el `<svg>` —eso desviaría el `click` del nodo al
  lienzo— y el arrastre se anula al soltar, incluso si el `pointerup` se perdió. · rojo visto: si

### El recorrido

- **E-18** — Terminado un recorrido completo, el directorio tiene fichas, `indice.md` y `mapa.html`.
  · verificación: lectura · rojo visto: no consta
- **E-19** — El mapa se regenera después del índice, no antes. · verificación: lectura
  · rojo visto: no consta
- **E-20** — El reporte del recorrido dice cuántos nodos y cuántas aristas quedaron, y nombra las
  fichas huérfanas. · verificación: lectura · rojo visto: no consta

## Cómo se verifica

| Escenarios | Cómo | Por qué |
|---|---|---|
| E-02 a E-17, E-21 a E-24 | Suite | Son deterministas: entran fichas de fixture, sale un hallazgo o sale un archivo. No hay modelo en el medio |
| E-25, E-26 | Suite, sobre la **forma** del script | Ningún test abre un navegador, así que no se puede verificar el comportamiento. Lo que se sostiene es que las dos defensas sigan escritas: son las que arreglaron los dos bugs que aparecieron al abrir el mapa por primera vez, y las dos son fáciles de borrar sin querer al simplificar un handler |
| E-01, E-18, E-19, E-20 | Lectura, ADR-0009 | El sujeto es una corrida de `dev-iniciador-code`. Ningún test puede obligar a un modelo a enlazar; lo que sí se puede es correr el recorrido sobre un repo real y que alguien que no lo construyó lea el resultado, con fecha y nombre |

🔴 Los de lectura son **cuatro**, y se cuentan aparte de los `sostenido`. Es la parte más débil de
esta verificación y conviene que se vea: lo que el agente escribe se comprueba mirando.

## Riesgos conocidos

- **El check ve enlaces rotos, no aristas faltantes.** Si el agente omite una dependencia, el mapa
  sale prolijo y con menos aristas de las reales. Un grafo incompleto miente mejor que un texto
  incompleto, porque parece exhaustivo. La única defensa es E-20 —el reporte declara los números— y
  es una declaración, no una medición.
- **`mapa.html` es generado y versionado.** El determinismo hace que el diff sea legible cuando
  cambia una arista, pero cualquier cambio del layout mueve el archivo entero de una vez.
- **Escala.** Trece nodos se leen. Trescientos son una nube. No hay corte definido, y el primer
  proyecto grande lo va a encontrar antes que nosotros.
- **Envejecimiento.** Si nadie vuelve a correr el recorrido, el mapa envejece con el código. No es
  un riesgo nuevo: es el de la ficha, dibujado.
- 🔴 **Ningún test abre un navegador, y ya cobró.** Lo verificado del panel y del arrastre es la
  **estructura**: que el `<article>` esté, que el nodo sea un enlace, que el texto salga escapado.
  Que el clic realmente abra el panel y que la rueda realmente acerque no lo comprueba nada. El
  2026-08-22, con los 49 casos en verde, la primera persona que abrió el archivo encontró dos bugs
  en menos de un minuto: el mapa atrapaba la rueda y no soltaba el arrastre, y el clic sobre un
  nodo no abría nada porque `setPointerCapture` desviaba el evento al lienzo. E-25 y E-26 fijan
  las dos defensas, pero **fijan el código, no la conducta**: el siguiente bug de esta familia se
  va a encontrar igual, abriendo el archivo. Y no
  puede tomar la marca `leído`: ADR-0009 es explícito en que esa marca es solo para un escenario
  cuyo sujeto es una corrida de un **modelo**, y un navegador no lo es. Queda como un agujero
  declarado, no como un escenario disfrazado de verificado.
- **La página pesa siete veces más.** De 10 KB a 75 KB, por las fichas embebidas. En un proyecto
  con cien módulos eso escala lineal y nadie midió dónde molesta.
- **El texto de la ficha queda en dos lados.** El `.md` y la copia adentro del mapa. No se
  desincronizan mientras el mapa se regenere en el mismo recorrido que escribe las fichas, que es
  lo que dice el procedimiento del agente — pero si alguien edita una ficha a mano y no regenera,
  el panel muestra lo viejo con la misma cara de siempre.
- **El script viaja a proyectos que no lo usan.** Un archivo de texto en `comun/bin/` de un
  proyecto de análisis. Barato hoy; deja de serlo con el segundo.
