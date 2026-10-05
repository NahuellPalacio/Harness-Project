# Informe de construcción — canonical-domain-model

**Escrito por:** la sesión que construyó el cambio · **Fecha:** 03-10-2026 · **Spec:**
[spec.md](spec.md) · **Línea de base:** 0.29.0 (`4c6f0f3`)

📌 **Esto no es un veredicto.** Dice qué se construyó, cómo se probó y qué quedó abierto, para que
`harness-spec-refuter` lo contraste contra la spec. Quien construyó no verifica.

## Resultado de la compuerta

```
.\tests\Invoke-Tests.ps1
775/775 pasaron (PowerShell).
38431/38431 pasaron.
39206/39206 pasaron.
exit=0 · 1429 s
```

Corrida el 03-10-2026 sobre el árbol de trabajo sin commitear, con stdin redirigido desde un archivo
vacío. `pre-tool-use.py` y `zonas.py` tenían después el mismo hash que antes (`61567f3` y `e996067`).
`VERSION`, `CHANGELOG.md` y `UPGRADE.md` no se tocaron: son del cierre.

**La corrida anterior dio rojo: 39205/39206, exit 1, en 1979 s.** Falló el E-16 de
`63-harness-unico-instalador.ps1`, que compara cada archivo instalado contra 0.28.0 y admite cinco
excepciones. Este cambio modifica once archivos instalados a propósito, y los casos puntuales que
corrieron los carriles no incluían ese `.ps1`. Se adaptó el test (ver `Cómo se probó`) y la compuerta
volvió a correr entera.

## Cómo se repartió el trabajo

| Carril | Quién | Qué |
|---|---|---|
| Dominio y planificación | un agente general | `plan.py`, `refutacion.py`, `dev-harness.py`, `libro.py`, `tarea.py`, `dev-orchestrator.md` |
| Schemas y contratos | un agente general | los tres schemas, `control-registry.json`, `controles.py`, los docstrings de `controles/checks/` y `integraciones/registro.py` |
| Documentación, ADR y pendientes | la sesión que orquestó | el documento canónico, ADR-0013, los cuatro docs, el README y `PENDIENTES-FH.md` |
| Tests y rojo visto | `harness-backend-engineer`, dueño de `tests/` | los dos casos `64_*`, las adaptaciones y las mutaciones |

Ningún archivo lo tocaron dos carriles. Los carriles de código corrieron solo casos Python puntuales:
ninguno corrió la compuerta mientras otro editaba.

## Qué se construyó

- **El documento canónico**, `docs/dominio/modelo-canonico.md`. `## Conceptos` abre con la tabla
  índice, que es la fuente del catálogo, y sigue con un `### <Concepto>` por fila, cada uno con los
  diez campos de E-02. Lleva:
  - el mapa de contextos: nueve contextos y Execution como límite reservado;
  - las doce clasificaciones;
  - las catorce desigualdades;
  - el vocabulario;
  - el límite de la ejecución;
  - lo que queda fuera del producto.

  El catálogo quedó en 68 conceptos, el mismo número que encontró el relevamiento. No es un
  contrato: E-01 no lo exige.
- **ADR-0013**, `docs/adr/0013-modelo-de-dominio-canonico.md`, aceptado, con las seis decisiones de
  D14. La regla de inclusión de D15 no está, porque es el criterio de alcance de esta Task.
- **`orchestration-plan/2.0`:**
  - `$id` y `meta.schema_version` dicen 2.0;
  - el plan tiene tres estados y la unidad otros tres, con `PENDING` definido como "planificada y sin
    nada que la frene";
  - las descripciones de `agents[].exists` y `agentExists` dicen que decide el registro y que el
    disco diagnostica;
  - el productor escribe solo 2.0 (`plan.py`, `VERSION_SCHEMA`).
- **La regla de lectura de un plan guardado**, `plan.aceptar_guardado`, que es una sola y la usan
  `refute --compile` (`refutacion._leer_plan`) y `--replanificar` (`dev-harness.planificar`). Acepta
  un 2.0, o un 1.0 cuyos estados existen en 2.0. Rechaza otra versión, la falta de versión y
  cualquier estado fuera de los conjuntos. El mensaje nombra el campo y el valor y pide regenerar con
  `plan --propuesta`. No convierte nada, no escribe, y corre antes de cualquier escritura del plan o
  de la refutación.
