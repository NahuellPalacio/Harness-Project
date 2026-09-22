# La normativa de ES0901 §7.1 en el harness

Qué regla del estándar le aplica a una unidad de trabajo, cuál no, y cuál no se puede decidir
todavía.

📌 **Este no es el único estándar.** ES0902 v6.2 —seguridad— se instaló aparte, con sus 21 reglas
propias, sobre este mismo runtime: [seguridad-es0902.md](seguridad-es0902.md). Los dos tienen una
regla `G1` y no son la misma, así que entre estándares la clave es compuesta: `ES0901.G1`,
`ES0902.G1`.

## Cinco palabras que no son sinónimos

| | |
|---|---|
| **Regla normativa** | Una cláusula de §7.1. `G1`, `D8`, `M3`. Su texto es una cita y no se traduce |
| **Policy** | Un contrato de gobierno que la regla exige. Restringe comportamiento **antes** |
| **Check** | Una verificación objetiva del resultado. Comprueba **después** |
| **Review** | Lo que exige criterio humano y no admite un check mecánico |
| **Evidencia** | Con qué señales se decidió que una regla aplicaba |

Una regla puede exigir una policy, un check, las dos o una review. **Inventar un check para que
una regla "cierre" es peor que declarar el hueco**: un `check_buenas_practicas() == true` se lee
igual de autoritativo que uno real y no comprueba nada.

## Dos archivos, dos preguntas

```
reglas/es0901-7.1.json                    26 filas: el TEXTO citado y la pagina, en espanol
reglas/es0901-7.1-normative-matrix.json   24 filas: modo, senales, agentes, policies, checks
```

El primero es la fuente citable. El segundo clasifica. Se unen por id de regla, y la matriz trae
una paráfrasis operativa en inglés que sirve para clasificar y **no** para citar: una cita
traducida deja de ser una cita ([ADR-0011](adr/0011-el-idioma-de-un-archivo-lo-decide-quien-lo-lee.md)).

Son 26 y 24 porque el archivo citable parte `P1` en tres cláusulas y la matriz clasifica la madre;
una cláusula derivada —`P1.node`— hereda su clasificación, y esa herencia vive en un solo lugar.

## Lo que está y lo que falta

La matriz tiene 24 filas y el registro declara **31 controles**. **Once** reglas están completas
—cada control que declaran existe: G1, G2, D1 a D8 y P1— y **trece** siguen con controles declarados
y no construidos: P2 a P7, C1 a C4 y M1 a M3. Ninguna de las 24 declara cero controles.

📌 El número se mueve con cada regla que se instala, así que vale más la forma de recontarlo que el
número: una regla está completa cuando **todos** los ids que declara —policies, checks y reviews—
están en el registro con estado `INSTALLED`.

🔴 **Un id declarado no finge estar implementado.** Lo que la matriz exige y el registro no tiene
se reporta `DECLARED_POLICY_NOT_INSTALLED`, `DECLARED_CHECK_NOT_INSTALLED` o
`DECLARED_REVIEW_NOT_INSTALLED`, y eso **no invalida la matriz**: es el estado correcto de un
harness que clasificó antes de construir. Lo que sí sería un defecto es que el hueco no se vea.

🔴 **Desconocido no es falso.** Una señal ausente deja la regla en `APPLICABILITY_UNRESOLVED`,
nunca en `NOT_APPLICABLE`. Convertir lo que falta en "no aplica" es la forma más barata de que un
plan quede verde: la regla desaparece del reporte y nadie la vuelve a buscar.

## Dos reglas en el mismo párrafo: D5 y D6

El estándar pone dos obligaciones distintas en un mismo tramo de texto, y el harness las separa en
dos reglas porque se incumplen por separado.

D5 pide que las direcciones de calles estén normalizadas y validadas contra la opción catastral
del GCBA. D6 pide que la visualización georreferenciada use el mapa del GCBA. Una aplicación puede
normalizar bien y dibujar sobre un mapa que no corresponde, y al revés. Meterlas en una sola regla
haría que un solo veredicto tapara la mitad que falla.

