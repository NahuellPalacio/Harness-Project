# Verificación — ES0902 Vu8: los perfiles respetan los roles asignados

**Estado:** cerrado · **Fecha:** 25-09-2026 · **Versión:** 0.24.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 25-09-2026,
en **tres pasadas**:
- **La primera** dejó 59 sostenidos y 2 contradichos: E-29 y E-49.
- **La segunda** dejó 59 sostenidos y 3 contradichos: E-29, E-51 y E-51b.
- **La tercera** fue la final, porque para cortar el ciclo se reemplazaron las tres respuestas
  parciales por una sola regla (la 8 de la spec). Dejó los 62 sostenidos.

En las tres corrió `-k 56_` y sondeó con scripts propios, sin tocar el repositorio. La última corrida
dio `481/481`. La compuerta completa la corrió quien construyó, antes de la pasada final:
`35779/35779`, EXIT=0.

**Resultado: 62 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

Cada `E-nn` es el `VU8-nn` del paquete con el mismo número. `E-51b` salió de la primera refutación.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu8`, en la fila y en todo resultado | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e01_la_clave` |
| E-02 | `applicationRolesPresent`, `user-profile-role-enforcement-required` y `role-profile-consistency` están exactos en la matriz, el registro de controles y el módulo | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e02_los_ids` |
| E-03 | La fila declara `dev-security` y `dev-backend`, en ese orden | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e03_los_dos_agentes` |
| E-04 | No hay ningún agente, skill, review ni señal nuevos, y `ALGORITMOS` sigue en diez | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e04_nada_nuevo` |
| E-05 | Una evidencia legible `APPLICATION_ROLES: PRESENT` enciende la señal | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e05_un_modelo_de_roles_enciende` |
| E-06 | Un `APPLICATION_DATABASE_SCHEMA` con los roles en la base la enciende | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e06_roles_en_la_base` |
| E-07 | Un `IDENTITY_PROVIDER_CONFIGURATION` con grupos o claims la enciende | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e07_roles_por_claims_o_grupos` |
| E-08 | Un `SOURCE_CODE` que dice `ABSENT` porque no hay enum `Role` no apaga la señal | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e08_sin_enum_role_no_apaga` |
| E-09 | Una evidencia autoritativa `ABSENT`, sola, apaga la señal y da `NOT_APPLICABLE` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e09_una_ausencia_autoritativa_apaga` |
| E-10 | El vacío, una evidencia débil, o un `ABSENT` con algo ilegible o con una superficie registrada dan `UNRESOLVED` y `APPLICABILITY_UNRESOLVED` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e10_lo_incompleto_no_resuelve` |
| E-11 | La fuente resuelta sale en la salida con su `sourceRef` y la evidencia que la sostiene | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e11_la_fuente_se_registra` |
| E-12 | Un `NAMING_CONVENTION` o un `SOURCE_CODE` que nombra la fuente no la resuelve | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e12_la_fuente_no_sale_de_un_nombre` |
| E-13 | Sin fuente, o con dos fuentes autoritativas distintas, da `ROLE_ASSIGNMENT_SOURCE_UNRESOLVED` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e13_sin_fuente` |
| E-14 | Un `AUTHENTICATION_SUCCESS` no resuelve la fuente ni dice nada de acceso | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e14_autenticar_no_es_la_fuente` |
| E-15 | Un `ROLE_PROFILE_MAPPING` citado resuelve el acceso esperado del mapping | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e15_el_mapeo_resuelve_lo_esperado` |
| E-16 | Un rol llamado `admin` sin mapeo no tiene acceso esperado, y el módulo no tiene ninguna lista de nombres de rol | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e16_el_nombre_del_rol_no_define_permisos` |
| E-17 | Sin mapeo, o con un rol de la fuente que ningún mapping cubre, da `ROLE_PROFILE_MAPPING_UNRESOLVED` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e17_sin_mapeo` |
| E-18 | El módulo no nombra ningún framework, anotación ni claim, y dos implementaciones distintas con la misma evidencia dan el mismo resultado | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e18_ningun_framework` |
| E-19 | Un modelo de grupos, uno de claims y uno de conjuntos de permisos llegan a `PASS` con la misma forma de evidencia | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e19_grupos_claims_y_permisos` |
| E-20 | Lo esperado igual a lo efectivo da `CONSISTENT` y `PASS` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e20_igual_es_consistente` |
| E-21 | Una operación protegida de más, permitida por el servidor, da `OVER_PRIVILEGED_PROFILE` y falla | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e21_una_operacion_de_mas` |
| E-22 | Un alcance de datos de más, permitido por el servidor, da `OVER_PRIVILEGED_PROFILE` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e22_un_alcance_de_datos_de_mas` |
| E-23 | Una operación esperada que el servidor niega da `UNDER_PRIVILEGED_PROFILE` y falla | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e23_una_operacion_de_menos` |
| E-24 | La `severity` de la evidencia no cambia ningún estado: un `UNDER` leve falla igual que un `OVER` grave | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e24_la_severidad_no_es_el_resultado` |
| E-25 | Un mapping inconsistente hace fallar el agregado aunque los demás cumplan | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e25_un_mapping_inconsistente_tumba_el_agregado` |
| E-26 | Un botón de administración escondido, solo, no prueba que se niegue una operación protegida: queda sin resolver | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e26_un_boton_escondido_no_prueba_nada` |
| E-27 | Con el cliente negando y el servidor permitiendo, da `DIRECT_ACCESS_BYPASSES_ROLE` y falla | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e27_el_acceso_directo_saltea_el_rol` |
| E-28 | Con el servidor negando la operación al rol que no debe tenerla, cumple | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e28_el_servidor_rechaza` |
| E-29 | La guarda del cliente y la del servidor salen como evidencia separada, y cuando hay servidor, manda el servidor | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e29_cliente_y_servidor_por_separado` |
| E-30 | Una opción de presentación local, no protegida, se resuelve con evidencia del cliente sola, y una diferencia ahí —mostrada sin esperarla o escondida esperándola— no falla | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e30_una_opcion_de_presentacion_local` |
| E-31 | Dos roles con operaciones `x` e `y` no dan `x ∪ y` sin su propio mapeo | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e31_no_se_suman` |
| E-32 | Tampoco dan `x ∩ y` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e32_no_se_intersecan` |
| E-33 | Tampoco dan el perfil del rol "más alto" | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e33_no_gana_el_mas_alto` |
| E-34 | Con la semántica resuelta y el mapeo propio del conjunto, cumple | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e34_la_semantica_del_proyecto` |
| E-35 | Sin semántica sostenida da `MULTI_ROLE_PROFILE_UNRESOLVED` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e35_semantica_desconocida` |
| E-36 | Un rol revocado vigente, sin semántica sostenida, no hace `FAIL` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e36_no_se_inventa_la_propagacion` |
| E-37 | Con la semántica resuelta, un rol revocado vigente dentro de la ventana cumple | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e37_la_ventana_documentada` |
| E-38 | Sin semántica sostenida da `ROLE_CHANGE_PROPAGATION_UNRESOLVED` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e38_semantica_de_cambio_desconocida` |
| E-39 | Con la semántica resuelta, un rol revocado vigente más allá de la ventana falla | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e39_un_rol_revocado_mas_alla_de_la_ventana` |
| E-40 | El `PASS` de C1 no pone en `PASS` a Vu8 | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e40_c1_no_es_vu8` |
| E-41 | El `PASS` de Vu8 no pone en `PASS` a C1 | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e41_vu8_no_es_c1` |
| E-42 | Un `TOKEN_CLAIM_PRESENCE`, solo, no resuelve ni cumple nada | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e42_un_claim_no_prueba_vu8` |
| E-43 | El `PASS` de Vu5 no pone en `PASS` a Vu8 | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e43_vu5_no_es_vu8` |
| E-44 | Un `INPUT_VALIDATION` no cuenta como acceso | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e44_validar_no_es_autorizar` |
| E-45 | Evidencia estática de configuración y de código del servidor sostiene un `PASS` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e45_evidencia_estatica` |
| E-46 | Tests unitarios y de integración de autorización sostienen un `PASS` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e46_tests_de_autorizacion` |
| E-47 | Una prueba autorizada en QA con identidades sintéticas sostiene un `PASS` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e47_prueba_autorizada_en_qa` |
| E-48 | Se llega a `PASS` sin ninguna prueba en runtime | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e48_sin_cuenta_real` |
| E-49 | Lo que la regla de salida compartida (`controles/lib/evidencia.py`) reconoce como credencial no sale en la salida, la unidad ni el libro, y `testIdentityRef` no sale nunca | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e49_ninguna_credencial_sale` |
| E-50 | Una prueba en `PRD`, con una cuenta privilegiada real, destructiva, sin identidades sintéticas, no autorizada o con credenciales registradas da `ROLE_PROFILE_TEST_UNSAFE` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e50_una_prueba_insegura` |
| E-51 | Una prueba insegura no es `PASS` ni `FAIL`, también cuando dice que hay acceso de más o de menos, citada o no | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e51_insegura_no_es_pass_ni_fail` |
| E-51b | Una evidencia citada con `outcome` `UNAVAILABLE`, `INCONCLUSIVE` o `REFUTED` impide el `PASS` y no hace `FAIL`, diga lo que diga | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e51b_lo_citado_que_no_se_puede_leer` |
| E-52 | Un mapping sin resolver impide el `PASS` aunque los demás cumplan | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e52_un_mapping_sin_resolver` |
| E-53 | Una superficie sin fuente impide el `PASS` aunque otra la tenga | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e53_una_superficie_sin_fuente` |
| E-54 | La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en NFC | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e54_el_mismo_resultado` |
| E-55 | La trazabilidad `ES0902 / 6.2 / 6 / Vu8` viaja en todo resultado y en `rules.Vu8` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e55_la_trazabilidad` |
| E-56 | La salida pasada por `seguridad.resultado` y `desde_regla` entra como `RULE_EVALUATION` de `ES0902.Vu8` al mismo libro, y Vu8 está en `authorization-roles` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e56_entra_al_libro_de_siempre` |
| E-57 | `reporte_seguridad/` no tiene ningún archivo nuevo y no hay un segundo libro | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e57_ningun_libro_nuevo` |
| E-58 | Un plan con Vu8 aplicable en una unidad de trabajo compila a una sola unidad de `ES0902.Vu8` por alcance, con una skill de `dev-security` o `dev-backend` | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e58_una_unidad_por_regla_y_alcance` |
| E-59 | Un `PASS` o un `FAIL` del check, traducido por `para_refutacion`, cierra la unidad sin refutador | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e59_un_check_concluyente_no_llama_al_refutador` |
| E-60 | La unidad pendiente lleva solo el alcance declarado, y un veredicto de otra regla o con evidencia fuera del alcance se rechaza | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e60_la_refutacion_no_sale_del_alcance` |
| E-61 | El `PASS` de Vu8 no mueve el estado oficial de seguridad | sostenido | sí | `56_es0902_vu8_perfiles_y_roles.py`, `test_e61_no_es_la_aprobacion_oficial` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno. El rojo
> de los 62 salió de más de setenta mutaciones, restauradas y con `__pycache__` purgado. Las del
> arreglo de cada pasada se volvieron a ver en rojo antes de la pasada siguiente, y el refutador
> repitió las del predicado único por su cuenta.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-49 probaba la regla de salida que existe, no la del escenario.** El test usaba un JWT, que es
   justo el único token que reconoce `controles/lib/evidencia.py`. Con un `glpat-` en
   `testIdentityRef`, o con una contraseña sin nada que la marque, el valor salía tal cual en la
   salida y en `rules.Vu8`. Por decisión del usuario, E-49 se angostó a lo que la regla compartida
   reconoce, y `testIdentityRef` dejó de salir. El límite quedó clavado en verde, y el arreglo de la
   lib es un cambio aparte.
