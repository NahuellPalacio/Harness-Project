# Verificación — `dev-refutador` lee `project-context.json` como evidencia

**Estado:** cerrado · **Fecha:** 29-08-2026, lectura firmada el 30-08-2026 · **Versión:** 0.14.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los emitió
`harness-spec-refuter` el 29-08-2026, en dos pasadas: la primera contra el código recién construido,
corriendo la suite completa él mismo (686/686 antes de tocar nada); la segunda, después de un
arreglo aplicado sobre una reserva que la primera pasada dejó escrita en E-01, confirmando el
arreglo con la misma disciplina —doce corridas de la mutación, restauración verificada en cada una.
**Una tercera pasada, el 30-08-2026**, verificó la firma de [`lectura.md`](lectura.md) —dos corridas
reales de `dev-refutador` sobre `C:\Users\Asus\lecturas-0.14.0\reservas`, una con
`project-context.json` y otra sin él, restaurado después con `md5` verificado.

**Resultado: 7 escenarios sostenidos, 2 leídos (independientes), 0 contradichos, 0 sin sustento.**

**El cambio cierra.** E-08 y E-09 pasaron a `leído` con lecturas que cumplen las cuatro condiciones
de [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md) — incluida la
coincidencia byte a byte entre el `repo_revision` que cita el `Observado` de E-08 y el
`meta.repo_revision` real del contrato.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Validación fallida no pisa un `project-context.json` válido preexistente | sostenido | sí, y reescrito | `13_contexto.py::test_e01_refutador_lee_contrato_...` |
| E-02 | El prompt lee el contrato antes de invocar una skill o grepear | sostenido | sí | `16_refutador_contrato.py::test_e02_...` |
| E-03 | El prompt dice que el contrato es evidencia, nunca norma | sostenido | sí | `16_refutador_contrato.py::test_e03_...` |
| E-04 | Contrato ausente/roto/insuficiente → hueco, nunca inferencia | sostenido | sí | `16_refutador_contrato.py::test_e04_...` |
| E-05 | La fila de salida suma la columna `repo_revision` | sostenido | sí | `16_refutador_contrato.py::test_e05_...` |
| E-06 | `cumple` sigue exigiendo cita y línea, sin excepción nueva | sostenido | sí, dos mitades | `16_refutador_contrato.py::test_e06_...` |
| E-07 | `dev-refutador` sigue sin herramienta de ejecución | sostenido | sí | `16_refutador_contrato.py::test_e07_...` |
| E-08 | Con contrato completo, una corrida real lo cita como evidencia y nombra el `repo_revision` | leído, independiente | no consta | [`lectura.md`](lectura.md) — Nahue Palacio, 30-08-2026 |
| E-09 | Sin contrato o con uno roto, una corrida real declara `sin-verificar` sin inventar | leído, independiente | no consta | [`lectura.md`](lectura.md) — Nahue Palacio, 30-08-2026 |

📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** No aplica acá para E-01 a E-07:
los siete tienen su rojo visto confirmado por el refutador mismo, no sólo declarado por quien
construyó.

## E-01, el escenario cuyo primer `rojo visto` era timing-dependiente

No es un `contradicho` —terminó `sostenido`— pero merece su propia sección: la primera pasada del
refutador encontró que la evidencia de rojo visto de este escenario no probaba lo que decía probar,
igual que pasó con E-15 del cambio anterior. ADR-0006 pide que eso se diga, no que se pula en
silencio.

El primer diseño de E-01 comparaba únicamente los bytes de `project-context.json` antes y después de
una corrida que debía fallar. La mutación que se usó para verlo en rojo —`exigir_lo_imposible`, la
misma técnica de `E-07`, un campo `required` imposible en un schema de mentira— **no cambia nada de
lo que `armar()` calcula**: la segunda corrida produce un documento funcionalmente idéntico al
primero, salvo `meta.generated_at`, que tiene resolución de un segundo. Si las dos corridas caían
dentro del mismo segundo de reloj, los bytes coincidían igual **aunque el bug estuviera presente**, y
el test pasaba por casualidad de timing, no porque el invariante se sostuviera.

```
Primera verificación del refutador: mutación repetida 3 veces
  Cayó: 1 de 3. En las otras 2, el único test que atrapó la regresión fue E-07
  (sobre un directorio vacío), no el escenario nuevo.
```

**La decisión: se corrigió el test, no se aflojó el escenario.** Se sumó el `mtime` del archivo **en
nanosegundos**, capturado antes y después de la segunda corrida: una reescritura real siempre mueve
el `mtime` a nivel de sistema operativo, coincida o no el contenido por el segundo compartido de
`generated_at`.

```
Segunda verificación del refutador, sobre el arreglo: mutación repetida 12 veces
  mtime detectó el bug:                    12 de 12
  bytes solos habrían detectado el bug:     3 de 12
  (las otras 9 cayeron dentro del mismo segundo de reloj — bytes idénticos,
  bug presente, y el mtime lo marcó igual las 9 veces)
```

La proposición de la spec —una corrida rota no toca un contrato válido preexistente— sigue siendo
la misma; lo que cambió es cómo se prueba que se sostiene.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El defecto de E-01**, descripto arriba: un `rojo visto` declarado `sí` que en 2 de 3 corridas
   reales no hubiera atrapado el bug que dice proteger. Es el hallazgo que justifica que la
   verificación exista — y la segunda pasada, con doce corridas, es la que da la confianza real de
   que el arreglo cierra el hueco.
2. **Nada más.** Los seis escenarios sobre el texto del prompt (E-02 a E-07) resultaron sólidos en
   la primera pasada; el refutador confirmó específicamente que el diseño de dos mitades de E-06
   —no sólo "la regla sigue ahí" sino "la sección nueva no menciona `cumpl-` de más"— era necesario y
   no cosmético, reproduciendo el caso que ese mismo diseño existe para atrapar.

## E-08 y E-09, firmadas el 30-08-2026

Dos corridas reales sobre el mismo lote (`src/api/main.ts`, `src/api/reservas.ts`,
`src/api/espacios.ts`), la primera con `project-context.json` presente, la segunda con el archivo
movido aparte y restaurado después —`md5` verificado idéntico antes y después,
`9378becdf3e858270438f54826c4cfbc`—. En la primera, las 14 filas citaron el `repo_revision` real y
ninguna citó el contrato como norma; en la segunda, `dev-refutador` dijo de entrada que no había
contrato y las 14 filas quedaron con `repo_revision` en `—`, sin inventar nada de lo que el
contrato ausente hubiera resuelto.

## Lo que queda abierto, anotado y no escondido

**El eje regulatorio y el de gobierno del repositorio siguen sin modelar en el contrato.** No es un
defecto de este cambio: es exactamente lo que `Pendientes/Ideas-Harness/PENDIENTES-I.md` deja
abierto a propósito, y esta spec no lo resuelve porque no le corresponde.

## Lo que ningún test cubre y se mira con los ojos

**Que `dev-refutador`, corriendo de verdad, efectivamente lea el contrato, lo cite como evidencia y
no como norma, y declare `sin-verificar` cuando el contrato falta o está roto.** Es E-08 y E-09, y es
lo único de esta spec que un test no puede alcanzar: el sujeto es una corrida real del modelo, y la
suite de este repositorio son tests deterministas y sin red.

`docs/cambios/dev-refutador-lee-el-contrato/lectura.md` tiene la guía completa de cómo llenarlos —
qué correr, contra qué proyecto, qué mirar en cada mitad de cada escenario— y sigue sin firma.
