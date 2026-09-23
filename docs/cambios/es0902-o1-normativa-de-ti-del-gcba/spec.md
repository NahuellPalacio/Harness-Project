# ES0902 O1 — la normativa de TI del GCABA como línea base, y la revisión que la mide

**Estado:** verificado y cerrado · **Fecha:** 22-09-2026 · **Regla:** ES0902 6.2 §3 O1

## Qué problema resuelve

O1 es la primera fila de ES0902 y la más ancha de las veintiuna:

> `ES0902-3-O1` — *"Se deben respetar los principios y normativas vigentes de TI del GCABA."*

La fila ya está clasificada desde que se instaló la línea base de ES0902 —`ALWAYS`, cero señales,
`dev-security`, una policy, cero checks, una review— y sus dos controles **no existen**. Hoy el
resultado de O1 sale por el camino genérico de `seguridad.py`, y ese camino tiene un agujero que es
propio de esta regla y de ninguna otra:

```
_generico(O1)  ->  ¿hay hallazgos abiertos que citen O1?      no
                   ¿algún control declarado en FAIL?           no
                   ¿todos con PASS y evidencia?                si  ->  COMPLIANT
```

Dos `controlResults` en `PASS` —uno por la policy, uno por la review— y O1 cumple. Nadie miró qué
normativa de TI del GCABA aplica, si está cargada, ni si sigue vigente. **La regla más ancha del
estándar es la más barata de poner en verde**, y lo que queda escrito es que la solución respeta
los principios y normativas del GCABA.

Y hay tres cosas que hoy el harness no sabe decir:

1. **Qué normativa de TI del GCABA existe.** ES0902 nombra tres resoluciones —177-ASINF-2013,
   239-ASINF/2014 y N° 12/ASINF/17— cuyo contenido el harness no tiene. No hay ningún lugar donde
   diga que las conoce de nombre y no de contenido, así que el que las necesite las va a inventar o
   las va a ignorar, y las dos cosas se leen igual de autoritativas.
2. **Si lo que tiene cargado sigue vigente.** Tiene ES0901 v6.3 y ES0902 v6.2. No tiene cómo saber
   si alguna fue reemplazada, y un estándar reemplazado aplicado como vigente miente sin avisar.
3. **Que O1 se contesta con lo que ya se midió.** ES0901 y ES0902 producen resultados por regla.
   O1 pregunta si se respetan los principios y normativas de TI del GCABA: la respuesta está en
   esos resultados. Volver a correr los controles bajo el nombre de O1 es tener dos respuestas a la
   misma pregunta y que el día que difieran las dos tengan razón.

## Qué queda afuera

- **El contenido de las tres resoluciones.** No se transcribe, no se resume y no se deduce del
  texto de ES0902. Entran con su título, su autoridad y el estado de que no están cargadas. Una
  resolución inventada se lee igual de autoritativa que una real, y esta es exactamente la regla
  donde eso haría más daño.
- **Un check de O1.** El pedido lo prohíbe y además no hay qué comprobar mecánicamente: "respetar
  los principios y normativas vigentes de TI del GCABA" no se reduce a una comprobación sobre el
  código sin mentir. Es una `REVIEW`, que es la forma que el harness ya tiene para lo que exige
  criterio sobre evidencia explícita.
- **Un mecanismo para achicar la línea base.** No se construye forma de declarar que una fuente de
  la línea base *no* aplica a una unidad. Todo lo que la línea base declara es aplicable. Achicarla
  exigiría evidencia autoritativa que hoy no produce nadie, y un campo `notApplicable` sin esa
  evidencia sería la puerta por la que se sale de O1 escribiendo una línea en el proyecto.
- **Declarar vigente lo que está cargado.** No se le agrega `currency: CURRENT` a ES0901 6.3 ni a
  ES0902 6.2. Que el harness los tenga cargados no le consta que sean la versión vigente, y
  escribirlo sería firmar una afirmación que nadie firmó. La consecuencia se acepta y se declara:
  **con la línea base como viene, la review de O1 nunca da `COMPLIANT`.**
- **Reejecutar controles.** O1 no llama a ningún check, no evalúa `controlResults` y no recalcula
  nada de ES0901 ni de ES0902. Consume los resultados ya producidos, declarados como evidencia.
