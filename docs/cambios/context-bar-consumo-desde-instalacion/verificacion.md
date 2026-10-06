# Verificación — Bloque 1: la Context Bar muestra el consumo de contexto desde la instalación

**Estado:** cerrado · **Fecha:** 01-10-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` en dos
pasadas, las dos el 30-09-2026.

- **Primera:** sobre E-01 a E-77. Corrió `62_context_bar_consumo` (335/335), `30_b4` (868/868),
  `53_context_bar` (502/502) y `38_integridad` (6659/6659), y sus propias sondas de mutación, de
  R01 a R15, sobre una copia del repositorio.
- **Segunda:** sobre E-78, que se agregó después del primer veredicto, y sobre las regresiones.
  `62_context_bar_consumo` dio 371/371.

La compuerta entera la corrió la sesión que orquestó el cambio, no quien lo construyó ni el
refutador: `37989/37989` con exit 0 antes de E-78, y `38025/38025` con exit 0 después.

**Resultado: 78 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `context_window_size` da `contextLimit`, y de ningún otro lado | sostenido | sí | `62_context_bar_consumo.py` |
| E-02 | Entrada más salida dan `contextTokens` | sostenido | sí | `62_context_bar_consumo.py` |
| E-03 | La caché de `current_usage` no se suma otra vez | sostenido | sí | `62_context_bar_consumo.py` |
| E-04 | `current_usage` solo sin los totales | sostenido | sí | `62_context_bar_consumo.py` |
| E-05 | Sin observación no hay foto ni `Ctx 0%` | sostenido | sí | `62_context_bar_consumo.py`, adaptador y renderizador instalado |
| E-06 | Un tamaño de ventana inválido deja el límite sin resolver | sostenido | sí | `62_context_bar_consumo.py`, seis valores |
| E-07 | Un total inválido no se vuelve 0 ni cae a `current_usage` | sostenido | sí | `62_context_bar_consumo.py`, siete valores y NaN |
| E-08 | El `cost` del stdin no cambia el libro ni la línea | sostenido | sí | `62_context_bar_consumo.py`; débil, ver abajo |
| E-09 | Los campos de `context_window` solo en `claude_code.py` | sostenido | sí | `62_context_bar_consumo.py`; débil, ver abajo |
| E-10 | Ningún tamaño de ventana escrito en `contabilidad/` | sostenido | sí | `62_context_bar_consumo.py`; débil, ver abajo |
| E-11 | Una foto no suma `tokens.input` | sostenido | sí | `62_context_bar_consumo.py` |
| E-12 | Ni `tokens.output` | sostenido | sí | `62_context_bar_consumo.py` |
| E-13 | Ni la caché | sostenido | sí | `62_context_bar_consumo.py` |
| E-14 | Ni costo | sostenido | sí | `62_context_bar_consumo.py` |
| E-15 | Ni conteos de eventos | sostenido | sí | `62_context_bar_consumo.py` |
| E-16 | Ni avisos de atribución | sostenido | sí | `62_context_bar_consumo.py` |
| E-17 | Gana la última foto, nunca la suma ni la mayor | sostenido | sí | `62_context_bar_consumo.py` |
| E-18 | Diez dibujos iguales, una foto | sostenido | sí | `62_context_bar_consumo.py` |
| E-19 | Otra observación, o la misma después de avanzar, es una foto nueva | sostenido | sí | `62_context_bar_consumo.py`, el caso A → B → A |
| E-20 | La conciliación no ve las fotos | sostenido | sí | `62_context_bar_consumo.py` |
| E-21 | 134000 de 200000 es `Ctx 67%` | sostenido | sí | `62_context_bar_consumo.py` |
| E-22 | Sin límite, `Ctx 134k` | sostenido | sí | `62_context_bar_consumo.py` |
| E-23 | Más tokens que ventana: `Ctx 270k`, el diagnóstico, y nunca más de 100% | sostenido | sí | `62_context_bar_consumo.py`, la línea, `--barra` y `--json` |
| E-24 | Ese caso no pinta ni etiqueta | sostenido | sí | `62_context_bar_consumo.py` |
| E-25 | `NORMAL` sin color | sostenido | sí | `62_context_bar_consumo.py` |
| E-26 | 70% es `WARNING`, 69% `NORMAL` | sostenido | sí | `62_context_bar_consumo.py` |
| E-27 | 90% es `ERROR`, 89% `WARNING` | sostenido | sí | `62_context_bar_consumo.py` |
| E-28 | El amarillo es el de `context-bar-colores` | sostenido | sí | `62_context_bar_consumo.py` |
| E-29 | El rojo es el de `context-bar-colores` | sostenido | sí | `62_context_bar_consumo.py` |
| E-30 | `LINEA_SIN_DATOS` no cambia | sostenido | sí | `62_context_bar_consumo.py` |
| E-31 | La instalación crea la política | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log de la compuerta |
| E-32 | La política valida contra su schema | sostenido | sí | `62_context_bar_consumo.py` |
| E-33 | `contextWarningAt` 0.7 | sostenido | sí | `62_context_bar_consumo.py` |
| E-34 | `contextErrorAt` 0.9 | sostenido | sí | `62_context_bar_consumo.py` |
| E-35 | Ningún `softLimit` | sostenido | sí | `62_context_bar_consumo.py` |
| E-36 | Ningún `hardLimit` | sostenido | sí | `62_context_bar_consumo.py` |
| E-37 | La política sola no dibuja `Budget` ni cambia el costo | sostenido | sí | `62_context_bar_consumo.py` |
| E-38 | Instalar no toca una política que ya estaba | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-39 | `-Update` crea la que falta | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-40 | `-Update` no toca una que existe | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-41 | `setup` no pregunta | sostenido | sí | `62_context_bar_consumo.py` |
| E-42 | `setup` muestra el bloque `Context Bar` | sostenido | sí | `62_context_bar_consumo.py` |
| E-43 | `DEFAULT`, `PROJECT`, `MISSING` e `INVALID` en `setup` | sostenido | sí | `62_context_bar_consumo.py` |
| E-44 | Nombra `contextWarningAt` si falta | sostenido | sí | `62_context_bar_consumo.py` |
| E-45 | Nombra `contextErrorAt` si falta | sostenido | sí | `62_context_bar_consumo.py` |
| E-46 | Solo `presupuesto --context-defaults` agrega umbrales | sostenido | sí | `62_context_bar_consumo.py`; la parte de `-Update`, por el log |
| E-47 | Ese comando no agrega plata | sostenido | sí | `62_context_bar_consumo.py` |
| E-48 | `ACTIVA` no es "lista" | sostenido | sí | `62_context_bar_consumo.py` |
| E-49 | Sin límite, dice por qué | sostenido | sí | `62_context_bar_consumo.py` |
| E-50 | Sin umbrales, los nombra, y solo esos | sostenido | sí | `62_context_bar_consumo.py` |
| E-51 | Con todo resuelto, dice que está lista | sostenido | sí | `62_context_bar_consumo.py` |
| E-52 | La inconsistencia del proveedor se ve | sostenido | sí | `62_context_bar_consumo.py` |
| E-53 | `NO_COLOR` en el proceso real se ve | sostenido | sí | `62_context_bar_consumo.py` |
| E-54 | Una señal de vida vieja dice `SIN VERIFICAR` y no cambia el estado | sostenido | sí | `62_context_bar_consumo.py`, también contra el `bienvenida.py` de `27cd551` |
| E-55 | `verbose` no muestra el prompt | sostenido | sí | `62_context_bar_consumo.py` |
| E-56 | Ni un secreto | sostenido | sí | `62_context_bar_consumo.py` |
| E-57 | Sin `NO_COLOR`, `ENABLED` | sostenido | sí | `62_context_bar_consumo.py` |
| E-58 | Con `NO_COLOR=1`, `DISABLED_NO_COLOR` | sostenido | sí | `62_context_bar_consumo.py` |
| E-59 | Con `NO_COLOR=` vacía, también | sostenido | sí | `62_context_bar_consumo.py` |
| E-60 | Seis claves y ningún número | sostenido | sí | `62_context_bar_consumo.py` |
| E-61 | La señal de 1.1.0 cumple el contrato nuevo | sostenido | sí | `62_context_bar_consumo.py` |
| E-62 | PowerShell 5.1 dibuja `Ctx NN%` | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-63 | Git Bash también | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-64 | Una sola línea no vacía | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-65 | La señal lleva la huella y `1.2.0` | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-66 | De 1.1.0 a 1.2.0: `RELOAD_REQUIRED` y después `ACTIVE` | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log; débil, ver abajo |
| E-67 | La primera observación usable da `Ctx NN%` | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-68 | Sin `setup`, sin `-Update` y sin tocar la política | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-69 | La doc separa `Ctx` de `Tok` | sostenido | sí | `62_context_bar_consumo.py` |
| E-70 | Después de compactar, `Ctx` baja y `Tok` sube | sostenido | sí | `62_context_bar_consumo.py` |
| E-71 | 70% y 90% son defaults del harness, no normas | sostenido | sí | `62_context_bar_consumo.py` |
| E-72 | `context-bar-colores` sigue en verde | sostenido | sí | `53_context_bar.py` 502/502 y la 54 en el log |
| E-73 | El Bloque 4 sigue en verde, salvo las cuatro aserciones pisadas | sostenido | sí | `30_b4` 868/868, `53` 502/502 y `30-contabilidad-instalador` en el log |
| E-74 | La compuerta sale 0 | sostenido | no consta | `Invoke-Tests.ps1`, `38025/38025` |
| E-75 | La instalación dice los umbrales y no promete un porcentaje | sostenido | sí | `62-context-bar-consumo-instalador.ps1`, por el log |
| E-76 | La fuente de contexto, en `verbose` | sostenido | sí | `62_context_bar_consumo.py` |
| E-77 | El porcentaje del proveedor se guarda y no pisa los tokens | sostenido | sí | `62_context_bar_consumo.py` |
| E-78 | La política, en `verbose`, con el criterio de `setup` | sostenido | sí | `62_context_bar_consumo.py` (segunda pasada) |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

La marca `sí` sale de 67 mutaciones sobre copias del repositorio, hechas por el constructor el
30-09-2026: 63 de una sustitución, dos dobles para E-55 y E-56, y cuatro para E-78. El detalle está
en `## Cómo se verifica` de la spec. El refutador hizo las suyas aparte, también sobre una copia: de
R01 a R15 en la primera pasada, y cuatro para E-78 en la segunda.

