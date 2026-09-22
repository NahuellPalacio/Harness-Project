# G2: la primera regla que no se puede reducir a un check

**Estado:** construido · **Fecha:** 2026-09-18

## Qué problema resuelve

G1 se pudo construir entero porque su pregunta tiene respuesta mecánica: la versión está en el
Anexo II o no está. G2 no. Dice que hay que adoptar las buenas prácticas reconocidas de la
industria aplicables a cada tecnología, y eso exige decidir **qué prácticas existen**, **cuáles
aplican a esta tecnología y a esta versión**, **si la implementación las adoptó** y **si un
apartamiento está justificado**. Ninguna de las cuatro se contesta con un booleano.

El harness hoy sólo sabe dos formas de control: `POLICY` y `CHECK`. Forzar G2 a un check produce
exactamente lo que el paquete pide no hacer:

```text
goodPractices == true
```

Una función así se lee igual de autoritativa que un check real y no comprueba nada. Falta el
tercer tipo: **`REVIEW`** — criterio técnico estructurado sobre evidencia explícita.

Y falta el contrato de esa evidencia. Sin él, "el agente revisó y está bien" es una revisión; con
él, una revisión sin fuente citada no llega a `COMPLIANT`.

## Qué queda afuera

- **El catálogo de buenas prácticas de cada tecnología.** Congelar "las buenas prácticas de
  Angular" en un archivo del harness es garantizar que envejezca mal y quede desactualizado sin que
  nadie se entere. El perfil de prácticas se resuelve cuando una unidad de trabajo real identifica
  sus tecnologías, contra fuentes citadas en el momento.
- **Salir a buscar guías a internet.** Este cambio no scrapea nada. La evidencia entra como dato,
  con su fuente y su fecha.
- **Aprobar una excepción.** El harness puede registrar una justificación; no puede aprobarla,
  porque no existe todavía la autoridad que aprueba. Queda `JUSTIFICATION_PENDING`.
- **Absorber controles de otras reglas.** G2 es amplio, y esa amplitud es su riesgo: `D3`, `P2` y
  las demás siguen siendo exigibles por su cuenta. Lo que ya tiene regla propia no se revisa acá.
- **Los otros 66 controles.** Siguen declarados y sin construir.

## Las decisiones, y por qué

### `REVIEW` es un tipo de control, no un alias de `CHECK`

```text
POLICY   restringe antes
CHECK    verifica objetivamente despues
REVIEW   criterio tecnico estructurado sobre evidencia explicita
```

Se extiende el registro de controles que nació con G1 —dos tipos, y el lugar del tercero ya estaba
previsto— en vez de abrir un registro paralelo. Un solo lugar donde consta qué está instalado, que
es lo que el pedido pide y lo que evita que "instalado" dependa de a quién se le pregunte.

### La estructura se valida mecánicamente; el juicio no

Un modelo puede aportar el criterio técnico —qué práctica existe, si se adoptó—. Lo que **no**
puede depender de un modelo es si la revisión está bien formada: que el schema valide, que la tupla
normativa esté, que cada hallazgo referencie evidencia que exista, que el agente dueño esté
declarado en el registro. Eso es código y se comprueba siempre.

### La opinión de un agente no es evidencia

Seis clases de fuente, y las dos últimas no alcanzan solas:

```text
GCBA_NORMATIVE                      la norma del organismo
OFFICIAL_TECHNOLOGY_DOCUMENTATION   la documentacion oficial de la tecnologia
FORMAL_STANDARD                     un estandar formal
RECOGNIZED_INDUSTRY_GUIDANCE        guia reconocida de la industria
PROJECT_IMPLEMENTATION              como esta hecho el proyecto — evidencia de adopcion
PROJECT_CONVENTION                  como se hace en el proyecto — NO prueba reconocimiento
```

Que un proyecto haga algo de una manera no convierte esa manera en práctica reconocida de la
industria. Sin al menos una fuente reconocida, la práctica no tiene fuerza y la revisión no cierra.

### La modalidad de la fuente no se sube ni se baja

`REQUIRED_BY_SOURCE`, `RECOMMENDED_BY_SOURCE`, `OPTIONAL_BY_SOURCE`, `UNRESOLVED`. Si la fuente
recomienda, el harness no exige; si la fuente exige, el harness no lo rebaja a sugerencia. Cambiar
la modalidad en silencio es reescribir la fuente.

### Sin evidencia no hay `COMPLIANT`

Cuatro resultados: `COMPLIANT`, `COMPLIANT_WITH_OBSERVATIONS`, `NON_COMPLIANT` y
`REVIEW_INCOMPLETE`. Falta evidencia material → `REVIEW_INCOMPLETE`, nunca cumple. Es la misma
regla que sostiene `dev-quality-validation`: *"never turns missing evidence into success"*.

### Las fuentes que se contradicen se muestran, no se eligen

`SOURCE_CONFLICT`, con las dos fuentes conservadas. Elegir en silencio la que hace pasar la
implementación es el sesgo más barato que puede tener un revisor, y no deja rastro.

