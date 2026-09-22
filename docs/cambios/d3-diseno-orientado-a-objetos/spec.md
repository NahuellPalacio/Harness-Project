# D3: la primera regla que es condicional y además no se puede comprobar

**Estado:** construido · **Fecha:** 2026-09-20

## Qué problema resuelve

Las tres reglas construidas hasta acá aportaron una pieza cada una:

```text
G1   un check mecanico contra un catalogo
G2   una REVIEW, para lo que no admite comprobacion mecanica
D1   una SENAL con evidencia, para lo que no aplica siempre
```

D3 es la primera que necesita **las dos últimas juntas**:

> "Uso de la programación orientada a objetos (POO) implementando una codificación de alto nivel y
> buenas prácticas." — ES0901 §7.1 D3, pág. 12

Aplica sólo si hay código de aplicación en juego —señal `applicationCodePresent`— y lo que exige no
se contesta con un booleano. La tentación es exactamente la que G2 ya nombró, con otro disfraz:

```text
classCount > 0
inheritancePresent == true
isOOP == true
```

Una función así se lee autoritativa y no comprueba nada: un sistema con doscientas clases y toda la
lógica en un `Helper` de tres mil líneas pasa las tres.

Hay además dos cosas que la infraestructura de G2 no puede hacer todavía:

1. **La regla de evidencia de G2 es la opuesta a la de D3.** G2 pregunta *si una práctica es
   reconocida por la industria*, así que exige una fuente reconocida y declara insuficiente a
   `PROJECT_IMPLEMENTATION`. D3 pregunta *si este código está diseñado así*, y la única evidencia
   que puede contestarlo es la implementación. Hoy `revisiones.py` exige la fuente reconocida
   siempre, para cualquier review.
2. **No hay dónde poner un conflicto de paradigma.** Si la tecnología elegida no permite demostrar
   la obligación de D3, eso no es un desvío ni evidencia faltante: es un problema que resuelve
   arquitectura o una persona, y el harness no puede aprobarlo solo.

Sus dos controles —`high-level-oop-design-required` y `object-oriented-design-review`— están
declarados y no existen; la fila de D3 en la matriz todavía no declara su review.

## Qué queda afuera

- **Un check de D3.** No se fabrica uno para simetría estructural. `checks: []` es la declaración
  correcta y es lo que el pedido exige preservar.
- **Un catálogo de qué es buen diseño orientado a objetos.** Congelar eso en un archivo del harness
  es garantizar que envejezca mal; además cambia por lenguaje, por framework y por capa. Las
  dimensiones de revisión —encapsulamiento, cohesión, acoplamiento, fronteras de abstracción— son
  operativas y **no** son requisitos citados de ES0901: el estándar dice una línea y esa línea no
  enumera nada.
- **Leer el código.** La review no abre el repositorio: la evidencia de implementación entra como
  dato, con su referencia. Quien la junte es otro cambio, igual que en G1, G2, D1 y D2.
- **Un segundo inventario de tecnologías.** El de G1 se reusa. Un detector paralelo es la forma más
  rápida de que dos reglas digan cosas distintas del mismo stack.
- **Aprobar una excepción de paradigma.** El harness puede registrar el conflicto; no puede
  aprobarlo, porque no existe la autoridad que aprueba. Es la misma decisión que G2 tomó con
  `JUSTIFICATION_PENDING`.
- **P2 y P3.** Los patrones de diseño y el estilo unificado son reglas propias, con sus propios
  controles. Que haya un Strategy o que pase el linter no es asunto de D3.
- **Los otros productores de señales.** `applicationCodePresent` es la tercera señal con productor;
  las once restantes siguen sin nadie.
- **Los otros 60 controles declarados.** Siguen declarados y sin construir.

## Las decisiones, y por qué

### La regla de evidencia deja de ser una sola para todas las reviews

Hoy `revisiones.resolver` exige, para cualquier hallazgo, al menos una fuente de la lista de
reconocidas. Eso es correcto para G2 y es **falso** para D3: una guía de Angular no prueba que este
sistema esté bien diseñado, y el código de este sistema sí.