Trece escenarios dicen "por el log": E-31, E-38 a E-40, E-62 a E-68, E-74 y E-75. Se sostienen con la
corrida de la compuerta, no con una corrida del grupo PowerShell hecha por el refutador. El conteo
del grupo en el log (78) coincide con las aserciones del archivo, así que corrieron los dos shells.

La latencia que pedía la spec, medida por el refutador con `tests/medir_barra.py` y un umbral de
400 ms:

| | p50 | con un mensaje nuevo |
|---|---|---|
| Antes, en `27cd551`, sin `context_window` | 119 ms | 147-148 ms |
| Después | 121-130 ms | 153-156 ms |

## Lo que la verificación encontró y no habría encontrado un test verde

1. **`harness --verbose` no decía qué política había.** Lo afirmaban la decisión "`DEFAULT` quiere
   decir el contenido de la plantilla" y `docs/contabilidad.md`, pero ningún escenario se lo pedía a
   `verbose`. Se agregó E-78 después del primer veredicto, y lo resuelve la misma función que usa
   `setup`.
2. **Tres choques con tests que ya existían, vistos en la construcción.**
   - E-13 de `30_b4` no admite ninguna clave `rateTable` en un JSON instalado, así que la plantilla va
     sin ella.
   - `colores E-20` pedía `1.1.0`, contra el `1.2.0` de E-65.
   - Cuatro aserciones contradecían a la spec.

   La spec se precisó, con la fecha, y el refutador lo comprobó: las versiones de `27cd551` de 30 y
   53 fallan contra el código nuevo en exactamente esas cinco aserciones, y en ninguna otra.