- **Los dos invariantes del Plan en `armar`:** ids de unidad únicos, y el dominio de cada unidad
  entre los del plan. Valen también en `--replanificar`, porque pasa por `armar`. El marcador interno
  `PLANNING` quedó como estaba (D4, D15).
- **`main` mapea `PlanInvalido` a código 2.** Antes se escapaba sin capturar, y E-18, E-19 y E-16b
  piden 2.
- **`seguridad` valida la TaskKey** en el bloque de `main` que corre antes de tocar el disco.
- **La LedgerKey**, en `libro.py`: `SESION` (UUID), `ClaveDeLibroInvalida` y
  `validar_clave(clave, es_clave_de_tarea)`. La llama `contabilidad` antes de abrir el libro. La
  `statusLine` no la usa y sigue escribiendo por el `session_id` que manda el Host. La regla de la
  TaskKey se pasa como parámetro para no escribir una tercera copia.
- **El conflicto de clave en el TaskContext:** si Jira devuelve otra clave, `tarea.py` lo anota en
  `gaps_and_conflicts.conflicts` con las dos. La clave pedida sigue en `meta.task_key`, en
  `context_id` y en el nombre del archivo.
- **`declaredChecks` sin GuardrailCheck:** la refutación dejó de unir `requiredChecks`. No cambian la
  `cacheKey`, los `REF-nnn` ni ningún veredicto (E-32, E-33).
- **Correcciones descriptivas:**
  - `execution-accounting-event`: la descripción general, la de `eventType` (donde estaba C-12) y la
    de `taskId`. El enum, el orden y los campos no cambian;
  - `normative-signal` nombra ES0901 y ES0902;
  - "PostToolUse" en `control-registry.json`, en `controles.py` y en los ocho docstrings de
    `controles/checks/` que decían que un check del hook corre en PreToolUse;
  - lo soportado lo declaran las clases, en `integraciones/registro.py` y `docs/integraciones.md`.
- **Docs:**
  - `docs/orquestacion.md`: los estados exactos, la 2.0 y la tabla de la regla de lectura;
  - `docs/contabilidad.md`: "La contabilidad no es estado de ejecución", y la LedgerKey;
  - el enlace en el README.
- **`dev-orchestrator.md`:** las dos reglas de la propuesta, y la 2.0 donde decía 1.0.
- **`PENDIENTES-FH.md`:** una sección nueva con los doce títulos de E-48, cada uno con sus
  contradicciones por número. Al ítem de `controles/` se le sumó el efecto sobre el C3 que encontró
  E-44.

## Compatibilidad 1.0 → 2.0, como quedó

| Caso | Qué pasa | Escenario |
|---|---|---|
| Un 2.0 | Se lee | E-16c, parte positiva |
| Un 1.0 de `4c6f0f3`, con estados que existen en 2.0 | `refute --compile` lo lee sin reescribirlo y compila las mismas unidades que la línea de base. `--replanificar` lo escribe como 2.0, con `plan_version` + 1 y toda la historia | E-16, E-45 |
| Un 1.0 con un plan `DELEGATING` o una unidad `READY` | Se rechaza con 2. El mensaje nombra el campo y el valor y pide regenerar. No se migra | E-16b |
| Otra versión, o ninguna | Se rechaza con 2, nombrando la versión | E-16c |

**Atomicidad observada.** En E-16b y E-16c se toman las huellas de `.claude/planes/<KEY>.json`, de
`.claude/refutaciones/<KEY>/` (preparada antes con unidades y `run.json`) y de
`.claude/refutaciones/cache/`. Las tres quedan iguales byte a byte. Los archivos que puede escribir la
compuerta normativa quedan fuera de la comparación, y el test los nombra. En E-26 se compara todo
`.claude/`, porque la clave se rechaza en `main`, antes de cualquier escritura.

## Cómo se probó

- **Casos nuevos:**
  - `tests/casos/64_modelo_de_dominio.py`, con 848 aserciones: cubre E-01 a E-43 y E-46 a E-48;
  - `tests/casos/64-modelo-de-dominio-instalador.ps1`, con 21: cubre E-44 y E-45.

  Cada aserción nombra su escenario. La línea de base sale de `git archive 4c6f0f3` en cada corrida,
  y su código corre en un proceso aparte, así que los módulos de las dos versiones no se cruzan. No se
  versionó ninguna copia de la línea de base.
