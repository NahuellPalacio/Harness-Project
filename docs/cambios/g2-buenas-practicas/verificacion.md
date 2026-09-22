# Verificación — G2: la primera regla que no se puede reducir a un check

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.19.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el
22-09-2026, en **tres pasadas**, corriendo `python tests/correr.py -k 25_g2 --detallado` y
`-k 28_d3` —la otra review que usa el mismo contrato— sobre el árbol de release de 0.19.0, sin
ES0902 O1 ni O2. La segunda y la tercera pasada sumaron mutaciones en memoria propias sobre
`revisiones.py` y el schema de revisión.

**Resultado: 24 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| Pasada | Sostenidos | Sin sustento |
|---|---|---|
| Primera | 22 | E-13, E-20 |
| Segunda | 23 | E-13, la mitad de tecnología |
| Tercera | 24 | — |

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | G2 es `ALWAYS`, aplica sin señales | sostenido | sí | `25_g2`, `test_e01_g2_aplica_siempre` |
| E-02 | Una policy, cero checks, una review | sostenido | sí | `test_e02_una_policy_cero_checks_una_review` |
| E-03 | La review se instala sin fabricar un check | sostenido | sí | `test_e03_no_se_fabrico_un_check_para_simetria` |
| E-04 | `REVIEW` es un tipo del registro; `reviews` es opcional | sostenido | sí | `test_e04_review_es_un_tipo_y_reviews_es_opcional` |
| E-05 | El schema de revisión valida y entra en el subconjunto | sostenido | sí | `test_e05_el_schema_de_revision` |
| E-06 | La opinión del agente sola no llega a `COMPLIANT` | sostenido | sí | `test_e06_la_opinion_del_agente_no_alcanza` |
| E-07 | `OFFICIAL_TECHNOLOGY_DOCUMENTATION` es fuente reconocida | sostenido | sí | `test_e07_la_documentacion_oficial_si_alcanza` |
| E-08 | `PROJECT_CONVENTION` sola no prueba reconocimiento | sostenido | sí | `test_e08_la_convencion_del_proyecto_no_prueba_reconocimiento` |
| E-09 | Una evidencia que no existe hace inválida la revisión | sostenido | sí | `test_e09_un_hallazgo_que_referencia_evidencia_que_no_existe` |
| E-10 | Sin aplicabilidad, `UNRESOLVED`, nunca `NOT_APPLICABLE` | sostenido | sí | `test_e10_aplicabilidad_sin_resolver` |
| E-11 | `NOT_APPLICABLE` exige su motivo | sostenido | sí | `test_e11_no_aplicable_exige_motivo` |
| E-12 | La modalidad de la fuente se conserva | sostenido | sí | `test_e12_la_modalidad_de_la_fuente_se_conserva` |
| E-13 | Sin tecnología, o sin versión donde la guía depende de ella: `REVIEW_INCOMPLETE` | sostenido | sí | `test_e13_falta_el_contexto_de_version` — tercera pasada |
| E-14 | Desvío de un `REQUIRED_BY_SOURCE`: `NON_COMPLIANT` | sostenido | sí | `test_e14_apartarse_de_lo_exigido` |
| E-15 | Desvío de un `RECOMMENDED_BY_SOURCE`: `COMPLIANT_WITH_OBSERVATIONS` | sostenido | sí | `test_e15_apartarse_de_una_recomendacion` |
| E-16 | Sin evidencia material: `REVIEW_INCOMPLETE` | sostenido | sí | `test_e16_falta_evidencia_material` |
| E-17 | Una justificación no aprueba: `JUSTIFICATION_PENDING` | sostenido | sí | `test_e17_una_justificacion_no_aprueba_la_excepcion` |
| E-18 | `SOURCE_CONFLICT` conserva las dos fuentes | sostenido | sí | `test_e18_dos_fuentes_que_se_contradicen` |
| E-19 | G1 `HOMOLOGATED` no hace `COMPLIANT` a G2 | sostenido | sí | `test_e19_g1_no_hace_cumplir_a_g2` |
| E-20 | La review manda a reusar el inventario de G1; no hay segundo detector | sostenido | sí | `test_e20_el_inventario_de_g1_se_reusa` — redacción angostada |
| E-21 | Un agente no declarado invalida la revisión | sostenido | sí | `test_e21_los_agentes_tienen_que_estar_declarados` |
| E-22 | La unidad lleva `declaredReviews` sin romper policies ni checks | sostenido | sí | `test_e22_la_unidad_lleva_declared_reviews` |
| E-23 | `DECLARED_REVIEW_NOT_INSTALLED` antes; después desaparece | sostenido | sí | `test_e23_la_review_deja_de_faltar` |
| E-24 | La revisión conserva ES0901 / 6.3 / 7.1 / G2 | sostenido | sí | `test_e24_la_revision_conserva_su_traza` |

