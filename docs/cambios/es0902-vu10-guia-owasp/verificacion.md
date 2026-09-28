# Verificación — ES0902 Vu10: la guía OWASP que aplica, revisada y con fuente vigente

**Estado:** cerrado · **Fecha:** 27-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 27-09-2026,
en **tres pasadas y una confirmación acotada**:
- **La primera** dejó 60 sostenidos y 2 contradichos: E-11 (lo ilegible por `outcome` no frenaba el
  `NOT_APPLICABLE`) y E-18 (un `UPDATE_AVAILABLE` de otra clase no le quitaba el `CURRENT`).
- **La segunda** dejó 60 sostenidos, 1 contradicho (E-23: la foto que se declaraba evidencia de punto
  lo sostenía) y 1 sin sustento (E-11: lo mal formado no tenía test).
- **La tercera** fue la final: para cortar el ciclo se escribieron dos reglas que gobiernan todo el
  módulo (lo que sostiene lo decide la clase; lo ilegible pesa en todas sus formas). Dejó 61 sostenidos
  y 1 contradicho: E-10, porque la regla 2 no se había aplicado al activo.
- **La confirmación acotada** revisó E-10, E-24, E-29 y E-44 después de corregirlos y dejó los 62
  sostenidos, sin mover ningún otro escenario.

En todas corrió `-k 59_es0902` y la compuerta, y sondeó con mutaciones y scripts propios en memoria,
sin tocar el repositorio. La confirmación dio `292/292` y `36878/36878`, EXIT=0. Después se agregaron
tres tests de prosa que la confirmación marcó sin cobertura, sin cambiar código: `295/295` y la
compuerta `36881/36881`.

**Resultado: 62 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

