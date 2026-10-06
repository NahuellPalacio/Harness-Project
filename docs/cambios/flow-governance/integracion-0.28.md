# Flow Governance — integración con la línea oficial 0.28.0

**Estado:** integrada, refutada y aceptada (Manual B PASS); el merge commit espera la aprobación de
la persona · **Fecha:**
05-10-2026 · **Rama:** `integration/flow-governance-0.28` · **Merge sin commit**

Este documento registra la integración de las Waves 1 a 6 de Flow Governance con `origin/main` en
0.28.0. No reescribe ninguna spec cerrada: las specs de las Waves y las de 0.27.0/0.28.0 siguen
diciendo lo que decían cuando se cerraron. Lo que la integración pisa de un test cerrado lo dice acá
y en el test.

## Las dos líneas

```text
                  05dc830 ─ 27cd551 ─ e5d7a14          (0.27.0, 0.28.0)
                 /                            \
6cff4b4 (0.26.0)                               merge sin commit
                 \                            /
                  4a18ddc ─ … ─ 73a7b47                (Waves 1 a 6)
```

| | |
|---|---|
| Merge-base | `6cff4b4105b066c04a7b41090787775e41e51463` — 0.26.0 |
| Línea local | `4a18ddc`, `32febd7`, `2b43a77`, `2c33fba`, `556c7bd`, `73a7b47`, sin rebase ni squash |
| Línea oficial | `05dc830`, `27cd551`, `e5d7a14` |
| Checkpoint | `checkpoint/flow-governance-wave6` → `73a7b47` |
| Comando | `git merge --no-commit --no-ff origin/main` |
| VERSION | `0.28.0`, la de la línea oficial. Flow Governance no tiene número propio todavía |

109 archivos cambiados de un lado y 48 del otro; 13 en los dos.

## Los conflictos, y cómo se resolvieron

Siete archivos con conflicto de texto. En los siete, las dos líneas agregaban cosas distintas al
mismo lugar, y la resolución es la unión: ninguna línea gana entera.

| Archivo | Waves | 0.27/0.28 | Resolución |
|---|---|---|---|
| `.claude/agents/harness-hook-engineer.md` | «nothing blocks except secrets **and the flow gate**» | suma `PowerShell` a las herramientas | las dos cosas |
| `comun/hooks/lib/bienvenida.py` | la evidencia opcional `lastSessionWithData` en la señal de vida, y `con_datos` al escribirla | `presentation` opcional y su parámetro `presentacion` | el contrato admite las dos, cada una con `additionalProperties: false`; `escribir_senal_de_vida(..., con_datos=False, *, presentacion=None)` |
| `harnesses/desarrollo/bin/contabilidad/statusline.py` | `presentacion.resuelto` (Wave 5) decide qué familia se muestra; `con_datos` a la señal | los colores, el módulo `eventos` y la foto de la ventana | colores de 0.28 sobre la regla de la Wave 5: `Budget` se pinta por nivel solo si el costo está resuelto; la señal recibe `con_datos` y `presentacion` |
| `harnesses/desarrollo/bin/contabilidad/agregacion.py` | `resumen["resolved"]` | `_sin_resolver(..., resumen["context"])` | las dos |
| `harnesses/desarrollo/bin/dev-harness.py` | imports de `flujo` y `estado_de_tarea`, el subcomando `flujo` | imports de `http` y `auto_refresh`, el subcomando `presupuesto` | los dos subcomandos y todos los imports |
| `install.ps1` | `Test-FormaDeLaBarra`, `Get-BarraEnVivo`, `Get-BarraDelDoctor`, `Get-NivelDeLaBarra`, `Test-EsAliasDeLaStore` | `Get-UmbralesDeContexto` | todas las funciones; el BOM del archivo se conserva |
| `tests/casos/53_context_bar.py` E-10 | pisado por la Wave 6: los cinco campos y la evidencia | pisado por 0.28 E-60: los cinco campos y `presentation` | los cinco, `presentation` y la evidencia, con los dos motivos en el test |

Lo que git mezcló solo se revisó igual. En particular, la ingesta de la barra quedó con la regla de
la Wave 6 (se escribe todo registro con clave, también `USAGE_UNRESOLVED`) y la foto de la ventana de
0.28 va después, en la misma escritura.

## La frescura del conocimiento: decisión A

### El conflicto

Dos specs cerradas decían cosas distintas sobre lo mismo, y con el código mezclado ganaba 0.27,
porque su compuerta corría antes de `planificar`:

| | Wave 5 (`fail-closed-hardening`) | 0.27.0 (`conocimiento-auto-refresco`) |
|---|---|---|
| Qué fuentes bloquean | solo las que la operación exige (E-17) | cualquier fuente seguida (KRF E-42) |
| `plan` con una exigida en alerta | escribe el plan `BLOCKED`, el flujo queda `HARD_BLOCKER` en `PLANNING` (E-16); resuelta, el plan queda viejo (E-38) | sale con 2 sin escribir el plan (KRF E-42) |
| Estados que bloquean | `SOURCE_INTEGRITY_ALERT`, `SOURCE_CHANGED_SAME_VERSION`, `VERSION_REGRESSION` | los mismos |

Con `plan` saliendo antes de `reconciliar_estado`, el bloqueo ni siquiera quedaba en
`task-flow-state`. El rojo, sobre el árbol mezclado sin la decisión:

```text
MAL 65_fail_closed / E-16 el flujo BLOCKED                 esperado BLOCKED / obtenido None
MAL 65_fail_closed / E-16 con el codigo del estado         es falso
MAL 65_fail_closed / E-16 HARD_BLOCKER en PLANNING         obtenido []
MAL 65_fail_closed / E-17 refute --compile con alerta en ES0903 sale 0   obtenido 2
MAL 65_fail_closed / E-38 el plan quedo viejo              es falso
MAL 65_fail_closed / E-38 hay que regenerarlo              es falso
```

### La decisión

**La persona eligió la opción A el 05-10-2026.**

```text
auto-refresh                      = refresca + observa + registra + avisa
frescura de la operación          = decide si plan / refute pueden avanzar

auto_refresh  -> produce o actualiza el estado
operación     -> calcula las fuentes que exige
frescura      -> evalúa solo esas (frescura.de_la_operacion)
plan / refute -> persiste el bloqueo o lo niega, según su contrato
```

- Solo las fuentes que la operación exige participan del bloqueo. Bloquean
  `SOURCE_INTEGRITY_ALERT`, `SOURCE_CHANGED_SAME_VERSION` y `VERSION_REGRESSION`.
- `FRESHNESS_UNVERIFIED` no es `CURRENT`, se informa, y por sí sola no bloquea.
- Una fuente seguida que la operación no exige no frena `plan` ni `refute --compile`: se avisa.
- Con una exigida en alerta, `plan` se escribe `BLOCKED` y el flujo queda `HARD_BLOCKER`;
  `refute --compile` sale con 2 sin escribir, por `compuerta_de_refutacion` y su frescura.
- El refresco corre antes de la decisión, y la decisión usa lo que el refresco dejó.

### Lo que se construyó

- `dev-harness.py` — `compuerta_normativa` ya no corta nunca: refresca, emite el evento, avisa lo
  `unresolved` y nombra las fuentes seguidas en alerta («la operación decide por las fuentes que
  exige»). Se fue el parámetro `cortar`: ninguna operación lo usa.
- `orquestacion/auto_refresh.py` — `ensure_normative_knowledge_fresh(..., requeridas=None)`. Puede
  devolver `blocked` solo con un alcance, y lo calcula con `frescura.de_la_operacion`, la misma
  función que el plan y la refutación: no puede decidir distinto. Sin alcance, una alerta queda en
  `alerts` y la decisión es `unresolved`. La lista de estados que bloquean es
  `frescura.BLOQUEAN_OPERACION`, que la Wave 5 ya fija igual a la de la bienvenida.

### KRF E-42: SUPERSEDED_AT_INTEGRATION_BOUNDARY

```text
0.27 E-42                                   = parada global antes de la operación
0.28 integrada con Flow Governance          = primero el refresco, después la autoridad de la operación
```

La spec de 0.27 no se reescribe: sigue diciendo lo que se decidió el 29-09-2026, sin conocer la
Wave 5. Su test en `61_conocimiento_auto_refresco.py` cambió, con la nota de que es una adaptación
de integración de un cambio cerrado. Ahora afirma:

- sin alcance, una fuente en alerta no frena: `unresolved`, con la alerta en `alerts`;
- con la fuente en el alcance, `blocked`;
- con la fuente fuera del alcance, nada bloquea;
- `plan` no se corta en el refresco, avisa la alerta y sigue hasta su propio error.

Lo que E-42 protegía, que una alerta de integridad no se use como si nada, sigue en pie en la
operación: E-16 de la Wave 5 e I-02, I-04 e I-07.

