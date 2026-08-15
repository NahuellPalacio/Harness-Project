# gentle-ai — lectura

**Repo:** https://github.com/Gentleman-Programming/gentle-ai
**Commit:** `07f75262ad5f6438a8ecae8cfe0334e5d3db2689` · **Licencia:** MIT
**Leído el:** 2026-08-10

## Qué es

Un **configurador de ecosistema** escrito en Go (42 MB): equipa el agente que ya tenés
—Claude Code, Codex, Cursor, OpenCode y una decena más— con memoria persistente,
Spec-Driven Development, skills, servidores MCP, ruteo de modelos, persona y revisión
nativa acotada. 5.566 estrellas, muy activo, 704 issues abiertos.

## Por qué NO se instala el binario

| Motivo | Detalle |
|---|---|
| **Colisión de dueño** | Es un configurador de agentes, igual que nuestro harness. Los dos escriben en `.claude/settings.json`. Nuestro `-Update` lo regenera entero, así que pisaría lo que gentle-ai ponga. Dos configuradores no pueden ser dueños del mismo archivo |
| **Sin binario en Windows** | El propio proyecto retiene la distribución binaria *"held for public-trust Authenticode signing"*, y Scoop está caído. Solo queda compilar desde fuente |
| **Runtime nuevo** | Exige Go 1.25.10+, que no está instalado. Go **no figura** en la tabla de versiones homologadas de ES0901 |
| **Sin desinstalación** | La palabra `uninstall` no aparece en el README. Para algo que escribe en el config global de tus agentes, es el dato que más pesa |
| **Memoria duplicada** | Trae su propia memoria persistente (Engram), que convive mal con el `CLAUDE.md` de zonas y `docs/conocimiento/` que decidimos en ADR-0003 |

Decisión: **se toman ideas, no el binario.** Es exactamente el caso que ADR-0005 previó.

## Revisión de seguridad del material leído

Los cuatro archivos se leyeron enteros. Ninguno intenta cambiar el rol del modelo, ni pide
leer fuera del proyecto, ni ejecuta nada, ni contiene URLs de exfiltración ni credenciales.
Son prompts de agente bien acotados. **Limpio.**

Detalle a resolver al adaptar: `{{CLAUDE_MODEL}}` y `{{CLAUDE_EFFORT_FRONTMATTER}}` son
plantillas que su binario reemplaza en tiempo de instalación.

## Lo que sirve

### 1. `review-refuter.md` — el revisor independiente que nos falta

Un refutador **desacoplado y sin herramientas de escritura** que evalúa un lote de hallazgos
y devuelve un veredicto por cada uno. Tres decisiones que mejoran lo que teníamos pensado:

- **No puede arreglar ni agregar hallazgos.** *"Never edit, fix, delegate, or add findings."*
  Nosotros habíamos pensado "sin Write"; esto es más fuerte: tampoco puede ampliar el alcance.
- **Tres veredictos, no dos**: `corroborated`, `refuted`, `inconclusive`.
- **El default seguro está elegido a propósito**: *"Missing or malformed evidence is
  `inconclusive`; never imply corroboration."*

📌 **Traducción directa a nuestro problema:** para una historia de usuario, `inconclusive`
**es** "va a definiciones pendientes". La ley de no inventar ya tenía este contrato adentro
y no lo habíamos formalizado.

### 2. `review-risk.md` — presupuestos y umbrales de una revisión

Es un revisor de seguridad, pero lo valioso es el contrato que trae alrededor:

- **Precision gate:** *"When in doubt, stay silent: a missed nitpick costs nothing; a false
  positive costs a full fix cycle."* Es el mismo principio al que llegamos con los secretos,
  por otro camino. Que dos diseños independientes converjan ahí es buena señal.
- **Sweep budget:** una pasada exhaustiva por lente y para. *"There is no loop-until-dry
  mechanism."* Presupuesto de esfuerzo explícito.
- **Severity floor:** solo lo grave entra al ciclo de corrección; lo menor se reporta una vez
  con estado `info`, **nunca se re-revisa y nunca bloquea**. Es nuestro "avisa siempre,
  bloquea solo secretos" con más granularidad.
- **Techo estructural de refutación:** *"NEVER spawn one refuter task per candidate"* — el
  techo es por revisión, no por hallazgo, tenga 2 candidatos o 20.
- **Ledger con esquema fijo** (`id`, `lens`, `location`, `severity`, `status`) y una regla
  que vale la pena robar: *"If the first pass finds nothing, persist an empty ledger record
  rather than skip persistence."* Registrar el vacío también es un dato.
