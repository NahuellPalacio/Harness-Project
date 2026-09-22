# Verificación — La matriz normativa de §7.1: qué regla aplica, y qué todavía no se sabe

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.19.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el
22-09-2026, en **dos pasadas**, corriendo `python tests/correr.py -k 23_matriz_normativa
--detallado` sobre el árbol de release de 0.19.0 —sin ES0902 O1 ni O2—, y en la segunda también
`-k 25_g2` y `-k 20_orquestacion`, los otros consumidores de `matriz.validar`. La segunda pasada
sumó ocho mutaciones en memoria propias sobre `matriz.py` y `plan.py`.

**Resultado: 24 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

La primera pasada rindió 22 sostenidos, **1 contradicho** —E-12— y **1 sin sustento** —E-23—, y
el cambio no cerró.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La matriz valida contra su schema, y el schema entra en el subconjunto | sostenido | sí | `23_matriz_normativa`, `test_e01_carga_y_valida` |
| E-02 | 24 reglas, ningún id repetido | sostenido | sí | `test_e02_veinticuatro_reglas_sin_repetir` |
| E-03 | El inventario es exactamente G1…M3 | sostenido | sí | `test_e03_el_inventario_exacto` |
| E-04 | Una duplicada da `NORMATIVE_MATRIX_INVALID` y nombra el id | sostenido | sí | `test_e04_una_regla_duplicada_invalida_la_matriz` |
| E-05 | Otra versión da `NORMATIVE_STANDARD_VERSION_MISMATCH` | sostenido | sí | `test_e05_otra_version_del_estandar` |
| E-06 | Una regla que no existe da `NORMATIVE_RULE_NOT_FOUND` | sostenido | sí | `test_e06_una_regla_que_no_existe` |
| E-07 | `ALWAYS` resuelve `APPLICABLE` sin señales | sostenido | sí | `test_e07_always_aplica_sin_senales` |
| E-08 | `CONDITIONAL` con la señal en true da `APPLICABLE` | sostenido | sí | `test_e08_condicional_con_senal_verdadera` |
| E-09 | La señal en false da `NOT_APPLICABLE` | sostenido | sí | `test_e09_condicional_con_senal_falsa` |
| E-10 | Sin la señal, `UNRESOLVED` y nombra la que falta | sostenido | sí | `test_e10_condicional_sin_la_senal` |
| E-11 | Ninguna de las 17 condicionales cae a "no aplica" | sostenido | sí | `test_e11_lo_desconocido_nunca_es_falso` |
| E-12 | Ninguna declara dos señales y el validador lo afirma; dos sin combinación dan `EXPRESSION_UNRESOLVED` | sostenido | sí | `test_e12_dos_senales_sin_modo_de_combinacion` — segunda pasada |
| E-13 | D8 en sus tres estados | sostenido | sí | `test_e13_d8_en_sus_tres_estados` |
| E-14 | Un agente no declarado da `AGENT_REFERENCE_INVALID` y no se crea | sostenido | sí | `test_e14_un_agente_que_el_registro_no_declara` |
| E-15 | Una skill desconocida invalida; `dev-miba` sigue pendiente | sostenido | sí | `test_e15_una_skill_desconocida_y_una_pendiente` |
| E-16 | Resolver no toca el registro | sostenido | sí | `test_e16_resolver_no_toca_el_registro` |
| E-17 | G1 resuelve sus dos policies y sus dos checks | sostenido | sí | `test_e17_g1_resuelve_sus_controles` |
| E-18 | D7 resuelve varias policies y varios checks | sostenido | sí | `test_e18_una_regla_con_varios_controles` |
| E-19 | `DECLARED_*_NOT_INSTALLED`, y la matriz sigue válida | sostenido | sí | `test_e19_los_ids_no_fingen_estar_implementados` |
| E-20 | Las 24 filas tienen cita y ninguna cita quedó sin fila | sostenido | sí | `test_e20_cada_fila_tiene_su_cita` |
| E-21 | `P1.node` y `P1.plataformas` heredan de P1; sin madre no heredan | sostenido | sí | `test_e21_las_clausulas_derivadas_heredan` |
| E-22 | La cita sale del archivo citable, no de la matriz | sostenido | sí | `test_e22_la_cita_no_sale_de_la_matriz` |
| E-23 | `applicableStandards` no cambia y `normative` entra en cada unidad | sostenido | sí | `test_e23_applicable_standards_no_cambio` — segunda pasada, con un plan real |
| E-24 | Misma entrada, mismo resultado | sostenido | sí | `test_e24_misma_entrada_mismo_resultado` |

Todos los tests están en `tests/casos/23_matriz_normativa.py`.

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno.

## E-12, el escenario contradicho en la primera pasada

La spec decía *"Hoy ninguna condicional declara más de una señal, y el cargador lo afirma"*. El
cargador no afirmaba nada: el test contaba las señales por su cuenta, y una matriz en memoria con
D1 en dos señales y sin `combination` pasaba el validador.

```
validar dos senales ('NORMATIVE_MATRIX_VALID', [])
```

**Decisión: se subió el mecanismo, no se angostó el escenario.** `matriz.validar()` ahora rechaza
una condicional con más de una señal y sin `combination` —`NORMATIVE_MATRIX_INVALID`, con un error
que nombra la regla—, y la acepta cuando la combinación está declarada (`ALL` o `ANY`, como ya
preveía el schema). El resolvedor sigue fallando cerrado con `APPLICABILITY_EXPRESSION_UNRESOLVED`
si una regla así le llega sin pasar por el validador. Cuatro mutaciones propias del refutador
—sacar el control, correr el umbral a `> 2`, rechazar aunque haya `combination`, dejar que el
resolvedor invente un AND— ponen el test en rojo.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El validador no hacía lo que la spec decía que hacía** (E-12, arriba). El test estaba verde
   porque se contestaba a sí mismo.
2. **E-23 nunca armaba un plan.** Probaba la función que llena el bloque `normative`, no que el
   bloque llegue al plan sin desplazar a `applicableStandards`. Ahora arma uno con `plan.armar` y
   dos unidades, y afirma que cada una resuelve con sus propias señales. La redacción "al lado"
   era imprecisa —`applicableStandards` vive en la raíz y `normative` en cada `workUnit`— y se
   aclaró con una nota fechada en la spec, que el refutador juzgó una aclaración y no un recorte.
3. **El schema del plan admite propiedades de más en la raíz.** Un `normative` agregado en la raíz
   del plan sigue validando; lo ataja sólo la aserción nueva de E-23.

## Lo que queda abierto, anotado y no escondido

1. **"El cargador" de E-12 es `validar()`, no `cargar()`.** `cargar()` sólo controla la versión.
   La spec usa "cargador" en ese sentido amplio también en otras secciones; no cambia el veredicto.
2. **El schema del plan no cierra su raíz** (punto 3 de arriba). Va a
   `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

## Lo que ningún test cubre y se mira con los ojos

Que las citas de las 24 filas digan lo que dice ES0901 6.3. E-20 y E-22 prueban que cada fila
tiene su cita y que sale del archivo citable; que el archivo citable transcriba bien la norma sólo
se ve leyéndolo contra el estándar.