Cada `E-nn` es el `VU10-nn` del paquete con el mismo número.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu10`, en la fila y en todo resultado. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e01_*` |
| E-02 | `owaspApplicableAssetPresent`, `dev-security`, `owasp-security-guidance-required` y… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e02_*` |
| E-03 | La fila sigue con `checks: []` y no hay ningún check de Vu10 en `controles/checks/`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e03_*` |
| E-04 | No hay ningún agente ni skill nuevos, y `ALGORITMOS` sigue en diez. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e04_*` |
| E-05 | Un activo `WEB` sostenido enciende la señal y aporta la familia `WEB`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e05_*` |
| E-06 | Un activo `API_OR_WEB_SERVICE` la enciende y aporta su familia. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e06_*` |
| E-07 | Un activo `MOBILE` la enciende y aporta su familia. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e07_*` |
| E-08 | Un activo web con su API aporta las dos familias, y la review necesita las dos. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e08_*` |
| E-09 | Un activo web interno y autenticado cuenta igual. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e09_*` |
| E-10 | Un inventario de activos que no está entero, un tipo sin sostener o un tipo ilegible sobre el activo dan… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e10_*` |
| E-11 | Una ausencia autoritativa de las tres familias, sola, da `NOT_APPLICABLE`, y con algo ilegible sobre la… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e11_*` |
| E-12 | Cada familia aplicable se ata a su foto autoritativa, y la salida lo dice. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e12_*` |
| E-13 | Una edición que solo sostiene `MODEL_KNOWLEDGE` no resuelve la fuente. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e13_*` |
| E-14 | Sin foto, o con `freshness: SOURCE_UNAVAILABLE`, da `OWASP_GUIDANCE_SOURCE_UNAVAILABLE` y nunca `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e14_*` |
| E-15 | Sin frescura sostenida da `OWASP_GUIDANCE_FRESHNESS_UNRESOLVED` y nunca `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e15_*` |
| E-16 | La edición sale en la salida de la familia. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e16_*` |
| E-17 | La fecha, la referencia y la huella de la fuente salen en la salida cuando están. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e17_*` |
| E-18 | Una frescura `UPDATE_AVAILABLE`, de cualquier clase, o una ilegible sobre la fuente, le quita el `CURRENT`… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e18_*` |
| E-19 | Los puntos esperados de una familia son los de su foto. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e19_*` |
| E-20 | El módulo no tiene ninguna lista de puntos ni ids de OWASP, y otra edición con otros puntos llega a `PASS`… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e20_*` |
| E-21 | Un punto repetido, uno que la edición no tiene o uno sin disposición impide el `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e21_*` |
| E-22 | Un punto que falta da `OWASP_GUIDANCE_COVERAGE_INCOMPLETE`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e22_*` |
| E-23 | `REVIEWED_NO_FINDING` con evidencia de punto vale | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e23_*` |
| E-24 | `FINDING_PRESENT` con su hallazgo vale como disposición, y con un hallazgo que el catálogo no tiene, no. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e24_*` |
| E-25 | `NOT_APPLICABLE_WITH_RATIONALE` sin razón no vale. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e25_*` |
| E-26 | `NOT_APPLICABLE_WITH_RATIONALE` sin evidencia tampoco, y la review instalada no trae ninguna disposición… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e26_*` |
| E-27 | Un punto `UNRESOLVED` impide el `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e27_*` |
| E-28 | Una review completa con un hallazgo no es `FAIL`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e28_*` |
| E-29 | Un hallazgo nuevo sale como `FINDING_CREATED` de `ES0902.Vu10` por `desde_hallazgo`, y uno que ya está en… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e29_*` |
| E-30 | La severidad del hallazgo no cambia el estado de la review. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e30_*` |
| E-31 | La confianza viaja en el hallazgo y no cambia el estado de la review. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e31_*` |
| E-32 | Un hallazgo que bloquea sale con `blocking` en el libro, y la review sigue en `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e32_*` |
| E-33 | ASVS no se exige: el módulo no lo nombra y se llega a `PASS` sin él. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e33_*` |
| E-34 | MASVS tampoco. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e34_*` |
| E-35 | SAMM tampoco. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e35_*` |
| E-36 | Ningún scanner: el módulo no nombra ninguno y ninguna clase de evidencia es obligatoria. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e36_*` |
| E-37 | Ningún umbral: el módulo no tiene números de vulnerabilidades, y diez hallazgos siguen en `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e37_*` |
| E-38 | Evidencia de Vu5 sostiene un punto. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e38_*` |
| E-39 | El `PASS` de Vu5 no pone en `PASS` a Vu10, y un `RULE_RESULT` no sostiene un punto. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e39_*` |
| E-40 | Evidencia de Vu8 sostiene un punto. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e40_*` |
| E-41 | El `PASS` de Vu8 no pone en `PASS` a Vu10. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e41_*` |
| E-42 | Evidencia de Vu9 sostiene un punto. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e42_*` |
| E-43 | El `PASS` de Vu9 no pone en `PASS` a Vu10. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e43_*` |
| E-44 | Un hallazgo que dos puntos citan sale una sola vez. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e44_*` |
| E-45 | Vu10 es una review: está registrada como `REVIEW`, con su documento, y la fila no tiene checks. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e45_*` |
| E-46 | Un veredicto `cumple` de la refutación no pone la review en `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e46_*` |
| E-47 | Un punto semántico arma un alcance de una unidad con un punto, un activo y sus rutas, y compila a una sola… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e47_*` |
| E-48 | Un alcance vacío o del repositorio entero se rechaza, y un veredicto con evidencia fuera del alcance también. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e48_*` |
| E-49 | Un veredicto guardado no se reusa cuando cambia la huella de la evidencia. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e49_*` |
| E-50 | El módulo no importa nada que abra una conexión o un proceso, y no escribe archivos. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e50_*` |
| E-51 | Una prueba en `PRD` o destructiva no sostiene nada. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e51_*` |
| E-52 | Una prueba sin objetivo, o no autorizada, deja el punto sin resolver. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e52_*` |
| E-53 | Lo que la regla de salida compartida reconoce como credencial no sale en la salida, la unidad ni el libro,… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e53_*` |
| E-54 | La review completa sin hallazgos da `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e54_*` |
| E-55 | La review completa con un hallazgo registrado puede dar `PASS`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e55_*` |
| E-56 | Una familia aplicable omitida en una review hecha da `FAIL`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e56_*` |
| E-57 | Sin frescura no hay `PASS`, aunque todo lo demás esté completo. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e57_*` |
| E-58 | Un punto material sin resolver da `REVIEW_INCOMPLETE`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e58_*` |
| E-59 | El módulo no llama a ningún modelo: no importa nada fuera de la biblioteca estándar y del harness. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e59_*` |
| E-60 | La misma evidencia da el mismo resultado en cualquier orden, también con ids en NFC. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e60_*` |
| E-61 | La trazabilidad `ES0902 / 6.2 / 6 / Vu10` viaja en todo resultado y en `rules.Vu10`. | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e61_*` |
| E-62 | La salida entra como `RULE_EVALUATION` de `ES0902.Vu10` al libro de siempre, en… | sostenido | sí | `59_es0902_vu10_guia_owasp.py`, `test_e62_*` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 62 se vieron en rojo
> con un script de unas ochenta mutaciones, repetido después de cada pasada con mutaciones para cada
> corrección.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El "no" pasaba por otra compuerta que el "sí" (E-18).** La frescura exigía la clase del registro
   de fuentes también para lo que le quita el `CURRENT`: un `UPDATE_AVAILABLE` de otra clase no pesaba.
