# Verificación — D3: la primera regla que es condicional y además no se puede comprobar

**Estado:** cerrado · **Fecha:** 20-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 20-09-2026,
en dos pasadas, corriendo `.\tests\Invoke-Tests.ps1`, `python tests/correr.py -k 28_d3` y
`-k g2_buenas`, y sondeando por su cuenta —en memoria, sin tocar el árbol— los cuatro escenarios que
se le pidió mirar con desconfianza. La primera pasada dejó **dos sin sustento** —E-10 y E-11—; la
segunda, después de cambiar el mecanismo, los dio por sostenidos.

**Resultado: 28 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos. Los 28 con
`rojo visto: si`.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `D3` es `CONDITIONAL` y su identidad normativa no cambia | sostenido | sí, de módulo | `28_d3_diseno_orientado_a_objetos.py::test_e01_d3_es_condicional` |
| E-02 | `TRUE` deja `D3` aplicable, con policy y review | sostenido | sí, de módulo | `::test_e02_true_hace_aplicable` |
| E-03 | `FALSE` deja `D3` fuera | sostenido | sí, de módulo | `::test_e03_false_hace_no_aplicable` |
| E-04 | Sin señal, `APPLICABILITY_UNRESOLVED` con la que falta | sostenido | sí, de módulo | `::test_e04_sin_senal_queda_sin_resolver` |
| E-05 | Lo ausente nunca es `FALSE`, por cuatro caminos | sostenido | sí, las dos mitades | `::test_e05_lo_ausente_nunca_es_falso` |
| E-06 | La señal se resuelve una vez y la reusan sus cuatro consumidores | sostenido | sí, las tres | `::test_e06_la_senal_la_reusan_sus_cuatro_consumidores` |
| E-07 | Una policy, cero checks, una review | sostenido | sí, específico | `::test_e07_una_policy_cero_checks_una_review` |
| E-08 | No se fabrica ningún check mecánico de OOP | sostenido | sí, específico | `::test_e08_no_se_fabrica_un_check_de_oop` |
| E-09 | La review reusa la infraestructura de G2 | sostenido | sí, específico | `::test_e09_la_review_reusa_la_infraestructura_de_g2` |
| E-10 | Un conteo de clases no es un hallazgo: falta la dimensión | sostenido | sí, las cuatro | `::test_e10_un_conteo_de_clases_no_es_un_hallazgo` |
| E-11 | Una jerarquía de herencia tampoco | sostenido | sí, las dos mitades | `::test_e11_una_jerarquia_de_herencia_tampoco` |
| E-12 | El framework elegido no alcanza | sostenido | sí, las tres | `::test_e12_el_framework_elegido_no_alcanza` |
| E-13 | La afirmación de un agente, sin evidencia, no alcanza | sostenido | sí, las dos mitades | `::test_e13_la_afirmacion_de_un_agente_no_alcanza` |
| E-14 | La evidencia de la implementación produce `COMPLIANT` | sostenido | sí, específico | `::test_e14_la_evidencia_de_la_implementacion_cumple` |
| E-15 | Evidencia incompleta: `REVIEW_INCOMPLETE` | sostenido | sí, las dos mitades | `::test_e15_evidencia_incompleta_no_cumple` |
| E-16 | Un desvío material: `NON_COMPLIANT` | sostenido | sí, las dos mitades | `::test_e16_un_desvio_material_no_cumple` |
| E-17 | Un desvío sin materialidad no se ablanda | sostenido | sí, las dos mitades | `::test_e17_un_desvio_sin_materialidad_no_se_ablanda` |
| E-18 | El conflicto de paradigma se expone | sostenido | sí, específico | `::test_e18_el_conflicto_se_expone` |
| E-19 | El conflicto no se autoaprueba | sostenido | sí, las tres | `::test_e19_el_conflicto_no_se_autoaprueba` |
| E-20 | `G2 COMPLIANT` no es `D3 COMPLIANT` | sostenido | sí, las tres | `::test_e20_g2_compliant_no_es_d3_compliant` |
| E-21 | Un patrón de P2 no es `D3 COMPLIANT` | sostenido | sí, las dos mitades | `::test_e21_un_patron_no_es_d3_compliant` |
| E-22 | El estilo de P3 no es `D3 COMPLIANT` | sostenido | sí, las tres | `::test_e22_el_estilo_no_es_d3_compliant` |
| E-23 | El inventario de G1 se reusa | sostenido | sí, las cuatro | `::test_e23_el_inventario_de_g1_se_reusa` |
| E-24 | La evidencia de G2 apoya y no aprueba | sostenido | sí, las cuatro | `::test_e24_la_evidencia_de_g2_apoya_y_no_aprueba` |
| E-25 | Los agentes salen del registro | sostenido | sí, específico | `::test_e25_los_agentes_salen_del_registro` |
| E-26 | La unidad propaga señal, policy y review | sostenido | sí, las tres | `::test_e26_la_unidad_propaga_senal_policy_y_review` |
| E-27 | Los controles dejan de faltar sin tocar el texto normativo | sostenido | sí, las tres | `::test_e27_los_controles_dejan_de_faltar` |
| E-28 | La tupla `ES0901 / 6.3 / 7.1 / D3` se conserva | sostenido | sí, específico | `::test_e28_la_traza_se_conserva` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los 28 escenarios se vieron
> en rojo con 30 mutaciones deliberadas sobre siete archivos, cada una revertida; el refutador
> reprodujo seis de ellas por su cuenta, en memoria y sin tocar el árbol.