- **Un mecanismo de excepción nuevo.** Se reusa el de ES0902 —`seguridad.excepcion`, las dos
  mitades, y lo local que no cuenta nunca—. Una segunda implementación de la misma idea es una
  segunda manera de eximirse.
- **Mover el estado oficial de la evaluación.** O1 en `COMPLIANT` no produce `APPROVED` ni
  `SECURITY_APPROVED` ni nada parecido. Esa frontera ya vive en `evaluacion.py` y este cambio no la
  toca: la refuerza no teniendo con qué cruzarla.
- **Un agente y una skill.** `dev-security` es el dueño de la fila y sigue siendo el mismo, con sus
  cuatro skills. Este cambio no crea, no modifica y no renombra ninguna de las dos cosas.
- **El texto citable de ES0902.** Sigue sin existir, por la razón que ya quedó escrita cuando se
  instaló la línea base del estándar: una cita mal transcrita se lee igual de autoritativa que una
  bien transcrita.

## Las decisiones, y por qué

### La línea base es un registro de apoyo, no una matriz normativa

`gcba-it-normative-baseline.json` no se parece a `es0901-7.1-normative-matrix.json` ni a
`es0902-6.2-normative-matrix.json` y no tiene que parecerse. Una matriz normativa dice **qué reglas
tiene un estándar y cómo se clasifican**. La línea base dice **qué fuentes normativas existen, de
quién son y en qué estado están**. Meterla en el mismo cajón le heredaría un contrato que no puede
cumplir —`expectedRuleCount`, `rules`, señales, policies— y la primera consecuencia sería un
validador exigiéndole reglas a un archivo que no tiene ninguna.

La alternativa era declararla como un tercer estándar bajo `standards` en el bloque normativo. Se
descartó: no es un estándar, no tiene reglas, y el día que aparezca un tercer estándar de verdad
—ES0903— el lugar tiene que estar libre.

### Un módulo nuevo, `linea_base.py`, y no una función más en `seguridad.py`

La pregunta que contesta es distinta de las tres que ya hay:

| Módulo | La pregunta que contesta |
|---|---|
| `seguridad.py` | Qué regla de ES0902 aplica a esta unidad, y con qué resultado |
| `evaluacion.py` | En qué estado está la evaluación de seguridad, y quién puede moverla |
| `cruzada.py` | Qué relación hay entre una regla de ES0901 y una de ES0902 |
| `linea_base.py` | Qué normativa de TI del GCABA existe, en qué estado está, y qué dice O1 |

Y hay una razón de peso además de la simetría: `seguridad.py` no puede importar los resultados de
ES0901 sin volverse el módulo que sabe de los dos estándares. `linea_base.py` los recibe
declarados, que es lo que O1 exige —consumir, no recalcular—, y así ninguno de los dos estándares
queda adentro del otro.

### O1 es el noveno algoritmo, y por eso deja de pasar por el camino genérico

`seguridad.ALGORITMOS` tenía ocho entradas y pasa a tener nueve. No es una rama de más: es
exactamente el caso que la tabla existe para hacer visible. El camino genérico de O1 cumple con dos
`controlResults` en `PASS`, y esos dos ids son **la policy y la review de O1 misma** — o sea, O1
cumpliría porque alguien declaró que O1 cumple. Con el algoritmo propio, el resultado de la fila
sale de la review, que mira la línea base y los resultados reusados.

La alternativa era dejar el camino genérico y confiar en que nadie declare esos dos `PASS`. Se
descartó porque es precisamente lo que un productor automático de evidencia va a hacer el día que
exista.

### `NON_COMPLIANT` le gana a `REVIEW_INCOMPLETE`, al revés que `revisiones.resolver`

En `revisiones.py` lo incompleto gana: un hallazgo sin evidencia deja toda la revisión
`REVIEW_INCOMPLETE` aunque otro hallazgo sea un desvío material. Acá se invierte, a propósito y con
motivo: **hoy toda corrida real de O1 tiene `EXTERNAL_NORMATIVE_CONTEXT_REQUIRED`**, porque las
tres resoluciones no están cargadas y no se van a cargar solas. Si lo incompleto ganara, un
resultado normativo en `NON_COMPLIANT` quedaría escondido detrás de un estado permanente, para
siempre.

Lo incompleto no desaparece: viaja en `states` y en `issues` en los dos casos. Lo que cambia es
cuál de los dos titula. Y `COMPLIANT` sigue siendo imposible mientras quede algo sin resolver, que
es lo que el fallo cerrado exige.