- **Casos adaptados:**
  - `tests/casos/20_orquestacion.py`: E-01 espera `orchestration-plan/2.0`, y lo explica citando E-13
    y E-17;
  - `tests/casos/63-harness-unico-instalador.ps1`: su E-16 suma, en una lista aparte y nombrada, los
    once archivos instalados que este cambio modifica a propósito. Sigue cuidando que nada más se haya
    movido desde 0.28.0.
- **Rojo visto.** Lo hizo `harness-backend-engineer` sobre copias completas del repo con `.git`, en
  `%TEMP%`, sin tocar el árbol versionado. Quedan 50 escenarios en `si`. E-49 queda en `no consta`,
  porque es la compuerta misma. El registro, mutación por mutación, está en la spec, en
  `Cómo se verifica`.

## Desvíos respecto de la spec

1. **E-31 y E-44 se corrigieron durante la construcción**, porque tal como estaban escritos no se
   podían cumplir. Las dos causas ya existían en `4c6f0f3`:
   - **E-31** pedía que los `declaredChecks` fueran ids del `control-registry`. Pero la matriz de
     ES0901 declara 21 checks que todavía no están registrados ("NO existen todavía"), y llegan por el
     bloque normativo. Ahora pide exactamente los ControlCheck que declara la norma, y que ninguno sea
     un check del roster.
   - **E-44** excluía solo `normativeEvidence`. Pero la línea base del C3 depende de `controles/`,
     que no se instala. Ahora esa diferencia queda nombrada como la única, y el test comprueba que es
     la conocida.

   Las dos correcciones están en la spec, con una nota "Corregido durante la construcción". El
   refutador tiene que decidir si las acepta.
2. **El mapeo de `PlanInvalido` a código 2** vale para todo `PlanInvalido`, no solo para los
   escenarios nuevos: un ciclo de dependencias, que antes salía con un traceback, ahora sale con 2.
3. **`aceptar_guardado` mira los estados también en un 2.0.** D16 dice "un 2.0 se acepta". Un 2.0
   que escribió HARNESS siempre pasa; uno editado a mano con un estado eliminado se rechaza, igual
   que un 1.0, porque si no se aceptaría un artefacto que contradice I-16.
4. **`aceptar_guardado(documento, clave="")`** recibe la clave solo para el mensaje, cuando el plan
   no trae la suya. `SESION` usa `fullmatch`.
5. **Dos schemas que la tabla 3.2 dejaba sin concepto** (`database-environment-access-policy` y
   `database-profile`, dormidos) quedaron bajo NormativeMatrix y Evidence. Sin eso, E-05 no se
   cumplía.
6. **Ocho docstrings de `controles/checks/`** cambiaron PreToolUse por PostToolUse, aunque `Qué se
   construye` nombraba solo `control-registry.json` y `controles.py`. E-34 los alcanza, y el cambio
   es descriptivo (D15).
7. **La descripción de `eventType`** también cambió, porque ahí estaba el "los emite quien orquesta
   la ejecución" de C-12.
8. **`normative-signal`** dice "ES0902 v6.2" y no "§6.2": en el repo, 6.2 es la versión de ES0902.

## Hallazgos fuera de alcance

- **El C3 de un plan depende de `controles/`**, que no se instala. Lo encontró E-44, y quedó en el
  ítem de `controles/` de `PENDIENTES-FH.md`.
- **Los docstrings de `controles/checks/` todavía dicen que los checks del hook tienen "tres
  salidas".** Quedó en el ítem *Schemas that do not describe what their producers write*.

## Archivos

