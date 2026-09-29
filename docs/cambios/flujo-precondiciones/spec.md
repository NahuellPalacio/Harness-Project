# Flow Governance, Wave 1 — precondiciones del flujo, identidad del repositorio y localizador de inputs

**Estado:** verificado y cerrado · **Fecha:** 29-09-2026 · **Bloque:** transversal (no es un bloque nuevo)

## Qué problema resuelve

Hoy el harness avanza con información que le falta, y lo hace en silencio:

- `plan.estado_de` da `READY_FOR_EXECUTION` sin saber de qué repositorio es la tarea ni si la
  carpeta donde se trabaja es ese repositorio. Nadie compara el `origin` del checkout con el
  proyecto GitLab de la tarea: se asume que `cwd` es el repo correcto.
- `contexto/repositorio.referencia_de_proyecto` se queda con `GITLAB_PROJECT` si está, y si no con
  **la primera** URL de GitLab de la Ficha. Si las dos dicen cosas distintas, o la Ficha trae dos
  URLs, gana una sin que nadie se entere.
- Una unidad de trabajo cuyo agente el Agent Registry no rutea (`AGENT_NOT_FOUND`, huérfano,
  archivo que falta) queda `PENDING` y el plan sale listo: `agentExists: false` es un dato que nadie
  mira.
- `refute --compile` compila sobre cualquier plan, en cualquier estado: con aprobaciones pendientes,
  con un contexto de tarea que cambió después de planificar, o en otro checkout.
- `run.json` guarda `planFingerprint` desde 0.23.0 y nadie lo compara: si el plan se reescribe
  después de compilar, `--unit` y `--record` siguen trabajando sobre unidades de otro plan.
- Cuando falta una variable del `.env`, el harness dice su nombre y nada más. No hay un código que
  sepa en qué línea está, o dónde agregarla, sin mostrar el valor.

## Qué queda afuera

- **Los hooks y el flow gate por turno.** Es la Wave 3. Esta Wave deja el cálculo que los hooks van
  a leer; ningún hook cambia.
- **El estado por tarea en `.claude/runtime/tasks/`, `resumeFrom` y la reanudación.** Son las Waves
  2 y 4. Acá una compuerta dice "no" y por qué; no guarda en qué punto retomar.
- **Un comando de la CLI para el localizador.** El módulo existe y se prueba como biblioteca; quien
  lo muestra en VS Code es la Wave 3, y agregarle hoy una superficie de CLI es decidir su forma antes
  de quien la usa.
- **Compuertas sobre `contexto`, `--unit` y `--record`.** La Wave nombra solo `refute --compile`.
  `--unit` y `--record` ganan únicamente el chequeo de plan viejo, que es lo que el punto 9 pide.
- **`refutacion.compilar` como biblioteca.** Queda como en 0.23.0: la compuerta es del comando.
  Meterla adentro obligaba a reescribir el fixture de los 61 escenarios de la refutación atómica,
  que es una versión cerrada.
- **Sacar `AlmacenSecretos.set/remove`.** Nadie los llama desde 0.26.0, pero la spec de
  `entorno-primero` decidió dejarlos en la interfaz y tienen tests de esa versión. Queda anotado.
- **Cambiar cómo resuelve `contexto/repositorio.py`.** Sigue resolviendo como antes para armar el
  TaskContext. El conflicto lo detecta la identidad del repositorio, que lee lo mismo y no elige.
  Lo único que se toca ahí es sacar a una constante los campos de la Ficha donde se busca la URL,
  para que los dos lean los mismos.
- **Nuevos estados de integración.** Siguen siendo los cinco de `base.py`.

## Las decisiones, y por qué

### Flow Governance es un paquete, no un bloque

