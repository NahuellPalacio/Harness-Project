# Verificación — ES0902 Vu7: el software de base no entrega datos privados

**Estado:** cerrado · **Fecha:** 24-09-2026 · **Versión:** 0.22.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 24-09-2026
en **un pase**. Corrió la compuerta completa una sola vez, con el árbol quieto:
- `-k 54_es0902` dio `895/895`;
- la compuerta dio `34969/34969`, EXIT=0.

Vu7 iba a refutarse en tanda con Vu8. Por decisión del usuario se refutó solo, para publicarlo en la
0.22.0.

**Resultado: 45 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

El paquete no trae una lista `VU7-nn`, así que los escenarios salen del paquete y de las reglas de
Vu3 a Vu6.

## Los veredictos

Todos los tests están en `tests/casos/54_es0902_vu7_software_de_base.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.Vu7`, en la fila y en todo resultado | sostenido | sí | `test_e01_la_clave` |
| E-02 | `base-software-private-data-disclosure-prohibited` y `base-software-data-disclosure-configuration` están… | sostenido | sí | `test_e02_los_ids` |
| E-03 | No hay ningún agente, skill, review ni señal nuevos, y `ALGORITMOS` sigue en diez | sostenido | sí | `test_e03_nada_nuevo` |
| E-04 | El check nunca emite `NOT_APPLICABLE`, con ninguna entrada | sostenido | sí | `test_e04_nunca_no_aplica` |
| E-05 | El registro vacío da `BASE_SOFTWARE_INVENTORY_UNRESOLVED` | sostenido | sí | `test_e05_el_registro_vacio` |
| E-06 | Un componente nombrado en el `BASE_SOFTWARE_INVENTORY` citado y sin entrada da… | sostenido | sí | `test_e06_un_componente_del_inventario_sin_entrada` |
| E-07 | Sin ninguna `BASE_SOFTWARE_INVENTORY` autoritativa citada, el inventario no está entero | sostenido | sí | `test_e07_sin_inventario_autoritativo` |
| E-08 | Una superficie nombrada en el `DISCLOSURE_SURFACE_SCOPE` sin entrada da… | sostenido | sí | `test_e08_una_superficie_del_alcance_sin_entrada` |
| E-09 | Un componente o una superficie fuera del inventario o del alcance impide el `PASS` y no hace `FAIL` por… | sostenido | sí | `test_e09_lo_que_esta_afuera` |
| E-10 | El módulo no tiene ninguna lista de productos ni de tipos de componente: dos productos distintos con la… | sostenido | sí | `test_e10_ninguna_lista_de_productos` |
| E-11 | Una clase `PRIVATE` sin `DATA_CLASSIFICATION` autoritativa citada da… | sostenido | sí | `test_e11_una_clase_privada_sin_clasificacion` |
| E-12 | Un `dataClassId` que parece privado (`dni`, `cuit`, `password`) sin clasificación no se trata como privado | sostenido | sí | `test_e12_un_nombre_no_clasifica` |
| E-13 | Una fuga establecida de una clase `NOT_PRIVATE` no es `FAIL` de Vu7 | sostenido | sí | `test_e13_una_fuga_de_datos_no_privados` |
| E-14 | `configurationStatus: UNRESOLVED` da `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED` | sostenido | sí | `test_e14_la_configuracion_sin_resolver` |
| E-15 | Un `REPOSITORY_DEFAULT_CONFIGURATION` que dice que no hay fuga, solo, no cumple | sostenido | sí | `test_e15_el_default_del_repositorio_solo` |
| E-16 | Un `ENVIRONMENT_OVERRIDE` citado que establece la fuga le gana al default del repositorio: da `FAIL` | sostenido | sí | `test_e16_el_override_le_gana_al_default` |
| E-17 | Una `EFFECTIVE_CONFIGURATION` de `DEV` no sostiene nada en un registro de `QA` | sostenido | sí | `test_e17_dev_no_prueba_qa` |
| E-18 | Un registro con `environment` nulo da `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED` en toda superficie | sostenido | sí | `test_e18_sin_ambiente` |
| E-19 | Una `SOURCE_CODE`, sola, no cumple ninguna superficie | sostenido | sí | `test_e19_el_codigo_solo` |
| E-20 | Una fuga de una clase `PRIVATE` a un consumidor `UNAUTHORIZED`, establecida, da… | sostenido | sí | `test_e20_la_fuga_a_un_no_autorizado` |
| E-21 | Lo mismo con `authorizationContext: PUBLIC` | sostenido | sí | `test_e21_la_fuga_publica` |
| E-22 | El mismo dato servido a un consumidor `AUTHORIZED`, con `AUTHORIZATION_CONTEXT` citado, cumple y no es fuga | sostenido | sí | `test_e22_el_acceso_autorizado` |
| E-23 | `AUTHORIZED_PRIVATE_DATA_ACCESS` sin `AUTHORIZATION_CONTEXT` citado no cumple | sostenido | sí | `test_e23_el_acceso_autorizado_sin_contexto` |
| E-24 | `NO_PRIVATE_DATA_DISCLOSURE` con una `EFFECTIVE_CONFIGURATION` del ambiente citada cumple | sostenido | sí | `test_e24_sin_fuga_con_la_configuracion_efectiva` |
| E-25 | Un listado de directorios, una exposición de backups o una interfaz de administración cumplen o fallan por… | sostenido | sí | `test_e25_el_tipo_de_superficie_no_decide` |
| E-26 | Un `VERSION_BANNER`, solo, no hace `FAIL` | sostenido | sí | `test_e26_el_banner_de_version` |
| E-27 | Un `ENDPOINT_NAME` como `/actuator`, solo, no hace `FAIL` ni cumple | sostenido | sí | `test_e27_el_nombre_del_endpoint` |
| E-28 | Una evidencia citada por Vu6 y por Vu7 deja a cada regla con su resultado: el de Vu6 no entra ni sale del… | sostenido | sí | `test_e28_vu6_no_entra_ni_sale` |
| E-29 | Una prueba en QA con fixtures sintéticos cuenta | sostenido | sí | `test_e29_una_prueba_segura_en_qa` |
| E-30 | Una prueba en `PRD`, destructiva, con `realPrivateDataAccessed: true`, sin fixtures sintéticos o con… | sostenido | sí | `test_e30_las_condiciones_inseguras` |
| E-31 | Una prueba de otro ambiente que el del registro no cuenta | sostenido | sí | `test_e31_una_prueba_de_otro_ambiente` |
| E-32 | Una prueba insegura no es `FAIL`, también cuando dice que hay fuga | sostenido | sí | `test_e32_una_prueba_insegura_no_es_fail` |
| E-33 | El texto de una evidencia y una muestra de un dato no aparecen en la salida, en `rules.Vu7` ni en el libro… | sostenido | sí | `test_e33_ningun_texto_ni_muestra_sale` |
| E-34 | Nada con forma de credencial sale, tampoco como clave de un diccionario | sostenido | sí | `test_e34_ningun_secreto` |
| E-35 | El registro vacío instalado valida contra el schema, y una clave de más en cualquier capa no valida | sostenido | sí | `test_e35_el_schema_cerrado` |
| E-36 | Una evidencia ilegible que nombra el componente o la superficie impide el `PASS`, y un id que no es texto… | sostenido | sí | `test_e36_lo_ilegible` |
| E-37 | La falla establecida gana siempre: una fuga citada con el registro en `NO_PRIVATE_DATA_DISCLOSURE` da el… | sostenido | sí | `test_e37_la_falla_establecida_gana_siempre` |
| E-38 | El bloqueo es uno solo, con la regla 5, y una prueba no citada que dice "sin fuga" no bloquea | sostenido | sí | `test_e38_un_solo_bloqueo` |
| E-39 | El `PASS` de Vu7 no pone en `PASS` a Vu6, a C3, a Ve1 ni a la aprobación oficial | sostenido | sí | `test_e39_el_pass_de_vu7_no_es_el_de_otras` |
| E-40 | Un veredicto de integridad del repositorio en la evidencia no cambia el resultado de Vu7 | sostenido | sí | `test_e40_la_integridad_del_repositorio_no_decide` |
| E-41 | Una fuga en cualquier superficie hace `FAIL` el agregado | sostenido | sí | `test_e41_una_fuga_en_cualquier_superficie` |
| E-42 | Un sin resolver material impide el `PASS` | sostenido | sí | `test_e42_un_sin_resolver_material` |
| E-43 | La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en NFC | sostenido | sí | `test_e43_el_mismo_resultado` |
| E-44 | La trazabilidad `ES0902 / 6.2 / 6 / Vu7` viaja en todo resultado, y la unidad lleva `rules.Vu7` sin… | sostenido | sí | `test_e44_la_trazabilidad` |
| E-45 | La salida pasada por `seguridad.resultado` y `desde_regla` entra como `RULE_EVALUATION` de `ES0902.Vu7` al… | sostenido | sí | `test_e45_entra_al_libro_como_cualquier_regla` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 45 la declaran `sí`.
> Las 45 mutaciones se repitieron enteras sobre el código final, y 16 mutaciones de borde agregaron
> tests.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El refutador no encontró nada que contradiga la letra.** Lo probó con 600 casos al azar, cada
   uno mezclado tres veces, con ids repetidos, gemelos NFC/NFD y pruebas bloqueantes. Todos dieron
   el mismo resultado, y ninguno dio `NOT_APPLICABLE` ni un `FAIL` pelado.