| | |
|---|---|
| Creados | `docs/dominio/modelo-canonico.md`, `docs/adr/0013-modelo-de-dominio-canonico.md`, `tests/casos/64_modelo_de_dominio.py`, `tests/casos/64-modelo-de-dominio-instalador.ps1`, este informe |
| Código | `harnesses/desarrollo/bin/orquestacion/plan.py`, `refutacion.py`, `controles.py` (docstring); `harnesses/desarrollo/bin/dev-harness.py`; `harnesses/desarrollo/bin/contabilidad/libro.py`; `harnesses/desarrollo/bin/contexto/tarea.py`; `harnesses/desarrollo/bin/integraciones/registro.py` (docstring); los ocho docstrings de `harnesses/desarrollo/controles/checks/` |
| Contratos y datos | `comun/schemas/orchestration-plan.schema.json`, `execution-accounting-event.schema.json`, `normative-signal.schema.json`; `harnesses/desarrollo/reglas/control-registry.json` |
| Instrucciones de modelo | `harnesses/desarrollo/agents/dev-orchestrator.md` |
| Documentación | `README.md`, `docs/orquestacion.md`, `docs/contabilidad.md`, `docs/integraciones.md`, `Pendientes/Fix-Harness/PENDIENTES-FH.md` |
| Tests adaptados | `tests/casos/20_orquestacion.py`, `tests/casos/63-harness-unico-instalador.ps1` |
| Spec | `docs/cambios/canonical-domain-model/spec.md`: el estado, las marcas de rojo visto, su registro, y las correcciones de E-31 y E-44 |

No se tocaron `dev-refutador.md`, ninguna `SKILL.md`, `VERSION`, `CHANGELOG.md` ni `UPGRADE.md`.

## Estado

READY FOR SPEC VERIFICATION. No conozco ninguna contradicción abierta contra la spec, salvo las dos
correcciones de E-31 y E-44, que tiene que aceptar quien verifica.

## Correcciones posteriores a la primera verificación

**Fecha:** 04-10-2026 · **Diagnóstico:** [verificacion.md](verificacion.md), con 48 sostenidos y 3
contradichos (E-02, E-05 y E-06).

Se construyó lo que pidió el veredicto y nada más. `verificacion.md` no se tocó: es la evidencia de
una verificación que falló, y una segunda pasada la registra quien verifica. Esta sección tampoco es
un veredicto.

### Los cinco bloqueantes

| | Qué decía el documento | Qué dice ahora | Código |
|---|---|---|---|
| S1 · Capability ≠ Tool | Que el plan prohíbe que una capability se llame como una HostTool | Que no hay ninguna prohibición en el contrato. `requiredCapabilities` no tiene patrón, y un `Read` pedido queda como CapabilityGap, con el plan en `CAPABILITY_RESOLUTION`. Lo único que es cierto es que ninguna capability *declarada* se llama así. Se corrigieron el apartado, los invariantes de Capability y de HostTool, I-20 y la fila de §4.3 | sin cambios |
| S2 · Check ≠ development test | Que GuardrailCheck y ControlCheck se instalan | Que se distinguen por su contrato, su ciclo de vida, su dueño y su mecanismo. El GuardrailCheck se instala, y `controles/` no (deuda conocida) | sin cambios; la instalación tampoco se tocó |
| S3 · Policy ≠ Check | Que G2 declara a propósito el mismo id como policy y como check | Que es un defecto de los datos, y que `seguridad.colisiones_de_id` lo diagnostica como `SECURITY_CONTROL_ID_TYPE_COLLISION`. Remite a la deuda *The provided ES0902 matrix declares one control id with two types* | sin cambios; G2 tampoco se tocó |
| S4 · `database-environment-access-policy` | Que es una NormativeMatrix | Que es una **DatabaseAccessPolicy**, concepto nuevo de Catalog (Domain Policy, dormida), que también se lleva `database-profile`, que antes figuraba en Evidence | sin cambios |
| S5 · ModelTierApproval | Que una aprobación `PENDING` deja el plan en `WAITING_FOR_HUMAN_APPROVAL` | Que eso pasa solo si no hay nada que pese más. La precedencia de `plan.estado_de` es: CapabilityGap, aprobación `PENDING`, unidad `BLOCKED`, y si no `READY_FOR_EXECUTION`. Se corrigieron el invariante y el ciclo del Plan | sin cambios; la precedencia es la de antes |

**Por qué S4 tuvo un concepto nuevo.** `bases.py` dice que no es una regla de ES0901, no está en
la matriz ni en el registro, y ningún módulo de producción la importa. Ninguno de los 68 conceptos
describía su contrato, que es qué operación sobre una base puede correr en cada ambiente, decidido
antes de conectar. El catálogo quedó en 69, y la spec se alineó en §3.2, §4.2 y el vocabulario.