### Sin vigencia declarada, `NORMATIVE_SUPERSESSION_UNRESOLVED` — también para lo que está cargado

`currency` es un campo de la fuente con tres valores: `CURRENT`, `SUPERSEDED` y `UNRESOLVED`. La
línea base provista no lo declara para ninguna de las cinco fuentes, así que las cinco quedan
`UNRESOLVED` — incluidas ES0901 6.3 y ES0902 6.2. Es incómodo y es cierto: que el harness haya
cargado ES0901 6.3 no le consta que sea la versión vigente.

`SUPERSEDED` sin `supersededBy` queda sin resolver por la misma razón: saber que algo fue
reemplazado sin saber por qué cosa no alcanza para aplicar nada.

### La aplicabilidad de una fuente no se decide acá

Todo lo que la línea base declara es aplicable. No hay filtro por alcance, por dominio ni por tipo
de activo. Elegir cuáles de las cinco fuentes le tocan a una unidad es interpretación normativa, y
es la misma interpretación que el paquete de ES0902 prohíbe cuando cruza D1 con C1. El día que
llegue evidencia autoritativa que diga que una resolución no aplica a cierta clase de sistema, eso
entra como un campo declarado con su fuente, no como una deducción.

### La review de O1 no es un documento de `revisiones.py`

`revisiones.resolver` pide hallazgos con `evidenceRefs`, `practiceStrength` o `materiality`: está
hecho para una persona que revisa código o diseño contra una fuente. La review de O1 se contesta
con datos que el harness ya tiene —la línea base y los resultados de los dos estándares—, y
obligarla a pasar por un documento escrito a mano sería pedirle a alguien que transcriba a mano lo
que el harness ya sabe, con el error de transcripción incluido.