2. **Un cliente no citado bloqueaba el PASS** en una operación que el servidor ya había decidido.
   Eso contradecía "manda el servidor" (E-29).
3. **La tabla hacía fallar una diferencia de presentación local.** El check del paquete, §6, dice lo
   contrario. Se reescribió la tabla, y E-30 lo afirma.
4. **Una prueba insegura, no citada, que negaba algo esperado dejaba pasar el PASS**, y su gemela
   segura no lo dejaba. Es el patrón "lo que dice que no pasa por la misma compuerta" (E-51).
5. **Un item citado con `outcome` `REFUTED` o `INCONCLUSIVE` se descartaba en silencio.** Es el
   escenario nuevo E-51b. El mismo hueco está en Vu6 y Vu7.
6. **En la segunda pasada, las tres respuestas a "¿este item dice una falla?" divergían.** El bloqueo
   miraba solo `ACCESS`, lo ilegible no miraba el servidor y las pruebas quedaban fuera de lo
   ilegible. De ahí salieron dos contradichos nuevos (E-51 con un rol revocado; E-51b con una prueba
   segura ilegible) y la regla 8: un solo predicado, `_dice_falla`, para los tres lugares.

## Lo que queda abierto, anotado y no escondido

Todo vive en `Pendientes/Fix-Harness/PENDIENTES-FH.md`:
- **`controles/lib/evidencia.py` no redacta tokens con prefijo de proveedor.** Hasta que se amplíe, un
  `glpat-` en `sourceRef`, en un id o en otro campo libre sale tal cual, también en
  `rules.Vu8.evidence`. Es la mitad angostada de E-49.
- **Vu6 y Vu7 dejan pasar un item citado con `outcome` ilegible.** Vu8 lo cerró para sí como E-51b.
- **Un mapping que la evidencia nombra y el registro no tiene.** Es la nota de la tercera pasada:
  un item del servidor legible, no citado, que nombra una superficie registrada y un mapping que no
  está en el registro no bloquea el PASS, y una prueba insegura con el mismo contenido sí. No va en
  la dirección peligrosa, y ningún escenario dice qué hacer ahí.

## Lo que ningún test cubre y se mira con los ojos

- **Que un proyecto real llegue a `PASS`.** Hacen falta una matriz de acceso autoritativa, la
  semántica de varios roles y la de cambio de rol. Lo esperable, hoy, es que un proyecto real quede
  sin resolver.
- **Que `dev-refutador` reciba una unidad de Vu8 y la conteste acotada.** La suite prueba el
  compilador y el registro de veredictos, no una corrida del modelo. Es el pendiente de 0.23.0 sobre
  una corrida real de `refutation-unit/1.0`.
