# Bloque 3 — la refutación atómica

**Estado:** verificado y cerrado · **Fecha:** 25-09-2026 · **Bloque:** 3, leyendo al 4

## Qué problema resuelve

`dev-refutador` hace hoy **una pasada exhaustiva por lote** y **una invocación por lote**. Recibe
el conjunto, lo revisa entero y devuelve una tabla Markdown. Eso tiene tres costos:

- Cada revisión vuelve a descubrir qué reglas aplican, cuando el plan (`.claude/planes/<KEY>.json`)
  ya lo dice en `workUnits[].normative`.
- Una regla que un check determinista ya resolvió vuelve a pasar por un modelo.
- Una afirmación que no cambió desde la revisión anterior se vuelve a pagar entera, porque no hay
  nada que ate un veredicto a los bytes que miró.

Además, la tabla es prosa: nadie la valida, nadie la agrega y nada impide que un `cumple` sin cita
viaje con el sello puesto.

Este cambio convierte esa pasada en una **tubería determinista primero**:

```
plan → compilador → RefutationUnit[] → check concluyente | caché exacta | dev-refutador
     → veredicto validado → agregador → resumen en español + resultado de máquina
```

El paquete de entrada son `atomic-refutation-governance.md` y `dev-refutador-v2-atomic-contract.md`.
Los tres `refutation-*.schema.json` que el paquete nombraba **no venían**: se escriben acá, dentro del
subconjunto que interpreta `contexto-armar.py`.

## Qué queda afuera

- **Otro refutador, otra skill, un refutador por estándar.** Lo prohíbe el paquete. `dev-refutador`
  sigue siendo el único, `CRITIC_AGENT`, con cero skills en el registro.
- **Migrar `orchestration-plan/1.0`.** La refutación es una capa derivada, posterior a la ejecución.
  El plan no gana ni pierde un campo.
- **Invocar al modelo desde el harness.** El harness compila, entrega una unidad, valida lo que
  vuelve, lo guarda y agrega. Quien corre `dev-refutador` sigue siendo la sesión de Claude Code,
  igual que hoy.
- **Un ejecutor que atribuya archivos a una unidad de trabajo.** No existe. El alcance entra por un
  archivo que declara quien ejecutó (`scope.json`) y, si no está, la unidad queda bloqueada. No se
  infiere nada del diff.
- **Un objetivo de rendimiento.** El paquete pide medir antes de fijar uno. Este cambio deja los
  contadores y el corte del Bloque 4 por fase; la línea de base se mide con corridas reales.
- **Un segundo libro de seguridad o un reporte de seguridad de la refutación.** Un veredicto de
  ES0902 entra al libro que ya existe, por un productor nuevo.
- **Una corrida real de `dev-refutador` sobre una unidad.** El sujeto sería una corrida de un
  modelo. Lo que la suite sí prueba es la frontera: qué recibe, qué se le acepta y qué se rechaza.
  Queda como pendiente de lectura (ver `## Riesgos conocidos`).

## Las decisiones, y por qué

### La clave atómica es (unidad de trabajo, regla, alcance)

Una regla distinta es una unidad distinta. Un alcance distinto, también. Nunca una unidad por línea
de código.

Las reglas salen de `normative.standards.<ESTÁNDAR>` de cada unidad del plan. Si un plan viejo no
trae `standards`, salen del bloque de arriba (ES0901). La clave de regla es la global compuesta:
`ES0901.G1`, `ES0902.Vu4`.

- Una regla en `applicableRules` es una unidad a verificar.
- Una regla en `unresolvedRules` también es una unidad, pero **bloqueada** con
  `REFUTATION_RULE_UNRESOLVED`. No se sabe si aplica, así que no se puede decir que cumple. Esconderla
  daría `PASS` sobre un plan que no terminó de clasificarse.
- Una regla en `notApplicableRules` no genera unidad.

El id es `REF-001`, `REF-002`… en el orden de `(workUnitId, ruleKey, scopeId)`. Mismas entradas, mismos
ids.

### El alcance se declara, no se descubre

El plan no dice qué archivos tocó cada unidad de trabajo. Lo tiene que decir quien ejecutó, en
`.claude/refutaciones/<KEY>/scope.json`. Por cada unidad de trabajo trae una lista de alcances. Cada
alcance tiene:

- `scopeId`
- `source`
- `paths`
- opcionalmente, `rules`, para limitarlo a algunas reglas

Las fuentes, de mayor a menor prioridad:

| `source` | Qué es |
|---|---|
| `workUnitFiles` | archivos atribuidos explícitamente a la unidad |
| `changedFiles` | archivos cambiados que alguien mapeó a esa unidad |
| `projectContext` | rutas de `architecture.important_paths` de `docs/codebase/project-context.json` |
| `executionEvidence` | rutas de evidencia que entregó la ejecución |

Para cada par (unidad, regla) se usan los alcances de la fuente más prioritaria que tenga alguno. Los
de fuentes más bajas se descartan.

`projectContext` necesita que cada ruta figure en `important_paths`. Los componentes de
`project-context/1.1` no traen rutas, y mapear un componente a archivos sería inventar.

Una ruta sirve si cumple todo esto:

- es relativa a la raíz del proyecto
- usa `/`
- no tiene `..`, comodines ni ruta absoluta
- no es `.` ni la raíz
- existe
- no parece un secreto: `.env*`, `secrets/`, `*.pem`, `*.key`, `*.pfx`, `*.p12`, `id_rsa*`

Un directorio se expande a sus archivos, en orden estable y sin `.git`. Un alcance de más de 200
archivos no es la evidencia de una regla: es un barrido con otro nombre, y no sirve.

**Una ruta que no sirve invalida su alcance entero.** El alcance no se achica: queda
`EVIDENCE_SCOPE_UNRESOLVED`. Si una regla se queda sin alcance, la unidad queda `BLOCKED` con
`REFUTATION_SCOPE_UNRESOLVED`. **Nunca se cae al repositorio entero.**

### La huella es de los bytes, no de `HEAD`

`repoRevision` es `git rev-parse HEAD`, o `null` si el proyecto no es un repositorio. No alcanza:
con un archivo modificado, `HEAD` no cambia.

`evidenceFingerprint` es el `sha256` de la lista ordenada de `(ruta, sha256 de sus bytes)` del
alcance. Un archivo tocado, en stage o no, cambia la huella.

Cuando un veredicto sale de un check, lleva además `checkEvidenceFingerprint`, que es la huella del
resultado del check.

### El check va primero, y cierra solo en un caso

Los resultados de checks entran por `.claude/refutaciones/<KEY>/checks.json`: los escribe quien
corrió los checks. Un resultado cierra la unidad sin modelo (`resolutionPath =
DETERMINISTIC_CHECK`) solo si se cumplen las seis condiciones:

1. El control es un `CHECK` `INSTALLED` de `control-registry.json`.
2. El control está atado a la misma `ruleKey`, por `source` o por `normativeSources`.
3. El control figura en los `checks` de la regla en la matriz, y en `declaredChecks` o
   `requiredChecks` de la unidad de trabajo.
4. Su `evidenceFingerprint` y su `repoRevision` son los de la unidad **ahora**.
5. Su estado es concluyente: `PASS` o `FAIL`.
6. La regla no declara `reviews` en la matriz.

Además, para `cumple` tienen que estar en `PASS` todos los checks instalados que la matriz declara para
esa regla. Un solo `FAIL` actual alcanza para `incumple`.

Si falta cualquiera de las seis, la unidad va a refutación semántica con los checks adjuntos como
referencia. **Un check sin resolver nunca se convierte en `cumple`.** Un check de otra regla no
cierra nada.

### La caché es exacta

La caché vive en `.claude/refutaciones/cache/<hex>.json`. La clave es el `sha256` del JSON canónico
de:

- la versión del schema
- la afirmación canónica
- el estándar, su versión y la regla
- la huella de la skill (los bytes de su `SKILL.md`)
- la huella de la fuente normativa (la entrada de la regla en la matriz, con su versión)
- `evidenceFingerprint`
- `repoRevision`
- la versión y la huella del contrato de `dev-refutador`

Se reusan `cumple` e `incumple`. `sin-verificar` no se reusa: lo que no se pudo ver puede verse la
próxima vez.

