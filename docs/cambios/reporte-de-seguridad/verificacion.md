# Verificación — Reporte de seguridad: del libro al tablero

**Estado:** cerrado · **Fecha:** 23-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **tres pases**. Todos corrieron `python tests/correr.py -k 48_reporte` y la compuerta completa
`.\tests\Invoke-Tests.ps1` con el árbol quieto. La corrida del tercero dio `566/566` y
`30808/30808` (272 PowerShell), EXIT=0. El tercero fue el pase final, y juzgó E-03 contra la regla
unificadora E-03b.

**Resultado: 59 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

Cada escenario trae entre paréntesis el id `SR-nn` del paquete. El refutador contrastó el mapeo
contra el pedido y no encontró huecos en SR-01..SR-50.

## Los veredictos

Salvo E-56, todos los tests están en `tests/casos/48_reporte_de_seguridad.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | El libro es append-only y ningún escritor lo pisa | sostenido | sí | `test_e01_el_libro_es_append_only`, `test_e01_el_paquete_no_tiene_verbo_que_reescriba_el_libro`, `test_e01_ninguna_grafia_del_libro_esquiva_la_guarda` |
| E-02 | Un evento incompleto o con tipo fuera del enum no entra | sostenido | sí | `test_e02_un_evento_incompleto_no_entra` |
| E-03 | Ningún secreto de `details` o `evidenceRefs` llega al disco | sostenido | sí | `test_e03_ningun_secreto_llega_al_disco`, `test_e03_citada_o_espaciada_tampoco_llega` |
| E-03b | La contraseña se reconoce por la palabra que la anuncia | sostenido | sí | `test_e03b_la_palabra_anuncia_la_contrasena` |
| E-04 | Sin productor de la lista o sin huella, no entra | sostenido | sí | `test_e04_sin_productor_o_sin_huella_no_entra` |
| E-05 | Las mismas entradas dan el mismo resumen byte a byte | sostenido | sí | `test_e05_el_mismo_libro_da_el_mismo_resumen_byte_a_byte` |
| E-05b | La huella cubre las cuatro entradas, con marca de presencia del Bloque 4 | sostenido | sí | `test_e05b_la_huella_cubre_las_cuatro_entradas` |
| E-06 | Ningún cliente de modelo ni red | sostenido | sí | `test_e06_el_paquete_no_llama_modelos_ni_hace_red` |
| E-07 | No hay puntaje global | sostenido | sí | `test_e07_no_hay_puntaje` |
| E-08 | `NOT_APPLICABLE` no suma al denominador | sostenido | sí | `test_e08_no_aplicable_no_suma_al_denominador` |
| E-09 | `UNRESOLVED` se intentó y no se resolvió | sostenido | sí | `test_e09_unresolved_se_intento_y_no_se_resolvio` |
| E-10 | Sin evento suma a aplicables y no a intentadas | sostenido | sí | `test_e10_sin_evento_suma_a_aplicables_y_no_a_intentadas` |
| E-11 | Sin denominador es `N/D`, nunca 100% | sostenido | sí | `test_e11_sin_denominador_es_n_d` |
| E-12 | El resumen valida y los schemas entran en el validador | sostenido | sí | `test_e12_el_resumen_valida_y_los_schemas_se_entienden` |
| E-13 | Frescura bloqueante da `BLOCKED` | sostenido | sí | `test_e13_frescura_bloqueante_da_blocked` |
| E-14 | Sin conocimiento, `BLOCKED` | sostenido | sí | `test_e14_sin_conocimiento_da_blocked` |
| E-15 | Sin evaluar o evidencia material, `REVIEW_INCOMPLETE` | sostenido | sí | `test_e15_sin_evaluar_o_evidencia_material_da_review_incomplete` |
| E-16 | Una falla da `ACTION_REQUIRED` con su bloqueo | sostenido | sí | `test_e16_una_falla_da_action_required` |
| E-17 | Todo en `PASS` da `READY_FOR_SECURITY_REVIEW` | sostenido | sí | `test_e17_todo_en_pass_da_ready` |
| E-18 | Listo no es aprobado | sostenido | sí | `test_e18_listo_no_es_aprobado` |
| E-19 | El umbral de G2 no es aprobación | sostenido | sí | `test_e19_el_umbral_de_g2_no_es_una_aprobacion` |
| E-20 | Un aprobado interno no es externo | sostenido | sí | `test_e20_un_aprobado_interno_no_es_externo` |
| E-21 | C2 cambiada o a reevaluar da `STALE` | sostenido | sí | `test_e21_c2_cambiada_o_a_reevaluar_esta_vencida` |
| E-22 | Otro ambiente u otro release no evidencian | sostenido | sí | `test_e22_otro_ambiente_u_otro_release_no_evidencian` |
| E-22b | Las cinco filas de la aprobación, en orden | sostenido | sí | `test_e22b_las_cinco_filas_en_orden` |
| E-23 | C2 a reevaluar gana sobre el flujo y bloquea | sostenido | sí | `test_e23_c2_a_reevaluar_gana_sobre_el_flujo` |
| E-24 | Las 21 reglas, en el orden del estándar | sostenido | sí | `test_e24_las_21_reglas_en_el_orden_del_estandar` |
| E-25 | Un control compartido no le pone resultado a ninguna regla | sostenido | sí | `test_e25_un_control_compartido_no_le_pone_nota_a_ninguna` |
| E-26 | `OVERRIDDEN` baja a `UNRESOLVED` y conserva `sourceResult` | sostenido | sí | `test_e26_overridden_baja_a_unresolved_en_los_tres` |
| E-27 | Sin evento es `NOT_EVALUATED` en los tres | sostenido | sí | `test_e27_sin_evento_es_not_evaluated_en_los_tres` |
| E-28 | El reporte muestra el conocimiento | sostenido | sí | `test_e28_el_reporte_muestra_el_conocimiento` |
| E-29 | `FRESHNESS_UNVERIFIED` es `UNVERIFIED` y no deja `READY` | sostenido | sí | `test_e29_freshness_unverified_es_unverified` |
| E-30 | `SOURCE_INTEGRITY_ALERT` bloquea | sostenido | sí | `test_e30_alerta_de_integridad_bloquea` |
| E-31 | `CURRENT` es `VERIFIED` y no bloquea | sostenido | sí | `test_e31_current_es_verified_y_no_bloquea` |
| E-32 | Severidad y confianza no se mezclan | sostenido | sí | `test_e32_severidad_y_confianza_no_se_mezclan` |
| E-33 | Un crítico abierto pide acción | sostenido | sí | `test_e33_un_critico_abierto_pide_accion` |
| E-34 | Los bloqueos son una lista propia | sostenido | sí | `test_e34_los_bloqueos_son_una_lista_propia` |
| E-35 | Resuelto y abierto otra vez es `REOPENED` | sostenido | sí | `test_e35_resuelto_y_abierto_otra_vez_es_reopened` |
| E-36 | Un resuelto no desaparece | sostenido | sí | `test_e36_un_resuelto_no_desaparece` |
| E-37 | Sin línea de base bloquea solo en incidente | sostenido | sí | `test_e37_sin_linea_de_base_bloquea_solo_en_incidente` |
| E-38 | Sin indicadores no es sin malware | sostenido | sí | `test_e38_sin_indicadores_no_es_sin_malware` |
| E-39 | Malicioso confirmado tiene su rótulo y su bloqueo | sostenido | sí | `test_e39_malicioso_confirmado_tiene_su_rotulo` |
| E-40 | Cuenta el último estado de cada evidencia | sostenido | sí | `test_e40_cuenta_el_ultimo_estado_de_cada_evidencia` |
| E-41 | Una prueba insegura deja su evidencia | sostenido | sí | `test_e41_una_prueba_insegura_deja_su_evidencia` |
| E-42 | Solo la evidencia material cambia el estado | sostenido | sí | `test_e42_solo_la_evidencia_material_cambia_el_estado` |
| E-43 | La tabla ejecutiva del md es el resumen | sostenido | sí | `test_e43_la_tabla_ejecutiva_es_el_resumen` |
| E-44 | Cada `data-field` del HTML es el valor del resumen | sostenido | sí | `test_e44_cada_data_field_es_el_valor_del_resumen` |
| E-45 | md y HTML muestran la huella y el id | sostenido | sí | `test_e45_md_y_html_muestran_la_huella_y_el_id` |
| E-46 | El alcance muestra lo que trae el libro | sostenido | sí | `test_e46_el_alcance_muestra_lo_que_trae_el_libro` |
| E-47 | Un alcance ausente dice `desconocido` | sostenido | sí | `test_e47_un_alcance_ausente_dice_desconocido` |
| E-48 | La tarjeta de ejecución copia al Bloque 4 | sostenido | sí | `test_e48_la_tarjeta_de_ejecucion_copia_al_bloque_4` |
| E-49 | El subcomando no toca la contabilidad | sostenido | sí | `test_e49_el_subcomando_no_toca_la_contabilidad` |
| E-50 | Una clave de API no llega al libro | sostenido | sí | `test_e50_una_clave_de_api_no_llega_al_libro`, `test_e50_los_hallazgos_no_repiten_la_muestra` |
| E-51 | Las cuatro tarjetas primarias, siempre | sostenido | sí | `test_e51_las_cuatro_tarjetas_primarias_siempre` |
| E-52 | Hasta cinco bloqueos y `+N más` | sostenido | sí | `test_e52_hasta_cinco_bloqueos_y_mas` |
| E-53 | El aviso de aprobación oficial | sostenido | sí | `test_e53_el_aviso_solo_falta_con_aprobacion_externa` |
| E-54 | El subcomando deja los cuatro archivos | sostenido | sí | `test_e54_el_subcomando_deja_los_cuatro_archivos` |
| E-55 | Un `taskId` con ruta se rechaza antes del disco | sostenido | sí | `test_e55_una_tarea_con_ruta_se_rechaza_antes_del_disco` |
| E-56 | El paquete y los dominios llegan al proyecto instalado | sostenido | sí | `tests/casos/30-contabilidad-instalador.ps1`, asserts `E-56` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 59 la declaran `sí`.
> En E-01, E-05b y E-22b el rojo se vio con mutaciones que devolvían el comportamiento anterior.
> Contra el código viejo esos tests también fallaban, pero por el cambio de firma de `resumir`, y
> eso no probaba nada.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-01, pase 1.** La guarda del libro comparaba el nombre exacto. En Windows,
   `SECURITY-LEDGER.NDJSON` o `security-ledger.ndjson.` (con punto final) la esquivaban y los
   escritores pisaban el libro. El test probaba el único caso donde la guarda no podía fallar.
2. **E-01, pase 2.** Un `<destino>.tmp` que ya existía como hardlink al libro se abría con `w` y
   truncaba el libro. Se cerró creando el temporal con `tempfile.mkstemp`.
3. **E-03, pases 1 y 2.** Contraseñas entre comillas, con espacios, en un array de PHP, en XML o
   como flag de línea de comando llegaban crudas al libro. Después de dos pases se cortó el ciclo
   con la regla E-03b: la contraseña se reconoce por la palabra que la anuncia, no por la sintaxis.
4. **La huella no identificaba la foto.** Con el mismo libro y la misma matriz, un Bloque 4 o unos
   dominios distintos daban resúmenes distintos con la misma huella. La spec se corrigió para que
   la huella cubra las cuatro entradas (E-05b).
5. **La tabla de aprobación era ambigua** cuando el alcance no estaba en QA. Se reescribió como
   cinco filas ordenadas (E-22b).
6. **Los hallazgos que devolvía `agregar` repetían 12 caracteres del secreto** en la consola,
   aunque el libro no los guardara.

## Lo que queda abierto, anotado y no escondido

Todo está en `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- **El catálogo compartido de secretos** no conoce varias formas de credencial, y `muestra_segura`
  filtra 12 caracteres. El reporte los cubre con una capa propia, así que hay dos capas de redacción
  que pueden divergir.
- **Cuatro formas quedan afuera de la regla E-03b.** Por su letra, no contradicen E-03:
  - `PASSWORD=` con el valor en la línea siguiente. Es una regresión respecto del pase 2.
  - Una comilla escapada adentro del valor.
  - `Bearer:valor`.
  - Un cuerpo PEM sin encabezado.
- **E-03b angosta lo que E-03 abarcaba** con "una contraseña". Queda a la vista.
- **El temporal de `mkstemp` queda en la carpeta si la escritura falla**, porque el paquete no
  tiene ningún verbo que borre.
- **Dos causas de `BLOCKED` del paquete no tienen productor.** Están declaradas en la spec.
- **Nada ejecuta los checks contra un proyecto real.** El libro recibe eventos solo de los
  productores, y todavía no hay un ejecutor que los llame.

## Lo que ningún test cubre y se mira con los ojos

Que el HTML impreso a PDF se entienda en quince segundos, como pide la página 1 del paquete. La
suite compara cada valor contra el resumen, pero no juzga si la página se entiende.
