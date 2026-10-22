---
estado: aceptada
creado: 2026-10-20
---

# ADR-0018 — Dos corredores, un oráculo

## Contexto

La compuerta de la fábrica es una sola: `.\tests\Invoke-Tests.ps1`. Corre los dos motores sobre el mismo
árbol, suma un único exit code y es lo que pide `CLAUDE.md` antes de dar algo por hecho. Es también lo que
hoy más tarda: entre 45 y 70 minutos según la máquina, y quien construye espera esa corrida entera cada vez
que quiere saber si una etapa rompió algo.

La regla de `harness-backend-engineer.md` protegía hasta ahora esa unicidad con una frase corta: no sumar
una tercera forma de correr los tests ni dejar que las dos reporten distinto. Esa frase evita dos riesgos
reales, un comando de cierre ambiguo y una salida que haya que aprender a leer dos veces, pero también
impide un acelerador, que es lo que pide la Task 6.1 (`docs/cambios/verification-pipeline-performance/spec.md`).

Lo que pesa en la decisión:

- **Un runner más rápido es una segunda opinión sobre el mismo árbol, no una segunda compuerta.** Mientras
  nadie haya contrastado, suite por suite y con la misma huella del árbol, que da lo mismo que el oráculo,
  un verde del runner no tiene con qué ganarse el derecho de cerrar un cambio, un veredicto o un release;
- **`correr.py -k` ya es una segunda forma de correr**: el refutador lo usa para una suite por subcadena.
  La regla vieja protegía un comando de cierre y una forma de reporte, y las dos se pueden conservar;
- **un candado entre procesos no coordina todo lo pesado**: el del runner solo ve a otros runners. El
  oráculo, las corridas focales y los lotes de mutaciones no lo toman, y esta Task no ensancha el código
  para que lo tomen.

## Decisión

### 1. `tests/Invoke-Tests.ps1`, sin parámetros, es el único oráculo y la única compuerta

Es lo que cierra un cambio, un veredicto y un release. Su salida y su exit code no cambian por existir un
runner, y `CLAUDE.md`, §«The gate», sigue diciendo lo mismo: un comando, dos motores, un exit code.

### 2. `tests/Invoke-Tests-Parallel.ps1` es un acelerador, y nunca cierra

Corre los mismos archivos de casos con el mismo oráculo, un archivo por proceso, y reporta en las mismas
formas. Sirve para tres usos: el feedback de quien construye, la regresión focal intermedia (después de una
etapa y antes de pedir refutación) y, desde la fase C, el apoyo a quien refuta. Un runner en verde no cierra
un cambio, un veredicto ni un release, ni siquiera cuando es lo único que se corrió.

### 3. `-SoloCaso` es una corrida parcial, y tampoco es la compuerta

`Invoke-Tests.ps1 -SoloCaso <archivo>` corre exactamente un archivo de `tests/casos/` y lo dice en su primera
línea. Es la forma focal y la que usa cada proceso del runner, pero un verde de un solo archivo no es el
verde de la suite.

### 4. Un `sostenido` que cierra cita el oráculo o `correr.py -k`, nunca el runner

Desde la fase C (§2), quien refuta puede explorar con el runner; antes, no lo usa. En cualquier fase, el
veredicto que cierra se apoya en una corrida del oráculo completo o en `python tests\correr.py -k <suite>`
sobre la suite que corresponde. Un veredicto que cita solo al runner no es evidencia de cierre.

### 5. Promover el runner a compuerta pide un ADR nuevo que reemplace a este

No se promueve con una nota de versión, con un cambio de `CLAUDE.md` ni por costumbre. La condición es un
ADR propio, con refutación y con la aprobación de una persona, después de las fases B a D de la migración de
la spec: que el runner haya acumulado pares con el oráculo sobre más de una Task y más de un árbol, sin
discrepancias sin explicar, y que la deriva de las suites que hoy no son deterministas esté resuelta o
contemplada. Hasta entonces, este ADR rige.

### 6. El candado `pesada.lock` excluye runner contra runner, y nada más

El candado del sistema operativo sobre `%LOCALAPPDATA%\gcba-harness\recursos\pesada.lock` garantiza que de
dos runners paralelos, corre uno. No garantiza nada frente al oráculo, las corridas focales, los lotes de
mutaciones ni ningún proceso externo: no lo ven. Esa limitación es conocida y se cubre con **una regla
operativa del workflow, no del código**: mientras corre un trabajo pesado de cierre, quien orquesta no lanza
otro que compita por CPU, RAM o disco, y el que cierra corre solo. Son trabajos pesados el oráculo
completo, el runner, un lote grande de mutaciones y el benchmark; lo focal no cuenta. La coordinación técnica
más amplia queda como deuda registrada.

### 7. El manifest es una obligación de quien agrega un caso

La clase de cada archivo de `tests/casos/` vive en `tests/parallel-manifest.json`. Quien agrega un archivo a
`tests/casos/` agrega su línea en el manifest: una suite sin entrada corre como `serial`, y la suite de la
propia Task 6.1 se pone roja por la entrada que falta. La clase no se infiere del nombre.

## Consecuencias

A favor:

- El comando que cierra no cambia ni de nombre ni de salida: quien ya lo usa sigue igual, y la regla de
  `harness-backend-engineer.md` se conserva en lo que protegía, un solo comando de cierre y una sola forma de
  reporte, que son los cinco verbos de aserción de siempre.
- El builder y la regresión intermedia dejan de esperar una corrida entera, sin que un verde sin contrastar
  pueda cerrar nada.
- La frontera entre acelerador y compuerta queda escrita antes de que exista el código del runner, y el
  camino para cruzarla también.
- Lo que el candado no cubre se dice en lugar de dejarse como propiedad implícita.

En contra, y dicho:

- **Hay dos corredores que mantener**, y uno puede divergir del otro: lo contiene que cada proceso del runner
  es el oráculo filtrado, y que un par medido sobre la misma huella lo compara suite por suite.
- **Un builder puede confundir el verde del runner con el de la compuerta.** Esta decisión y la enmienda del
  agente lo escriben, pero depende de que se lea; el punto 4 es lo que lo contiene en la refutación.
- **La regla operativa del punto 6 no la hace cumplir ningún código.** Dos trabajos pesados lanzados a la vez
  por alguien que no la conoce compiten sin aviso, y los tiempos medidos se contaminan.
- **El manifest es una obligación nueva para todo builder futuro**: olvidarla pone roja la suite de la Task
  6.1, y es a propósito, pero es un costo que antes no existía.
- **El runner suma una pieza de infraestructura de tests** con su propio manifest, candado, barrido de
  temporales y comparador, y cada una necesita su evidencia.

## Alternativas descartadas

- **El runner como compuerta desde el principio**: sin pares acumulados, un verde que nadie contrastó
  cerraría cambios. Es la fase D.
- **Construir el runner sin enmendar la regla del agente**: viola por omisión un contrato escrito.
- **Un modo del oráculo, `Invoke-Tests.ps1 -Paralelo`**: mete el acelerador en el camino de la compuerta y
  vuelve más riesgoso cada cambio del runner.
- **Un candado en el oráculo**: le agregaría un exit nuevo a la compuerta, y cambiar su salida es lo que este
  ADR evita.

## Revisión

Este ADR no edita ninguno de los anteriores. Se revisa cuando se cumplan las condiciones de promoción del
punto 5, y entonces lo reemplaza un ADR nuevo, no una enmienda; o si aparece un uso del runner que cierre algo
sin pasar por el oráculo, que es la contradicción que pide un ADR antes que un parche.
