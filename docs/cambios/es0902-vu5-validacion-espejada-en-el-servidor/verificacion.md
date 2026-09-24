# Verificación — ES0902 Vu5: toda validación del cliente está espejada en el servidor

**Estado:** cerrado · **Fecha:** 24-09-2026 · **Versión:** 0.21.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 24-09-2026
en **dos pases**, y los dos corrieron la compuerta completa `.\tests\Invoke-Tests.ps1` con el árbol
quieto. En el segundo:
- `-k 50_es0902` dio `696/696`;
- `-k 49_es0902` (Vu4) dio `597/597`;
- `-k 47_es0902` (Vu3) dio `266/266`;
- `-k 46_es0902` (Vu2) dio `324/324`;
- la compuerta dio `32117/32117`, EXIT=0.

**Resultado: 69 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

`E-nn` es `VU5-nn` del pedido. E-63..E-69 los agrega la spec.

## Los veredictos

Todos los tests están en `tests/casos/50_es0902_vu5_validacion_espejada.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu5`, en la fila y en todo resultado | sostenido | sí | `test_e01_la_clave` |
| E-02 | `clientValidationPresent`, `client-validation-server-mirroring-required` y… | sostenido | sí | `test_e02_los_ids` |
| E-03 | No hay ningún agente, skill ni review nuevo, y `ALGORITMOS` sigue en diez | sostenido | sí | `test_e03_nada_nuevo` |
| E-04 | Una validación explícita del cliente, citada con su evidencia, enciende la señal, y pasada por `senales`… | sostenido | sí | `test_e04_una_validacion_explicita_enciende` |
| E-05 | Una validación declarativa o generada, evidenciada, enciende la señal | sostenido | sí | `test_e05_una_validacion_declarativa_o_generada` |
| E-06 | Un `DEPENDENCY_MANIFEST` con una librería de validación, solo, no enciende la señal | sostenido | sí | `test_e06_una_libreria_sola_no_enciende` |
| E-07 | Evidencia autoritativa de `CLIENT_VALIDATION` en `ABSENT` para todo el alcance, con el registro vacío y la… | sostenido | sí | `test_e07_la_ausencia_autoritativa_apaga` |
| E-08 | Un alcance con clientes sin registro ni ausencia autoritativa, y sin ninguna validación presente, da la… | sostenido | sí | `test_e08_un_alcance_sin_cubrir` |
| E-09 | Solo las validaciones del cliente generan exigencias: el check no tiene ningún camino que parta de una… | sostenido | sí | `test_e09_solo_el_cliente_genera_exigencias` |
| E-10 | Una evidencia de validación que existe solo en el servidor no cambia el resultado | sostenido | sí | `test_e10_lo_que_solo_esta_en_el_servidor_no_cambia_nada` |
| E-11 | Con todas las validaciones del cliente cumplidas y validaciones extra solo en el servidor, da `PASS` | sostenido | sí | `test_e11_las_del_servidor_de_mas_no_impiden_el_pass` |
| E-12 | `required` en el cliente y en el servidor, `EQUIVALENT` y con evidencia de enforcement, cumple | sostenido | sí | `test_e12_required_en_los_dos_lados` |
| E-13 | El cliente exige un valor y el servidor acepta `null`: `SERVER_WEAKER` establecido da… | sostenido | sí | `test_e13_el_servidor_acepta_null` |
| E-14 | Un enum en el cliente y un string libre en el servidor da `FAIL`, igual que E-13 | sostenido | sí | `test_e14_un_enum_contra_un_string_libre` |
| E-15 | Una cota inferior en el cliente y ninguna en el servidor da `FAIL`, igual que E-13 | sostenido | sí | `test_e15_una_cota_inferior_sin_cota` |
| E-16 | Con `maxLength` de 100 en el cliente y 80 en el servidor, declarado `SERVER_STRONGER_COMPATIBLE` y sin… | sostenido | sí | `test_e16_mas_estricto_sin_contrato` |
| E-17 | Lo mismo, con una `CONTRACT_COMPATIBILITY` autoritativa en `COMPATIBLE`, cumple | sostenido | sí | `test_e17_mas_estricto_con_contrato` |
| E-18 | Con `CONTRACT_COMPATIBILITY` en `INCOMPATIBLE`, queda sin resolver y no cumple | sostenido | sí | `test_e18_mas_estricto_con_contrato_en_contra` |
| E-19 | `enforcementStatus: MISSING`, establecido, da `SERVER_VALIDATION_MISSING`, que es `FAIL` | sostenido | sí | `test_e19_missing_establecido` |
| E-20 | `parity: UNRESOLVED` da `VALIDATION_EQUIVALENCE_UNRESOLVED` | sostenido | sí | `test_e20_parity_unresolved` |
| E-21 | Un `FIELD_NAME_MATCH`, solo, no aprueba | sostenido | sí | `test_e21_el_nombre_del_campo` |
| E-22 | Un `DTO_NAME_MATCH`, solo, no aprueba | sostenido | sí | `test_e22_el_nombre_del_dto` |
| E-23 | Un `DEPENDENCY_MANIFEST` de la librería compartida, solo, no aprueba | sostenido | sí | `test_e23_la_libreria_compartida` |
| E-24 | Un `SHARED_SCHEMA_PRESENCE`, solo, no aprueba | sostenido | sí | `test_e24_el_schema_compartido_presente` |
| E-25 | Una evidencia de enforcement que establece `SHARED_SCHEMA_SERVER_EXECUTION` para la operación sostiene la… | sostenido | sí | `test_e25_el_schema_compartido_ejecutado` |
| E-26 | Un `HTML_ATTRIBUTE` `required`, solo, no aprueba | sostenido | sí | `test_e26_el_atributo_required` |
| E-27 | Un `TYPESCRIPT_TYPE`, solo, no aprueba | sostenido | sí | `test_e27_el_tipo_de_typescript` |
| E-28 | Una máscara del cliente con solo `CLIENT_TRANSFORMATION` como evidencia no cumple | sostenido | sí | `test_e28_la_mascara` |
| E-29 | Lo mismo con la sanitización | sostenido | sí | `test_e29_la_sanitizacion` |
| E-30 | Lo mismo con la normalización | sostenido | sí | `test_e30_la_normalizacion` |
| E-31 | Una `NORMALIZATION` del cliente con evidencia de que el servidor valida el dominio ya normalizado cumple | sostenido | sí | `test_e31_la_normalizacion_con_el_dominio_validado` |
| E-32 | Una prueba con `rejectedBy: AUTHORIZATION` no sostiene la validación | sostenido | sí | `test_e32_rechazada_por_autorizacion` |
| E-33 | Una prueba con `responseStatus: 403`, sola, no sostiene la validación, aunque diga `rejectedBy: VALIDATION` | sostenido | sí | `test_e33_un_403_no_es_validacion` |
| E-34 | Una prueba segura con un contexto de prueba autorizado, que llega a la validación y la ve rechazar,… | sostenido | sí | `test_e34_una_prueba_segura_que_llega_a_la_validacion` |
| E-35 | El `PASS` de Vu5 no pone en `PASS` a Vu8: el resultado de Vu8 no cambia | sostenido | sí | `test_e35_el_pass_de_vu5_no_es_el_de_vu8` |
| E-36 | Una prueba directa segura con `INVALID_INPUT_ACCEPTED` da `FAIL`, aunque el registro diga `EQUIVALENT` | sostenido | sí | `test_e36_la_prueba_ve_aceptar_la_entrada_invalida` |
| E-37 | Una prueba directa segura con `INVALID_INPUT_REJECTED` y `rejectedBy: VALIDATION` sostiene la validación | sostenido | sí | `test_e37_la_prueba_ve_rechazar_por_validacion` |
| E-38 | Dos pruebas con mensajes de error distintos a los del cliente dan el mismo resultado: el mensaje no decide | sostenido | sí | `test_e38_el_mensaje_no_decide` |
| E-39 | Un rechazo por validación con `responseStatus` 400, con 422 o sin código da el mismo resultado | sostenido | sí | `test_e39_el_codigo_no_decide` |
| E-40 | Una evidencia citada de que el servidor procesó como válida una entrada mal formada da `FAIL` | sostenido | sí | `test_e40_el_servidor_proceso_como_valida` |
| E-41 | El frontend público cumplido y el backoffice con una validación en `FAIL` dan `FAIL` | sostenido | sí | `test_e41_el_backoffice_no_lo_tapa_el_portal` |
| E-42 | Un cliente móvil se evalúa con sus propias validaciones y sale en `clients[]` | sostenido | sí | `test_e42_el_cliente_movil` |
| E-43 | Lo mismo con un cliente legado | sostenido | sí | `test_e43_el_cliente_legado` |
| E-44 | Un `operationRef` que no está en `interfaces` del contexto de proyecto, o sin contexto, da… | sostenido | sí | `test_e44_el_mapeo_es_una_interfaz_del_contexto` |
| E-45 | Una prueba en `PRD` no cuenta y da `SERVER_VALIDATION_TEST_UNSAFE` | sostenido | sí | `test_e45_en_produccion_no` |
| E-46 | Una prueba en QA con `syntheticValues: true` y el resto seguro cuenta | sostenido | sí | `test_e46_en_qa_con_valores_sinteticos` |
| E-47 | Una prueba con `destructive: true` no cuenta | sostenido | sí | `test_e47_destructiva_no` |
| E-48 | Una prueba con `realPrivilegedData: true` no cuenta, y ninguna condición de la prueba segura exige datos… | sostenido | sí | `test_e48_con_datos_privilegiados_reales_no` |
| E-49 | Sin autorización, sin contexto de prueba, sin valores sintéticos o con secretos registrados, da… | sostenido | sí | `test_e49_las_condiciones_inseguras` |
| E-50 | Una prueba insegura no es `FAIL`, también cuando dice `INVALID_INPUT_ACCEPTED` | sostenido | sí | `test_e50_insegura_no_es_fail` |
| E-51 | Con un resultado de P5 en `PASS` o en `FAIL` en la evidencia, el de Vu5 no cambia | sostenido | sí | `test_e51_p5_no_mueve_a_vu5` |
| E-52 | El `PASS` de Vu5 no pone en `PASS` a P5 | sostenido | sí | `test_e52_el_pass_de_vu5_no_es_el_de_p5` |
| E-53 | Una evidencia citada por Vu5 y por otra regla no copia el resultado final: la otra regla sigue con el suyo | sostenido | sí | `test_e53_una_evidencia_compartida_no_copia_el_resultado` |
| E-54 | El `PASS` de Vu5 no dice nada de la autorización: ningún campo de la salida afirma roles ni permisos | sostenido | sí | `test_e54_vu5_no_dice_nada_de_la_autorizacion` |
| E-55 | El `PASS` de Vu5 no pone en `PASS` a Vu6 | sostenido | sí | `test_e55_el_pass_de_vu5_no_es_el_de_vu6` |
| E-56 | El `PASS` de Vu5 no pone en `PASS` a Vu10 | sostenido | sí | `test_e56_el_pass_de_vu5_no_es_el_de_vu10` |
| E-57 | El `PASS` de Vu5 no cambia la aprobación oficial: C2 y el estado oficial no se mueven | sostenido | sí | `test_e57_el_pass_de_vu5_no_es_la_aprobacion` |
| E-58 | Una validación en `SERVER_VALIDATION_MISSING` o en `SERVER_VALIDATION_WEAKER` hace `FAIL` el agregado | sostenido | sí | `test_e58_una_validacion_en_fail` |
| E-59 | Un mapeo material sin resolver impide el `PASS` | sostenido | sí | `test_e59_un_mapeo_sin_resolver_impide_el_pass` |
| E-60 | La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en NFC | sostenido | sí | `test_e60_el_mismo_resultado` |
| E-61 | La trazabilidad `ES0902 / 6.2 / 6 / Vu5` viaja en todo resultado, y la unidad de trabajo lleva `rules.Vu5`… | sostenido | sí | `test_e61_la_trazabilidad` |
| E-62 | La salida del check, pasada por `seguridad.resultado` y `reporte_seguridad.productores.desde_regla`, entra… | sostenido | sí | `test_e62_entra_al_libro_como_cualquier_regla` |
| E-63 | Nada con forma de credencial sale, tampoco en `constraint.description` ni como clave de un diccionario, en… | sostenido | sí | `test_e63_ningun_secreto` |
| E-64 | Una evidencia ilegible que nombra la validación, citada o no, impide el `PASS`, también cuando el… | sostenido | sí | `test_e64_lo_ilegible_que_nombra_la_validacion` |
| E-65 | El bloqueo es uno solo para todas las ramas | sostenido | sí | `test_e65_un_solo_bloqueo` |
| E-66 | El registro vacío instalado valida contra el schema, y una clave de más en cualquier capa no valida | sostenido | sí | `test_e66_el_schema_cerrado` |
| E-67 | Un cliente del registro que no está en el alcance de C1 ni en `CLIENT_SURFACE_SCOPE` impide el `PASS` con… | sostenido | sí | `test_e67_un_cliente_fuera_del_alcance` |
| E-68 | La falla establecida gana siempre | sostenido | sí | `test_e68_la_falla_establecida_gana_siempre` |
| E-69 | Una entrada del registro sin validaciones no cubre su superficie | sostenido | sí | `test_e69_entrada_vacia_y_estado_informado` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 69 la declaran `sí`.
> La pasada de mutaciones se repitió entera sobre el código final: 69 de 69 en rojo.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-07.** La señal se apagaba aunque una superficie quedara sin cubrir, porque `completa` no
   miraba `sin_cubrir`. El test afirmaba justamente ese caso.