### Escenarios de la integración

En `tests/casos/67_integracion_frescura.py`, con su id en el nombre del test.

- **I-01** — (A) Una fuente seguida y no exigida (ES0903) en `SOURCE_INTEGRITY_ALERT`: `plan` sale
  0, el plan se escribe y no queda `BLOCKED`, el flujo no la lleva, y la alerta se avisa.
  `rojo visto`
- **I-02** — (B) Una exigida (ES0901) en `SOURCE_INTEGRITY_ALERT`: el plan se escribe `BLOCKED`, y
  el flujo queda `BLOCKED` con `HARD_BLOCKER` en `PLANNING` por `plan.knowledgeSources`.
  `rojo visto`
- **I-03** — (C) Una seguida y no exigida en `SOURCE_CHANGED_SAME_VERSION`: no frena el plan, y
  `refute --compile` sale 0 y escribe la corrida. `rojo visto`
- **I-04** — (D) Una exigida en `SOURCE_CHANGED_SAME_VERSION`: el plan `BLOCKED` con el
  `HARD_BLOCKER`, y `refute --compile` sale 2 con el código y sin `run.json`. `rojo visto`
- **I-05** — (E) Una exigida en `FRESHNESS_UNVERIFIED`: no es `CURRENT`, el plan y el refresco lo
  dicen, nada bloquea, y la corrida lleva `REFUTATION_SOURCE_UNVERIFIED`. `rojo visto`
- **I-06** — (F) Con la agenda vencida y un canal local, una alerta escrita a mano que el canal no
  confirma: el plan refresca con `PRE_NORMATIVE_OPERATION_IF_STALE` y decide con lo observado, sin
  `BLOCKED`. Control: con la agenda al día no hay refresco, y la misma alerta lo deja `BLOCKED`.
  `rojo visto`
- **I-07** — (G) `refute --compile` decide por el estándar que compila: la misma alerta frena en
  ES0901 (sale 2, sin `run.json`) y no en ES0903 ni en PC0901 (sale 0, con `run.json`). `rojo visto`
- **I-08** — (F, para la refutación) Con la agenda vencida y un canal local, una alerta escrita a
  mano en ES0901 que el canal no confirma: `refute --compile` refresca con
  `PRE_NORMATIVE_OPERATION_IF_STALE`, sale 0 y escribe la corrida. Control: con la agenda al día no
  hay refresco, sale 2 y nombra la alerta. *Agregado el 05-10-2026, después de la primera pasada
  del refutador: I-06 probaba el orden solo para `plan`.* `rojo visto`

El `rojo visto` salió de romper el código el 05-10-2026, sobre la copia de trabajo y con respaldo
byte a byte, que se restauró y se comparó después de cada mutación:

| Mutación | Rojo |
|---|---|
| la parada global de 0.27 de vuelta: `compuerta_normativa` corta si hay una fuente seguida en alerta | I-01, I-02, I-03, I-04, el control de I-06, I-07; también 7 aserciones de `65_fail_closed` |
| el refresco después de `planificar` | I-06 |
| el refresco después de `refutar` | I-08 |
| `ensure_normative_knowledge_fresh` sin alcance: bloquea por cualquier alerta | E-42 integrado de `61_conocimiento_auto_refresco` (fuera del alcance) |
| `FRESHNESS_UNVERIFIED` entre los que bloquean | I-05 |

E-16, E-17 y E-38 de la Wave 5 son el rojo de la decisión: los seis que fallaban en el árbol mezclado
pasan sin que se haya tocado su test.

## Tests de cambios cerrados que la integración pisa — ratificados

**La persona ratificó las tres adaptaciones el 05-10-2026.** Cada una lo dice en el test, con este
documento como motivo. Lo que protegían no cambia.

| Test | Antes | Ahora | Por qué |
|---|---|---|---|
| `61_conocimiento_auto_refresco` E-58 (KRF-058) | `pre-tool-use.py` y `secretos.py` iguales a 0.26.0 | iguales a la Wave 6 (`73a7b47`); `permisos-por-capacidad.json` sigue contra 0.26.0; el stderr de git no sale | las Waves 3 a 6 los cambiaron a propósito. E-58 protege que el auto-refresco no toque las protecciones, y eso sigue. No es un debilitamiento |
| `62_context_bar_consumo` E-60 | exactamente seis claves | las seis, `presentation` incluida, y `lastSessionWithData`, sin números tampoco adentro | el dibujo del test tiene datos, y la Wave 6 (E-36) suma la evidencia |
| `66_integrity_cleanup` E-36 y E-41 | la versión del renderizador escrita como `"1.0.0"` | la versión real del renderizador instalado, y la nueva derivada de ella | 0.28 la pasa a `1.2.0`. Con el literal, E-41 no podía fallar: el reemplazo no cambiaba nada. Ahora el test afirma además que el reemplazo cambió el archivo, así que detecta de verdad una versión incompatible |

