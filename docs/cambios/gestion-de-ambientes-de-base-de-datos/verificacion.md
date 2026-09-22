# Verificación — Gestión de ambientes de base de datos

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.19.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el
22-09-2026, en **dos pasadas**, corriendo `python tests/correr.py -k 33_bases --detallado` sobre el
árbol de release de 0.19.0 —el árbol de trabajo sin ES0902 O1 ni O2—. La compuerta completa
`.\tests\Invoke-Tests.ps1` corrió aparte sobre el mismo árbol: 24192/24192.

La spec dice "cuatro refutaciones, en la quinta": las cuatro anteriores no dejaron un
`verificacion.md`. Éste es el primero, y es el de la quinta.

**Resultado: 37 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

La primera pasada rindió 36 sostenidos y **1 contradicho**, E-31. 🔴 **No era un defecto del
cambio.** El test cuenta directorios de `harnesses/desarrollo/skills/`, y el árbol de release se
armó copiando archivos: los siete directorios de las skills viejas borradas (`dev-ambientes`,
`dev-identidad`, `dev-pantalla`, `dev-repositorio`, `dev-seguridad`, `dev-tramites-asi`,
`dev-versiones`) quedaron vacíos en el disco. Se borraron, sin tocar test ni código, y la segunda
pasada dio `3604/3604 pasaron`.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Política: cuatro ambientes, default DENY, en `reglas/` | sostenido | sí | `33_bases`, `test_e01_la_politica_es_del_harness` |
| E-02 | DEV da FULL con los cuatro permisos | sostenido | sí | `33_bases`, `test_e02_dev_resuelve_full` |
| E-03 | QA da READ_ONLY | sostenido | sí | `33_bases`, `test_e03_qa_resuelve_solo_lectura` |
| E-04 | HML da READ_ONLY | sostenido | sí | `33_bases`, `test_e04_hml_resuelve_solo_lectura` |
| E-05 | PRD da READ_ONLY | sostenido | sí | `33_bases`, `test_e05_prd_resuelve_solo_lectura` |
| E-06 | Ambiente no declarado: UNRESOLVED, producto de formas | sostenido | sí | `33_bases`, `test_e06_el_ambiente_desconocido_falla_cerrado` |
| E-07 | Clase y efecto son dos campos; tabla de nueve verbos | sostenido | sí | `33_bases`, `test_e07_la_clase_y_el_efecto_son_dos_campos` |
| E-08 | Verbo no declarado da UNCLASSIFIED | sostenido | sí | `33_bases`, `test_e08_un_verbo_que_la_tabla_no_declara_se_deniega` |
| E-09 | El barrido sólo sube la clase | sostenido | sí | `33_bases`, `test_e09_el_barrido_solo_puede_subir` |
| E-10 | Varias sentencias: gana la más alta; una ilegible deniega todo | sostenido | sí | `33_bases`, `test_e10_una_sentencia_sin_clasificar_deniega_todo` |
| E-11 | DELETE sin alcance es DESTRUCTIVE | sostenido | sí | `33_bases`, `test_e11_delete_sin_alcance_es_destructivo` |
| E-12 | `resolver()` no ejecuta nada | sostenido | sí | `33_bases`, `test_e12_el_resolvedor_no_ejecuta_nada` |
| E-13 | SELECT en DEV se permite | sostenido | sí | `33_bases`, `test_e13_select_en_dev_se_permite` |
| E-14 | UPDATE en DEV se permite | sostenido | sí | `33_bases`, `test_e14_update_en_dev_se_permite` |
| E-15 | ALTER en DEV: permite el ambiente, la aprobación la decide la compuerta | sostenido | sí | `33_bases`, `test_e15_alter_en_dev_se_permite_y_la_compuerta_decide` |
| E-16 | Lo destructivo en DEV pasa por `tools` | sostenido | sí | `33_bases`, `test_e16_lo_destructivo_en_dev_pasa_por_la_compuerta_que_ya_existe` |
| E-17 | Descubrimiento de esquema en DEV, READ_ONLY y primero | sostenido | sí | `33_bases`, `test_e17_el_descubrimiento_de_esquema_en_dev_precede_a_la_mutacion` |
| E-18 | SELECT en QA, HML y PRD | sostenido | sí | `33_bases`, `test_e18_select_se_permite_en_los_tres` |
| E-19 | Escritura en los tres da WRITE_NOT_ALLOWED | sostenido | sí | `33_bases`, `test_e19_la_escritura_se_deniega_en_los_tres` |
| E-20 | DDL en los tres da DDL_NOT_ALLOWED | sostenido | sí | `33_bases`, `test_e20_el_ddl_se_deniega_en_los_tres` |
| E-21 | Migración en los tres da MIGRATION_NOT_ALLOWED | sostenido | sí | `33_bases`, `test_e21_la_migracion_se_deniega_en_los_tres` |
| E-22 | Inspección con SELECT al catálogo; verbos de metadata UNCLASSIFIED | sostenido | sí | `33_bases`, `test_e22_los_tres_sirven_para_inspeccionar_con_select` |
| E-23 | Producto promoción × verbos × variantes: 324 celdas, 18 permitidas | sostenido | sí | `33_bases`, `test_e23_el_producto_de_promocion_por_operaciones` |
| E-24 | Cada ambiente tiene su propio perfil | sostenido | sí | `33_bases`, `test_e24_cada_ambiente_resuelve_su_propio_perfil` |
| E-25 | Sin perfil, PROFILE_NOT_FOUND; el archivo instalado está vacío | sostenido | sí | `33_bases`, `test_e25_sin_perfil_no_se_inventa_ninguno` |
| E-26 | Ninguna salida lleva una credencial | sostenido | sí | `33_bases`, `test_e26_ningun_valor_de_credencial_sale_del_modulo` |
| E-27 | `resolver()` no habla con el almacén | sostenido | sí | `33_bases`, `test_e27_el_resolvedor_no_habla_con_el_almacen` |
| E-28 | Referencia inexistente da SECRET_UNRESOLVED en el borde | sostenido | sí | `33_bases`, `test_e28_una_referencia_que_no_existe_se_resuelve_en_el_borde` |
| E-29 | Ninguna migración en promoción; la negación trae el remedio | sostenido | sí | `33_bases`, `test_e29_ninguna_migracion_se_aplica_en_promocion` |
| E-30 | Flujo DEV primero, declarado y ordenado | sostenido | sí | `33_bases`, `test_e30_el_flujo_dev_primero_esta_declarado_y_ordenado` |
| E-31 | Ningún agente ni skill nuevos; la cuenta no cambia | sostenido | sí | `33_bases`, `test_e31_no_se_crea_ningun_agente_ni_ninguna_skill` — segunda pasada |
| E-32 | La política es del harness; fuera de la matriz y del registro | sostenido | sí | `33_bases`, `test_e32_la_politica_es_del_harness_y_no_entra_en_la_matriz` |
| E-33 | Diez estados, sin solapes, ninguno permite | sostenido | sí | `33_bases`, `test_e33_los_diez_estados_existen_y_ninguno_permite` |
| E-34 | Producto de datos faltantes: nada permite | sostenido | sí | `33_bases`, `test_e34_todo_dato_faltante_falla_cerrado` |
| E-35 | Todo resultado conserva el contrato | sostenido | sí | `33_bases`, `test_e35_todo_resultado_conserva_su_contrato` |
| E-36 | El validador acepta `$defs`, `$ref` local y `additionalProperties: false` | sostenido | sí | `33_bases`, `test_e36_el_validador_lee_los_schemas_del_pedido` |
| E-37 | La compuerta arranca en un árbol instalado | sostenido | sí | `33_bases`, `test_e37_la_compuerta_arranca_en_un_arbol_instalado` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno: los 37
> escenarios declaran `rojo visto: si` en la spec.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-31 cuenta directorios, no skills.** Un directorio vacío en `harnesses/desarrollo/skills/`
   —lo que deja cualquier borrado hecho fuera de git— lo pone en rojo sin que haya una skill nueva.
   Esta vez delató un árbol mal armado, y no al cambio. Es un falso rojo posible, no un falso
   verde: el lado barato.

## Lo que queda abierto, anotado y no escondido

Nada nuevo. Lo que el cambio ya dejaba abierto sigue en
`Pendientes/Fix-Harness/PENDIENTES-FH.md`, donde estaba.

## Lo que ningún test cubre y se mira con los ojos

Que la política se respete en una sesión real contra una base real: el resolvedor decide y no
ejecuta, y E-12 y E-27 prueban justamente eso. Lo que haga el agente con la negación se ve abriendo
una sesión.
