# ES0902 Vu10 — la guía OWASP que aplica, revisada y con fuente vigente

**Estado:** verificado y cerrado · **Fecha:** 26-09-2026 · **Regla:** ES0902 6.2 §6 Vu10

## Qué problema resuelve

> *"Para mejorar la seguridad en las aplicaciones, se debe tener en cuenta la información suministrada
> en los siguientes links: Aplicaciones Web: OWASP Top 10 · API's y/o Web Services: OWASP API Security
> · Aplicaciones Mobile: OWASP Mobile Top 10"* (ES0902 v6.2, §6)

La fila está en la matriz: `CONDITIONAL` con la señal `owaspApplicableAssetPresent`, el agente
`dev-security`, una policy, **cero checks** y una review. Ni `owasp-security-guidance-required` ni
`owasp-security-guidance-review` están en el registro de controles. `seguridad.py` tiene un `_vu10` de
la línea base que pide una guía por tipo de activo con referencia, versión y fecha, y nada más: no mira
si la fuente está vigente ni si cada punto de la guía se revisó.

Vu10 tiene seis formas baratas de ponerse en verde o en rojo, y este cambio las cierra:

1. **Una guía genérica por las tres.** Una aplicación web con su API necesita las dos familias.
2. **La edición de memoria.** "OWASP Top 10 2021" escrito por un modelo no es una fuente.
3. **Una lista eterna de puntos en el código.** La próxima edición de OWASP rompería la regla.
4. **El silencio por la revisión.** Un punto sin disposición, o un `NOT_APPLICABLE` sin razón.
5. **Un hallazgo por una falla de Vu10.** ES0902 pide tener en cuenta la guía, no cero hallazgos.
6. **Un marco que Vu10 no pide.** ASVS, MASVS, SAMM, un scanner o un umbral de vulnerabilidades.

## Qué queda afuera

- **Un check determinístico.** La matriz dice `checks: []` y así queda. La agregación de la review es
  determinística; la review sigue siendo una review.
- **Traer la edición de OWASP de internet.** El harness no tiene un canal HTTP genérico y el registro de
  fuentes (`source-registry.json`) no admite hoy una página web con edición y URL. Vu10 lee la foto de
  la fuente y su frescura como evidencia; ampliar el registro es un cambio aparte, anotado en
  `PENDIENTES-I.md`.
- **La lista de puntos de una edición.** Sale de la foto autoritativa de la fuente, nunca del módulo.
- **ASVS, MASVS, SAMM, un scanner, un producto de pentest o un umbral numérico.** Pueden aportar
  evidencia a un punto; no son exigencia de Vu10.
- **Decidir si un hallazgo bloquea la entrega.** Eso lo dicen las reglas de evaluación de seguridad.
- **Ejecutar pruebas.** El módulo lee la evidencia de una prueba ya hecha y decide si era segura.
- **Un agente, una skill, un check, un algoritmo nuevo en `seguridad.py`, un libro, un dominio o un
  tablero.** Vu10 entra al libro de siempre por `owasp-application-security`, que ya lo nombra.
- **La forma vieja de `_vu10` (`assetTypes` y `owaspGuidance`).** La línea base la verificó (E-27, E-52
  y E-53 de `es0902-linea-base-de-seguridad`) y sigue igual.

## Las decisiones, y por qué

### Las dos reglas que cortaron el ciclo

Dos pasadas del refutador encontraron el mismo defecto con caras distintas. Desde la tercera, todo el
módulo responde a dos reglas y a nada más:

1. **Lo que sostiene lo decide la clase, no lo que el item dice de sí mismo.** `establishes` lo escribe
   quien llena la review; la clase también, pero cada pregunta tiene su tabla de clases y ninguna tabla
   se amplía porque un item diga más cosas. La foto (`AUTHORITATIVE_SOURCE_SNAPSHOT`) y el registro de
   fuentes (`TRUSTED_KNOWLEDGE_REGISTRY`) dicen la fuente y su frescura, y nunca un punto ni un
   hallazgo; las débiles y `RULE_RESULT` no sostienen nada.
