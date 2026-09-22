# Verificación — P1: frameworks homologados, nada de lenguaje puro, y NPM en Node

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 22-09-2026,
corriendo `python tests/correr.py -k 36_p1` y la compuerta completa `.\tests\Invoke-Tests.ps1`, y
**replicando la marca `rojo visto` de los 42**: para cada escenario aplicó al menos una mutación en
el artefacto que verifica, corrió el archivo y restauró. Los 42 se pusieron en rojo con la mutación
que les corresponde.

**Resultado: 42 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

Es el primer cambio de las once reglas instaladas que **cierra con el primer veredicto**. No hubo
segunda pasada porque no hizo falta: ningún escenario quedó contradicho ni sin sustento. Lo que el
veredicto sí dejó fueron **tres deudas de verificación**, cerradas antes de este documento y
contadas abajo.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | P1 sigue `ALWAYS` con cero señales, y con las claves de toda fila | sostenido | sí, replicado | `36_p1`, `test_e01_p1_es_always_sin_senales` |
| E-02 | Los dos agentes dueños siguen siendo los mismos | sostenido | sí, replicado | `36_p1`, `test_e02_los_dos_agentes_duenos` |
| E-03 | Las tres policies y los dos checks son los que la matriz declara | sostenido | sí, replicado | `36_p1`, `test_e03_las_tres_policies_y_los_dos_checks` |
| E-04 | P1 no crea ni referencia ninguna skill; siguen siendo 27 | sostenido | sí, replicado | `36_p1`, `test_e04_p1_no_crea_ninguna_skill` |
| E-05 | `P1.node` hereda la clasificación de P1 | sostenido | sí, replicado | `36_p1`, `test_e05_p1_node_hereda` |
| E-06 | `P1.plataformas` hereda igual | sostenido | sí, replicado | `36_p1`, `test_e06_p1_plataformas_hereda` |
| E-07 | No hay filas nuevas, ni controles duplicados bajo un id hijo | sostenido | sí, replicado | `36_p1`, `test_e07_no_hay_filas_nuevas` |
| E-08 | Las tres cláusulas citables, con su página y un tramo distintivo de su texto | sostenido | sí, replicado | `36_p1`, `test_e08_las_tres_clausulas_citables` |
| E-09 | El catálogo es el mismo archivo de G1, P1 lo lee, y no lleva una copia | sostenido | sí, replicado | `36_p1`, `test_e09_el_catalogo_es_el_de_g1`, con el barrido AST |
| E-10 | P1 no duplica la lógica de versiones de G1 | sostenido | sí, replicado | `36_p1`, `test_e10_p1_no_duplica_la_logica_de_versiones`, doce nombres |
| E-11 | Sin el veredicto de G1 citado, `G1_EVIDENCE_REQUIRED` | sostenido | sí, replicado | `36_p1`, `test_e11_sin_veredicto_de_g1` |
| E-12 | El estado de G1 se conserva en el campo estructurado y no pasa | sostenido | sí, replicado | `36_p1`, `test_e12_el_estado_de_g1_se_conserva` |
| E-13 | Las siete formas de inventario incompleto | sostenido | sí, replicado | `36_p1`, `test_e13_el_inventario_incompleto_no_se_resuelve` |
| E-14 | Las cinco clases de superficie, nombradas una por una | sostenido | sí, replicado | `36_p1`, `test_e14_las_cinco_clases_de_superficie` |
| E-15 | El script auxiliar declarado no se clasifica solo como vanilla | sostenido | sí, replicado | `36_p1`, `test_e15_el_script_auxiliar_no_es_vanilla` |
| E-16 | Las superficies se evalúan por separado | sostenido | sí, replicado | `36_p1`, `test_e16_las_superficies_se_evaluan_por_separado` |
| E-17 | Un framework homologado que gobierna con traza da `PASS` | sostenido | sí, replicado | `36_p1`, `test_e17_el_framework_que_gobierna_pasa` |
| E-18 | Las cinco clases inertes, una por una | sostenido | sí, replicado | `36_p1`, `test_e18_las_cinco_clases_inertes` |
| E-19 | Sin identidad de framework, `FRAMEWORK_CONTEXT_UNRESOLVED` | sostenido | sí, replicado | `36_p1`, `test_e19_sin_identidad_de_framework` |
| E-20 | El lenguaje puro da `FAIL` con su motivo | sostenido | sí, replicado | `36_p1`, `test_e20_el_lenguaje_puro_falla` |
| E-21 | El framework instalado que no gobierna: la traza manda | sostenido | sí, replicado | `36_p1`, `test_e21_el_framework_instalado_que_no_gobierna` |
| E-22 | El bajo nivel integrado a través del framework puede cumplir | sostenido | sí, replicado | `36_p1`, `test_e22_el_bajo_nivel_por_el_framework` |
| E-23 | El mismo componente como reemplazo directo da `FAIL` | sostenido | sí, replicado | `36_p1`, `test_e23_el_bajo_nivel_como_reemplazo` |
| E-24 | La forma de uso no se deduce del nombre | sostenido | sí, replicado | `36_p1`, `test_e24_el_uso_no_se_deduce_del_nombre` |
| E-25 | Node con el camino activo del permitido puede pasar | sostenido | sí, replicado | `36_p1`, `test_e25_node_con_npm_pasa` |
| E-26 | Un camino activo de YARN da `FAIL` | sostenido | sí, replicado | `36_p1`, `test_e26_yarn_activo_falla` |
| E-27 | Un camino activo de pnpm da `FAIL` | sostenido | sí, replicado | `36_p1`, `test_e27_pnpm_activo_falla` |
| E-28 | Cualquier administrador activo que no sea el permitido da `FAIL` | sostenido | sí, replicado | `36_p1`, `test_e28_cualquier_alternativa_falla`, ocho formas |
| E-29 | Sin saber cuál está activo, `NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED` con su motivo | sostenido | sí, replicado | `36_p1`, `test_e29_sin_saber_cual_esta_activo` |
| E-30 | Lo histórico se investiga: no se ignora y no falla solo | sostenido | sí, replicado | `36_p1`, `test_e30_lo_historico_se_investiga` |
| E-31 | Dos activos distintos dan `NODE_PACKAGE_MANAGER_CONFLICT` | sostenido | sí, replicado | `36_p1`, `test_e31_dos_activos_distintos` |
| E-32 | Sin Node, `NOT_RELEVANT`, que no es `NOT_APPLICABLE` | sostenido | sí, replicado | `36_p1`, `test_e32_sin_node_la_clausula_no_es_relevante` |
| E-33 | P1 no inventa una versión del administrador de paquetes | sostenido | sí, replicado | `36_p1`, `test_e33_no_se_inventa_una_version_de_npm` |
| E-34 | La plataforma gobernada con las cuatro cosas puede pasar | sostenido | sí, replicado | `36_p1`, `test_e34_la_plataforma_gobernada_pasa` |
| E-35 | El nombre del producto no alcanza: siete formas del hueco | sostenido | sí, replicado | `36_p1`, `test_e35_el_nombre_del_producto_no_alcanza` |
| E-36 | El lineamiento que contradice da `BUSINESS_PLATFORM_STANDARD_CONFLICT` | sostenido | sí, replicado | `36_p1`, `test_e36_el_lineamiento_que_contradice` |
| E-37 | La plataforma no exime a los servicios propios | sostenido | sí, replicado | `36_p1`, `test_e37_la_plataforma_no_exime_al_resto` |
| E-38 | La unidad propaga los cinco controles sin ninguna señal | sostenido | sí, replicado | `36_p1`, `test_e38_la_unidad_propaga_sin_senal` |
| E-39 | Treinta y un controles, once reglas completas, sin sueltos | sostenido | sí, replicado | `36_p1`, `test_e39_los_controles_dejan_de_ser_un_hueco` |
| E-40 | Todo resultado conserva `ES0901 / 6.3 / 7.1 / P1` | sostenido | sí, replicado | `36_p1`, `test_e40_todo_resultado_conserva_la_traza`, los 17 caminos |
| E-41 | Los nueve y los ocho estados se alcanzan; sólo `PASS` aprueba | sostenido | sí, replicado | `36_p1`, `test_e41_los_estados_existen_y_solo_pasa_uno` |
| E-42 | Ningún artefacto lleva una versión, un catálogo ni un producto de plataforma | sostenido | sí, las tres mitades | `36_p1`, `test_e42_...`: 8 artefactos, 17 resultados, 31 fugas crudas, 21 textos limpios |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide ADR-0006:
> un test que nunca se vio fallar no probó que puede fallar. Los 42 llevan `sí` por dos vías
> independientes: la pasada de mutaciones de quien construyó —52 mutaciones— y la del refutador, que
> replicó la marca escenario por escenario en vez de creerla.