Se separan además porque sus señales de aplicabilidad son distintas: una mira si hay un campo de
dirección en el frontend, la otra si hay visualización georreferenciada. Un sistema puede tener una
sin la otra, y entonces una de las dos reglas **no aplica** mientras la otra sí.

🔴 Lo que comparten es lo que el harness **no** sabe. Ninguna de las dos trae el nombre del
proveedor, ni la forma de invocarlo, ni los campos que devuelve. Eso no está en §7.1 y no se
inventa: se declara el hueco con su estado y se espera evidencia del proyecto.

## La cadena que D5 verifica, y por qué no es la llamada

El defecto que D5 busca no es que falte la invocación al servicio. Es que la invocación ocurra y
el sistema guarde igual lo que escribió la persona.

Por eso lo que se verifica es una **cadena de cinco etapas**, comparadas por identidad y no por
contenido:

```
RAW_INPUT  ->  PROVIDER_REQUEST  ->  PROVIDER_RESPONSE  ->  NORMALIZED_RESULT  ->  CONSUMED_VALUE
```

Cada etapa lleva un token opaco. El harness nunca mira una dirección: sólo compara si el valor que
terminó consumido es el mismo token que el crudo o el mismo que el normalizado. Si el consumido es
el crudo, la cadena se recorrió para nada. Si el crudo y el normalizado son el mismo token, la
cadena no discrimina y no prueba nada, así que tampoco alcanza.

Y la cobertura tiene que ser completa: los cinco tipos de camino por los que una dirección entra
—búsqueda, carga manual, selección, edición y entrada alternativa— están todos declarados, o el
resultado queda sin resolver. **El silencio no es ausencia.**

## El alcance de una señal, desde D5

Una señal no dice sólo qué vale: dice **para qué alcance de orquestación** se produjo. Proyecto,
unidad de trabajo o tarea.

Una señal producida para una tarea no decide la aplicabilidad de un proyecto entero, y una
producida para un proyecto no describe necesariamente lo que hace una tarea. El alcance viaja con
la señal, se conserva en su resolución y llega al plan.

🔴 Lo trajo la refutación de D5, y el defecto era de los que no se ven: el campo existía en el
documento de señal y **desaparecía en la resolución**. El mecanismo quedaba estricto donde el dato
no podía cumplir —una señal malformada se rechazaba— y laxo donde no se había declarado nada —una
señal sin alcance pasaba—. Toda corrida real salía sin alcance declarado y nadie se enteraba.

## El mecanismo que el harness no sabe

Hay una familia entera de cosas que §7.1 **obliga** y no **especifica**: cuál es el proveedor, cómo
se lo invoca, qué devuelve, con qué se autentica, qué pasa si no responde.

El harness no las inventa. Cuando la evidencia no está, la regla queda con un estado que lo dice
—`..._PROVIDER_UNRESOLVED`, `..._CONTRACT_MISSING`— y ahí se queda hasta que llegue evidencia del
proyecto.

🔴 **La razón no es pudor, es que un dato inventado se lee igual de autoritativo que uno real.** Un
nombre de servicio escrito en una policy viaja a un plan, de ahí a una tarea y de ahí a una
implementación, y en ningún tramo del camino queda dicho que alguien se lo imaginó.

Por eso los artefactos de cada regla —la policy, el check, la fila de la matriz, el registro y esta
documentación— se barren buscando el mecanismo, y el barrido incluye **el resultado que el check
produce**, que es lo que efectivamente viaja. Un artefacto limpio y un resultado que filtra serían
lo mismo que no tener el invariante.

## Tres obligaciones en una oración: D7

D7 dice tres cosas distintas en una sola oración del estándar, y el harness las trata como tres
obligaciones porque se incumplen por separado y se remedian por separado:

```
1. el almacenamiento de archivos usa el servicio estandar del GCBA
2. no se guardan archivos de forma persistente en el disco local de la aplicacion
3. los archivos temporales se destruyen apenas se dejan de usar
```