```text
G2   exige fuente reconocida     la pregunta es si la practica existe afuera
D3   exige evidencia del sistema la pregunta es como esta hecho esto
```

La exigencia pasa a declararse por regla, en una tabla en `revisiones.py`. El default para una regla
que no figure es el de G2 —el más estricto—: una review nueva es estricta hasta que alguien decida
lo contrario y lo escriba.

Se descartó que la declare el propio documento de review: dejar que quien escribe la revisión elija
qué evidencia le alcanza es dejar que una revisión sin respaldo diga que cumple.

### Un hallazgo de D3 declara qué dimensión del diseño evalúa

El pedido dice que clases, herencia, ORM y framework *"may be evidence but are not sufficient by
themselves"*, y el harness no puede leer un `claim` para saber si alguien está reportando un conteo
o juzgando un diseño. Lo que sí puede exigir es que el hallazgo diga **sobre qué propiedad del
diseño concluye**, de un vocabulario cerrado:

```text
responsibility-encapsulation · cohesion · controlled-coupling · abstraction-boundaries
layer-responsibilities · framework-native-organization · procedural-concentration
collaboration-maintainability
```

Un conteo no está en esa lista y no puede estar: "define 240 clases" es un hecho del código, no una
propiedad de su diseño. Puede ser **evidencia** de una dimensión, y entonces la conclusión es sobre
la dimensión y la firma quien revisa.

🔴 Estas dimensiones son **operativas de revisión y no requisitos citados de ES0901**. El estándar
dice una línea y esa línea no enumera nada; citarlas como si fueran la norma sería inventar texto
normativo. El vocabulario existe para forzar que se declare de qué se está hablando, no para
agregar obligaciones.

Lo que esto **no** compra: que la conclusión sea buena. Un revisor puede declarar
`cohesion: ADOPTED` citando un conteo de clases, y la estructura lo acepta. Eso ya está declarado
en los riesgos, y es el límite de cualquier review.

### Un desvío de D3 pesa por materialidad, no por fuerza de la fuente

G2 pesa un desvío por `practiceStrength`: si la fuente exige, incumplir es `NON_COMPLIANT`; si
recomienda, es observación. D3 no tiene fuente que exija o recomiende —tiene una obligación del
estándar, y punto—; lo que varía es **cuánto pesa el desvío en este sistema**:

```text
MATERIAL     la organizacion del codigo contradice la obligacion       NON_COMPLIANT
MINOR        hay desvios y no cambian el caracter del diseño           COMPLIANT_WITH_OBSERVATIONS
sin declarar no se sabe cuanto pesa                                     REVIEW_INCOMPLETE
```

Un desvío sin materialidad declarada **no se resuelve solo**. Elegir el lado suave por defecto
—"habrá sido menor"— es exactamente cómo un `NON_COMPLIANT` se convierte en una observación sin que
nadie lo decida.

Los dos ejes conviven en el schema y cada regla exige el suyo: una review de G2 sin
`practiceStrength` es inválida, y una de D3 sin `materiality` también.

### `TECHNOLOGY_PARADIGM_CONFLICT` no es un desvío ni evidencia faltante

Es un sexto estado de hallazgo, y arrastra el resultado a `REVIEW_INCOMPLETE` con el conflicto
visible. No a `NOT_APPLICABLE` —la regla sigue aplicando, hay código—, no a `COMPLIANT` y no a una
excepción aprobada. Lo resuelve arquitectura o una persona, y hoy el harness no tiene a quién
preguntarle.

🔴 Lo que esto evita tiene nombre: que la regla se reinterprete para que entre la tecnología que ya
se eligió. Si el paradigma no da, el que tiene un problema es el proyecto, no la regla.

### Ningún resultado se hereda

```text
G2 COMPLIANT          != D3 COMPLIANT
un Strategy presente  != D3 COMPLIANT
el linter en verde    != D3 COMPLIANT
```