**S3 encontró algo más mientras se probaba.** Ningún comando de producción llama
`colisiones_de_id`: solo lo llaman `37_es0902_seguridad.py` y `64_modelo_de_dominio.py`. El documento
y la spec ya no dicen que "el producto lo reporta", sino que el diagnóstico existe y que hoy ningún
comando lo emite. El docstring de `seguridad.py` y `docs/seguridad-es0902.md:869` dicen que "se
reporta". Eso quedó anotado en el mismo ítem de `PENDIENTES-FH.md`, y no se corrigió porque está
fuera de alcance.

### Hallazgos menores

- **Capability.** Las de integración son *soportadas* si las declara la clase, y *disponibles* si
  `setup` las validó `ENABLED`. Las locales salen de `capacidadesLocales` del roster:
  `capacidades.disponibles` las suma siempre, sin validarlas. Está en el documento y en el detalle de
  §4.2 de la spec.
- **GuardrailCheck.** Tiene dos fuentes:
  - `comun/checks/claude-md-zonas.py`, que corre siempre y no está en el roster;
  - `harnesses/desarrollo/checks/`, con los `dev-*` que lista el roster.
- **Agent y Skill.** El documento ya no dice que el AgentRegistry gobierna todo. Hay tres casos que
  no declara el registro:
  - `comun/agents/flush-memoria.md` y `leer-docs.md` se instalan sin estar declarados;
  - `comun/skills/instalar-desde-github` está en la misma situación;
  - `dev-iniciador-code` es un huérfano reconocido en `huerfanos-reconocidos.json`.
- **Installation.** El runtime valida contra la copia que lleva en línea `bienvenida.py`
  (`FORMA_INSTALACION`, a la que le falta `integrationConfiguration`). El schema solo lo usan los
  tests.

### I-25 y ControlCheck

Un check que declara una norma no es un ControlCheck registrado e instalado que pueda cerrar una
unidad. ControlCheck ahora tiene dos momentos:

- **declarado por la norma:** 21 de los 34 no están registrados (`DECLARED_CHECK_NOT_INSTALLED`);
- **registrado e `INSTALLED`:** es el único que puede cerrar.

`declaredChecks` lleva los checks que declara la norma, estén registrados o no, y nunca un
GuardrailCheck. Así quedaron I-25, la decisión 5 de ADR-0013, ControlCheck y RefutationUnit. E-31 no
cambió: no se filtra ningún id y no se agregan los 21 controles.

### Conteo de contradicciones

La tabla de §17 tiene 57 filas: de C-01 a C-55, más C-09b y C-17b. No se renumeró nada.

| Dónde | Cómo lo dice ahora |
|---|---|
| §1 de la spec | da el número como el de la tabla, no como una constante |
| ADR-0013 | "enumeradas en su sección 17" |
| `PENDIENTES-FH.md` | "57 entries as of this writing" |
| documento canónico | no lo menciona |

### PlanInvalido

- **Antes, en `4c6f0f3`:**
  - `main` no atrapaba `PlanInvalido`, así que un ciclo, una dependencia rota o una propuesta sin
    unidades salían con 1, por traceback, y no escribían nada;
  - el id repetido y el dominio fuera del plan no se controlaban: salían con 0 y escribían el plan.
- **En la primera construcción:** `main` mapeaba todo `PlanInvalido` a 2, y eso también cambiaba
  los casos que ya existían.
- **La solución:** una subclase, `PlanRechazado(PlanInvalido)`, en `plan.py`. La levantan solo el id
  repetido, el dominio fuera del plan y las cuatro ramas de rechazo de `aceptar_guardado`. En
  `dev-harness.py`, `main` atrapa `PlanRechazado` y nada más. D15 no se amplió.
- **Compatibilidad:**
  - los `PlanInvalido` que ya existían salen con el mismo código que en la base y no escriben;
  - los tres rechazos nuevos salen con 2;
  - `refute` sigue convirtiendo cualquier `PlanInvalido` de la lectura en `RefutacionInvalida`
    (`refutacion.py` no cambió);
  - en la spec, lo dicen el escenario nuevo **E-18b** y la fila de `plan.py` de *Qué se construye*.

### Tests

`harness-backend-engineer` tocó un solo archivo, `tests/casos/64_modelo_de_dominio.py`. Agregó 110
aserciones, y el caso pasó de 841 a **951/951**.