2. **Lo que no se pudo leer pesa en todas sus formas.** Mal formado, repetido, sin id, con un `outcome`
   fuera de lo legible, una prueba insegura, o una afirmación que no dice ni sí ni no: si toca la
   pregunta —la señal, un activo, la referencia de una fuente o un punto que se cita—, impide el `PASS`
   y el `NOT_APPLICABLE`. Nunca hace `FAIL`.

### La review se resuelve en código, como la de O1

La review de O1 la resuelve `linea_base.py`, en Python, sin modelo. Vu10 hace lo mismo con un módulo
nuevo, `bin/orquestacion/guia_owasp.py`: toma el registro de la review y el catálogo de evidencia y
devuelve el estado. El modelo puede llenar el registro —disposiciones, razones, evidencia—; nunca
decide el estado. La review se documenta en `controles/reviews/owasp-security-guidance-review.md` y
se registra como `REVIEW`.

### `_vu10` le cede la palabra a la review

Igual que `_vu9` en Vu9: si la evidencia trae el resultado de la review de la fila y no trae la forma
vieja (`assetTypes` ni `owaspGuidance`), `_vu10` va por el genérico y manda la review. Con la forma
vieja, todo sigue como estaba.

### La señal y las familias salen de evidencia

`owaspApplicableAssetPresent` se deriva de las evidencias `OWASP_APPLICABLE_ASSET`:
- **`TRUE`**: una evidencia legible no débil dice `PRESENT`.
- **`FALSE`**: una autoritativa legible dice `ABSENT`, ninguna dice `PRESENT`, el registro no tiene
  activos, el registro valida, y no hay nada ilegible sobre `OWASP_APPLICABLE_ASSET` —mal formado,
  repetido, sin id, con un `outcome` fuera de lo legible, o una afirmación sin `PRESENT` ni `ABSENT`—
  (regla 2).
- **`UNRESOLVED`**: todo lo demás.

Las débiles son `README_STATEMENT`, `AGENT_STATEMENT`, `SKILL_OUTPUT`, `NAMING_CONVENTION` y
`MODEL_KNOWLEDGE`. Las autoritativas del proyecto son `SECURITY_DOCUMENTATION`,
`ARCHITECTURE_DOCUMENTATION`, `PROJECT_REQUIREMENT`, `PROJECT_CONTRACT`, `ASSESSMENT_FINDING` y
`OTHER_AUTHORITATIVE_EVIDENCE`.

Cada activo del registro declara sus `assetTypes`. Un tipo cuenta si una evidencia legible
`ASSET_TYPE` con ese valor nombra el activo, de una clase autoritativa o de `ASSET_INVENTORY`,
`API_SPECIFICATION`, `ROUTE_INVENTORY`, `MOBILE_BUILD_CONFIGURATION` o `APPLICATION_CODE`. Que el
activo sea interno o autenticado no cambia nada: el catálogo acepta `internal` y `authenticated` y el
módulo no los lee. Un tipo declarado sin sostener, o un tipo que la evidencia dice y el registro no
declara, da `OWASP_ASSET_COVERAGE_UNRESOLVED`; también un `ASSET_TYPE` o un `ASSET_INVENTORY` ilegible
que nombra el activo, y un `ASSET_TYPE` que no dice una de las tres familias (regla 2). Sostener un tipo exige una clase de la tabla; contradecirlo no: un `ASSET_TYPE` legible de
cualquier clase no débil que dice un tipo no declarado deja la cobertura sin resolver. También un inventario de activos que no está entero
(`ASSET_INVENTORY: COMPLETE` que nombra todos los activos del registro, y ninguno de más).