`harnesses/desarrollo/bin/flujo/` tiene cuatro módulos: `requeridos` (el registro de inputs),
`repositorio` (la identidad), `precondiciones` (la evaluación de una etapa y la compuerta de la
refutación) y `entrada_humana` (el localizador y el renderizador). No absorbe nada de los bloques:
lee el TaskContext, el OrchestrationPlan, el Agent Registry y el contrato de entorno, que siguen
siendo la fuente de su dato.

### El registro de inputs es un archivo de `reglas/`

`harnesses/desarrollo/reglas/flow-required-inputs.json`, con forma
`comun/schemas/flow-required-inputs.schema.json`. Se instala y se pisa en cada `-Update`, como
todo `reglas/`. Cada entrada dice `stage`, `inputId`, `classification`, `interactionType`,
`sourceOfTruth`, `derivableFrom`, `blocking`, `askUser`, `failureCode` y `persistentTarget`.

Lo que el cargador rechaza (`FLOW_REQUIRED_INPUTS_INVALID`), porque es una contradicción:

- `HARD_BLOCKER` con `blocking: false`, o `SOFT_DEPENDENCY`/`OPTIONAL` con `blocking: true`.
- `DERIVABLE` con `askUser: true`, o sin `derivableFrom`. Al usuario no se le pregunta lo que el
  harness puede calcular.
- `interactionType: null` en algo que no es `DERIVABLE`.
- `PERSISTENT_CONFIG_INPUT` sin `persistentTarget` o con `askUser: true`: eso se completa en un
  archivo, no en el chat.
- Un `persistentTarget` en `.env` cuya variable no esté en `integration-environment-contract`, o
  que declare su propia `sensitivity`: la sensibilidad de una variable del `.env` sale del
  contrato, que es la autoridad. Cualquier otro archivo la declara.
- Un `persistentTarget` en `.claude/harness.integraciones.json`
  (`FLOW_INPUT_TARGET_NOT_HUMAN`). Es una proyección generada desde 0.26.0, no un input humano.

### Una pregunta HARD_BLOCKER es un input bloqueante que no se resolvió

La evaluación de una etapa recibe hechos (`inputId → resuelto sí/no`) y devuelve `READY` o
`BLOCKED`, con una `question` por input sin resolver: su clasificación, tipo de interacción, código,
si bloquea y si se le pregunta a la persona. Solo bloquea lo que el registro declara bloqueante
**para esa etapa**. Un `SOFT_DEPENDENCY` sin resolver aparece como pregunta con `blocking: false` y
no cambia el estado. Un input bloqueante de la etapa del que no llegó ningún hecho se cuenta como
no resuelto: lo que no se evaluó no pasa.

### La identidad del repositorio compara, no elige

La tarea declara su repositorio por hasta tres lados: `GITLAB_PROJECT` (vía `entorno.py`), las URLs
de GitLab de la Ficha y el `web_url` que GitLab devolvió al armar el TaskContext. Cada uno se
normaliza a `host/grupo/proyecto`: minúsculas, sin esquema, sin usuario ni contraseña, sin puerto,
sin `.git` y sin barras sobrantes. `git@host:g/p.git`, `ssh://git@host:22/g/p.git` y
`https://host/g/p` son la misma identidad.

- Dos declaraciones distintas son `REPOSITORY_CONFLICT`, incluidas dos URLs distintas en la misma
  Ficha. La identidad no nombra a ninguna como la de la tarea.
- Ninguna declaración, o solo un id numérico que el TaskContext no resolvió, es
  `REPOSITORY_UNRESOLVED`.
- Del checkout se leen **todos** los remotos con `git remote -v`: es local, no toca la red. Sin
  repositorio git o sin remotos, `LOCAL_REPOSITORY_UNRESOLVED`. Con remotos y ninguno igual al de la
  tarea, `MISMATCH` / `REPOSITORY_MISMATCH`. Con alguno igual, `MATCHED`. Que coincida un remoto
  cualquiera no es elegir: se compara contra un objetivo que ya está fijo.
- Lo que se guarda son identidades normalizadas, nunca la URL del remoto. Una URL con un token
  adentro (`https://oauth2:glpat-…@host/…`) no llega a ningún archivo.

