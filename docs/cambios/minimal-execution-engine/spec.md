# Minimal Execution Engine: una WorkUnit, un intento, persistido y terminal

**Estado:** cerrada el 13-10-2026 y publicada en 0.32.0: refutada el 09-10-2026 (4 contradichos), enmendada (§34),
corregida y reverificada, con ME-E50 leído y firmado
([`verificacion.md`](verificacion.md), «Cierre formal de Task 4»)
· **Fecha:** 08-10-2026; revisada el mismo día
(MD-22 a MD-24, MD-04d, ME-I28 a ME-I31, ME-E52 a ME-E55, §33.1) y construida el mismo día
([`informe-de-construccion.md`](informe-de-construccion.md)) · **Versión de partida:** 0.31.0 (`fdca5ce`), con Task 3 integrada y reverificada,
sin commitear

Esta spec es la Task 4. Convierte el contrato de ejecución de Task 3
([`docs/cambios/execution-contract/spec.md`](../execution-contract/spec.md), ADR-0014) en un motor
mínimo real: admite, crea la Execution, la persiste, la entrega a un Host Adapter, recibe un
AgentReport, registra la evidencia y deja un ExecutionResult terminal. Se escribió antes de
construir: la construcción está en [`informe-de-construccion.md`](informe-de-construccion.md), la
refutación en [`verificacion.md`](verificacion.md), y lo que esa refutación obligó a cambiar, en §34.

Abreviaturas:

- `bin/` es `harnesses/desarrollo/bin/`, `reglas/` es `harnesses/desarrollo/reglas/` y `hooks/` es
  `comun/hooks/`;
- **T3** es la spec de Task 3, y sus secciones se citan `T3 §n`;
- **MC** es `docs/dominio/modelo-canonico.md`;
- **FH** es `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

📌 **Los ids.** Los escenarios son `ME-Enn`, los invariantes `ME-Inn`, las contradicciones `ME-nn`,
las decisiones `MD-nn` y las decisiones diferidas `MP-nn`. El prefijo `ME-` separa esta Task de los
`EX-` de Task 3. Para el método de `CLAUDE.md`, un `ME-Enn` es un `E-nn` con todas sus reglas,
`rojo visto` incluido.

---

## 1. Problema

Task 3 dejó un contrato verificado y nada que lo produzca:

- `execution-request/1.0` y `execution-result/1.0` existen, y nadie escribe ninguno;
- la regla de admisión de 15 condiciones (T3 §37.5) está escrita, y ningún código la aplica;
- el ciclo `REQUESTED → RUNNING → terminal` está fijado, y ninguna Execution lo recorre;
- la reserva atómica de la `idempotencyKey` (EX-I28) es obligatoria, y no hay mecanismo;
- el AgentReport `{declaredStatus, artifact}` es el único contrato de salida, y ningún Host Adapter
  lo produce.

Mientras tanto, la única forma de que un especialista trabaje una WorkUnit es que el modelo de una
sesión de Claude Code lo delegue con la herramienta `Agent`, sin admisión, sin identidad, sin
evidencia y sin resultado registrado (§4.1). Un plan `READY_FOR_EXECUTION` termina en "Hand it over"
(`agents/dev-orchestrator.md:123`), y nadie lo recibe (EC-13).

**La pregunta de esta Task:** ¿cuál es la implementación mínima que convierte un ExecutionRequest
válido en una Execution persistida y terminal, manteniendo idempotencia, atomicidad, evidencia y
separación del Host?

**La respuesta corta**, que el resto de la spec justifica:

- un subcomando `ejecutar`, que corre **una** WorkUnit **una** vez, sincrónico;
- un registro por Execution bajo `.claude/ejecuciones/<TaskKey>/`, de archivos que se escriben una
  sola vez;
- la reserva atómica por **turnos de intento** que se crean de forma exclusiva;
- un Host Adapter que lanza `claude -p` con la salida estructurada del propio Host
  (`--json-schema`), así que nadie interpreta texto;
- la admisión de T3, aplicada dos veces, leyendo cada condición de su dueño.

## 2. Baseline

| Qué se verificó | Resultado |
|---|---|
| `HEAD` | `fdca5ce86e73ea2a47ad3745ff850310e88f80f5`, en `main`, tag `v0.31.0` |
| `VERSION` | `0.31.0` |
| `git status` | Cinco modificados (`PENDIENTES-FH.md`, `PENDIENTES-I.md`, `modelo-canonico.md`, `63-harness-unico-instalador.ps1`, `64_modelo_de_dominio.py`) y diez nuevos: los de Task 3 |
| Task 3 | Integrada con 0.31.0 y reverificada el 08-10-2026: 70 sostenidos, 0 contradichos, 0 sin sustento, suite 43201/43201 (`docs/cambios/execution-contract/verificacion.md`, sección final) |
| Stash | `task3-execution-contract-sobre-0f8b725`: la copia de resguardo de Task 3. No se toca |
| `.claude/ejecuciones/` | No existe |
| Host instalado | Claude Code `2.1.294`, por `claude --version` en esta máquina |

🔴 **Task 4 se construye encima del árbol de trabajo de Task 3, sin commit.** No reescribe ni pierde
ese trabajo. Si Task 3 se commitea antes de construir, la base de Task 4 pasa a ese commit, y la
spec no cambia por eso.

## 3. Scope y no scope

### 3.1 Qué se construye

#### MD-02. Una WorkUnit, un intento, sincrónico, por invocación

Una ejecución mínima real: **una request, una WorkUnit, un intento**, sincrónica, con un solo Host
Adapter (Claude Code, en modo headless). El proceso que pide es el que entrega y el que espera el
resultado. No hay cola, ni proceso de fondo, ni un segundo intento automático. La sección 31 lista
los artefactos.

### 3.2 Qué queda afuera, y por qué

- **Graph Execution, DAG, scheduler, colas, workers, paralelismo y lotes.** Son Task 5 (T3 P2, P10).
  Esta Task corre una unidad por invocación; elegir la siguiente es de quien invoca.
- **LangGraph, LangChain y cualquier framework de agentes.** El Host ya corre agentes; HARNESS no
  agrega un segundo runtime.
- **Reanudación y checkpoints** (T3 P9). Una Execution interrumpida termina `FAILED` con
  `HOST_INTERRUPTED` y se reintenta con otra Execution.
- **Reintento automático y backoff** (T3 P1). Un reintento lo pide una persona: es otra Execution con
  la misma clave.
- **Reusar resultados entre versiones del plan** (T3 P12). Una dependencia se satisface solo dentro
  de la misma huella.
- **Replanificar.** Execution rechaza; replanificar es de Planning.
- **Una abstracción general de proveedores o de Hosts.** Hay un solo adaptador. La frontera queda
  limpia para un segundo, que no se escribe.
- **Eventos contables** (T3 P5). No bloquean esta Task: la correlación queda por
  `host.sessionRef` y por el `contabilidad --ingerir` de hoy (MD-21).
- **Proyectar la evidencia a la refutación o al ledger de seguridad** (T3 P4). Es la Task que
  conecte Execution con Governance.
- **Resolver capacidades de integración para el agente** (EC-08). El adaptador declara que no las
  provee, y la unidad se rechaza.
- **Cambiar Flow Governance, el plan 2.1, los hooks, la política de herramientas, el vínculo de
  sesión, la intención humana, el registro de agentes, la contabilidad, `install.ps1` o
  `manifest.json`.** Esta Task los consume. Lo que les falta va a pendientes (§30).
- **RAG, una Knowledge API y una capa de intención.** No están en el pedido.
- **`VERSION`, `CHANGELOG.md` y `UPGRADE.md`.** Son de `close-a-version`.

## 4. Discovery AS-IS

El relevamiento se hizo el 08-10-2026 sobre el árbol de trabajo, con cuatro búsquedas
independientes: la delegación y el Host, la persistencia, la admisión y la semántica de Claude Code.
Las citas `archivo:línea` son de ese árbol.

### 4.1 Cómo se delega hoy

**Ningún código de `bin/` ni de `comun/` lanza un agente, la CLI `claude` ni un SDK de modelos.** La
única llamada al binario `claude` del repo es `install.ps1:451`, que pide `--version`. Lo único que
corre un agente es la herramienta `Agent`/`Task` del Host, llamada por el modelo de una sesión:

- entra `{description, prompt, subagent_type}` y vuelve al modelo **solo el texto final** del
  subagente, sin estado estructurado (docs de Claude Code, `tools-reference`);
- la PreToolUse la clasifica `WORKFLOW_ADVANCING`, etapa `EXECUTION`
  (`hooks/lib/tool_policy.py:1504-1505`), y la compuerta del flujo la deja pasar si la tarea de la
  sesión puede avanzar (`hooks/lib/flow_gate.py:159`);
- ninguna PostToolUse ni otro hook observa lo que devuelve el subagente: no hay hook `Stop`,
  `SubagentStop` ni `SessionEnd` (`comun/settings/hooks.plantilla.json:16-48`).

**La refutación es el único precedente de punta a punta**, y es "HARNESS entrega, el Host corre,
HARNESS registra y valida":

| Paso | Quién | Qué |
|---|---|---|
| Compilar | la sesión corre `refute <KEY> --compile` | compuerta normativa y de REFUTATION, unidades, `run.json` (`orquestacion/refutacion.py:960-1036`) |
| Entregar | la sesión corre `refute <KEY> --unit REF-001` | imprime la unidad por stdout; no escribe nada (`refutacion.py:1073-1112`) |
| Correr | el modelo de la sesión llama a `Agent` con `dev-refutador` | el subagente devuelve un JSON `refutation-verdict/1.0` como texto final |
| Registrar | la sesión guarda ese texto y corre `refute <KEY> --record <archivo>` | valida todo o nada, redacta y persiste (`refutacion.py:1117-1291`) |

Sirve para la refutación porque el veredicto es un documento con schema que el CLI revalida entero.
Para Execution no alcanza (ME-03).

**Los especialistas no tienen camino de entrega.** Dicen que devuelven su resultado a
`dev-orchestrator` (`agents/dev-backend.md:13`), y `dev-orchestrator` no tiene la herramienta
`Agent` (`agents/dev-orchestrator.md:4`). Su `agentResult` es prosa: nada de `bin/` lo lee.

### 4.2 Qué hay para persistir, reservar y observar

| Necesidad | Qué existe | Sirve tal cual |
|---|---|---|
| Escritura atómica | `estado_de_tarea/persistencia.py:28` `_escribir_atomico` y `hooks/lib/task_binding.py:130` `escribir_atomico`: temporal, fsync y `os.replace` | **No**: las dos pisan el destino. **No existe una escritura de una sola vez** |
| Creación exclusiva | `hooks/lib/human_intent.py:110-120`: un candado `O_CREAT|O_EXCL`, roto por antigüedad a los 60 s | No: está atado a la intención, y romper por antigüedad no sirve para corridas de minutos |
| Saber si un proceso vive | Solo en PowerShell, en un helper de tests (`tests/isolated-factory.ps1:27-65`) | No: no hay nada en Python |
| Un proceso con límite y muerte del árbol | `flujo/repositorio.py:201-238` `_correr_con_limite` y `_matar_arbol` | El algoritmo sí; las funciones son privadas de Flow Governance |
| Redacción | `contexto/limpieza.py:66,86,115,149`: `cargar_catalogo`, `redactar`, `redactar_arbol`, `recortar`, con el catálogo de la SecretGate | **Sí**. `refutacion._limpiar` (`:1209-1226`) es el precedente que falla cerrado sin catálogo |
| Revisión del repo | `refutacion.revision_del_repo` (`:392-400`), `git rev-parse HEAD` | El algoritmo; el módulo es de Governance |
| Archivos cambiados | **No existe** un `git diff --name-status` ni un listado local de cambios. `status --porcelain` solo se cuenta en la bienvenida | No |
| Huellas | `ejecucion/contrato.huella` y `clave_de_idempotencia` | **Sí** |
| Ids al azar | **No existe**: ningún `secrets` ni `os.urandom`; `uuid4` solo nombra temporales | No |
| Rutas | `contrato._ruta_mala` y `_rutas` (`:366-395`) | Parcial: no rechaza `.`, `a//b`, `~`, `file:` ni duplicados por mayúsculas |
| Instalación | `install.ps1:315-349` `Copy-Arbol` copia `bin/` (`:1986`) y `comun/schemas/` (`:1971`) enteros; el lock se genera (`:2142-2157`); `manifest.json` no tiene globs | **Sí**: un módulo nuevo llega solo |

### 4.3 Qué hay para admitir

| Condición | De quién es | API real | Lo que hay que saber |
|---|---|---|---|
| Leer el plan | Planning | `plan.aceptar_guardado` (`orquestacion/plan.py:595`); la ruta, `refutacion.ruta_del_plan` (`:229`) | No valida schema, no mira `task_key`, no busca ids repetidos. `plan.escribir` no es atómico (`:580-590`): un lector puede ver un plan a medio escribir |
| Plan listo | Planning | `plan.estado_de` (`:525`), por los dos lados, como `flujo/precondiciones.plan_listo` (`:137-146`) | `estado_de` levanta `KeyError` si faltan campos |
| La tarea puede delegar | Planning (TaskFlowState) | `flujo/estado.leer` (`:164`), `vigencia_local` (`:524`), `permisos` (`:591`) | `delegationAllowed` exige además la etapa `EXECUTION`, `VERIFICATION` o `REFUTATION` (`:602`). La compuerta del hook solo mira `puede_avanzar` (`flow_gate.py:159`) |
| Compuerta normativa | Normative Sources | `auto_refresh.ensure_normative_knowledge_fresh` (`:474-523`) | **Sin `requeridas` nunca da `blocked`** (`:503`), y `plan` la llama sin ellas (`dev-harness.py:1086`). Escribe la agenda y puede escribir `harness.fuentes.json` |
| El agente | Catalog | `registro_agentes.cargar` (`:69`), `resolver_ruteo` (`:370`), `agente` (`:330`) | `resolver_ruteo` no da tipo ni dominio, y recarga todo en cada llamada |
| Capacidades | Catalog | `capacidades.disponibles` (`:28`) | **No hay mapa Capability → herramienta del Host.** El `tools:` de cada agente (`agents/*.md:4`) no lo lee ningún código |
| Dependencias y duplicados | Execution | — | No existe |

### 4.4 Qué puede hacer hoy el Host

Ver §8.

## 5. Inventario

Cada mecanismo encontrado, clasificado con las seis clases del pedido. El detalle de cada fila está
en el relevamiento (§4).

| # | Mecanismo | Dónde | Clase | ¿Lo usa Task 4? |
|---|---|---|---|---|
| 1 | Herramienta `Agent`/`Task` | Host | Host primitive | No: la usa el modelo, no Python (ME-03) |
| 2 | `claude -p` headless | Host, `claude --help` | Host primitive | **Sí**: es el Host Adapter (MD-08) |
| 3 | Salida estructurada `--json-schema` | Host | Host primitive | **Sí**: produce el AgentReport (MD-09) |
| 4 | `--agent`, `--session-id`, `--allowedTools`, `--permission-mode` | Host | Host primitive | **Sí** (MD-08, MD-18) |
| 5 | Evento de hook con `session_id` | `hooks/lib/hook.py:23-33` | Host primitive | Indirecto: el Host corre los hooks durante la corrida |
| 6 | Transcripción de la sesión | Host | Host primitive | No; la correlación es `host.sessionRef` |
| 7 | Plantilla de hooks y escritor de `settings.json` | `hooks.plantilla.json:16-48`, `install.ps1:711-764` | installation/runtime glue | No se toca |
| 8 | Copia de agentes a `.claude/agents/` | `install.ps1:1975,1989` | installation/runtime glue | Sí: `--agent` los encuentra ahí |
| 9 | `Copy-Arbol` de `bin/` y `schemas/` | `install.ps1:315-349` | installation/runtime glue | Sí: instala el motor sin cambios (§26) |
| 10 | SecretGate y compuerta del flujo en PreToolUse | `hooks/pre-tool-use.py:68-115` | HARNESS domain behavior | Sí, como defensa del Host durante la corrida (MD-17) |
| 11 | Clasificación de herramientas y de subcomandos | `tool_policy.py:1473-1510`, `:423-492` | HARNESS domain behavior | No se toca; `ejecutar` queda `UNRESOLVED` (ME-22) |
| 12 | Vínculo de sesión | `task_binding.py:183,206` | HARNESS domain behavior | Sí, por la primera línea del prompt (MD-17) |
| 13 | `refute --compile/--unit/--record` | `refutacion.py` | HARNESS domain behavior | Es el precedente; no se reusa |
| 14 | `dev-refutador` y su contrato | `agents/dev-refutador.md:118-181` | HARNESS domain behavior | No: es `CRITIC_AGENT` (T3 D5) |
| 15 | Contabilidad por transcripción | `contabilidad/adaptadores/claude_code.py:105-326` | HARNESS domain behavior | No se toca |
| 16 | Contrato de ejecución | `bin/ejecucion/contrato.py`, dos schemas | HARNESS domain behavior | **Sí**: todo pasa por sus validadores |
| 17 | `agentResult` de los especialistas | `agents/dev-backend.md:101-114` y seis más | legacy behavior | Solo su vocabulario de cuatro valores |
| 18 | `toolBuilderResult` | `agents/dev-tool-builder.md:273-302` | legacy behavior | No |
| 19 | Eventos `WORKUNIT_*`, `AGENT_RUN_*`, `TASK_*` sin productor | `contabilidad/eventos.py:27-42` | legacy behavior | No (MP-02) |
| 20 | `executionId` del ledger de seguridad, siempre nulo | `reporte_seguridad/productores.py:117` | legacy behavior | No (T3 P4) |
| 21 | `maxRetries`, `modelo.escalar`, `retryPolicy`, `timeoutSeconds` | `consumo.py:23`, `modelo.py:91-106`, `tool-contract.schema.json:63-81` | legacy behavior | No |
| 22 | `git` en procesos | `refutacion.py:395`, `contexto-armar.py:154`, `repositorio.py:183,228` | unrelated | El patrón, en un módulo propio (MD-14) |
| 23 | `markitdown` | `contexto/documentos.py:45-56` | unrelated | No |
| 24 | Eventos sintéticos de hooks y payloads | `tests/casos/63_compuerta_del_flujo.py`, `tests/payloads/` | test helper | El estilo, para el Host falso (§29) |
| 25 | Agentes de la fábrica | `.claude/agents/harness-*.md` | unrelated | No |

**Conclusión.** No hay un segundo mecanismo que reemplazar. Task 4 agrega uno solo, el Host Adapter,
sobre primitivas del Host que ya existen (filas 2 a 4), y reusa del repo el contrato, la redacción y
la instalación.

## 6. Contradicciones

Ordenadas por prioridad: primero las que obligan a elegir diseño.