## E-10 y E-11, los dos que la primera pasada dejó sin sustento

El escenario decía *"que existan clases no hace `COMPLIANT`"*. El test armaba una revisión cuyo
único respaldo era *"el módulo define 240 clases"* con `sourceType: PROJECT_CONVENTION` y
comprobaba `REVIEW_INCOMPLETE`.

**Lo que el refutador encontró: el test pasaba por la razón equivocada.** Lo que hacía fallar la
revisión era la **clase de fuente**, no el contenido del `claim` —el módulo nunca lee un claim—, y
esa etiqueta contradice al propio contrato de la review, que define `PROJECT_IMPLEMENTATION` como
*"what the code actually does"*. Un conteo de clases de este módulo es exactamente eso. Con la
etiqueta que el contrato manda usar:

```
evidencia {sourceType: PROJECT_IMPLEMENTATION, claim: "el modulo define 240 clases"}
hallazgo  {status: ADOPTED, materiality: MINOR}
                                                      ->  COMPLIANT
```

Es decir: una revisión respaldada sólo por "existen clases" **sí** llegaba a cumplir. El test
probaba una proposición vecina —que `PROJECT_CONVENTION` no sostiene un hallazgo de D3, que ya es
E-13— y no la del escenario.

**La decisión: el mecanismo, no el texto.** Se podía achicar el escenario a lo que el test
verificaba; no se hizo. Un hallazgo de D3 ahora tiene que declarar **qué dimensión del diseño
evalúa**, de un vocabulario cerrado de ocho:

```text
responsibility-encapsulation · cohesion · controlled-coupling · abstraction-boundaries
layer-responsibilities · framework-native-organization · procedural-concentration
collaboration-maintainability
```

Un conteo no está ahí y no puede estar: "define 240 clases" es un hecho del código, no una propiedad
de su diseño. Sin dimensión declarada, o con una fuera del vocabulario, la revisión es
estructuralmente inválida. El refutador corrió su propio contraejemplo contra el mecanismo nuevo:

```
sin dimension          -> REVIEW_INCOMPLETE
dimension ''           -> REVIEW_INCOMPLETE
dimension None         -> REVIEW_INCOMPLETE
dimension 123          -> REVIEW_INCOMPLETE
dimension class-count  -> REVIEW_INCOMPLETE
```