Y uno más, el de la decisión: **KRF E-42**, arriba.

La primera corrida de la compuerta se cortó sin terminar el motor Python: el `git diff` de E-58
escribía en stderr un aviso de fin de línea —`03-instalador.ps1` restaura los hooks con LF—, e
`Invoke-Tests.ps1` lo toma como error. E-58 ahora captura el stderr de git, como ya lo hace el resto
de ese archivo. El árbol no quedó roto.

## Lo que se revisó y no pide cambios

- **Context Bar.** Los colores, `Ctx NN%` desde el stdin, el adaptador, `INTEGRATION_VERSION 1.2.0`
  y la política por defecto de 0.28 conviven con las cuatro reglas de la Wave 6: la evidencia
  histórica no es actividad de la sesión, un dibujo vacío no la borra, otra configuración (también
  otra versión del renderizador) no la reusa, y `-Doctor` `ACTIVE` no es `activeInCurrentSession`.
  Una foto `CONTEXT_WINDOW_OBSERVED` lleva el `sessionId` de la sesión: un dibujo que solo muestra
  `Ctx` es un dibujo con datos, y avanza la evidencia.
- **Bloque 4.** Un mensaje sin uso sigue `USAGE_UNRESOLVED` con su clave y llega al libro. Trae
  `context: None`, así que el contexto de la transcripción (`TRANSCRIPT_ONLY`) lo saltea y no
  aparece un `Ctx 0`. `Tok` se oculta con la regla de la Wave 5, que cubre también
  `USAGE_RECONCILIATION_UNRESOLVED`. El presupuesto con costo sin resolver sigue `COST_UNRESOLVED`, y
  `Budget` no se dibuja ni se pinta.
- **Hooks.** 0.27/0.28 no tocan `pre-tool-use.py`, `secretos.py`, `tool_policy.py`,
  `flow_gate.py`, `session-start.py` ni la plantilla de settings. El matcher `^mcp__`, E-24, el
  evento ilegible y el Secret Guard antes de la compuerta quedan como en la Wave 6.
- **La CLI nueva bajo la política de las Waves.** `fuentes --auto` y `fuentes --si-vence` son
  `FLOW_RECOVERY`, como `fuentes`.
- **Instalador.** 0.27/0.28 solo agregan: la siembra de `harness.presupuesto.json`, el refresco del
  conocimiento y los umbrales al terminar. Nada de la Wave 6 (`-Doctor`, el alias de la Store, el
  matcher) se perdió.

### `presupuesto` cae en `UNRESOLVED_TOOL_CLASS`

`presupuesto` llegó con 0.28.0 y la tabla de la política no lo nombra: es `UNRESOLVED_TOOL_CLASS`.
Con la tarea sana pasa; con la tarea bloqueada, una decisión pendiente o la autoridad ambigua se
niega, aunque solo lea. **La persona lo clasificó USABILITY / CONSERVATIVE_OVERBLOCK /
NON-BLOCKING el 05-10-2026**: no bloquea la integración, el contrato de `UNRESOLVED_TOOL_CLASS` no
cambia y no hay una excepción apurada. Queda en `Pendientes/Ideas-Harness/PENDIENTES-I.md`.

## Tests

| | |
|---|---|
| Árbol mezclado, antes de la decisión | 40331/40337, exit 1: los 6 de la Wave 5 de arriba |
| Después de la decisión A | 40382/40382, exit 0 |
| Final, con I-08 y todo en el index | **40389/40389, exit 0** (PowerShell 644/644, Python 39745/39745) |
| Focales finales | `65_fail_closed` 284, `61_conocimiento_auto_refresco` 292, `67_integracion_frescura` 43, `66_integrity_cleanup` 725, `62_context_bar_consumo` 372, `53_context_bar` 515, `51_bienvenida` 660, `30_b4` 881, `63_compuerta_del_flujo` 487, `64_interaccion_humana` 376, `55_refutacion_atomica` 306, `60_entorno_primero` 307, `48_reporte_de_seguridad` 566, `37_es0902_seguridad` 1482 |