Las familias aplicables son la unión de los tipos sostenidos: `WEB`, `API_OR_WEB_SERVICE`, `MOBILE`.
Un activo web con su API aporta las dos.

### La fuente de cada familia

Cada familia de la review declara `source` con `edition`, `sourceRef`, `resolvedAt`,
`sourceFingerprint` y `freshness`. La fuente está resuelta si una evidencia legible
`OWASP_GUIDANCE_SOURCE` de una clase que puede decirlo —`AUTHORITATIVE_SOURCE_SNAPSHOT` o
`TRUSTED_KNOWLEDGE_REGISTRY`— tiene `reference` igual al `sourceRef`, `value` igual a la `edition`,
nombra la familia en `families`, y, si las dos lo traen, el mismo `sourceFingerprint`. La evidencia
trae en `items` los puntos de esa edición. `MODEL_KNOWLEDGE` y las demás débiles nunca lo dicen.
Sin eso, o con `freshness: SOURCE_UNAVAILABLE`, da `OWASP_GUIDANCE_SOURCE_UNAVAILABLE`. Dos fotos que
dicen puntos distintos para la misma fuente y edición dejan la fuente sin resolver.

### La frescura, con el mecanismo de fuentes confiables

La familia está vigente si declara `freshness: CURRENT` y una evidencia legible `SOURCE_FRESHNESS` de
`TRUSTED_KNOWLEDGE_REGISTRY`, con la misma `reference` y la misma `edition` en `version`, dice
`CURRENT`, y nada más sobre esa fuente dice otra cosa: ninguna evidencia legible `SOURCE_FRESHNESS`
**de cualquier clase** dice otro estado u otra edición, y nada ilegible —de la clase que sea, foto
incluida— nombra la referencia. Un `CURRENT` redundante de otra clase, de la misma edición, no la
quita ni la sostiene. Lo que dice "no" pasa por la misma
compuerta que lo que dice "sí" (refutador, pase 1). Si no, da `OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`. Una que dice `UPDATE_AVAILABLE` le quita el `CURRENT` a la foto
vieja, diga lo que diga el registro de la review.

`guia_owasp.evidencia_de_frescura(sid, entrada, referencia, edicion)` traduce una entrada de
`.claude/harness.fuentes.json` —la que escribe `frescura.py`— a ese item: el estado es el que el
mecanismo resolvió, tal cual.

### Los puntos salen de la edición

Los puntos de una familia son los `items` de su foto. La review los tiene que tener todos, cada uno
una vez, y ninguno de más. Un punto que falta, uno repetido o uno que la edición no tiene dan
`OWASP_GUIDANCE_COVERAGE_INCOMPLETE`. El módulo no tiene ninguna lista de puntos, ni un id de OWASP.

### Las disposiciones

| Disposición | Vale si | Si no |
|-|-|-|
| `REVIEWED_NO_FINDING` | cita en `evidenceRefs` al menos una evidencia legible que sostiene | sin resolver |
| `FINDING_PRESENT` | nombra al menos un hallazgo en `findingIds`, y cada uno es un `SECURITY_FINDING` legible del catálogo, de una clase que sostiene (regla 1) | sin resolver |
| `NOT_APPLICABLE_WITH_RATIONALE` | trae `rationale` no vacía y cita al menos una evidencia legible que sostiene | sin resolver |
| `UNRESOLVED` | nunca | sin resolver |

