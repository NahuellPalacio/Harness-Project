# Verificación — Bloque 3, la refutación atómica

**Estado:** cerrado · **Fecha:** 25-09-2026 · **Versión:** sin publicar todavía (`close-a-version`)

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó.

Los veredictos los emitió `harness-spec-refuter` el 25-09-2026, en tres pasadas:

- **Primera pasada, sobre los 61 escenarios.** Corrió `python tests/correr.py -k 55_` (287/287) y
  `.\tests\Invoke-Tests.ps1` (35272/35272, exit 0), más sondas de solo lectura en temporales.
- **Segunda pasada, sobre E-30, E-55 y E-57.** Corrió el archivo 55 (301/301).
- **Pasada final, sobre E-57.** Corrió el archivo 55 (305/305).

La suite entera sobre el árbol final la corrió el constructor: 35290/35290, exit 0.

**Resultado: 61 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos.**

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Un solo agente de refutación, un solo `dev-refutador*` | sostenido | sí | `55_refutacion_atomica.py`, `test_e01_…` |
| E-02 | Ninguna skill con `refut` ni `atomic` | sostenido | sí | `test_e02_…`; el refutador revisó además `.claude/skills/` |
| E-03 | El registro valida; `CRITIC_AGENT` con cero skills | sostenido | sí | `test_e03_…` |
| E-04 | El plan no gana campos y `--compile` no lo toca | sostenido | sí | `test_e04_…` |
| E-05 | Una regla + un alcance = una unidad | sostenido | sí | `test_e05_…` |
| E-06 | Dos reglas, dos unidades | sostenido | sí | `test_e06_…` |
| E-07 | Misma regla, dos alcances, dos unidades | sostenido | sí | `test_e07_…` |
| E-08 | Sin alcance, con `.` o con `/`: nunca el repositorio | sostenido | sí | `test_e08_…` |
| E-09 | Alcance sin resolver → `BLOCKED`, no `PASS` | sostenido | sí | `test_e09_…` |
| E-10 | Dos `--compile` iguales byte a byte | sostenido | sí | `test_e10_…` |
| E-11 | Check concluyente cierra sin modelo | sostenido | sí | `test_e11_…` |
| E-12 | Check no concluyente nunca da `cumple` | sostenido | sí, las dos guardas | `test_e12_…` |
| E-13 | Check con otra huella u otra revisión no cierra | sostenido | sí | `test_e13_…` |
| E-14 | Regla con `reviews` va al refutador | sostenido | sí | `test_e14_…` |
| E-15 | Check de otra regla no cierra | sostenido | sí, las dos guardas | `test_e15_…` (ver hallazgos) |
| E-16 | `--unit` entrega un objeto; bloqueada o resuelta sale con 2 | sostenido | sí | `test_e16_…`, por CLI |
| E-17 | Evidencia fuera del alcance se rechaza | sostenido | sí | `test_e17_…` y `dev-refutador.md` |
| E-18 | Otra `ruleKey` se rechaza | sostenido | sí | `test_e18_…` |
| E-19 | `tools` exactas; no corrige ni parchea | sostenido | sí | `test_e19_…` |
| E-20 | `cumple` sin cita o sin línea se rechaza | sostenido | sí | `test_e20_…` |
| E-21 | Sin regla citable → `sin-verificar` | sostenido | sí | `test_e21_…` |
| E-22 | `EVIDENCE_INSUFFICIENT` entra; sin motivo no | sostenido | sí | `test_e22_…` |
| E-23 | `incumple` sin evidencia concreta se rechaza | sostenido | sí | `test_e23_…` |
| E-24 | Todo veredicto guardado valida | sostenido | sí | `test_e24_…` |
| E-25 | Prosa, bloque de código o JSON roto se rechazan | sostenido | sí | `test_e25_…`, también por CLI |
| E-26 | Un byte cambia la huella | sostenido | sí | `test_e26_…` |
| E-27 | `HEAD` igual y archivo tocado → `EVIDENCE_STALE` | sostenido | sí | `test_e27_…` |
| E-28 | Otra revisión, otra clave | sostenido | sí | `test_e28_a_e31_…` |
| E-29 | Otra skill, otra clave | sostenido | sí | `test_e28_a_e31_…` y `test_e29_e31_…_de_punta_a_punta` |
| E-30 | Otra entrada de matriz, otra clave | sostenido | sí | `test_e30_…_de_punta_a_punta` (segunda pasada) |
| E-31 | Otro contrato, otra clave | sostenido | sí | los mismos dos que E-29 |
| E-32 | `cumple` se reusa con sus evidencias | sostenido | sí | `test_e32_e33_…` |
| E-33 | `incumple` se reusa igual | sostenido | sí | `test_e32_e33_…` |
| E-34 | `sin-verificar` no se reusa | sostenido | sí | `test_e34_…` |
| E-35 | Un acierto de caché no escribe consumo | sostenido | sí | `test_e35_e46_…` |
| E-36 | Caché adulterada no se usa y se avisa | sostenido | sí | `test_e36_…`, tres adulteraciones |
| E-37 | `refutacion.py` sin cliente de modelo ni red | sostenido | sí | `test_e37_…` (ver hallazgos) |
| E-38 | Todo `cumple` → `PASS` | sostenido | sí | `test_e38_a_e41_…` |
| E-39 | Un `incumple` → `FAIL` | sostenido | sí | `test_e38_a_e41_…` |
| E-40 | Sin `incumple` y algo abierto → `INCOMPLETE` | sostenido | sí | `test_e38_a_e41_…` |
| E-41 | Cero unidades → `NOTHING_TO_VERIFY` | sostenido | sí | `test_e38_a_e41_…`, también con un plan real |
| E-42 | Contadores deterministas | sostenido | sí | `test_e42_…` |
| E-43 | `workUnitId` original en el Bloque 4 | sostenido | sí | `test_e43_a_e45_…`, por CLI |
| E-44 | `metadata` con fase, id, camino y `cacheHit` | sostenido | sí | `test_e43_a_e45_…` |
| E-45 | `agentId = dev-refutador`; otro `--agente` sale con 2 | sostenido | sí | `test_e43_a_e45_…` |
| E-46 | Sin libro ni `cacheHit: true` por caché | sostenido | sí | `test_e35_e46_…` |
| E-47 | Resuelta por check: sin libro ni atribución | sostenido | sí | `test_e47_…` |
| E-48 | Reglas distintas no forman lote | sostenido | sí | `test_e48_…` |
| E-49 | Huellas distintas no forman lote | sostenido | sí | `test_e49_…`; la sonda confirmó el motivo |
| E-50 | Lote: uno por unidad, todo o nada | sostenido | sí | `test_e50_…` |
| E-51 | `plan` igual con y sin refutaciones | sostenido | sí | `test_e51_…`, por CLI |
| E-52 | `SessionStart` no nombra `refut` | sostenido | sí | `test_e52_…` |
| E-53 | Compile y record no escriben seguridad | sostenido | sí | `test_e53_e55_…` y `test_e53_e55_corrida_completa_por_cli` |
| E-54 | ES0902 entra como `REVIEW_EVALUATION` al libro existente | sostenido | sí | `test_e54_…`, por CLI |
| E-55 | Nada de seguridad bajo `refutaciones/`; un solo libro | sostenido | sí | `test_e53_e55_corrida_completa_por_cli` (segunda pasada) |
| E-56 | `--summary` en español | sostenido | sí | `test_e56_e57_…` |
| E-57 | `--json` canónico, avisos `CÓDIGO:sujeto`, el schema no admite otros | sostenido | sí, las dos guardas | `test_e56_e57_…` (pasada final) |
| E-58 | Sin claves de conversación; el veredicto no admite claves de más | sostenido | sí | `test_e58_…` |
| E-59 | Secreto redactado; `.env` en el alcance bloquea | sostenido | sí | `test_e59_…` |
| E-60 | Nunca más rutas que las declaradas | sostenido | sí | `test_e60_…` |
| E-61 | La suite sale con 0 | sostenido | no consta | `.\tests\Invoke-Tests.ps1`: 35272/35272 del refutador; 35290/35290 del constructor sobre el árbol final |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