2. **E-10.** Una prueba insegura que nombraba solo una validación del servidor convertía un `PASS`
   en `SERVER_VALIDATION_TEST_UNSAFE`. El test usaba la única clase que ese camino no miraba.
3. **E-13, E-14, E-15 y E-19.** Con la misma evidencia, declarar la falla en el registro daba un
   resultado más blando (sin resolver) que declarar que cumplía (`FAIL`). Se cerró con la regla 3
   de la spec: una falla establecida gana siempre (E-68).
4. **El bloqueo pisaba el orden de los pasos.** Un mapeo sin resolver con una prueba insegura
   informaba el estado de la prueba. Lo cubre E-69.
5. **La regla de salida redactaba prosa y dejaba pasar `contrasenia=`, `pw=` y `pin=`.**

## Lo que queda abierto, anotado y no escondido

- **La regla 5 falla en una combinación que ningún escenario nombra.** Se da con una validación
  mapeada, `enforcementStatus: PRESENT` y `parity: UNRESOLVED` declarado, cuando la única evidencia
  del servidor es una prueba insegura citada. En ese caso se informa `SERVER_VALIDATION_TEST_UNSAFE`,
  con `VALIDATION_EQUIVALENCE_UNRESOLVED` en `states[]`, y la regla dice lo contrario. No cambia
  ningún veredicto, porque el `PASS` sigue impedido. Está en `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
- **La regla 6 cambió la redacción compartida y choca con la letra de E-49 de Vu4.** Una palabra en
  castellano o `pass` seguida solo de un espacio (`clave hunter2abc`) ya no se redacta. La decisión
  está registrada en la verificación de Vu4.
- **`EVIDENCE_INCOMPLETE`** figura en la policy del paquete, pero el check no lo emite, porque
  tampoco está en sus resultados.

## Lo que ningún test cubre y se mira con los ojos

Que un proyecto real declare sus validaciones del cliente y mapee cada una a un `interface_id` del
contexto de proyecto. Sin ese contexto, todo mapeo queda sin resolver.