Sostiene un punto un item de una clase que sostiene (regla 1) que establece `GUIDANCE_ITEM_EVIDENCE`.
La foto de OWASP, la frescura o el inventario no son evidencia de haber revisado nada, aunque digan
serlo (refutador, pases 1 y 2). Tampoco
sostienen un punto las débiles, `RULE_RESULT` —el resultado final de otra regla no se copia— ni una
prueba dinámica insegura o sin objetivo. Un nombre en `findingIds` que el catálogo no tiene no es un
hallazgo: el paquete pide un hallazgo real (VU10-29) con su severidad y su confianza. Solo los hallazgos
reales de un `FINDING_PRESENT` salen en `findings` y llegan al reporte; un nombre en otra disposición, o
uno que el catálogo no tiene, queda en `unknownFindingIds` (refutador, pase 3). La evidencia de otra regla sí: un item con
`reusedFrom: "ES0902.Vu5"` sostiene igual que uno propio. Un punto sin resolver da
`OWASP_GUIDANCE_ITEM_UNRESOLVED` y el agregado `REVIEW_INCOMPLETE`.

### Los hallazgos no son la cobertura

`FINDING_PRESENT` es una disposición válida y no hace `FAIL`. La severidad y la confianza viven en el
hallazgo (`SECURITY_FINDING`, con `severity` y `confidence`), y el módulo no las lee para decidir.
`guia_owasp.hallazgos_para_reporte(resultado, catalogo, existentes, …)` arma los eventos por
`reporte_seguridad.productores.desde_hallazgo`: un hallazgo que ya está en el libro se referencia y no
se vuelve a crear, y uno que dos puntos citan sale una sola vez.

### La prueba dinámica es segura o no cuenta

Una `AUTHORIZED_DYNAMIC_TEST` sostiene si `authorized: true`, `environment` en `DEV`, `QA`, `HML` u
`OTHER`, `bounded: true`, `syntheticData: true` y `destructive` no es `true`. Si no, o con
`outcome: UNAVAILABLE`, no sostiene nada: el punto que la cita queda sin resolver.

### Omitir una familia es ignorarla

`FAIL` es una sola cosa: la review está hecha —tiene al menos una familia— y una familia aplicable no
está. Eso es la guía demostrablemente ignorada. La review vacía, como se instala, es
`REVIEW_INCOMPLETE`, y también un registro que el schema rechaza —un punto sin disposición, por
ejemplo— cuando la señal está encendida.

📌 El §9 de la review del paquete dice que también es `FAIL` un punto ignorado o una review no hecha.
Acá un punto que falta es `OWASP_GUIDANCE_COVERAGE_INCOMPLETE` y la review vacía `REVIEW_INCOMPLETE`:
VU10-22 pide solo que un punto omitido impida el `PASS`, y la review vacía del paquete trae
`REVIEW_INCOMPLETE`. La review instalada lo aclara al final.

### El schema propio de la review

`revisiones.py` y `normative-review.schema.json` son la infraestructura de review de G2 y D3: un
registro de hallazgos por práctica. El paquete de Vu10 trae otro contrato —activos, familias, fuente y
puntos— y pide validar contra `owasp-security-guidance-review.schema.json`. Se instala ese, cerrado
en todas las capas. El test E-09 de D3, que contaba un solo schema con `review` en el nombre, pasa a
decir lo que protegía: que D3 no agrega uno propio y reusa el de G2.

### El agregado

Una familia omitida hace `FAIL`, y gana. Sin eso, gana el primer sin resolver de este orden:
`APPLICABILITY_UNRESOLVED`, `OWASP_ASSET_COVERAGE_UNRESOLVED`, `OWASP_GUIDANCE_SOURCE_UNAVAILABLE`,
`OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`, `OWASP_GUIDANCE_COVERAGE_INCOMPLETE`, `REVIEW_INCOMPLETE`. Un
punto sin resolver da `REVIEW_INCOMPLETE` con `OWASP_GUIDANCE_ITEM_UNRESOLVED` en `states`. Lo
ilegible que se cita impide el `PASS`. `PASS` exige todo resuelto, aunque haya hallazgos.

### La refutación atómica apoya y no reemplaza

