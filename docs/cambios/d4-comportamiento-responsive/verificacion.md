# Verificación — D4: verificar lo que se renderiza, sin inventar el tamaño de la pantalla

**Estado:** cerrado · **Fecha:** 20-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 20-09-2026,
en **tres pasadas**, corriendo `.\tests\Invoke-Tests.ps1` y `python tests/correr.py -k
d4_comportamiento` con `__pycache__` purgado antes y después de cada una, y sondeando por su cuenta
—con scripts propios contra los módulos en disco— los cinco escenarios que se le pidió mirar con
desconfianza.

**Resultado: 31 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos. Los 31 con
`rojo visto: si`.**

Ninguna pasada encontró un escenario contradicho. Las tres se ocuparon de lo mismo: si las guardas
prueban lo que dicen probar.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `D4` es `CONDITIONAL` sobre `frontendPresent`, identidad intacta | sostenido | sí, las dos mitades | `29_d4_comportamiento_responsive.py::test_e01_d4_es_condicional` |
| E-02 | `TRUE` deja `D4` aplicable con sus dos controles | sostenido | sí, de módulo | `::test_e02_true_hace_aplicable` |
| E-03 | `FALSE` deja `D4` fuera | sostenido | sí, de módulo | `::test_e03_false_hace_no_aplicable` |
| E-04 | Sin señal, `APPLICABILITY_UNRESOLVED` con la que falta | sostenido | sí, de módulo | `::test_e04_sin_senal_queda_sin_resolver` |
| E-05 | Lo ausente nunca es `FALSE`, por cuatro caminos | sostenido | sí, las dos mitades | `::test_e05_lo_ausente_nunca_es_falso` |
| E-06 | La señal es reusable: sumar un consumidor no pide código | sostenido | sí, las dos mitades | `::test_e06_la_senal_es_reusable` |
| E-07 | Backend o API solamente: `NOT_APPLICABLE` | sostenido | sí, las dos mitades | `::test_e07_una_unidad_de_backend_no_aplica` |
| E-08 | Una policy, un check, ninguna review | sostenido | sí, las dos mitades | `::test_e08_una_policy_y_un_check` |
| E-09 | Bootstrap instalado no hace `PASS` | sostenido | sí, las tres | `::test_e09_bootstrap_instalado_no_alcanza` |
| E-10 | Obelisco instalado ni homologado por G1 hacen `PASS` | sostenido | sí, las tres | `::test_e10_obelisco_instalado_no_alcanza` |
| E-11 | Las media queries no hacen `PASS` | sostenido | sí, las tres | `::test_e11_las_media_queries_no_alcanzan` |
| E-12 | Una captura sola no hace `PASS` | sostenido | sí, las tres | `::test_e12_una_captura_sola_no_alcanza` |
| E-13 | La afirmación de alguien tampoco | sostenido | sí, las tres | `::test_e13_la_afirmacion_de_alguien_no_alcanza` |
| E-14 | Sin matriz: `VIEWPORT_MATRIX_UNRESOLVED`, en sus tres formas | sostenido | sí, las dos mitades | `::test_e14_sin_matriz_no_hay_resultado` |
| E-15 | La matriz declara de dónde sale | sostenido | sí, las dos mitades | `::test_e15_la_matriz_declara_de_donde_sale` |
| E-16 | Ningún artefacto de `D4` trae un breakpoint | sostenido | sí, las seis | `::test_e16_no_se_inventan_breakpoints` |
| E-17 | Sin objetivo: `TEST_TARGET_UNAVAILABLE` | sostenido | sí, las dos mitades | `::test_e17_sin_objetivo_no_hay_corrida` |
| E-18 | Recorte o superposición material: `FAIL` | sostenido | sí, específico | `::test_e18_un_defecto_material_falla` |
| E-19 | Una acción crítica inalcanzable: `FAIL` | sostenido | sí, específico | `::test_e19_una_accion_inalcanzable_falla` |
| E-20 | Lo que no se ejecutó no pasa | sostenido | sí, las tres | `::test_e20_lo_que_no_se_ejecuto_no_pasa` |
| E-21 | Todo ejecutado, sin defecto material, con evidencia: `PASS` | sostenido | sí, específico | `::test_e21_todo_ejecutado_y_sin_defecto_pasa` |
| E-22 | El desktop no tapa al mobile | sostenido | sí, las tres | `::test_e22_el_desktop_no_tapa_al_mobile` |
| E-23 | La evidencia está atada al build y al runtime | sostenido | sí, las tres | `::test_e23_la_evidencia_esta_atada_a_la_corrida` |
| E-24 | Misma entrada, mismo resultado | sostenido | sí, específico | `::test_e24_misma_entrada_mismo_resultado` |
| E-25 | Un defecto sin materialidad no se ablanda | sostenido | sí, específico | `::test_e25_un_defecto_sin_materialidad_no_se_ablanda` |
| E-26 | De los siete estados, `PASS` es el único que aprueba | sostenido | sí, de módulo | `::test_e26_solo_pass_aprueba` |
| E-27 | `D4` no es accesibilidad ni es `G1` | sostenido | sí, específico | `::test_e27_d4_no_es_accesibilidad_ni_g1` |
| E-28 | No se crea un segundo framework de automatización | sostenido | sí, específico | `::test_e28_no_se_crea_otro_framework_de_automatizacion` |
| E-29 | La unidad propaga señal, policy y check | sostenido | sí, las dos mitades | `::test_e29_la_unidad_propaga_senal_policy_y_check` |
| E-30 | Los controles dejan de faltar sin tocar la identidad | sostenido | sí, las tres | `::test_e30_los_controles_dejan_de_faltar` |
| E-31 | La tupla `ES0901 / 6.3 / 7.1 / D4` se conserva | sostenido | sí, específico | `::test_e31_la_traza_se_conserva` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los 31 escenarios se vieron
> en rojo con 27 mutaciones deliberadas sobre seis archivos, cada una revertida y con `__pycache__`
> purgado; el refutador reprodujo y extendió el sondeo de E-16 en las tres pasadas.

