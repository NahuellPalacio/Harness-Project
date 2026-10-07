---
estado: aceptada
creado: 2026-10-03
---

# ADR-0013 — El modelo de dominio canónico

## Contexto

HARNESS creció en 29 versiones, cambio por cambio, y cada cambio nombró lo que necesitaba. En 0.29.0
el dominio existía, pero no estaba escrito en ningún lado:

- **la misma palabra nombraba cosas distintas**: `check` tenía cuatro sentidos, `policy` cinco y
  `source` siete;
- **el plan declaraba once estados y el código escribía tres**, y los demás hablaban de delegar y de
  ejecutar, cosas que no existen;
- **en el ledger de la Context Bar, `taskId` era el id de la sesión de Claude Code.**

El relevamiento completo está en `docs/cambios/canonical-domain-model/spec.md`, con las
contradicciones entre schemas, código y documentación enumeradas en su sección 17. El modelo que salió de ahí está en
`docs/dominio/modelo-canonico.md`.

## Decisión

### 1. Nueve contextos delimitados

HARNESS tiene nueve contextos:

- Work Intake
- Project Knowledge
- Normative Sources
- Planning
- Catalog
- Governance
- Guardrails
- Observability
- Host Integration

Cada uno se justifica por su lenguaje, sus invariantes, su dueño, sus datos y su ciclo de vida.
Governance no se parte en normativa, refutación y seguridad: comparten la `ruleKey`, los registros y
el dueño. El ciclo entre Planning y Governance se acepta y se nombra: el Plan lleva la resolución
normativa de cada WorkUnit, porque la refutación la necesita unidad por unidad.

### 2. La Task es externa, y su identidad es la TaskKey

HARNESS no tiene ni el estado ni el ciclo de vida de una Task: los tiene Jira. Lo que HARNESS guarda
de una Task son snapshots y documentos derivados, todos nombrados por su TaskKey. No hay un agregado
`Task`, y el issue de Jira no es una entidad de dominio: es un TaskRecord externo, que se lee por la
Integration de Jira.

### 3. El Host no es dominio

Claude Code es el Host: corre los hooks, dibuja la UI, ejecuta agentes y skills, da las
herramientas, escribe la transcripción y da acceso al modelo. No es un concepto de dominio. Por
dónde se filtra a los contratos (`CLAUDE_CODE_STATUSLINE`, el bloque `contextBar`, el `session_id`
como clave de ledger) queda nombrado. No se rompe en esta decisión.

### 4. Execution es un límite reservado, no un contexto

En 0.29.0 nada toma una WorkUnit y la lleva a cabo. Execution no tiene lenguaje, ni datos, ni
invariantes, ni ciclo de vida, ni implementación. Está nombrado y vacío: ningún concepto lo tiene
como contexto. Dos invariantes valen hoy y solo se rompen con una decisión escrita:

- la contabilidad no es estado de ejecución;
- el estado del Plan se deriva del contenido del Plan.

### 5. "Check" son tres conceptos

| Nombre canónico | Qué es |
|---|---|
| **GuardrailCheck** | El check del hook: `verificar(evento, proyecto, config) -> [str]` en PostToolUse. Avisa y nunca bloquea |
| **ControlCheck** | El Control de tipo CHECK: `evaluar(...)` devuelve un estado y su evidencia |
| **CheckSpecification** | El `.md` que describe un ControlCheck. No se ejecuta |

Los tests de `tests/casos/` no son ninguno de los tres. Los campos de contrato no cambian de nombre:
`requiredChecks` nombra GuardrailCheck, y `declaredChecks` lleva los checks que declara la norma,
estén registrados o no, y nunca un GuardrailCheck. Solo un ControlCheck registrado e instalado puede
cerrar una unidad de refutación.

### 6. Qué promete `schema_version`

`schema_version` promete **todo documento que el schema declara válido**, no solo los que produce
HARNESS. Es el criterio que el repo ya había escrito al subir `project-context/1.1`: la
compatibilidad se juzga sobre "todo documento v1.0 válido", y un documento ajeno pide "una
migración, no un `enum` más flojo" (`docs/cambios/interfaces-identidad-ambientes/spec.md`).

Por eso, achicar el enum de estados de `orchestration-plan` es un cambio de versión mayor, y el
contrato pasa a `orchestration-plan/2.0`. La compatibilidad tiene tres caras:

- **del productor:** `plan` escribe solo 2.0;
- **del consumidor:** `refute --compile` y `--replanificar` leen un plan guardado por una sola regla.
  Aceptan un 2.0, o un 1.0 cuyos estados existen en 2.0, y rechazan cualquier otra versión;
- **del documento guardado:** un 1.0 compatible se migra la próxima vez que se escribe. Un 1.0 con un
  estado que no existe en 2.0, como `DELEGATING` o `READY`, se rechaza y no se migra: no hay un estado
  2.0 que signifique eso, y la salida es regenerarlo.

## Consecuencias

A favor:

- El dominio queda escrito una vez, y cada nombre del código apunta a un nombre canónico.
- El próximo cambio, el de la ejecución, encuentra el límite vacío y con nombre, en vez de estados
  que nadie diseñó.
- La versión de un contrato vuelve a decir algo: quien lee un `1.0` sabe qué esperar.

En contra, y dicho:

- **`orchestration-plan` rompe su contrato.** Un lector externo que exija `1.0` en un plan nuevo deja
  de encontrarlo, y un plan editado a mano con un estado eliminado deja de poder leerse.
- **Los nombres canónicos están en inglés y el código sigue en español.** No se renombra nada:
  cuesta nombres persistidos, huellas, hashes y tests. Quien lee necesita el mapa del vocabulario.
- **El documento canónico puede desviarse del código.** Los tests miden su forma y su cobertura, no
  la verdad de cada definición.

## Revisión

Se revisa cuando la Task de ejecución defina dónde vive el estado de una ejecución. Esa Task puede
romper los dos invariantes del punto 4, pero con su propia decisión escrita. También se revisa si
aparece un contexto que no quepa en los nueve, o si un concepto cambia de contexto. Lo que no se
revisa por eso solo es que la Task sea externa: mientras Jira sea el registro de las tareas, HARNESS
no les inventa un ciclo de vida.