| Función | Qué prueba |
|---|---|
| `test_e02_s5_un_hueco_pesa_mas_que_una_aprobacion_pendiente` | comportamiento: las 8 combinaciones de hueco, aprobación `PENDING` y unidad `BLOCKED` contra `estado_de`, y los planes de E-21 |
| `test_e05_s4_cada_schema_esta_en_el_concepto_que_dice_la_spec` | cruza el documento contra la spec: cada concepto que §3.2 le asigna a un schema lo nombra; desde el código, `bases.py` no la importa nadie y ni la matriz ni el registro la nombran |
| `test_e06_s1_una_herramienta_del_host_pedida_es_un_hueco` | comportamiento en un proceso aparte: `["Glob","Read"]` sale con 0, escribe el plan en `CAPABILITY_RESOLUTION` con dos huecos, y el plan valida; el schema no pone patrón |
| `test_e06_s2_controles_no_se_instala` | el mapa de copias de `install.ps1` no tiene `controles` |
| `test_e06_s3_el_id_compartido_es_un_defecto_reportado` | `colisiones_de_id` sobre una matriz sintética y sobre la provista |
| `test_e18b_solo_los_rechazos_nuevos_salen_con_2` | contra `git archive 4c6f0f3`, en procesos aparte: mismo código de salida que la base para los tres de antes, y 2 para los nuevos; en ninguno se escribe ni se cambia el plan |
| `test_e25_plan_con_una_clave_invalida_no_escribe` (adaptado) | la llamada en proceso atrapa el `PlanInvalido` de `plan.escribir`, que vuelve a salir como en la base. Ninguna aserción cambió |

S1 y S5 se prueban con comportamiento, y S2, S3 y S4 con evidencia de código o estructural. Las
guardas de texto atan cada apartado a un hecho que está en otro lado y no comparan el documento
consigo mismo.

**Por qué E-02, E-05 y E-06 deberían quedar en verde:**

- **E-02:** el invariante de ModelTierApproval describe la precedencia que el código ejecuta.
- **E-05:** cada schema está en el concepto que describe su contrato, de acuerdo con §3.2.
- **E-06:** las tres desigualdades dicen lo que el código hace.

**Rojo visto.** Se buscó sobre copias completas del repo, `.git` incluido. Cada mutación de la
tabla nueva del registro de la spec (§15) puso en rojo la aserción que cuida, y E-18b pasó a `si`.

**Lo que no se vio en rojo:**

- las aserciones de control: que se leyó el mapa, que la tabla de §3.2 tiene los 46 schemas, y que
  el error nombra el caso;
- algunas variantes, como la del dominio fuera del plan en E-18b;
- E-21: con la precedencia invertida siguió en verde, y la precedencia la cubre solo E-02 S5.

Las guardas de texto son heurísticas: `_afirma_prohibicion` busca una negación cercana. Una
redacción nueva podría engañarlas, en los dos sentidos.

`20_orquestacion.py`, corrido después del cambio de `main`: 218/218.

### La compuerta

```
.\tests\Invoke-Tests.ps1
775/775 pasaron (PowerShell).
38534/38534 pasaron.
39309/39309 pasaron.
exit=0 · 1514 s
```

Corrió el 05-10-2026 sobre el árbol de trabajo sin commitear, como un proceso aparte y con stdin
redirigido desde un archivo vacío. Después de la corrida:

- `pre-tool-use.py` (`61567f3`) y `zonas.py` (`e996067`) tienen el mismo hash que antes;
- `git status` tiene las mismas 32 entradas que al empezar.

La primera corrida de esta pasada, la del 04-10-2026, la cortó Claude Code por falta de memoria del
sistema apenas arrancó, y no dejó resultado. El árbol también quedó intacto.

La compuerta sumó 103 tests a los 39206 de la primera construcción, todos en Python. Los 775 de
PowerShell no cambiaron.

### Archivos de esta pasada

| | |
|---|---|
| Código | `harnesses/desarrollo/bin/orquestacion/plan.py` (`PlanRechazado`), `harnesses/desarrollo/bin/dev-harness.py` (el `except` de `main`) |
| Documentación | `docs/dominio/modelo-canonico.md`, `docs/adr/0013-modelo-de-dominio-canonico.md`, `Pendientes/Fix-Harness/PENDIENTES-FH.md` |
| Spec | `spec.md`: §1, §3.2, §4.2, §4.3, I-20, I-25, el vocabulario, la fila de `plan.py`, E-18b, el registro del rojo visto y el riesgo del tamaño del catálogo |
| Tests | `tests/casos/64_modelo_de_dominio.py` |