Compuerta en la que se rindió el veredicto:

```
python tests/correr.py -k 36_p1             ->  1187/1187
.\tests\Invoke-Tests.ps1                    ->  18597/18597, exit 0
```

## Lo que la verificación encontró y no habría encontrado un test verde

El veredicto no contradijo nada, y aun así encontró tres cosas con la suite en verde. Las tres son
**la misma familia**: una aserción que se satisface con algo más débil que lo que el escenario
afirma. Las tres están cerradas.

1. **E-08 se apoyaba en el test de otro cambio.** El escenario afirma que las tres cláusulas
   citables existen **con su texto**, y la aserción era `len(texto) > 80`. El refutador reemplazó el
   texto de `P1.plataformas` por 133 caracteres de prosa inventada y `36_p1` quedó en 1167/1167. Lo
   que sí lo agarró fue `20_orquestacion/E-25b` —*ninguna regla parafrasea al extracto*—, que coteja
   cada texto contra `normativa/extractos/`: la proposición estaba sostenida por la compuerta, pero
   no por su escenario. Ahora cada cláusula clava por literal dos o tres tramos distintivos de su
   texto.

2. **E-09 no sostenía su propia mitad.** El escenario dice que el catálogo es el de G1 y que *P1 lo
   lee*. Si el check dejaba de leerlo se ponían rojas 23 aserciones de otros ocho escenarios, y
   **E-09 quedaba verde**. Ahora E-09 lo prueba por comportamiento: con un catálogo vacío inyectado,
   la misma tecnología deja de resolver y el resultado cambia a
   `G1_STATE_CONTRADICTED_BY_CATALOG`.