## E-16, el escenario que costó tres pasadas

El escenario afirma que ningún artefacto de D4 trae un valor de breakpoint ni un modelo de
dispositivo, y que la guarda se prueba contra fugas. El hecho nunca estuvo en duda —el refutador
escaneó los dos archivos por su cuenta en cada pasada: cero números, cero marcas—. Lo que estuvo en
duda las tres veces fue **la red que tiene que atraparlo mañana**.

### Primera versión: una lista de anchos conocidos

Cinco patrones, con una lista canónica `320|360|375|…|1920` y seis marcas. El refutador corrió
dieciséis candidatas y **catorce entraron en verde**, entre ellas las dos formas más idiomáticas:

```
BREAKPOINTS = (640, 900, 1200)      el patron de breakpoints no llevaba re.I
perfil de referencia: Pixel 7        Pixel no estaba entre las seis marcas
```

### Segunda versión: proximidad, y una fuga reescrita

Se sacó la lista canónica y se puso una regla de proximidad —un número cerca de una palabra de
tamaño—, más nueve marcas y `(?i)` en todos. Once de las catorce formas cayeron.

🔴 **Y acá está el error que este documento tiene que registrar.** El refutador había reportado
`escritorio: 1600` como forma que entraba en verde. La fuga que se agregó fue
`escritorio: ancho 1600` — con la palabra `ancho` insertada, que es justo el disparador que el
patrón nuevo necesitaba. La forma cruda seguía entrando, y la lista de fugas decía cubrirla.

Es exactamente el movimiento que el método existe para impedir: acomodar la prueba al resultado. Lo
detectó la segunda pasada, y lo detectó porque el refutador comparó la fuga declarada contra la
forma que él había reportado.

### Tercera versión: un invariante, no una enumeración

El diagnóstico que lo resolvió fue del refutador, de la primera pasada: *"los anchos los arreglaste
bien porque abandonaste la enumeración; las marcas siguen siendo la clase que no tiene esa
propiedad"*. Eso valía un nivel más arriba: **la regla de proximidad seguía siendo una enumeración,
de palabras en vez de números.**

El invariante real es más simple, y se verificó antes de escribirlo:

> Un artefacto de D4 no lleva ningún número, porque el estándar no define ninguno.

Seis patrones, sin lista de anchos y sin proximidad. Las once formas que el refutador había
reportado en verde caen todas, las fugas pasaron a ser las **formas crudas** —incluidas
`escritorio: 1600`, `| movil | 600 |` y `MINIMO = 600`, que él reportó y no estaban—, ningún patrón
quedó muerto, y el barrido de constantes del módulo pasó a ser recursivo: entero suelto, colección,
dict anidado.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Una fuga reescrita para que el patrón la atrapara.** Está arriba. Es el hallazgo más caro de
   los tres cambios de estas dos jornadas, porque no lo detecta ninguna suite: el test estaba verde,
   la lista de fugas se leía completa, y la forma que el escenario promete atrapar entraba igual.