| # | Contradicción | Evidencia | Qué obliga a decidir |
|---|---|---|---|
| **ME-01** | MC `### Host` dice "HARNESS no llama a ningún modelo ni lanza agentes: lo hace el Host". Un motor tiene que iniciar la corrida | MC, `### Host`, Invariantes | MD-08: HARNESS lanza **el Host**; el Host corre el agente y llama al modelo. El invariante se reescribe, como preveía T3 §34.3.7 |
| **ME-02** | Los tests de Task 3 prohíben el motor: ningún subcomando `ejecutar`, nada de `bin/ejecucion/` escribe ni lanza procesos, nadie importa `ejecucion`, y E-41 permite lanzar solo `git`, `markitdown` y `taskkill` | `65_contrato_de_ejecucion.py` EX-E49, EX-E51, EX-E52; `64_modelo_de_dominio.py:2847` E-41 | §26.2: cada uno se reemplaza con su decisión escrita, y lo que siguen cuidando (la pureza de `contrato.py`, nada de concurrencia, nada de SDK) pasa a escenarios de esta Task |
| **ME-03** | La única primitiva de delegación, `Agent`, no la puede llamar Python, devuelve texto, y el precedente de la refutación hace que el modelo de la sesión **retransmita** el resultado | §4.1 | MD-08: un Host Adapter headless. Si el modelo de la sesión retransmitiera el AgentReport, podría escribir `COMPLETE` por el agente, y el motor no controlaría ni el fin ni el timeout ni la cancelación |
| **ME-04** | El `agentResult` es prosa, y Execution no interpreta texto (T3 D8) | `agents/*.md`, T3 §11 | MD-09: el `declaredStatus` sale de la salida estructurada del Host, validada contra un schema. Nadie parsea Markdown |
| **ME-05** | T3 D4 dice que la compuerta normativa se llama "igual que en `plan`", y así nunca da `blocked`: `NORMATIVE_GATE_BLOCKED` sería inalcanzable | `auto_refresh.py:503`, `dev-harness.py:1086`; hallazgo 1 de la reverificación | MD-13: la admisión pasa `requeridas`, las normas de la unidad |
| **ME-06** | T3 P14: ninguna función da "el TaskFlowState vigente" sin costo. `derivar` lee el `.env`; `reconciliar` escribe; el hook usa `leer` y `vigencia_local` con 1,5 s | `flujo/estado.py:374,524`; `persistencia.py:72` | MD-12: `leer` + `vigencia_local` con 10 s + `permisos`. El motor no escribe estado del flujo |
| **ME-07** | El ciclo de T3 no tiene `REQUESTED → FAILED`, y ningún código de `REJECTED` dice "el motor falló antes de entregar" | T3 §13, §14 | MD-07: un `REQUESTED` sin motor vivo queda abierto hasta una cancelación explícita. El contrato no cambia |
| **ME-08** | No existe una escritura de una sola vez: todas las atómicas pisan | §4.2 | MD-05: una primitiva nueva, temporal más `os.link` |
| **ME-09** | No existe en Python una forma de saber si el motor que creó una Execution sigue vivo | §4.2 | MD-06: un candado del sistema operativo que el motor tiene tomado mientras vive |
| **ME-10** | No hay índice de `idempotencyKey`, y la carpeta de T3 es por `executionId` | T3 D17 | MD-04: turnos de intento por clave, creados de forma exclusiva. También resuelven las dependencias sin recorrer nada |
| **ME-11** | Una sesión headless no tiene vínculo; con dos tareas con estado, la compuerta del flujo niega todo con `SESSION_TASK_AMBIGUOUS` | hallazgo 11 de la reverificación; `task_binding.py:206-233` | MD-17: la primera línea del prompt declara la tarea, y el vínculo lo escribe el hook que ya existe |
| **ME-12** | No hay mapa Capability → herramienta, y el `tools:` de los agentes no lo lee nadie | §4.3 | MD-18: una tabla mínima en el adaptador, para las cuatro capacidades locales |
| **ME-13** | Las capacidades de integración (`jira.*`, `gitlab.*`) están disponibles para HARNESS y no para el agente | EC-08, FH | MD-18: el adaptador no las provee, y la unidad sale `REJECTED` con `CAPABILITY_UNAVAILABLE` |
| **ME-14** | El validador de subconjunto acepta un `\n` final por `$`, y Task 4 usa ids como nombres de carpeta | hallazgo 6 de la reverificación; `contexto-armar.py:932` | MD-15: todo id que se vuelve ruta se valida con anclaje completo antes |
| **ME-15** | Las rutas no tienen forma canónica: pasan `./a`, `a//b`, `~/x`, `file:///x` y duplicados por mayúsculas | hallazgo 7 de la reverificación | MD-16: una política canónica en el registro, sin tocar `contrato.py` |
| **ME-16** | `workUnits.items` del plan está abierto: un request con claves de más en `workUnit` pasa `validar_request` | hallazgo 10 de la reverificación | MD-11: al entregar, la unidad del request tiene que tener la huella de la del plan |
| **ME-17** | `aceptar_guardado` no mira `task_key`, ni ids repetidos, y el plan se escribe sin atomicidad | `plan.py:580,595-649` | MD-11: la admisión hace esas comprobaciones con sus propios códigos, y lee un JSON roto como `PLAN_UNREADABLE` |
| **ME-18** | Varias cosas del Host no están documentadas: los `subtype` de error, cómo se combinan `--agent` con `--allowedTools` y `--json-schema`, y si `-p` lee el prompt de stdin | docs de Claude Code (§8) | MD-10: el adaptador clasifica lo desconocido como `HOST_FAILURE`, y un escenario de lectura confirma lo demás con una corrida real |
| **ME-19** | En Windows, `claude` es un shim `.cmd`/`.ps1`, y pasar JSON por argv a un `.cmd` es frágil | `where claude`: `AppData\Roaming\npm\claude.ps1` | MD-08: el prompt va por stdin; el schema, por argv sin metacaracteres de `cmd`, y un escenario lo prueba a través de un shim |
| **ME-20** | El Host puede sobrevivir al motor: en Windows, un hijo no muere con su padre | docs de Claude Code, §7 | MD-07: la recuperación no mata procesos por PID (reuso de PID). Riesgo declarado (§33) |
| **ME-21** | El repo puede estar sucio antes de ejecutar, y el contrato tiene tres estados de cambios | T3 §18 | MD-20: separación por ruta; lo mezclado es `CHANGES_UNATTRIBUTABLE` |
| **ME-22** | Un subcomando nuevo cae en `UNRESOLVED_TOOL_CLASS` en la política de herramientas | `tool_policy.py:492` | No se toca el hook (§30): `ejecutar` desde una sesión pasa solo si la tarea puede avanzar, que es la misma condición de la admisión |
| **ME-23** | T3 D15 pide que el motor emita `WORKUNIT_*` y sume `executionId` a `CLAVES_DE_METADATA`; el pedido prefiere no bloquear por contabilidad | `contabilidad/eventos.py:78`; T3 §19 | MD-21: se difiere (MP-02). La correlación queda por `host.sessionRef` |
| **ME-24** | `requestedBy` es obligatorio, y el CLI no sabe quién pide | T3 §10.1 | MD-19: `--pedido-por`, si no `usuario` de `harness.config.json`, si no el usuario del sistema |
| **ME-25** | El tier de la unidad no dice qué modelo usar | T3 §10.1 ("lo resuelve el runtime") | MD-18: `modelRouting.perfiles` de `harness.config.json`, que ya lee `plan` (`modelo.perfiles_declarados`); sin perfil declarado, el modelo del Host |
| **ME-26** | La compuerta del flujo del hook deja pasar con `puede_avanzar`, sin mirar la etapa; la admisión exige `delegationAllowed` | `flow_gate.py:159`, `estado.py:602` | Ninguna: son dos compuertas y la de Execution es más estricta. Se documenta (§18) |
| **ME-27** | Encontrada en la construcción. §11, fila 2, mandaba leer la ruta del plan con `refutacion.ruta_del_plan`; MD-13 dice que Execution no importa la refutación, y EX-E08 de Task 3 lo prueba (`bin/ejecucion/` no importa `refutacion`). Armar la ruta en Execution suma un módulo al inventario de E-22 de Task 2 | `65_contrato_de_ejecucion.py` EX-E08; `64_modelo_de_dominio.py` E-22; §11; MD-13 | Se eligió la que no relaja un límite de dominio: `admision.ruta_del_plan` arma `.claude/planes/<KEY>.json`, la misma ruta (ME-E29 lo fija), y E-22 suma `ejecucion/admision.py` a su inventario con dos aserciones nuevas: la admisión lee el plan por `aceptar_guardado` y no lo escribe (§26.2). **Para revisión** |

## 7. Modelo

### 7.1 Lo que no cambia

El modelo de Task 3 sigue igual: ocho conceptos en el contexto Execution, seis estados, cuatro
terminales, 23 códigos, la precedencia de 15, el AgentReport y la evidencia. **Esta Task no agrega
conceptos de dominio.**

### 7.2 Lo que aparece, y qué es

| Candidato | Qué es | Clasificación | ¿Concepto del catálogo? |
|---|---|---|---|
| Host Adapter | La pieza que habla con un Host concreto | Infrastructure | **No.** ADR-0014 ya lo dejó como infraestructura; sigue en el vocabulario |
| El registro de una Execution (`.claude/ejecuciones/...`) | Dónde vive su estado | Infrastructure | **No.** Es la persistencia de Execution y ExecutionRequest, que ya existen |
| La reserva por turnos | El mecanismo de EX-I28 | Infrastructure | **No.** No tiene ciclo propio que el dominio vea |
| El motor | Quien orquesta una corrida | Application Service | **No.** Su comportamiento ya está en el ciclo de Execution |
| ExecutionAdmission | La regla | Domain Service | Ya existe. Pasa de "sin implementación" a implementada |

**Por qué ningún concepto nuevo.** MC exige que un concepto tenga lenguaje, invariantes y ciclo
propios. La reserva, el registro y el adaptador son cómo se cumple lo que Execution ya promete, y
cambiarlos no cambia ninguna regla de dominio.

### 7.3 Las piezas, por responsabilidad

```
ejecucion/
  contrato.py           Task 3. Puro: constantes y validadores. No cambia
  admision.py           la regla de 15 condiciones, leyendo a cada dueño
  registro.py           el registro: rutas canónicas, escritura de una sola vez, reserva,
                        candado de vida, estado derivado
  evidencia.py          las fotos del árbol antes y después, y ExecutionEvidence
  proceso.py            lanzar con límite y matar el árbol
  host_claude_code.py   el Host Adapter: agente, capacidades, entrega y AgentReport
  motor.py              orquesta: admitir, crear, entregar, registrar; cancelar; recuperar
```

Cada módulo es chico y tiene un solo dueño de datos. `motor.py` es el único que conoce el orden.

## 8. Host real

Lo que puede hacer Claude Code desde HARNESS, con su fuente. **Verificado** quiere decir que está en
el `--help` de la versión instalada; **documentado**, que está en la documentación oficial; **a
confirmar**, que no está escrito y lo confirma la lectura ME-E50.

| Pregunta | Respuesta | Fuente |
|---|---|---|
| ¿Cómo se corre un agente sin sesión interactiva? | `claude -p` con `--agent <nombre>`: la sesión entera corre como ese agente, con su prompt de sistema, su `tools:` y su `model:` | verificado (`--agent`); documentado (`sub-agents`) |
| ¿De dónde sale el agente? | `.claude/agents/<nombre>.md` del proyecto, que instala `install.ps1:1975,1989` | documentado |
| ¿Qué recibe? | El prompt, por argumento o por stdin | verificado (argumento); a confirmar (stdin sin argumento) |
| ¿Qué devuelve? | Con `--output-format json`, un objeto `{type: "result", subtype, is_error, result, session_id, num_turns, duration_ms, total_cost_usd, usage, permission_denials}` por stdout | documentado (`headless`) |
| ¿Hay salida estructurada? | `--json-schema <schema>`: el objeto suma `structured_output`, validado contra el schema, con reintentos. Si no lo logra, `subtype: error_max_structured_output_retries` | verificado (flag); documentado (campo y error) |
| ¿Hay id de sesión? | `session_id` en la salida, y `--session-id <uuid>` lo fija de antemano | verificado (flag); documentado |
| ¿Hay id de corrida? | No. La sesión es la corrida | documentado |
| ¿Corren los hooks del proyecto? | Sí, salvo con `--bare` | documentado |
| ¿Qué pasa si falla? | Código de salida distinto de 0; con JSON, `is_error: true` y un `subtype` de error | documentado; la lista de `subtype` es a confirmar |
| ¿Y si se corta? | SIGTERM sale con 143 y SIGINT con 130; la transcripción queda hasta ese punto | documentado. En Windows, que el hijo muera con el padre no está documentado |
| ¿Quién conoce las herramientas? | El Host: el `tools:` del agente, `--allowedTools`, `--disallowedTools` y `--permission-mode` | verificado; cómo se combinan `tools:` y `--allowedTools`, a confirmar |
| ¿Puede quedarse esperando a una persona? | No con `--permission-mode dontAsk` y `--permission-prompts none`: lo que pediría permiso se niega | verificado (flags); documentado |
| ¿Y `Agent` en PreToolUse? | Es la delegación dentro de una sesión. El motor no la usa: lanza una sesión nueva | §4.1 |

📌 **Lo que esta spec no supone.** El adaptador no depende de lo que está "a confirmar": todo lo que no
reconoce lo clasifica como `HOST_FAILURE` (MD-10). Y lo confirma una corrida real, que es una lectura
(ME-E50), porque su sujeto es una corrida de un modelo (ADR-0009).

## 9. Host Adapter

#### MD-08. Un Host Adapter headless, `claude -p`, y no la herramienta `Agent`

Se evaluaron cinco formas de que el Host corra la unidad:

| Alternativa | Cómo | Por qué no, o por qué sí |
|---|---|---|
| A. La herramienta `Agent`, retransmitida por la sesión, como la refutación | `ejecutar --preparar` imprime la unidad; el modelo delega; `ejecutar --registrar` recibe el texto | **No.** El AgentReport lo escribiría el modelo de la sesión: podría poner `COMPLETE` por el agente. El motor no ve el fin, no tiene timeout ni cancelación, y un `RUNNING` solo se cierra por tiempo |
| B. `claude -p` lanzado por el motor | El motor arranca una sesión headless con `--agent`, espera, lee la salida estructurada | **Se elige.** El motor controla la entrega, el fin, el timeout, la cancelación y la interrupción. La salida la valida el Host contra un schema |
| C. El SDK de agentes de Python | `claude_agent_sdk` con `output_format` | No: es una dependencia nueva, y E-41 y EX-E51 prohíben SDKs de modelos con razón. `-p` es la misma capacidad sin dependencia |
| D. Un Host Adapter general, con proveedores enchufables | — | No: hay un Host. La frontera queda limpia para un segundo |
| E. Sesiones en segundo plano, `--bg`, con `claude stop` | — | No: agrega estado del Host que el motor tendría que seguir. Una corrida sincrónica alcanza |

**ME-01 se resuelve así:** HARNESS lanza el Host, nunca un modelo. El invariante de MC `### Host`
pasa a decir: "HARNESS no llama a ningún modelo. Desde Task 4, el motor de Execution puede lanzar el
Host para que corra un agente; el agente y el modelo los corre el Host".

**El contrato del adaptador**, que no es un concepto de dominio:

| Operación | Entrada | Salida | Errores |
|---|---|---|---|
| `resolver_agente(proyecto, agente)` | `workUnit.assignedAgent`, ya validado por el registro | la definición del agente en el Host: ruta y `tools:` | Sin `.claude/agents/<agente>.md`, o con un `name:` distinto: el agente no se puede correr. Corre en la admisión al entregar, **antes** de escribir `entrega.json`: `REJECTED` con `AGENT_UNAVAILABLE`. Después de la entrega, que el Host no pueda iniciar o cargar el agente es `HOST_FAILURE` (MD-10) |
| `provee(capacidades, agente)` | `workUnit.requiredCapabilities` | qué provee y qué no (MD-18) | Una que no provee: `CAPABILITY_UNAVAILABLE` |
| `entregar(request, ruta_de_la_ejecucion, avisos)` | el request ya admitido, y cómo avisar cancelación | `(informe o None, falla o None, host)`, con `host = {kind: "claude-code", sessionRef, runRef: null}` | Las fallas son códigos de corrida (§21). Nunca levanta por una falla del Host |
| `terminar(proceso)` | — | — | Mata el árbol (MD-14) |

**Cómo se lanza** (MD-08, MD-18):

```
claude -p
  --agent <assignedAgent>
  --output-format json
  --json-schema <el schema del AgentReport>
  --session-id <uuid4 que genera el adaptador>
  --permission-mode dontAsk
  --permission-prompts none
  --allowedTools <herramientas de MD-18>
  [--model <perfil declarado para el tier>]
stdin  = el prompt
cwd    = la raíz del proyecto
stdout = un archivo temporal, no un pipe   (como flujo/repositorio.py, para que un nieto
                                            que hereda el pipe no cuelgue la espera)
stderr = otro archivo temporal, recortado
```

- **Nunca** `--bare`, `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions` ni
  `bypassPermissions`: los hooks del proyecto, la SecretGate y la compuerta del flujo, siguen
  activos durante la corrida (ME-I23).
- **El comando** sale de `ejecucion.comandoHost` en `.claude/harness.config.json` si está, y si no de
  `shutil.which("claude")`. Es configuración del motor, no del request: así los tests usan un Host
  falso (§29). Se resuelve **antes de crear la Execution**, y un comando que no se resuelve es un
  error del comando, sin Execution (MD-22).
- **El prompt va por stdin** (ME-19). Lo arma el adaptador desde el request:
  1. `Seguimos con <TaskKey>.`, que vincula la sesión por el hook que ya existe (MD-17);
  2. la WorkUnit del request, como JSON: es la unidad que "viaja sola"
     (`orchestration-plan.schema.json:150`);
  3. la instrucción de devolver `declaredStatus` (el `agentResult.status` del agente) y `artifact`
     (su informe entero, con el bloque `agentResult`), y de no escribir en `.claude/`.
- **El schema va por argv.** Se arma de `contrato.DECLARACIONES_DEL_AGENTE`, y no lleva ninguno de
  los caracteres que `cmd` interpreta (`& | < > ^ %`). ME-E40 lo prueba a través de un shim `.cmd`.

## 10. AgentReport real

#### MD-09. El `declaredStatus` sale de la salida estructurada del Host

| Alternativa | Cómo | Juicio |
|---|---|---|
| **A. Salida estructurada del Host** | `--json-schema` con `{declaredStatus: enum de 4, artifact: string}`, sin propiedades de más | **Se elige.** El Host valida y reintenta; el adaptador toma dos claves de un objeto ya validado |
| B. Un protocolo en el prompt | "Terminá con una línea `STATUS: …`" | No: alguien tendría que buscar esa línea en texto libre. Es interpretar texto |
| C. Un archivo que escribe el agente | El agente deja `informe.json` | No: `dev-architecture` no tiene `Write`, y escribir en `.claude/` está protegido por la compuerta del flujo |
| D. Un parser del `result` | Buscar el bloque `agentResult` en Markdown | **Prohibido** por T3 D8 |
| E. Otra primitiva | No hay hook `SubagentStop` instalado, y no devuelve estructura | No |

**Cómo se normaliza:**

1. el adaptador lee el JSON de stdout;
2. si `subtype` es `success` y hay `structured_output`, el AgentReport es
   `{declaredStatus: structured_output.declaredStatus, artifact: structured_output.artifact}`;
3. `contrato.validar_informe` lo valida. Si no pasa, es `OUTPUT_INVALID`;
4. **el campo `result` no se lee nunca**, aunque diga `COMPLETE`.

El `artifact` es texto opaco: se redacta y se guarda aparte (§17). `declaredStatus` es una
declaración del agente, no de Execution: `PARTIAL`, `BLOCKED` o `FAILED` dan `FAILED` con
`AGENT_DECLARED_NOT_COMPLETE` (T3 D8). El contrato de Task 3 no cambia.

## 11. ExecutionAdmission

#### MD-11. La regla de T3 §37.5, implementada, leyendo a cada dueño

El orden, los códigos y la primera falla que gana son los de T3 §37.5. Lo que esta Task agrega es
**de dónde sale cada dato**:

| # | Condición | Código | Cómo se evalúa |
|---|---|---|---|
| 1 | Forma de lo pedido | `CONTRACT_INVALID` | La TaskKey y el id de la unidad con anclaje completo (MD-15); `requestedBy` no vacío. **Al entregar:** `validar_request` sobre el `request.json` guardado, y que su `workUnit` tenga la huella de la unidad del plan (ME-16) |
| 2 | Plan legible | `PLAN_UNREADABLE` | `.claude/planes/<KEY>.json`, la ruta de `refutacion.ruta_del_plan` armada en la admisión, porque Execution no importa la refutación (ME-27); leer el JSON (uno roto es ilegible, ME-17); `plan.aceptar_guardado`; los ids de las unidades no se repiten (ME-17) |
| 3 | `meta.task_key` | `TASK_KEY_MISMATCH` | Comparación directa: `aceptar_guardado` no la hace |
| 4 | Solo al entregar: huella del plan | `PLAN_CHANGED` | `contrato.huella(plan)` contra `request.plan.planFingerprint` |
| 5 | Plan 2.1 listo por los dos lados | `PLAN_NOT_READY` | `meta.schema_version == orchestration-plan/2.1`, `status == READY_FOR_EXECUTION` y `plan.estado_de(plan) == READY_FOR_EXECUTION`, como `precondiciones.plan_listo`. Una excepción de `estado_de` es "no listo" |
| 6 | La tarea puede delegar | `DELEGATION_NOT_ALLOWED` | MD-12 |
| 7 | La unidad está | `WORK_UNIT_NOT_FOUND` | Una unidad con ese id. Que no haya dos ya lo miró la condición 2 |
| 8 | `PENDING` | `WORK_UNIT_NOT_PENDING` | `workUnit.status` |
| 9 | Compuerta normativa | `NORMATIVE_GATE_BLOCKED` | MD-13 |
| 10 | Agente ruteable ahora | `AGENT_UNAVAILABLE` | `registro_agentes.cargar` una vez, `resolver_ruteo(documento=)`. **Al entregar**, además, el adaptador encuentra y carga su definición (`resolver_agente`), antes de escribir `entrega.json`. Es la última vez que este código puede salir: después de la entrega, el mismo motivo es `HOST_FAILURE` (MD-10) |
| 11 | Tipo ejecutable | `AGENT_NOT_EXECUTABLE` | `registro_agentes.agente(id, documento)["type"]` en `contrato.TIPOS_EJECUTABLES` |
| 12 | Dominio | `AGENT_DOMAIN_MISMATCH` | `agente(...)["domain"] == workUnit.domain` |
| 13 | Capacidades | `CAPABILITY_UNAVAILABLE` | `capacidades.disponibles` sobre `.claude/harness.capacidades.json`. **Al entregar**, además, `provee` del adaptador (MD-18) |
| 14 | Dependencias | `DEPENDENCY_NOT_SATISFIED` | MD-04: el último turno de la clave de cada dependencia es `SUCCEEDED` |
| 15 | Duplicado | `DUPLICATE_EXECUTION` | MD-04, con la exclusión de sí misma al entregar |

`detail` nombra la causa, redactada y de hasta 300 caracteres: la clave que no coincide, el estado
del flujo y sus bloqueos, las fuentes en alerta, el turno que duplica.

### 11.1 Admisión en dos momentos

**Antes de admitir**, el motor lee su configuración (MD-22). Una configuración inválida es un error
del comando: no hay Execution, ni ExecutionError, ni nada escrito.

**Al pedir.** Corren las condiciones 1 a 3 y 5 a 15. La 4 no: todavía no hay request.

- Si falla una, vuelve el ExecutionError al que pidió, por la salida del comando, que pasa
  `contrato.validar_rechazo`. **No hay Execution y no queda nada escrito.**
- Una falla de infraestructura al pedir (sin catálogo de secretos, disco lleno) no es un
  ExecutionError: el comando falla, sin Execution y sin residuo.

#### MD-23. La request se redacta, se valida, se fija su huella y se persiste, en ese orden

Si las quince condiciones pasan, la request se arma así, y en ningún otro orden:

1. **se deriva la request lógica** del plan, del flujo, del registro y de las capacidades, con
   `workUnitFingerprint` e `idempotencyKey` calculadas sobre la unidad tal como está en el plan;