3. **Dos defectos del producto que salieron de ver los tests en rojo.** Los parámetros de
   `contrato.foto` se llamaban como los campos del proveedor, y E-09 los agarró.
   `presupuesto --context-defaults` con una plantilla sin umbrales tiraba un `KeyError`, y ahora sale
   con 2 y dice por qué.
4. **Sembrar la política cambia un evento del Bloque 4, no el resumen.** Un costo que reporta el
   proveedor pasa a `COST_UNRESOLVED` con `apiEquivalentEstimated`, en lugar de `PRICING_UNAVAILABLE`
   con `null`. El costo del resumen y su lista `unresolved` salen iguales, y no contradice ningún
   escenario de `bloque-4-contabilidad-de-ejecucion`.

## Lo que queda abierto, anotado y no escondido

Queda en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en *The Context Bar consumption change closed
with two literal-ban tests and six uncovered edges*:
- **E-09 y E-10 son prohibiciones de literales, y se esquivan.** Un `2 * 10 ** 5` o un nombre de
  campo partido en dos dejan el grupo en verde. La defensa real es de comportamiento: E-06, E-22 y
  E-49.
- **Al pisar E-22 de 53 se perdió el caso de una ventana parcial.** Ningún test cubre un total
  presente y el otro faltando.
- **E-08 no fija la hora de la foto. Lo que la fija es E-19.**
- **E-66 simula 1.1.0** editando la línea de versión. Nunca instala el renderizador de 0.27.0.
- **`current_usage` con ceros, en lugar de `null`, y los dos totales en 0 dibuja `Ctx 0%`.** E-05
  solo cubre `null`.
- **Una foto sin `transcript_path` toma la hora del reloj.**
- **`-Uninstall` deja la política sembrada,** porque no está en el lockfile, y su mensaje no lo dice.
- **`docs/contabilidad.md` sigue diciendo 8.811 bytes para el evento más grande.** Es un número que
  ya estaba viejo antes de este cambio.

Los riesgos de la spec siguen vigentes, y ninguno es un defecto:
- después de un `/compact`, la barra puede mostrar la ventana anterior;
- nuestro `Ctx` no coincide con el porcentaje de Claude Code;
- el libro crece con cada ventana nueva.

## Lo que ningún test cubre y se mira con los ojos

Es la observación de una sesión real que pide la spec. **No se hizo todavía.** La tiene que hacer
alguien que no construyó, en un proyecto descartable, y anotarla acá con la fecha:
1. instalar o actualizar, abrir Claude Code y producir al menos una respuesta;
2. mirar la barra y correr `dev-harness.py harness --verbose`;
3. confirmar que la señal de vida dice si el ANSI quedó habilitado;
4. ver `Ctx NN%` y `Tok … in / … out` juntos;
5. cruzar los umbrales de forma controlada y ver los colores;
6. si el proveedor manda un límite inconsistente, ver que la barra falla a la vista.