No se tocaron:

- `verificacion.md`, `dev-refutador.md` ni ninguna `SKILL.md`;
- `VERSION`, `CHANGELOG.md` ni `UPGRADE.md`;
- la instalación de `controles/`, los datos de G2 ni la precedencia de `estado_de`.

Execution sigue sin implementarse.

### Estado de esta pasada

READY FOR RE-VERIFICATION. Alcanza con una segunda pasada focalizada en cuatro puntos:

- E-02, E-05 y E-06;
- el escenario nuevo E-18b;
- la comparación de `PlanInvalido` contra `4c6f0f3`;
- la no regresión de lo que ya estaba sostenido: D16 y la migración, la atomicidad, E-31, E-44,
  TaskKey, LedgerKey, el conflicto de Jira, los ids únicos y el dominio, la `cacheKey`, el
  `resolutionPath`, los veredictos y los `eventId`.

## Corrección final de E-02

**Fecha:** 05-10-2026 · **Diagnóstico:** `## Segunda verificación` de [verificacion.md](verificacion.md),
con 51 sostenidos y 1 contradicho (E-02).

Es una pasada documental. Solo cambió un comentario de código, y ningún comportamiento.
`verificacion.md` no se tocó: la tercera pasada la registra quien verifica. Esta sección tampoco es un
veredicto.

### E-02: la oración de Agent

- **Antes** (`modelo-canonico.md`, Agent, `Dónde vive`): "El plan solo asigna agentes del registro."
- **Ahora:** "El plan no se limita al registro. La propuesta puede pedir cualquier `assignedAgent` y
  el plan conserva ese id. El AgentRegistry decide si existe, y si no lo declara, la unidad lleva
  `agentExists: false` y `agentValidation: AGENT_NOT_FOUND` (`plan.py`,
  `roster.validacion_de_agente`). El plan no se rechaza por eso."
- **De dónde sale:**
  - `plan.py:313` toma `assignedAgent` de la propuesta;
  - `plan.py:337, 341` escribe `agentExists` y `agentValidation`;
  - `roster.validacion_de_agente` devuelve `AGENT_NOT_FOUND` para lo que el registro no declara.
- **Lo que no se hizo:** no se cambió código, el plan no empieza a rechazar agentes desconocidos y
  no se agregó ningún invariante.

### Las imprecisiones de la segunda verificación

| | Antes | Ahora |
|---|---|---|
| Capability | Disponible "si `setup` la validó" | Disponible si la última validación del entorno (`correr_bootstrap`) la encontró `ENABLED`. La corren los casos de uso que validan el entorno, y las locales no pasan por ella. También en Integration y en la fila Catalog del mapa. Donde la spec enumera comandos (§3.1), se verificaron todos en `main`: `setup`, `reconfigurar` y `estado` validan siempre; `contexto`, solo sin registro o con `--revalidar`; `fuentes`, `plan` y los demás no validan |
| DatabaseAccessPolicy | Identidad: "el ambiente" | La regla se identifica por el ambiente, y un perfil por el par (base lógica, ambiente) (`bases.clave_de_perfil`, `bases.py:664-670`). Cambió en el documento, en la fila de §4.2 y en la de `database-profile` de §3.2. La fila Catalog de §5.1 de la spec suma "ambiente", sin crear un contexto nuevo |
| GuardrailCheck (apartado "Check ≠ development test") | "en cada escritura de la sesión" | "en los eventos PostToolUse que alcanza el matcher configurado", hoy `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash\|PowerShell` (`comun/settings/hooks.plantilla.json:38`). No se tocó ningún hook |
| Comentario de E-31 (`refutacion.py:621`) | "Solo controles del registro." | "Los checks que declara la norma, esten o no en el registro; nunca un check del hook (GuardrailCheck)." Solo cambió el comentario: no cambió la lógica, no se filtra ningún id y E-31 no cambió |
| `docs/orquestacion.md` | "Lo que requiere aprobación deja el plan en `WAITING_FOR_HUMAN_APPROVAL`" | La aprobación pendiente da ese estado solo si no falta ninguna capacidad. La fila de la tabla dice lo mismo, y debajo va el orden de `plan.estado_de`: hueco → `CAPABILITY_RESOLUTION`; aprobación `PENDING` → `WAITING_FOR_HUMAN_APPROVAL`; unidad `BLOCKED` → `CAPABILITY_RESOLUTION`; si no, `READY_FOR_EXECUTION`. La frase venía de `4c6f0f3`, y se corrige porque contradice el modelo canónico |