2. **se redacta** con `limpieza.redactar_arbol` (MD-19). Si la redacción cambia la `workUnit`, la
   unidad del request ya no sería la del plan: es `CONTRACT_INVALID` y **no se crea la Execution**.
   El plan tiene un secreto según el catálogo de hoy, y se replanifica;
3. **se valida la request redactada** con `contrato.validar_request`;
4. **se calcula su huella**, `contrato.huella(request redactada)`. Es la que va a llevar
   `requestFingerprint` en el resultado;
5. **se persiste exactamente esa request** como `request.json` (MD-05).

`requestFingerprint` es la huella **del request persistido**, no de una versión anterior a la
redacción (ME-I30). Quien lea `request.json` y calcule su huella obtiene el mismo valor, que es lo que
exige la coherencia 1 de `validar_resultado`.

**Al entregar.** Corren las quince, con el mismo código para el mismo motivo. El `request.json`
guardado no se cree: se vuelve a derivar todo del plan, del flujo, del registro, de las capacidades y
del registro de ejecuciones (EX-I21).

- Si falla una, la Execution termina `REJECTED` con ese código, `startedAt`, `evidence`,
  `agentDeclaredStatus` y `output` en `null`.

**Qué cambia entre una y otra:**

| Condición | Al pedir | Al entregar |
|---|---|---|
| 1 | forma de los argumentos | `validar_request` del guardado, y la huella de la unidad contra el plan |
| 4 | no corre | corre |
| 10 | registro | registro y `resolver_agente` |
| 13 | Catalog | Catalog y `provee` |
| 15 | no hay otra Execution con la clave abierta o `SUCCEEDED` | el último turno de la clave es esta misma Execution (MD-04) |

**La frontera es `entrega.json`.** Antes de escribirlo, una condición que falla da `REJECTED` con su
código de admisión. Después, la Execution está `RUNNING` y solo puede terminar con un código de
corrida (`HOST_FAILURE`, `HOST_INTERRUPTED`, `PROVIDER_FAILURE`, `TIMEOUT`, `OUTPUT_INVALID`,
`AGENT_DECLARED_NOT_COMPLETE`, `ENGINE_FAILURE`) o con `CANCELLED`. T3 §14 permite además
`AGENT_UNAVAILABLE` y `CAPABILITY_UNAVAILABLE` en `FAILED`; **este motor no los usa nunca**
(ME-I29). Así, la misma causa no puede dar dos estados según cuándo se la mire: un agente que no se
carga es `REJECTED` con `AGENT_UNAVAILABLE` si lo descubre el adaptador antes de la marca, y `FAILED`
con `HOST_FAILURE` si lo descubre el Host después. El contrato de Task 3 no cambia: lo que se acota es
qué emite este motor.

En esta Task, las dos corren dentro del mismo `ejecutar`, con segundos entre una y otra. La segunda
no es redundante: entre las dos, una persona puede cancelar la tarea, replanificar o aceptar una
fuente, y el motor escribe la request antes de reservar (MD-04).

## 12. Atomicidad: EX-I28 y EX-F01

#### MD-04. Turnos de intento por clave, creados de forma exclusiva

```
.claude/ejecuciones/<TaskKey>/claves/<hex de la clave>/
    000001.json     {"executionId": "exe_…", "reservadoEn": "…Z"}     se escribe una vez
    000002.json     solo si el turno 1 terminó FAILED, CANCELLED o REJECTED
```

- **Un turno es la reserva.** Su archivo se crea con la escritura de una sola vez (MD-05), que falla
  si ya existe. Nada se borra nunca: los turnos son la historia de la clave.
- **Una Execution existe si y solo si un turno la nombra** (ME-I21). Una carpeta sin turno no es una
  Execution: no la ve nadie, no bloquea nada, y la barre la recuperación (§14.1).
- **El orden de la creación:**
  1. se lee el último turno N de la clave. Si su Execution está abierta o `SUCCEEDED`:
     `DUPLICATE_EXECUTION`, y no se escribe nada;
  2. se crea la carpeta `<executionId>/` con `os.mkdir`, que es exclusiva;
  3. se toma el candado de vida (MD-06);
  4. se escribe `request.json`, redactado, validado y con su huella ya calculada (MD-23);
  5. **se reserva el turno N+1.** Es una sola creación exclusiva, y es el instante en que la Execution
     existe: **se publica**.
  6. Si el turno N+1 ya existe, otra admisión ganó: se borra la carpeta propia, que nadie más
     conoce, y vuelve `DUPLICATE_EXECUTION`.

#### MD-04d. El residuo previo a la publicación

Si el motor muere entre los pasos 2 y 5, queda una carpeta que **no es una Execution**: puede tener
`vivo.lock`, un temporal de escritura y hasta un `request.json` completo, pero ningún turno la nombra.
Es un **residuo previo a la publicación**, y es legítimo: es la ventana de la creación.

| | Residuo previo a la publicación | `REQUESTED` real |
|---|---|---|
| Qué hay | carpeta, quizás `request.json`, **sin turno** | turno que la nombra, `request.json`, sin `entrega.json` |
| ¿Es una Execution? | **No** (ME-I21) | Sí |
| ¿Participa de la idempotencia? | **No**: los duplicados leen turnos, no carpetas | Sí: bloquea su clave |
| ¿Aparece en `--estado`? | No | Sí |
| ¿Qué hace la recuperación? | La borra entera, temporales incluidos, si tiene más de 10 minutos y su candado está libre (ME-I28) | Nada: queda abierta hasta una cancelación explícita (§14.1, R2) |

La antigüedad se mide por `vivo.lock`, que se crea en el paso 3 y no se toca; sin `vivo.lock`, por la
carpeta. **El candado decide, y la edad es la guarda:** una carpeta con el candado tomado es una
admisión en curso y no se barre nunca, tenga la edad que tenga.

**Por qué es atómico.** Dos admisiones de la misma clave que leen el mismo N compiten por crear el
mismo archivo N+1, y el sistema de archivos deja ganar a una sola. La perdedora no deja ni request,
ni marca, ni turno. Un turno nunca nombra una request a medio escribir, porque la request se escribe
antes.

**Las alternativas que se descartaron:**

| Alternativa | Por qué no |
|---|---|
| Un candado por clave, con antigüedad | Romperlo por edad tiene carrera entre dos que lo rompen, y no hay en el repo un candado sin antigüedad |
| Un candado del sistema operativo durante la admisión, más un recorrido | Funciona, pero el recorrido de todas las requests es lento y el turno exclusivo ya resuelve sin candado |
| Un índice único que se reescribe | Es un archivo mutable, y su escritura no es exclusiva |
| Un `symlink` por clave | En Windows exige privilegios |
| `mkdir` de una carpeta por clave | Bloquea los reintentos: habría que borrarla, y borrar no es atómico respecto de otra admisión |

**Lo que sale gratis:** las dependencias (MD-04 también) y los duplicados se resuelven leyendo **un
solo archivo**, el último turno de una clave. No hace falta recorrer el registro.

#### MD-04b. El escenario EX-F01, ejecutable

Dos procesos del sistema operativo, no dos llamadas seguidas, admiten la misma TaskKey, la misma
huella y la misma unidad, con `executionId` distintos:

1. el test lanza dos `python` hijos con la API del motor y un punto de encuentro en el disco;
2. los dos leen el último turno y se avisan por un archivo cada uno;
3. cuando los dos leyeron, los dos intentan reservar;
4. el resultado es exactamente una Execution, un `DUPLICATE_EXECUTION`, un solo turno, una sola
   carpeta y ningún temporal.

El punto de encuentro está entre la lectura y la reserva, que es justo la ventana de la carrera.
Además se repite 20 veces sin punto de encuentro, lanzando los dos a la vez, y cada vez se exige lo
mismo.

#### MD-04c. EX-F02: la Execution no es duplicado de sí misma

Al entregar, la condición 15 es: **el último turno de la clave nombra a esta Execution.** Por
construcción no puede haber un turno posterior mientras esta esté abierta, así que la propia no
bloquea. Si el último turno nombra a otra, que esté abierta o `SUCCEEDED`, la Execution termina
`REJECTED` con `DUPLICATE_EXECUTION`. Eso solo pasa con un registro editado a mano, y por eso el
escenario lo arma así.

## 13. Persistencia

#### MD-03. El registro de D17, revalidado

```
.claude/ejecuciones/<TaskKey>/
  claves/<hex>/<NNNNNN>.json   turno de intento                se escribe una vez (MD-04)
  <executionId>/
    vivo.lock                  candado de vida, vacío          lo crea y lo tiene el motor (MD-06)
    request.json               execution-request/1.0           una vez, al crear
    cancelacion.json           pedido explícito de cancelar    una vez, a pedido
    entrega.json               la marca de entrega             una vez, al pasar a RUNNING
    proceso.json               el pid del Host                 una vez, al lanzarlo
    output.md                  el artifact, redactado          una vez, si hubo AgentReport válido
    result.json                execution-result/1.0            una vez, al quedar terminal
```

- **Todo se escribe una sola vez.** No hay `state.json`: el estado se deriva de lo que existe (§14).
  `vivo.lock` es un archivo vacío que nadie lee.
- **`entrega.json`** es `{deliveredAt, repoRevisionBefore, antes, host: {kind, sessionRef},
  motor: {pid, maquina}}`. `antes` es la foto del árbol (MD-20). Guardarla ahí hace que la
  recuperación pueda armar la evidencia sin el motor.
- **`proceso.json`** es `{pid}`. Se usa solo para avisar en `--estado`; nadie mata por él (MD-07).
- **`cancelacion.json`** es `{pedidoEn, pedidoPor}`, con `pedidoPor` redactado.
- **Los archivos de infraestructura no tienen schema.** Son de Execution, no contratos que otro
  consuma, y T3 P6 los dejó como infraestructura. Cada uno se valida en código con un conjunto
  cerrado de claves. Sumar un schema cambiaría la cuenta de E-05 sin que nadie lo lea.
- **Va bajo `.claude/`**, como D17: gitignoreado, y sobrevive al `-Update` y al `-Uninstall`
  (`install.ps1:2308-2316`, `:2405-2438`).

#### MD-05. La escritura de una sola vez

```
escribir_una_vez(ruta, bytes):
    temporal = mkstemp en la misma carpeta        (O_EXCL: el temporal también es exclusivo)
    escribir, flush, fsync, cerrar
    os.link(temporal, ruta)                       atómico, y falla con FileExistsError si ya está
    finally: borrar el temporal
```

- **No pisa nunca:** `os.link` no reemplaza. Es lo que no tiene ningún escritor del repo (ME-08).
- **Es atómica:** quien lee ve el archivo entero o no lo ve.
- **Limpia:** el temporal, `.<nombre>.<aleatorio>.tmp`, se borra siempre, haya fallado o no. Si el
  proceso muere entre `mkstemp` y el `finally`, el temporal queda, y lo borra la recuperación cuando
  el candado de esa carpeta está libre (§14.1).
- **Dónde no anda:** en un sistema de archivos sin enlaces duros, como FAT o exFAT, `os.link`
  falla. El motor no sigue sin ella: es `ENGINE_FAILURE`, o un error del comando si fue al pedir
  (§33).
- **La reusan los siete archivos de la tabla**, el turno incluido.

#### MD-06. El candado de vida

El motor crea `vivo.lock` y lo **toma con un candado del sistema operativo** desde que crea la
carpeta hasta que escribe `result.json`: `msvcrt.locking` en Windows y `fcntl.flock` en POSIX, sin
bloquear. **Si el proceso muere, el sistema operativo suelta el candado**, sin antigüedad y sin
importar el reuso de PID. Para saber si una Execution tiene motor vivo, se intenta tomar el candado
sin esperar:

- si se toma, el motor está muerto. Se suelta enseguida;
- si no, está vivo;
- si falla por otra razón, se lo toma por vivo: ante la duda, no se cierra una Execution ajena.

## 14. Lifecycle materializado

#### MD-07. El estado sale de los archivos, y nadie reanuda

| Hay | Estado |
|---|---|
| un turno que la nombra, `request.json`, sin `entrega.json` ni `result.json` | `REQUESTED` |
| además `entrega.json`, sin `result.json` | `RUNNING` |
| `result.json` | su `status`: `SUCCEEDED`, `FAILED`, `CANCELLED` o `REJECTED` |
| una carpeta sin turno que la nombre, con o sin `request.json` | **no es una Execution**: es un residuo previo a la publicación (MD-04d) |

`cancelacion.json` no cambia el estado: es un pedido. Lo cumple el motor vivo, `--cancelar` sobre una
`REQUESTED` sin motor, o la recuperación (§14.1).

Un `result.json` que no pasa `validar_resultado`, o una request que no pasa `validar_request`, hacen
la Execution **ilegible**: cuenta como abierta para los duplicados (falla cerrada), y `--estado` lo
dice.

**Huérfana.** Una Execution `REQUESTED` o `RUNNING` cuyo candado de vida se puede tomar.

### 14.1 Recuperación

**La recuperación**, `recuperar(proyecto, clave)`, corre al principio de `--unidad` y de
`--cancelar`, y a pedido con `--recuperar`:

1. por cada turno cuya Execution no tiene `result.json`, intenta tomar su candado;
2. **`RUNNING` huérfana** (MD-24): toma la foto de ahora y la compara con `antes` de `entrega.json`.
   Si son iguales, la evidencia es `RESOLVED` con `files: []`; si no, `CHANGES_UNATTRIBUTABLE`. Después
   escribe `result.json`, con `startedAt` de la entrega, `agentDeclaredStatus` y `output` en `null`, y
   `host` de la entrega:
   - **si existe `cancelacion.json`**: `CANCELLED`, con código `CANCELLED`;
   - **si no existe**: `FAILED`, con `HOST_INTERRUPTED`.

   Un `output.md` que haya quedado no se usa: un resultado de recuperación no tiene AgentReport;
3. **`REQUESTED` huérfana:** no la toca. No se puede `FAILED` desde `REQUESTED`, ni `REJECTED` sin una
   condición de admisión que falle, ni entregarla, que sería reanudar (ME-07). Queda abierta y
   bloquea la clave hasta que una persona la cancele; `--estado` y el `DUPLICATE_EXECUTION` dicen el
   comando exacto (R2);
4. **barre los residuos previos a la publicación** (MD-04d): las carpetas sin turno con más de 10
   minutos y el candado libre. Nunca fueron Executions;
5. **borra los temporales de escritura** (`.<nombre>.<aleatorio>.tmp`) de toda carpeta cuyo candado
   esté libre, sea una Execution o un residuo.

#### MD-24. Una cancelación persistida gana sobre la muerte del motor

Si `cancelacion.json` quedó escrito antes de que el motor muriera, la intención explícita de cancelar
ya existe de forma durable, y precede a la interrupción. La recuperación termina la Execution
`CANCELLED`, no `FAILED` con `HOST_INTERRUPTED`. Así se conserva la diferencia de Task 3 entre una
cancelación explícita y una interrupción accidental (T3 §13, D16). `RUNNING → CANCELLED` ya es una
transición del ciclo: no se agrega ninguna.

**`--cancelar` mira primero y pide después**, para que el pedido nunca llegue tarde a una corrida
que ya estaba cortada:

1. corre la recuperación de la tarea. Una `RUNNING` cuyo motor ya había muerto queda `FAILED` con
   `HOST_INTERRUPTED`, porque el corte precedió al pedido; `--cancelar` lo informa y no escribe
   `cancelacion.json`;
2. si la Execution ya es terminal, lo informa y no cambia nada;
3. si no, escribe `cancelacion.json`:
   - con el motor vivo, el motor lo cumple: mata el árbol del Host si estaba `RUNNING`, y escribe
     `CANCELLED`. El motor mira el pedido antes de entregar y mientras el Host corre. Si el Host ya
     terminó, gana el resultado del Host;
   - con una `REQUESTED` sin motor, el propio `--cancelar` escribe `CANCELLED`, sin `startedAt` ni
     evidencia.

Si el motor muere después de que `cancelacion.json` quedó escrito, y antes de cumplirlo, la próxima
recuperación la cierra `CANCELLED`. La misma situación tiene un solo resultado.

**La regla general.** Cuando una corrida termina sin un resultado del Host, por una señal externa,
un Ctrl-C sobre el motor o la muerte del motor, quien escribe el resultado mira si existe
`cancelacion.json`:
- si existe, es `CANCELLED`;
- si no, es `FAILED` con `HOST_INTERRUPTED`.

Vale igual para el motor vivo y para la recuperación.

**Cuándo es seguro escribir el resultado:** solo con el candado tomado, es decir, con el motor
muerto. Si el motor vivo escribe su resultado al mismo tiempo, la escritura de una sola vez deja uno
solo, y el otro acepta el que quedó. **Un resultado tardío no pisa nada** (T3 D10).

**No hay reanudación** (T3 P9): ni checkpoint, ni volver a entregar una huérfana. Un reintento es
otra Execution.

**Si el Host sobrevivió al motor** (ME-20), la recuperación no lo mata: matar por PID puede matar
otro proceso que reusó el número. Lo avisa, y si hubo cambios, la evidencia ya dice
`CHANGES_UNATTRIBUTABLE`. Es un riesgo declarado (§33).

## 15. Idempotencia y reintento

La clave es la de T3 D19, sin cambios: `huella([taskKey, planFingerprint, workUnit.id])`. **El flujo
no entra en la identidad** (EX-I34): decide si se puede ejecutar ahora, no qué se ejecuta.

| Último turno de la clave | Qué pasa con una request nueva |
|---|---|
| ninguno | se crea el turno 1 |
| `REQUESTED` | `DUPLICATE_EXECUTION` |
| `RUNNING` | `DUPLICATE_EXECUTION` |
| `SUCCEEDED` | `DUPLICATE_EXECUTION`, siempre |
| `FAILED` | reintento: turno N+1, otro `executionId`, la misma clave |
| `CANCELLED` | reintento |
| `REJECTED` | reintento |
| ilegible | `DUPLICATE_EXECUTION`, con la causa en `detail` |

- **Después de un `SUCCEEDED` no hay más turnos.** Por eso, si una clave tiene un éxito, es su último
  turno. Varios `FAILED` y un `SUCCEEDED` al final es la historia normal de una unidad.
- **Una dependencia se satisface** si el último turno de la clave de la unidad de la que se depende
  (`huella([taskKey, planFingerprint, idDeLaDependencia])`) es `SUCCEEDED`. Su `executionId` va a
  `admission.dependencies`. No hace falta un índice global.
- **Un reintento no lo decide el motor:** lo pide una persona con otro `ejecutar`. T3 P1 sigue
  diferida.

## 16. Evidence

#### MD-20. Dos fotos del árbol y una regla de atribución por ruta

**La foto**, `instantanea(proyecto)`:

- `revision`: `git -C <proyecto> rev-parse HEAD`;
- `sucios`: cada ruta que `git status --porcelain=v1 -z --untracked-files=all` informa, con la huella
  `sha256:` de su contenido actual, o `null` si se borró;
- se excluye `.claude/ejecuciones/`.

Las dos llamadas son a `git` con un límite de 10 s, por `proceso.py` (MD-14).

**La evidencia**, al terminar:

- `repoRevisionBefore` y `repoRevisionAfter` son las dos revisiones;
- **los cambios** son las rutas cuya huella difiere entre las dos fotos, más las de
  `git diff --name-status -z <antes> <después>` si la revisión cambió (el agente hizo commit). Cada
  una es `ADDED`, `MODIFIED` o `DELETED`, con la huella de ahora.

**El estado de los cambios:**

| Estado | Cuándo |
|---|---|
| `RESOLVED` | Se pudieron tomar las dos fotos; ninguna ruta cambiada estaba sucia antes; y ninguna otra Execution del proyecto estuvo `RUNNING` en el mismo lapso. Una lista vacía quiere decir que no cambió nada |
| `CHANGES_UNATTRIBUTABLE` | Se observaron cambios que no se pueden atribuir: una ruta cambiada ya estaba sucia antes con otro contenido, otra Execution del proyecto corrió al mismo tiempo, o la recuperación cierra una huérfana con cambios |
| `CHANGES_UNRESOLVED` | No se pudo observar: sin `git`, fuera de un repositorio, o `git` no contestó a tiempo |

En los dos últimos, `files` va vacío, como pide T3 (EX-I25).

**El repo sucio antes de ejecutar** (ME-21):

- **se permite**. El motor no limpia, no hace `stash`, no hace `git reset` ni `checkout`;
- lo que estaba sucio y no cambió **no es de la Execution**: su huella es la misma en las dos fotos;
- lo que estaba limpio y cambió **es de la Execution**;
- lo que estaba sucio y cambió otra vez **no se puede separar**, y toda la evidencia pasa a
  `CHANGES_UNATTRIBUTABLE`.

**Qué no puede ver el motor:** que una persona edite un archivo limpio mientras corre el Host. Se le
atribuye a la Execution. Es el mismo límite que T3 §36 ("se confía en el motor") y va a §33.

**La evidencia no es contabilidad:** no lleva tokens, costo, tiempos ni llamadas a herramientas. El
tiempo vive solo en el resultado (EX-I29).

## 17. Output y redacción

#### MD-19. Se redacta todo lo que se persiste, y sin catálogo no se persiste

Con `contexto/limpieza.py`, el catálogo de la SecretGate:

| Qué | Cómo | Si no hay catálogo |
|---|---|---|
| `request.json` | En el orden de MD-23: redactar, validar, huella, persistir. Si la redacción cambia la `workUnit`, el plan tiene un secreto según el catálogo de hoy: `CONTRACT_INVALID`, sin Execution, y se replanifica | El comando falla y no crea la Execution |
| `output.md` | `redactar` del `artifact`; recortado a 1 MiB con `recortar` | `FAILED` con `ENGINE_FAILURE`, sin `output` |
| `result.json` | `error.detail` redactado y recortado a 300 | Se escribe igual, con un `detail` hecho solo de texto del motor (el código, el `subtype`, el código de salida), sin nada que venga del Host ni del agente |
| `cancelacion.json`, `requestedBy` | `redactar` | Como `request.json` |
| `host` | `sessionRef` es un UUID que genera el adaptador; `runRef` es `null`; `kind` es `claude-code` | — |
| stderr del Host | Solo entra a `detail`, redactado y recortado | — |

Falla cerrado, como `refutacion._limpiar` (`refutacion.py:1209-1226`): sin catálogo no se escribe
texto que vino de un agente.

**El output:**

- se llama `output.md`, porque el informe de un agente es Markdown para una persona. Execution no lo
  lee, así que la extensión no decide nada;
- está en UTF-8 y con LF;
- existe si y solo si hubo un AgentReport válido;
- en el resultado, `output.path` es la ruta relativa POSIX desde la raíz del proyecto
  (`.claude/ejecuciones/<KEY>/<exe>/output.md`) y `output.fingerprint` es `sha256:` de los bytes
  escritos;
- **el texto no entra a `result.json`** (T3 D8).

#### MD-15. Los ids que se vuelven rutas

- **`executionId`** se genera con `"exe_" + secrets.token_hex(16)`: 128 bits del generador
  criptográfico del sistema.
- **Todo id que se usa como carpeta** (`executionId`, TaskKey, el hex de la clave, el número de
  turno) se valida con `re.fullmatch`, nunca con `$`. Un `\n` final no pasa (ME-14).
- `contrato.py` no cambia: su validador sigue siendo el de Task 3, y el motor valida antes de usar
  un id como ruta.

#### MD-16. La ruta canónica

Toda ruta que el motor escribe en `output` o en `evidence.files`:

- es relativa a la raíz del proyecto, POSIX, sin `\`;
- no es absoluta, ni de unidad (`C:`), ni UNC;
- no tiene esquema (`file:`, `x:` en el primer tramo), ni `~` al principio;
- no tiene tramos vacíos, ni `.`, ni `..`, ni `/` al final;
- no tiene NUL ni caracteres de control;
- después de `realpath`, cae adentro de la raíz del proyecto: un enlace no la saca;
- no se repite, **sin distinguir mayúsculas en Windows y en macOS** (`os.path.normcase`), y
  distinguiendo en Linux.

Las rutas de la evidencia salen de `git`, y la del output la arma el motor. Si una no cumple, la
evidencia pasa a `CHANGES_UNRESOLVED` en vez de escribir una ruta dudosa. `contrato._ruta_mala` y
`_rutas` siguen igual (Task 3); esta política vive en `registro.py` y es más estricta.

## 18. Flow Governance en runtime

#### MD-12. P14: el TaskFlowState vigente se lee, no se reconcilia

- **La autoridad** es `permisos(doc, vig)["delegationAllowed"]` de `flujo/estado.py`, con:
  - `doc = estado.leer(proyecto, clave)`, el `state.json` guardado;
  - `vig = estado.vigencia_local(doc, proyecto, remotos=True, timeout=10)`.
- **Es lo mismo que mira la compuerta del flujo**, con el límite de 10 s de la CLI y no el de 1,5 s
  del hook (ME-06). Así no hereda la falla bajo carga.
- **El motor no reconcilia ni escribe estado del flujo.** Si el estado falta, no se lee, está
  desactualizado o `git remote -v` no contesta, no hay `delegationAllowed`, y es
  `DELEGATION_NOT_ALLOWED`. `detail` dice qué: el código del estado, la vigencia y los bloqueos, y el
  comando para reconciliar (`flujo <KEY> --status`, o la etapa que corresponda).
- **No hace falta una HostSession para admitir.** La TaskKey viene explícita, y el SessionTaskBinding
  no entra en la identidad (EX-I34). `SESSION_TASK_AMBIGUOUS` no aplica a la admisión: es de la
  compuerta del hook.

**Cuándo se lee:** dos veces, al pedir y al entregar (condición 6). Si entre una y otra una persona
cancela la tarea, el TaskContext cambia o se replanifica, la Execution termina `REJECTED` con
`DELEGATION_NOT_ALLOWED`.

#### MD-17. Durante la corrida, la compuerta del flujo sigue siendo del Host

- La sesión headless corre los hooks del proyecto. Su PreToolUse aplica la SecretGate y la
  compuerta del flujo a cada herramienta del agente.
- **La primera línea del prompt es `Seguimos con <TaskKey>.`** El UserPromptSubmit que ya existe
  (`flow_context.py:191-193`, `task_binding.clave_declarada`) vincula la sesión nueva a la tarea. Con
  dos tareas con estado, la compuerta ve `SESSION_TASK_BOUND` y no `AMBIGUOUS` (ME-11). No se toca
  `task_binding.py`.
- **Las dos compuertas siguen separadas.** La compuerta del flujo decide por herramienta y por
  sesión; la admisión, por WorkUnit, antes. La de Execution es más estricta: exige la etapa (ME-26).

```
HumanIntent ── flujo --approve / --alternative ──> replanifica                         (Planning)
TaskFlowState guardado + vigencia_local ── permisos().delegationAllowed ─┐
Plan 2.1 ── aceptar_guardado; listo por los dos lados; WorkUnit PENDING ─┤
NormativeFreshnessGate con requeridas ── allowed / unresolved ───────────┤   ExecutionAdmission
AgentRegistry, capacidades y adaptador ── ruteable, tipo, dominio, provee ┤   (dos veces)
Execution ── turnos: dependencias y duplicados ──────────────────────────┘
                                                                          │
                                                                          ▼
                     Execution persistida ─> Host Adapter ─> AgentReport ─> Evidence + Output ─> ExecutionResult

Durante la corrida, del lado del Host: SecretGate y compuerta del flujo en PreToolUse.
```

## 19. Normative Gate

#### MD-13. La admisión llama a la compuerta con las normas de la unidad

- **Se llama a `ensure_normative_knowledge_fresh`** con `requeridas` igual a las normas de la unidad:
  las claves de `workUnit.normative.standards`, que escribe Planning (`normativa.resolucion`).
  - Sin esa estructura, vale `["ES0901"]`, la misma regla que `refutacion.estandares_de_unidades`
    (`refutacion.py:523-537`).
  - Execution no importa la refutación: un escenario fija que dan lo mismo (ME-E29), como EX-E08 con
    la huella.
- **El resto de la llamada es como en `plan`**: el mismo observador de Jira del CLI y las mismas
  capacidades. Si la compuerta refresca, los efectos son suyos (MC, `### NormativeFreshnessGate`):
  la agenda y, si cambió, `harness.fuentes.json`. La segunda llamada, al entregar, no está vencida y
  no sale a la red.
- **`NORMATIVE_GATE_BLOCKED` se vuelve alcanzable.** Es una fuente de la unidad en
  `SOURCE_INTEGRITY_ALERT`, `SOURCE_CHANGED_SAME_VERSION` o `VERSION_REGRESSION`
  (`frescura.py:70`) que el `state.json` guardado todavía no refleja, por ejemplo porque la alerta
  apareció en el refresco de la propia admisión.
- **La causa se conserva:** `detail` dice `fuentes en alerta: ES0901 SOURCE_INTEGRITY_ALERT`, del
  `reason` de la compuerta.
- **Si el flujo ya lo vio**, sale antes `DELEGATION_NOT_ALLOWED`, por la precedencia (6 antes que 9),
  y su `detail` nombra el bloqueo `plan.knowledgeSources SOURCE_INTEGRITY_ALERT`. Es el hallazgo 1 de
  la reverificación: el código no cambia, y la causa no se pierde.
- **`unresolved` admite**, como en T3 D12.

Los códigos no cambian.

## 20. Agent y capabilities

#### MD-18. Agente del registro, herramientas mínimas

**Agent → implementación:**

1. el AgentRegistry es la autoridad: la condición 10 lo resuelve;
2. el adaptador busca `.claude/agents/<assignedAgent>.md` y exige que su `name:` sea ese id;
3. le pasa ese id al Host con `--agent`.

Un id que no está en el registro no llega al Host: la admisión lo rechaza antes. El motor nunca le
pasa al Host un agente que no revalidó al entregar.

**Capability → HostTool.** Una tabla en el adaptador, la mínima:

| Capability | Herramientas del Host |
|---|---|
| `repository.read` | `Read`, `Glob`, `Grep` |
| `repository.search` | `Grep`, `Glob` |
| `repository.write` | `Edit`, `Write` |
| `tests.run` | `Bash` |
| `jira.*`, `gitlab.*` | **ninguna**: el adaptador no las provee (EC-08) |
| cualquier otra | ninguna |

- **`provee(capacidad, agente)`** es verdadero si la capability está en la tabla y el `tools:` del
  agente tiene todas sus herramientas. Por ejemplo, `dev-architecture`, que no tiene `Write`, no
  provee `repository.write`.
- **Sale `REJECTED` con `CAPABILITY_UNAVAILABLE`** si la unidad pide una que no se provee, en la
  admisión al entregar, antes de `entrega.json`. Una herramienta negada durante la corrida es un
  hecho de esa llamada, no un estado de la Execution (T3 §15): el agente sigue, y lo que declare
  decide.
- **`--allowedTools`** es la unión de las herramientas de las capabilities de la unidad, intersecada
  con el `tools:` del agente, más `Skill` si el agente la tiene. **El agente recibe solo lo que su
  unidad pide** (ME-I24). Con `dontAsk`, lo demás se niega.
- **El modelo:** si `modelRouting.perfiles[<requiredTier>]` de `harness.config.json` está declarado
  (`modelo.perfiles_declarados`), va por `--model`. Si no, decide el Host. El tier no entra al
  request (T3 §10.1).

**Lo que no se construye:** un catálogo de herramientas, un registro de plugins o un mapa
configurable. La tabla tiene cuatro filas, porque hay cuatro capacidades locales (`roster.json:51-56`).

## 21. Error mapping

#### MD-10. Cada falla del Host, con su código y su frontera

**Antes de la entrega**, lo que falla no es una corrida:

| Qué pasó | Qué resulta |
|---|---|
| La configuración del motor es inválida, o el comando del Host no se resuelve (MD-22) | Un error del comando, **antes de crear la Execution**: sin ExecutionError, sin Execution, sin residuo |
| El adaptador no encuentra o no carga la definición del agente | `REJECTED` con `AGENT_UNAVAILABLE` (condición 10) |
| El adaptador no provee una capability de la unidad | `REJECTED` con `CAPABILITY_UNAVAILABLE` (condición 13) |

**Después de la entrega**, solo códigos de corrida o `CANCELLED` (§11.1, ME-I29):

| Qué pasó | Código | Estado |
|---|---|---|
| El comando ya resuelto no arranca: el sistema operativo lo rechaza, o desapareció entre resolverlo y lanzarlo | `HOST_FAILURE` | `FAILED`: la entrega ya pasó a `RUNNING` (T3 D10) |
| El Host no puede iniciar o cargar el agente | `HOST_FAILURE` | `FAILED`. Nunca `AGENT_UNAVAILABLE` |
| El Host terminó sin un JSON `type: result` legible por stdout | `HOST_FAILURE` | `FAILED` |
| `is_error: true` con un error del proveedor que el JSON identifica | `PROVIDER_FAILURE` | `FAILED`. Solo si el Host lo distingue (T3 D11); si no, `HOST_FAILURE`. Lo confirma ME-E50 |
| `subtype: error_during_execution`, `error_max_turns` u otro desconocido | `HOST_FAILURE` | `FAILED` |
| `subtype: error_max_structured_output_retries`, o `success` sin `structured_output` | `OUTPUT_INVALID` | `FAILED` |
| `structured_output` que no pasa `validar_informe` | `OUTPUT_INVALID` | `FAILED` |
| AgentReport válido con `PARTIAL`, `BLOCKED` o `FAILED` | `AGENT_DECLARED_NOT_COMPLETE` | `FAILED` |
| AgentReport válido con `COMPLETE` | — | `SUCCEEDED` |
| Venció el límite del motor | `TIMEOUT` | `FAILED`. El motor mata el árbol |
| El Host murió por una señal que el motor no mandó (130, 143, o terminado desde afuera), sin `cancelacion.json` | `HOST_INTERRUPTED` | `FAILED`. Con `cancelacion.json`, `CANCELLED` (MD-24) |
| Ctrl-C sobre el motor, sin `cancelacion.json` | `HOST_INTERRUPTED` | `FAILED`. El motor mata el árbol y escribe el resultado (T3 D16). Con `cancelacion.json`, `CANCELLED` (MD-24) |
| El motor murió, sin `cancelacion.json` | `HOST_INTERRUPTED` | `FAILED`, por la recuperación (§14.1) |
| El motor murió con `cancelacion.json` ya escrito | `CANCELLED` | `CANCELLED`, por la recuperación (MD-24) |
| Un pedido de cancelar con el motor vivo | `CANCELLED` | `CANCELLED`. Desde `REQUESTED` o `RUNNING` |
| Un pedido de cancelar una `REQUESTED` sin motor vivo | `CANCELLED` | `CANCELLED`, lo escribe `--cancelar` |
| Un pedido de cancelar una `RUNNING` cuyo motor ya había muerto | `HOST_INTERRUPTED` | `FAILED`. `--cancelar` recupera primero: el corte precedió al pedido, y no se escribe `cancelacion.json` (MD-24) |
| El motor falló después de la entrega: disco, sin catálogo, un error propio | `ENGINE_FAILURE` | `FAILED`. No se disfraza de falla del Host |

**Lo desconocido es `HOST_FAILURE`.** El adaptador no adivina: un `subtype` que no está en la tabla,
un código de salida raro o un JSON sin `type` son fallas del Host. `detail` lleva el `subtype`, el
código de salida y el principio de stderr, redactados.

**El límite** (T3 P11) es configuración del motor: `ejecucion.limiteSegundos` en
`harness.config.json`, y si no, 1800 s (MD-22). No va al request. Lo que se aplicó sale en el
`detail` de `TIMEOUT`.

#### MD-22. La configuración del motor: claves opcionales de `harness.config.json`

**El contrato de hoy permite extenderla: es la opción A.**

- MC `### HarnessConfig` dice "`.claude/harness.config.json` y `manifest.json`, **sin schema**".
- El instalador lo crea solo si falta y no lo vuelve a tocar (`install.ps1:839-865`, `:2026-2031`).
  Por eso "los proyectos instalados no reciben claves nuevas" (MC, Invariantes).
- El código ya lee claves opcionales con el default en el código: `timeoutIntegraciones` con
  `TIMEOUT_POR_DEFECTO` (`dev-harness.py:160`). El precedente que lo explica es
  `hooks/session-start.py:179-182`: "el default vive acá y no en el manifiesto".

Task 4 agrega `ejecucion.comandoHost` y `ejecucion.limiteSegundos` como claves opcionales, con el
default en el código. **No cambia ningún schema, ni `manifest.json`, ni el instalador**, y un
proyecto instalado antes funciona sin tocar su archivo. MC `### HarnessConfig` suma al motor entre
quienes la leen (§24).

| Clave | Ausente | Presente y válida | Presente e inválida |
|---|---|---|---|
| `ejecucion.comandoHost` | `shutil.which("claude")`. Si no lo encuentra, error | Se usa. Válida es una lista no vacía de textos no vacíos (el programa y sus primeros argumentos), cuyo primer elemento es un archivo que existe o un nombre que `shutil.which` resuelve | Error |
| `ejecucion.limiteSegundos` | 1800 | Se usa. Válido es un entero positivo, y un booleano no lo es | Error |
| `ejecucion` | Las dos ausentes | Un objeto | Error, si no es un objeto |

**Si `harness.config.json` existe y no es un objeto JSON legible**, también es error. El motor no cae
al default: lanza una corrida que cuesta, y el archivo pudo haber dicho otro Host. Los demás lectores
siguen como están.

**Todos estos errores pasan antes de crear la Execution:**

- son un error del comando, con exit 2;
- no son un ExecutionError ni un ExecutionResult, porque todavía no hay Execution;
- no dejan nada escrito.

Los prueban ME-E54 y ME-E55.

#### MD-14. Un proceso con límite, propio de Execution

`proceso.py` repite el algoritmo de `flujo/repositorio.py:201-238`:

- stdout y stderr a temporales;
- grupo de procesos propio en POSIX;
- `taskkill /F /T /PID` en Windows, y `killpg` en POSIX.

Agrega la espera por tramos de 1 s, para mirar `cancelacion.json` sin hilos.

No se importan las funciones de `flujo`: son privadas de Flow Governance, que esta Task no toca. La
duplicación va a §30 para consolidarla después, con el `harness-staff-engineer`.

## 22. Seguridad

| Amenaza | Mitigación | Capa dueña | Escenario |
|---|---|---|---|
| Request adulterada en disco | Al entregar no se confía en `request.json`: `validar_request`, y la unidad tiene que tener la huella de la del plan | Execution | ME-E28 |
| Plan adulterado o cambiado | `PLAN_CHANGED` por la huella | Execution, sobre Planning | ME-E07 |
| Plan viejo (2.0 o 1.0) | Se lee y no se admite: `PLAN_NOT_READY` | Planning y Execution | ME-E30 |
| El TaskFlowState cambió entre pedir y entregar | Se vuelve a leer: `DELEGATION_NOT_ALLOWED` | Planning (flujo) | ME-E08 |
| Agente falsificado | Registro al pedir y al entregar, y el archivo del Host con su `name:`, antes de la entrega | Catalog y el adaptador | ME-E10, ME-E42 |
| Una request cuyo `requestFingerprint` no es el de lo persistido | Redactar, validar, huella y persistir, en ese orden (MD-23) | Execution | ME-E01, ME-E24 |
| Un comando de Host apuntado por una configuración rota | La configuración se valida antes de crear la Execution, y un archivo ilegible no cae al default | Execution | ME-E54, ME-E55 |
| Capability falsificada | La disponibilidad sale de Catalog y del adaptador, nunca del request | Catalog y el adaptador | ME-E11, ME-E41 |
| Path traversal | MD-16; los ids con `fullmatch` | Execution | ME-E23, ME-E36 |
| Replay o duplicado | Turnos exclusivos; un `SUCCEEDED` cierra la clave | Execution | ME-E13, ME-E14, ME-E18 |
| Pisar request o resultado | Escritura de una sola vez | Execution | ME-E21, ME-E22 |
| Un secreto que se persiste | MD-19 y MD-23, falla cerrada | Execution, con el catálogo de Guardrails | ME-E24 |
| Acceso arbitrario a herramientas del Host | `--allowedTools` mínimo y `dontAsk`; nunca `--bare` ni saltear permisos; los hooks siguen | El adaptador y el Host | ME-E39, ME-E40 |
| El agente escribe la autoridad del flujo | La compuerta del flujo protege `.claude/` en la sesión headless | Guardrails | ME-E39 |
| Un AgentReport falsificado por el modelo de una sesión | No hay retransmisión: el adaptador lee la salida del Host que lanzó | El adaptador | ME-E29 |
| El texto del agente como instrucción | El `artifact` no se interpreta; el `result` del Host no se lee | Execution y el adaptador | ME-E03, ME-E29 |

## 23. CLI y API mínimas

#### MD-01. Un subcomando, `ejecutar`

```
dev-harness.py ejecutar <KEY> --unidad <id> [--pedido-por <texto>] [--json]
dev-harness.py ejecutar <KEY> --cancelar <executionId> [--json]
dev-harness.py ejecutar <KEY> --estado [--json]
dev-harness.py ejecutar <KEY> --recuperar [--json]
```

- **Quién crea la request:** el propio `ejecutar --unidad`. Pedir y correr son un solo comando,
  porque no hay cola (Task 5).
- **Cómo se elige la unidad:** por su id, explícito. El motor no elige la siguiente: eso es
  scheduling.
- **Cómo se cancela:** `--cancelar`, desde otra terminal. Recupera primero y pide después (MD-24).
- **Cómo se consulta:** `--estado`, que solo lee: lista los turnos de la tarea por clave, con el
  estado derivado y las huérfanas sospechadas, sin escribir.
- **La salida:** con `--json`, el `result.json` o el ExecutionError por stdout.
- **El código de salida:** 0 si la Execution quedó `SUCCEEDED`; 2 si la admisión la rechazó al pedir
  o terminó en otro estado. Es la convención del CLI (`dev-harness.py:2152-2162`).
- **El nombre** sigue a los verbos del CLI (`reconfigurar`) y a `ejecucion/`. Alternativas que se
  descartaron: `run` y `execute`, por inglés; `refute`-style `--compile/--unit`, porque acá no hay
  dos pasos.

**La API interna**, sin una clase grande:

```python
motor.ejecutar(proyecto, clave, unidad, pedido_por, adaptador=None, config=None) -> (resultado | None, error | None)
motor.cancelar(proyecto, clave, execution_id, pedido_por) -> resultado | None
motor.recuperar(proyecto, clave) -> [executionId cerradas]
motor.estado(proyecto, clave) -> [{turno, executionId, estado, huerfana}]

admision.al_pedir(proyecto, clave, unidad, pedido_por) -> (request | None, error | None)
admision.al_entregar(proyecto, request, adaptador) -> error | None

registro.crear(proyecto, request) -> executionId | DUPLICATE      # MD-04
registro.escribir_una_vez(ruta, bytes)                             # MD-05
registro.estado(proyecto, clave, execution_id) -> estado derivado  # MD-07

evidencia.instantanea(proyecto) -> foto
evidencia.armar(antes, despues, otras_corriendo) -> ExecutionEvidence

host_claude_code.Adaptador(comando, config).entregar(request, carpeta, cancelada) -> (informe, falla, host)
```