Un acierto de caché copia el veredicto original, con sus `evidence` y sus huellas, y lo marca
`resolutionPath = CACHE`. Una entrada que no valida, que dice otra clave o que no coincide en una
huella es `REFUTATION_CACHE_INVALID`. No se usa, se avisa, y la unidad sigue a refutación semántica.

### El refutador recibe una unidad y devuelve un objeto

`refute <KEY> --unit REF-001` imprime exactamente una `refutation-unit/1.0`. `dev-refutador` lee la
skill nombrada y los archivos de `evidenceScope.paths`, y nada más. Devuelve un solo objeto JSON
`refutation-verdict/1.0`, sin prosa alrededor.

`refute <KEY> --record <verdict.json>` lo acepta solo si pasa todas estas pruebas:

- el archivo es un objeto JSON y nada más: un bloque de código o una frase antes lo invalidan
- valida contra el schema
- la unidad existe y está pendiente de refutación semántica
- `ruleKey`, `workUnitId`, `cacheKey`, `evidenceFingerprint` y `repoRevision` son los de la unidad
- la huella **recalculada ahora** sigue siendo la de la unidad
- `cumple` e `incumple` traen una cita de la skill de la unidad y un locator, y al menos una evidencia
  con ruta **dentro del alcance**, línea ≥ 1 y lo observado
- `sin-verificar` trae su motivo y qué hay que abrir o correr para cerrarlo
- no trae campos que solo escribe el harness: `resolutionPath`, `cacheHit`, `recordedAt`

Si la huella cambió, el error es `REFUTATION_EVIDENCE_STALE`. Si falla cualquier otra prueba, es
`REFUTATION_OUTPUT_INVALID`. En los dos casos **no se guarda nada** y el comando sale con 2.

El texto observado pasa por la limpieza de secretos del Bloque 2 y se recorta a 300 caracteres.

### Los avisos de la corrida son de máquina

`run.json` sale tal cual por `--status --json`, así que sus `warnings` son códigos:
`REFUTATION_CHECK_UNRESOLVED:REF-002`, `REFUTATION_EVIDENCE_STALE:wu-1:ES0902.Vu4`. El schema de la
corrida exige ese patrón. La frase en español la arma el renderizador de `--summary`. Lo pidió el
refutador: los avisos iban en español sin tildes y se colaban en la salida de máquina.

### El agregador no llama a nadie

| Condición | Estado |
|---|---|
| Cero unidades | `NOTHING_TO_VERIFY` |
| Algún `incumple` | `FAIL` |
| Todo `cumple` | `PASS` |
| Cualquier otro caso | `INCOMPLETE` |

Una unidad sin veredicto (bloqueada o pendiente) cuenta como `sin-verificar`.

Los contadores son `cumple`, `incumple`, `sinVerificar`, `cacheHits`, `checkResolved`,
`semanticRuns`, `pending` y `blocked`.

### El micro-lote es de transporte

`--unit REF-001,REF-002` entrega varias unidades en un solo sobre, pero solo si comparten `ruleKey`,
`skillId`, `evidenceFingerprint`, `repoRevision` y `verificationMode`. `--record` acepta entonces un
arreglo con **un veredicto por unidad**, sin ids repetidos, y lo valida uno por uno contra el mismo
criterio de lote. Si falla uno, no se guarda ninguno. Dos reglas distintas nunca van juntas.

### El Bloque 4 se reusa, no se extiende

El schema de eventos no cambia. Se agregan cuatro claves a la lista cerrada de `metadata` de
`contabilidad/eventos.py`: `phase`, `refutationUnitId`, `resolutionPath` y `cacheHit`. Es una lista
de código; el schema ya admitía el objeto.

Las cuatro se cierran **por valor**, no solo por nombre:

| Clave | Admite |
|---|---|
| `phase` | `refutation` |
| `resolutionPath` | `SEMANTIC_REFUTATION` |
| `cacheHit` | `false`, y nada más |
| `refutationUnitId` | `REF-` y de 3 a 6 dígitos |

Hay dos razones:

- **El techo del evento.** El Bloque 4 publica que el contenido de un evento no llega a 10.000
  caracteres, y `30_b4_contabilidad.py` lo clava. Cuatro claves de texto libre de 300 caracteres lo
  romperían. Cerradas por valor, el techo pasa de 9.643 a 9.725 y se re-mide en ese mismo test.
- **Nadie puede escribir un acierto de caché como llamada.** Un evento con `cacheHit: true` no se
  puede construir.

`contabilidad <KEY> --ingerir <fuente> --refutacion REF-001` atribuye lo ingerido así:

- `workUnitId` = la unidad de trabajo original
- `agentId` = `dev-refutador`
- `metadata` = `{phase: refutation, refutationUnitId, resolutionPath: SEMANTIC_REFUTATION,
  cacheHit: false}`

Un `--unidad` o un `--agente` que contradigan a la unidad son un error.

Ni un acierto de caché ni un check escriben eventos: **no hubo llamada**, y un evento de cero tokens
diría que la hubo y fue gratis.

`refute --summary` muestra, si el libro existe, lo que el Bloque 4 tiene con `phase = refutation`:

- eventos
- tokens de input y de output
- tiempo de pared y de modelo
- costo real y equivalente de API

### Seguridad, por el camino que ya existe

`seguridad <KEY> --refutacion` pasa los veredictos de unidades `ES0902.*` por
`productores.desde_refutacion` al libro de seguridad de siempre. Cada uno entra como
`REVIEW_EVALUATION`, con `PASS`, `FAIL` o `UNRESOLVED`.

No es `RULE_EVALUATION`: el resumen de seguridad saca el resultado de una regla solo de ahí, y un
veredicto semántico no puede fijarlo. No se crea ningún archivo de seguridad bajo
`.claude/refutaciones/`.

### Lo que cambia en `dev-refutador.md`, y lo que no

Se mantiene:

- identidad, id y descripción
- `tools: Read, Grep, Glob, Skill`
- no corrige, no refactoriza, no recomienda
- la norma sale solo de skills `dev-*`
- `project-context` es evidencia, nunca norma
- tres veredictos
- la regla de que no hay `cumple` sin cita y sin línea

Se reemplaza:

- «Una pasada exhaustiva por lote» y «Una invocación por lote» pasan a **un alcance semántico acotado
  por RefutationUnit**
- la tabla Markdown pasa a **un objeto `refutation-verdict/1.0`**; la presentación la hace el
  renderizador

