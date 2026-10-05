# Verificación — Modelo de dominio canónico: qué conceptos tiene HARNESS, qué significa cada uno y dónde termina

**Estado:** cerrado en la tercera verificación (05-10-2026) · **Fecha:** 03-10-2026 · **Versión:** 0.30.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 03-10-2026,
en dos contextos propios, sin el de la construcción. Usó
[informe-de-construccion.md](informe-de-construccion.md) solo como mapa.

| | |
|---|---|
| Verificó | `harness-spec-refuter`, en dos partes. La parte 1 cubre la verdad semántica, los escenarios del documento y los estáticos. La parte 2, el comportamiento, la compatibilidad y la compuerta |
| Línea de base | `4c6f0f3`. Es `HEAD`, y su `VERSION` dice 0.29.0. Los dos casos `64_*` la sacan con `git archive` en cada corrida (`64_modelo_de_dominio.py:193-209`; `64-modelo-de-dominio-instalador.ps1:263-278`), sin fixtures versionados |
| Árbol verificado | el árbol de trabajo sin commitear sobre `4c6f0f3`, con 32 entradas en `git status`. Quedó igual después de verificar |
| Registró | la sesión que construyó, con `write-a-verdict`. No agregó veredictos propios |

**Resultado: 48 escenarios sostenidos, 3 contradichos, 0 leídos, 0 sin sustento.** Los contradichos
(E-02, E-05 y E-06) son por verdad semántica: el documento canónico tiene la forma que piden los
tests, pero afirma cosas que el código no hace. Con un contradicho, **el cambio no cierra**.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Catálogo: la tabla índice, un `###` por concepto, sin duplicados | sostenido | si | `64_modelo_de_dominio.py`. La tabla es idéntica a la §4.2 de la spec |
| E-02 | Diez campos por concepto | **contradicho** | si | El test cumple la forma. El invariante de ModelTierApproval es falso (S5) |
| E-03 | Nueve contextos y Execution como límite reservado | sostenido | si | `64_*`; leído |
| E-04 | Doce clasificaciones y ningún Domain Event | sostenido | si | `64_*` |
| E-05 | Los 46 schemas tienen un concepto | **contradicho** | si | El test cumple la cobertura. `database-environment-access-policy` bajo NormativeMatrix es falso (S4) |
| E-06 | Las catorce desigualdades, con rutas que existen | **contradicho** | si | El test cumple la forma. Tres apartados afirman cosas falsas (S1, S2 y S3) |
| E-07 | El vocabulario apunta a conceptos | sostenido | si | `64_*`. Nota menor: la fila `policy` dice "cuatro configuraciones" y nombra tres |
| E-08 | Host es External, con sus seis papeles | sostenido | si | `64_*`; leído |
| E-09 | El límite de la ejecución | sostenido | si | `64_*`: 9 ítems que existen, 9 que no, 2 invariantes y 3 preguntas |
| E-10 | Los veredictos SDD quedan fuera del producto | sostenido | si | `64_*` |
| E-11 | El README enlaza el documento | sostenido | si | `64_*` |
| E-12 | ADR-0013 aceptado, con las seis decisiones | sostenido | si | `64_*`. Leído contra `plan.py:31-41, 444-490`; no menciona D15 |
| E-13 | El plan es 2.0, con tres estados | sostenido | si (la mutación cubre el estado y no el `$id`) | `64_*`; schema `:3, 19, 370-374` |
| E-14 | La unidad tiene tres estados, y PENDING está definido | sostenido | si | `64_*`; schema `:261-265` |
| E-15 | Ningún documento escrito lleva un estado retirado | sostenido | si | 44 documentos propios. `PLANNING` se pisa antes de validar (`plan.py:286-288`) |
| E-16 | Un 1.0 de `4c6f0f3` se acepta y se migra al escribirlo | sostenido | si | reproducción propia: plan igual byte a byte, 135 unidades iguales a la base y `run.json` idéntico |
| E-16b | Un 1.0 con `DELEGATING` o con una unidad `READY` se rechaza | sostenido | si (repetida: 20 de 36 aserciones en rojo) | los dos documentos validan contra el schema y el validador de `4c6f0f3`, y no contra 2.0 |
| E-16c | Otra versión, o ninguna, se rechaza | sostenido | si | reproducción propia (3.0, 1.1, entero, sin meta) |
| E-17 | El productor escribe lo mismo que `4c6f0f3`, salvo la versión | sostenido | si (la mutación cubre la versión; el refutador sumó una de `defaultTier`) | 44 documentos contra la base |
| E-18 | Ids repetidos: sale con 2 y no escribe | sostenido | si | reproducción. La base escribía el plan con exit 0 |
| E-19 | Dominio fuera del plan: sale con 2 y no escribe | sostenido | si | reproducción. La base lo escribía |
| E-20 | `--replanificar` con una propuesta rota deja el plan intacto | sostenido | si | reproducción; no hay una regla más amplia |
| E-21 | El estado del plan se deriva del contenido | sostenido | si | 44 documentos; se alcanzan los tres estados |
| E-22 | Un solo escritor y una sola regla de lectura | sostenido | si | `plan.py:444-491`, usada en `dev-harness.py:1227` y `refutacion.py:861` |
| E-23 | El registro decide si un agente existe | sostenido | si | `dev-iniciador-code` da `agentExists: false` |
| E-24 | El orquestador conoce las dos reglas y la 2.0 | sostenido | si (la mutación cubre la versión, no las reglas) | `dev-orchestrator.md:40, 73-77` |
| E-25 | `plan` con una clave inválida no escribe | sostenido | si | 5 claves; la base salía con 1, por traceback |
| E-26 | `contexto`, `refute` y `seguridad` rechazan la clave antes de escribir | sostenido | si | 6 claves por 7 variantes, con el árbol del proyecto igual; la base escribía con `seguridad` |
| E-27 | Las cuatro reglas de la clave aceptan lo mismo | sostenido | si | los cuatro patrones son idénticos |
| E-28 | La LedgerKey es una TaskKey o una sesión | sostenido | si | 8 claves rechazadas por 4 variantes. La `statusLine` escribe en `runtime/accounting/barra-no-uuid-77/` |
| E-29 | Jira devuelve otra clave | sostenido | si | conflicto con las dos claves; la pedida se conserva |
| E-30 | La misma TaskKey de punta a punta | sostenido | si | `OBRA-77` en el contexto, el plan, 135 unidades y la seguridad |
| E-31 | Los `declaredChecks` son los que declara la norma, sin checks del hook | sostenido, con la corrección aceptada | si (repetida) | ver `## Cambios de spec durante la construcción` |
| E-32 | Los casos de cierre resuelven igual que `4c6f0f3` | sostenido | si | 4 variantes de `checks.json` con 211 resultados, idénticos a la base |
| E-33 | La `cacheKey` no cambia | sostenido | si | caché cruzada base↔nueva, con acierto `CACHE` |
| E-34 | Ningún check del hook corre en PreToolUse | sostenido | si | grep propio; `controles.py:10-13`; `control-registry.json:12-15` |
| E-35 | Ningún control se llama como un check del roster | sostenido | si | intersección vacía |
| E-36 | La señal normativa es de las dos normas | sostenido | si | el diff toca solo `description` |
| E-37 | La forma de una capability, que no es una HostTool | sostenido | si | 11 capabilities, rederivadas |
| E-38 | Ningún `tools:` nombra una capability | sostenido | si | 13 agentes |
| E-39 | Lo soportado lo declaran las clases | sostenido | si | solo cambian el docstring y el doc |
| E-40 | Nadie emite los eventos del ciclo | sostenido | si | los literales solo en `eventos.py:28-35` y el schema |
| E-41 | Todo `subprocess` lanza git o markitdown | sostenido | si | 5 lugares, rederivados |
| E-42 | `orquestacion/` no lee la contabilidad | sostenido | si | grep propio |
| E-43 | La contabilidad no cambia su contrato | sostenido | si (la mutación cubre el enum y el `eventId`) | schema idéntico salvo 3 `description`; mismos `eventId` con base y nuevo |
| E-44 | Fábrica e instalado, iguales salvo la diferencia conocida de C3 | sostenido, con la corrección aceptada | si | ver `## Cambios de spec durante la construcción` |
| E-45 | Un proyecto 0.29.0 sobrevive al `-Update` | sostenido | si | reproducción propia, con veredictos registrados |
| E-46 | Los tres schemas pasan `controlar_soporte` | sostenido | si | corrida propia |
| E-47 | La documentación dice los estados y la regla de lectura | sostenido* | si | *`docs/orquestacion.md:204` nombra `DELEGATING` y `READY` como ejemplos de rechazo, no como estados |
| E-48 | Los doce pendientes | sostenido | si | los 12 `###`; 172 inserciones y 0 borrados |
| E-49 | La compuerta sale con 0 | sostenido | no consta | corrida propia: 39206/39206, exit 0 |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Las 50 marcas `si` están en el
> registro de la spec, en `Cómo se verifica`. Los refutadores confirmaron que cada mutación registrada
> rompe lo que cuida su escenario. Cuatro son parciales y se completaron con chequeos propios (E-13,
> E-17, E-24 y E-43). E-16b y E-31 se repitieron.