## 24. Modelo canónico

Lo que cambia en `docs/dominio/modelo-canonico.md`:

- **`### Host`**: el invariante de ME-01.
- **`### Execution`**, **`### ExecutionRequest`**, **`### ExecutionAdmission`** y
  **`### ExecutionResult`**: "Crea / cambia / lee" pasa a lo real (el motor, la admisión, el
  registro), y "Persistencia y contrato" dice el registro de MD-03. Sin conceptos nuevos (§7.2).
- **`## El límite de la ejecución`**: el motor, la admisión, el almacenamiento y el Host Adapter pasan
  de *Lo que todavía no existe* a *Lo que existe ahora*. Siguen sin existir el scheduler, las colas,
  los workers, el reintento automático, la reanudación y el cliente de modelo.
- **Mapa de contextos**: la fila de Execution pasa de "contractual hasta la Task siguiente" a "una
  WorkUnit por invocación; Task 5 decide el resto".
- **Vocabulario**: "turno de intento" y "candado de vida", como infraestructura de Execution; "Host
  Adapter" deja de decir "A futuro".
- **Relaciones**: `Host → Execution` deja de decir "A futuro".
- **`### HarnessConfig`**: entre quienes la leen, suma el motor de ejecución, con las claves
  opcionales `ejecucion.*` y su default en el código (MD-22). Sigue sin schema.

## 25. ADR previsto

**ADR-0015 — El motor mínimo de ejecución.** Se escribe en la construcción, cuando esta spec esté
aprobada. Sus decisiones:

1. Una WorkUnit, un intento, sincrónico, por invocación de `ejecutar`. El scheduling es de Task 5.
2. El registro de cada Execution es de archivos que se escriben una sola vez, y el estado se deriva
   de cuáles existen. No hay `state.json`.
3. La reserva atómica de la `idempotencyKey` son turnos de intento por clave, creados de forma
   exclusiva. Una Execution existe si y solo si un turno la nombra.
4. La vida del motor es un candado del sistema operativo. Una `RUNNING` sin motor vivo termina
   `FAILED` con `HOST_INTERRUPTED`, o `CANCELLED` si un pedido de cancelar ya estaba persistido. No hay
   reanudación. Una carpeta sin turno no es una Execution, y se recoge como residuo.
5. El Host Adapter de Claude Code lanza `claude -p` con `--agent` y salida estructurada. El
   AgentReport sale de `structured_output`, y nadie interpreta texto.
6. La admisión lee el TaskFlowState guardado y su vigencia local, y no escribe estado del flujo.
   Llama a la compuerta normativa con las normas de la unidad.
7. HARNESS lanza el Host, nunca un modelo. Revisa el invariante de MC `### Host`.

**Revisa** ADR-0014 en lo que dejaba para Task 4, sin cambiar sus siete decisiones. ADR-0013 y
ADR-0014 no se editan.

## 26. Compatibilidad

| Contrato | ¿Cambia? |
|---|---|
| `orchestration-plan/2.1` | No. Se lee por `aceptar_guardado` y `estado_de` |
| `execution-request/1.0` y `execution-result/1.0` | No. Se escriben tal cual los validan los schemas de Task 3 |
| `task-flow-state/1.0` y Flow Governance | No. Se leen; el motor no los escribe |
| Contabilidad | No. Ningún evento nuevo (MP-02); `execution-accounting-event` igual |
| Refutación y seguridad | No. La evidencia no se proyecta (T3 P4) |
| Agent Registry | No. Se lee |
| Hooks y política de herramientas | No |
| `install.ps1` y `manifest.json` | No: `Copy-Arbol` copia `bin/` entero, y el lock se genera. ME-E26 lo prueba en un proyecto instalado |
| `harness.config.json` | No tiene schema. Suma dos claves opcionales, `ejecucion.comandoHost` y `ejecucion.limiteSegundos`, con el default en el código y sin entrar a `manifest.json` (MD-22). Un proyecto instalado antes funciona sin tocar su archivo |

### 26.1 Contabilidad y observabilidad

#### MD-21. Sin eventos contables, y la observabilidad es el registro

Execution no depende de la contabilidad para decidir nada (ADR-0013 §4). T3 D15 dejaba a Task 4 la
publicación de `WORKUNIT_*` y la clave `metadata.executionId`. **Se difiere** (MP-02), porque el
pedido prefiere no bloquear el motor por la contabilidad, y nada del motor la necesita.

| Qué | Dónde vive | Para qué |
|---|---|---|
| ExecutionResult | `result.json` | El estado terminal, el error y el tiempo del intento |
| ExecutionEvidence | `result.json`, en `evidence` | Lo que cambió en el árbol |
| La marca de entrega y el proceso | `entrega.json`, `proceso.json` | Diagnosticar una huérfana: la foto de antes, el pid del motor y del Host, la sesión |
| Logs | **No hay archivos de log.** El CLI escribe su avance por stderr, y con `--json` el resultado por stdout | Lo que pasó en una corrida se lee del registro |
| AccountingEvent | No lo emite el motor | Si hace falta, `contabilidad --ingerir <transcripción> --unidad <id> --agente <agente>`, que ya existe, carga la sesión `host.sessionRef` a la unidad |
| Metadata del Host | `result.json`, en `host`: `kind`, `sessionRef` | Encontrar la transcripción del Host para esa corrida |

No hay trazas distribuidas, métricas ni un tablero.

### 26.2 Tests de tareas anteriores que cambian, con su decisión

| Test | Qué afirmaba | Qué afirma ahora | Por qué |
|---|---|---|---|
| `64` E-41 | Los procesos lanzan solo `git` y `markitdown`, y `taskkill` solo desde `flujo/repositorio.py` | Además, `claude` solo desde `ejecucion/host_claude_code.py`, y `git` y `taskkill` desde `ejecucion/proceso.py` | ME-01, MD-08, MD-14; T3 §34.3.7 lo preveía |
| `64` E-09 | Los anclajes del límite: "motor", "admisión", "almacenamiento" y "Host Adapter" en *Lo que todavía no existe* | Pasan a *Lo que existe ahora*; siguen sin existir el scheduler y el reintento | §24 |
| `65` EX-E47 | Lo mismo, desde Task 3 | Igual que E-09 | §24 |
| `65` EX-E49 | Doce subcomandos, ninguno ejecuta, y nada importa concurrencia | Trece, con `ejecutar`; nada importa `threading`, `multiprocessing`, `asyncio`, `concurrent`, `sched` ni `queue`: eso sigue (ME-E47) | MD-01 |
| `65` EX-E51 | E-41 igual al de `fdca5ce` | E-41 igual al de esta Task | La línea anterior |
| `65` EX-E52 | `bin/ejecucion/` no escribe ni lanza procesos; nada nombra `.claude/ejecuciones`; nadie importa `ejecucion` | **`contrato.py`** no escribe, no lanza y no importa refutación ni contabilidad (sigue, ME-E46); los demás módulos sí escriben, solo bajo `.claude/ejecuciones/`; `dev-harness.py` importa `ejecucion.motor` | MD-03 |
| `65` EX-E50 | `bin/ejecucion/` no nombra `maxRetries`, `allowEscalation`, `retryPolicy` ni `timeoutSeconds` | No cambia: el motor usa `limiteSegundos` y no tiene reintento | — |

Cada cambio lleva un comentario en el test con su decisión de esta spec, como hizo Task 3.

**Ajuste documental de la construcción: cuatro más que esta tabla no listaba.** Aparecieron al
construir, son consecuencia directa de decisiones que la spec ya tomaba, y cada una lleva su
comentario en el test. Ninguna afloja una garantía distinta de la que la decisión cambia:

| Test | Qué afirmaba | Qué afirma ahora | Por qué |
|---|---|---|---|
| `64` E-22 | Cinco módulos de `bin/` arman una ruta bajo `.claude/planes/` | Seis, con `ejecucion/admision.py`; y dos aserciones nuevas: la admisión lee el plan por `aceptar_guardado` y no lo escribe | ME-27 |
| `65` EX-G06 | `bin/ejecucion/` no importa un hook ni el flujo | No importa un hook; del flujo, solo `admision.py` importa `flujo.estado`, y nada importa `estado_de_tarea`. Sigue sin nombrar `state.json` ni `runtime/tasks` | MD-12: la admisión lee el TaskFlowState con `estado.leer`, `vigencia_local` y `permisos` |
| `65` EX-G11 | `dev-harness.py` es el de `fdca5ce` | Sale de la lista de lo protegido de 0.31.0; sus subcomandos los cuida EX-E49 | MD-01: `dev-harness.py` suma `ejecutar` (§31.1) |
| `63-harness-unico-instalador` E-15 y E-16 | El lock del instalado tiene 286 rutas: las de `ea2dff7` y las cuatro del contrato | 292: suma los seis módulos del motor, que E-16 saltea como a las del contrato | §31.1: los seis módulos nuevos de `bin/ejecucion/` llegan solos por `Copy-Arbol`; ME-E26 los prueba instalados |

## 27. Invariantes

**Se verifica en** dice dónde se puede contradecir cada uno: en esta Task con un test, o en una
lectura.

| Id | Invariante | Cómo se observa | Escenario |
|---|---|---|---|
| ME-I01 | Una Execution es una WorkUnit y un intento | Un turno, una request, una unidad | ME-E01 |
| ME-I02 | `request.json` se escribe una vez | La escritura de una sola vez | ME-E21 |
| ME-I03 | Todo archivo del registro se escribe una vez; `result.json` también | Ídem | ME-E22 |
| ME-I04 | A lo sumo una Execution abierta o `SUCCEEDED` por clave | Turnos | ME-E13, ME-E14 |
| ME-I05 | Reservar la clave y crear la Execution es una sola operación respecto de otras admisiones | Turno exclusivo, request escrita antes | ME-E18 |
| ME-I06 | Al entregar se aplica la misma regla, sin confiar en lo guardado | Admisión dos veces | ME-E07 a ME-E12, ME-E28 |
| ME-I07 | La Execution no es duplicado de sí misma | Último turno propio | ME-E19 |
| ME-I08 | Un terminal no cambia | Escritura de una sola vez | ME-E22 |
| ME-I09 | Un reintento es otra Execution, con la misma clave | Turno N+1 | ME-E15 a ME-E17 |
| ME-I10 | Después de `FAILED`, `CANCELLED` o `REJECTED`, se puede reintentar | Turnos | ME-E15 a ME-E17 |
| ME-I11 | Después de `SUCCEEDED`, no | Turnos | ME-E14 |
| ME-I12 | La salida del Host pasa solo por el adaptador, y Execution recibe un AgentReport | `validar_informe` | ME-E01, ME-E03 |
| ME-I13 | Nadie interpreta texto: ni Execution el `artifact`, ni el adaptador el `result` | Estático y comportamiento | ME-E29 |
| ME-I14 | No hay reanudación | Una huérfana no se vuelve a entregar | ME-E20 |
| ME-I15 | Una `RUNNING` sin motor vivo termina `FAILED` con `HOST_INTERRUPTED` si no hay `cancelacion.json`, y solo la escribe quien tomó el candado | Recuperación | ME-E20, ME-E53 |
| ME-I16 | Toda ruta persistida es canónica y adentro del proyecto | MD-16 | ME-E23 |
| ME-I17 | Lo persistido está redactado, y sin catálogo no se persiste texto del agente ni del Host | MD-19 | ME-E24, ME-E33 |
| ME-I18 | La evidencia no es contabilidad, y el motor no lee ledgers | Estático; schema | ME-E46 |
| ME-I19 | El plan es exacto por su huella | `PLAN_CHANGED` | ME-E07 |
| ME-I20 | El flujo decide la admisibilidad, no la identidad, y el motor no escribe estado del flujo | MD-12 | ME-E08, ME-E45 |
| ME-I21 | Una Execution existe si y solo si un turno la nombra | Registro | ME-E37, ME-E52 |
| ME-I22 | Un pedido de cancelar persistido antes de que la corrida termine o se corte da `CANCELLED`, también si el motor muere después; un corte sin pedido persistido da `HOST_INTERRUPTED`; nunca al revés | Motor, `--cancelar` y recuperación (MD-24) | ME-E05, ME-E06, ME-E34, ME-E53 |
| ME-I23 | El motor nunca lanza el Host con `--bare` ni salteando permisos | Argumentos del adaptador | ME-E39 |
| ME-I24 | El agente recibe solo las herramientas de las capabilities de su unidad | `--allowedTools` | ME-E40 |
| ME-I25 | Un id solo se usa como ruta después de validarlo con anclaje completo | MD-15 | ME-E36 |
| ME-I26 | `contrato.py` sigue puro | Estático | ME-E46 |
| ME-I27 | Una corrida por invocación: sin scheduler, hilos, colas ni workers | Estático | ME-E47 |
| ME-I28 | Una carpeta sin un turno que la nombre no representa una Execution, no participa de la idempotencia, no aparece en `--estado`, y la recuperación la recoge como residuo previo a la publicación cuando su candado está libre y pasó el umbral | Registro y recuperación (MD-04d) | ME-E52, ME-E37 |
| ME-I29 | Después de `entrega.json`, el motor solo escribe códigos de corrida o `CANCELLED`: nunca `AGENT_UNAVAILABLE` ni `CAPABILITY_UNAVAILABLE` en `FAILED`, aunque T3 §14 los permita | El armado del resultado (§11.1, MD-10) | ME-E42, ME-E04 |
| ME-I30 | `requestFingerprint` es la huella del `request.json` persistido, que es la request ya redactada y validada | MD-23 | ME-E01, ME-E24 |
| ME-I31 | Una configuración del motor inválida, o un comando de Host que no se resuelve, se rechaza antes de crear la Execution, sin residuo | MD-22 | ME-E54, ME-E55 |
| ME-I32 | Agregado por la enmienda (§34): un código de salida del Host distinto de 0 nunca produce `SUCCEEDED` | MD-10′ | ME-E56 |

## 28. Escenarios

Todos pasan por la suite, con un Host falso (§29), salvo ME-E50, que es una lectura. Cada test nombra
su id en el título.

### El camino feliz y el AgentReport

- **ME-E01** — Con un plan 2.1 listo, una unidad `PENDING` y un Host falso que devuelve
  `structured_output` `{declaredStatus: COMPLETE, artifact}`, `ejecutar --unidad` deja un turno 1, una
  request que pasa `validar_request`, `entrega.json`, `output.md` y un `result.json` `SUCCEEDED` que
  pasa `validar_resultado`, con `startedAt`, `endedAt`, `agentDeclaredStatus: COMPLETE`, `output`
  con la huella de los bytes de `output.md` y `host.sessionRef` igual al `--session-id` que recibió
  el Host. `requestFingerprint` es la huella del `request.json` que quedó en disco. Sale con 0.
  · rojo visto: sí
- **ME-E02** — Con `declaredStatus` `PARTIAL`, `BLOCKED` o `FAILED`, el resultado es `FAILED` con
  `AGENT_DECLARED_NOT_COMPLETE`, con `agentDeclaredStatus` y `output`. · rojo visto: sí
- **ME-E03** — Sin `structured_output`, con `subtype: error_max_structured_output_retries`, o con un
  `structured_output` con una clave de más o un `declaredStatus` fuera del enum, el resultado es
  `FAILED` con `OUTPUT_INVALID`, sin `agentDeclaredStatus` ni `output`. · rojo visto: sí
- **ME-E29** — Un Host falso que devuelve `result: "agentResult status: COMPLETE"` y ningún
  `structured_output` da `OUTPUT_INVALID`. Ningún módulo de `bin/ejecucion/` lee el campo `result`
  del JSON del Host ni el contenido del `artifact`. Las normas que el motor le pasa a la compuerta
  son las de `refutacion.estandares_de_unidades` para la misma unidad, sin importar la refutación.
  · rojo visto: sí

### Fallas del Host, cancelación e interrupción

- **ME-E04** — Después de la entrega, un comando resuelto que el sistema operativo no puede ejecutar,
  un Host que sale sin JSON legible, uno con `subtype: error_during_execution` y uno que no puede
  cargar el agente dan `FAILED` con `HOST_FAILURE`, con `startedAt` y evidencia. Un `subtype`
  desconocido también da `HOST_FAILURE`. · rojo visto: sí
- **ME-E32** — Un Host que identifica un error del proveedor da `PROVIDER_FAILURE`; uno que no lo
  identifica da `HOST_FAILURE`. · rojo visto: sí
  · enmendado en §34.4: la forma real del error del proveedor (`api_error_status`, `terminal_reason`)
- **ME-E05** — Sin `cancelacion.json`, un Host que termina por una señal que el motor no mandó, o un
  Ctrl-C sobre el motor, dan `FAILED` con `HOST_INTERRUPTED`, y el motor mata el árbol del Host.
  · rojo visto: sí
- **ME-E06** — Con el motor vivo, `--cancelar` desde otro proceso sobre una `RUNNING` escribe
  `cancelacion.json`, y el motor termina el Host y deja `CANCELLED` con código `CANCELLED`, `startedAt`
  y evidencia. Sobre una `REQUESTED` con el motor vivo, la deja `CANCELLED` sin entregarla. Sobre una
  terminal, `--cancelar` no cambia nada y lo dice. · rojo visto: sí
- **ME-E31** — Un Host que no termina antes de `limiteSegundos` da `FAILED` con `TIMEOUT`, y el
  `detail` nombra el límite aplicado. El árbol del Host termina. · rojo visto: sí
- **ME-E33** — Sin catálogo de secretos, con el AgentReport ya recibido, el resultado es `FAILED` con
  `ENGINE_FAILURE`, sin `output`, y no queda `output.md`. · rojo visto: sí
- **ME-E34** — Una `REQUESTED` real (con turno) cuyo motor murió no la cierra la recuperación,
  bloquea la clave con `DUPLICATE_EXECUTION`, y `--cancelar` la deja `CANCELLED` sin `startedAt` ni
  evidencia. Una `RUNNING` cuyo motor ya había muerto, con `--cancelar`, queda `FAILED` con
  `HOST_INTERRUPTED`, y no se escribe `cancelacion.json`: el corte precedió al pedido.
  · rojo visto: sí

### La admisión al entregar

- **ME-E07** — Si el plan cambia entre la creación y la entrega, por cualquier campo, uno de 2.1
  incluido (`flowPreconditions`), la Execution termina `REJECTED` con `PLAN_CHANGED`, aunque
  `plan_id` y `plan_version` coincidan. · rojo visto: sí
- **ME-E08** — Si el TaskFlowState deja de permitir delegar entre la creación y la entrega (una
  cancelación de la tarea, un TaskContext cambiado), termina `REJECTED` con `DELEGATION_NOT_ALLOWED`,
  y el `detail` nombra el bloqueo. · rojo visto: sí
- **ME-E09** — Con una fuente de la unidad en `SOURCE_INTEGRITY_ALERT` en `harness.fuentes.json` y el
  `state.json` todavía sin reflejarlo, la admisión da `NORMATIVE_GATE_BLOCKED` y el `detail` nombra
  la fuente y su estado. Con la misma alerta sobre una fuente que la unidad no exige, admite.
  · rojo visto: sí
- **ME-E10** — Si el agente deja de ser ruteable entre la creación y la entrega, termina `REJECTED`
  con `AGENT_UNAVAILABLE`. · rojo visto: sí
- **ME-E11** — Si una capability deja de estar disponible entre la creación y la entrega, termina
  `REJECTED` con `CAPABILITY_UNAVAILABLE`. · rojo visto: sí
- **ME-E12** — Una unidad con una dependencia sin `SUCCEEDED` en la misma huella se rechaza al pedir
  con `DEPENDENCY_NOT_SATISFIED`. Con la dependencia `SUCCEEDED`, se admite y
  `admission.dependencies` nombra esa Execution. · rojo visto: sí
- **ME-E27** — Al pedir, la regla corre en el orden de T3 §37.5 y gana la primera falla: con dos
  condiciones rotas a la vez, sale el código de la anterior. Ningún rechazo al pedir deja algo
  escrito. · rojo visto: sí
- **ME-E28** — Un `request.json` editado a mano entre la creación y la entrega (una clave de más en
  `workUnit`, otra `admission`) termina `REJECTED` con `CONTRACT_INVALID`. · rojo visto: sí
  · fortalecido en §34.4: cualquier cambio de la request persistida, admission, requestedBy y createdAt incluidos
- **ME-E30** — Un plan 2.0 legible, con `status: READY_FOR_EXECUTION` escrito, se rechaza con
  `PLAN_NOT_READY`; un JSON de plan cortado, con `PLAN_UNREADABLE`; un plan de otra TaskKey, con
  `TASK_KEY_MISMATCH`; un plan con dos unidades con el mismo id, con `PLAN_UNREADABLE`.
  · rojo visto: sí
- **ME-E41** — Una unidad que pide `jira.issue.read`, disponible para Catalog, se admite al pedir y
  termina `REJECTED` con `CAPABILITY_UNAVAILABLE` al entregar, porque el adaptador no la provee. Una
  que pide `repository.write` con un agente sin `Write` también. · rojo visto: sí
- **ME-E42** — Con el agente en el registro y sin `.claude/agents/<agente>.md`, o con otro `name:`,
  la Execution termina `REJECTED` con `AGENT_UNAVAILABLE`, sin `entrega.json`, y el Host no se lanza.
  Con la definición presente y un Host que no la puede cargar después de la entrega, termina `FAILED`
  con `HOST_FAILURE`. Ningún `result.json` que escriba el motor tiene `FAILED` con
  `AGENT_UNAVAILABLE` o `CAPABILITY_UNAVAILABLE`. · rojo visto: sí