### E-18b y E-19

Se acepta el cruce como parte de E-19. Una WorkUnit con un dominio desconocido también viola
`domain ∈ plan.domains`:

- `domains` solo admite dominios conocidos (`plan.py:188-192`), así que un dominio desconocido nunca
  puede estar en ese conjunto;
- por eso sale con 2, como pide E-19.

No se recupera el exit 1 para este subtipo, y no cambió el código. D15 no se amplía en general: el
caso queda absorbido por el invariante que este cambio introduce. La precisión quedó en la spec, debajo
de E-19.

### Tests

`harness-backend-engineer` tocó solo `tests/casos/64_modelo_de_dominio.py`, dentro de
`test_e23_el_registro_decide_si_un_agente_existe`. Agregó 7 aserciones, y el caso pasó de 951 a
**958/958**.

- **Dos de comportamiento:** la unidad conserva el `assignedAgent` que pidió la propuesta y da
  `agentValidation: AGENT_NOT_FOUND`.
- **Cinco atan la sección `### Agent` a lo que el test observó del plan:**
  - la sección existe;
  - no afirma que el plan solo asigna agentes del registro;
  - no afirma que rechaza un agente desconocido;
  - nombra el `agentExists` que escribió el plan;
  - nombra el `agentValidation` que escribió el plan.

  Las dos últimas buscan el valor sacado del plan, no un literal.
- **Refactor:** la lógica de negación de `_afirma_prohibicion` se extrajo a `_afirma`, sin cambiar lo
  que hace.

**Rojo visto,** sobre una copia del repo con `.git`:

| Mutación | Resultado |
|---|---|
| Vuelve "El plan solo asigna agentes del registro." | 957/958 |
| El párrafo vuelve a ser solo esa oración | 956/958 |
| "El plan rechaza uno desconocido", y sin `agentExists: false` | 956/958 |
| En el código, `validacion_de_agente` devuelve `ORPHAN_AGENT` | 956/958: el documento ya no nombra lo que escribe el plan |

### La compuerta

```
.\tests\Invoke-Tests.ps1
775/775 pasaron (PowerShell).
38541/38541 pasaron.
39316/39316 pasaron.
exit=0 · 1461 s
```

Corrió el 05-10-2026 sobre el árbol sin commitear, como un proceso aparte y con stdin vacío. La
referencia anterior era 39309: los 7 tests de más son las aserciones nuevas de E-23.

Después de la corrida:

- `pre-tool-use.py` (`61567f3`) y `zonas.py` (`e996067`) tienen el mismo hash que antes;
- `git status` sigue con 32 entradas.

### Estado de esta pasada

READY FOR FINAL RE-VERIFICATION. Alcanza con volver a verificar E-02. Del resto, conviene confirmar
cuatro cosas:

- que las imprecisiones de arriba ahora describen el código;
- que la precisión de E-19 en la spec se lee como se decidió;
- que el comentario de `refutacion.py` es lo único que cambió en código;
- que la compuerta sigue en verde.

### Archivos de esta pasada

| | |
|---|---|
| Documentación | `docs/dominio/modelo-canonico.md` (Agent, Capability, Integration, DatabaseAccessPolicy, el apartado "Check ≠ development test" y la fila Catalog del mapa), `docs/orquestacion.md` |
| Spec | `spec.md`: §3.1 (capacidades), §3.2 (`database-profile`), §4.2 (la identidad de DatabaseAccessPolicy), §5.1 (Catalog) y la precisión debajo de E-19 |
| Código | `harnesses/desarrollo/bin/orquestacion/refutacion.py`, solo el comentario |
| Tests | `tests/casos/64_modelo_de_dominio.py` |

No se tocaron `verificacion.md`, `plan.py`, `dev-harness.py`, `orchestration-plan/2.0`, D16,
`aceptar_guardado`, `PlanRechazado`, las claves, el AgentRegistry, la instalación de `controles/`,
G2, ninguna skill ni `dev-refutador.md`. Tampoco `VERSION`, `CHANGELOG.md` ni `UPGRADE.md`.
Execution sigue sin implementarse.