**Y lo que el mecanismo no cierra quedó clavado en verde.** E-11 asserta que un hallazgo que declara
`abstraction-boundaries` citando esa misma evidencia **sí** da `COMPLIANT`. Eso es juicio de quien
revisa, ningún test lo puede contradecir, y está escrito en tres lugares: la tabla de
`## Cómo se verifica`, la frase que dice que ningún test de este cambio promete atraparlo, y esa
aserción. El día que alguien lo cierre, el test se pone rojo y obliga a hablarlo.

El texto de los dos escenarios se reescribió para decir eso y no menos. Ninguna proposición se mudó
de número, de grupo ni desapareció.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-10 y E-11 pasaban por la clase de fuente, no por lo que afirmaban.** Está arriba. Es la
   segunda vez en tres cambios que un test verde resulta estar probando una proposición vecina
   —la primera fue `D1 / E-28`— y las dos veces lo encontró el sondeo por mutación semántica, no la
   suite.
2. **La cláusula del disco de E-08 era un filtro de nombres.** Buscaba `oop`, `object`, `design` y
   `high-level` entre los `.py` de `controles/checks/`: un check de D3 llamado `class-count.py` la
   esquivaba. Se cambió por `controles.descubrir_no_declarados() == []` sobre el árbol real más la
   ausencia de un `CHECK` con `rule: D3` en el registro. Con las dos, un check de D3 no tiene por
   dónde entrar, se llame como se llame.
3. **"Sobre el mismo sistema" en E-20 era encuadre narrativo.** Las dos reviews tenían `subject`
   distintos y evidencias distintas: la no-implicación quedaba demostrada, pero no sobre nada
   común. Ahora comparten la lista de evidencia y cada hallazgo referencia la que su regla admite.
4. **La premisa de la sección sobre G2 era falsa.** La spec decía que G2 está *"verificado y
   cerrado"*. No lo está: `g1-tecnologias-homologadas/` y `g2-buenas-practicas/` tienen `spec.md` y
   no tienen `verificacion.md`. Están **construidos y sin refutar**. Corregido en la spec, con la
   corrección visible.
5. **`applicability: NOT_APPLICABLE` borra el estado de un hallazgo.** En `revisiones.resolver` la
   rama de aplicabilidad corre antes que la de `status`, así que un hallazgo que declara
   `TECHNOLOGY_PARADIGM_CONFLICT` —o `JUSTIFICATION_PENDING`, o `EVIDENCE_MISSING`— y
   `NOT_APPLICABLE` resuelve a `COMPLIANT` con `states` e `issues` vacíos: el conflicto desaparece
   sin rastro. Es precedencia heredada de G2, D3 no la introdujo, y los tres escenarios que la
   contradirían —`G2/E-16`, `G2/E-17`, `D3/E-19`— están sostenidos hoy **porque ningún test combina
   los dos campos**. Queda abierto abajo.
6. **`resolver` tiene una rama muerta.** `if peso is None or peso == "UNRESOLVED"`: la primera mitad
   es inalcanzable, porque `validar_estructura` ya rechaza el eje ausente. No cambia ninguna salida.
   El refutador lo reportó dos veces —la segunda porque yo lo había dado por anotado y no lo
   estaba—, y ahora sí lo está.

## Lo que el cambio le toca a G2, verificado aparte

`revisiones.py` deja de tener una sola regla de evidencia, y G2 es una de las dos filas de la tabla.
El refutador lo corrió, no lo dedujo:

```
G2 DEVIATION REQUIRED_BY_SOURCE          -> NON_COMPLIANT
G2 DEVIATION RECOMMENDED_BY_SOURCE       -> COMPLIANT_WITH_OBSERVATIONS
G2 con sola evidencia de implementacion  -> REVIEW_INCOMPLETE
G2 DEVIATION sin practiceStrength        -> REVIEW_INCOMPLETE
G2 con materiality y sin practiceStrength-> REVIEW_INCOMPLETE  (no pesa por el eje ajeno)
G2 con una dimension inventada           -> COMPLIANT          (no se le exige vocabulario)
una regla sin fila, DEVIATION REQUIRED   -> NON_COMPLIANT      (hereda la fila de G2)
```

`G2 / E-04`, `E-06`, `E-14` y `E-15` siguen **sostenidos**, 80/80.

`E-04` es el que este cambio tocó: su aserción contaba 23 filas de la matriz sin `reviews`, y ese
número bajó a 22 cuando D3 declaró la suya. Lo que el escenario afirma —que el campo es opcional y
una fila sin él sigue siendo válida— no cambió; lo que estaba mal escrito era el test, que medía el
calendario. Se reescribió la aserción para que afirme la opcionalidad —`sin_reviews > con_reviews`,
las dos listas partiendo la matriz entera, y la matriz válida— y no el conteo.

Un aflojamiento real y sin efecto alcanzable: el schema solo ya no rechaza un hallazgo de G2 sin
`practiceStrength`. El único llamador de `validar_schema` es `validar_estructura`, que reimpone el
eje por regla. Lo mismo vale para el vocabulario de dimensiones, que vive en el módulo y no en el
schema.

## Lo que queda abierto, anotado y no escondido

1. **`applicability: NOT_APPLICABLE` borra el estado de un hallazgo, incluido un conflicto de
   paradigma.** Anotado en `Pendientes/Fix-Harness/PENDIENTES-FH.md` con la reproducción del
   refutador. Fuera del alcance de este cambio: es del módulo, heredado de G2, y cerrarlo exige
   re-refutar `G2/E-16` y `G2/E-17` además de `D3/E-19`.
2. **La rama muerta de `resolver`.** Anotada en el mismo archivo.
3. **El vocabulario de dimensiones vive en el módulo y no en el schema.** Un consumidor que validara
   sólo contra el schema aceptaría `class-count`. Hoy no hay ninguno: el único llamador de
   `validar_schema` es `validar_estructura`.
4. **G1 y G2 están construidos y sin refutar.** Es el ítem 4 de la tabla de prioridades de
   `PENDIENTES-FH.md`, y este cambio se apoya en los dos.
5. **Nada de esto está en `HEAD`.** `revisiones.py`, la matriz, el registro, el schema y los archivos
   de tests siguen sin trackear, igual que todo G1, G2, D1 y D2. Las afirmaciones de la forma "no
   cambió" se verifican contra los literales que el test fija, no contra una revisión anterior.
6. **El reuso del inventario de G1 es una declaración, no un camino de código.** Ningún módulo fuera
   de `anexo2.py` lee el catálogo, y `revisiones.py` nunca lo toca. La spec saca de alcance juntar
   la evidencia, así que lo verificado es que el alcance esté declarado en el contrato de la review.
7. **`controles/` sigue sin llegar a un proyecto instalado.** Los dos controles de D3 se suman a los
   diez que ya estaban así. Ítem 2 de la tabla de prioridades.

## Lo que ningún test cubre y se mira con los ojos

- **Si una revisión acierta sobre el diseño de un sistema.** Un revisor puede declarar
  `cohesion: ADOPTED` citando un conteo de clases y la estructura lo acepta. Es el límite de
  cualquier review y está escrito en los riesgos de la spec.
- **Si el vocabulario de ocho dimensiones alcanza.** Una revisión sobre un paradigma que no encaje
  en ninguna va a forzar la que menos le queda mal en vez de declarar el conflicto. Se ve usándolo.
- **Si `TECHNOLOGY_PARADIGM_CONFLICT` se vuelve la salida de lo incómodo.** Deja el resultado
  incompleto sin obligar a nada y no hay todavía quien lo resuelva.