2. **Lo ilegible pesaba distinto según su forma (E-11, E-10, E-18).** Mal formado bloqueaba; con un
   `outcome` ilegible, no. Pasó en la señal, en el activo y en la frescura, y terminó en la regla 2.
3. **Lo que un item decía de sí mismo le alcanzaba para sostener (E-23, E-24).** Una foto con
   `GUIDANCE_ITEM_EVIDENCE` revisaba un punto, y un nombre en `findingIds` era un hallazgo. Terminó en
   la regla 1: lo decide la clase.
4. **Tests que elegían la única entrada donde el módulo no podía fallar**: E-18 con el
   `UPDATE_AVAILABLE` desde la única clase aceptada, E-23 con una foto que solo decía ser foto, y
   E-39/E-41/E-43 sin una review de Vu10 al lado.
5. **Un nombre de hallazgo inventado llegaba al libro** aunque el estado ya lo rechazaba: la puerta del
   estado y la del reporte no eran la misma.
6. **`seguridad.py` ya tenía un `_vu10` de la línea base**, y el test E-09 de D3 contaba un solo schema
   de review. No lo encontró el refutador sino quien construyó, al integrar.

## Lo que queda abierto, anotado y no escondido

- Tres bordes de las dos reglas sin escenario, en `Pendientes/Fix-Harness/PENDIENTES-FH.md` bajo
  "ES0902 Vu10 leaves three edges of its two rules without a scenario". El que importa: una foto
  legible de una edición más nueva no le quita el `CURRENT` a la vieja.
- El registro de fuentes no admite las páginas de OWASP, en `Pendientes/Ideas-Harness/PENDIENTES-I.md`
  bajo "Let the source registry hold the OWASP project pages". Hasta entonces casi todo proyecto real
  queda en `OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`.
- La edición de OWASP no entra en la clave de caché de la refutación: escrito en los riesgos de la spec.

## Lo que ningún test cubre y se mira con los ojos

- Que alguien pueda llenar el registro de la review de un proyecto real con las ediciones vigentes de
  OWASP, sus puntos y una disposición con evidencia por punto.
- Que `dev-security` use `alcance_de_punto` para acotar una unidad semántica, en vez de mandar el
  alcance de la unidad de trabajo entera.
