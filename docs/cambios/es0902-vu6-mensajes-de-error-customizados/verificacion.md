# Verificación — ES0902 Vu6: todo mensaje de error que ve un consumidor está customizado

**Estado:** cerrado · **Fecha:** 24-09-2026 · **Versión:** 0.21.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 24-09-2026
en **dos pases**. Cada uno corrió la compuerta completa una sola vez, con el árbol quieto. En el
segundo, `-k 52_es0902` dio `654/654` y la compuerta `33558/33558`, EXIT=0.

**Resultado: 60 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

`E-nn` es `VU6-nn` del pedido; E-54..E-60 los agrega la spec. Después del primer pase se tocaron
tres escenarios, y la spec lo dice en cada uno:
- E-28 se amplió;
- E-58 se angostó a la regla de bloqueo de Vu3 y Vu5;
- E-60 se aclaró.

## Los veredictos

Todos los tests están en `tests/casos/52_es0902_vu6_mensajes_de_error.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu6`, en la fila y en todo resultado | sostenido | sí | `test_e01_la_clave` |
| E-02 | `userFacingErrorPresent`, `custom-error-messages-required` y `custom-error-message-compliance` están… | sostenido | sí | `test_e02_los_ids` |
| E-03 | No hay ningún agente, skill ni review nuevo, y `ALGORITMOS` sigue en diez | sostenido | sí | `test_e03_nada_nuevo` |
| E-04 | Una pantalla de error del frontend evidenciada enciende la señal | sostenido | sí | `test_e04_una_pantalla_de_error_enciende` |
| E-05 | Un payload de error de API evidenciado enciende la señal | sostenido | sí | `test_e05_un_payload_de_api_enciende` |
| E-06 | Un error expuesto del móvil o del backoffice enciende la señal | sostenido | sí | `test_e06_el_movil_y_el_backoffice_encienden` |
| E-07 | Una evidencia `INTERNAL_LOG`, sola, no enciende la señal | sostenido | sí | `test_e07_un_log_interno_solo_no_enciende` |
| E-08 | Un alcance con superficies sin cubrir y sin ningún error presente da la señal `UNRESOLVED` | sostenido | sí | `test_e08_un_alcance_sin_cubrir` |
| E-09 | Un mensaje controlado por la aplicación, con evidencia de comportamiento, cumple su escenario | sostenido | sí | `test_e09_un_mensaje_controlado_cumple` |
| E-10 | Una página de debug del framework expuesta y evidenciada da `DEFAULT_ERROR_EXPOSED` y `FAIL` | sostenido | sí | `test_e10_la_pagina_de_debug_del_framework` |
| E-11 | Un stack trace expuesto y evidenciado da `RAW_TECHNICAL_ERROR_EXPOSED` y `FAIL` | sostenido | sí | `test_e11_el_stack_trace_expuesto` |
| E-12 | La página por defecto del servidor o de la plataforma, expuesta sin cambios, da `FAIL` | sostenido | sí | `test_e12_la_pagina_por_defecto_del_servidor` |
| E-13 | Una ruta del sistema de archivos expuesta en un error inesperado, evidenciada, da… | sostenido | sí | `test_e13_una_ruta_expuesta` |
| E-14 | Lo mismo con una IP interna | sostenido | sí | `test_e14_una_ip_interna` |
| E-15 | Lo mismo con una excepción de la base o del driver | sostenido | sí | `test_e15_una_excepcion_del_driver` |
| E-16 | Lo mismo con un diagnóstico del contenedor o de la plataforma | sostenido | sí | `test_e16_un_diagnostico_de_la_plataforma` |
| E-17 | Un mensaje customizado que no dice "Ocurrió un error" cumple igual: el módulo no exige ningún texto | sostenido | sí | `test_e17_ningun_texto_se_exige` |
| E-18 | Dos mensajes customizados con textos distintos en castellano dan el mismo resultado | sostenido | sí | `test_e18_dos_textos_en_castellano` |
| E-19 | Un mensaje customizado en inglés da el mismo resultado que uno en castellano | sostenido | sí | `test_e19_ingles_y_castellano` |
| E-20 | Dos payloads customizados con formas JSON distintas dan el mismo resultado | sostenido | sí | `test_e20_dos_formas_json` |
| E-21 | El componente de la pantalla no cambia el resultado | sostenido | sí | `test_e21_el_componente_no_decide` |
| E-22 | Un error de validación customizado con `400` y otro con `422` dan el mismo resultado, y sin contrato… | sostenido | sí | `test_e22_el_codigo_de_error_no_decide` |
| E-23 | Un frontend customizado con la API que expone un stack trace da `FAIL` | sostenido | sí | `test_e23_el_frontend_no_tapa_la_api` |
| E-24 | Una API segura con el backoffice que muestra la página por defecto da `FAIL` | sostenido | sí | `test_e24_la_api_no_tapa_el_backoffice` |
| E-25 | Un escenario cumplido no tapa otro material sin resolver: no da `PASS` | sostenido | sí | `test_e25_un_escenario_no_tapa_otro` |
| E-26 | Una superficie del alcance sin escenario `UNEXPECTED_ERROR` da `ERROR_SURFACE_COVERAGE_UNRESOLVED` | sostenido | sí | `test_e26_sin_el_error_inesperado` |
| E-27 | Un stack trace en un log interno protegido, solo, no hace `FAIL` | sostenido | sí | `test_e27_un_stack_trace_en_el_log` |
| E-28 | Un `INTERNAL_DIAGNOSTIC_FORWARDED` que llega al consumidor de la API da `FAIL`, también cuando su `value`… | sostenido | sí | `test_e28_el_diagnostico_reenviado` |
| E-29 | El texto de una evidencia con un stack trace, una IP y una ruta no aparece en la salida, en la señal, en… | sostenido | sí | `test_e29_ningun_texto_de_evidencia_sale` |
| E-30 | Un cuerpo customizado de un error inesperado con estado `5xx` cumple | sostenido | sí | `test_e30_un_5xx_customizado_cumple` |
| E-31 | Un error inesperado respondido con `2xx`, evidenciado, da `HTTP_ERROR_SEMANTICS_MASKED` y `FAIL` | sostenido | sí | `test_e31_un_error_inesperado_con_2xx` |
| E-32 | Customizar el cuerpo no es enmascarar: un cuerpo customizado con el estado de error intacto no da… | sostenido | sí | `test_e32_customizar_no_es_enmascarar` |
| E-33 | La regla de ES0901 sobre errores HTTP se cita como fuente de apoyo en la salida, y ningún resultado de… | sostenido | sí | `test_e33_es0901_se_cita_y_no_se_evalua` |
| E-34 | Un `ERROR_HANDLER_PRESENCE`, solo, no cumple ningún escenario | sostenido | sí | `test_e34_el_manejador_presente_no_cumple` |
| E-35 | Un `ERROR_HANDLER_MAPPING` que nombra la superficie y el `errorType`, con todos los escenarios cubiertos,… | sostenido | sí | `test_e35_el_mapeo_que_nombra_la_superficie_y_el_tipo` |
| E-36 | `owner: FRAMEWORK_DEFAULT` con evidencia de comportamiento de que la configuración customiza la salida cumple | sostenido | sí | `test_e36_el_framework_customizado_por_configuracion` |
| E-37 | Un `ERROR_HANDLER_MAPPING` que dice que customiza, con una observación citada de que la salida es el stack… | sostenido | sí | `test_e37_el_mapeo_contra_la_observacion` |
| E-38 | Una prueba en QA con un error de validación sintético cuenta | sostenido | sí | `test_e38_una_prueba_en_qa_con_un_error_de_validacion` |
| E-39 | Una prueba con un recurso inexistente o una petición inválida cuenta | sostenido | sí | `test_e39_un_recurso_inexistente_o_una_peticion_invalida` |
| E-40 | Una prueba con `infrastructureOutageInduced: true` o `destructive: true` no cuenta | sostenido | sí | `test_e40_una_caida_o_una_prueba_destructiva` |
| E-41 | Una prueba con `realPersonalData: true` o `realSecrets: true` no cuenta | sostenido | sí | `test_e41_datos_personales_o_secretos_reales` |
| E-42 | Sin autorización, en `PRD`, sin datos sintéticos o con secretos registrados, da `ERROR_MESSAGE_TEST_UNSAFE` | sostenido | sí | `test_e42_las_condiciones_inseguras` |
| E-43 | Una prueba insegura no es `FAIL`, también cuando dice `RAW_TECHNICAL_ERROR_EXPOSED` | sostenido | sí | `test_e43_una_prueba_insegura_no_es_fail` |
| E-44 | El `PASS` de Vu5 no pone en `PASS` a Vu6 | sostenido | sí | `test_e44_el_pass_de_vu5_no_es_el_de_vu6` |
| E-45 | El `PASS` de Vu6 no pone en `PASS` a Vu5 | sostenido | sí | `test_e45_el_pass_de_vu6_no_es_el_de_vu5` |
| E-46 | El `PASS` de Vu6 no pone en `PASS` a Vu7 | sostenido | sí | `test_e46_el_pass_de_vu6_no_es_el_de_vu7` |
| E-47 | El `PASS` de Vu6 no pone en `PASS` a Vu10 | sostenido | sí | `test_e47_el_pass_de_vu6_no_es_el_de_vu10` |
| E-48 | El `PASS` de Vu6 no cambia la aprobación oficial | sostenido | sí | `test_e48_el_pass_de_vu6_no_es_la_aprobacion` |
| E-49 | Una exposición confirmada en cualquier superficie hace `FAIL` el agregado | sostenido | sí | `test_e49_una_exposicion_en_cualquier_superficie` |
| E-50 | Un camino material sin resolver impide el `PASS` | sostenido | sí | `test_e50_un_camino_material_sin_resolver` |
| E-51 | La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en NFC | sostenido | sí | `test_e51_el_mismo_resultado` |
| E-52 | La trazabilidad `ES0902 / 6.2 / 6 / Vu6` viaja en todo resultado, y la unidad lleva `rules.Vu6` con… | sostenido | sí | `test_e52_la_trazabilidad` |
| E-53 | La salida pasada por `seguridad.resultado` y `desde_regla` entra como `RULE_EVALUATION` de `ES0902.Vu6` al… | sostenido | sí | `test_e53_entra_al_libro_como_cualquier_regla` |
| E-54 | El check no decide por palabras: una evidencia cuyo `reference` contiene `java.lang.NullPointerException`… | sostenido | sí | `test_e54_ninguna_palabra_decide` |
| E-55 | Nada con forma de credencial sale, tampoco como clave de un diccionario | sostenido | sí | `test_e55_ningun_secreto` |
| E-56 | Una evidencia ilegible que nombra la superficie o el escenario impide el `PASS`, y un id que no es texto… | sostenido | sí | `test_e56_lo_ilegible_que_nombra_la_superficie_o_el_escenario` |
| E-57 | La falla establecida gana siempre: una exposición citada con el registro en `CUSTOMIZED_SAFE` da el mismo… | sostenido | sí | `test_e57_la_falla_establecida_gana_siempre` |
| E-58 | El bloqueo es uno solo | sostenido | sí | `test_e58_un_solo_bloqueo` |
| E-59 | El registro vacío instalado valida contra el schema, y una clave de más en cualquier capa no valida | sostenido | sí | `test_e59_el_schema_cerrado` |
| E-60 | Una entrada del registro fuera del alcance impide el `PASS` con `ERROR_SURFACE_COVERAGE_UNRESOLVED` | sostenido | sí | `test_e60_una_entrada_fuera_del_alcance` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 60 la declaran `sí`,
> con 64 mutaciones repetidas enteras sobre el código final.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-28.** Un diagnóstico interno reenviado al consumidor terminaba sosteniendo un "mensaje
   customizado" y daba `PASS`, tanto si decía `CUSTOMIZED_SAFE` como si decía solo que había un
   error visible. El test probaba el único caso donde también decía `RAW_TECHNICAL_ERROR_EXPOSED`.
   Ahora un reenviado citado es siempre exposición.
2. **E-58.** La letra decía más que la regla de bloqueo que comparten Vu3 y Vu5. Se angostó el
   escenario a esa regla, y la proposición que salió quedó negada por escrito.
3. **El primer pase de la construcción** encontró un test flojo en E-08: pasaba por
   `senales.producir` y no llegaba a lo que deriva el check.

## Lo que queda abierto, anotado y no escondido

- **`EVIDENCE_INCOMPLETE`** figura en la policy del paquete, pero el check no lo emite. Pasó lo
  mismo en Vu5.
- **El enmascaramiento HTTP solo se juzga para el error inesperado, o con contrato.** Un `404`
  convertido en `200` sin contrato no se detecta, y así lo declara la spec.
- **`19_contexto / E-29` falló una vez en la construcción.** Es el intermitente que ya es el
  pendiente #4, fuera de Vu6.

## Lo que ningún test cubre y se mira con los ojos

Que un proyecto real declare sus superficies de error y pruebe el error inesperado en cada una.