## E-02, E-05 y E-06, los escenarios contradichos

La suite mide la forma del documento canónico, no si es verdad (spec, `Cómo se verifica`). Por eso
la verdad semántica la juzgó el refutador, leyendo el documento contra el código. Cinco afirmaciones
son falsas:

```
S1  modelo-canonico.md:1291  "Capability ≠ Tool": "el plan lo prohíbe (capacidades.py)".
    No hay prohibición: capacidades.py:29-55 convierte cualquier nombre en hueco, y
    requiredCapabilities no tiene patrón en el schema. Reproducido: armar con
    ["Glob","Read"] da CAPABILITY_RESOLUTION y validar() devuelve [], el plan se escribe.

S2  modelo-canonico.md:1314  "GuardrailCheck y ControlCheck se instalan".
    controles/ no se instala (install.ps1:1839-1844), y el propio documento lo dice en
    ControlRegistry (:745-746). Viene de la spec §4.3.

S3  modelo-canonico.md:1309  "G2 declara a propósito el mismo id como las dos cosas".
    El código lo trata como un defecto de la matriz provista,
    SECURITY_CONTROL_ID_TYPE_COLLISION, "quien pueda lo arregla en origen"
    (seguridad.py:37-39, 281-287; docs/seguridad-es0902.md:866-869). Viene de la spec §4.3.

S4  modelo-canonico.md:686  NormativeMatrix incluye database-environment-access-policy.
    bases.py:3-4: "No es una regla de ES0901: … no entra en la matriz normativa y no figura en
    el registro de controles". Es el desvío 5 del informe, hecho para cumplir E-05.

S5  modelo-canonico.md:525  ModelTierApproval: "una aprobación pendiente deja el plan en
    WAITING_FOR_HUMAN_APPROVAL". Con un hueco de capacidad, estado_de devuelve
    CAPABILITY_RESOLUTION (plan.py:408-416). Reproducido: el plan queda en
    CAPABILITY_RESOLUTION con la aprobación PENDING.
```

Cada una cae en un escenario:

- **E-02:** S5. El campo `Invariantes` describe una regla que no existe.
- **E-05:** S4. El schema está mapeado, pero a un concepto al que el código dice que no pertenece.
- **E-06:** S1, S2 y S3. Tres de las catorce desigualdades se sostienen con una justificación falsa.

**La decisión: vuelve a construcción.** No se mueve ningún criterio para que el resultado entre.
El arreglo es del documento, no del código: corregir las cinco afirmaciones y darle a
`database-environment-access-policy` un concepto que el código respalde. S2 y S3 vienen de la spec
§4.3, que se corrige en el mismo movimiento. Ninguno de los contradichos cambia comportamiento.

📌 **Hay una tensión con la spec, y queda dicha.** El §15 manda los hallazgos de verdad semántica a
`Lo que la verificación encontró`, no a un escenario. El pedido de verificación decía lo contrario:
"si una definición estructuralmente válida no describe el código real: `contradicho`". El refutador
siguió el pedido, y el registro no lo cambia.

## Cambios de spec durante la construcción

Las dos correcciones tienen una nota "Corregido durante la construcción" en la spec. Su texto
anterior no está versionado (`spec.md` no tiene commit), así que la redacción original se tomó de la
nota misma y del pedido de verificación.

### E-31

- **Redacción original:** los `declaredChecks` de una RefutationUnit son ids de controles `CHECK` del
  `control-registry`, y ninguno es un check del roster.
- **La contradicción preexistente, comprobada en `4c6f0f3`:**
  - la matriz de ES0901 declara 34 checks;
  - 21 de esos 34 no están en `control-registry.json`, y el `_comentario` de la matriz dice que "NO
    existen todavía";
  - esos 21 ya llegaban a `declaredChecks` por el bloque normativo. En el plan de prueba llegan 9.
