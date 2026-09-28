# Verificación — ES0902 Vu9: control de uso de lo público sin autenticación

**Estado:** cerrado · **Fecha:** 27-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` entre el
26-09-2026 y el 27-09-2026, en **tres pasadas**:
- **La primera** dejó 61 sostenidos y 1 contradicho (E-25: un camino que no nombra ninguna superficie
  igual las cubría), más cinco hallazgos contra el texto (H-1 a H-5).
- **La segunda** dejó 61 sostenidos y 1 contradicho (E-46: con un control compartido, lo ilegible no
  pesaba igual en todas sus formas), más tres hallazgos (N-1 a N-3).
- **La tercera** fue la final. Dejó los 62 sostenidos y tres hallazgos que solo cambian cuál sin
  resolver se informa (F-1 a F-3).

En las tres corrió `-k 58_es0902`, la compuerta completa y sondeó con scripts propios, sin tocar el
repositorio. La última corrida dio `425/425` y la compuerta `36581/36581`, EXIT=0.

**Resultado: 62 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

Cada `E-nn` es el `VU9-nn` del paquete con el mismo número.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu9`, en la fila y en todo resultado. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e01_*` |
| E-02 | `unauthenticatedPublicInterfacePresent`, `public-interface-abuse-control-required` y… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e02_*` |
| E-03 | No hay ningún agente, skill, review ni señal nuevos, `ALGORITMOS` sigue en diez, y con el resultado del… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e03_*` |
| E-04 | Una operación de API pública sin autenticación, en evidencia legible, enciende la señal. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e04_*` |
| E-05 | Una funcionalidad web pública sin autenticación la enciende. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e05_*` |
| E-06 | Un `STATIC_ASSET_EXPOSURE` que dice `PRESENT`, solo, no la enciende. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e06_*` |
| E-07 | Un `PUBLIC_DNS_RECORD` que dice `PRESENT`, solo, no la enciende. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e07_*` |
| E-08 | Una funcionalidad con `readOnly: true` la enciende igual, y una superficie de solo lectura sigue en alcance. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e08_*` |
| E-09 | Un inventario `INCOMPLETE`, o ninguno, deja la superficie sin resolver… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e09_*` |
| E-10 | Una superficie en alcance con `controls: []` da `ABUSE_CONTROL_MISSING` y falla. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e10_*` |
| E-11 | Una superficie protegida no tapa otra sin control: el agregado falla. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e11_*` |
| E-12 | Una superficie que el inventario entero nombra y el registro no tiene impide el `PASS`, una en alcance que… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e12_*` |
| E-13 | Un control en la aplicación, sostenido y en el camino, llega a `PASS`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e13_*` |
| E-14 | Un control en el gateway llega a `PASS` si el camino lo prueba. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e14_*` |
| E-15 | Un control en el WAF llega a `PASS` si el camino lo prueba. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e15_*` |
| E-16 | Un control en el router de OpenShift llega a `PASS` si el camino lo prueba. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e16_*` |
| E-17 | Un control que no es rate limiting llega a `PASS`: el módulo no nombra ningún mecanismo. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e17_*` |
| E-18 | Sin CAPTCHA se llega a `PASS`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e18_*` |
| E-19 | Sin WAF se llega a `PASS`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e19_*` |
| E-20 | El módulo no tiene ningún número de pedidos, cuota ni concurrencia, y el mismo control con otro límite… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e20_*` |
| E-21 | Un botón deshabilitado, solo, no es un control: no hay `PASS`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e21_*` |
| E-22 | Un temporizador en JavaScript, solo, tampoco. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e22_*` |
| E-23 | Un origen alcanzable por detrás del control da `ABUSE_CONTROL_BYPASS_PRESENT` y falla. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e23_*` |
| E-24 | Un control configurado sin evidencia de camino no llega a `PASS`, y uno que el camino no atraviesa no… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e24_*` |
| E-25 | Un item citado que no nombra el control ni la superficie no sostiene nada, un camino que no lista la… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e25_*` |
| E-26 | Sin evidencia de mitigación del consumo excesivo no hay `PASS`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e26_*` |
| E-27 | Una mitigación del consumo excesivo contradicha da `EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED` y no falla. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e27_*` |
| E-28 | Sin evidencia de mitigación del consumo automatizado no hay `PASS`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e28_*` |
| E-29 | Una mitigación del consumo automatizado sin sostener da `AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED` y no… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e29_*` |
| E-30 | Una cuota del gateway, sin CAPTCHA, sostiene la mitigación automatizada. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e30_*` |
| E-31 | Una sola evidencia sostiene las dos mitigaciones. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e31_*` |
| E-32 | Sin evidencia de estabilidad da `SERVICE_STABILITY_EVIDENCE_UNRESOLVED`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e32_*` |
| E-33 | El módulo no tiene ningún SLA ni porcentaje. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e33_*` |
| E-34 | Una configuración acotada sostiene la estabilidad. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e34_*` |
| E-35 | Una prueba de carga acotada en QA sostiene la estabilidad. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e35_*` |
| E-36 | Un `PERFORMANCE_TEST_REPORT` en verde, solo, no cierra Vu9. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e36_*` |
| E-37 | El `PASS` de Vu9 no cambia el resultado de ninguna otra regla de ES0902 y la salida no dice nada de… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e37_*` |
| E-38 | La evidencia de DEV no sostiene un registro de QA, HML ni PRD. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e38_*` |
| E-39 | Las huellas de despliegue de la evidencia usada salen en la salida. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e39_*` |
| E-40 | Se llega a `PASS` con evidencia estática sola, sin ninguna prueba en runtime. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e40_*` |
| E-41 | Una prueba autorizada, acotada, en QA, con datos sintéticos, sostiene un `PASS`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e41_*` |
| E-42 | El módulo no genera ni ejecuta pedidos: no importa nada que abra una conexión o un proceso, y no abre nada… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e42_*` |
| E-43 | Una prueba en `PRD` da `PUBLIC_ABUSE_TEST_UNSAFE`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e43_*` |
| E-44 | Una prueba sin datos sintéticos da `PUBLIC_ABUSE_TEST_UNSAFE`. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e44_*` |
| E-45 | Una prueba no autorizada, no acotada, sin condiciones de corte, destructiva o sin ambiente da… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e45_*` |
| E-46 | Una prueba insegura o sin objetivo no es `PASS` ni `FAIL`, citada o no, diga lo que diga | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e46_*` |
| E-47 | El `PASS` de Vu1 no pone en `PASS` a Vu9. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e47_*` |
| E-48 | El `PASS` de Vu9 no pone en `PASS` a Vu1. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e48_*` |
| E-49 | La review de Vu10 en `PASS` no pone en `PASS` a Vu9. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e49_*` |
| E-50 | El `PASS` de Vu9 no pone en `PASS` a Vu10. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e50_*` |
| E-51 | Un plan con Vu9 aplicable compila a una sola unidad de `ES0902.Vu9` por alcance, con una skill de… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e51_*` |
| E-52 | Un `PASS` o un `FAIL` del check, traducido por `para_refutacion`, cierra la unidad sin refutador. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e52_*` |
| E-53 | Un sin resolver deja una sola unidad pendiente con el alcance declarado, y un veredicto de otra regla o… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e53_*` |
| E-54 | Un veredicto guardado no se reusa cuando cambia la huella de la evidencia del alcance. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e54_*` |
| E-55 | Una unidad sin alcance declarado queda bloqueada y no se refuta el repositorio entero. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e55_*` |
| E-56 | La salida pasada por `seguridad.resultado` y `desde_regla` entra como `RULE_EVALUATION` de `ES0902.Vu9` al… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e56_*` |
| E-57 | `operationRef` y `controlType` no salen, así que un dato personal escrito ahí tampoco, y lo que la regla… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e57_*` |
| E-58 | Un item del catálogo con un script o un payload queda mal formado y no sostiene nada, y el registro no… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e58_*` |
| E-59 | Un control faltante o salteado en una superficie hace fallar el agregado aunque las demás cumplan. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e59_*` |
| E-60 | Una dimensión sin resolver en una superficie impide el `PASS` aunque las demás cumplan. | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e60_*` |
| E-61 | La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en NFC, y un id que… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e61_*` |
| E-62 | La trazabilidad `ES0902 / 6.2 / 6 / Vu9` viaja en todo resultado y en `rules.Vu9`, y el `PASS` de Vu9 no… | sostenido | sí | `58_es0902_vu9_control_de_uso_publico.py`, `test_e62_*` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 62 se vieron en rojo
> con un script de unas ochenta mutaciones, repetido después de cada pasada con mutaciones para cada
> corrección.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Citar no era nombrar (E-25, H-3, N-3).** Un item citado que no nombraba ni el control ni la
   superficie sostenía la existencia, las dimensiones y el camino; un camino que nombraba solo el
   control cubría todas las superficies del control compartido. El test de E-25 elegía, para su caso
   negativo, un camino que nombraba otra superficie: la entrada donde el sistema no podía fallar.
2. **Lo ilegible pesaba distinto según su forma (H-1, E-46).** Un `ABSENT` mal formado bloqueaba y el
   mismo con `outcome: INCONCLUSIVE` dejaba pasar; con un control compartido, pasaba lo mismo para un
   item que nombraba la otra superficie. Se unificó en una sola regla (la 2 de la spec).
3. **Un segundo paso de bloqueo reemplazaba un sin resolver anterior (H-2, N-1).** Una prueba insegura
   que hablaba de estabilidad convertía un camino faltante en `PUBLIC_ABUSE_TEST_UNSAFE`.
4. **El inventario entero podía no nombrar la superficie (H-4)**, y **los campos libres
   `operationRef` y `controlType` sacaban un DNI o un script a la salida (H-5)**: ahora no salen.
5. **El estado se elegía por el orden de los pasos y no por la lista de la spec (N-2).**
6. **`seguridad.py` ya tenía un `_vu9` de la línea base** que convertía todo sin resolver del check en
   `NON_COMPLIANT`. No lo encontró el refutador sino quien construyó, al primer test de integración;
   se resolvió cediéndole la palabra al check sin tocar la forma vieja.

## Lo que queda abierto, anotado y no escondido

- **F-1 a F-3**, en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, bajo "ES0902 Vu9 can name the wrong
  open state when an unreadable test explains part of a gap": solo cambian cuál sin resolver se
  informa, nunca dan `PASS` ni `FAIL`.
- El token con prefijo de proveedor que `controles/lib/evidencia.py` no redacta, ya anotado: vale
  también para Vu9 en los ids.

## Lo que ningún test cubre y se mira con los ojos

- Que un proyecto real pueda llenar el registro: inventario entero, evidencia del camino por
  superficie y las tres dimensiones. Lo esperable es que casi todo quede sin resolver.
- Que el catálogo de clases (`GATEWAY_CONFIGURATION`, `NETWORK_TOPOLOGY`, …) alcance para describir la
  infraestructura real del GCBA, con OpenShift y sus rutas.