La refutación compila una unidad de `ES0902.Vu10` por alcance, como con cualquier regla. Un veredicto
`cumple` resuelve esa unidad y no toca la review: el módulo no lee veredictos. Para un punto
semántico, `guia_owasp.alcance_de_punto(familia, punto, activo, paths)` arma el alcance acotado de una
unidad —un punto, un activo, rutas concretas— y rechaza un alcance vacío o del repositorio entero. El
id sigue el patrón de `scope.json` (`^[A-Za-z0-9][A-Za-z0-9._-]*$`): lo que no entra se escribe `-`.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/orquestacion/guia_owasp.py` | La señal, la review, los hallazgos, el alcance y las traducciones |
| `harnesses/desarrollo/controles/reviews/owasp-security-guidance-review.md` | La review |
| `harnesses/desarrollo/controles/policies/owasp-security-guidance-required.md` | La policy |
| `harnesses/desarrollo/reglas/es0902-vu10-governance.md` y `es0902-vu10-owasp-applicable-asset-present-signal.md` | Gobierno y señal, como vinieron |
| `harnesses/desarrollo/reglas/owasp-security-guidance-review.json` | El registro de la review, instalado como vino |
| `comun/schemas/owasp-security-guidance-review.schema.json` | Su contrato: el del paquete, cerrado en todas las capas |
| `harnesses/desarrollo/bin/orquestacion/seguridad.py` | `_vu10` le cede la palabra a la review |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu10` en la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | La policy y la review |
| `docs/seguridad-es0902.md` | Vu10 |
| `tests/casos/59_es0902_vu10_guia_owasp.py` | Los escenarios |
| `tests/casos/28_*.py`, `3[1-7]_*.py`, `39_*.py`, `40_*.py` y los `E-0n` de reviews en disco de `44_` a `58_` | Los contadores: dos controles y una review más |

## Escenarios verificables