- **Qué hacía falta para cumplir la redacción original:** o filtrar contra el registro, que es un
  comportamiento nuevo que `Qué se construye` no autoriza y haría que la unidad declare menos de lo
  que pide la norma, o registrar 21 controles, que está fuera de alcance.
- **Redacción corregida:** exactamente los ControlCheck que declara la norma, y ninguno de
  `roster.json`.
- **Juicio: conserva la intención.**
  - El código solo saca de la unión los nombres del roster: `dev-accesibilidad-html`, `dev-api-rutas`,
    `dev-dependencias` y `dev-infra-en-codigo`.
  - Ningún check del hook se vuelve control normativo.
  - El cierre por check no cambia: `cacheKey`, `REF-nnn`, `resolutionPath`, veredictos y `run.json`
    son idénticos a la base.
  - La mutación repetida pone en rojo E-31 y deja en verde E-32 y E-33.
  - La corrección no saca nada que se pudiera cumplir dentro del alcance. **Sostenido.**

### E-44

- **Redacción original:** el plan armado desde la fábrica y el armado en un proyecto instalado son
  iguales, salvo `meta.generated_at`, `meta.harness_version` y `planHistory[].timestamp`. Solo se
  excluía `normativeEvidence`.
- **La contradicción preexistente, comprobada en `4c6f0f3`:**
  - el instalador no copia `controles/`;
  - con el instalador y la fábrica de la base, la única diferencia es
    `workUnits[*].normative.standards.ES0902.rules.C3.developmentStandardBaseline.status`: `RESOLVED`
    en la fábrica y `UNRESOLVED` en el instalado.
- **Task 2 no lo agrandó:** con el código nuevo, el conjunto de rutas que difieren es exactamente el
  mismo.
- **Redacción corregida:** iguales salvo esos campos y los resultados normativos que dependen de
  `controles/`, que hoy son exactamente esa ruta. El test comprueba que es la única diferencia y que
  es la conocida.
- **Juicio: conserva la intención.**
  - La excepción es angosta: una regex sobre esa sola ruta, más una aserción que exige `RESOLVED` en
    la fábrica y `UNRESOLVED` en el instalado (`64-modelo-de-dominio-instalador.ps1:131-151`).
  - No es un "pueden diferir" genérico. La mutación pone en rojo tanto una divergencia nueva como la
    desaparición de la conocida.
  - **Sostenido.**

## El contrato 2.0

| | Qué se comprobó |
|---|---|
| Productor | `$id` y `meta.schema_version` dicen solo 2.0 (`orchestration-plan.schema.json:3, 19`). Los estados son exactamente tres en el plan y tres en la unidad. Ningún documento escrito lleva `DELEGATING`, `READY` ni `PLANNING`: este último se pisa antes de validar |
| Consumidores | Hay una sola autoridad, `plan.aceptar_guardado`, que usan `refute --compile` y `--replanificar`. No hay una segunda implementación |
| Migración | Un 1.0 compatible: `refute --compile` lo lee sin tocarlo, y `--replanificar` lo escribe como 2.0, con versión + 1 y la historia entera |
| Rechazo | Con exit 2 y el campo y el valor en el mensaje: 1.0 con `DELEGATING`, unidad `READY`, `3.0`, `1.1`, una versión entera, sin `schema_version`, sin `meta`, 2.0 con `DELEGATING`, unidad `RUNNING` y plan `PLANNING` |
| Atomicidad | Antes de cada rechazo se prepararon `run.json`, 136 unidades (una vieja, `REF-999`), un veredicto y una entrada de caché. En los 22 rechazos el plan conserva el sha, `refutaciones/<KEY>/`, `cache/` y el resto de `.claude/` quedan sin diferencias, `REF-999` sigue y `run.json` no se reescribe. Solo cambia `.claude/runtime/knowledge-refresh.json`, que es de la compuerta y está permitido |

## El modelo de dominio

- **Veracidad.** Se contrastaron 22 conceptos contra el código y los schemas: Task, TaskKey,
  TaskContext, ProjectContext, ProjectMemory, Plan, WorkUnit, AgentRegistry, Agent, Skill, Capability,
  Integration, Policy, ControlCheck, GuardrailCheck, Evidence, EvaluationResult, Refutation,
  AccountingEvent, LedgerKey, Host e Installation. Para cada uno se miraron definición, identidad,
  estados, invariantes, persistencia, productores y consumidores. Coinciden, salvo S1 a S5 y las
  imprecisiones de `## Lo que la verificación encontró`.
- **Contextos.** Son nueve, y Execution es un límite reservado: ningún concepto lo tiene como contexto,
  y no hay contratos de ejecución. No se construyó ningún agregado de ejecución, ejecutor, scheduler,
  DAG, reintento, checkpoint, `ExecutionResult` ni cliente de modelo.
- **Clasificaciones.** Son doce, y ningún concepto es un Domain Event.
- **Vocabulario.** Es cierto, salvo la fila `policy`, que dice cuatro y nombra tres.
- **El límite de la ejecución.** Coincide con la spec §10.1.

## Compatibilidad

| | Resultado |
|---|---|
| Línea de base | `4c6f0f3` es 0.29.0. Los tests comparativos la sacan con `git archive` |
| `-Update` | Reproducción propia: un proyecto instalado con `4c6f0f3`, con un TaskContext real (Jira simulado), un plan 1.0, 90 unidades compiladas y un veredicto registrado. Después del `-Update`, `contextos`, `planes` y `refutaciones`, caché incluida, quedan iguales. `refute --compile` no regenera el plan, y da unidades, veredictos, `run.json` y caché idénticos a la base. `--replanificar` escribe 2.0 con la historia entera, y recompilar conserva los veredictos |
| Refutación | `REF-nnn`, `cacheKey`, `resolutionPath`, veredictos y `run.json` iguales a la base. La caché se lee en los dos sentidos, base↔nueva |
| Contabilidad | El schema es idéntico salvo tres `description`. Mismos `eventId` con el código de la base y con el nuevo |
| Test 63 adaptado | La lista nueva tiene exactamente los once archivos de la sección 12, sin comodines. Mutar un docstring de `modelo.py`, que no está autorizado, en una copia del repo: 187/188, y falla solo E-16, nombrando ese archivo |

## La suite, corrida por el refutador