3. **E-12 no fijaba el campo estructurado.** La aserción era `estado in repr(...)`, y el `detail`
   del resultado también nombra el estado: sacar el campo `g1State` dejaba la suite verde. Ahora se
   iguala el campo.

Y una cuarta, menor, del mismo tipo: el barrido de E-10 cubría once de los doce nombres de la lógica
de versiones de G1 y le faltaba `_CON_CALIFICATIVO`. Está agregado, y con él la premisa que hace
valer la lista: los doce nombres existen de verdad en `anexo2.py`, así que ninguno es un nombre que
el sistema no pueda fallar.

🔴 **Las tres primeras son deuda de verificación, no de construcción.** En los tres casos el
artefacto estaba bien y lo que faltaba era la aserción que lo sostuviera. Es el cuarto cambio
seguido en el que el hallazgo del refutador no sale de un test en rojo sino de mutar el artefacto y
mirar si alguien se queja.

## Las dos decisiones que el veredicto juzgó

- **`NOT_RELEVANT` frente a `NOT_APPLICABLE`: sostenida por dos vías independientes.** Los dos
  módulos no declaran `NOT_APPLICABLE` en `ESTADOS` y **ninguna de sus cadenas lo contiene** —barrido
  por AST, sin docstrings—, así que no lo pueden devolver ni por accidente. Y el docstring que
  explica la diferencia no dispara el guard, que es exactamente la separación que hace falta: un
  módulo puede decir de qué no habla, y no puede devolverlo.
- **Los dos motivos en vez de estados: aceptada.** `VANILLA_RUNTIME_PATH_DETECTED` y
  `LOW_LEVEL_DIRECT_USE_BYPASS` aparecen en la lista de estados del pedido (§12) y no en la del
  check que el mismo pedido adjunta. Quedaron como motivos de un `FAIL`, y lo que hace segura la
  decisión es que E-41 no se conforma con declararlos: exige que se alcancen, que se informen y que
  no aprueben. El costo, escrito: quien lea sólo `state` no distingue un `FAIL` de vanilla de uno de
  bypass — hay que leer `reason`, y los tests fijan el `reason` caso por caso.

## Lo que queda abierto, anotado y no escondido

- **La evidencia de que un framework gobierna una superficie no la produce nadie todavía.** El check
  la recibe declarada, y no hay productor que la arme desde un repositorio. Es la misma deuda de G1
  a D8, y lo que la destraba es el análisis de impacto.
- **`AUXILIARY_TOOLING` y `active` son puertas declaradas.** Una superficie entregada clasificada
  como herramienta auxiliar, y un lockfile vivo declarado histórico, salen de la verificación con
  una afirmación de quien los declaró. Quedan citadas y son refutables; que sean honestas no lo
  puede saber el check. Es el mismo riesgo que G1 ya acepta con `TOOLCHAIN_AUXILIARY`.
- **P1 depende de que G1 haya corrido.** Sin el veredicto de G1, P1 sale `G1_EVIDENCE_REQUIRED` en
  cualquier proyecto real de hoy, porque el inventario de tecnologías tampoco lo junta nadie.
- **`controles/` no llega a un proyecto instalado.** Con P1 son **treinta y un** controles que
  declaran `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Es el ítem 2,
  ya actualizado.
- **Cuatro copias de los tres ayudantes de evidencia.** El pendiente para `harness-staff-engineer`
  está actualizado: unas 60 líneas repetidas cuatro veces, y la próxima regla las hace cinco.
- **El borde del barrido de E-10.** La lista cubre las funciones de comparación de `anexo2`; una
  copia textual de una regex suelta que no esté nombrada no la agarraría. El escenario habla de las
  funciones de comparación y están todas.

## Lo que ningún test cubre y se mira con los ojos

- **Que un framework gobierne de verdad una aplicación entregada.** Lo que este check verifica es
  que la traza exista y esté atada al build. Quién la produce, y con qué cuidado, es lo que decide
  si P1 sirve.
- **Que la clasificación de superficies sea honesta.** Un proyecto que declare su runtime entregado
  como herramienta auxiliar pasa P1 y no está cumpliendo nada. El inventario declara de dónde sale;
  leerlo con desconfianza es trabajo de una persona.
- **Que las tres policies se lean como obligaciones.** Son el artefacto que un modelo carga como
  instrucciones, y la de frameworks es la más expuesta a leerse como una guía de arquitectura.
