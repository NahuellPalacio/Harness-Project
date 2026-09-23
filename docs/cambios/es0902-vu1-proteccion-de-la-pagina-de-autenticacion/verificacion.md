# Verificación — ES0902 Vu1: captcha o bloqueo de usuario, en cada página de autenticación y con evidencia

**Estado:** cerrado, con dos contradichos documentados · **Fecha:** 23-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **tres pases**. Los tres corrieron `python tests/correr.py -k 44_es0902` y la compuerta completa
`.\tests\Invoke-Tests.ps1`, sin nadie tocando el árbol; la del tercero: `29086/29086` y
`29336/29336`, EXIT=0. El tercero fue el pase final por regla de la casa: desde la tercera pasada se
corta con reglas unificadoras, y lo que queda contradicho cierra documentado.

**Resultado: 42 escenarios sostenidos, 2 contradichos (E-39, E-42), 0 leídos, 0 sin sustento.**

## Los veredictos

Todos los tests están en `tests/casos/44_es0902_vu1_proteccion_de_autenticacion.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es `ES0902.Vu1`, en la fila y en todo resultado | sostenido | sí | `test_e01_la_clave_es_es0902_vu1` |
| E-02 | La única señal es `authenticationPagePresent`, la que el check produce | sostenido | sí | `test_e02_la_senal_es_authentication_page_present` |
| E-03 | Agente, policy y check con sus ids exactos, en matriz, registro y módulo | sostenido | sí | `test_e03_los_ids_de_agente_policy_y_check` |
| E-04 | Ningún agente, skill ni review nuevos | sostenido | sí | `test_e04_no_se_inventa_nada` |
| E-05 | La señal sale del inventario de C1 y enciende la fila | sostenido | sí | `test_e05_la_senal_sale_del_inventario_de_c1` |
| E-06 | El login delegado al proveedor enciende la señal | sostenido | sí | `test_e06_la_pagina_del_proveedor_enciende` |
| E-07 | Lo no interactivo con autoridad apaga; lo débil o delegado, no | sostenido | sí | `test_e07_lo_no_interactivo_con_autoridad_apaga` |
| E-08 | Lo que no consta no apaga; una superficie sin resolver deja la cobertura sin resolver | sostenido | sí | `test_e08_lo_que_no_consta_no_apaga` |
| E-09 | Una página que cumple no tapa a otra | sostenido | sí | `test_e09_una_pagina_no_tapa_a_otra` |
| E-10 | La página vieja o secundaria entra | sostenido | sí | `test_e10_la_pagina_vieja_entra` |
| E-11 | Captcha activo solo satisface | sostenido | sí | `test_e11_captcha_solo` |
| E-12 | Bloqueo activo solo satisface | sostenido | sí | `test_e12_bloqueo_solo` |
| E-13 | Los dos activos satisfacen | sostenido | sí | `test_e13_los_dos` |
| E-14 | Es una `o`, en las dos combinaciones | sostenido | sí | `test_e14_es_una_o` |
| E-15 | Los dos inactivos es `FAIL`; uno sin declarar o contradicho, no | sostenido | sí | `test_e15_ninguno_activo_es_fail` |
| E-16 | La capacidad del proveedor no aprueba | sostenido | sí | `test_e16_la_capacidad_del_proveedor_no_aprueba` |
| E-17 | La capacidad de librería o framework no aprueba | sostenido | sí | `test_e17_la_capacidad_de_libreria_no_aprueba` |
| E-18 | Un WAF solo no satisface | sostenido | sí | `test_e18_waf` |
| E-19 | Un límite por IP solo no satisface | sostenido | sí | `test_e19_limite_por_ip` |
| E-20 | MFA solo no satisface | sostenido | sí | `test_e20_mfa` |
| E-21 | La complejidad de contraseña sola no satisface | sostenido | sí | `test_e21_complejidad_de_contrasena` |
| E-22 | Bots, throttling, cuotas, huella; la equivalencia evita el `FAIL` y no aprueba | sostenido | sí | `test_e22_bots_y_equivalencias` |
| E-23 | No se inventa una cantidad de intentos | sostenido | sí | `test_e23_no_se_inventa_una_cantidad_de_intentos` |
| E-24 | No se inventa una duración de bloqueo | sostenido | sí | `test_e24_no_se_inventa_una_duracion` |
| E-25 | No se inventa un umbral de captcha | sostenido | sí | `test_e25_no_se_inventa_un_umbral_de_captcha` |
| E-26 | El umbral de la evidencia sale tal cual y no es normativo | sostenido | sí | `test_e26_el_umbral_de_la_evidencia_pasa_como_no_normativo` |
| E-27 | La página del proveedor sale de C1; una evidencia sirve a varias páginas | sostenido | sí | `test_e27_una_evidencia_del_proveedor_sirve_a_varias_paginas` |
| E-28 | A la página del proveedor no se le pide la aplicación | sostenido | sí | `test_e28_a_la_pagina_del_proveedor_no_se_le_pide_la_aplicacion` |
| E-29 | OIDC configurado no es Vu1; la frase de la fuente se conserva | sostenido | sí | `test_e29_oidc_configurado_no_es_vu1` |
| E-30 | `PASS` de C1 no es `PASS` de Vu1 | sostenido | sí | `test_e30_c1_no_es_vu1` |
| E-31 | `PASS` de Vu1 no es `PASS` de C1 | sostenido | sí | `test_e31_vu1_no_es_c1` |
| E-32 | Una prueba en `PRD` no cuenta; el módulo no puede ejecutar nada | sostenido | sí | `test_e32_en_produccion_no` |
| E-33 | Sin identidad de prueba dedicada no cuenta | sostenido | sí | `test_e33_sin_identidad_dedicada_no` |
| E-34 | La prueba autorizada en QA con identidad dedicada sostiene | sostenido | sí | `test_e34_la_prueba_autorizada_sostiene` |
| E-35 | Las cuatro condiciones inseguras | sostenido | sí | `test_e35_las_cuatro_condiciones_inseguras` |
| E-36 | No poder probar no es `FAIL`, tampoco cuando la prueba dice inactivo | sostenido | sí | `test_e36_no_poder_probar_no_es_fail` |
| E-37 | El registro se instala vacío y cierra sus cuatro capas | sostenido | sí | `test_e37_el_registro_se_instala_vacio` |
| E-38 | La evidencia se ata por `surfaceId`; una entrada ajena no deja apagar | sostenido | sí | `test_e38_la_evidencia_se_ata_por_surface_id` |
| E-39 | Ningún secreto se guarda ni se repite | **contradicho** | sí | `test_e39_ningun_secreto` |
| E-40 | Todas las páginas tienen que pasar | sostenido | sí | `test_e40_todas_tienen_que_pasar` |
| E-41 | Una página en `FAIL` pone todo en `FAIL` | sostenido | sí | `test_e41_una_en_fail_es_fail` |
| E-42 | Una página sin resolver, o evidencia ilegible sobre ella, impide el `PASS` | **contradicho** | sí | `test_e42_una_sin_resolver_impide_el_pass` |
| E-43 | La misma evidencia da el mismo resultado, en cualquier orden | sostenido | sí | `test_e43_la_misma_evidencia_el_mismo_resultado` |
| E-44 | La trazabilidad `ES0902 / 6.2 / 6 / Vu1` viaja por todos los caminos | sostenido | sí | `test_e44_la_trazabilidad_viaja` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno: los
> cuarenta y cuatro se vieron en rojo con una pasada de mutaciones, y lo que agregó cada pase se vio
> en rojo contra la versión anterior del check.

## E-39, el escenario contradicho

```
details "app:password=hunter2"          PASS, y el texto sale tal cual
details "env/DB_PASSWORD=hunter2"       PASS, y el texto sale tal cual
details "ci-job:api_key=abc123"         PASS
details "realm:token=abc123"            PASS
surfaceId "app:password=hunter2abc"     sale en el resultado y en la señal
```

**Causa.** La forma de credencial empieza con `(?<![:/\w-])`, que se puso para no cerrar el
`:secret:` de un ARN de un gestor de secretos, que es la forma natural de un
`dedicatedTestIdentityRef`. El mismo lookbehind deja afuera una clave pegada a un `:` o una `/`
anterior. Todo lo demás de E-39 se sostiene: la regla de salida única (`_depurar`) cubre
`detectedSurfaces`, ids del catálogo, errores de schema, claves del registro y el inventario de C1.

**Decisión.** Cierra contradicho. Distinguir `realm:token=abc` de `arn:…:secret:nombre` sin volver a
cerrar los textos legítimos que abrió el tercer pase necesita una regla sobre el **valor**, no sobre
la clave, y eso es otra iteración del detector. Queda en `PENDIENTES-FH.md`. La defensa principal
sigue siendo el schema cerrado: una clave `password` o `token` no entra al registro.

## E-42, el escenario contradicho

```
surfaceId "trámites-login", INACTIVE mal formada sin citar     PASS
surfaceId "trámites-login", INACTIVE repetida sin citar        PASS
surfaceId 'log"in', INACTIVE mal formada sin citar             PASS
```

**Causa.** La regla 2 del tercer pase busca el `surfaceId` dentro de `json.dumps(evidencia)`, y
`json.dumps` escapa lo que no es ASCII y las comillas: la búsqueda no encuentra el id. Con ids ASCII
la regla funciona, y lo no citado nunca hace `FAIL`.

**Decisión.** Cierra contradicho. El arreglo es buscar sobre `json.dumps(…, ensure_ascii=False)` o
recorrer los textos de la evidencia; es una línea, pero es una pasada más sobre la misma regla, y el
corte se hizo en el tercer pase. Queda en `PENDIENTES-FH.md`, junto con el exceso del lado cerrado
que la misma subcadena produce.

## Los tres pases

| Pase | Resultado | Qué encontró |
|---|---|---|
| 1 | 35 sostenidos, 9 contradichos | Equivalencias sólo de la lista de ocho; el dueño de la página puesto por el registro; literales que nombraban a C1; una prueba insegura que decía inactivo hacía `FAIL` (E-32 a E-36, una causa); una entrada ajena no impedía apagar la señal; secretos con prefijo |
| 2 | 42 sostenidos, 2 contradichos | Secretos por otros campos (`surfaceId`, errores de schema, claves); evidencia ilegible no citada descartada en silencio |
| 3 | 42 sostenidos, 2 contradichos | Las dos reglas unificadoras, salvo sus bordes: prefijo con `:` o `/`, e ids no ASCII |

Entre el segundo y el tercero se escribieron las tres reglas que están en la spec: una regla de salida
para los secretos, lo ilegible que nombra la página impide el `PASS` y lo no citado nunca hace `FAIL`,
y la contradicción simétrica entre registro y evidencia.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Lo que dice que no se leía distinto de lo que dice que sí.** Una prueba de intentos fallidos en
   producción, sin autorización o sin identidad dedicada no aprobaba, y sí hacía `FAIL` cuando decía
   "inactivo". Es exactamente la asimetría que el paquete prohíbe: no poder probar no es incumplir.
2. **El registro ponía lo que el inventario no decía.** Con `credentialEntryDelegated` en `null`, el
   dueño de la página salía del registro de Vu1 y abría la puerta a evidencia de la aplicación.
3. **La señal se podía apagar con una entrada que decía que había página.**
4. **Quien arma el registro elegía qué contradicción se leía:** una evidencia inactiva no citada no
   contaba, ni repetida ni mal formada.
5. **La salida repetía secretos** por `surfaceId`, errores de schema y claves, y la primera versión de
   la forma de credencial cerraba textos legítimos como `passwordPolicy:` y `tokenLifespan=`.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- E-39: la forma de credencial con prefijo `:` o `/`.
- E-42: la búsqueda del `surfaceId` sobre el JSON escapado, y el bloqueo de más por subcadena
  (`ciudadano` bloqueada por evidencia mal formada de `ciudadano-v2`).
- Una equivalencia con `value: SUPPORTED` evita el `FAIL`: es el valor de capacidad que el resto del
  módulo rechaza (fuera de la letra del tercer pase).
- El campo de "efectos esperados conocidos" que el schema provisto no tiene, ya anotado antes de
  verificar.
- El registro vive en `reglas/` y se sobrescribe en cada `-Update`, como los de O2, C1 y C2.

## Lo que ningún test cubre y se mira con los ojos

- Que la evidencia real de un proveedor —la configuración de protección contra fuerza bruta de un
  realm, un captcha condicional— se deje escribir en el catálogo con las clases que este cambio
  eligió. La tabla de clases es del harness, no del estándar.
- Que nadie "arregle" el registro vacío declarando `ACTIVE` sin evidencia: toda corrida real hoy da
  `AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED`, y es lo correcto.