La evidencia sí se reusa —el inventario de G1 como alcance, los hallazgos de G2 como apoyo— y el
resultado no. Es la misma frontera que G2 ya escribió contra G1, y se vuelve a escribir porque acá
hay tres reglas vecinas en vez de una.

### La señal se resuelve una vez y la usan sus cuatro consumidores

`applicationCodePresent` es la primera señal que la matriz ata a más de una regla: `D3`, `P2`, `P3`
y `C2`. Se produce una vez por resolución y las cuatro toman el mismo valor y la misma evidencia.
No hay una segunda producción por regla, que es como dos reglas terminan discrepando sobre si hay
código.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/normative-review.schema.json` | Suma `dimension`, `materiality`, el estado `TECHNOLOGY_PARADIGM_CONFLICT` y la clase de fuente `PROJECT_ARCHITECTURE`; `practiceStrength` deja de ser obligatorio para todas |
| `harnesses/desarrollo/bin/orquestacion/revisiones.py` | La exigencia de evidencia y el peso de un desvío pasan a declararse por regla; el conflicto de paradigma nunca llega a `COMPLIANT` |
| `harnesses/desarrollo/controles/policies/high-level-oop-design-required.md` | El contrato de la policy |
| `harnesses/desarrollo/controles/reviews/object-oriented-design-review.md` | El contrato de la review |
| `harnesses/desarrollo/reglas/control-registry.json` | Suma los dos controles de D3 |
| `harnesses/desarrollo/reglas/es0901-7.1-normative-matrix.json` | La fila de D3 declara su review; su modo, su señal y su identidad normativa no cambian |
| `docs/normativa-7.1.md` | La tercera señal y la segunda review |
| `tests/casos/25_g2_buenas_practicas.py` | `E-04` dejaba de pasar por un conteo fijo de filas sin `reviews`; pasa a afirmar la opcionalidad |
| `tests/casos/28_d3_diseno_orientado_a_objetos.py` | Los escenarios de este cambio |

No se agrega ningún módulo de señales ni de reviews: los dos existen y se reusan.

## Escenarios verificables

Entre paréntesis, el `D3-nn` del pedido de instalación.

### La señal

- **E-01** — `D3` es `CONDITIONAL` sobre `applicationCodePresent`, y su identidad normativa —id,
  categoría, intención operativa, modo y señal— no cambia. (D3-01) · rojo visto: si
- **E-02** — `applicationCodePresent = TRUE` con evidencia deja `D3` aplicable. (D3-02)
  · rojo visto: si
- **E-03** — `FALSE` con evidencia deja `D3` en `notApplicableRules`. (D3-03)
  · rojo visto: si
- **E-04** — Sin señal, `D3` queda `APPLICABILITY_UNRESOLVED` con la señal que falta escrita al
  lado. (D3-04) · rojo visto: si
- **E-05** — Lo ausente nunca se convierte en `FALSE`, por cuatro caminos: sin señal, con la señal
  sin resolver, sin evidencia y con evidencia que no referencia nada. (D3-05)
  · rojo visto: si
- **E-06** — La señal se resuelve una vez y la reusan sus cuatro consumidores —`D3`, `P2`, `P3` y
  `C2`—: el mismo documento mueve a las cuatro y todas leen el mismo valor y la misma evidencia.
  (D3-06) · rojo visto: si

### La forma del control

- **E-07** — `D3` declara **una** policy, **cero** checks y **una** review. (D3-07)
  · rojo visto: si
- **E-08** — No se fabrica ningún check de D3: ni la matriz lo declara, ni el registro de controles
  tiene uno con esa regla, ni existe un archivo de check suyo en el disco. (D3-08)
  · rojo visto: si
- **E-09** — La review de D3 reusa la infraestructura de G2: mismo registro de controles, mismo
  schema y mismo módulo, sin un segundo registro ni un segundo contrato.
  · rojo visto: si

### Lo que no alcanza, y lo que sí

- **E-10** — Que existan clases no es un hallazgo de D3: un hallazgo tiene que declarar **qué
  dimensión del diseño evalúa**, de un vocabulario cerrado, y "el módulo define 240 clases" no es
  ninguna. Un hallazgo sin dimensión declarada, o con una que no está en el vocabulario, invalida la
  revisión. (D3-09) · rojo visto: si
- **E-11** — Lo mismo para la herencia: tres niveles de jerarquía son un hecho del código, no una
  propiedad de su diseño. (D3-10) · rojo visto: si
- **E-12** — Que el framework elegido sea orientado a objetos tampoco. (D3-11)
  · rojo visto: si
- **E-13** — Que un agente afirme que el diseño está limpio tampoco: sin evidencia de la
  implementación, no hay resultado que cumpla. · rojo visto: si
- **E-14** — Evidencia de la implementación que muestra responsabilidades encapsuladas y
  colaboración mantenible produce `COMPLIANT`. (D3-12) · rojo visto: si
- **E-15** — Evidencia de código o de contexto incompleta: `REVIEW_INCOMPLETE`, nunca cumple.
  (D3-13) · rojo visto: si
- **E-16** — Un desvío **material** —lógica concentrada de forma procedural— produce
  `NON_COMPLIANT`. (D3-14) · rojo visto: si
- **E-17** — Un desvío sin materialidad declarada no se resuelve hacia el lado suave:
  `REVIEW_INCOMPLETE`. · rojo visto: si

### El conflicto de paradigma

- **E-18** — El conflicto entre la tecnología elegida y la obligación de D3 se expone
  explícitamente, con su estado propio. (D3-15) · rojo visto: si
- **E-19** — El conflicto no se autoaprueba: no da `COMPLIANT`, no vuelve la regla
  `NOT_APPLICABLE` y no produce ninguna excepción aprobada. (D3-16) · rojo visto: si

### Las fronteras

- **E-20** — `G2 COMPLIANT` no implica `D3 COMPLIANT`: las dos reviews sobre el mismo sistema dan
  resultados independientes. (D3-17) · rojo visto: si
- **E-21** — Que un patrón de diseño esté presente no implica `D3 COMPLIANT`, y D3 no emite ningún
  veredicto de `P2`. (D3-18) · rojo visto: si
- **E-22** — Que el estilo y el linter estén en verde no implica `D3 COMPLIANT`, y D3 no emite
  ningún veredicto de `P3`. (D3-19) · rojo visto: si
- **E-23** — El inventario de tecnologías de G1 se reusa como alcance; no hay un segundo detector ni
  un segundo inventario. (D3-20) · rojo visto: si
- **E-24** — La evidencia de G2 se puede reusar como apoyo y no arrastra su resultado.
  · rojo visto: si

### Los agentes, la propagación y la instalación

- **E-25** — El agente dueño y los de apoyo se resuelven contra el registro de agentes; uno que el
  registro no declara invalida la review y no se crea. (D3-22) · rojo visto: si
- **E-26** — La unidad de trabajo propaga la señal con su evidencia, la policy y la review, y
  `declaredChecks` no gana ninguno por D3. (D3-21) · rojo visto: si
- **E-27** — Antes de instalar, la policy y la review son `DECLARED_POLICY_NOT_INSTALLED` y
  `DECLARED_REVIEW_NOT_INSTALLED`; después desaparecen de la lista de faltantes **sin tocar el texto
  normativo de la regla**. (D3-23) · rojo visto: si
- **E-28** — Todo resultado de `D3` conserva la tupla `ES0901 / 6.3 / 7.1 / D3`. (D3-24)
  · rojo visto: si

## Cómo se verifica

Los 28 pasan por la suite, en `tests/casos/28_d3_diseno_orientado_a_objetos.py`. Ninguno necesita
lectura.

Ninguno evalúa criterio técnico: no se comprueba que una revisión acierte sobre el diseño de un
sistema, porque eso es juicio y ningún test lo puede contradecir. Lo que se comprueba es que la
**estructura** de la revisión sea válida y que el resultado se derive de sus hallazgos y de su
evidencia según reglas fijas.

Sobre las cuatro formas de falso positivo que el pedido nombra, lo verificado es exactamente esto y
no más:

| | Qué lo cierra |
|---|---|
| clases · herencia | No son dimensiones del vocabulario: un hallazgo que sólo las reporta no tiene qué declarar y la revisión es inválida |
| framework | Su fuente natural —la documentación del proveedor— está fuera de las que D3 admite |
| opinión de un agente | Sin evidencia de la implementación referenciada, no hay resultado que cumpla |

Ninguna de las cuatro depende de leer el texto de un `claim`, porque el harness no lo lee. Un
revisor que declare una dimensión real citando un conteo pasa la estructura: eso es juicio, está en
los riesgos, y ningún test de este cambio promete atraparlo.

E-20, E-21 y E-22 corren sobre el mismo sistema con las dos reviews o con la evidencia de la regla
vecina: un resultado independiente es lo que prueba que nada se hereda.

Las revisiones, las señales y los inventarios se arman en memoria. Del árbol se lee sólo lo
versionado, y ningún caso escribe.

## Lo que este cambio le toca a G2

Dos cosas, y las dos se declaran porque son trabajo ajeno a este cambio:

📌 **Corrección.** La primera versión de esta sección decía que G2 está *"verificado y cerrado"*.
No lo está: `docs/cambios/g2-buenas-practicas/` tiene `spec.md` y no tiene `verificacion.md`, igual
que `g1-tecnologias-homologadas/`. Los dos están **construidos y sin refutar**, que es el ítem 4 de
`Pendientes/Fix-Harness/PENDIENTES-FH.md`. Lo que sigue vale igual —lo que se toca es de otro
cambio y se declara— pero la premisa era falsa y queda registrada.

1. **`revisiones.py` deja de tener una sola regla de evidencia.** El comportamiento de G2 no cambia
   —su fila de la tabla es exactamente lo que el módulo hacía antes para todas—, pero el módulo que
   su verificación cubrió ya no es el mismo archivo.
2. **`25_g2_buenas_practicas.py::E-04` afirmaba que veintitrés filas de la matriz no traen
   `reviews`.** Ese número baja a veintidós el día que D3 declara la suya. Lo que el escenario
   afirma —que el campo es opcional y una fila sin él sigue siendo válida— no cambió; lo que estaba
   mal escrito era el test, que medía el calendario en vez de la opcionalidad. Se reescribe la
   aserción, no el escenario.

Las dos piden que `G2 / E-04`, `E-06`, `E-14` y `E-15` vuelvan a pasar por el refutador junto con
este cambio.

## Riesgos conocidos

- **La estructura válida no es una revisión buena.** Un revisor puede citar tres archivos
  irrelevantes, declarar `cohesion: ADOPTED` y concluir cualquier cosa. Lo que compra el contrato es
  que la conclusión esté atada a evidencia que existe, que diga sobre qué propiedad del diseño
  concluye, y que las dos cosas se puedan discutir. **No** compra que la conclusión sea cierta.
- **El vocabulario de dimensiones puede envejecer.** Ocho entradas escritas a mano, y una revisión
  sobre un paradigma que no encaje en ninguna va a forzar una dimensión que no le corresponde en vez
  de declarar el conflicto.
- **`materiality` la declara quien revisa.** Es el eje que decide entre `NON_COMPLIANT` y una
  observación, y lo elige la misma persona o agente que escribe el hallazgo. Lo único que lo
  contiene es que omitirlo no da el lado suave, sino `REVIEW_INCOMPLETE`.
- **`TECHNOLOGY_PARADIGM_CONFLICT` puede volverse la salida de lo incómodo.** Deja el resultado
  incompleto sin obligar a nada, y no hay todavía quien lo resuelva. Se verá cuando alguien lo use
  sobre un proyecto real.
- **La frontera con P2 y P3 no la hace cumplir nada.** Está escrita y testeada con casos; el día que
  alguien meta una verificación de estilo adentro de la review de D3, los tests siguen verdes.
- **La tabla de exigencia por regla crece con cada review.** Hoy tiene dos filas. Es un lugar donde
  una regla nueva puede entrar con la exigencia floja sin que se note, y el default estricto es lo
  único que lo demora.