| Corrida | PowerShell | Python | Total | Exit | Duración |
|---|---|---|---|---|---|
| `harness-spec-refuter`, parte 2, sola y al final, con stdin redirigido | 775/775 | 38431/38431 | **39206/39206** | **0** | 967 s (21:59:20 a 22:15:27) |

`pre-tool-use.py` y `zonas.py` tenían antes y después el mismo hash (`61567f3`, `e996067`). Además,
la parte 1 corrió `python tests/correr.py -k 64_modelo`: 848/848, exit 0.

Las salidas crudas de la parte 2 —las reproducciones y la compuerta— están en
[evidencia-verificacion/](evidencia-verificacion/README.md). Ahí también está explicado por qué una
línea de `e45b_out.txt` da `False` sin que eso sea una falla.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Cinco afirmaciones falsas en el documento canónico,** S1 a S5. Son las que motivan los tres
   contradichos.
2. **Imprecisiones sin veredicto propio:**
   - Capability: "disponible = validada ENABLED" y "la valida `setup`" no valen para las capacidades
     locales del roster (`capacidades.py:22-26`).
   - GuardrailCheck: `claude-md-zonas` no figura en la lista `checks` de `roster.json`.
   - Agent y Skill: `Dónde vive` incluye `comun/agents`, `comun/skills` y `dev-iniciador-code`, que no
     están en `agent-registry.json`.
   - Installation: en runtime se valida contra una copia en línea (`bienvenida.py:407-443`), no
     contra el archivo de schema.
3. **El `### ControlCheck` del documento no cubre los ids "declarados y no instalados"** sobre los que
   se apoya la corrección de E-31, y el I-25 de la spec no se ajustó.
4. **El conteo de contradicciones no coincide:** el ADR y la spec §1 dicen 54, `PENDIENTES-FH.md` dice
   55, y la tabla del §17 tiene 57 filas.
5. **`main` mapea todo `PlanInvalido` a código 2.** Alcanza también casos que ya existían: un ciclo de
   dependencias salía con 1 por traceback y ahora sale con 2. No evita ningún artefacto, así que no
   pasa D15 por sí solo. Está declarado como desvío 2 del informe, y es menor.
6. **E-47 se sostiene por lectura:** `docs/orquestacion.md:204` nombra `DELEGATING` y `READY`, pero
   como ejemplos de rechazo dentro de la regla de lectura, no como estados.
7. **El test de E-45 usa un TaskContext mínimo y no registra veredictos.** La reproducción del
   refutador cubre ese hueco.

## Lo que queda abierto, anotado y no escondido

- **Los tres contradichos vuelven a construcción.** Hay que corregir el documento canónico (S1 a S5),
  la spec §4.3 (S2 y S3), y la ubicación de `database-environment-access-policy`. Después hay que
  volver a verificar E-02, E-05 y E-06.
- **Los hallazgos 2 a 4** se resuelven en la misma pasada del documento, o se anotan en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
- **El hallazgo 5** queda a decisión: o se acepta como desvío declarado, o se limita a los casos
  nuevos con una subclase.
- **La deuda que la spec dejó afuera a propósito** sigue en `PENDIENTES-FH.md`, en los doce ítems de
  E-48. Los dos hallazgos nuevos de la construcción son reales y quedaron anotados sin arreglar: el
  efecto sobre C3 de que `controles/` no se instale, y los docstrings que todavía dicen "tres
  salidas". No se cerró ningún ítem viejo: el diff de `PENDIENTES-FH.md` tiene 172 inserciones y 0
  borrados.

## Lo que ningún test cubre y se mira con los ojos

- **Que cada definición del documento canónico describa el código real.** Eso no lo prueba ninguna
  suite. Esta verificación lo hizo para 22 conceptos y encontró S1 a S5. Los otros 46 se leyeron solo
  en lo que tocaban los escenarios. La próxima verificación tiene que volver a leer los conceptos que
  se corrijan.

---

## Segunda verificación

**Fecha:** 05-10-2026 · **Alcance:** focalizado, por pedido. No se volvieron a dictaminar los 51
escenarios.

Lo de arriba es la primera verificación y se conserva tal cual: **48 sostenidos, 3 contradichos.**
Después volvió a construcción, y el informe de esa pasada está en `Correcciones posteriores a la
primera verificación` de [informe-de-construccion.md](informe-de-construccion.md). Los refutadores
lo usaron solo como mapa.

| | |
|---|---|
| Verificó | `harness-spec-refuter`, en dos contextos propios y sin el de la construcción. El A cubrió E-02, E-05, E-06, I-25, el conteo y el alcance. El B cubrió E-18b, la no regresión y la compuerta |
| Línea de base | `4c6f0f3`, cuya `VERSION` dice 0.29.0. La sacaron con `git archive` a `%TEMP%`, sin fixtures versionados |
| Qué entró en la pasada | Se delimitó por fecha de modificación, porque no hay commit. Es todo lo posterior al cierre de la primera verificación, el 03-10-2026 a las 23:28:42 (ver `## Alcance de la pasada`) |
| Árbol | 32 entradas en `git status`, antes y después. Ninguno de los dos escribió en el repo |
| Registró | la sesión que construyó, con `write-a-verdict`. No agregó veredictos propios |

**Resultado de la segunda pasada: 3 sostenidos (E-05, E-06 y E-18b) y 1 contradicho (E-02).** No
hubo ninguna regresión, y la compuerta salió con 0. **Con un contradicho, el cambio no cierra.**

### Re-verificados

| # | Escenario | Veredicto | Rojo visto | Evidencia y reproducción propia |
|---|---|---|---|---|
| E-02 | Diez campos por concepto, y que sean verdad | **contradicho** | si (confirmado: con los dos primeros `if` de `estado_de` invertidos, `test_e02_s5` da 21/29) | S5 quedó corregido y reproducido. Una oración nueva en Agent es falsa: ver `### E-02, contradicho otra vez` |
| E-05 | Los 46 schemas tienen un concepto, y es el correcto | sostenido | si | `database-environment-access-policy` y `database-profile` están en DatabaseAccessPolicy, que describe el contrato real. Ver `### E-05` |
| E-06 | Las catorce desigualdades, sin justificaciones falsas | sostenido | si (confirmado: con "el plan lo prohíbe" de vuelta, `test_e06_s1` da 13/14) | S1 reproducido por CLI, y S2 y S3 contra el código. Ver `### E-06` |
| E-18b | Solo los rechazos nuevos salen con 2, y los `PlanInvalido` de antes como en `4c6f0f3` | sostenido | si (confirmado: `main` atrapando `PlanInvalido` pone 6 de 35 en rojo; el id repetido como `PlanInvalido`, 2 de 35) | reproducción por CLI sobre los dos árboles. Ver `### E-18b` |