Todos los tests están en `tests/casos/25_g2_buenas_practicas.py`.

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **`resolver()` nunca leía la versión.** El test de E-13 mezclaba una fuerza `UNRESOLVED` con
   una versión ausente, y el `REVIEW_INCOMPLETE` salía sólo de la fuerza: con la versión en `None`
   y lo demás bien, la revisión daba `COMPLIANT`. **Se subió el mecanismo.** Un hallazgo declara
   ahora `versionDependent` —booleano, opcional, `false` por defecto, así que D3 y toda revisión
   vieja resuelven igual— y, si lo es y el sujeto no trae versión, `revisiones.resolver` suma
   `REVIEW_VERSION_CONTEXT_MISSING` y da `REVIEW_INCOMPLETE`. El control corre antes que la
   aplicabilidad: un `NOT_APPLICABLE` dependiente de versión y sin versión tampoco cierra. El
   refutador lo juzgó coherente con E-10 —*"Missing context resolves to UNRESOLVED, never to
   NOT_APPLICABLE"*— y sin contradicción con E-11, que es una condición de validez y no de
   resultado.
2. **La mitad de tecnología de E-13 no la probaba nada.** La frenan dos guardas —el `required` de
   `subject.id` en el schema y el control de `validar_estructura`— y sacar las dos dejaba la suite
   en verde con una revisión sin sujeto en `COMPLIANT`. Ahora el test afirma cada guarda por su
   propio mensaje, y cada una sola lo pone en rojo. El string vacío sólo lo frena la segunda.
3. **E-20 afirmaba un reuso que no tiene camino de código.** El test comparaba el literal
   `"angular"` contra una lista armada en el mismo test que contenía `"angular"`. Nadie produce
   el inventario de G1: la spec de G1 deja afuera detectar qué tecnologías usa un proyecto.
   **Se angostó la redacción**, con nota fechada, a lo que hoy se puede romper: `revisiones.py` no
   abre más archivo que su schema —por AST—, no nombra manifiestos ni define detectores, la review
   manda a tomar el inventario de G1 y `controles/reviews/` no tiene código. La sección "Pasar G1
   no es pasar G2", que todavía decía "se reusa" como hecho, se alineó en la tercera pasada.

## Lo que queda abierto, anotado y no escondido

1. **El reuso del inventario de G1 es una instrucción, no un hecho probado.** Lo va a ser el día
   que algo produzca ese inventario. Va a `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
2. **El análisis por AST de E-20 tiene dos agujeros conocidos:** una lectura a nivel de módulo
   —fuera de toda función— y una llamada a `subprocess` pasan en verde. Ninguno contradice el
   escenario hoy. Van al mismo lugar.

## Lo que ningún test cubre y se mira con los ojos

Que un agente, en una sesión real, arme la revisión con fuentes reconocidas y no con su opinión.
El contrato la rechaza si no las trae —E-06 a E-09—; que la traiga bien sólo se ve leyendo una.