El estado de la identidad es uno de tres: `MATCHED`, `MISMATCH` o `UNRESOLVED`, y el código dice
cuál de los cuatro inputs de repositorio falló.

### `GITLAB_PROJECT` se lee con `entorno.resolver`, sin escribir

`plan` y `refute --compile` resuelven el contrato contra el `.env` de solo lectura: no regeneran la
proyección ni la leen como fuente. Es el camino de 0.26.0,
`.env → contrato → entorno.py`, y un `.env` roto hace fallar el comando en vez de dar una
identidad sin la declaración principal.

### El plan gana `BLOCKED` y `flowPreconditions`

El schema `orchestration-plan/1.0` suma, sin romper lo anterior, el estado `BLOCKED`, el bloque
opcional `flowPreconditions` (`stage`, `status`, `questions`, `repository`) y, en cada unidad,
`blockers` opcional. `estado_de` calcula en este orden:

```
flowPreconditions ausente, no READY o con una pregunta bloqueante   -> BLOCKED
capabilityGaps                                                      -> CAPABILITY_RESOLUTION
una aprobación PENDING                                              -> WAITING_FOR_HUMAN_APPROVAL
una unidad BLOCKED                                                  -> CAPABILITY_RESOLUTION
lo demás                                                            -> READY_FOR_EXECUTION
```

Un plan sin `flowPreconditions` —uno de antes, o uno que se armó sin evaluarlas— es `BLOCKED`. Es la
migración que esta Wave declara: `READY_FOR_EXECUTION` pasa a exigir repositorio resuelto y local
coincidente. Los tests de `20_orquestacion.py` que esperaban `READY` sin identidad ahora la reciben
en el fixture y dicen `pisado por docs/cambios/flujo-precondiciones/spec.md`.

### Una unidad con agente no ruteable queda BLOCKED

`plan` pregunta a `registro_agentes.resolver_ruteo`, la validación canónica del Agent Registry. Si
no rutea, la unidad queda `BLOCKED` con `blockers: [{"inputId": "agents.routing", "code": <result>}]`
—`AGENT_NOT_FOUND`, `ORPHAN_AGENT` o el estado del registro, tal cual— y el input
`agents.routing`, que es `DERIVABLE`, bloquea la etapa sin preguntarle nada a nadie.

### La compuerta de la refutación es del comando

`refute --compile` evalúa la etapa `REFUTATION` antes de compilar: plan `READY_FOR_EXECUTION`
recalculado (no el que dice el archivo), `context_hash` del plan igual al del TaskContext actual y
ese igual a su hash recalculado, y repositorio local `MATCHED`. Si algo falla sale con 2, nombra los
códigos (`PLAN_NOT_READY`, `CONTEXT_STALE`, `REPOSITORY_MISMATCH`) y no crea ni toca `run.json`.

### El plan viejo invalida la corrida

`planFingerprint` sigue siendo `huella(plan)` del documento entero, como en 0.23.0. `--unit` y
`--record` lo comparan con la huella del plan actual; si difieren, `REFUTATION_PLAN_STALE` y no
se escribe nada. Cualquier reescritura del plan —un `plan` nuevo o una replanificación— deja
vieja la corrida hasta el próximo `--compile`, que cuesta poco porque la caché exacta sigue valiendo.

### El localizador ubica y nunca escribe

`entrada_humana.localizar(inputId, proyecto)` sale de un `persistentTarget` y devuelve
exactamente `inputId`, `file`, `absolutePath`, `line`, `column`, `key`, `present`, `format`,
`sensitivity`, `vscodeUri` y `fallback`. Nada más. `vscodeUri` es un enlace que abre el archivo;
no es una integración nativa con VS Code, que el harness sigue sin proveer.

- El `.env` se recorre con el parser de `integraciones/almacen.py` (la misma expresión, con una
  función nueva que da posiciones sin valores). La línea es la de la **primera** asignación, que es
  la que lee `AlmacenSecretos.get`.