Esto pisa el E-05 de `docs/cambios/dev-refutador-lee-el-contrato/spec.md`, que pedía una columna
`repo_revision` en la tabla. `repoRevision` sigue viajando, ahora como campo del veredicto. El test de
ese escenario se ajusta y nombra este cambio.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/refutation-unit.schema.json` | La unidad, el `scope.json` y el `checks.json` (en `$defs`) |
| `comun/schemas/refutation-verdict.schema.json` | El veredicto: lo que devuelve el modelo más lo que agrega el harness |
| `comun/schemas/refutation-run.schema.json` | La corrida: unidades, agregado y avisos |
| `harnesses/desarrollo/bin/orquestacion/refutacion.py` | Compilador, alcance, huellas, checks, caché, validación, agregación, micro-lote, atribución, render |
| `harnesses/desarrollo/bin/dev-harness.py` | `refute <KEY> --compile\|--status\|--unit\|--record\|--summary`; `contabilidad --refutacion`; `seguridad --refutacion` |
| `harnesses/desarrollo/bin/contabilidad/eventos.py` | Cuatro claves más de `metadata` |
| `harnesses/desarrollo/bin/reporte_seguridad/productores.py` | `desde_refutacion` |
| `harnesses/desarrollo/agents/dev-refutador.md` | El contrato atómico, en el mismo archivo |
| `.gitignore` | `.claude/refutaciones/` |
| `tests/casos/55_refutacion_atomica.py` | Los escenarios de abajo |
| `tests/casos/16_refutador_contrato.py` | E-05 de ese cambio pasa a exigir `repoRevision` en el objeto |
| `tests/casos/30_b4_contabilidad.py` | El techo re-medido y las claves acotadas en E-37 de ese cambio |

## Escenarios verificables

Cada `E-nn` es el `AR-0nn` del paquete, con el mismo número.

### Un refutador, ninguna skill nueva

- **E-01** — El registro de agentes tiene un solo agente de dominio `refutation` en el harness de
  desarrollo, `dev-refutador`, y en `agents/` no hay otro archivo `dev-refutador*`. · rojo visto: si
- **E-02** — No existe ninguna skill cuyo nombre contenga `refut` ni `atomic`, ni en el registro ni en
  disco. · rojo visto: si
- **E-03** — El registro de agentes valida, y `dev-refutador` sigue `CRITIC_AGENT` con cero skills.
  · rojo visto: si
- **E-04** — `orchestration-plan.schema.json` no nombra `refut` en ningún campo, y un plan armado por
  `plan.armar` valida y se compila sin tocarlo: sus bytes son los mismos antes y después de
  `--compile`. · rojo visto: si

### El compilador

- **E-05** — Una unidad de trabajo con una regla aplicable y un alcance da una sola RefutationUnit,
  con `workUnitId`, `ruleKey`, `skillId` y `evidenceScope.paths`. · rojo visto: si
- **E-06** — Dos reglas aplicables con el mismo alcance dan dos unidades, con `ruleKey` distintas.
  · rojo visto: si
- **E-07** — La misma regla con dos alcances distintos da dos unidades, con `scopeId` distintos y la
  misma `ruleKey`. · rojo visto: si
- **E-08** — Sin `scope.json`, ninguna unidad tiene rutas en `evidenceScope.paths`. Con un alcance `.`,
  tampoco: nunca el repositorio entero. · rojo visto: si
- **E-09** — Una unidad sin alcance resoluble sale con `scopeState = EVIDENCE_SCOPE_UNRESOLVED`,
  `status = BLOCKED` y `failure = REFUTATION_SCOPE_UNRESOLVED`, y la corrida no es `PASS`.
  · rojo visto: si
- **E-10** — Dos `--compile` seguidos sobre las mismas entradas dejan `run.json` y `units/*.json`
  idénticos byte a byte. · rojo visto: si

### Check primero

- **E-11** — Un resultado de check que cumple las seis condiciones cierra la unidad con
  `resolutionPath = DETERMINISTIC_CHECK`, y la unidad no queda pendiente de refutación semántica.
  · rojo visto: si
- **E-12** — Un check en un estado no concluyente (p. ej. `APPLICABILITY_UNRESOLVED`) nunca da
  `cumple`: la unidad queda pendiente de refutación semántica. · rojo visto: si
- **E-13** — Un check `PASS` con `evidenceFingerprint` o `repoRevision` distintos a los actuales no
  cierra la unidad. · rojo visto: si
- **E-14** — Una regla con `reviews` en la matriz va a refutación semántica aunque su check esté en
  `PASS` actual. · rojo visto: si
- **E-15** — Un check `PASS` actual cuyo control está atado a otra regla no cierra la unidad.
  · rojo visto: si

### La frontera del refutador

- **E-16** — `refute --unit REF-001` imprime un solo objeto que valida contra
  `refutation-unit/1.0`. Sobre una unidad `BLOCKED` o ya resuelta, sale con 2. · rojo visto: si
- **E-17** — `--record` rechaza con `REFUTATION_OUTPUT_INVALID` un veredicto con una evidencia fuera
  de `evidenceScope.paths`, y `dev-refutador.md` dice que no se lee fuera del alcance.
  · rojo visto: si
- **E-18** — `--record` rechaza un veredicto con una `ruleKey` distinta a la de la unidad, y el agente
  dice que no descubre otras reglas ni agrega una segunda afirmación. · rojo visto: si
- **E-19** — `dev-refutador.md` sigue con `tools: Read, Grep, Glob, Skill` exactamente, y sigue
  diciendo que no corrige, no refactoriza y no propone parches. · rojo visto: si
- **E-20** — Un `cumple` sin cita o sin evidencia con línea se rechaza. La regla «Nunca declares
  `cumple` sin poder citar la regla con su página y señalar la línea» sigue una sola vez en el agente.
  · rojo visto: si
- **E-21** — Un `sin-verificar` con motivo `RULE_NOT_CITABLE` y lo que hay que abrir se acepta, y la
  unidad cuenta como `sin-verificar`. Un `cumple` sin cita no se acepta en su lugar.
  · rojo visto: si
- **E-22** — Un `sin-verificar` con motivo `EVIDENCE_INSUFFICIENT` se acepta. Un `sin-verificar` sin
  motivo o sin lo que hay que abrir se rechaza. · rojo visto: si
- **E-23** — Un `incumple` sin evidencia concreta dentro del alcance se rechaza. · rojo visto: si
- **E-24** — Todo veredicto guardado en `verdicts/` valida contra `refutation-verdict/1.0`.
  · rojo visto: si
- **E-25** — Un veredicto envuelto en prosa, en un bloque ```` ```json ```` o con JSON roto se rechaza
  con `REFUTATION_OUTPUT_INVALID` y no se guarda. · rojo visto: si

### Huellas e invalidación

- **E-26** — Cambiar un byte de un archivo del alcance cambia `evidenceFingerprint`. · rojo visto: si
- **E-27** — Con `HEAD` igual y un archivo del alcance modificado después de `--compile`, `--record`
  sale con `REFUTATION_EVIDENCE_STALE` y no guarda nada. Un veredicto ya guardado deja de valer en el
  `--compile` siguiente. · rojo visto: si
- **E-28** — Un `repoRevision` distinto da otra `cacheKey`. · rojo visto: si
- **E-29** — Un `SKILL.md` distinto da otra `cacheKey`. · rojo visto: si
- **E-30** — Una entrada de matriz distinta para la regla da otra `cacheKey`. · rojo visto: si
- **E-31** — Un `dev-refutador.md` distinto da otra `cacheKey`. · rojo visto: si

### La caché

- **E-32** — Un `cumple` registrado se reusa en otra tarea con las mismas entradas: `resolutionPath =
  CACHE`, `cacheHit = true`, y las `evidence` y huellas originales. · rojo visto: si
- **E-33** — Un `incumple` registrado se reusa igual. · rojo visto: si
- **E-34** — Un `sin-verificar` registrado no se reusa: la otra tarea queda pendiente de refutación
  semántica. · rojo visto: si
- **E-35** — Un acierto de caché no escribe ningún evento en el libro del Bloque 4.
  · rojo visto: si
- **E-36** — Una entrada de caché adulterada (otra `cacheKey`, una huella cambiada o JSON roto) no se
  usa, y la corrida lo avisa con `REFUTATION_CACHE_INVALID`. · rojo visto: si

### El agregador

- **E-37** — `refutacion.py` no importa ningún cliente de modelo ni hace red: no aparece `anthropic`,
  `openai`, `urllib`, `http.client`, `requests` ni `socket`. · rojo visto: si
- **E-38** — Todas las unidades en `cumple` dan `PASS`. · rojo visto: si
- **E-39** — Un `incumple` da `FAIL`, aunque haya unidades sin resolver. · rojo visto: si
- **E-40** — Sin `incumple` y con alguna sin resolver, da `INCOMPLETE`. · rojo visto: si
- **E-41** — Cero unidades da `NOTHING_TO_VERIFY`. · rojo visto: si
- **E-42** — Los contadores salen iguales al agregar dos veces, y al agregar con las unidades en otro
  orden. · rojo visto: si

### El Bloque 4

- **E-43** — `contabilidad --ingerir … --refutacion REF-001` escribe eventos con el `workUnitId`
  original de la unidad. · rojo visto: si
- **E-44** — Esos eventos llevan `metadata.phase = refutation`, `refutationUnitId`, `resolutionPath =
  SEMANTIC_REFUTATION` y `cacheHit = false`. · rojo visto: si
- **E-45** — Llevan `agentId = dev-refutador`, y un `--agente` distinto con `--refutacion` sale con 2.
  · rojo visto: si
- **E-46** — Una tarea resuelta toda por caché no tiene libro del Bloque 4, ni un evento con
  `cacheHit = true`. · rojo visto: si
- **E-47** — Una tarea resuelta toda por checks no tiene libro del Bloque 4. · rojo visto: si

### El micro-lote

- **E-48** — Dos unidades de reglas distintas no forman lote: `--unit` con las dos sale con 2.
  · rojo visto: si
- **E-49** — Dos unidades de la misma regla con huellas distintas no forman lote. · rojo visto: si
- **E-50** — Un lote válido sale de `--unit` con sus dos unidades. `--record` de un arreglo guarda
  un veredicto por unidad: con un id repetido o con uno inválido no guarda ninguno, y con los dos
  válidos guarda los dos. · rojo visto: si

### Lo que no cambia

- **E-51** — `plan <KEY> --propuesta` da el mismo plan, salvo la fecha, con y sin una carpeta
  `.claude/refutaciones/` presente. · rojo visto: si
- **E-52** — `comun/hooks/session-start.py` y `comun/hooks/lib/bienvenida.py` no nombran `refut`.
  · rojo visto: si
- **E-53** — `refute --compile` y `--record` no escriben nada bajo `.claude/runtime/security/`.
  · rojo visto: si
- **E-54** — `seguridad <KEY> --refutacion` escribe en el libro de seguridad existente un
  `REVIEW_EVALUATION` por cada veredicto de una unidad `ES0902.*`, con la regla en `normative.rule`, y
  ninguno por las de `ES0901.*`. · rojo visto: si
- **E-55** — No hay ningún `security` ni `ledger` bajo `.claude/refutaciones/` después de una corrida
  completa, y en el harness no hay un segundo módulo de libro de seguridad. · rojo visto: si

### Presentación y datos

- **E-56** — `--summary` sin `--json` imprime en español: «Refutación», «cumple», «incumple»,
  «sin verificar», «Estado». · rojo visto: si
- **E-57** — `--summary --json` y `--status --json` usan los estados canónicos (`PASS`, `FAIL`,
  `INCOMPLETE`, `NOTHING_TO_VERIFY`, `cumple`, `incumple`, `sin-verificar`) y nada en español fuera de
  esos tres, también con avisos presentes: cada aviso de `run.json` es `CÓDIGO:sujeto`, sin prosa, y
  el schema de la corrida no admite otro. · rojo visto: si
- **E-58** — Ningún archivo bajo `.claude/refutaciones/` tiene claves `prompt`, `messages`,
  `conversation` ni `transcript`, y el schema del veredicto no admite claves de más.
  · rojo visto: si
- **E-59** — Un token con forma de secreto en el `observed` de un veredicto sale redactado en el
  archivo guardado, y una ruta `.env` en el alcance deja la unidad `BLOCKED`. · rojo visto: si
- **E-60** — Ninguna unidad compilada tiene más rutas que las que declaró su alcance: un alcance
  inválido deja cero rutas, no las del repositorio. · rojo visto: si
- **E-61** — `.\tests\Invoke-Tests.ps1` sale con 0 con los tests nuevos adentro. · rojo visto: no consta

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/55_refutacion_atomica.py`. E-61 es la suite
misma.

Ninguno lleva `· verificación: lectura`. Los que hablan del refutador (E-16 a E-25) tienen como sujeto:

- el texto de `dev-refutador.md`
- lo que `--unit` entrega
- lo que `--record` acepta o rechaza

Los tres son deterministas. Qué hace de verdad una corrida del modelo queda afuera (ver abajo).

## Riesgos conocidos

- **La frontera no prueba la corrida.** `--record` rechaza evidencia fuera del alcance, pero no puede
  saber si el modelo *leyó* un archivo fuera del alcance y citó solo los de adentro. La defensa
  mecánica llega hasta lo que se cita. Una lectura de corridas reales queda como pendiente.
- **`scope.json` y `checks.json` los escribe alguien.** Un alcance mal atribuido da un veredicto
  correcto sobre los archivos equivocados. El harness garantiza que el veredicto sea de esos bytes, no
  que esos bytes sean los correctos.
- **Muchas unidades bloqueadas al principio.** Casi todas las reglas de un plan real salen
  `APPLICABILITY_UNRESOLVED`, y cada una da una unidad `BLOCKED`. El estado va a ser `INCOMPLETE`
  hasta que haya señales. Es lo honesto, pero se va a ver.
- **La huella de la skill es la de su archivo.** Un cambio de formato en `SKILL.md` invalida la caché
  de todas sus reglas. Es caro, pero es seguro.