2. **Durante la construcción**, las mutaciones de borde encontraron cuatro tests que pasaban por la
   razón equivocada:
   - uno de ambiente en blanco;
   - una contradicción de la clasificación no citada;
   - el bloqueo tapado por el agregado;
   - una prueba insegura frenada antes por el ambiente (E-32).

## Lo que queda abierto, anotado y no escondido

Son tensiones de la spec que ningún escenario cubre, y quedan escritas acá para la próxima vez que
se toque Vu7:
- **Una fuga con un contexto `AUTHORIZED` sostenido** da `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED`.
  La letra, leída paso por paso, daría `PASS`. El check es más estricto.
- **Una clase declarada `UNRESOLVED`**, con una `DATA_CLASSIFICATION` `PRIVATE` citada y una fuga
  citada, da `PRIVATE_DATA_CLASSIFICATION_UNRESOLVED`, no `FAIL`. La sección de clasificación lo
  respalda, y la letra amplia de la regla 3 empuja en contra.
- **El `VERSION_BANNER`** aparece dos veces en la spec: como "nunca hace `FAIL`, salvo…" y como
  clase que no sostiene nada. El check aplica la segunda: nunca hace `FAIL`.
- **Una evidencia que no nombra nada**, no citada y que dice fuga, no se atribuye a ninguna
  superficie y no impide el `PASS`.
- **El paquete pide guardar una muestra redactada y una huella del dato.** La spec cierra el catálogo
  y no lo pide, así que un ítem con `sample` queda mal formado.

## Lo que ningún test cubre y se mira con los ojos

Que un proyecto real tenga un inventario autoritativo del software de base y una clasificación de
datos privados por ambiente. Sin eso, Vu7 queda sin resolver, y es verdad.