- `present` es si esa asignación tiene un valor no vacío y que no es un placeholder `<…>`. El valor
  se mira y se tira.
- Si la clave no está, la línea es la siguiente a la última del archivo y la columna 1: agregar al
  final de un `.env` no rompe nada. En JSON, la línea siguiente a la llave que abre el objeto.
- `vscodeUri` es `vscode://file/` + la ruta absoluta con `/`, la letra de unidad en mayúscula y los
  caracteres que no van en una URI codificados (un espacio es `%20`), + `:línea:columna`.
  `fallback` es la misma ruta sin codificar, para pegar en el buscador de archivos.
- Una clave con forma de secreto (la heurística de `config.py`) es `SECRET` aunque su archivo diga
  otra cosa.

El renderizador arma la instrucción en español para `dotenv`, `json`, `yaml`, `toml`,
`properties` e `ini`, siempre con un placeholder en el lugar del valor. Si es `SECRET`, agrega que
no se pegue en el chat. Un formato desconocido es `INPUT_FORMAT_UNRESOLVED`.

### Los criterios de aceptación son SOFT en la planificación

`campoCriteriosAceptacion` vacío deja al TaskContext sin criterios, pero el plan se puede armar: los
criterios importan para verificar, no para decidir las unidades. Es `SOFT_DEPENDENCY` de
`PLANNING`, con `persistentTarget` en `.claude/harness.config.json`. Si se quiere más duro, es un
cambio de una línea en el registro.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/flow-required-inputs.schema.json` | La forma del registro de inputs |
| `harnesses/desarrollo/reglas/flow-required-inputs.json` | Los inputs de `CONTEXT`, `PLANNING` y `REFUTATION` |
| `harnesses/desarrollo/bin/flujo/requeridos.py` | Carga y valida el registro contra el contrato de entorno |
| `harnesses/desarrollo/bin/flujo/repositorio.py` | Normaliza, lee los remotos y da `MATCHED`/`MISMATCH`/`UNRESOLVED` |
| `harnesses/desarrollo/bin/flujo/precondiciones.py` | Evalúa una etapa; los hechos de `PLANNING`; la compuerta de `REFUTATION` |
| `harnesses/desarrollo/bin/flujo/entrada_humana.py` | El localizador y el renderizador |
| `harnesses/desarrollo/bin/integraciones/almacen.py` | `posiciones(lineas)`: nombre, línea y columna, sin valor |
| `harnesses/desarrollo/bin/contexto/repositorio.py` | `CAMPOS_DE_FICHA`, la misma lista que ya usaba, como constante |
| `harnesses/desarrollo/bin/orquestacion/plan.py` | `precondiciones`, `flowPreconditions`, `BLOCKED`, unidades con `blockers` |
| `harnesses/desarrollo/bin/orquestacion/refutacion.py` | `REFUTATION_PLAN_STALE` en `--unit` y `--record` |
| `harnesses/desarrollo/bin/dev-harness.py` | `plan` evalúa `PLANNING`; `refute --compile` pasa por la compuerta |
| `comun/schemas/orchestration-plan.schema.json` | `BLOCKED`, `flowPreconditions`, `blockers` |
| `tests/casos/61_flujo_precondiciones.py` | Los escenarios de esta spec |
| `tests/casos/20_orquestacion.py`, `tests/casos/55_refutacion_atomica.py` | El fixture de los escenarios pisados |

## Escenarios verificables

`E-nn` es `W1-0nn` del paquete de la Wave. Los que la Wave no numeraba van de E-21 en adelante.

### La identidad del repositorio

- **E-01** — `git@gitlab.example:Grupo/Proyecto.git`, `ssh://git@gitlab.example:22/grupo/proyecto.git`
  y `https://usuario@gitlab.example/grupo/proyecto/` normalizan igual, y un checkout con cualquiera
  de ellos como remoto, contra una tarea de `https://gitlab.example/grupo/proyecto`, es `MATCHED`.
  · rojo visto: si
