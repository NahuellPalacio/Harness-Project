# Verificación — ES0902 Vu4: una sesión inactiva vence sola, aparte del token de OpenID

**Estado:** cerrado · **Fecha:** 23-09-2026 · **Versión:** 0.21.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **dos pases**. Los dos corrieron `python tests/correr.py -k 49_es0902` y la compuerta completa
`.\tests\Invoke-Tests.ps1` con el árbol quieto. El segundo dio `597/597` y `31413/31413`, EXIT=0, y
además `-k 47_es0902` (Vu3) `266/266` y `-k 46_es0902` (Vu2) `324/324`, porque el arreglo de E-49
amplió la redacción compartida.

**Resultado: 61 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

`E-nn` es `VU4-nn` del pedido. E-58..E-61 los agrega la spec.

## Los veredictos

Todos los tests están en `tests/casos/49_es0902_vu4_vencimiento_por_inactividad.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu4`, en la fila y en todo resultado | sostenido | sí | `test_e01_la_clave` |
| E-02 | `sessionPresent`, `session-inactivity-timeout-required` y `session-inactivity-timeout` están exactos en la… | sostenido | sí | `test_e02_los_ids` |
| E-03 | No hay ningún agente, skill ni review nuevo, y `ALGORITMOS` sigue en diez | sostenido | sí | `test_e03_nada_nuevo` |
| E-04 | Una sesión de aplicación autenticada en el registro pone la señal en `TRUE`, la cita, y pasada por… | sostenido | sí | `test_e04_una_sesion_autenticada_enciende` |
| E-05 | Una sesión `TOKEN_BASED_APPLICATION_SESSION` de browser enciende la señal | sostenido | sí | `test_e05_una_sesion_por_tokens_en_el_browser` |
| E-06 | Una sesión de una app móvil autenticada enciende la señal | sostenido | sí | `test_e06_una_app_movil` |
| E-07 | Una evidencia de backend sin estado, o de login delegado a OIDC, no apaga la señal | sostenido | sí | `test_e07_sin_estado_u_oidc_no_apaga` |
| E-08 | Evidencia autoritativa de que no hay sesión de aplicación en ninguna superficie, con los registros vacíos… | sostenido | sí | `test_e08_sin_sesion_con_autoridad_apaga` |
| E-09 | Con autenticación presente y la semántica de sesión sin establecer, la señal es `UNRESOLVED` y el check da… | sostenido | sí | `test_e09_con_autenticacion_y_sin_semantica` |
| E-10 | Las superficies salen del inventario de C1, leído con su cargador, y una superficie cuya señal de Vu3 es… | sostenido | sí | `test_e10_las_superficies_son_las_de_c1` |
| E-11 | Una sesión de backoffice declarada en el registro se evalúa aunque la ciudadana cumpla, y aparece en… | sostenido | sí | `test_e11_el_backoffice_se_evalua` |
| E-12 | Una superficie de C1 con sesión y sin ninguna entrada en el registro da `SESSION_COVERAGE_UNRESOLVED` | sostenido | sí | `test_e12_una_superficie_sin_entrada` |
| E-13 | El vencimiento de la aplicación y el del access token salen por separado en la sesión, y una evidencia del… | sostenido | sí | `test_e13_el_access_token` |
| E-14 | Lo mismo con el refresh token | sostenido | sí | `test_e14_el_refresh_token` |
| E-15 | Lo mismo con el SSO del proveedor | sostenido | sí | `test_e15_el_sso_del_proveedor` |
| E-16 | Con `NOT_CONFIGURED` y una referencia de token, citado y establecido, da `TOKEN_TIMEOUT_ONLY`, que es `FAIL` | sostenido | sí | `test_e16_solo_el_token_es_fail` |
| E-17 | Un `valueRef` igual a la referencia del access token no aprueba: da `TOKEN_TIMEOUT_ONLY` | sostenido | sí | `test_e17_el_valor_del_access_token` |
| E-18 | Una evidencia de que venció la sesión de Keycloak, sola, no aprueba | sostenido | sí | `test_e18_el_vencimiento_de_keycloak` |
| E-19 | Un vencimiento independiente, configurado, con su semántica y con su comportamiento evidenciado, cumple la… | sostenido | sí | `test_e19_un_vencimiento_independiente_cumple` |
| E-20 | El módulo no tiene ninguna duración: ninguna constante ni literal numérico de minutos o segundos decide un… | sostenido | sí | `test_e20_ninguna_duracion` |
| E-21 | `CONFIGURED` con `valueRef` nulo da `SESSION_INACTIVITY_TIMEOUT_UNRESOLVED`, y `UNRESOLVED` en el estado… | sostenido | sí | `test_e21_sin_valor_o_sin_estado` |
| E-22 | El `valueRef` sale tal cual en la sesión evaluada | sostenido | sí | `test_e22_el_valor_sale_tal_cual` |
| E-23 | Ninguna duración evidenciada da `FAIL` por corta o por larga | sostenido | sí | `test_e23_ninguna_duracion_hace_fail` |
| E-24 | Una observación de que el movimiento del mouse reinicia el reloj, sin política citada, deja… | sostenido | sí | `test_e24_el_mouse` |
| E-25 | Lo mismo con el scroll | sostenido | sí | `test_e25_el_scroll` |
| E-26 | Lo mismo con el polling en segundo plano | sostenido | sí | `test_e26_el_polling` |
| E-27 | Lo mismo con el refresh del token | sostenido | sí | `test_e27_el_refresh_del_token` |
| E-28 | Lo mismo con un heartbeat | sostenido | sí | `test_e28_el_heartbeat` |
| E-29 | Una política del proyecto citada, que define la actividad (incluso si dice que el refresh del token… | sostenido | sí | `test_e29_una_politica_citada_resuelve` |
| E-30 | `activitySemantics` en `UNRESOLVED`, o `DEFINED` sin `sourceRef` citado y legible, da… | sostenido | sí | `test_e30_sin_semantica` |
| E-31 | Con `evidenceMode: CONFIGURATION` y una evidencia de configuración como única cita, la sesión no cumple | sostenido | sí | `test_e31_la_configuracion_sola` |
| E-32 | `SESSION_REJECTED` citado con una evidencia de comportamiento que lo establece cumple | sostenido | sí | `test_e32_session_rejected` |
| E-33 | `REAUTHENTICATION_REQUIRED` en las mismas condiciones cumple | sostenido | sí | `test_e33_reauthentication_required` |
| E-34 | `NEW_SESSION_REQUIRED` en las mismas condiciones cumple | sostenido | sí | `test_e34_new_session_required` |
| E-35 | `OLD_INACTIVE_SESSION_STILL_USABLE` es `INACTIVE_SESSION_REMAINS_USABLE` y `FAIL` | sostenido | sí | `test_e35_la_sesion_vieja_sigue_sirviendo` |
| E-36 | Una `UI_OBSERVATION` del login más una evidencia citada de que el endpoint protegido acepta la sesión… | sostenido | sí | `test_e36_la_pantalla_no_tapa_al_recurso` |
| E-37 | Un `CLIENT_TIMER` o `enforcementLayer: frontend` sin evidencia de comportamiento en el recurso no aprueba | sostenido | sí | `test_e37_el_reloj_del_cliente` |
| E-38 | Dos entradas de la misma superficie para dos roles se evalúan cada una con su política, y salen las dos en… | sostenido | sí | `test_e38_dos_roles_dos_entradas` |
| E-39 | La sesión ciudadana cumplida y la de administración en `FAIL` dan `FAIL` | sostenido | sí | `test_e39_la_ciudadana_no_tapa_a_la_de_administracion` |
| E-40 | Un `SESSION_ROLE_SCOPE` citado que nombra un rol sin entrada da `SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED` | sostenido | sí | `test_e40_un_rol_sin_entrada` |
| E-41 | `PASS` de Vu3 no es `PASS` de Vu4: con el cierre cumplido y sin vencimiento, Vu4 no aprueba | sostenido | sí | `test_e41_vu3_no_es_vu4` |
| E-42 | `PASS` de Vu4 no es `PASS` de Vu3 | sostenido | sí | `test_e42_vu4_no_es_vu3` |
| E-43 | `PASS` de C1 no es `PASS` de Vu4 | sostenido | sí | `test_e43_c1_no_es_vu4` |
| E-44 | `PASS` de Vu4 no es `PASS` de C1 | sostenido | sí | `test_e44_vu4_no_es_c1` |
| E-45 | Ningún literal operativo del módulo exige cerrar el SSO del proveedor, y una sesión cumple con el SSO del… | sostenido | sí | `test_e45_no_se_exige_cerrar_el_sso` |
| E-46 | Una prueba en `PRD` no cuenta y da `SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE` | sostenido | sí | `test_e46_en_produccion_no` |
| E-47 | Una prueba con `realUserAccount: true` no cuenta | sostenido | sí | `test_e47_con_una_cuenta_real_no` |
| E-48 | Una prueba autorizada en QA con identidad dedicada sostiene la sesión | sostenido | sí | `test_e48_con_identidad_dedicada_en_qa` |
| E-49 | Nada con forma de credencial sale: una cookie, un id de sesión, un access o refresh token, un código de… | sostenido | sí | `test_e49_ningun_secreto`, `test_e49_una_contrasena_en_castellano_o_corta`, `test_e49_un_id_como_clave_de_diccionario` |
| E-61 | Una sesión cuya `surfaceRef` no está en el inventario de C1 impide el `PASS` con `SESSION_COVERAGE_UNRESOLVED` | sostenido | sí | `test_e61_fuera_del_inventario_y_la_observacion` |
| E-50 | Una prueba con `productionTimeoutWeakened: true` no cuenta | sostenido | sí | `test_e50_el_timeout_de_produccion_debilitado` |
| E-51 | Sin autorización, sin identidad, en otro ambiente o con secretos registrados, da… | sostenido | sí | `test_e51_las_condiciones_inseguras` |
| E-52 | Una prueba insegura o sin objetivo no es `FAIL`, también cuando dice `OLD_INACTIVE_SESSION_STILL_USABLE` | sostenido | sí | `test_e52_no_poder_probar_no_es_fail` |
| E-53 | Una sesión en `FAIL` hace `FAIL` el agregado | sostenido | sí | `test_e53_una_sesion_en_fail` |
| E-54 | Una sesión sin resolver impide el `PASS` | sostenido | sí | `test_e54_una_sin_resolver_impide_el_pass` |
| E-55 | La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en NFC | sostenido | sí | `test_e55_el_mismo_resultado` |
| E-56 | La trazabilidad `ES0902 / 6.2 / 6 / Vu4` viaja en todo resultado, y la unidad de trabajo lleva `rules.Vu4`… | sostenido | sí | `test_e56_la_trazabilidad` |
| E-57 | La salida del check, pasada por `seguridad.resultado` y `reporte_seguridad.productores.desde_regla`, entra… | sostenido | sí | `test_e57_entra_al_libro_como_cualquier_regla` |
| E-58 | Una evidencia ilegible que nombra la sesión, citada o no, impide el `PASS`, también cuando el `evidenceId`… | sostenido | sí | `test_e58_lo_ilegible_que_nombra_la_sesion` |
| E-59 | El bloqueo es uno solo para todas las ramas: una prueba insegura que dice… | sostenido | sí | `test_e59_un_solo_bloqueo` |
| E-60 | El registro vacío instalado valida contra el schema, y una clave de más en cualquier capa no valida | sostenido | sí | `test_e60_el_schema_cerrado` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 61 la declaran `sí`:
> 63 mutaciones en el primer armado y, para E-49 y E-61, los tests nuevos vistos fallar contra el
> código anterior al arreglo.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-49, pase 1:** una contraseña con la clave en castellano o corta (`contraseña=`, `clave=`,
   `pass=`, `passphrase=`) salía sin redactar por los cuatro destinos. `SECRETOS` solo conocía
   `password|passwd|pwd`. Se alineó con la regla E-03b del reporte de seguridad, y eso amplía
   también la redacción de Vu3: ahora redacta más.
2. **E-49, pase 1:** un id con forma de credencial salía como **clave** de un diccionario
   (`coverage.rolesWithoutPolicy`), mientras el mismo texto quedaba redactado en `reason`. La
   función `depurar` recorría los valores y no las claves. Ahora redacta las claves también, con
   sufijos deterministas que nunca funden dos claves.
3. **Tres lecturas del builder que la spec no respaldaba del todo**, que se resolvieron enmendando
   la spec:
   - una falla posterior le gana a un paso anterior sin resolver;
   - una sesión fuera del inventario de C1 dejaba el agregado en `PASS` con el inventario vacío;
   - un ítem que se declaraba observación y política a la vez resolvía la semántica.

   Las dos últimas son E-61.

## Lo que queda abierto, anotado y no escondido

- **E-49 se enmendó después de cerrar**, el 24-09-2026, por decisión del usuario. La regla 6 de
  Vu5 cambió la redacción compartida de `controles/lib/evidencia.py`. Ahora, después de `pass` o de
  una palabra en castellano (`contraseña`, `contrasenia`, `clave`), un espacio solo no es separador.
  Así "la clave del trámite es obligatoria" sale entera, y `clave hunter2abc` sale sin redactar. El
  refutador de Vu5 lo encontró contra la letra de E-49 (sonda `p8`). Los tests de E-49 no tenían
  formas con espacio solo, y siguen en verde.

- **Vu1 y Vu2 tienen su propia copia de los ayudantes de evidencia**, así que la redacción ampliada
  no los alcanza. Ya está en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en el ítem de los ayudantes
  que Vu3 movió a `controles/lib/evidencia.py`.
- **Una superficie que se llama literalmente `[redactado]-2`** sale igual que una clave redactada, y
  en la salida no se distinguen. No se funde con ninguna, que es lo que pide la letra.
- **La divergencia de agentes con el paquete** queda declarada en la spec: la matriz dice
  `dev-security` y `dev-backend`, y el usuario decidió el 23-09-2026 no migrarla.

## Lo que ningún test cubre y se mira con los ojos

Que un proyecto real declare sus sesiones, sus roles y la prueba de vencimiento en la forma que el
check espera. La suite prueba con entradas armadas.