Un sistema puede usar el servicio correcto y aun así dejar temporales tirados. Puede destruir sus
temporales y guardar lo persistente donde no corresponde. Y puede hacer las dos bien y no usar el
servicio del GCBA. Son tres controles, tres policies y tres checks, y por eso el registro los
declara por separado.

Los tres comparten un módulo de flujos: qué archivo entra, dónde se escribe, quién lo lee y cuándo
se borra. Compartir el recorrido evita tres implementaciones que se desincronizan; compartir el
veredicto haría que un incumplimiento tapara a los otros dos.

### Lo que D7 sabe, y lo que no

Lo único de tecnología que el estándar da es el protocolo: el servicio estándar habla S3. Eso está
en §7.1 y por eso está acá; borrarlo para que el barrido pase sería perder la única evidencia
técnica que la regla tiene.

Lo que no da: cuál es el servicio concreto, cómo se lo direcciona, con qué credencial y bajo qué
nomenclatura. Nada de eso está en §7.1. El harness declara la obligación y el hueco, y no escribe
una configuración que nadie le dio. Que el protocolo esté nombrado no autoriza a deducir el
proveedor: hablar S3 no dice quién lo implementa.

### El límite, dicho

Para decidir si una regla aplica, **el harness confía en la etiqueta de la fuente**. Una evidencia
declarada como contexto de tarea vale como contexto de tarea; nadie comprueba que quien la escribió
tuviera derecho a escribirla, ni que el contenido corresponda a la etiqueta.

Es una decisión y no un olvido: la alternativa —que el harness valide la procedencia de cada
evidencia— exige una autoridad que hoy no existe. Queda anotado acá, y no **sólo para D5**: la
misma confianza sostiene la aplicabilidad de todas las reglas condicionales del estándar.

### Lo que se destruye, y cuándo

"Apenas se dejan de usar" no es un plazo y el harness no lo convierte en uno. Lo que se verifica es
que exista una destrucción atada al fin del uso, no que ocurra dentro de una ventana que el
estándar no da. Poner un número ahí sería escribir normativa.

## El binding sale de la matriz: D8

D8 pide que los servicios estén protegidos. Lo que el harness verifica no es cómo se los protege
—eso es un mecanismo y §7.1 no lo especifica— sino que **la protección esté atada al servicio que
la regla gobierna**, y que esa atadura salga de la matriz normativa y no de una lista escrita al
costado.

### Por qué el binding, y no el mecanismo

Un sistema puede tener una protección impecable puesta sobre otra cosa. Verificar que "hay
protección" sin verificar **sobre qué**, deja pasar exactamente el caso que importa: el servicio
gobernado quedó descubierto y el reporte salió verde porque el vecino estaba cubierto.

Por eso la pregunta que se contesta es la de identidad: el servicio que la unidad declara y el
servicio que la protección declara cubrir, ¿son el mismo? Se comparan como identificadores opacos.
El harness no abre ninguno de los dos.

### La señal es de D8 y de nadie más

Ninguna otra señal la sustituye. Con cualquier otra en verdadero, D8 sigue sin resolver y dice por
qué: llegó una señal que no es la suya. Eso parece obvio y no lo es —un check que acepta "alguna
señal encendida" convierte catorce reglas en una—, así que está fijado contra **todas** las demás
señales declaradas, no contra una elegida a mano.

### Lo que D8 no sabe, y no escribe

No sabe qué tecnología de protección se usa, ni cómo se transporta la credencial, ni qué nombres
llevan los permisos, ni cuánto duran, ni qué contesta el servicio cuando la protección falla. Nada
de eso está en el estándar.

🔴 Y no lo escribe en ningún lado: ni en la policy, ni en el check, ni en la fila de la matriz, ni
en el registro, ni acá. El barrido cubre los cinco artefactos **y** el resultado del check en todos
sus caminos, porque un artefacto limpio con un resultado que filtra no es un invariante, es una
formalidad.

### Lo que sí queda dicho