El paquete trae la lista `VU10-01` a `VU10-62`. Cada `E-nn` es el `VU10-nn` con el mismo número.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu10`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `owaspApplicableAssetPresent`, `dev-security`, `owasp-security-guidance-required` y
  `owasp-security-guidance-review` están exactos en la matriz, el registro de controles y el módulo.
  · rojo visto: si
- **E-03** — La fila sigue con `checks: []` y no hay ningún check de Vu10 en `controles/checks/`.
  · rojo visto: si
- **E-04** — No hay ningún agente ni skill nuevos, y `ALGORITMOS` sigue en diez. · rojo visto: si

### La aplicabilidad

- **E-05** — Un activo `WEB` sostenido enciende la señal y aporta la familia `WEB`. · rojo visto: si
- **E-06** — Un activo `API_OR_WEB_SERVICE` la enciende y aporta su familia. · rojo visto: si
- **E-07** — Un activo `MOBILE` la enciende y aporta su familia. · rojo visto: si
- **E-08** — Un activo web con su API aporta las dos familias, y la review necesita las dos.
  · rojo visto: si
- **E-09** — Un activo web interno y autenticado cuenta igual. · rojo visto: si
- **E-10** — Un inventario de activos que no está entero, un tipo sin sostener o un tipo ilegible sobre
  el activo dan `OWASP_ASSET_COVERAGE_UNRESOLVED`; el vacío o una evidencia débil dan `APPLICABILITY_UNRESOLVED`.
  · rojo visto: si
- **E-11** — Una ausencia autoritativa de las tres familias, sola, da `NOT_APPLICABLE`, y con algo
  ilegible sobre la pregunta, en cualquiera de sus formas, no.
  · rojo visto: si

### La fuente

- **E-12** — Cada familia aplicable se ata a su foto autoritativa, y la salida lo dice.
  · rojo visto: si
- **E-13** — Una edición que solo sostiene `MODEL_KNOWLEDGE` no resuelve la fuente. · rojo visto: si
- **E-14** — Sin foto, o con `freshness: SOURCE_UNAVAILABLE`, da `OWASP_GUIDANCE_SOURCE_UNAVAILABLE` y
  nunca `PASS`. · rojo visto: si
- **E-15** — Sin frescura sostenida da `OWASP_GUIDANCE_FRESHNESS_UNRESOLVED` y nunca `PASS`.
  · rojo visto: si
- **E-16** — La edición sale en la salida de la familia. · rojo visto: si
- **E-17** — La fecha, la referencia y la huella de la fuente salen en la salida cuando están.
  · rojo visto: si
- **E-18** — Una frescura `UPDATE_AVAILABLE`, de cualquier clase, o una ilegible sobre la fuente, le
  quita el `CURRENT` a la foto vieja, y la traducción de
  una entrada de `harness.fuentes.json` lleva el estado tal cual. · rojo visto: si

### Los puntos

- **E-19** — Los puntos esperados de una familia son los de su foto. · rojo visto: si
- **E-20** — El módulo no tiene ninguna lista de puntos ni ids de OWASP, y otra edición con otros
  puntos llega a `PASS` sin tocar nada. · rojo visto: si
- **E-21** — Un punto repetido, uno que la edición no tiene o uno sin disposición impide el `PASS`. · rojo visto: si
- **E-22** — Un punto que falta da `OWASP_GUIDANCE_COVERAGE_INCOMPLETE`. · rojo visto: si
- **E-23** — `REVIEWED_NO_FINDING` con evidencia de punto vale; sin evidencia, o citando la foto de
  OWASP, no. · rojo visto: si
- **E-24** — `FINDING_PRESENT` con su hallazgo vale como disposición, y con un hallazgo que el
  catálogo no tiene, no. · rojo visto: si
- **E-25** — `NOT_APPLICABLE_WITH_RATIONALE` sin razón no vale. · rojo visto: si
- **E-26** — `NOT_APPLICABLE_WITH_RATIONALE` sin evidencia tampoco, y la review instalada no trae
  ninguna disposición por defecto. · rojo visto: si
- **E-27** — Un punto `UNRESOLVED` impide el `PASS`. · rojo visto: si

### Los hallazgos

- **E-28** — Una review completa con un hallazgo no es `FAIL`. · rojo visto: si
- **E-29** — Un hallazgo nuevo sale como `FINDING_CREATED` de `ES0902.Vu10` por `desde_hallazgo`, y uno
  que ya está en el libro no se vuelve a crear. · rojo visto: si
- **E-30** — La severidad del hallazgo no cambia el estado de la review. · rojo visto: si
- **E-31** — La confianza viaja en el hallazgo y no cambia el estado de la review. · rojo visto: si
- **E-32** — Un hallazgo que bloquea sale con `blocking` en el libro, y la review sigue en `PASS`.
  · rojo visto: si

### Los marcos que Vu10 no pide

- **E-33** — ASVS no se exige: el módulo no lo nombra y se llega a `PASS` sin él. · rojo visto: si
- **E-34** — MASVS tampoco. · rojo visto: si
- **E-35** — SAMM tampoco. · rojo visto: si
- **E-36** — Ningún scanner: el módulo no nombra ninguno y ninguna clase de evidencia es obligatoria.
  · rojo visto: si
- **E-37** — Ningún umbral: el módulo no tiene números de vulnerabilidades, y diez hallazgos siguen en
  `PASS`. · rojo visto: si

### La evidencia de otras reglas

- **E-38** — Evidencia de Vu5 sostiene un punto. · rojo visto: si
- **E-39** — El `PASS` de Vu5 no pone en `PASS` a Vu10, y un `RULE_RESULT` no sostiene un punto.
  · rojo visto: si
- **E-40** — Evidencia de Vu8 sostiene un punto. · rojo visto: si
- **E-41** — El `PASS` de Vu8 no pone en `PASS` a Vu10. · rojo visto: si
- **E-42** — Evidencia de Vu9 sostiene un punto. · rojo visto: si
- **E-43** — El `PASS` de Vu9 no pone en `PASS` a Vu10. · rojo visto: si
- **E-44** — Un hallazgo que dos puntos citan sale una sola vez. · rojo visto: si

### La review y la refutación atómica

- **E-45** — Vu10 es una review: está registrada como `REVIEW`, con su documento, y la fila no tiene
  checks. · rojo visto: si
- **E-46** — Un veredicto `cumple` de la refutación no pone la review en `PASS`. · rojo visto: si
- **E-47** — Un punto semántico arma un alcance de una unidad con un punto, un activo y sus rutas, y
  compila a una sola unidad de `ES0902.Vu10`. · rojo visto: si
- **E-48** — Un alcance vacío o del repositorio entero se rechaza, y un veredicto con evidencia fuera
  del alcance también. · rojo visto: si
- **E-49** — Un veredicto guardado no se reusa cuando cambia la huella de la evidencia. · rojo visto: si

### La prueba dinámica

- **E-50** — El módulo no importa nada que abra una conexión o un proceso, y no escribe archivos.
  · rojo visto: si
- **E-51** — Una prueba en `PRD` o destructiva no sostiene nada. · rojo visto: si
- **E-52** — Una prueba sin objetivo, o no autorizada, deja el punto sin resolver. · rojo visto: si
- **E-53** — Lo que la regla de salida compartida reconoce como credencial no sale en la salida, la
  unidad ni el libro, y el schema no admite un campo de más. · rojo visto: si

### El agregado

- **E-54** — La review completa sin hallazgos da `PASS`. · rojo visto: si
- **E-55** — La review completa con un hallazgo registrado puede dar `PASS`. · rojo visto: si
- **E-56** — Una familia aplicable omitida en una review hecha da `FAIL`. · rojo visto: si
- **E-57** — Sin frescura no hay `PASS`, aunque todo lo demás esté completo. · rojo visto: si
- **E-58** — Un punto material sin resolver da `REVIEW_INCOMPLETE`. · rojo visto: si
- **E-59** — El módulo no llama a ningún modelo: no importa nada fuera de la biblioteca estándar y del
  harness. · rojo visto: si
- **E-60** — La misma evidencia da el mismo resultado en cualquier orden, también con ids en NFC.
  · rojo visto: si
- **E-61** — La trazabilidad `ES0902 / 6.2 / 6 / Vu10` viaja en todo resultado y en `rules.Vu10`.
  · rojo visto: si
- **E-62** — La salida entra como `RULE_EVALUATION` de `ES0902.Vu10` al libro de siempre, en
  `owasp-application-security`, y `reporte_seguridad/` no tiene ningún archivo nuevo.
  · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/59_es0902_vu10_guia_owasp.py`, con el id en el
título. Ninguno lleva `· verificación: lectura`: la review la llena quien sea, y lo que se verifica es
la agregación determinística, no una corrida de un modelo.

## Riesgos conocidos

- **La foto de la fuente la trae alguien.** Sin canal HTTP, una foto con puntos equivocados y marcada
  `AUTHORITATIVE_SOURCE_SNAPSHOT` sostiene la review. La frescura del mecanismo de fuentes es lo único
  que la contrasta, y hoy ninguna fuente OWASP está en `source-registry.json`.
- **Una disposición con evidencia no prueba que la evidencia diga lo que la disposición dice.** El
  módulo cuenta y ata; juzgar si la evidencia alcanza es la parte semántica de la review.
- **Casi todo proyecto real va a quedar en `OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`** hasta que el registro
  de fuentes admita las páginas de OWASP.
- **La edición de OWASP no entra en la clave de caché de la refutación.** VU10-49 habla de la huella de
  la evidencia o de la fuente; `refutacion.clave_de_cache` solo ve rutas y revisión. Si cambia la
  edición y no cambian las rutas, un veredicto guardado se reusa. No mueve la review, que no lee
  veredictos (E-46) y vuelve a pedir foto y frescura en cada evaluación.
