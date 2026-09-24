# Verificación — ES0902 Vu3: cerrar la aplicación o el browser no deja viva la sesión anterior

**Estado:** cerrado · **Fecha:** 23-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **cuatro pases**. Todos corrieron `python tests/correr.py -k 47_es0902` y la compuerta completa
`.\tests\Invoke-Tests.ps1` con el árbol quieto. La corrida del cuarto pase dio `266/266` y
`30216/30216` (250 PowerShell, 29966 Python), EXIT=0. El tercero juzgó E-48 contra una regla
unificadora, y el cuarto fue el pase final, acotado a E-40 más un barrido de regresión.

**Resultado: 50 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

## Los veredictos

Todos los tests están en `tests/casos/47_es0902_vu3_cierre_de_sesion.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu3` | sostenido | sí | `test_e01_la_clave` |
| E-02 | Señal, policy y check con sus ids exactos en matriz, registro y módulo | sostenido | sí | `test_e02_los_ids` |
| E-03 | Ningún agente, skill ni review nuevos | sostenido | sí | `test_e03_nada_nuevo` |
| E-04 | Una sesión autenticada en el browser enciende la señal y la fila | sostenido | sí | `test_e04_una_sesion_en_el_browser_enciende` |
| E-05 | El login delegado a OIDC no apaga la señal | sostenido | sí | `test_e05_oidc_no_apaga` |
| E-06 | Un SPA con sesión por tokens enciende la señal | sostenido | sí | `test_e06_un_spa_con_tokens` |
| E-07 | Sin sesión, con autoridad, apaga; una fuente débil no | sostenido | sí | `test_e07_sin_sesion_con_autoridad_apaga` |
| E-08 | Sin `sessionModel`, la señal es `UNRESOLVED` | sostenido | sí | `test_e08_sin_modelo_no_se_sabe` |
| E-09 | Sesión de la aplicación y del proveedor por separado | sostenido | sí | `test_e09_aplicacion_y_proveedor_por_separado` |
| E-10 | El tiempo de vida del token no es el veredicto | sostenido | sí | `test_e10_el_tiempo_de_vida_del_token` |
| E-11 | No se exige cerrar el SSO del proveedor | sostenido | sí | `test_e11_no_se_exige_el_logout_global` |
| E-12 | Sesión nueva no es sesión vieja | sostenido | sí | `test_e12_sesion_nueva_no_es_sesion_vieja` |
| E-13 | Sin `APPLICATION_WINDOW_CLOSE`, sin resolver | sostenido | sí | `test_e13_la_ventana` |
| E-14 | Sin `BROWSER_CLOSE`, lo mismo | sostenido | sí | `test_e14_el_browser` |
| E-15 | `TAB_CLOSE` no se exige sin evidencia de equivalencia | sostenido | sí | `test_e15_la_pestana_no_se_inventa` |
| E-16 | Los clientes salen de la evidencia del proyecto | sostenido | sí | `test_e16_los_clientes_los_dice_el_proyecto` |
| E-17 | Sin alcance, o con dos que no coinciden, `SUPPORTED_BROWSER_SCOPE_UNRESOLVED` | sostenido | sí | `test_e17_sin_alcance` |
| E-18 | Un botón de logout, solo, no aprueba | sostenido | sí | `test_e18_el_boton_de_logout` |
| E-19 | El logout del proveedor, solo, no aprueba | sostenido | sí | `test_e19_el_logout_del_proveedor` |
| E-20 | `dev-openid-connect` entra por su clase y sostiene el modelo, no el cierre | sostenido | sí | `test_e20_dev_openid_connect_entra_por_su_clase` |
| E-21 | `explicitLogoutEvidenceRefs` es contexto | sostenido | sí | `test_e21_el_logout_es_contexto` |
| E-22 | Una cookie de sesión sola no aprueba | sostenido | sí | `test_e22_la_cookie_de_sesion` |
| E-23 | `sessionStorage` solo no aprueba | sostenido | sí | `test_e23_session_storage` |
| E-24 | `localStorage` solo no reprueba | sostenido | sí | `test_e24_local_storage` |
| E-25 | Un artefacto que restaura la sesión vieja es `FAIL` | sostenido | sí | `test_e25_el_artefacto_que_restaura_la_sesion` |
| E-26 | La sesión del servidor aceptada después del cierre es `FAIL` | sostenido | sí | `test_e26_la_sesion_del_servidor` |
| E-27 | El artefacto rechazado después del cierre cumple | sostenido | sí | `test_e27_el_artefacto_rechazado` |
| E-28 | Login con la API aceptando la sesión vieja es `FAIL` | sostenido | sí | `test_e28_la_pantalla_con_la_api_viva` |
| E-29 | Login con la sesión vieja rechazada puede pasar; la pantalla sola, no | sostenido | sí | `test_e29_la_pantalla_con_la_sesion_rechazada` |
| E-30 | Un intercambio nuevo con sesión nueva no es reusar la vieja | sostenido | sí | `test_e30_una_sesion_nueva_despues_del_sso` |
| E-31 | La sesión vieja que vuelve sin establecerse es `FAIL` | sostenido | sí | `test_e31_la_sesion_vieja_que_vuelve` |
| E-32 | `beforeunload` solo no aprueba | sostenido | sí | `test_e32_beforeunload` |
| E-33 | `unload` solo no aprueba | sostenido | sí | `test_e33_unload` |
| E-34 | `pagehide` solo no aprueba | sostenido | sí | `test_e34_pagehide` |
| E-35 | `sendBeacon` solo no aprueba | sostenido | sí | `test_e35_send_beacon` |
| E-36 | El comportamiento le gana al hook | sostenido | sí | `test_e36_el_comportamiento_gana` |
| E-37 | Una prueba en `PRD` no cuenta; el módulo no ejecuta nada | sostenido | sí | `test_e37_en_produccion_no` |
| E-38 | Una prueba con cuenta real no cuenta | sostenido | sí | `test_e38_con_una_cuenta_real_no` |
| E-39 | Una prueba autorizada en QA con identidad dedicada sostiene | sostenido | sí | `test_e39_con_identidad_dedicada_en_qa` |
| E-40 | Nada con forma de credencial sale; `status_code=` no es secreto | sostenido | sí | `test_e40_ningun_secreto`, `test_e40_un_id_legitimo_no_se_redacta` |
| E-41 | Las condiciones inseguras dan `BROWSER_SESSION_TERMINATION_TEST_UNSAFE` | sostenido | sí | `test_e41_las_condiciones_inseguras` |
| E-42 | Una prueba insegura o sin objetivo no es `FAIL` | sostenido | sí | `test_e42_no_poder_probar_no_es_fail` |
| E-43 | Un timeout por inactividad no reemplaza a Vu3 | sostenido | sí | `test_e43_el_timeout_no_reemplaza` |
| E-44 | `PASS` de Vu3 no es `PASS` de Vu4 | sostenido | sí | `test_e44_vu3_no_es_vu4` |
| E-45 | `PASS` de C1 no es `PASS` de Vu3 | sostenido | sí | `test_e45_c1_no_es_vu3` |
| E-46 | `PASS` de Vu3 no es `PASS` de C1 | sostenido | sí | `test_e46_vu3_no_es_c1` |
| E-47 | Una combinación que cumple no tapa a una que falla | sostenido | sí | `test_e47_una_combinacion_no_tapa_a_otra` |
| E-48 | Una combinación sin resolver, o una evidencia ilegible, impide el `PASS` | sostenido | sí | `test_e48_una_sin_resolver_impide_el_pass`, `test_e48_un_id_que_no_es_texto_es_ilegible`, `test_e48_lo_ilegible_bloquea_igual_en_toda_rama` |
| E-49 | La misma evidencia da el mismo resultado en cualquier orden | sostenido | sí | `test_e49_el_mismo_resultado` |
| E-50 | La trazabilidad viaja en todo resultado y en `rules.Vu3` | sostenido | sí | `test_e50_la_trazabilidad` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los cincuenta la
> declaran `sí`, y los rojos de los tests agregados en los pases 2 a 4 los vio quien construyó.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Pase 1:** E-40, E-48, E-49 y E-50 contradichos. Las cuatro fallas se corrigieron antes del pase 2.
2. **Pase 2, E-48:** un `evidenceId` que era lista o dict hacía caer el check con
   `TypeError: unhashable type: 'list'`, en vez de impedir el `PASS`. Además, la rama
   `NOT_APPLICABLE` ignoraba `blockedBy`, así que un cierre declarado no aplicable pasaba aunque una
   prueba ilegible dijera que la sesión vieja seguía viva. Se arregló con un solo paso de bloqueo
   por el que pasan todas las ramas.
3. **Pase 2, redacción de más:** `es_secreto` redactaba ids legítimos como `session:portal-close`
   o `cookie:check-1`, y la unidad perdía la trazabilidad por id.
4. **Pase 3, E-40:** el ajuste del punto 3 abrió un agujero: un `code=` seguido solo de dígitos
   salía sin redactar. Por decisión del usuario, `code=` y `code:` se redactan siempre, cualquiera
   sea el valor. `zip code=1414` y `http code: 401` dejaron de contar como legítimos, y
   `status_code=` sigue siendo la única excepción.

## Lo que queda abierto, anotado y no escondido

- `sid: x` y `session: x`, con dos puntos, salen enteros. La spec nombra solo `sid=`. Es una
  decisión libre, no un hallazgo.
- La divergencia de E-02 con el paquete sigue declarada en la spec y la decide el usuario.
- Vu1 y Vu2 conservan sus copias de los helpers de evidencia, que Vu3 movió a
  `controles/lib/evidencia.py`. Ya está en `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

## Lo que ningún test cubre y se mira con los ojos

Que un proyecto real declare sus superficies y su evidencia de cierre en la forma que el check
espera. La suite prueba el check con entradas armadas, y ninguna viene de un proyecto real.