## La refutación

`harness-spec-refuter`, que no construyó, el 05-10-2026, en dos pasadas, sobre 14 afirmaciones:
I-01 a I-07, la autoridad única, el refresco antes de decidir, KRF E-42 integrado, E-16/E-17/E-38 de
la Wave 5 con su test sin cambios, las capacidades fail-closed, E-24 con los hooks y los settings
iguales a la Wave 6, `UNRESOLVED_TOOL_CLASS` y `presupuesto`, el Bloque 4 sin resolver, E-05/E-06 de
la Context Bar y de la Wave 6, E-36 a E-46 de la Wave 6, las tres adaptaciones ratificadas, lo de
0.28 y VERSION.

- **Primera pasada:** 13 sostenidos y 1 sin sustento. El sin sustento era el refresco antes de decidir
  en `refute --compile`, que ningún test probaba. Además el index no tenía la decisión A.
- **Segunda pasada:** I-08 sostenido, y con él la afirmación 3. El index es el árbol probado.

Resultado: **14 sostenidos**, ninguno contradicho, ninguno sin sustento, ninguno leído.

Lo que vio fuera de las afirmaciones quedó anotado:
- dos tests débiles de la Wave 6, en `PENDIENTES-FH.md`, dentro de «Wave 6 leftovers»: E-03 de 66
  busca solo `" 0 "`, y E-41 de 66 registra en un momento fijo pero dibuja con el reloj real;
- el docstring de E-58, que se corrigió.

## La aceptación manual B, sobre el árbol integrado

**PASS de la persona, 05-10-2026**, con Claude Code CLI real, en un proyecto de prueba actualizado a
0.28.0. La B de la Wave 6 no servía: la resolución había cambiado `bienvenida.py` y `statusline.py`.

| Paso | Lo que se observó |
|---|---|
| 1. `-Update` real | 0.26.0 → 0.28.0, exit 0, `integrationVersion` `1.2.0` |
| 2. Después del update | Context Bar `RELOAD_REQUIRED`, con el aviso de reiniciar |
| 3. Sesión nueva de 0.28, sin datos | `state` `CONFIGURED`, `reloadRequired` false, `activeInCurrentSession` false, `integrationVersion` `1.2.0`, `lastSessionWithData` null. La evidencia de la sesión de 0.26 no se reusó como `ACTIVE` |
| 4. Después de un mensaje real | `state` `ACTIVE`; `lastSessionId` y `lastSessionWithData` `fe0c7c61-35f6-4fd2-b7c5-7dc59c8eb456` |
| 5. La barra, mirada en la terminal | `HARNESS \| claude-opus-5-5 \| Ctx 5% \| Tok 51k in / 29 out` |
| 6. Reinicio real, sin mensaje en la sesión nueva | `-Doctor`: `OK Context Bar: ACTIVA (última sesión con datos: fe0c7c61-35f6-4fd2-b7c5-7dc59c8eb456)`. `bienvenida.py barra`: `state` `ACTIVE`, `version` `0.28.0`, `integrationVersion` `1.2.0`, `activeInCurrentSession` false, `lastSessionId` `12f49a04-b7c6-4652-a9ab-aab5faaa9b08`, `lastSessionWithData` `fe0c7c61-35f6-4fd2-b7c5-7dc59c8eb456` |

Lo que sostiene:

```text
actividad de la sesión actual        != estado efectivo de la integración
una sesión nueva vacía               != borrar la evidencia histórica compatible
otra versión de la integración       != reusar la evidencia ACTIVE vieja       (paso 3)
```

| | |
|---|---|
| Manual B integrada | PASS |
| Presentación de 0.27 | PASS. La línea se dibujó en la sesión real. Con `Ctx 5%`, debajo de WARNING 70% y de ERROR 90%, ni el amarillo ni el rojo correspondían, y no se pidieron en esta observación |
| `Ctx NN%` de 0.28 | PASS: `Ctx 5%` con la primera respuesta real |
| Persistencia de la Wave 6 | PASS: la evidencia sobrevivió al reinicio sin hacer activa a la sesión nueva |

## Lo que falta

1. ~~La refutación focal~~: hecha, 14 sostenidos.
2. ~~La aceptación manual B~~: PASS, arriba.
3. El merge commit, con la aprobación de la persona.

`qualification-readiness.md` se actualizó el 05-10-2026: la base integrada es 0.28.0, la
recomendación vieja de 0.27.0 se fue, y la versión siguiente queda DECISION_PENDING.