El A corrió aparte las ocho funciones `test_e02*`, `test_e05*` y `test_e06*` del caso 64: 225/225.

### E-02, contradicho otra vez

**Lo que se corrigió y se sostiene.** La precedencia está en `plan.py:418-426`: primero un hueco,
después una aprobación `PENDING`, después una unidad `BLOCKED`, y si no `READY_FOR_EXECUTION`. Ahora
lo dicen ModelTierApproval (`modelo-canonico.md:532-535`) y el ciclo del Plan (`:393-399`).

```
dev-harness.py plan OBRA-91 --propuesta ...
  hueco (gitlab.project.read) + aprobación PENDING (premium)  -> CAPABILITY_RESOLUTION, exit 0, validar()=[]
  sin hueco (repository.read) + PENDING (reasoning)           -> WAITING_FOR_HUMAN_APPROVAL
  estado_de en las 8 combinaciones de hueco, PENDING y BLOCKED -> el orden de los dos textos
```

Los menores corregidos también son ciertos:

- **Capability:** coincide con `capacidades.py:22-26` y `registro.py:10-16`.
- **GuardrailCheck:** tiene dos fuentes. `claude-md-zonas.py` no está en el roster, y los cinco
  `dev-*` son los cinco de `roster.json`. Se instalan en `install.ps1:1827, 1840`.
- **Skill:** `instalar-desde-github` no está declarada.
- **Installation:** en runtime se valida contra `FORMA_INSTALACION`, en `bienvenida.py:461-467`.

**Lo que es falso.**

```
modelo-canonico.md:590  Agent, "Dónde vive": "El plan solo asigna agentes del registro."
plan.py:313             agente = str(propuesta_unidad.get("assignedAgent") or roster.agente_de_dominio(dominio))
Reproducido:            assignedAgent=dev-iniciador-code  -> agentExists=False, AGENT_NOT_FOUND,
                        unidad PENDING, plan READY_FOR_EXECUTION, exit 0
                        assignedAgent=cualquier-cosa      -> igual
```

La propuesta manda, y el plan asigna lo que pida. La oración contradice al mismo concepto
(`:578-579`, "El plan no rechaza uno desconocido") y a la spec §4.2. El propio test de E-23 arma ese
plan (`64_modelo_de_dominio.py:1686-1692`).

La oración entró en la pasada de corrección, cuando se reescribió `Dónde vive` por el hallazgo menor
de Agent. Antes no estaba. Ningún test la cubre, así que no tiene rojo visto posible.

**La decisión: vuelve a construcción, solo por esa oración.** No se mueve ningún criterio. El
pedido de esta pasada decía "si el documento sigue diciendo algo falso: `contradicho`", y el
refutador lo aplicó igual que en la primera. Sigue en pie la tensión con el §15 de la spec, ya dicha
arriba.

### E-05

- **El contrato:**
  - `bases.py:3-5` dice que no es una regla de ES0901;
  - ningún módulo de producción importa `bases` (solo `tests/casos/33_bases_de_datos.py:27`);
  - ni las matrices `es090*`, ni el anexo, ni la línea base, ni `control-registry.json` nombran
    `database-*`;
  - la política vive en `reglas/database-environment-access-policy.json`: DEV con todo; QA, HML y PRD
    en solo lectura; el resto DENY con `DATABASE_ENVIRONMENT_UNRESOLVED`;
  - los perfiles vienen vacíos y se validan con `validar_perfil` (`bases.py:249-255`). Está dormida.
- **El mejor concepto.** Ninguno de los otros 68 describe qué operación corre en qué ambiente,
  decidido antes de conectar. NormativeMatrix y Evidence eran falsos.
- **La coherencia, comparada por script:**
  - la tabla §4.2 de la spec y el índice del documento tienen las mismas filas en el mismo orden;
  - el contexto y la clasificación coinciden en cada `###`;
  - cada uno de los 46 schemas de §3.2 está nombrado por su concepto;
  - ningún otro concepto nombra los schemas de bases.
- **Imprecisiones sin veredicto:**
  - la identidad de un perfil es (base lógica, ambiente), no solo el ambiente (`bases.py:664-670`);
  - la fila Catalog del §5.1 de la spec no sumó "ambiente";
  - el vocabulario de `policy` cuenta sus sentidos distinto que la spec §1. Esto viene de la primera
    construcción.

### E-06

- **S1, Capability ≠ Tool:**
  - con `["Read","Glob"]` por CLI sale exit 0, y el plan queda en `CAPABILITY_RESOLUTION` con dos
    huecos y `validar()=[]`;
  - `requiredCapabilities` es `{"type":"array","items":{"type":"string"}}`;
  - ninguna de las 11 capabilities declaradas lleva nombre de HostTool;
  - ninguna redacción implica una prohibición: el apartado, los invariantes de Capability y de
    HostTool, I-20 y la fila §4.3.
- **S2, Check ≠ development test:**
  - se distinguen por contrato, ciclo de vida, dueño y mecanismo;
  - GuardrailCheck se instala (`install.ps1:1827, 1840`), y `controles` no aparece en `install.ps1`;
  - imprecisión sin veredicto: el texto dice "en cada escritura", pero el matcher también incluye
    Bash y PowerShell (`hooks.plantilla.json:38`).
- **S3, Policy ≠ Check:**
  - el texto dice que es un defecto de los datos y no una excepción;
  - `colisiones_de_id()` sobre la matriz provista devuelve el id con `[CHECK, POLICY]` y
    `SECURITY_CONTROL_ID_TYPE_COLLISION`;
  - fuera de `seguridad.py:281` solo lo llaman `37_es0902_seguridad.py:1999` y el caso 64. El texto
    dice que ningún comando lo emite, y no le atribuye al producto un reporte que no hace;
  - la matriz de G2 es igual a la de `4c6f0f3`.

### E-18b

Se corrió `dev-harness.py plan OBRA-91 --propuesta ...` sobre los dos árboles, un proceso por
corrida, sin plan previo y con un plan escrito por ese mismo árbol:

| Caso | `4c6f0f3` | Ahora | Plan |
|---|---|---|---|
| Ciclo, dependencia rota, sin unidades, sin `workUnits` | 1, por traceback | 1 | no se crea, o queda igual |
| Dominio del plan inventado (`plan.py:188-192`) | 1 | 1 | igual |
| Id fuera del patrón (falla el schema al escribir) | 1 | 1 | igual |
| Id repetido | 0, y crea o modifica el plan | **2**, nombra el id | no se crea, o queda igual |
| Dominio de la unidad fuera del plan | 0, y lo escribe | **2**, nombra el dominio | igual |
| `--replanificar` con ciclo, dependencia rota o sin unidades | 1 | 1 | igual |
| `--replanificar` con id repetido o dominio fuera | 0, y modifica el plan | 2 | igual |
| `--replanificar` sobre un plan guardado que D16 rechaza | 0 con `DELEGATING` (lo reescribía) | 2 | byte a byte |

En el código:

- `PlanRechazado` se levanta en cinco lugares: `plan.py:208`, `:218` y `:475, 479, 486, 494`;
- los otros `raise PlanInvalido` son los de antes (`:94, 113, 123, 152, 190, 195, 432, 442, 511`);
- `main` atrapa `orq_plan.PlanRechazado` (`dev-harness.py:1982`). `PlanInvalido` general no volvió a
  mapearse a 2;
- `refutacion.py:862` atrapa `PlanInvalido`, pero solo alrededor de `aceptar_guardado`.

📌 **Un cruce entre E-18b y E-19, que queda dicho.**

