# Verificación — ES0902 C1: OpenID Connect con el Keycloak de DGSEI, por superficie y con evidencia

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 22-09-2026
en **ocho pases**: el primero sobre los cincuenta escenarios, y los siete siguientes acotados a los
que el pase anterior había contradicho o reabierto. En cada pase corrió
`python tests/correr.py -k 41_es0902`; hasta el séptimo corrió además la compuerta completa
`.\tests\Invoke-Tests.ps1`, y el octavo —sobre E-43 sólo— corrió únicamente el archivo 41, porque
en paralelo se integraba ES0902 C2 al repositorio.

**Resultado: 50 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

## Los veredictos

Todos los tests están en `tests/casos/41_es0902_c1_openid_connect.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es `ES0902.C1` | sostenido | sí | `test_e01_la_clave_es_es0902_c1` |
| E-02 | La única señal es `authenticationPresent`, ninguna nueva | sostenido | sí | `test_e02_authentication_present_se_reusa` |
| E-03 | Sin la señal, `APPLICABILITY_UNRESOLVED` | sostenido | sí | `test_e03_sin_la_senal_queda_sin_resolver` |
| E-04 | Con la señal en falso, `NOT_APPLICABLE` | sostenido | sí | `test_e04_con_la_senal_en_falso_no_aplica` |
| E-05 | Los agentes siguen siendo `dev-security` y `dev-integration` | sostenido | sí | `test_e05_los_agentes_primarios` |
| E-06 | Las tres policies, con sus ids literales | sostenido | sí | `test_e06_las_tres_policies` |
| E-07 | Los dos checks y cero reviews | sostenido | sí | `test_e07_los_dos_checks` |
| E-08 | Ningún agente ni skill nuevos | sostenido | sí | `test_e08_ningun_agente_ni_skill_nuevos` |
| E-09 | La policy de D2 no se duplica | sostenido | sí | `test_e09_la_policy_de_d2_no_se_duplica` |
| E-10 | El check de D2 se reusa y no se corre | sostenido | sí | `test_e10_el_check_de_d2_se_reusa_y_no_se_corre` |
| E-11 | Las fuentes de cada control | sostenido | sí | `test_e11_las_fuentes_de_cada_control` |
| E-12 | El resultado compartido no decide la regla | sostenido | sí | `test_e12_el_resultado_compartido_no_decide_la_regla` |
| E-13 | El inventario vacío no cubre | sostenido | sí | `test_e13_el_inventario_vacio_no_cubre` |
| E-14 | Cada superficie se evalúa sola | sostenido | sí | `test_e14_cada_superficie_se_evalua_sola` |
| E-15 | Una que cumple no tapa a otra, y lo que otra fuente vio cuenta | sostenido | sí | `test_e15_una_que_cumple_no_tapa_a_otra` |
| E-16 | Una librería no prueba OIDC, las cuatro formas | sostenido | sí | `test_e16_una_libreria_no_prueba_oidc` |
| E-17 | La evidencia real prueba el protocolo; la prueba que no confirmó, no | sostenido | sí | `test_e17_la_evidencia_real_prueba_el_protocolo` |
| E-18 | El hostname no prueba la autoridad | sostenido | sí | `test_e18_el_hostname_no_prueba_la_autoridad` |
| E-19 | La evidencia de DGSEI satisface el proveedor | sostenido | sí | `test_e19_la_evidencia_de_dgsei_satisface_el_proveedor` |
| E-20 | Un `client_id` no prueba el registro | sostenido | sí | `test_e20_un_client_id_no_prueba_el_registro` |
| E-21 | El registro autoritativo satisface | sostenido | sí | `test_e21_el_registro_autoritativo_satisface` |
| E-22 | No hay flujo universal | sostenido | sí | `test_e22_no_hay_flujo_universal` |
| E-23 | El default del framework no alcanza | sostenido | sí | `test_e23_el_default_del_framework_no_alcanza` |
| E-24 | Sin flujo declarado | sostenido | sí | `test_e24_sin_flujo_declarado` |
| E-25 | Flujo sin autoridad | sostenido | sí | `test_e25_flujo_sin_autoridad` |
| E-26 | Con autoridad para el flujo pasa | sostenido | sí | `test_e26_con_autoridad_para_el_flujo_pasa` |
| E-27 | Recibir la contraseña falla, también con varios flujos de D2 | sostenido | sí | `test_e27_recibir_la_contrasena_falla` |
| E-28 | La delegación sale de D2, y un D2 ilegible no se lee | sostenido | sí | `test_e28_la_delegacion_sale_de_d2` |
| E-29 | El servicio anterior activo falla | sostenido | sí | `test_e29_el_servicio_anterior_activo_falla` |
| E-30 | Una referencia histórica no falla | sostenido | sí | `test_e30_una_referencia_historica_no_falla` |
| E-31 | La migración no se aplica | sostenido | sí | `test_e31_la_migracion_no_se_aplica` |
| E-32 | Producción no se fuerza en QA | sostenido | sí | `test_e32_produccion_no_se_fuerza_en_qa` |
| E-33 | Sin contrato de ambiente | sostenido | sí | `test_e33_sin_contrato_de_ambiente` |
| E-34 | Sin política de ASI | sostenido | sí | `test_e34_sin_politica_de_asi` |
| E-35 | No se inventa ningún parámetro | sostenido | sí | `test_e35_no_se_inventa_ningun_parametro` |
| E-36 | Autenticar no prueba autorizar | sostenido | sí | `test_e36_autenticar_no_prueba_autorizar` |
| E-37 | Los roles son de la aplicación | sostenido | sí | `test_e37_los_roles_son_de_la_aplicacion` |
| E-38 | Los grupos de AD no se exigen | sostenido | sí | `test_e38_los_grupos_de_ad_no_se_exigen` |
| E-39 | La restricción de AD es recomendación | sostenido | sí | `test_e39_la_restriccion_de_ad_es_recomendacion` |
| E-40 | Institucional con evidencia se evalúa | sostenido | sí | `test_e40_institucional_con_evidencia_se_evalua` |
| E-41 | Una ciudadana no reemplaza D1 | sostenido | sí | `test_e41_ciudadana_no_reemplaza_d1` |
| E-42 | Las cuatro audiencias sin reconciliar | sostenido | sí | `test_e42_las_cuatro_audiencias_sin_reconciliar` |
| E-43 | La reconciliación de un proyecto es suya, y lo ilegible bloquea | sostenido | sí | `test_e43_la_reconciliacion_de_un_proyecto_es_suya` |
| E-44 | Frontend ciudadano y backoffice, por separado | sostenido | sí | `test_e44_frontend_ciudadano_y_backoffice` |
| E-45 | Ningún checkpoint se vuelve doctrina | sostenido | sí | `test_e45_ningun_checkpoint_se_vuelve_doctrina` |
| E-46 | `dev-openid-connect` no crea verdad | sostenido | sí | `test_e46_dev_openid_connect_no_crea_verdad` |
| E-47 | C1 no es C2, ni Vu8, ni D1, ni D8 | sostenido | sí | `test_e47_c1_no_es_c2_ni_vu8_ni_d1_ni_d8` |
| E-48 | C1 no es aprobación oficial | sostenido | sí | `test_e48_c1_no_es_aprobacion_oficial` |
| E-49 | La trazabilidad viaja | sostenido | sí | `test_e49_la_trazabilidad_viaja` |
| E-50 | La misma evidencia, el mismo resultado, en cualquier orden | sostenido | sí | `test_e50_la_misma_evidencia_el_mismo_resultado` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los cincuenta de esta tabla
> llevan `sí`: la pasada de mutaciones se corrió entera en la construcción, con `__pycache__`
> borrado antes y después de cada una, y cada corrección de los pases siguientes se volvió a ver en
> rojo con la suya. El refutador rehízo las del pase que le tocaba en cada uno.

La compuerta, en el último pase que la corrió entera (el séptimo):

```
.\tests\Invoke-Tests.ps1
  250/250 pasaron (PowerShell)
  28314/28314 pasaron (python), de los cuales 358 son 41_es0902_c1_openid_connect
  28564/28564 pasaron