### Idempotencia, reintento y atomicidad

- **ME-E13** — Con una Execution `REQUESTED` o `RUNNING` de la misma clave, una request nueva da
  `DUPLICATE_EXECUTION` al pedir y no escribe nada. · rojo visto: sí
- **ME-E14** — Con una `SUCCEEDED` de la misma clave, una request nueva da `DUPLICATE_EXECUTION`,
  aunque después haya pasado cualquier cosa. · rojo visto: sí
- **ME-E15** — Después de una `FAILED`, una request nueva crea el turno 2, con otro `executionId` y la
  misma `idempotencyKey`. · rojo visto: sí
- **ME-E16** — Lo mismo después de una `CANCELLED`. · rojo visto: sí
- **ME-E17** — Lo mismo después de una `REJECTED`. · rojo visto: sí
- **ME-E18** — EX-F01: dos procesos del sistema operativo admiten la misma clave con un punto de
  encuentro entre la lectura del último turno y la reserva. Queda exactamente una Execution, un
  `DUPLICATE_EXECUTION`, un turno, una carpeta y ningún temporal. Repetido 20 veces sin punto de
  encuentro, siempre lo mismo. · rojo visto: sí
- **ME-E19** — EX-F02: una Execution `REQUESTED` pasa la condición 15 al entregar y llega a `RUNNING`.
  Si el último turno de su clave nombra a otra Execution abierta o `SUCCEEDED`, termina `REJECTED`
  con `DUPLICATE_EXECUTION`. · rojo visto: sí
- **ME-E37** — El barrido es seguro. Una carpeta sin turno con el candado tomado, que es una
  admisión en curso, no se barre aunque tenga más de 10 minutos. Una con el candado libre y menos de
  10 minutos tampoco. · rojo visto: sí
- **ME-E52** — Un corte antes de publicar. El caso es una carpeta con `vivo.lock`, un `request.json`
  completo y válido, un temporal de escritura y ningún turno que la nombre, con el candado libre:
  - no aparece en `--estado` ni cuenta como `REQUESTED`;
  - una admisión nueva de la misma clave pasa el chequeo de duplicados y crea el turno 1;
  - la recuperación borra la carpeta entera, temporal incluido, cuando pasan los 10 minutos.

  Una `REQUESTED` real de la misma forma, pero con turno, sí bloquea la clave y la recuperación no la
  borra. · rojo visto: sí

### Persistencia y recuperación

- **ME-E20** — Una `RUNNING` sin `cancelacion.json` cuyo motor murió (el proceso del motor terminado
  a la fuerza) la cierra la recuperación con `FAILED` y `HOST_INTERRUPTED`, `startedAt` de la entrega
  y evidencia `CHANGES_UNATTRIBUTABLE` si el árbol cambió, o `RESOLVED` vacía si no. Con el motor
  vivo, la recuperación no la toca. No se vuelve a entregar, y la recuperación no mata ningún proceso.
  · rojo visto: sí
- **ME-E53** — Una cancelación persistida antes de que el motor muera. Hay dos Executions `RUNNING`
  cuyo motor murió, iguales salvo por `cancelacion.json`:
  - la que lo tiene queda `CANCELLED`, con código `CANCELLED`;
  - la que no lo tiene queda `FAILED`, con `HOST_INTERRUPTED`.

  Las dos llevan `startedAt` de `entrega.json` y evidencia, sin `agentDeclaredStatus` ni `output`
  aunque haya quedado un `output.md`. Ninguna se vuelve a entregar, y la recuperación no mata ningún
  proceso. · rojo visto: sí
- **ME-E21** — Escribir otra vez el `request.json` de una Execution falla sin cambiar un byte, y no
  deja temporales; lo mismo cualquier archivo del registro. Una falla a mitad de escritura no deja ni
  el destino ni el temporal. · rojo visto: sí
- **ME-E22** — Un resultado tardío, después de que otro proceso ya escribió `result.json`, no lo pisa:
  queda el primero. · rojo visto: sí
- **ME-E23** — Una ruta de evidencia o de output que no es canónica (`./a`, `a/./b`, `a//b`, `a/`,
  `.`, `~/x`, `file:///x`, `C:/x`, `\\srv\x`, `../x`, un enlace que sale del proyecto) no se persiste;
  dos que solo difieren en mayúsculas cuentan como repetidas en Windows. · rojo visto: sí
- **ME-E24** — Un `artifact` con un secreto de confianza alta se guarda redactado en `output.md`, y su
  huella es la del texto redactado. Un `requestedBy` con un secreto queda redactado en `request.json`,
  y el `requestFingerprint` del resultado es la huella de esa request redactada, no de la original. Un
  `detail` con un secreto también se redacta. Si la redacción cambiaría la `workUnit`, la admisión da
  `CONTRACT_INVALID` y no se crea la Execution. · rojo visto: sí
  · fortalecido en §34.4: secreto después del corte de stderr, y en un structured_output inválido
- **ME-E35** — `--estado` no escribe ningún archivo. Lista los turnos de la tarea con su estado
  derivado, marca como sospechada una huérfana sin cerrarla, e informa como ilegible una Execution
  cuyo `result.json` no pasa `validar_resultado`, que además cuenta como abierta para los duplicados.
  · rojo visto: sí
- **ME-E36** — Los `executionId` que genera el motor cumplen `^exe_[0-9a-f]{32}$` con `fullmatch` y no
  se repiten en 10 000. Un `executionId`, una TaskKey o una clave con `\n` final no se usan como
  ruta. · rojo visto: sí

### Evidencia

- **ME-E25** — Con el repo sucio antes de ejecutar: si el Host cambia solo archivos que estaban
  limpios, la evidencia es `RESOLVED` con esos archivos y sin los sucios; si cambia un archivo que ya
  estaba sucio, es `CHANGES_UNATTRIBUTABLE` con `files: []`. El motor no limpia ni resetea nada: el
  archivo sucio que no se tocó queda igual. · rojo visto: sí
- **ME-E43** — En un proyecto sin `git`, la evidencia es `CHANGES_UNRESOLVED` con `files: []`. Con un
  commit del Host durante la corrida, los archivos del commit están en `files` y las dos revisiones
  difieren. · rojo visto: sí
- **ME-E44** — Con otra Execution del mismo proyecto `RUNNING` durante la corrida, la evidencia es
  `CHANGES_UNATTRIBUTABLE`. · rojo visto: sí

### Flow Governance y el Host

- **ME-E38** — Con `modelRouting.perfiles[<requiredTier>]` declarado en `harness.config.json`, el
  adaptador pasa `--model` con ese perfil; sin declarar, no pasa `--model`. Nunca pasa
  `--max-budget-usd`. El tier sale de `workUnit.modelPolicy.requiredTier` y no entra al request.
  · rojo visto: sí
- **ME-E39** — Los argumentos con que el adaptador lanza el Host nunca tienen `--bare`,
  `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions` ni
  `--permission-mode bypassPermissions`, y siempre tienen `--permission-mode dontAsk`,
  `--permission-prompts none`, `--output-format json`, `--json-schema`, `--agent` y `--session-id`.
  La primera línea del prompt hace que `task_binding.clave_declarada` devuelva la TaskKey.
  · rojo visto: sí
  · enmendado en §34.4: el agente ya no va por `--agent`; y la configuración adversarial falla antes
- **ME-E40** — `--allowedTools` es la unión de las herramientas de las capabilities de la unidad,
  intersecada con el `tools:` del agente, más `Skill` si la tiene. El schema llega intacto al Host a
  través de un shim `.cmd` en Windows: el Host falso lo recibe y lo parsea como JSON. El prompt llega
  por stdin. · rojo visto: sí
  · enmendado en §34.4: `--tools` y `--allowedTools` llevan el mismo conjunto mínimo
- **ME-E45** — Una corrida entera no cambia `.claude/runtime/tasks/<KEY>/state.json` ni
  `active-task.json`: el motor no reconcilia. Con el `state.json` ausente, la admisión da
  `DELEGATION_NOT_ALLOWED` y el `detail` dice cómo reconciliar. La admisión no necesita una sesión.
  · rojo visto: sí

### La configuración del motor

- **ME-E54** — `ejecucion.comandoHost`:
  - ausente, el motor usa lo que da `shutil.which("claude")`;
  - presente y válido, usa ese comando;
  - presente e inválido, el comando falla con exit 2 antes de crear la Execution.
    Inválido es una lista vacía, un texto suelto, un elemento vacío o un programa que no existe.

  Con la clave ausente y sin `claude` en el `PATH`, también falla antes de crear la Execution. En
  ningún caso de error queda carpeta, turno, temporal ni `result.json`, y la salida no es un
  ExecutionError. · rojo visto: sí
- **ME-E55** — `ejecucion.limiteSegundos`:
  - ausente, el límite es 1800;
  - un entero positivo, se usa;
  - `0`, `-5`, `"60"`, `true` o `1.5`, el comando falla con exit 2 antes de crear la Execution.

  Un `harness.config.json` que existe y no es un objeto JSON legible también falla antes, sin caer al
  default. En ningún caso de error queda nada escrito bajo `.claude/ejecuciones/`.
  · rojo visto: sí

### Instalación, alcance y documentos

- **ME-E26** — En un proyecto instalado con `install.ps1` en `%TEMP%`, sin cambios al instalador ni
  al manifiesto, `dev-harness.py ejecutar <KEY> --unidad <id>` con el Host falso configurado deja una
  Execution `SUCCEEDED` bajo `.claude/ejecuciones/`. · rojo visto: sí
- **ME-E46** — `contrato.py` no escribe, no lanza procesos y no importa ni la refutación ni la
  contabilidad; ningún módulo de `bin/ejecucion/` importa `contabilidad` ni lee
  `.claude/runtime/accounting`; los módulos que escriben lo hacen solo bajo `.claude/ejecuciones/`.
  · rojo visto: sí
- **ME-E47** — Nada de `bin/` ni de `comun/` importa `threading`, `multiprocessing`, `asyncio`,
  `concurrent`, `sched`, `queue`, un SDK de modelos ni LangGraph. `dev-harness.py` tiene trece
  subcomandos, con `ejecutar`. `claude` solo lo lanza `host_claude_code.py` (E-41 adaptado).
  · rojo visto: sí
- **ME-E48** — `docs/dominio/modelo-canonico.md` dice el invariante nuevo de `### Host`, no agrega
  conceptos, y `## El límite de la ejecución` pone el motor, la admisión, el almacenamiento y el Host
  Adapter en *Lo que existe ahora*. ADR-0015 existe, aceptado, con sus siete decisiones, y ADR-0013 y
  ADR-0014 no cambian. · rojo visto: sí
- **ME-E49** — Los archivos de Flow Governance, del plan 2.1, de los hooks, del registro de agentes,
  de la contabilidad, `install.ps1` y `manifest.json` son los de la base, sin archivos nuevos entre
  ellos. · rojo visto: sí
- **ME-E50** — Una corrida real de `ejecutar` contra Claude Code, sobre un proyecto de prueba con una
  unidad de backend, termina terminal y su `result.json` pasa `validar_resultado`. La lectura
  confirma:
  - que `structured_output` existe y lleva las dos claves;
  - que `--agent` aplica el `tools:` del agente junto con `--allowedTools`;
  - que el prompt por stdin llega;
  - que la sesión queda vinculada a la TaskKey;
  - qué `subtype` y código de salida da un error del proveedor.

  · rojo visto: no consta
  · verificación: lectura — el sujeto es una corrida de un modelo en el Host real, y la suite usa un
    Host falso
  · enmendado en §34.4: la lectura mira la estrategia de §34.3
- **ME-E51** — `Invoke-Tests.ps1` sale con 0, con los escenarios de esta Task y los de Task 3 que no
  reemplaza §26.2. · rojo visto: no consta

**En números:** 55 escenarios, 54 por la suite y 1 lectura.

## 29. Rojo visto previsto

**El Host falso** es un script de Python en `tests/fixtures/` que imita `claude -p
--output-format json`. Lee su guion de una variable del entorno del test y puede:

- devolver un `structured_output`;
- devolver un error de `subtype` dado;
- no devolver JSON;
- dormir para el timeout o la cancelación;
- morir por una señal;
- cambiar o commitear archivos;
- imprimir lo que recibió por argv y por stdin.

El motor lo encuentra por `ejecucion.comandoHost` de `harness.config.json` (MD-08, MD-22), así que no
hay monkeypatch del motor.

**Cómo se ve rojo.** Para cada escenario, una mutación sobre una copia del repo, que tiene que poner
en rojo una aserción del propio escenario, no una excepción:

| Escenario | Mutación | Aserción que tiene que fallar |
|---|---|---|
| ME-E01 | `output.fingerprint` sale de la huella del texto sin redactar; y, en otra corrida, `requestFingerprint` se calcula antes de redactar | la huella es la de los bytes de `output.md`; `requestFingerprint` es la del `request.json` en disco |
| ME-E02 | `PARTIAL` da `SUCCEEDED` | el estado es `FAILED` con `AGENT_DECLARED_NOT_COMPLETE` |
| ME-E03 | el adaptador acepta un `structured_output` con una clave de más | el código es `OUTPUT_INVALID` |
| ME-E04 | un `subtype` desconocido da `SUCCEEDED` | el código es `HOST_FAILURE` |
| ME-E05 | una señal externa da `CANCELLED` | el código es `HOST_INTERRUPTED` |
| ME-E06 | el motor no mira `cancelacion.json` | el estado es `CANCELLED` |
| ME-E07 | la condición 4 compara `plan_version` en vez de la huella | el código es `PLAN_CHANGED` |
| ME-E08 | la admisión al entregar no vuelve a leer el flujo | el código es `DELEGATION_NOT_ALLOWED` |
| ME-E09 | la compuerta se llama sin `requeridas` | el código es `NORMATIVE_GATE_BLOCKED` |
| ME-E10 | la condición 10 se saltea al entregar | el código es `AGENT_UNAVAILABLE` |
| ME-E11 | la condición 13 usa la disponibilidad guardada en el request | el código es `CAPABILITY_UNAVAILABLE` |
| ME-E12 | una dependencia `FAILED` cuenta como satisfecha | el código es `DEPENDENCY_NOT_SATISFIED` |
| ME-E13 | una `RUNNING` no cuenta como abierta | el código es `DUPLICATE_EXECUTION` |
| ME-E14 | después de un `SUCCEEDED` se acepta un turno nuevo | el código es `DUPLICATE_EXECUTION` |
| ME-E15 | un reintento reusa el `executionId` | los dos ids difieren |
| ME-E16 | una `CANCELLED` cuenta como abierta | se crea el turno 2 |
| ME-E17 | una `REJECTED` cuenta como abierta | se crea el turno 2 |
| ME-E18 | la reserva se escribe con `open("w")` en vez de exclusiva | una sola Execution y un solo turno |
| ME-E19 | la condición 15 al entregar no excluye a la propia | la Execution llega a `RUNNING` |
| ME-E20 | la recuperación no mira el candado | con el motor vivo, la Execution sigue `RUNNING` |
| ME-E21 | `escribir_una_vez` usa `os.replace` | el archivo existente no cambia |
| ME-E22 | el motor escribe `result.json` con `os.replace` | queda el primer resultado |
| ME-E23 | `ruta_canonica` acepta `./a` | `./a` no se persiste |
| ME-E24 | el `artifact` se guarda sin redactar; y, en otra corrida, la request se valida y se guarda antes de redactar | `output.md` no tiene el secreto; `request.json` no lo tiene y su huella es el `requestFingerprint` |
| ME-E25 | la atribución ignora lo sucio de antes | el estado es `CHANGES_UNATTRIBUTABLE` |
| ME-E26 | la copia no tiene `ejecucion/motor.py` | la Execution queda `SUCCEEDED` en el instalado |
| ME-E27 | se invierten las condiciones 9 y 13. *Ajuste de la construcción: la 7 y la 8 no pueden fallar a la vez —una unidad que no está no tiene estado—, así que invertirlas no se puede ver en rojo con una aserción* | sale el código de la anterior |
| ME-E28 | al entregar no se compara la huella de la unidad | el código es `CONTRACT_INVALID` |
| ME-E29 | el adaptador lee `result` cuando falta `structured_output` | el código es `OUTPUT_INVALID` |
| ME-E30 | se saca la condición de versión 2.1 | un 2.0 da `PLAN_NOT_READY` |
| ME-E31 | el límite no mata el árbol | el código es `TIMEOUT` y el Host terminó |
| ME-E32 | todo `is_error` es `PROVIDER_FAILURE` | sin identificación, el código es `HOST_FAILURE` |
| ME-E33 | sin catálogo, el output se escribe igual | no hay `output.md` |
| ME-E34 | la recuperación cierra una `REQUESTED` huérfana | la `REQUESTED` sigue abierta |
| ME-E35 | `--estado` corre la recuperación | ningún archivo cambia |
| ME-E36 | el id se valida con `match` y `$` | un id con `\n` final no se usa |
| ME-E37 | el barrido no mira el candado, solo la edad | con el candado tomado, la carpeta sigue |
| ME-E38 | el adaptador pasa `--model` aunque el perfil esté vacío | sin perfil no hay `--model` |
| ME-E39 | el adaptador agrega `--bare` | los argumentos no tienen `--bare` |
| ME-E40 | `--allowedTools` es el `tools:` entero del agente | la lista es la mínima |
| ME-E41 | `provee` devuelve verdadero para `jira.*` | el código es `CAPABILITY_UNAVAILABLE` |
| ME-E42 | el adaptador no busca el archivo del agente; y, en otra corrida, un Host que no carga el agente da `AGENT_UNAVAILABLE` | `REJECTED` con `AGENT_UNAVAILABLE` sin `entrega.json`; después de la entrega, `HOST_FAILURE` |
| ME-E43 | sin `git`, la evidencia dice `RESOLVED` | el estado es `CHANGES_UNRESOLVED` |
| ME-E44 | no se miran las otras `RUNNING` | el estado es `CHANGES_UNATTRIBUTABLE` |
| ME-E45 | la admisión llama a `reconciliar` | `state.json` no cambia |
| ME-E46 | `contrato.py` importa `subprocess` | la pureza de `contrato.py` |
| ME-E47 | `motor.py` importa `threading` | nada importa concurrencia |
| ME-E48 | el modelo canónico deja el motor en *Lo que todavía no existe* | el anclaje está en *Lo que existe ahora* |
| ME-E49 | se toca `flujo/estado.py` | es el de la base |
| ME-E50 | — | lectura |
| ME-E51 | — | no consta: es la compuerta |
| ME-E52 | el registro toma como Execution cualquier carpeta con `request.json`, aunque no tenga turno | el residuo no aparece en `--estado` y no bloquea la admisión nueva de la misma clave |
| ME-E53 | la recuperación ignora `cancelacion.json` y siempre escribe `HOST_INTERRUPTED` | la `RUNNING` huérfana con `cancelacion.json` termina `CANCELLED` |
| ME-E54 | con `comandoHost` inválido, el motor cae a `shutil.which("claude")` | el comando falla antes de crear la Execution, y no queda nada escrito |
| ME-E55 | un `limiteSegundos` inválido se reemplaza por 1800 | el comando falla antes de crear la Execution, y no queda nada escrito |

📌 **Contra los rojos falsos.** Antes de cada mutación se ve el escenario en verde; después se cuentan
solo sus aserciones, y una excepción no cuenta. Es la regla de la primera mutación de EX-E36b en
Task 3.

### 29.1 El rojo visto de la construcción

Corrido el 08-10-2026 sobre una copia de la fábrica, con el código final, por
`scratchpad/rojo72/mutar.py` de la sesión de construcción. Por cada mutación: el escenario en
verde en la copia; la mutación de la tabla de arriba; solo ese escenario; al menos una aserción
propia en rojo y ninguna excepción; la restauración, comprobada por huella contra el árbol de
trabajo; y el escenario en verde otra vez. **56 mutaciones sobre 53 escenarios: las 56 en rojo
propio, restauradas y verdes otra vez.** ME-E51 queda `no consta`, como dice la tabla: es la
compuerta. ME-E50 es una lectura.

