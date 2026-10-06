# Verificación — La Context Bar con colores

**Estado:** cerrado · **Fecha:** 30-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` en dos
pasadas. La primera, el 29-09-2026, fue sobre los 21 escenarios con la compuerta entera
(`37552/37552`, exit 0). La segunda, el 30-09-2026, fue solo sobre E-21, después de reforzar su
test: `python tests/correr.py -k 53_context_bar` dio 500/500 y la compuerta, 37568/37568 con exit 0.

**Resultado: 21 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `Ctx` en `NORMAL` sin color | sostenido | sí | `53_context_bar.py`, `test_cb_e01_a_e03_ctx_sigue_su_nivel` |
| E-02 | `Ctx` en `WARNING` en amarillo, cerrado con su reset | sostenido | sí | `53_context_bar.py`, igualdad exacta del fragmento |
| E-03 | `Ctx` en `ERROR` en rojo, cerrado con su reset | sostenido | sí | `53_context_bar.py` |
| E-04 | `Budget` en `NORMAL` sin color | sostenido | sí | `53_context_bar.py`, `test_cb_e04_a_e06_budget_sigue_su_nivel` |
| E-05 | `Budget` en `WARNING` en amarillo | sostenido | sí | `53_context_bar.py` |
| E-06 | `Budget` en `ERROR` en rojo | sostenido | sí | `53_context_bar.py` |
| E-07 | La etiqueta `WARNING` en amarillo | sostenido | sí | `53_context_bar.py`, `test_cb_e07_e08_la_etiqueta_final` |
| E-08 | La etiqueta `ERROR` en rojo | sostenido | sí | `53_context_bar.py`, también con el otro nivel en `WARNING` |
| E-09 | Con datos, la línea empieza con `HARNESS` en negrita | sostenido | sí | `53_context_bar.py`, `test_cb_e09_e10_harness_en_negrita_sin_severidad` |
| E-10 | `HARNESS` nunca lleva color de severidad | sostenido | sí | `53_context_bar.py`, con todo en `ERROR` |
| E-11 | Con `NO_COLOR=1`, ni un byte `0x1B` | sostenido | sí | `53_context_bar.py`, en `dibujar` y en el renderizador instalado |
| E-12 | Con `NO_COLOR=` vacía, tampoco | sostenido | sí | `53_context_bar.py`, en `dibujar` y en el renderizador instalado |
| E-13 | La línea sin datos sale idéntica, con colores habilitados | sostenido | sí | `53_context_bar.py`, la constante y el renderizador sin stdin |
| E-14 | La línea sin datos sin ningún `0x1B` | sostenido | sí | `53_context_bar.py` |
| E-15 | `Ctx` en `UNRESOLVED` sin color, con porcentaje y en tokens | sostenido | sí | `53_context_bar.py`, `test_cb_e15_e16_unresolved_no_inventa_color` |
| E-16 | `Budget` en `UNRESOLVED` sin color y sin etiqueta inventada | sostenido | sí | `53_context_bar.py` |
| E-17 | Sin las secuencias, la línea con color es la de `NO_COLOR`, y esa es la escrita a mano | sostenido | sí | `53_context_bar.py`, contra `_LEGADO` |
| E-18 | El orden de los campos, con colores y sin ellos | sostenido | sí | `53_context_bar.py` |
| E-19 | El comando instalado pinta el `ERROR` en rojo en los dos shells | sostenido | sí | `54-context-bar-instalador.ps1:163-174`, `powershell -NoProfile -Command` y `bash -c` |
| E-20 | La señal de vida dice `integrationVersion: "1.1.0"` | sostenido | sí | `53_context_bar.py`, `test_cb_e20_la_senal_dice_la_version_nueva` |
| E-21 | `docs/contabilidad.md` dice qué va en amarillo y en rojo, y que `NO_COLOR` apaga | sostenido | sí | `53_context_bar.py`, `test_cb_e21_la_doc_dice_los_colores` (segunda pasada) |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

La marca `sí` de E-01 a E-18, E-20 y E-21 sale de romper `statusline.py` y `docs/contabilidad.md`
una vez por comportamiento, el 29-09-2026. La de E-19 sale de la primera corrida de la suite, que
traía `NO_COLOR=1` en el entorno. La del test reforzado de E-21 sale de diez mutaciones de
`docs/contabilidad.md` sobre copias, el 30-09-2026: todas lo hicieron fallar.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-21 pasaba con tres palabras sueltas.** El test comprobaba que "amarillo", "rojo" y `NO_COLOR`
   aparecieran en algún lugar de `docs/contabilidad.md`. Cambiar un solo "amarillo" no lo hacía
   fallar, porque la palabra estaba dos veces. Ahora lee solo la sección
   `### La Context Bar, en la terminal de Claude Code`, empareja cada color con su nivel y pide que
   se nombren `Ctx`, `Budget` y la etiqueta, y que `NO_COLOR` apague. Falla si se cruzan los
   colores, si falta cualquiera de las tres cosas pintadas, si se saca la frase de `NO_COLOR` o si se
   la mueve a otra sección.
2. **Ningún escenario de color pasa por el `NO_COLOR=1` del entorno.** Claude Code se lo pone a los
   comandos de sus herramientas, y la suite corrió con esa variable puesta. Se confirmó escenario por
   escenario:
   - E-01 a E-10 y E-15 a E-17 piden `color=True`;
   - E-11 saca la variable y exige que haya `0x1B`;
   - E-13, E-19 y E-20 corren el renderizador con la variable sacada;
   - la rama de E-12 que corre el renderizador instalado recibe `NO_COLOR=""` vacía de verdad en
     Windows.

## Lo que queda abierto, anotado y no escondido

- **Los riesgos de la spec siguen vigentes.** Una consola que no interpreta ANSI muestra `[33m` en
  crudo, y el amarillo sobre fondo claro se lee peor. Los dos se aceptaron en la spec. Ninguno es un
  defecto y ninguno entra a `Pendientes/`.
- **Lo que no se sabe es si Claude Code le pone `NO_COLOR=1` también a la `statusLine`.** Se mira
  con los ojos (abajo). Si pasa, la barra sale sin colores, que es lo correcto con `NO_COLOR`, y se
  anota acá.

## Lo que ningún test cubre y se mira con los ojos

- En una sesión real de Claude Code, con `Ctx` o `Budget` en `WARNING` o en `ERROR`, el fragmento
  se ve en amarillo o en rojo y `HARNESS` en negrita. **No se miró todavía.**
- En esa misma sesión, si la barra sale sin colores con un nivel en alerta: eso quiere decir que
  Claude Code le pasa `NO_COLOR` a la `statusLine`, y se anota acá con la fecha.