- **Qué cambió:** una unidad con un dominio inventado o vacío (`"inventado"`, `""`) salía con 1 en
  `4c6f0f3`, por el `PlanInvalido` de `contexto_para`. Ahora sale con 2 por `PlanRechazado` ("no
  está entre los dominios del plan"), y tampoco escribe el plan.
- **Por qué se sostiene:** el refutador lo leyó como sostenido. E-19 exige 2 para toda unidad cuyo
  dominio no esté en `domains`, y un dominio desconocido nunca puede estar, porque `:188` valida los
  dominios del plan.
- **Lo que pesa en contra:** es un rechazo que ya existía y que cambió de código sin evitar ningún
  artefacto, justo lo que motivó el hallazgo 5. El `raise` de `contexto_para` (`:151-155`) quedó
  inalcanzable desde `armar`, y ningún test cubre el cruce.

### No regresión

| Punto | Resultado | Evidencia |
|---|---|---|
| D16, aceptar | se mantiene | Un 2.0 recién escrito valida, y `refute --compile` no lo reescribe. Un 1.0 compatible queda byte a byte, con 90 unidades iguales a la base (ids, regla, `cacheKey`, `resolutionPath`, estado) y `run.json` idéntico |
| D16, migrar | se mantiene | `--replanificar` sobre un 1.0 escribe 2.0, con `plan_version` 1→2 y la historia previa como prefijo. Recompilar no lo reescribe |
| D16, rechazar | se mantiene | Se probaron seis documentos: 1.0 `DELEGATING`, unidad `READY`, `9.9`, sin `schema_version`, 2.0 `DELEGATING` y sin `meta`. Contra los dos consumidores dan 12 rechazos, todos con exit 2 y el campo y el valor en el mensaje. La base aceptaba el 1.0 `DELEGATING` |
| Atomicidad | se mantiene | Se prepararon `run.json`, un veredicto, una entrada de caché y `REF-999`. Después de cada rechazo, el plan, `refutaciones/<KEY>/`, `cache/` y el resto de `.claude/` quedan iguales, y `REF-999` sigue. Un compile exitoso sí la borra |
| E-31 | se mantiene | No volvió la unión con `requiredChecks`: solo salen nombres del roster, sin agregar nada. La caché cruzada base↔nueva acierta con el mismo archivo. El veredicto es igual salvo `recordedAt`. E-31, E-32, E-33 y E-43 dan 75/75 |
| I-25 | se mantiene | La matriz declara 34 checks, y 21 no están registrados (contados por el A). En 315 unidades compiladas, 9 ids no registrados llegan igual a `declaredChecks` y ningún nombre del roster entra. El registro tiene los mismos 60 controles que la base: solo cambió el `_comentario`, de la primera construcción (E-34) |
| E-44 | se mantiene | Con 5 dominios y 5 unidades, contra el instalador actual y el de la base, difiere exactamente la misma ruta de C3. Ninguna ruta aparece solo en uno de los dos árboles |
| TaskKey | se mantiene | `seguridad` con cinco claves inválidas: exit 2 y nada escrito. Con `OBRA-91`: exit 0 |
| LedgerKey | se mantiene | `contabilidad` con cuatro claves inválidas: exit 2 y nada escrito. Un UUID en minúscula, uno en mayúscula y `OBRA-91` se aceptan |
| Conflicto de Jira | se mantiene | Si Jira devuelve `ZETA-5` cuando se pidió `GCBA-1234`, se registra un conflicto con las dos. El archivo, `meta.task_key` y `context_id` conservan la pedida |
| `eventId` | se mantiene | Iguales a los de la base |
| `cacheKey`, `REF-nnn`, `resolutionPath`, veredictos | se mantiene | Los diffs de `plan.py` y `dev-harness.py` solo agregan código. `refutacion.py` y `libro.py` no cambiaron después del corte, y los puntos de arriba lo reproducen |

### Conteo de contradicciones

La tabla del §17 tiene 57 filas: de C-01 a C-55 sin huecos, más C-09b y C-17b. El A las contó.

| Dónde | Qué dice |
|---|---|
| Spec §1 (`:51-53`) | 57, y que el número es el de la tabla |
| `PENDIENTES-FH.md` | "57 entries as of this writing" |
| ADR-0013 | "enumeradas en su sección 17", sin número |
| Documento canónico | no da número |

Ya no se contradicen.

### Alcance de la pasada

Los archivos modificados después del corte, el 03-10-2026 a las 23:28:42, son:

- código: `plan.py` y `dev-harness.py`;
- documentación: ADR-0013, `modelo-canonico.md` y `PENDIENTES-FH.md` (179 inserciones, 0 borrados);
- el caso 64, la spec y el informe de construcción.

`pre-tool-use.py` y `zonas.py` tienen fecha nueva porque la compuerta los restaura, pero su
contenido es igual a `HEAD`.

No aparecieron Execution, la instalación de `controles/`, cambios en G2 ni en el AgentRegistry, ni
cambios en skills, `dev-refutador.md`, `VERSION`, `CHANGELOG.md` o `UPGRADE.md`.

### Suite

| Corrida | PowerShell | Python | Total | Exit | Duración |
|---|---|---|---|---|---|
| `harness-spec-refuter` B, desacoplada, con stdin vacío | 775/775 | 38534/38534 | **39309/39309** | **0** | 1828 s (11:54:42 a 12:25:10) |

Coincide con lo que declaró la construcción. Tardó más que la primera porque las reproducciones
corrían al mismo tiempo. `pre-tool-use.py` y `zonas.py` tuvieron el mismo hash antes, durante y
después (`61567f3`, `e996067`).

### Resultado acumulado

| | Sostenidos | Contradichos | Leídos | Sin sustento |
|---|---|---|---|---|
| Primera verificación (51 escenarios) | 48 | 3 | 0 | 0 |
| Segunda verificación (4 re-verificados) | 3 | 1 | 0 | 0 |
| **Acumulado (52 escenarios, con E-18b)** | **51** | **1** | **0** | **0** |

- **E-05 y E-06 quedaron resueltos.**
- **E-02 sigue contradicho,** por otra causa. S5 quedó resuelto, y el contradicho ahora es la oración
  de Agent.
- **Los 48 escenarios que no se re-verificaron** se sostienen por la muestra de no regresión y la
  compuerta en verde, no por un veredicto nuevo uno por uno.
- **No queda ningún `sin sustento` abierto.**

### Lo que esta pasada encontró y no habría encontrado un test verde

1. **La oración falsa de Agent** (`modelo-canonico.md:590`). Entró al corregir un hallazgo menor, y
   es el contradicho de E-02.
2. **El cruce entre E-18b y E-19:** un dominio de unidad desconocido pasó de 1 a 2.
3. **Imprecisiones sin veredicto propio:**
   - Capability: también validan `estado`, `reconfigurar` y `contexto` (sin registro o con
     `--revalidar`, `dev-harness.py:1092-1096, 1823-1824`), no solo `setup`;
   - DatabaseAccessPolicy: la identidad de un perfil es (base lógica, ambiente);
   - el §5.1 Catalog de la spec no sumó "ambiente";
   - el apartado de S2 dice "en cada escritura", y el matcher también incluye Bash y PowerShell;
   - el comentario de `refutacion.py:621` todavía dice "Solo controles del registro.", que es la
     redacción vieja de E-31. Es un comentario, no un comportamiento;
   - `docs/orquestacion.md:151` dice que lo que requiere aprobación deja el plan en
     `WAITING_FOR_HUMAN_APPROVAL`. Ya estaba en `4c6f0f3` y está fuera de E-02.

### Lo que queda abierto

- **E-02 vuelve a construcción.** Hay que corregir `modelo-canonico.md:590`, que tiene que decir que
  el plan asigna lo que pida la propuesta y marca con `agentExists: false` lo que el registro no
  declara. Después hay que volver a verificar E-02.
- **El cruce entre E-18b y E-19 queda a decisión:** o se acepta como parte de E-19, o el dominio
  desconocido vuelve a salir como en la base.
- **Las imprecisiones del punto 3** se corrigen en la misma pasada, o se anotan en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

**SPEC VERIFICATION FAILED**

---

## Tercera verificación

**Fecha:** 05-10-2026 · **Alcance:** focalizado en E-02 y en lo que cambió después de la segunda
verificación.

Las dos verificaciones de arriba se conservan tal cual. Después de la segunda hubo una pasada
documental, que está en `Corrección final de E-02` de
[informe-de-construccion.md](informe-de-construccion.md). El refutador la usó solo como mapa.

| | |
|---|---|
| Verificó | `harness-spec-refuter`, en un contexto propio, sin el de la construcción ni el de las verificaciones anteriores |
| Línea de base | `4c6f0f3` (0.29.0), sacada con `git archive` |
| Qué entró en la pasada | Se delimitó por fecha de modificación: todo lo posterior al cierre de la segunda verificación, el 05-10-2026 a las 12:28:30 |
| Árbol | 32 entradas en `git status`, antes y después. El refutador no escribió en el repo |
| Registró | la sesión que construyó, con `write-a-verdict`. No agregó veredictos propios |

**Resultado de la tercera pasada: E-02 sostenido.** Todo lo demás que se revisó se sostiene, y la
compuerta salió con 0.

### Re-verificado

| # | Escenario | Veredicto | Rojo visto | Evidencia y reproducción propia |
|---|---|---|---|---|
| E-02 | Diez campos por concepto, y que sean verdad | sostenido | si (confirmado: con "El plan solo asigna agentes del registro." de vuelta, `test_e23` da 17/18; con el párrafo reducido a esa oración, 16/18) | Todo `### Agent` contra el código, y la reproducción de abajo |

**Agent, contra el código:**

- `plan.py:313` toma `assignedAgent` de la propuesta, o `roster.agente_de_dominio` si no viene;
- `:337` escribe `agentExists` (`roster.existe_agente`, `roster.py:90-105`);
- `:341` escribe `agentValidation` (`roster.validacion_de_agente`, `roster.py:181-192`), que da
  `AGENT_NOT_FOUND` para lo que el registro no declara.

```
dev-harness.py plan OBRA-93 --propuesta ... --proyecto <tmp>     (un proceso por corrida)

assignedAgent              exit  plan  id conservado  agentExists  agentValidation  unidad   plan
dev-iniciador-code         0     sí    sí             false        AGENT_NOT_FOUND  PENDING  READY_FOR_EXECUTION
agente-que-nadie-declaro   0     sí    sí             false        AGENT_NOT_FOUND  PENDING  READY_FOR_EXECUTION
Cualquier Cosa 42!         0     sí    sí             false        AGENT_NOT_FOUND  PENDING  READY_FOR_EXECUTION
dev-backend (control)      0     sí    sí             true         VALID            PENDING  READY_FOR_EXECUTION
```

**Los textos corregidos, contra el código:**

- **Capability, Integration y la fila Catalog del mapa:** son ciertos. `correr_bootstrap`
  (`dev-harness.py:227`) se llama solo en dos lugares:
  - `:1095`, dentro de `contexto`, con `--revalidar` o sin registro;
  - `:1823`, al que solo llegan `setup`, `estado` y `reconfigurar`.

  Los demás subcomandos retornan antes (`:1764-1805`). La fila "Capacidades" de la spec §3.1 es
  exacta, y las capacidades locales no se validan.
- **DatabaseAccessPolicy:** es cierto. `bases.clave_de_perfil` (`bases.py:664-670`) arma la clave
  como `base/ambiente`. Coinciden la spec §3.2, §4.2 y §5.1.
- **"Check ≠ development test":** el matcher citado es idéntico a `hooks.plantilla.json:38`.
- **Las correcciones anteriores siguen intactas:** S1, S2, S3 y S5, y `database-*` solo en
  DatabaseAccessPolicy.

### Lo demás que se revisó

| Punto | Resultado | Evidencia |
|---|---|---|
| `docs/orquestacion.md` | se sostiene | La oración (`:151-153`) y el orden (`:186-191`) coinciden con `plan.py:418-426`, en las 8 combinaciones. Por CLI: hueco + `PENDING` → `CAPABILITY_RESOLUTION`; sin hueco + `PENDING` → `WAITING_FOR_HUMAN_APPROVAL`; solo hueco → `CAPABILITY_RESOLUTION`; nada → `READY_FOR_EXECUTION`. E-47 sigue en pie: las dos tablas tienen exactamente sus tres estados |
| La precisión de E-19 | se sostiene | El texto de la spec dice lo que se decidió: no se recupera el 1, D15 no se amplía en general, y E-18b no cuenta el caso. Reproducido sobre los dos árboles: `"inventado"` y `""` dan 2 ahora y 1 en `4c6f0f3`, sin escribir el plan; `frontend` fuera de `domains` da 2 ahora y 0 en la base; `domains` con `inventado` da 1 en los dos, lo que confirma que `plan.py:188-192` solo admite dominios conocidos |
| El código que cambió | se sostiene | Solo cambió el comentario de `refutacion.py:621`. Contra una copia anterior al corte, el `git diff` da esa sola línea y los `ast.dump` son idénticos. `plan.py`, `dev-harness.py`, `install.ps1`, `VERSION`, `CHANGELOG.md`, `UPGRADE.md`, `dev-refutador.md` y el AgentRegistry son anteriores al corte, y `verificacion.md` no se tocó después |
| Los tests | se sostienen | `test_e23` (`64_modelo_de_dominio.py:1695-1744`) suma dos aserciones de comportamiento y guardas que buscan en el documento los valores que escribió el plan. No compara markdown contra markdown |
| E-31 y E-33 | sin regresión | Un plan de 4 dominios compilado con la base y con el árbol actual: 180 unidades, con los mismos ids y la misma `cacheKey`. Las 135 que difieren solo pierden nombres del roster |
| D16 | sin regresión | Un 1.0 de la base en `DELEGATING`: `refute --compile` y `--replanificar` salen con 2, y el plan queda idéntico |
| E-18b | sin regresión | Un ciclo da 1 en los dos árboles. Un id repetido da 2 ahora, y 0 en la base |

### Suite

| Corrida | PowerShell | Python | Total | Exit | Duración |
|---|---|---|---|---|---|
| `harness-spec-refuter`, desacoplada, con stdin vacío | 775/775 | 38541/38541 | **39316/39316** | **0** | 1442 s (14:39:23 a 15:03:26) |

Coincide con lo que declaró la construcción, y `64_modelo_de_dominio` dio 958. `pre-tool-use.py`
(`61567f3`) y `zonas.py` (`e996067`) tuvieron el mismo hash antes y después.

### Resultado acumulado

| | Sostenidos | Contradichos | Leídos | Sin sustento |
|---|---|---|---|---|
| Primera verificación (51 escenarios) | 48 | 3 | 0 | 0 |
| Segunda verificación (4 re-verificados) | 3 | 1 | 0 | 0 |
| Tercera verificación (1 re-verificado) | 1 | 0 | 0 | 0 |
| **Acumulado (52 escenarios, con E-18b)** | **52** | **0** | **0** | **0** |

- **Los tres contradichos de la primera verificación quedaron resueltos.** E-05 y E-06 se resolvieron
  en la segunda, y E-02 en la tercera.
- **No queda ningún contradicho abierto.**
- **No queda ningún `sin sustento` abierto.**
- **Los 48 escenarios que no se re-verificaron** se sostienen por las muestras de no regresión de la
  segunda y la tercera pasada y por la compuerta en verde, no por un veredicto nuevo uno por uno.

### Lo que esta pasada encontró, sin veredicto propio

1. 📌 **La frase nueva de Agent tiene una excepción de borde.** "El plan conserva ese id" no vale
   para un id con forma de credencial: `_limpiar` redacta todo el documento salvo `meta`
   (`plan.py:298-299, 395-413`), y ese id sale como `[secreto redactado: …]`.
   - Lo que importa de la frase sigue siendo cierto: el plan no se limita al registro, y da
     `agentExists: false` y `AGENT_NOT_FOUND`.
   - El refutador lo clasificó como las imprecisiones de borde de la primera pasada, no como una
     afirmación falsa. También dijo que, aplicada al pie de la letra, la regla lo haría contradicho,
     y dejó esa decisión a quien pidió la verificación. El registro conserva su veredicto.
2. **La spec §5.1 Catalog dice "la disponibilidad la decide la validación del entorno"** sin aclarar
   "de las integraciones", y la I-21 arrastra lo mismo desde la primera verificación. Las locales
   están siempre disponibles. El documento canónico lo dice bien, y ninguna de las dos es un campo de
   concepto.
3. **La tabla de estados de la unidad en `docs/orquestacion.md` no dice la precedencia** de
   `plan.py:320-326`. Una unidad con hueco y aprobación queda en `WAITING_FOR_HUMAN_APPROVAL`, no en
   `BLOCKED`. La fila sigue siendo cierta leída de estado a significado.
4. **"`READY_FOR_EXECUTION` | No queda nada pendiente"** viene de `4c6f0f3`, y un plan queda en
   `READY` aunque tenga `agentExists: false`. Ningún concepto del documento canónico dice lo
   contrario.
5. **Ningún test cubre el subcaso de E-19 con un dominio desconocido.** Lo sostienen las
   reproducciones de la segunda y la tercera pasada.

### Lo que queda abierto

- **Los hallazgos 1 a 5** no bloquean: se corrigen en una pasada documental o se anotan en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
- **Si se prefiere aplicar la regla al pie de la letra al hallazgo 1,** E-02 vuelve a contradicho y
  la frase se corrige para nombrar la redacción de secretos.
- **La deuda que la spec dejó afuera** sigue en `PENDIENTES-FH.md`.
- **Cerrar la versión no es parte de esta verificación.**

**SPEC VERIFIED**