2. **El caso "sin bloque" de E-14 no existía.** La rama `matriz is None` caía al `else` y armaba la
   matriz vacía por segunda vez: la etiqueta prometía una cobertura que nunca corrió. Las tres
   formas corren ahora, y el helper dejó de reinterpretar la intención —`_caso(matriz=None)`
   significaba "usá la de siempre"—.
3. **La aserción de "no hay matriz por defecto" estaba acotada a nombres con `VIEWPORT`.** Un
   `ANCHOS_POR_DEFECTO = (640, 900)` evadía la aserción *y* los patrones.
4. **`EVIDENCIA_QUE_NO_PRUEBA` y `EVIDENCIA_DE_APOYO` son inertes.** Se leen contractuales y no
   mueven una sola decisión: la compuerta real es la lista blanca `EVIDENCIA_DE_CORRIDA`, que es lo
   que hace que una clase de evidencia que nadie previó no pueda aprobar nada. Las aserciones que
   las nombran afirman que una cadena está en una tupla; lo que sostiene E-09 a E-13 son las
   aserciones de estado.
5. **Nada hace cumplir el "unless project coverage is known to be complete"** que la policy escribe
   y que todas las de esta familia vienen escribiendo desde D1. La misma ausencia —"no apareció
   ninguna carpeta frontend"— rotulada `REPOSITORY_CONFIGURATION` en vez de `REPOSITORY_DEPENDENCY`
   saca a D4 del reporte. No contradice ningún escenario: E-05 recorre cuatro caminos que quedan sin
   resolver y E-07 **exige** que la evidencia estructurada resuelva `FALSE`; leer E-05 como
   universal pondría los dos en conflicto.

## Lo que queda abierto, anotado y no escondido

1. **La guarda de E-16 se va a romper por una edición correcta, no por una fuga.** El invariante
   "ningún número" pone en rojo prosa legítima —`pág. 12`, `Bootstrap 5`, `revisado en 2026`— y
   `responsive-ui-required.md` es el **único** de los siete policies instalados que no lleva
   números: los otros citan la página del estándar. El día que alguien le agregue la cita, el caso
   se pone rojo contra contenido correcto y el arreglo bajo presión va a ser aflojar el invariante.
   Anotado en `Pendientes/Fix-Harness/PENDIENTES-FH.md` con la banda que lo resolvería y con las dos
   fugas que esa decisión acepta: `ANCHO = 1_440` —el separador de miles de Python, en un artefacto
   que **es** un `.py`— y la variante en minúscula `fairphone 5`.
2. **El residuo de marcas.** Los números se cubren con un invariante y no dependen de una lista; las
   marcas no tienen invariante equivalente. Se cubren con veinte marcas más la forma genérica
   *marca + número de modelo*, que es lo que hace que la lista no tenga que estar completa. Una
   marca nueva **sin** número de modelo sigue entrando. Declarado en los riesgos de la spec.
3. **Las dos constantes inertes y el "unless" que nadie hace cumplir.** Los dos en
   `PENDIENTES-FH.md`. El segundo es del módulo de señales, heredado de D1, y cerrarlo exige
   re-refutar `D1/E-06`, `D2/E-05`, `D3/E-05` y `D4/E-05`.
4. **"No cambia" se afirma contra literales del propio cambio.** `es0901-7.1-normative-matrix.json`
   sigue sin trackear y `23_matriz_normativa.py` no pinea ninguna fila de D4, así que E-01 y E-30 no
   pueden detectar que se editó la fila *y* se editó la expectativa. Es el idioma del repositorio
   desde D1, no un criterio nuevo.
5. **`controles/` sigue sin llegar a un proyecto instalado.** Los dos controles de D4 se suman a los
   doce que ya estaban así. Ítem 2 de la tabla de prioridades.

## Lo que ningún test cubre y se mira con los ojos

- **Si una aplicación es efectivamente responsive.** Nada de este cambio renderiza nada. Lo que se
  verificó es que una corrida sea lo único que pueda hacerla pasar.
- **Si la matriz declarada es representativa.** Un `TEAM_APPROVED_TEST_PROFILE` con un solo viewport
  de escritorio cumple el contrato y no prueba nada. El check exige que la fuente esté declarada, no
  que la matriz sirva.
- **Si un reporte de corrida dice la verdad.** Rotular una dependencia como `RENDERED_BEHAVIOR_RUN`
  aprueba: nada valida que el contenido de una corrida sea una corrida. La spec lo declara en
  `Qué queda afuera` —la corrida entra como dato— y el check confía en el reporte por contrato.