- **Convergence budget:** máximo 2 rondas de corrección. *"The loop never extends."*
- **Defaults invertidos según qué es más caro:** un veredicto de refutación ausente o
  malformado deja el hallazgo `stands`; evidencia ausente en el refutador es `inconclusive`.

### 3. `skill-resolver.md` — el ruteo de skills que tenemos pendiente

Nuestro hook `UserPromptSubmit` está escrito y calla porque todavía no hay a qué rutear.
Este documento resuelve el problema completo:

- El registro es un **índice** —nombre, disparadores, alcance y ruta exacta— no un bundle de
  reglas comprimidas.
- **Se pasan rutas, no resúmenes.** *"`SKILL.md` is the runtime contract and source of
  truth."* Un resumen generado degrada la skill; una ruta no.
- El subagente **reporta cómo resolvió**: `paths-injected`, `fallback-registry`,
  `fallback-path` o `none`. Si no fue `paths-injected`, el orquestador re-lee el registro.

📌 **Esto arregla algo que ya nos pasó.** Nuestro agente `ige-hu` tiene un "Paso 0" con
respaldo por ruta absoluta, y el vault registra el porqué: *"una falla silenciosa deja al
agente trabajando sin guía"*. El reporte de resolución es lo que convierte esa falla
silenciosa en visible.

### 4. `_shared/SKILL.md` — paquetes de soporte que no son skills

Frontmatter con `disable-model-invocation: true` y `user-invocable: false`: material
compartido entre skills que el modelo no puede invocar como si fuera una skill. Además
declaran `license` y `metadata.author` en el frontmatter, que es justo lo que ADR-0005 pide
para trazabilidad.

## Lo que NO sirve

- Todo lo atado a su ecosistema: `mem_search` / `mem_get_observation` (Engram),
  `.atl/skill-registry.md`, `gentle-ai skill-registry refresh`, `openspec`.
- El modelo de cuatro severidades (`BLOCKER`/`CRITICAL`/`WARNING`/`SUGGESTION`) tal cual.
  Nuestro harness avisa o bloquea, y el bloqueo es solo para secretos: cuatro niveles serían
  precisión que no usamos.
- SDD y RDD completos. Son una metodología de trabajo entera; adoptarla es una decisión
  mucho más grande que este harness, y no es la que estamos tomando.

  ⚠️ **Parcialmente superado por [ADR-0006](../../docs/adr/0006-sdd-como-metodo-de-los-proyectos.md)
  (2026-08-12).** Lo escrito acá sigue vigente para el *paquete*: las ocho fases, el
  orquestador, el contrato de estado, Engram y OpenSpec siguen afuera, y no se tomó una línea
  de su implementación. Lo que cambió es que el **método** se adoptó por separado, escrito de
  cero contra las restricciones de este harness. La regla que dejó ese ADR es justamente la
  distinción: adoptar un método no es adoptar el paquete que lo trae.
- Los revisores por lente de código (`readability`, `reliability`, `resilience`). Sirven para
  el harness `desarrollo` cuando exista; hoy no hay código que revisar.

## Estado — qué se adaptó

| Nuestro | De | Qué cambió al adaptarlo |
|---|---|---|
| `harnesses/analisis/agents/hu-refutador.md` | `review-refuter.md` + `review-risk.md` | El objeto verificado no es un diff sino una historia contra su maqueta. Los veredictos pasan a `sostenido` / `contradicho` / `sin-sustento`. **El cambio de fondo: `sin-sustento` no es un descarte, es el entregable más valioso** — cada uno es una definición que nadie tomó y que alguien iba a inventar |
| `harnesses/analisis/agents/hu-redactor.md` | `skill-resolver.md` | Se toma el reporte de resolución de skill (`skill-invocada` / `leida-por-ruta` / `no-encontrada` / `sin-cargar`). Se descarta el registro en Engram: acá la skill se resuelve por ruta relativa al proyecto, que el instalador garantiza |

Pendiente de adaptar, cuando haya a qué aplicarlo:

- **El registro de skills como índice** y el ruteo desde `UserPromptSubmit`. Hoy hay una sola
  skill instalada; el registro se justifica a partir de tres o cuatro.
- **Sweep budget y severity floor** para el harness `desarrollo`, cuando existan sus checks.
- **`disable-model-invocation` / `user-invocable: false`** para material compartido entre
  skills, cuando haya más de una que comparta algo.