```

Y el octavo, sobre el archivo 41 sólo: `361/361`.

## Los ocho pases

Ningún escenario terminó contradicho, pero seis lo estuvieron en algún pase. Todos volvieron a
construcción y se arreglaron **en el código**, nunca aflojando la spec: cada pase agregó texto a los
escenarios, ninguno lo sacó.

```
pase 1   50 escenarios   E-43 y E-50 contradichos
pase 2   E-43 E-50       E-43 y E-50 contradichos otra vez, por casos nuevos
pase 3   E-43 E-50 E-17  sostenidos; E-27 reabierto y contradicho
pase 4   E-17 E-27 E-28 E-50   E-28 contradicho
pase 5   E-17 E-28       sostenidos; dos entradas más fuera de la regla
pase 6   E-15 E-43       E-43 contradicho
pase 7   E-43 E-28       sostenidos; una entrada más de la misma clase
pase 8   E-43            sostenido
```

| Pase | Qué encontró | Qué se hizo |
|---|---|---|
| 1 | Una reconciliación sin `surfaceIds` resolvía toda superficie ciudadana del proyecto que la citara (E-43). Un id de evidencia repetido hacía depender el resultado del orden, y las observaciones salían en el orden de entrada (E-50) | La audiencia y la reconciliación exigen nombrar la superficie; un id repetido no cuenta; `issues` ordenado |
| 2 | `surfaceIds` escrito como string se comparaba por substring (E-43). Dos superficies con el mismo id salían en el orden de entrada (E-50) | **Primera regla unificadora**: lo que no tiene la forma declarada no cuenta, y toda lista de la salida se ordena por su contenido |
| 3 | El check tomaba el **primer** flujo de D2 con el id de la superficie: uno delegado tapaba al que captura la contraseña, y C1 aprobaba con D2 en `FAIL` (E-27) | Se juntan todos los flujos: cualquier `FAIL` manda |
| 4 | Un flujo de D2 en `FAIL` con el `flowId` mal escrito se descartaba y el `PASS` de al lado aprobaba (E-28) | **Segunda regla**: lo que puede decir que no y viene torcido deja la dimensión sin resolver; una prueba de integración cuenta sólo con `CONFIRMED` |
| 5 | Una reconciliación contraria torcida desaparecía; un `detectedSurfaces` torcido se perdía en silencio | Las dos quedan sin resolver (E-43, E-15) |
| 6 | La contraria con el propio `evidenceId` torcido quedaba huérfana y la ciudadana aprobaba (E-43). Con D2 ilegible la cobertura figuraba completa (E-28) | Todo id citado que no resuelve en el catálogo bloquea la reconciliación; D2 ilegible deja la cobertura sin resolver |
| 7 | Una `resolution` no reconocida en la contraria se descartaba | Bloquea |
| 8 | —sostenido— | — |

Los pases 3 a 8 corrieron **después** de adoptar reglas que cierran clases y no casos, que es lo
que la memoria de este repositorio pide desde el tercer pase sobre un escenario. La clase que siguió
apareciendo —algo que puede decir que no llega ilegible y se pierde— es una sola; cada pase la
encontró en un campo distinto. Después del octavo se cortó: lo que queda de esa clase no lo alcanza
la letra de ningún escenario y está anotado abajo.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Tres caminos por los que C1 aprobaba lo que tenía que rechazar.** Con D2 en `FAIL` por captura
   de contraseña (pases 3 y 4) y con una reconciliación contraria legible por la mitad (pases 5, 6
   y 7). Los tests del constructor armaban siempre el caso bien formado.
2. **Que descartar no es neutral.** Para la evidencia, descartar lo torcido es fallar cerrado: sólo
   suma. Para un flujo de D2 o una reconciliación contraria es fallar abierto. La distinción no
   estaba en la spec y ahora es una decisión con nombre.
3. **Cuatro formas de depender del orden de la entrada** que ningún test mezclaba: ids repetidos,
   huérfanas, superficies con el mismo id, flujos de D2 con el mismo id.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- **ES0902 C1 no trata como veto la evidencia bien formada que contradice.** Una prueba de
  integración fallida junto a una configuración que prueba el protocolo; dos audiencias bien
  formadas que se contradicen; una reconciliación contraria legible sin autoridad. Son una decisión
  de política que nadie tomó, no un defecto contra la spec.
- **ES0902 C1 lee un valor de catálogo mal escrito como "no es esta dimensión", en silencio.**
  `CROSS_STANDARD_RECONCILIATON` o `IDENTITY_TIKET` en la contraria. Es el resto de la clase de los
  pases 3 a 8, y donde se cortó el ciclo.
- **Los registros del proyecto viven en `reglas/`, que `-Update` sobrescribe.** El inventario de C1
  es el tercero; la deuda no la crea C1.

## Lo que ningún test cubre y se mira con los ojos

- **Que el inventario se pueda llenar.** Ningún proyecto real declaró todavía sus superficies de
  autenticación, y la primera corrida real con autenticación va a dar
  `AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED`, que es el estado correcto.
- **Que las clases de fuente se correspondan con papeles reales.** `DGSEI_IDENTITY_REGISTRATION`,
  `IDENTITY_TICKET` y `ENVIRONMENT_IDENTITY_CONTRACT` son nombres de este cambio: alguien que conozca
  el circuito de identidad del GCBA tiene que decir si nombran algo que existe.