### Pasar G1 no es pasar G2

Que la tecnología esté homologada y que se la use bien son dos preguntas. El contrato de la review
manda a tomar el inventario de G1 como alcance de G2 —no se escribe un segundo detector— y ahí
termina la relación.

> **Nota del 2026-09-22.** Decía que el inventario de G1 "se **reusa**", como hecho. Hoy no hay
> camino de código que lleve ese inventario a una revisión —nadie lo produce todavía—, y E-20 se
> angostó a lo que se puede comprobar: que la review lo instruye y que ni la review ni
> `revisiones.py` detectan tecnologías por su cuenta. Esta sección dice lo mismo que E-20.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/normative-review.schema.json` | El contrato de una revisión: sujeto, evidencia, hallazgos, resultado y revisor |
| `harnesses/desarrollo/bin/orquestacion/revisiones.py` | Valida la estructura de una revisión, resuelve su resultado y controla las referencias contra el registro de agentes |
| `harnesses/desarrollo/controles/policies/industry-good-practices-required.md` | El contrato de la policy |
| `harnesses/desarrollo/controles/reviews/technology-practice-review.md` | El contrato de la review |
| `harnesses/desarrollo/reglas/control-registry.json` | Suma el tipo `REVIEW` y los dos controles de G2 |
| `harnesses/desarrollo/reglas/es0901-7.1-normative-matrix.json` | La fila de G2 declara su review |
| `comun/schemas/es0901-7.1-normative-matrix.schema.json` | `reviews` opcional, compatible con las filas que no lo traen |
| `harnesses/desarrollo/bin/orquestacion/matriz.py` | `declaredReviews` en la resolución, sin romper policies ni checks |
| `harnesses/desarrollo/bin/orquestacion/plan.py` | La unidad propaga `declaredReviews` |
| `tests/casos/25_g2_buenas_practicas.py` | Los escenarios de este cambio |

## Escenarios verificables

Entre paréntesis, el `G2-nn` del pedido.

### La regla y su tipo de control

- **E-01** — `G2` es `ALWAYS`: aplica sin ninguna señal. (G2-01) · rojo visto: si
- **E-02** — `G2` declara una policy, **cero checks** y una review. (G2-02)
  · rojo visto: si
- **E-03** — La review se instala sin que aparezca ningún check de G2: no se fabrica uno para
  simetría estructural. (G2-03) · rojo visto: si
- **E-04** — `REVIEW` es un tipo del registro de controles, y una fila sin `reviews` sigue siendo
  válida. (G2-20) · rojo visto: si

### El contrato de la evidencia

- **E-05** — El schema de revisión valida, y entra en el subconjunto soportado. (G2-04)
  · rojo visto: si
- **E-06** — Una revisión cuyo único respaldo es la opinión del agente no satisface G2: sin
  fuente reconocida no llega a `COMPLIANT`. (G2-05) · rojo visto: si
- **E-07** — `OFFICIAL_TECHNOLOGY_DOCUMENTATION` sí es fuente reconocida. (G2-06)
  · rojo visto: si
- **E-08** — `PROJECT_CONVENTION` sola no prueba que una práctica sea reconocida por la industria.
  (G2-07) · rojo visto: si
- **E-09** — Un hallazgo que referencia una evidencia que no existe es estructuralmente inválido.
  · rojo visto: si

### Aplicabilidad y fuerza

- **E-10** — Una práctica sin aplicabilidad declarada es `UNRESOLVED`, nunca `NOT_APPLICABLE`.
  (G2-10) · rojo visto: si
- **E-11** — Una práctica `NOT_APPLICABLE` exige su motivo escrito. (G2-09)
  · rojo visto: si
- **E-12** — La modalidad de la fuente se conserva: lo recomendado no se exige y lo exigido no se
  rebaja. (G2-11) · rojo visto: si
- **E-13** — Falta el contexto de tecnología o versión donde la guía depende de la versión:
  `REVIEW_INCOMPLETE`. (G2-08) · rojo visto: si

  > **Nota del 2026-09-22.** El refutador dictó `sin sustento`: el contrato no tenía cómo decir
  > que una guía depende de la versión, `resolver()` nunca leía `subject.version`, y el test
  > llegaba a `REVIEW_INCOMPLETE` por la fuerza `UNRESOLVED` que traía mezclada. Se sube el
  > mecanismo en vez de angostar el escenario: el hallazgo gana un campo opcional,
  > `versionDependent` (booleano, sin declarar vale `false`, compatible con las revisiones que no
  > lo traen, D3 incluida). Con `versionDependent: true` y el sujeto sin `version` —ausente,
  > `null` o vacía— el hallazgo no se juzga para ningún lado, tampoco como `NOT_APPLICABLE`, y la
  > revisión queda `REVIEW_INCOMPLETE` con el estado `REVIEW_VERSION_CONTEXT_MISSING` y un motivo
  > que nombra el hallazgo. Declarar que una guía depende de la versión es criterio de quien
  > revisa; lo que es código es que, dicho eso, sin versión no se cierra. La falta de tecnología
  > la frenan dos guardas, el `required` del schema y el control de `validar_estructura` sobre `subject.id`, y el test afirma cada una por su mensaje (ausente, `null` y vacío). El test aísla las tres mitades:
  > dependiente sin versión, dependiente con versión y no dependiente sin versión.

### El resultado

- **E-14** — Apartarse de una práctica aplicable `REQUIRED_BY_SOURCE` da `NON_COMPLIANT` si no hay
  resolución autoritativa. (G2-12) · rojo visto: si
- **E-15** — Apartarse de una `RECOMMENDED_BY_SOURCE`, con el resto de la evidencia completa, da
  `COMPLIANT_WITH_OBSERVATIONS`. (G2-13) · rojo visto: si
- **E-16** — Falta evidencia material: `REVIEW_INCOMPLETE`, y nunca `COMPLIANT`. (G2-14)
  · rojo visto: si
- **E-17** — Una justificación registrada **no** aprueba la excepción: queda
  `JUSTIFICATION_PENDING` y el resultado no pasa a cumplir. (G2-15) · rojo visto: si
- **E-18** — Dos fuentes creíbles que se contradicen dan `SOURCE_CONFLICT`, con las dos
  conservadas. (G2-16) · rojo visto: si

### Los límites

- **E-19** — Que G1 dé `HOMOLOGATED` no hace `COMPLIANT` a G2. (G2-17)
  · rojo visto: si
- **E-20** — El documento de la review manda a reusar el inventario de tecnologías de G1 como
  alcance de G2, y ni la review ni `revisiones.py` detectan tecnologías por su cuenta: no hay un
  segundo detector. (G2-18) · rojo visto: si

  > **Nota del 2026-09-22.** Redacción angostada tras un `sin sustento` del refutador: el test
  > comparaba un literal contra una lista armada en el mismo test. Decía antes "el inventario de
  > G1 se reusa como alcance de G2", y eso hoy no tiene camino de código que lo sostenga —nadie
  > produce todavía el inventario, ver los riesgos— así que el escenario afirma lo que sí se puede
  > comprobar, que es estructural: la review instruye reusar el inventario de G1; `revisiones.py`
  > no lee el sistema de archivos salvo su propio schema, no nombra manifiestos de dependencias
  > ni define nada con forma de detector (se lee por AST); y en `controles/reviews/` no hay
  > código. Que el día que exista el inventario la revisión lo tome de G1 queda como instrucción
  > del contrato, no como algo que un test pruebe.
- **E-21** — El agente dueño y los de apoyo tienen que estar declarados en el registro de agentes;
  uno desconocido invalida la revisión y no se crea. (G2-19) · rojo visto: si

### La propagación

- **E-22** — La unidad de trabajo lleva `declaredReviews` sin romper `declaredPolicies` ni
  `declaredChecks`. (G2-20) · rojo visto: si
- **E-23** — Antes de instalar, la review es `DECLARED_REVIEW_NOT_INSTALLED`; después desaparece de
  esa lista **sin tocar la regla de la matriz**. (G2-21, G2-14 del pedido de instalación)
  · rojo visto: si
- **E-24** — Toda revisión conserva la tupla `ES0901 / 6.3 / 7.1 / G2`. (G2-22)
  · rojo visto: si

## Cómo se verifica

Los 24 pasan por la suite. Ninguno evalúa criterio técnico: lo que se comprueba es que la
**estructura** de una revisión sea válida y que el resultado se derive de los hallazgos y de la
evidencia según reglas fijas. Que una práctica sea efectivamente una buena práctica de Angular es
juicio, y este cambio no promete comprobarlo — promete que sin fuente citada ese juicio no llega a
`COMPLIANT`.

Las revisiones de los casos se arman en memoria. Ninguna toca el árbol.

## Riesgos conocidos

- **G2 es amplio y puede tragarse a las otras reglas.** "Buenas prácticas" describe casi cualquier
  cosa. La frontera está escrita —lo que tiene regla propia no se revisa acá— y nada la hace
  cumplir: es criterio de quien revisa.
- **Nadie produce todavía las fuentes de práctica.** Igual que las señales de la matriz y el
  inventario de G1, la evidencia entra como dato y no hay quien la junte. Una revisión real hoy
  sale `REVIEW_INCOMPLETE`.
- **La estructura válida no es una revisión buena.** Un revisor puede citar una fuente irrelevante,
  o una guía real que no aplica a la versión en uso, y la validación estructural lo acepta. Lo que
  compra es que la cita esté y se pueda discutir.
- **`REVIEW` abre la puerta a que otras reglas eviten construir su check.** El día que una regla
  que sí admite comprobación mecánica se declare review para ahorrarse el trabajo, este tipo de
  control deja de significar lo que significa hoy.