| Escenario | Mutación | Aserciones propias en rojo | Una de ellas |
|---|---|---|---|
| ME-E01 | output.fingerprint sale de la huella del texto sin redactar | 1 | ME-E01 output.fingerprint es la huella de los bytes de output.md |
| ME-E01 | requestFingerprint se calcula antes de redactar | 13 | ME-E01 sale con 0 |
| ME-E02 | PARTIAL da SUCCEEDED | 3 | ME-E02 PARTIAL con AGENT_DECLARED_NOT_COMPLETE |
| ME-E03 | el adaptador acepta un structured_output con una clave de mas | 4 | ME-E03 una clave de mas da FAILED |
| ME-E04 | un subtype desconocido da SUCCEEDED | 4 | ME-E04 error_during_execution da FAILED |
| ME-E05 | una senal externa da CANCELLED | 2 | ME-E05 un Host terminado por una senal da FAILED |
| ME-E06 | el motor no mira cancelacion.json | 7 | ME-E06 el motor deja CANCELLED |
| ME-E07 | la condicion 4 compara plan_version en vez de la huella | 1 | ME-E07 con PLAN_CHANGED |
| ME-E08 | la admision al entregar no vuelve a leer el flujo | 6 | ME-E08 con el TaskContext cambiado: REJECTED |
| ME-E09 | la compuerta se llama sin requeridas | 4 | ME-E09 al pedir: NORMATIVE_GATE_BLOCKED |
| ME-E10 | la condicion 10 se saltea al entregar | 1 | ME-E10 con AGENT_UNAVAILABLE |
| ME-E11 | la condicion 13 usa la disponibilidad guardada en el request | 2 | ME-E11 REJECTED |
| ME-E12 | una dependencia FAILED cuenta como satisfecha | 1 | ME-E12 con la dependencia FAILED: DEPENDENCY_NOT_SATISFIED |
| ME-E13 | una RUNNING no cuenta como abierta | 2 | ME-E13 con una RUNNING: DUPLICATE_EXECUTION |
| ME-E14 | despues de un SUCCEEDED se acepta un turno nuevo | 3 | ME-E14 una request nueva: DUPLICATE_EXECUTION |
| ME-E15 | un reintento reusa el executionId | 2 | ME-E15 una request nueva crea el turno 2 |
| ME-E16 | una CANCELLED cuenta como abierta | 2 | ME-E16 una request nueva crea el turno 2 |
| ME-E17 | una REJECTED cuenta como abierta | 2 | ME-E17 una request nueva crea el turno 2 |
| ME-E18 | la reserva se escribe con open("w") en vez de exclusiva | 5 | ME-E18 exactamente una Execution |
| ME-E19 | la condicion 15 al entregar no excluye a la propia | 4 | ME-E19 paso la condicion 15 y llego a RUNNING: hay entrega.json |
| ME-E20 | la recuperacion no mira el candado | 2 | ME-E20 con el motor vivo la recuperacion no la toca |
| ME-E21 | escribir_una_vez usa os.replace | 10 | ME-E21 escribir otra vez request.json falla |
| ME-E22 | el motor escribe result.json con os.replace | 3 | ME-E22 el motor devuelve el primero |
| ME-E23 | ruta_canonica acepta ./a | 2 | ME-E23 ninguna ruta no canonica pasa |
| ME-E24 | el artifact se guarda sin redactar | 2 | ME-E24 output.md no tiene el secreto |
| ME-E24 | la request se valida y se guarda antes de redactar | 3 | ME-E24 request.json no tiene el secreto del requestedBy |
| ME-E25 | la atribucion ignora lo sucio de antes | 1 | ME-E25 el Host cambio uno que ya estaba sucio: CHANGES_UNATTRIBUTABLE con files vacio |
| ME-E26 | la copia no tiene ejecucion/motor.py | 5 | ME-E26 se instala bin\desarrollo\ejecucion\motor.py |
| ME-E27 | se invierten las condiciones 9 y 13 (ajuste documental: 7 y 8 no pueden fallar a la vez) | 1 | ME-E27 la compuerta normativa (9) y una capability (13): gana NORMATIVE_GATE_BLOCKED |
| ME-E28 | al entregar no se compara la huella de la unidad | 3 | ME-E28 una clave de mas en workUnit, con las huellas rehechas: REJECTED |
| ME-E29 | el adaptador lee result cuando falta structured_output | 3 | ME-E29 un result que dice COMPLETE sin structured_output da OUTPUT_INVALID |
| ME-E30 | se saca la condicion de version 2.1 | 1 | ME-E30 un plan 2.0 legible y READY da PLAN_NOT_READY |
| ME-E31 | el limite no mata el arbol | 2 | ME-E31 el Host termino |
| ME-E32 | todo is_error es PROVIDER_FAILURE | 1 | ME-E32 un is_error que no identifica al proveedor da HOST_FAILURE |
| ME-E33 | sin catalogo, el output se escribe igual | 1 | ME-E33 y no queda output.md |
| ME-E34 | la recuperacion cierra una REQUESTED huerfana | 4 | ME-E34 la recuperacion no la cierra |
| ME-E35 | --estado corre la recuperacion | 1 | ME-E35 --estado no escribe ningun archivo |
| ME-E36 | el id se valida con match y $ | 4 | ME-E36 el executionId con \n final no se usa como ruta |
| ME-E37 | el barrido no mira el candado, solo la edad | 1 | ME-E37 con el candado tomado no se barre, aunque tenga mas de 10 minutos |
| ME-E38 | el adaptador pasa --model aunque el perfil este vacio | 1 | ME-E38 sin perfil declarado (dos) no pasa --model |
| ME-E39 | el adaptador agrega --bare | 1 | ME-E39 nunca --bare ni saltear permisos |
| ME-E40 | --allowedTools es el tools: entero del agente | 4 | ME-E40 repository.read con Read,Glob,Grep,Edit,Write,Bash,Skill |
| ME-E41 | provee devuelve verdadero para jira.* | 3 | ME-E41 jira.issue.read termina REJECTED |
| ME-E42 | el adaptador no busca el archivo del agente | 6 | ME-E42 sin el archivo del agente: REJECTED con AGENT_UNAVAILABLE |
| ME-E42 | un Host que no carga el agente da AGENT_UNAVAILABLE | 3 | ME-E42 un Host que no carga el agente despues de la entrega: FAILED con HOST_FAILURE |
| ME-E43 | sin git, la evidencia dice RESOLVED | 1 | ME-E43 fuera de un repositorio: CHANGES_UNRESOLVED con files vacio |
| ME-E44 | no se miran las otras RUNNING | 1 | ME-E44 la evidencia es CHANGES_UNATTRIBUTABLE |
| ME-E45 | la admision llama a reconciliar | 3 | ME-E45 sin state.json: DELEGATION_NOT_ALLOWED |
| ME-E46 | contrato.py importa subprocess | 1 | ME-E46 contrato.py no lanza procesos ni importa la refutacion ni la contabilidad |
| ME-E47 | motor.py importa threading | 1 | ME-E47 nada importa concurrencia |
| ME-E48 | el modelo canonico deja el motor en Lo que todavia no existe | 4 | ME-E48 lo que existe ahora nombra motor |
| ME-E49 | se toca flujo/estado.py | 1 | ME-E49 harnesses/desarrollo/bin/flujo es el de fdca5ce |
| ME-E52 | el registro toma como Execution cualquier carpeta con request.json, aunque no tenga turno | 3 | ME-E52 ni cuenta como REQUESTED: la clave no tiene turnos |
| ME-E53 | la recuperacion ignora cancelacion.json y siempre escribe HOST_INTERRUPTED | 1 | ME-E53 la del pedido queda CANCELLED con CANCELLED |
| ME-E54 | con comandoHost invalido, el motor cae a shutil.which("claude") | 9 | ME-E54 una lista vacia: no queda nada bajo .claude/ejecuciones |
| ME-E55 | un limiteSegundos invalido se reemplaza por 1800 | 12 | ME-E55 limiteSegundos 0: no queda nada bajo .claude/ejecuciones |

## 30. Pendientes heredados

| Pendiente | De dónde | Clase | Qué pasa |
|---|---|---|---|
| P1, la política de reintento | T3 §32 | pasa a Task 5+ | Un reintento es manual (§15) |
| P2, scheduler y DAG | T3 | pasa a Task 5+ | — |
| P3, resolver aprobaciones | T3 | no afecta | Ya lo resolvió 0.31.0 (T3 §37.2, R-08) |
| P4, proyectar la evidencia | T3 | se mantiene pendiente | — |
| P5, eventos contables y `executionId` en la metadata | T3 D15 | se mantiene pendiente | MP-02, por el pedido de no bloquear |
| P6, la marca, la escritura atómica, la huérfana, la extensión | T3 | **se resuelve en Task 4** | MD-03, MD-05, MD-06, MD-07, MD-19 |
| P7, el Host Adapter | T3 | **se resuelve en Task 4** | MD-08, MD-09, MD-18 |
| P8, rechazar por un TaskContext viejo | T3 | no afecta | Lo hace el flujo (T3 §37.2, R-25): `DELEGATION_NOT_ALLOWED` |
| P9, checkpoints y reanudación | T3 | pasa a Task 5+ | No hay reanudación (MD-07) |
| P10, ejecutar por lote | T3 | pasa a Task 5+ | — |
| P11, el timeout | T3 | **se resuelve en Task 4** | `limiteSegundos`, 1800 s (MD-10) |
| P12, reusar resultados entre planes | T3 | pasa a Task 5+ | — |
| P13, el mecanismo de la reserva | T3 | **se resuelve en Task 4** | MD-04 |
| P14, cómo se obtiene el TaskFlowState vigente | T3 §37.11 | **se resuelve en Task 4** | MD-12 |
| EX-F01 | T3 §30 | **se resuelve en Task 4** | ME-E18 |
| EX-F02 | T3 §30 | **se resuelve en Task 4** | ME-E19 |
| El `\n` final de `$` | reverificación, hallazgo 6 | **se resuelve en Task 4**, para los ids que se vuelven rutas | MD-15. El validador de `contexto-armar.py` sigue igual: es de todos los contratos |
| La normalización de rutas | reverificación, hallazgo 7 | **se resuelve en Task 4**, para lo que el motor escribe | MD-16. `contrato.py` sigue igual |
| `workUnits.items` abierto | reverificación, hallazgo 10 | **se resuelve en Task 4**, en el motor | MD-11: la huella de la unidad contra el plan |
| La sesión ambigua | reverificación, hallazgo 11 | **se resuelve en Task 4** | MD-17, sin tocar `task_binding.py` |
| La compuerta normativa y `requeridas` | reverificación, hallazgo 1 | **se resuelve en Task 4** | MD-13 |
| `git remote -v` bajo carga | nota de 0.31.0 | se mantiene pendiente para el hook | La admisión usa 10 s (MD-12); el límite de 1,5 s del hook sigue |
| Fuerza de EX-E08 y EX-E36b | reverificación, hallazgo 5 | se mantiene pendiente | Son tests de Task 3. ME-E29 cubre la parte de esta Task |
| El texto de los agentes que dice que el resultado vuelve a `dev-orchestrator` | T3 §34.3.8, EC-13 | se mantiene pendiente | El prompt del adaptador nombra al receptor. Cambiar la prosa de siete agentes es otro cambio |
| El dueño de Execution y de sus schemas | T3 §34.3.10 | se mantiene pendiente | Es una decisión de la fábrica, en `CLAUDE.md`, con `harness-budget-auditor`. Propuesta: `harness-backend-engineer` |
| `ejecutar` y `presupuesto` como `UNRESOLVED_TOOL_CLASS` | ME-22; PENDIENTES-I | se mantiene pendiente | Una fila en `tool_policy._harness`, del `harness-hook-engineer` |
| `proceso.py` repite el algoritmo de `flujo/repositorio.py` | MD-14 | pasa a Task 5+ | Consolidarlo es del `harness-staff-engineer` |
| El mojibake del docstring de `test_e05` y la contradicción de la ModelTierApproval en MC | reverificación, hallazgos 2 y 3 | no afecta | Son de Task 3, y esperan la decisión de la persona |

**Decisiones diferidas nuevas:**

| # | Qué se difiere | Hasta | Qué queda estable |
|---|---|---|---|
| MP-01 | Un Job Object en Windows y la muerte del Host con su padre en POSIX | Cuando un caso real lo pida | La recuperación no mata por PID, y la evidencia dice `CHANGES_UNATTRIBUTABLE` (ME-20) |
| MP-02 | Los eventos `WORKUNIT_STARTED` y `WORKUNIT_COMPLETED`, y `executionId` en la metadata | La Task que conecte Execution con Observability | `host.sessionRef` es el `session_id` de la transcripción, y `contabilidad --ingerir --unidad --agente` ya atribuye |
| MP-03 | El presupuesto por corrida (`--max-budget-usd`) | Cuando la política de consumo lo pida | El tier decide el modelo; nada más gasta |

## 31. Plan de construcción

### 31.1 Qué se construye

| Artefacto | Qué hace | Escenarios |
|---|---|---|
| `bin/ejecucion/registro.py` (nuevo) | Rutas canónicas, escritura de una sola vez, turnos, candado de vida, estado derivado, residuos previos a la publicación y barrido | ME-E13 a ME-E23, ME-E34 a ME-E37, ME-E52 |
| `bin/ejecucion/admision.py` (nuevo) | La regla de 15, al pedir y al entregar, leyendo a cada dueño; el armado de la request en el orden de MD-23 | ME-E07 a ME-E12, ME-E24, ME-E27, ME-E28, ME-E30, ME-E41, ME-E42, ME-E45 |
| `bin/ejecucion/evidencia.py` (nuevo) | Las fotos y ExecutionEvidence | ME-E25, ME-E43, ME-E44 |
| `bin/ejecucion/proceso.py` (nuevo) | Lanzar con límite, matar el árbol | ME-E05, ME-E31 |
| `bin/ejecucion/host_claude_code.py` (nuevo) | El Host Adapter | ME-E01 a ME-E04, ME-E29, ME-E32, ME-E38 a ME-E40 |
| `bin/ejecucion/motor.py` (nuevo) | La orquestación, la configuración (MD-22), cancelar, recuperar, estado | ME-E01, ME-E05, ME-E06, ME-E20, ME-E24, ME-E33, ME-E53 a ME-E55 |
| `bin/dev-harness.py` | El subcomando `ejecutar` | ME-E26, ME-E47 |
| `docs/dominio/modelo-canonico.md` | §24 | ME-E48 |
| `docs/adr/0015-el-motor-minimo-de-ejecucion.md` (nuevo) | §25 | ME-E48 |
| `tests/casos/72_motor_de_ejecucion.py` (nuevo) | Los escenarios, cada uno con su id | todos menos ME-E26, ME-E50 y ME-E51 |
| `tests/casos/72-motor-de-ejecucion-instalador.ps1` (nuevo) | La instalación en `%TEMP%` | ME-E26 |
| `tests/fixtures/host_falso.py` (nuevo) | El Host falso | — |
| `tests/casos/64_modelo_de_dominio.py` y `65_contrato_de_ejecucion.py` | Las adaptaciones de §26.2, cada una con su comentario | — |
| `docs/cambios/minimal-execution-engine/lectura.md` (nuevo) | La lectura de ME-E50, firmada por una persona que no construyó (ADR-0009) | ME-E50 |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Lo que §30 deja pendiente y no está anotado | — |

### 31.2 Lo que no se toca

`contrato.py` y los dos schemas de Task 3; Flow Governance (`bin/flujo/`, `bin/estado_de_tarea/`);
`bin/orquestacion/` entero; `bin/contabilidad/`; los hooks y su política (`tool_policy.py`
incluido); los agentes y las skills; `install.ps1`; `manifest.json`, que no recibe las claves
`ejecucion.*` (MD-22); ADR-0013 y ADR-0014; `VERSION`, `CHANGELOG.md` y `UPGRADE.md`.

### 31.3 El orden

1. `registro.py`, con ME-E21, ME-E36 y ME-E18 primero: la escritura y la reserva sostienen todo lo
   demás.
2. `proceso.py` y `evidencia.py`.
3. `admision.py`.
4. El Host falso y `host_claude_code.py`.
5. `motor.py` y el subcomando.
6. Las adaptaciones de §26.2.
7. El modelo canónico y ADR-0015.
8. El instalador de prueba.
9. El rojo visto de cada escenario, con su registro en esta spec.
10. La compuerta entera en verde.
11. La lectura ME-E50, con una corrida real.

## 32. Criterio de cierre

El cambio cierra cuando:

- `harness-spec-refuter`, que no construyó, dictamina los 54 escenarios de la suite: todos
  `sostenido`;
- ME-E50 es `leído`, con un `lectura.md` firmado por una persona que no construyó. Es un solo
  escenario de lectura: ADR-0010 no aplica, y la firma no puede ser delegada;
- ningún escenario de Task 3 queda `contradicho`, salvo los que §26.2 reemplaza con su decisión;
- la compuerta sale con 0;
- `pre-tool-use.py` y `zonas.py` tienen el mismo hash antes y después;
- nada de lo de §31.2 cambió (ME-E49).

**Cierre parcial.** Con los 54 sostenidos y la lectura pendiente, el cambio **no** cierra: queda en
curso hasta la firma (R3).

## 33. Riesgos conocidos

### 33.1 Riesgos aceptados

Estos cuatro **no se resuelven en esta Task**, a propósito. No bloquean el motor mínimo, y cada uno
queda donde se lo puede seguir.

**R1. El Host puede sobrevivir al motor** (ME-20).

- La recuperación no mata procesos por PID, para no matar un proceso ajeno que reusó el número.
- Por eso puede quedar un Host vivo, escribiendo, mientras la Execution ya dice `FAILED` o
  `CANCELLED`.
- La evidencia de esa Execution queda `CHANGES_UNATTRIBUTABLE` si hubo cambios, y `--estado` avisa
  si el pid de `proceso.json` sigue vivo.
- El arreglo fuerte es MP-01 (§30). **Esta Task no agrega Job Objects ni un mecanismo equivalente.**

**R2. Una `REQUESTED` real huérfana bloquea su clave** (ME-07).

```text
turno + request.json
sin entrega.json
motor muerto
→ REQUESTED real
→ bloquea la idempotencyKey
→ no se reanuda
→ necesita una cancelación explícita (--cancelar)
```

Es raro, porque la ventana entre crear y entregar son segundos, pero no se resuelve solo. **No es el
caso de ME-E52:** una carpeta con `request.json` y **sin turno** no es una Execution, no bloquea nada
y la recuperación la barre (MD-04d). Lo que separa a los dos es el turno.

**R3. Lo no documentado del Host se confirma en ME-E50** (§8).

- El `subtype` de cada error, cómo se combinan `--agent` y `--allowedTools`, el prompt por stdin y el
  vínculo de la sesión pueden no ser como dice la documentación.
- El adaptador falla a `HOST_FAILURE` ante lo desconocido. **La suite con el Host falso no reemplaza
  la lectura:** prueba el motor contra lo que esta spec supone del Host, no al Host.
- ME-E50 es condición de cierre. **Hasta que esté `leído`, con la firma de una persona que no
  construyó, Task 4 no cierra** (§32).

**R4. `ejecutar` no tiene clasificación propia en la política de herramientas** (ME-22).

```text
ejecutar  →  UNRESOLVED_TOOL_CLASS
```

Esto vale mientras no exista una fila en `tool_policy._harness`. Desde una sesión interactiva de
Claude Code:
- pasa solo si la tarea puede avanzar;
- se niega si cualquier tarea espera una decisión humana.

La experiencia puede ser más restrictiva de lo necesario, pero **la semántica del motor no cambia**:
corrido desde una terminal, o con la tarea en condiciones, es el mismo motor. Esta Task no toca los
hooks, `tool_policy.py` ni Flow Governance. La fila queda en §30, del `harness-hook-engineer`.

### 33.2 Otros riesgos

- **`os.link` no anda en FAT y exFAT.** El motor no corre ahí, y lo dice.
- **El motor atribuye a la Execution lo que una persona edite a la vez en un archivo limpio.** El
  motor no lo puede ver (§16).
- **Ejecutar cuesta.** Cada `ejecutar` es una sesión del Host con su modelo, y esta Task no pone
  presupuesto por corrida (MP-03). El tier de la unidad, que ya pasó por el ConsumptionGate, decide
  el modelo.
- **La duplicación de `proceso.py`** con `flujo/repositorio.py` puede divergir. Mitigación: se cita el
  origen, y consolidarlo está en §30.
- **El JSON por argv a través de un shim `.cmd`** puede romperse con una versión nueva del shim.
  Mitigación: ME-E40 lo prueba a través de un `.cmd`, y el prompt nunca va por argv.

## 34. Enmienda post-refutación

**Fecha:** 09-10-2026. La refutación independiente ([`verificacion.md`](verificacion.md)) dio 51
sostenidos y 3 contradichos de la suite, ME-E50 contradicho contra el Claude Code real, y 3
invariantes contradichos. Lo que sigue **enmienda** la spec en esos puntos y en nada más. Las
secciones 1 a 33 quedan como se escribieron: son la historia de la decisión, y cada punto que esta
sección reemplaza lo dice abajo.

### 34.1 Qué contradijo la refutación

| Escenario o invariante | Qué se vio | Causa |
|---|---|---|
| **ME-E24**, ME-I17 | Un secreto que empieza después del carácter 166 de stderr llega a `detail` cortado y sin redactar. Sin catálogo, el nombre de una clave de más de un `structured_output` llega al `detail` de `OUTPUT_INVALID` | El adaptador recortaba stderr a 200 caracteres **antes** de redactar, y el pedazo ya no coincidía con el patrón. El mensaje de `validar_informe` llevaba texto del agente |
| **ME-E28**, ME-I06 | Un `request.json` editado a mano en `admission.*`, `requestedBy` o `createdAt` llega al Host y termina `SUCCEEDED` | Al entregar solo se comparaban la huella del plan y la de la unidad; el motor entregaba la request que tenía en memoria |
| **ME-E39**, ME-I23 | Con `ejecucion.comandoHost` válido para MD-22, el Host recibe `--bare`, `--dangerously-skip-permissions` o `--permission-mode bypassPermissions`; un perfil de `modelRouting.perfiles` se vuelve una bandera | La configuración aceptaba cualquier argumento, y `PROHIBIDOS` no lo usaba nadie |
| **ME-E50** | Claude Code 2.1.295, con los argumentos de MD-08, termina `success` **sin** `structured_output`: ninguna Execution real puede llegar a `SUCCEEDED`. Un error del proveedor llega con `subtype: "success"`, `api_error_status` y `terminal_reason: "api_error"`, sin `error.type`. `--allowedTools` no achica lo que ofrece `--agent` | §8 suponía que `--json-schema` suma `structured_output` con `--agent`: con `--agent`, el conjunto de herramientas es el `tools:` del agente, y `StructuredOutput` no está en él |

Y tres hallazgos no bloqueantes que esta enmienda también corrige, porque son del mismo código:
un JSON `success` con un código de salida distinto de 0 terminaba `SUCCEEDED`; el motor escribiría
`FAILED` con un código de admisión si un adaptador lo devolviera después de la entrega (ME-I29); y el
texto de §1, del modelo canónico y de ADR-0015 que ya no era cierto.

