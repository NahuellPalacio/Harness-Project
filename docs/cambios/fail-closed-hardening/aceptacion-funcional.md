# Aceptación funcional — Flow Governance, Wave 5

**Fecha:** 02-10-2026 · **Baseline:** `VERSION 0.26.0`, HEAD `2c33fba41cb13bb59c888377466b619cb70f42d1`,
con la Wave 5 sin commitear · **Resultado:** PASS en todo lo que sigue

Esta aceptación no es la verificación de ADR-0006, que está en [verificacion.md](verificacion.md).
Junta cuatro clases de evidencia y no las mezcla:

- **Manual:** lo que observó la persona, en proyectos instalados con `install.ps1` en el Escritorio.
- **Automática:** la suite.
- **Del refutador:** `harness-spec-refuter`, con sus corridas y sus sondas propias.
- **De quien construyó, sin la UI:** la CLI instalada, sobre copias de los fixtures, y una
  comparación contra la línea de base. No es de la persona.

Ningún token real: los `.env` de los fixtures tienen valores y hosts sintéticos.

## Resumen

| Qué | Resultado | Evidencia |
|---|---|---|
| Capacidades soportadas y no disponibles (manual) | PASS | manual |
| Bloque 4 sin resolver (manual) | PASS | manual |
| Ruteo a `dev-tool-builder` | PASS | manual, automática y del refutador |
| Reporte de seguridad, fallar cerrado | PASS | automática y del refutador |
| Frescura del conocimiento | PASS | automática y del refutador |
| Presentación del Bloque 4 | PASS | manual, automática y del refutador |
| E-22 | RATIFICADO | decisión de la persona |
| Los cinco estados de integración, sin `NOT_REQUIRED` | PASS | automática y del refutador |
| Compatibilidad con secretos y con el runtime de las Waves 1 a 4 | PASS | automática |
| Sin cambio de VERSION | sí | — |
| Sin push ni tag | sí | — |
| Sin commit todavía | sí | — |

## Automática

| Suite | Resultado |
|---|---|
| Wave 5 — `65_fail_closed` | 284/284 |
| Wave 4 — `64_interaccion_humana` | 376/376 |
| Wave 3 — `63_compuerta_del_flujo` | 487/487 |
| Wave 2 — `62_estado_del_flujo` | 177/177 |
| Wave 1 — `61_flujo_precondiciones` | 184/184 |
| Refutación atómica — `55` | 306/306 |
| Entorno primero — `60` | 307/307 |
| Reporte de seguridad — `48` | 566/566 |
| Bloque 4 — `30` | 871/871 |
| Context Bar — `53` | 464/464 |
| Compuerta entera, `.\tests\Invoke-Tests.ps1` | 38746/38746, salida 0 |

La compuerta entera es la del refutador en su cuarta pasada, sobre el árbol final; el árbol quedó
igual después. Los tests se escribieron antes del código y se vieron en rojo, o fallar por mutación
los seis escenarios que ya pasaban (detalle en `verificacion.md`).

## Del refutador

`harness-spec-refuter`, en cuatro pasadas: **43 escenarios sostenidos, 0 contradichos, 0 sin
sustento, 0 leídos**.

- **Primera pasada:** E-19, E-22 y E-39 contradichos; apareció E-42.
- **Segunda pasada:** sostenidos, con el texto de E-22 corregido.
- **Tercera pasada:** con la presentación normalizada (E-43), E-39 y E-43 contradichos en la sección de
  presupuesto.
- **Cuarta pasada:** los 43 sostenidos.

Sus sondas (`sonda1.py` a `sonda8.py`) probaron, entre otras cosas:

- las siete capacidades soportadas contra los cinco estados y cinco formas de registro: ninguna
  `NOT_SUPPORTED`;
- planes mixtos y planes anteriores a la Wave 5;
- los doce estados de frescura;
- severidades raras en los hallazgos;
- un `summary.json` sin `resolved`;
- el presupuesto con y sin política.

## Manual — capacidad soportada y no disponible

Proyecto `Desktop\harness-w5-aceptacion`. La sonda real contra los hosts sintéticos dejó GitLab en
`NOT_CONFIGURED`.