Lo que sí se reusa es **el contrato**: los cuatro resultados salen de `revisiones` por importación,
no por copia. Un quinto resultado, o uno con otro nombre, es una contradicción de tipos y no una
diferencia de criterio.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/gcba-it-normative-baseline.json` | Las cinco fuentes: dos cargadas, tres declaradas y no cargadas. Tal como vino |
| `comun/schemas/gcba-it-normative-baseline.schema.json` | El contrato del registro: estados, vigencia y autoridad, sin claves de más |
| `harnesses/desarrollo/reglas/es0902-o1-governance.md` | El paquete de gobierno de O1: la ligadura de la matriz, la doctrina de la review y la frontera |
| `harnesses/desarrollo/controles/policies/gcba-it-security-normative-compliance-required.md` | La policy, con sus seis resultados y la prohibición de adivinar la línea base |
| `harnesses/desarrollo/controles/reviews/gcba-it-security-normative-review.md` | La review, con sus entradas, su procedimiento y sus cuatro resultados |
| `harnesses/desarrollo/bin/orquestacion/linea_base.py` | Carga y valida la línea base, resuelve la review de O1 y el resultado de la fila |
| `harnesses/desarrollo/bin/orquestacion/seguridad.py` | `O1` entra en `ALGORITMOS` como el noveno, delegado a `linea_base` |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles de O1, declarados e instalados |
| `docs/seguridad-es0902.md` | O1, la línea base, y por qué la review no puede cumplir hoy |
| `tests/casos/39_es0902_o1_normativa_gcba.py` | Los escenarios de acá abajo |

La matriz de ES0902 **no se toca**: su fila de O1 ya declara `ALWAYS`, cero señales, `dev-security`,
la policy, cero checks y la review desde que se construyó.

Y se reescriben las afirmaciones que hoy están en verde y dejan de ser ciertas: el conteo de
controles —31 → 33— en `31_d6/E-30`, `32_d5/E-36`, `33_bases/E-32`, `34_d7/E-42`, `35_d8/E-37`,
`36_p1/E-39` y `37_es0902/E-13` y `E-14`, y el reporte de huecos de ES0902 —38 → 36, veinte
policies → diecinueve, dos reviews → una— en `37_es0902/E-70`.

## Escenarios verificables

Entre paréntesis, el `O1-nn` del pedido de instalación.

### La fila, que no se toca

- **E-01** — O1 sigue `ALWAYS` y con cero señales: el modo es `ALWAYS`, `signals` es la lista vacía,
  y con el diccionario de señales vacío la regla igual resuelve `APPLICABLE`. (O1-01, O1-02)
  · rojo visto: si
- **E-02** — El agente dueño sigue siendo `dev-security`, es el único que la fila nombra, y está
  declarado en el registro de agentes. (O1-03) · rojo visto: si
- **E-03** — La fila declara exactamente una policy y exactamente una review, con estos ids
  literales: `gcba-it-security-normative-compliance-required` y
  `gcba-it-security-normative-review`. (O1-04, O1-05) · rojo visto: si
- **E-04** — O1 no declara ningún check y no se instala ninguno: `checks` es la lista vacía en la
  matriz, el registro no declara ningún control de tipo `CHECK` con `rule: O1`, y no hay archivo
  bajo `controles/checks/` que cite O1 en su tupla normativa. (O1-06) · rojo visto: si
- **E-05** — Instalar O1 no agrega una fila ni un estándar: ES0902 sigue con 21 reglas, ES0901 con
  24, y el bloque normativo de una unidad sigue exponiendo dos estándares y no tres.
  · rojo visto: si

### La línea base, que es un registro de apoyo

- **E-06** — `gcba-it-normative-baseline.json` se carga, valida contra su schema y declara cinco
  fuentes bajo la autoridad `GCBA / ASI`. · rojo visto: si
- **E-07** — ES0901 6.3 y ES0902 6.2 entran como `LOADED`, cada uno con su versión y su autoridad,
  y son las **únicas dos** cargadas. (O1-07, O1-08) · rojo visto: si
- **E-08** — Las tres resoluciones que ES0902 nombra entran como `DECLARED_EXTERNAL_NOT_LOADED` con
  su título y nada más: ninguna lleva versión, fecha de fuente, vigencia ni texto, y ninguna puede
  declararse `LOADED` sin que alguien edite el archivo. (O1-09) · rojo visto: si
- **E-09** — La línea base no es una matriz normativa: no declara `rules`, no la cargan `matriz` ni
  `seguridad`, ninguna de sus fuentes aporta policies, checks ni señales, y no aparece bajo
  `standards` en el bloque normativo. · rojo visto: si
- **E-10** — Un estado de fuente que no es ninguno de los dos, o una vigencia que no es ninguna de
  las tres, hace fallar la validación del schema con el id de la fuente adentro del error.
  · rojo visto: si

### El fallo cerrado

- **E-11** — Una fuente aplicable que no está cargada deja `EXTERNAL_NORMATIVE_CONTEXT_REQUIRED`, y
  el id de esa fuente queda escrito en los motivos. (O1-10) · rojo visto: si
- **E-12** — Una fuente sin vigencia declarada deja `NORMATIVE_SUPERSESSION_UNRESOLVED` con su id; y
  una declarada `SUPERSEDED` sin `supersededBy` también. (O1-11) · rojo visto: si
- **E-13** — Con la línea base instalada tal como vino, la review de O1 da `REVIEW_INCOMPLETE` —
  nunca `COMPLIANT`— y nombra las fuentes que la dejan así. (O1-12) · rojo visto: si
- **E-14** — Una review sin sujeto es `REVIEW_INCOMPLETE`: una revisión que no dice sobre qué es no
  es una revisión. · rojo visto: si
- **E-15** — La línea base ausente, ilegible o inválida contra su schema deja `REVIEW_INCOMPLETE`
  con `NORMATIVE_BASELINE_UNRESOLVED`, y nunca una review que cumple al vacío.
  · rojo visto: si

### El reuso de los resultados que ya existen

- **E-16** — Los resultados de ES0901 que se le declaran entran como evidencia de O1, con su
  estándar, su regla y su resultado, y se cuentan en el resultado de la review. (O1-13)
  · rojo visto: si
- **E-17** — Los de ES0902 entran igual, y un resultado tal como sale de `seguridad.resultado` se
  consume sin traducirlo. (O1-14) · rojo visto: si
- **E-18** — O1 no reejecuta ningún control: con `seguridad.resultado` reemplazado por algo que
  levanta, la review de O1 sigue dando su resultado; y el módulo no nombra `controlResults` ni
  ninguno de los checks instalados. · rojo visto: si
- **E-19** — Sin ningún resultado declarado no hay nada que reusar: `REVIEW_INCOMPLETE`, y nunca
  `COMPLIANT`. · rojo visto: si
- **E-20** — Un resultado aplicable en `NON_COMPLIANT` impide `COMPLIANT`: la review da
  `NON_COMPLIANT` y nombra la regla que falla, aun cuando haya estados sin resolver al lado.
  (O1-15) · rojo visto: si

### La excepción contractual

- **E-21** — Contrato solo no levanta nada: la excepción no se concede, el resultado que falla
  sigue pesando, y la review no cumple. (O1-16) · rojo visto: si
- **E-22** — Contrato **y** aprobación de ASI la conceden: el resultado exceptuado deja de impedir
  el cumplimiento, la review queda `COMPLIANT_WITH_OBSERVATIONS` y la excepción viaja escrita en el
  resultado, con las reglas que alcanza. (O1-17) · rojo visto: si
- **E-23** — El mecanismo es el de ES0902 y no uno nuevo: la configuración local del proyecto no
  sostiene ninguna de las dos mitades, y una excepción no alcanza a una regla que no nombra.
  · rojo visto: si

### La frontera de la aprobación

- **E-24** — Una review de O1 en `COMPLIANT` no produce ninguna aprobación: ningún valor del
  resultado es un estado oficial de `evaluacion`, y el estado oficial de una evaluación declarada
  por un productor interno sigue sin moverse. (O1-18) · rojo visto: si
- **E-25** — Los cuatro resultados de la review son los de `revisiones`, importados y no
  redefinidos, y no hay un quinto. · rojo visto: si

### La traza, los agentes y el registro

- **E-26** — Todo resultado de O1 —el de la review y el de la fila— conserva `ES0902`, `6.2`, `O1` y
  la clave compuesta `ES0902.O1`, por todos los caminos. (O1-20) · rojo visto: si
- **E-27** — No se crea ni se modifica ningún agente ni ninguna skill: siguen siendo los diez
  agentes y las cuatro skills de `dev-security`, y ningún artefacto de O1 nombra uno nuevo.
  (O1-19) · rojo visto: si
- **E-28** — Los dos controles quedan declarados e instalados: 33 en el registro, la policy y la
  review en `INSTALLED`, sin archivos sueltos, y los dos dejan de figurar en el reporte de huecos
  de ES0902. · rojo visto: si

## Cómo se verifica

Los 28 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista y no hay ningún escenario cuyo sujeto sea una corrida
de un modelo.

E-08, E-10, E-18 y E-25 son **invariantes sobre un producto** y no ejemplos: las tres resoluciones
una por una con todos los campos que no pueden tener, todos los valores inválidos de estado y de
vigencia, todos los checks instalados contra el texto del módulo, y los cuatro resultados contra la
constante de `revisiones`.

🔴 Los ids que un escenario verifica van **clavados por literal** en el test, no leídos desde la
matriz ni desde el módulo. E-03 es el caso que importa: leer el id de la policy desde la fila y
compararlo contra sí mismo es un test que pasa con cualquier id.

📌 El veredicto no contradijo ningún escenario y dejó tres deudas de verificación, **las tres
cerradas antes de `verificacion.md`**, y las tres de la misma familia —una aserción que se satisface
con algo más débil que lo que el escenario afirma—:

```
E-04  `"rule": "O1"` no es la grafía que escribe ningún check  -> literales por AST + el registro
E-15  el escenario decía "ilegible" y nada lo probaba           -> un JSON roto en el árbol
E-09  la cláusula de `standards` vivía en el test de E-05       -> afirmada en E-09
```

## Riesgos conocidos

- **La review de O1 no puede cumplir, y va a quedar así mucho tiempo.** Tres resoluciones sin
  cargar y cinco fuentes sin vigencia declarada dejan toda corrida real en `REVIEW_INCOMPLETE`. Es
  el resultado correcto y es también el que más invita a que alguien "arregle" el archivo
  declarando `LOADED` y `CURRENT` sin evidencia. Lo único que lo defiende es que el archivo es
  normativa provista y que editarlo se ve en el diff.
- **Los resultados reusados no los produce nadie todavía.** La review los recibe declarados, igual
  que la evidencia de G1 a D8 y de todo ES0902. Lo que destraba esto es el análisis de impacto, no
  este cambio.
- **La frontera de la aprobación se verifica por ausencia.** E-24 comprueba que ningún valor del
  resultado es un estado oficial. Es una aserción sobre lo que *no* está, y una aserción así se
  satisface sola el día que el resultado cambie de forma. Por eso E-24 barre los valores del
  resultado serializado y no un campo elegido a mano.