### 34.2 El discovery puntual del Host

Contra el Claude Code real, `2.1.295`, el 09-10-2026: el modelo `haiku`, un prompt chico por stdin, una
carpeta temporal, y el conjunto de herramientas leído del mensaje `init` de `--output-format
stream-json`. Costo total, USD 0,01.

| # | Argumentos, además de `-p --json-schema <AgentReport> --permission-mode dontAsk --permission-prompts none` | Herramientas de la sesión | `structured_output` |
|---|---|---|---|
| E1 | `--tools Read,Glob,Grep`, sin `--agent` | `Glob, Grep, Read, StructuredOutput` | Sí, pero `Read` negada: sin `--allowedTools`, `dontAsk` niega |
| E2 | `--tools Read,Glob,Grep --allowedTools Read,Glob,Grep` | `Glob, Grep, Read, StructuredOutput` | **Sí, `COMPLETE`, sin negativas** |
| E3 | `--agents <archivo> --agent probe`, con `tools: [Read, Glob, Grep]` | `Read, Glob, Grep` | **No**: es el hallazgo de ME-E50 |
| E4 | Lo mismo con `StructuredOutput` en el `tools:` del agente | `Read, Glob, Grep, StructuredOutput` | Sí |
| E5 | `--agent probe --tools Read,Glob,Grep,StructuredOutput` | `Read, Glob, Grep` | No: el `tools:` del agente gana sobre `--tools` |
| E6 | `--system-prompt-file <cuerpo del agente> --tools Read,Glob,Grep --allowedTools Read,Glob,Grep`, sin `--agent` | `Glob, Grep, Read, StructuredOutput` | **Sí, `COMPLETE`** |
| E7 | `--tools ""` | `StructuredOutput` | Sí: una unidad sin herramientas igual devuelve su informe |
| E8 | `--tools Read,Bash` en Windows | `Read, StructuredOutput` | Sí; `Bash` no está en la sesión de este Host (su shell es PowerShell) |
| E9 | Los argumentos de A, repetidos sobre una Execution real de la corrida exploratoria de ME-E50, en una cuenta con conectores de claude.ai | `Glob, Grep, Read, Skill, StructuredOutput` **y las ocho `mcp__claude_ai_Claude_Docs__*`** | Sí, `COMPLETE`, sin negativas |
| E10 | Lo mismo que E9 con `--strict-mcp-config` | `Glob, Grep, Read, Skill, StructuredOutput` | Sí; los hooks corren igual: la sesión quedó vinculada a la TaskKey |

**Lo que el Host hace, observado:** `--tools` decide qué herramientas propias existen en la sesión, y
el Host suma `StructuredOutput` cuando hay `--json-schema`; `--allowedTools` decide cuáles se usan sin
preguntar; `--agent` toma el conjunto del `tools:` del agente y no suma `StructuredOutput`. Las
herramientas MCP —los conectores de la cuenta, el `.mcp.json`— no las alcanza `--tools`: las saca
`--strict-mcp-config` sin `--mcp-config` (E9 y E10, también del 09-10-2026, USD 0,011).

**Las tres alternativas:**

| | Cómo | Juicio |
|---|---|---|
| **A** | Sin `--agent`: el cuerpo del agente como `--system-prompt-file`, y `--tools` y `--allowedTools` con el conjunto mínimo | **Se elige.** Salida estructurada real y el conjunto de herramientas exacto. Lo único nuevo que se escribe es el prompt de sistema, en el registro |
| B | Un agente generado por el adaptador con `--agents <archivo>`, con `StructuredOutput` en su `tools:` | Funciona (E4), pero escribe una definición de agente por corrida y depende de la precedencia entre el agente del CLI y el del proyecto, que no está documentada. Descartada |
| C | El agente escribe un AgentReport en un archivo | No hace falta: A funciona. Exigía darle al agente permiso de escribir donde no lo tiene |

Parsear `result` sigue prohibido (T3 D8): nada de esta enmienda lo hace.

### 34.3 Las decisiones nuevas

#### MD-08′. El Host Adapter materializa el agente sin `--agent` (reemplaza «Cómo se lanza» de §9)

```
claude -p
  --output-format json
  --json-schema <el schema del AgentReport>
  --session-id <uuid4 que genera el adaptador>
  --permission-mode dontAsk
  --permission-prompts none
  --system-prompt-file <prompt-de-sistema.md del registro de la Execution>
  --tools <herramientas de MD-18′>
  --allowedTools <las mismas>
  --strict-mcp-config
  [--model <perfil declarado para el tier>]
stdin = el prompt, cwd = la raíz del proyecto, stdout y stderr a temporales
```

- **El agente se materializa con su propio texto:** `resolver_agente` sigue exigiendo
  `.claude/agents/<assignedAgent>.md` con ese `name:`, y además su cuerpo. Es el mismo texto que
  `--agent` usaba como prompt de sistema; el modelo lo decide el perfil del tier o el Host, como
  antes: ningún agente ejecutable declara `model:`.
- **El prompt de sistema es un archivo más del registro** (MD-03): `prompt-de-sistema.md`, el cuerpo
  de `.claude/agents/<assignedAgent>.md` sin su frente, escrito una sola vez al entregar, en la
  carpeta de la Execution. Deja constancia de con qué texto corrió el agente, no deja nada fuera de
  `.claude/ejecuciones/` (ME-E46) y no queda suelto si el motor muere.
- **No se pasa `--agent`.** Sigue sin pasarse `--bare` ni nada que saltee permisos (ME-I23): los hooks
  del proyecto corren igual.

#### MD-09′. El AgentReport sigue saliendo solo de `structured_output`

Sin cambios de principio: el adaptador toma `declaredStatus` y `artifact` de `structured_output`, lo
valida con `contrato.validar_informe`, y no lee `result`. Lo que cambia es que ahora el Host lo
produce (E2, E6).

#### MD-10′. Errores del Host con la forma real

- **Un código de salida distinto de 0 nunca produce `SUCCEEDED`**, aunque el JSON diga `success` y
  traiga `structured_output` (ME-I32). Con un código distinto de 0:
  - si el resultado identifica al proveedor, `PROVIDER_FAILURE`;
  - si el código es 130, 143 o negativo, `HOST_INTERRUPTED`;
  - si no, `HOST_FAILURE`.
- **El proveedor se identifica** por `terminal_reason == "api_error"` o por un `api_error_status`
  numérico, con `is_error: true` o un código distinto de 0. Ya no por `error.type`, que el Host no
  emite.
- **Windows, terminado desde afuera:** `taskkill /F` deja el código 1, igual que una falla común, y no
  hay otra señal observable. El motor no adivina: es `HOST_FAILURE`. `HOST_INTERRUPTED` queda para
  130, 143, un código negativo (POSIX) y el Ctrl-C sobre el motor. Es un límite declarado (R7).
- **Después de la entrega, el motor solo acepta códigos de corrida.** Si un adaptador devolviera otro
  —un código de admisión como `AGENT_UNAVAILABLE` o `CAPABILITY_UNAVAILABLE`—, el motor lo trata como
  una violación del contrato del adaptador: `FAILED` con `ENGINE_FAILURE` (ME-I29 deja de depender del
  adaptador).

#### MD-18′. Las herramientas: `--tools` y `--allowedTools`, el mismo conjunto mínimo

- El conjunto es el de MD-18: la unión de las herramientas de las capabilities de la unidad,
  intersecada con el `tools:` del agente, más `Skill` si la tiene.
- **Va dos veces:** `--tools` hace que solo existan esas herramientas en la sesión, y `--allowedTools`
  que se usen sin preguntar. El Host suma `StructuredOutput`.
- **Sin MCP:** `--strict-mcp-config`, sin `--mcp-config`, saca las herramientas MCP que el Host
  ofrece por su cuenta (E9, E10). Ninguna capability de MD-18 es de MCP: las de integración el
  adaptador no las provee. Ahora sí, **el agente recibe solo lo que su unidad pide** (ME-I24).
- **`Bash` en Windows:** el Host la descarta en silencio, porque su shell es PowerShell (E8). Una
  unidad con `tests.run` se admite y su agente no tiene con qué correr los tests. Queda como riesgo
  (R5): la tabla de MD-18 no cambia en esta enmienda.

#### MD-19′. Todo texto del Host se redacta antes de recortarse

- **El orden:** texto del Host → redactar → recortar → usar. Nunca recortar primero.
- **Qué es texto del Host:** stderr entero, un `subtype` que el adaptador no conoce, `terminal_reason`,
  los campos `api_error*`, y todo mensaje de validación que cite el payload, como los de
  `validar_informe` sobre un `structured_output` inválido.
- **Qué es texto del motor:** el código, los `subtype` que el adaptador conoce por su nombre, el código
  de salida y las frases del propio motor.
- **El `detail`** es el texto del motor y, solo si hay catálogo, el texto del Host redactado; todo junto
  se redacta otra vez y se recorta a 300. **Sin catálogo, solo el texto del motor.**

#### MD-11′. Al entregar, la request persistida tiene que ser exactamente la que se escribió

La condición 1 al entregar suma una comprobación, la primera: **la huella del `request.json` en disco
tiene que ser la que el motor calculó al crearla** (MD-23). La huella es la de `contrato.huella`, de
la estructura y no de los bytes: reescribir el JSON con el mismo contenido no la cambia, y cambiar un
valor sí, sea de la WorkUnit, de `admission`, de `requestedBy`, de `createdAt` o de `plan`. Si
difiere, `REJECTED` con `CONTRACT_INVALID`, sin `entrega.json` y sin Host. Después, al Host se le
entrega la request del disco, ya probada igual.

**Lo que queda escrito después de una adulteración:** el `result.json` lleva el `requestFingerprint` de
lo que el motor escribió, que es la verdad de esa Execution. Leído contra el `request.json`
adulterado, ya no coincide: la Execution queda **ilegible** (§14), cuenta como abierta, y la clave solo
se destraba replanificando. No se reescribe la request, no se borra la Execution y no se falsifica
ninguna huella. Es un riesgo declarado (R6).

#### MD-22′. La configuración no puede tocar lo que arma el adaptador

- **`ejecucion.comandoHost`** es el programa y, después, argumentos neutrales para lanzarlo. Se
  rechaza, antes de crear la Execution y con exit 2:
  - un argumento que sea, o empiece con, una opción del adaptador o de seguridad: `--print`,
    `--agent`, `--agents`, `--output-format`, `--json-schema`, `--session-id`, `--tools`,
    `--allowedTools`, `--allowed-tools`, `--disallowedTools`, `--disallowed-tools`,
    `--permission-mode`, `--permission-prompts`, `--model`, `--system-prompt`,
    `--system-prompt-file`, `--append-system-prompt`, `--append-system-prompt-file`, `--settings`,
    `--setting-sources`, `--mcp-config`, `--strict-mcp-config`, `--bare`,
    `--dangerously-skip-permissions` o `--allow-dangerously-skip-permissions`, también como
    `--opcion=valor` y sin distinguir mayúsculas;
  - un argumento que contenga `dangerously` o `bypasspermissions`, sin distinguir mayúsculas;
  - una opción corta (un `-` y letras): el adaptador no puede saber si combina `-p`;
  - un programa que empiece con `-`.
- **`modelRouting.perfiles[<tier>]`** es un nombre de modelo. Vacío, en blanco o `null` es «no
  declarado», como antes. Un texto declarado tiene que ser un nombre conservador: empieza con letra o
  dígito, sigue con letras, dígitos y `. _ : @ / [ ] -`, sin espacios, hasta 128 caracteres. Otra cosa
  —un `-` al principio, un espacio, un no texto— es un error de configuración, antes de crear la
  Execution. No hay una lista cerrada de modelos.

### 34.4 Escenarios enmendados y nuevos

Los 55 de §28 conservan su número; estos textos **reemplazan** a los de §28 para los escenarios que se
nombran, y la nota debajo de cada uno en §28 remite acá.

**ME-E24, fortalecido.** Lo de §28, y además: un secreto que empieza después de más de 166
caracteres de stderr no llega a `detail`; un secreto como nombre de una clave de más, o como valor de
`declaredStatus`, de un `structured_output` inválido, tampoco, con catálogo o sin él. Sin catálogo, el
`detail` de ese `OUTPUT_INVALID` es solo texto del motor.

**ME-E28, fortalecido.** Un `request.json` cambiado entre la creación y la entrega, en
`requestedBy`, `createdAt`, `admission.normativeGate`, `admission.agent.validation`,
`admission.agent.type`, `admission.agent.domain`, `admission.capabilities`,
`admission.dependencies`, `workUnit` o `plan`, termina `REJECTED` con `CONTRACT_INVALID`, sin
`entrega.json` y sin Host, y su `result.json` lleva el `requestFingerprint` de lo que el motor
escribió. Reescrito con el mismo contenido, se entrega.

**ME-E32, enmendado.** Un Host que termina con `is_error: true` y `api_error_status`, o con
`terminal_reason: "api_error"`, da `PROVIDER_FAILURE`, también con `subtype: "success"` y código de
salida 1. Uno con `is_error: true` sin esas marcas da `HOST_FAILURE`.

**ME-E39, enmendado.** Los argumentos con que el adaptador lanza el Host nunca tienen `--bare`,
`--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions`, `bypassPermissions` ni
`--agent`, y siempre tienen `-p`, `--output-format json`, `--json-schema`, `--session-id`,
`--permission-mode dontAsk`, `--permission-prompts none`, `--system-prompt-file` con el cuerpo del
agente, `--tools`, `--allowedTools` y `--strict-mcp-config`. Una configuración que intente meter una
de esas banderas por `comandoHost` (`--bare`, `--dangerously-skip-permissions`, `--permission-mode
bypassPermissions`, `--allowedTools`, `--agent`, `--model=x`, `-p`, `--mcp-config`, en cualquier
combinación de mayúsculas) o por un perfil
de modelo (`--dangerously-skip-permissions`, `--model`) falla con exit 2 antes de crear la Execution.
La primera línea del prompt hace que `task_binding.clave_declarada` devuelva la TaskKey.

**ME-E40, enmendado.** `--tools` y `--allowedTools` llevan el mismo conjunto: la unión de las
herramientas de las capabilities de la unidad, intersecada con el `tools:` del agente, más `Skill` si
la tiene. El schema llega intacto al Host a través de un shim `.cmd` en Windows, y el prompt por
stdin.

**ME-E50, enmendado.** Una corrida real de `ejecutar` contra Claude Code, con la estrategia de §34.3,
sobre un proyecto de prueba con unidades de backend y de calidad. La lectura confirma: que el prompt llega por
stdin; que el agente se materializa con su prompt; que el AgentReport llega en `structured_output`, con
`declaredStatus` y `artifact`; que la sesión ofrece solo las herramientas de la unidad y
`StructuredOutput`; que la sesión queda vinculada a la TaskKey; que `session_id` es `host.sessionRef`;
qué `subtype`, código de salida, `terminal_reason` y `api_error_status` da un error real del
proveedor, y que el motor lo lleva a `PROVIDER_FAILURE`; una Execution `SUCCEEDED` con `COMPLETE`, y
una `FAILED` con `AGENT_DECLARED_NOT_COMPLETE` si se puede provocar; y que cada `result.json` pasa
`validar_resultado`. · verificación: lectura — el sujeto es una corrida de un modelo en el Host real

- **ME-E56** — Un Host que termina con un código de salida distinto de 0 nunca deja `SUCCEEDED`, aunque
  su JSON diga `success` y traiga un `structured_output` `COMPLETE`: con 1 da `HOST_FAILURE`; con 143,
  `HOST_INTERRUPTED`; con 1 y `api_error_status`, `PROVIDER_FAILURE`. · rojo visto: sí
- **ME-E57** — Si un Host Adapter devuelve después de la entrega un código que no es de corrida
  (`AGENT_UNAVAILABLE` o `CAPABILITY_UNAVAILABLE`), el motor deja `FAILED` con `ENGINE_FAILURE`, nunca
  ese código. · rojo visto: sí

**ME-I32.** Un código de salida del Host distinto de 0 nunca produce `SUCCEEDED`. Se observa en el
adaptador (MD-10′) y en ME-E56.

**En números:** 57 escenarios, 56 por la suite y 1 lectura; 32 invariantes.

### 34.5 Rojo visto de la enmienda

| Escenario | Mutación | Aserción que tiene que fallar |
|---|---|---|
| ME-E24 | el adaptador recorta stderr antes de devolverlo | el `detail` no lleva el secreto que empieza después del corte |
| ME-E24 | el motor recorta el texto del Host antes de redactarlo | lo mismo |
| ME-E24 | el mensaje de `validar_informe` vuelve al texto del motor | el `detail` sin catálogo no lleva la clave del agente |
| ME-E28 | al entregar no se compara la huella del `request.json` con la de creación | cada campo adulterado da `CONTRACT_INVALID` |
| ME-E32 | el adaptador vuelve a mirar solo `error.type` | la forma real da `PROVIDER_FAILURE` |
| ME-E39 | la configuración no rechaza las banderas reservadas | cada configuración adversarial falla antes de crear la Execution |
| ME-E39 | el adaptador vuelve a pasar `--agent` | los argumentos no tienen `--agent` |
| ME-E39 | el adaptador no pasa `--strict-mcp-config` | los argumentos lo tienen |
| ME-E40 | `--tools` lleva el `tools:` entero del agente | `--tools` es el conjunto mínimo |
| ME-E56 | un JSON `success` con código distinto de 0 da `SUCCEEDED` | con 1, `HOST_FAILURE` |
| ME-E57 | el motor escribe el código que devuelve el adaptador | el código es `ENGINE_FAILURE` |

El registro de lo corrido va en §34.7.

### 34.6 Lo que no cambia

Los turnos de intento, el punto de publicación, la escritura de una sola vez, la idempotencia, el
candado de vida, la recuperación, la `REQUESTED` huérfana, la cancelación durable, Flow Governance,
la compuerta normativa, la evidencia, las rutas, el reintento manual, una WorkUnit por invocación, el
CLI y el contrato de Task 3: `execution-request/1.0`, `execution-result/1.0`, `contrato.py` y el
AgentReport no cambian, porque el problema estaba en el Host Adapter y no en el contrato.

**Riesgos nuevos o actualizados:**

- **R3** se achicó: lo no documentado del Host se observó (§34.2) y la estrategia cambió. Sigue
  abierto hasta que una persona que no construyó firme la lectura de ME-E50.
- **R5.** `Bash` no existe en la sesión del Host en Windows; una unidad con `tests.run` corre sin ella.
- **R6.** Una request adulterada deja su Execution ilegible y bloquea la clave hasta replanificar.
- **R7.** En Windows, un Host terminado desde afuera es `HOST_FAILURE`: no hay una señal que lo
  distinga de una falla.

### 34.7 Rojo visto de la enmienda, corrido

El 09-10-2026, sobre una copia de la fábrica en `%TEMP%` con el código final, cada mutación de §34.5
por separado: el escenario en verde; la mutación; solo ese escenario, con al menos una aserción propia
en rojo y ninguna excepción; restaurar, comparado por huella contra el árbol de trabajo; y verde otra
vez. **Once mutaciones, siete escenarios, once rojos.** 260 s.

| Escenario | Mutación | Aserciones propias en rojo | Una de ellas |
|---|---|---|---|
| ME-E24 | el adaptador recorta stderr a 200 antes de devolverlo | 1 | `ni un pedazo del secreto despues del corte llega al detail` |
| ME-E24 | el motor recorta el texto del Host antes de redactarlo | 1 | la misma |
| ME-E24 | el mensaje de `validar_informe` vuelve al texto del motor | 2 | `un secreto como clave de mas, sin catalogo: el detail no lo lleva` |
| ME-E28 | al entregar no se compara la huella del `request.json` | 18 | `requestedBy cambiado: REJECTED con CONTRACT_INVALID` |
| ME-E32 | el adaptador vuelve a mirar solo `error.type` | 2 | `la forma real del Host, con codigo 1 da PROVIDER_FAILURE` |
| ME-E39 | la configuración no rechaza las banderas reservadas ni un perfil que es una bandera | 24 | `comandoHost con --bare: sale con 2` |
| ME-E39 | el adaptador vuelve a pasar `--agent` | 1 | `nunca --bare, saltear permisos ni --agent` |
| ME-E39 | el adaptador no pasa `--strict-mcp-config` | 1 | `tiene --strict-mcp-config` |
| ME-E40 | `--tools` lleva el `tools:` entero del agente | 5 | `repository.read con Read,Glob,Grep,Edit,Write,Bash,Skill` |
| ME-E56 | un JSON `success` con código distinto de 0 da `SUCCEEDED` | 6 | `success con codigo 1: FAILED con HOST_FAILURE` |
| ME-E57 | el motor escribe el código que devuelve el adaptador | 2 | `un adaptador que devuelve AGENT_UNAVAILABLE despues de la entrega: FAILED con ENGINE_FAILURE` |

- **ME-E24, la aserción del corte:** el marcador de la redacción deja ver los primeros 12 caracteres
  del secreto, así que el test busca 13. Con 16, la mutación del motor —que deja 15— pasaba en
  verde: se vio al preparar esta tabla, y el test se ajustó antes de correrla.
- **ME-E28:** las adulteraciones de `workUnit` y `plan` siguen en verde con la mutación, porque las
  agarran las comprobaciones de antes (la huella de la unidad y la del plan); las de `requestedBy`,
  `createdAt` y `admission.*` solo las agarra la de §34.3.
- Las marcas de ME-E24, ME-E28, ME-E32, ME-E39 y ME-E40 en §28 quedan `sí`: la de antes era de su texto
  original, y esta es la del texto enmendado. ME-E56 y ME-E57 pasan a `sí`.