- **E-02** — Una tarea de `grupo/a` en un checkout cuyo único remoto es `grupo/b` es `MISMATCH` con
  `REPOSITORY_MISMATCH`. · rojo visto: si
- **E-03** — Un repositorio git sin remotos, y una carpeta que no es repositorio git, son
  `UNRESOLVED` con `LOCAL_REPOSITORY_UNRESOLVED`. · rojo visto: si
- **E-04** — Sin `GITLAB_PROJECT` ni URL de GitLab en la Ficha, la identidad es `UNRESOLVED` con
  `REPOSITORY_UNRESOLVED`, y `plan` escribe un plan `BLOCKED` con la pregunta `repository.task`
  `HARD_BLOCKER`. · rojo visto: si
- **E-05** — `GITLAB_PROJECT=grupo/a` con una Ficha que nombra `grupo/b` es `REPOSITORY_CONFLICT`
  `HARD_BLOCKER` y la identidad no nombra repositorio de la tarea; lo mismo con dos URLs distintas en
  la Ficha. · rojo visto: si

### El estado del plan

- **E-06** — Con agentes ruteables, sin huecos ni aprobaciones, y un solo input `HARD_BLOCKER` sin
  resolver (`repository.match`), el plan es `BLOCKED`, y lo mismo con un solo `DERIVABLE`
  bloqueante (`planning.taskContext`); y ponerle `READY_FOR_EXECUTION` a mano no
  cambia lo que da `estado_de`. · rojo visto: si
- **E-07** — Con todo resuelto salvo `campoCriteriosAceptacion`, el plan es `READY_FOR_EXECUTION` y
  lleva la pregunta `task.acceptanceCriteriaField` con `blocking: false`. · rojo visto: si
- **E-08** — Una unidad asignada a un agente que el registro no declara queda `BLOCKED` con
  `blockers` `agents.routing` / `AGENT_NOT_FOUND`, el plan es `BLOCKED`, y la pregunta
  `agents.routing` tiene `askUser: false`. · rojo visto: si

### La compuerta de la refutación

- **E-09** — Con una aprobación pendiente, `refute --compile` sale con 2, dice `PLAN_NOT_READY` y no
  hay `run.json`. · rojo visto: si
- **E-10** — Con un TaskContext cuyo hash no es el que dice el plan, o que fue editado después de
  escribirse, `refute --compile` sale con 2 con `CONTEXT_STALE`. · rojo visto: si
- **E-11** — En un checkout de otro repositorio, `refute --compile` sale con 2 con
  `REPOSITORY_MISMATCH`, no crea `run.json` y deja byte a byte igual uno que ya existía.
  · rojo visto: si
- **E-12** — Después de compilar, un plan reescrito hace que `--unit` y `--record` salgan con 2 con
  `REFUTATION_PLAN_STALE`, sin escribir veredictos. · rojo visto: si

### El localizador

- **E-13** — Para `jira.token`, con `JIRA_TOKEN` en la línea 5 del `.env`, el localizador da
  `line: 5`, `column: 1`, `key: JIRA_TOKEN`, `format: dotenv`, `sensitivity: SECRET`, y
  `present` según haya valor o no. · rojo visto: si
- **E-14** — La salida del localizador tiene exactamente sus once campos, ninguno se llama `value`,
  `rawLine`, `token`, `password`, `secret` ni `credential`, y su JSON no contiene el token ni
  ningún otro valor del `.env`. · rojo visto: si
- **E-15** — Sin la clave en el `.env`, la línea es la siguiente a la última del archivo, la
  columna 1 y `present: false`; sin `.env`, la línea 1. · rojo visto: si