«Sí, las dos guardas» quiere decir que el código tiene dos defensas independientes: la mutación de
una sola quedaba verde, y el rojo se vio rompiendo las dos.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-57, contradicho en la primera pasada.** `--status --json` volcaba `run.json` entero, con los
   avisos en español sin tildes. La regex del test (`[áéíóúñ]|sin verificar`) no los veía, y la
   entrada del test era una corrida sin avisos. Se corrigió en el código: los avisos pasaron a
   `CÓDIGO:sujeto`, el schema de la corrida exige ese patrón y el texto en español lo arma solo el
   renderizador.
2. **E-57, sin sustento en la segunda pasada.** La cláusula «el schema de la corrida no admite
   otro» no tenía una aserción contra el schema; el test comparaba contra la regex del módulo.
   Ahora la tiene.
3. **E-30, sin sustento.** El test reemplazaba el campo a mano. Faltaba probar que una entrada de
   matriz distinta cambia la huella de punta a punta.
4. **E-55, sin sustento.** La «corrida completa» no incluía `seguridad --refutacion`, que es el
   único camino que escribe seguridad. La entrada elegía el caso donde no se podía fallar.
5. **Observaciones sin cambio de veredicto:**
   - E-15: la condición 3 (checks de la matriz) ya rechazaba el caso sin ejercitar la condición 2.
     El rojo se vio rompiendo las dos.
   - E-37: el test mira `import` y `from`, y el escenario dice «no aparece». El grep del refutador
     no encontró ninguna de las seis palabras.
   - E-53: se probaba por funciones, y ahora también por CLI.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- *No real `dev-refutador` run over a `refutation-unit/1.0` has been read.* La frontera está
  probada, pero lo que hace una corrida real entre `--unit` y `--record` no.
- *Atomic refutation has counters and no baseline.* No se midió antes y después.

## Lo que ningún test cubre y se mira con los ojos

- Una sesión real de Claude Code que invoque a `dev-refutador` con la salida de `refute --unit` y
  devuelva un objeto que `--record` acepte, sin prosa alrededor.
- El resumen de `--summary` leído por una persona, con un plan real de muchas unidades bloqueadas.