| Dónde | Observado | Resultado |
|---|---|---|
| `plan`, en texto | sección «Capacidades soportadas y no disponibles»; `gitlab.project.read`; integración `gitlab`; `NOT_CONFIGURED`; plan `BLOCKED`; `dev-tool-builder` no aparece por esta capacidad | PASS |
| `plan --json` | `supported: true`, `available: false`, `availability: SUPPORTED_UNAVAILABLE`, `integration: gitlab`, `integrationState` y `reasonCode` `NOT_CONFIGURED`, `derivedTo: null`, `toolClass: null`, `capabilityGaps: []` | PASS |
| `flujo --status` | `BLOCKED` por `CAPABILITY_UNAVAILABLE`, `HARD_BLOCKER`; `CAPABILITY_GAP` no aparece | PASS |

```text
SUPPORTED_UNAVAILABLE != CAPABILITY_GAP
SUPPORTED_UNAVAILABLE != NEW_TOOL_REQUIRED
```

En la misma sesión, ligada a ABC-123 bloqueada, `contabilidad ABC-456` fue negado. Es aislamiento de
sesión de la Wave 3, no un defecto de esta Wave; queda explicado en `verificacion.md`, y la
inconsistencia del motivo que muestra quedó para la Wave 6.

## Manual — Bloque 4 sin resolver

Proyecto `Desktop\harness-w5-block4-aceptacion`, reinstalado con el código final:

- sin estado del flujo de ninguna tarea;
- con un solo evento de ABC-456, sin ninguna métrica resuelta.

Comando: `python .claude\harness\bin\desarrollo\dev-harness.py contabilidad ABC-456 --reporte`.

| Qué | Observado | Resultado |
|---|---|---|
| Eventos | 1 contado, 0 duplicados, 0 correcciones | PASS |
| Tokens | `N/D` | PASS |
| Ventana | `N/D` | PASS |
| Tiempo | `N/D` | PASS |
| Costo | `N/D` | PASS |
| Fila del modelo `m-1` | input y output `N/D` | PASS |
| Sin atribuir | el evento no tiene unidad de trabajo, y el reporte dice que no lo reparte | PASS |
| Sin resolver | agente, costo, sesión, tiempo, uso y unidad de trabajo | PASS |
| Artefactos | `execution-cost.md` y `summary.json` en `.claude/runtime/accounting/ABC-456/` | PASS |
| Un `0` en lugar de algo sin resolver | no apareció | PASS |

```text
métrica sin resolver -> N/D
cero medido           -> 0
```

Por qué el evento llegó sin uso es la ingesta del Bloque 4, que quedó para la Wave 6.

## E-22, ratificado

La persona ratificó el 02-10-2026 el recorte del texto de E-22:

```text
resolved wall time + unresolved model time
=
wall time visible + model time N/D
```

Cada métrica se presenta según su propia resolución.

## De quien construyó, sin la UI

- **Ensayos previos:** los pasos de las dos aceptaciones manuales se corrieron antes sobre copias de
  los fixtures, con el mismo resultado que después vio la persona.
- **El deny cruzado:** se reprodujo contra la compuerta real. `contabilidad ABC-456` se evalúa contra
  la tarea de la sesión y `seguridad ABC-456` contra ABC-456; los dos dan deny.
- **Los dos hallazgos del plan:** se compararon con la línea de base, armando el mismo plan en un
  worktree de `2c33fba`. La salida es idéntica: son previos a la Wave 5.
  - `workUnits[].context.repository` vacío;
  - el aviso de ES0901 «26 de 26».

## Compatibilidad con secretos y con el runtime

Ningún fixture usó un token real. Las Waves 1 a 4, el Secret Guard y el entorno primero siguen
verdes dentro de la compuerta entera. Esta Wave no toca la compuerta del flujo, la protección de la
autoridad ni el `human-intent`.

## Lo que queda afuera

Para la Wave 6, en `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- la ingesta del Bloque 4: el adapter de Claude Code registra como `RESOLVED` un mensaje sin
  `usage`, y la barra descarta `USAGE_UNRESOLVED` antes del libro;
- la decisión de presupuesto `WITHIN_BUDGET` sobre un costo parcial;
- el motivo del deny cruzado de `contabilidad`;
- `workUnits[].context.repository` vacío;
- el aviso de ES0901 «26 de 26»;
- los estados de instalación que pintan OK sin resolución suficiente.

Siguen los de la Wave 4: la persistencia fuera del proyecto y la lista de programas de lectura.