Que la obligación existe, sobre qué servicio, con qué señal se decidió que aplicaba, y qué falta
para poder decidirlo. Con eso alcanza para que alguien del proyecto traiga la evidencia; sin eso,
el harness estaría adivinando por él.

## Una regla, tres cláusulas y ninguna señal: P1

P1 trae tres cláusulas en una sola regla, y el archivo citable las parte en tres filas mientras la
matriz clasifica la madre:

```
P1        se usan los frameworks homologados
P1.vanilla   no se desarrolla sin framework
P1.node      el gestor de paquetes de Node es el que el GCBA homologa
```

La herencia vive en un solo lugar —quien pide `P1.node` recibe la clasificación de `P1` con la
marca de dónde la heredó— y nadie más mira el punto del nombre.

### Aplica siempre, y por eso no tiene señal

P1 es `ALWAYS`. No hay una señal que la encienda porque no hay sistema al que no le aplique: todo
desarrollo usa alguna tecnología, y el estándar no admite "este proyecto no tiene framework" como
excepción —no tenerlo es justamente lo que la segunda cláusula prohíbe—.

Eso la distingue de las condicionales: no puede quedar `APPLICABILITY_UNRESOLVED` por falta de
señal. Lo que sí puede quedar sin resolver es su **resultado**, cuando falta la evidencia de qué
tecnología se está usando.

### El catálogo no vive acá

Qué frameworks están homologados, y hasta dónde, es el Anexo II. Es un dato que cambia sin que
cambie el estándar, y por eso vive en su propio archivo y se consulta; no se copia adentro de la
regla ni de esta documentación.

🔴 **Ni un nombre ni un número.** Ningún artefacto de P1 —las policies, los checks, el registro, la
fila de la matriz y este texto— nombra una tecnología concreta ni un rango homologado. El día que
el Anexo II cambie, lo único que tiene que cambiar es el Anexo II. Un nombre escrito acá sería una
segunda fuente de verdad que nadie recuerda actualizar.

### Comparar no es opinar

Cuando la evidencia está, la comparación es mecánica: lo que el proyecto declara contra lo que el
catálogo homologa. Cuando no está, el resultado dice que falta, y no cae ni en cumple ni en no
cumple. Un catálogo que no se pudo leer tampoco produce un aprobado: sin contra qué comparar, no
hay comparación.

Y la tercera cláusula se mide igual que las otras dos. Cuál es el gestor de paquetes que el GCBA
homologa para Node es un dato del catálogo, no una preferencia del harness: lo que se verifica es
que el proyecto declare cuál usa y que ese sea el homologado. Si el proyecto no lo declara, el
resultado dice que falta esa declaración, no que incumple.

🔴 **Y no se deduce del repositorio.** Que exista un archivo de bloqueo de cierto gestor prueba
que alguien lo corrió alguna vez, no que sea el gestor del proyecto: los tres dejan rastros que
conviven, y elegir uno por el rastro que se encontró primero es adivinar con cara de comprobar.
Lo mismo vale para la segunda cláusula: la ausencia de un framework en un manifiesto no prueba
desarrollo sin framework, prueba que no está en ese manifiesto.

## Dónde mirar

```
reglas/es0901-7.1.json                    el texto citable y la pagina
reglas/es0901-7.1-normative-matrix.json   la clasificacion de las 24
reglas/control-registry.json              que control existe de verdad
reglas/agent-registry.json                que agente existe de verdad

bin/orquestacion/matriz.py       que regla aplica
bin/orquestacion/normativa.py    el bloque normativo que viaja a un plan
bin/orquestacion/senales.py      quien produce el dato que decide la aplicabilidad
bin/orquestacion/controles.py    el registro de controles
bin/orquestacion/revisiones.py   lo que no se puede reducir a un check sin mentir
```

El orden es **registro de agentes → resolución estructural → matriz**. Un agente que la matriz
nombra y el registro no declara es `NORMATIVE_AGENT_REFERENCE_INVALID`: no se crea, no se instala
y no se vuelve existente porque un archivo lo mencione.