- **E-16** — `C:\Work\app\.env` en la línea 12 da `vscode://file/C:/Work/app/.env:12:1` y
  `fallback` `C:/Work/app/.env:12:1`; `c:\Mis Proyectos\app\.env` da `vscode://file/C:/Mis%20Proyectos/app/.env:…`;
  y dos llamadas dan lo mismo. · rojo visto: si
- **E-17** — El renderizador de `dotenv` escribe `JIRA_TOKEN=<…>` y nunca el valor, agrega "No
  pegues" para un `SECRET`, los seis formatos rinden, y un formato desconocido es
  `INPUT_FORMAT_UNRESOLVED`. · rojo visto: si
- **E-18** — Después de localizar, planificar y pasar por la compuerta, el `.env` queda byte a byte
  igual; y el código de `bin/flujo/` no abre ningún archivo para escribir. · rojo visto: si
- **E-19** — Ningún input del registro de la fábrica apunta a `harness.integraciones.json`, el
  cargador rechaza uno que lo haga con `FLOW_INPUT_TARGET_NOT_HUMAN`, y el localizador tampoco lo
  ubica. · rojo visto: si

### El registro y lo que no cambia

- **E-21** — El registro de la fábrica valida contra su schema, y el cargador rechaza con
  `FLOW_REQUIRED_INPUTS_INVALID` un `HARD_BLOCKER` no bloqueante, un `DERIVABLE` que pregunta, un
  `PERSISTENT_CONFIG_INPUT` sin destino, una variable de `.env` fuera del contrato y una clasificación
  desconocida. · rojo visto: si
- **E-22** — La misma evaluación, la misma identidad y la misma ubicación, dos veces, dan el mismo
  JSON byte a byte. · rojo visto: si
- **E-23** — Con un remoto `https://oauth2:<token>@gitlab.example/grupo/proyecto.git`, ni la
  identidad ni el plan escrito contienen el token ni `oauth2`. · rojo visto: si
- **E-24** — `integration-environment-contract.json`, `entorno.py` y los cinco estados de
  `integraciones/base.py` son los mismos que en `6cff4b4`. · rojo visto: si

### La compuerta

- **E-20** — `.\tests\Invoke-Tests.ps1` sale en verde, con los dos motores. · rojo visto: no consta

## Cómo se verifica

Todos por la suite, en `tests/casos/61_flujo_precondiciones.py`. E-01 a E-03 y E-23 arman
repositorios git de verdad en una carpeta temporal, con remotos que no existen: `git remote -v` no
sale a la red. E-24 compara contra `6cff4b4` con `git show`. E-20 es la corrida entera. Ninguno se
lee: no hay un modelo en el camino.

`tests/casos/20_orquestacion.py` (E-02, E-23, E-33b) y `tests/casos/55_refutacion_atomica.py`
(E-53) cambian solo el fixture: le dan al plan un repositorio `MATCHED` y un TaskContext vigente, y
siguen afirmando lo mismo.

## Riesgos conocidos

- **Un monorepo o un fork con otro nombre.** Si el checkout es un fork cuyo `origin` no es el
  proyecto de la tarea y ningún otro remoto lo es, el plan queda `BLOCKED`. Es a propósito; la salida
  es agregar el remoto del proyecto o corregir `GITLAB_PROJECT`.
- **Las mayúsculas del path.** Se comparan en minúsculas, como las trata GitLab. Una instancia que
  distinga mayúsculas daría `MATCHED` entre dos proyectos que difieren solo en eso.
- **Un id numérico en `GITLAB_PROJECT`.** Sin un TaskContext que lo haya resuelto contra GitLab no se
  puede comparar con un remoto, y el repositorio queda sin resolver hasta correr `contexto`.
- **La biblioteca sin compuerta.** `refutacion.compilar` llamado directo no pasa por la compuerta.
  El único que lo llama en producción es el comando, y la Wave 3 va a cerrar el camino por los hooks.
- **Cualquier reescritura del plan vence la corrida.** Incluso una que no cambió nada útil. Es
  fail-closed y cuesta un `--compile`.
