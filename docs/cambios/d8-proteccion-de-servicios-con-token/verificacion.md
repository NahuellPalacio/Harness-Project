# Verificación — D8: los servicios están protegidos con sistema de token

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` los días
21 y 22-09-2026, en **dos pasadas**, corriendo `python tests/correr.py -k 35_d8` y la compuerta
completa `.\tests\Invoke-Tests.ps1`, y con una batería de **71 mutaciones** propias sobre el check y
la policy — no se conformó con que el test estuviera verde: para cada escenario buscó una mutación
plausible que lo falsificara y dejara la suite en verde.

**Resultado: 39 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

La primera pasada rindió **34 sostenidos y 5 sin sustento** —E-02, E-16, E-18, E-34 y E-35— y el
cambio no cerró. 🔴 **Ninguno era un defecto del check.** En los cinco el comportamiento era
exactamente el que la spec pide; lo que faltaba era el mecanismo que lo sostuviera. El check **no se
tocó en toda la verificación**: las correcciones fueron todas del lado de los tests.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | El binding —policy, check, señal, agentes y tupla— sale de la fila, y el módulo no los escribe | sostenido | sí | `35_d8`, `test_e01_el_binding_sale_de_la_matriz` |
| E-02 | Sin fila resoluble, `D8_MATRIX_BINDING_UNRESOLVED`: nueve formas, siete por documento y dos por ruta | sostenido | sí, las dos mitades | `35_d8`, `test_e02_sin_fila_resoluble_falla_cerrado` |
| E-03 | El binding corre antes que la señal | sostenido | sí | `35_d8`, `test_e03_el_binding_corre_antes_que_la_senal` |
| E-04 | La fila no se edita, y tiene las claves de toda fila de diseño | sostenido | sí | `35_d8`, `test_e04_la_fila_no_se_edita` |
| E-05 | TRUE hace a D8 aplicable | sostenido | sí | `35_d8`, `test_e05_true_hace_aplicable` |
| E-06 | FALSE lo deja `NOT_APPLICABLE`, y el check también | sostenido | sí | `35_d8`, `test_e06_false_hace_no_aplicable` |
| E-07 | Sin la señal, `APPLICABILITY_UNRESOLVED` con el nombre de la que falta | sostenido | sí | `35_d8`, `test_e07_sin_senal_no_se_resuelve` |
| E-08 | La ausencia nunca es FALSE por las dos clases débiles, y el límite de la etiqueta está dicho | sostenido | sí, las dos mitades | `35_d8`, `test_e08_la_ausencia_nunca_es_false` |
| E-09 | Ninguna otra señal sustituye: `SIGNAL_IDENTITY_MISMATCH` | sostenido | sí | `35_d8`, `test_e09_ninguna_otra_senal_sustituye`, sobre todas las señales de la matriz |
| E-10 | D8 no crea ni modifica agente ni skill | sostenido | sí | `35_d8`, `test_e10_d8_no_crea_agente_ni_skill` |
| E-11 | Una dependencia de tokens, sola, no pasa | sostenido | sí | `35_d8`, `test_e11_la_dependencia_sola_no_pasa` |
| E-12 | Un middleware declarado, solo, no pasa | sostenido | sí | `35_d8`, `test_e12_el_middleware_solo_no_pasa` |
| E-13 | La emisión y el login, solos, no pasan | sostenido | sí | `35_d8`, `test_e13_la_emision_y_el_login_solos_no_pasan` |
| E-14 | Las ocho clases inertes, una por una | sostenido | sí | `35_d8`, `test_e14_las_ocho_clases_inertes` |
| E-15 | Las ocho formas de inventario incompleto | sostenido | sí | `35_d8`, `test_e15_el_inventario_incompleto_no_se_resuelve` |
| E-16 | Las nueve clases de camino, nombradas una por una | sostenido | sí | `35_d8`, `test_e16_las_nueve_clases_de_camino` |
| E-17 | Sin mecanismo declarado, `TOKEN_MECHANISM_UNRESOLVED`: siete formas del hueco | sostenido | sí | `35_d8`, `test_e17_sin_mecanismo_no_se_inventa` |
| E-18 | Ningún artefacto lleva el contrato del token, rol y scope incluidos | sostenido | sí, las tres mitades | `35_d8`, `test_e18_ningun_artefacto_lleva_el_contrato`: 5 artefactos, 10 resultados, 51 fugas crudas, 25 textos limpios |
| E-19 | El código de rechazo no se exige sin contrato, y el módulo no declara ninguna constante numérica | sostenido | sí | `35_d8`, `test_e19_el_codigo_de_rechazo_no_se_exige` |
| E-20 | `NO_TOKEN` alcanzando el comportamiento protegido da `FAIL` | sostenido | sí | `35_d8`, `test_e20_sin_token_llegando_falla` |
| E-21 | `INVALID_TOKEN` alcanzando da `FAIL` | sostenido | sí | `35_d8`, `test_e21_token_invalido_llegando_falla` |
| E-22 | `VALID_TOKEN` aporta la positiva, y el camino que no funciona no la completa | sostenido | sí | `35_d8`, `test_e22_el_token_valido_aporta_la_positiva` |
| E-23 | Las dos negativas son obligatorias; sin objetivo, `TEST_TARGET_UNAVAILABLE` | sostenido | sí | `35_d8`, `test_e23_las_dos_negativas_son_obligatorias` |
| E-24 | Lo mockeado se distingue y no llega a `PASS` | sostenido | sí | `35_d8`, `test_e24_lo_mockeado_no_llega_a_pass` |
| E-25 | El camino feliz no tapa la ruta alterna, y lo no declarado no es ni `FAIL` ni `PASS` | sostenido | sí, las tres direcciones | `35_d8`, `test_e25_el_camino_feliz_no_tapa_la_ruta_alterna` |
| E-26 | El bypass por método alterno da `FAIL` | sostenido | sí | `35_d8`, `test_e26_el_metodo_alterno` |
| E-27 | La ruta vieja y la versionada se detectan | sostenido | sí | `35_d8`, `test_e27_la_ruta_vieja_y_la_versionada` |
| E-28 | Las ocho clases que no son la primaria, nombradas una por una | sostenido | sí | `35_d8`, `test_e28_las_ocho_clases_que_no_son_la_primaria` |
| E-29 | El inactivo no es un bypass; el que no lo declara no se da por apagado | sostenido | sí | `35_d8`, `test_e29_un_camino_inactivo_no_es_un_bypass` |
| E-30 | El público sin excepción autoritativa queda sin resolver | sostenido | sí | `35_d8`, `test_e30_el_publico_sin_excepcion` |
| E-31 | Las siete categorías, una por una, con el mismo resultado | sostenido | sí | `35_d8`, `test_e31_ninguna_categoria_se_exime_sola` |
| E-32 | No hay lista de exenciones ni comparación contra el nombre de un endpoint | sostenido | sí | `35_d8`, `test_e32_no_hay_lista_de_exenciones`, por AST |
| E-33 | Un `PASS` no afirma autorización | sostenido | sí | `35_d8`, `test_e33_un_pass_no_afirma_autorizacion` |
| E-34 | Un `PASS` no implica D1 ni D2, y ninguna cadena del módulo los nombra | sostenido | sí | `35_d8`, `test_e34_un_pass_no_implica_d1_ni_d2`, sobre las 377 cadenas literales |
| E-35 | Un `PASS` no implica otro estándar ni una aprobación | sostenido | sí | `35_d8`, `test_e35_un_pass_no_implica_otro_estandar`, sobre las 377 cadenas literales |
| E-36 | La unidad propaga los controles exactos de la fila | sostenido | sí | `35_d8`, `test_e36_la_unidad_propaga_los_controles_exactos` |
| E-37 | Veintiséis controles, diez reglas completas, sin archivos sueltos | sostenido | sí | `35_d8`, `test_e37_los_controles_dejan_de_ser_un_hueco` |
| E-38 | Todo resultado conserva la tupla, menos el del binding, que lo dice | sostenido | sí | `35_d8`, `test_e38_todo_resultado_conserva_la_traza` |
| E-39 | Los diez estados se alcanzan y sólo `PASS` aprueba | sostenido | sí | `35_d8`, `test_e39_los_estados_existen_y_solo_pasa_uno` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide ADR-0006:
> un test que nunca se vio fallar no probó que puede fallar. Los 39 escenarios de este cambio llevan
> `sí`: la pasada de mutaciones propia fue de 45 mutaciones, más 14 sobre los escenarios corregidos,
> y cada escenario se vio en rojo por al menos una.

Compuerta en la que se rindió el veredicto final:

```
python tests/correr.py -k 35_d8             ->  8083/8083   (eran 876 en la primera pasada)
.\tests\Invoke-Tests.ps1                    ->  17410/17410, exit 0
```

## Lo que la verificación encontró y no habría encontrado un test verde

Los cinco hallazgos de la primera pasada **no salieron de un test en rojo**: los 876 tests estaban
verdes y la compuerta cerraba. Salieron de una batería de mutaciones y de una regla explícita —un
escenario está sostenido cuando toda mutación plausible que lo falsifica pone la suite en rojo— y se
agrupan en tres causas que conviene no repetir:

1. **Una constante que el test recorre en vez de clavar.** E-16 afirmaba que las nueve clases de
   camino entran en el inventario, y el bucle recorría `CHECK.CLASES` clavando sólo el conteo.
   Cuatro de los nueve nombres —`SECONDARY_CONTROLLER`, `GATEWAY_EXPOSED`, `ADMINISTRATIVE`,
   `UPLOAD_DOWNLOAD`— no estaban como literal en ningún test: renombrar cualquiera dejaba la suite
   verde, y con el nombre cambiado un camino de esa clase **dejaba de entrar al inventario**. Es la
   clase que la propia spec pone de ejemplo de la trampa de esta regla. Es la tercera vez que este
   defecto aparece: D7/E-39 con un límite numérico y D8/E-08 y E-23 con dos constantes que encontré
   yo en la pasada de mutaciones.

2. **Un ítem del escenario sin patrón en el barrido.** E-18 enumera quince cosas que ningún
   artefacto puede nombrar, y **dos no tenían ningún patrón: un rol y un scope**. La propia policy
   promete en prosa que no se atribuyen, y esa promesa era la única de las quince sin sostén:
   agregarle `scope: tramites-escritura` dejaba la suite verde.

3. **Una afirmación universal muestreada sobre diez.** E-34 y E-35 afirman que *ningún* resultado
   nombra otra regla o declara una aprobación, y el test barría los diez resultados de `_caminos()`,
   uno por estado. Una rama que ningún camino muestreado alcanza —el detalle de una sonda negativa
   que no fue rechazada— podía nombrar `D1` o `ES0902` sin que nadie lo viera. Y E-35 tenía además un
   agujero de vocabulario: la lista no incluía **`aprobación`**, que es la palabra con la que está
   escrito el escenario.

El segundo veredicto sostuvo los cinco y dejó dos observaciones, **las dos cerradas antes de este
documento**, y las dos de la misma familia —un barrido que falla sin motivo es un barrido que
alguien apaga—:

4. **El patrón de `scope` se disparaba con prosa correcta.** `In scope:`, `Out of scope:`, `the scope
   of the WorkUnit` son formas que este repositorio escribe todo el tiempo en sus artefactos en
   inglés, y el refutador lo probó como mutación: agregarle `In scope: el borde del servicio.` a la
   policy ponía la suite en rojo. Yo había sacado `alcance` de los patrones por esta misma razón y
   dejé `scope`, que es cómo se dice lo mismo del otro lado del ADR-0011. Ahora las formas de
   discurso se sacan del texto antes de barrer —**sólo las inglesas**: en castellano este repositorio
   escribe `alcance`, así que `el scope de escritura` sigue siendo una fuga— y una clave estructural
   `scope: {` tampoco dispara. Seis textos limpios nuevos lo clavan.

5. **La frontera de E-35 no era «oración vs. identificador» sino «con espacio vs. sin espacio».** De
   los 377 literales del módulo, **329 no tienen espacio**, y entre ellos están todos los `reason` y
   los `state`, que son justamente lo que un resultado publica: `"detail":
   "SECURITY_ASSESSMENT_APPROVED"` en una rama no muestreada quedaba verde. Ahora se barren todas las
   cadenas y las dos legítimas —`TEAM_APPROVED_TEST_PROFILE`, una fuente de cobertura, y
   `dev-security-assessment`, una skill instalada— están **nombradas una por una** en vez de
   excluidas por su forma.

## Lo que queda abierto, anotado y no escondido

- **El barrido de rol y scope no cubre todas las redacciones.** El refutador lo midió: `rol
  administrador`, `ROLE_ADMIN`, `el rol "gestor"`, `los roles permitidos son admin y operador`, `el
  scope es tramites.escritura` y `con scope amplio` no se detectan. No es el hueco del primer
  veredicto —ahí el ítem no tenía **ningún** patrón y la forma canónica pasaba—: un barrido de texto
  nunca cubre todas las redacciones, y lo que la spec exige de esa mitad es que las formas declaradas
  se detecten en crudo, cosa que hacen las 51. Queda dicho para que nadie lea el verde como *«no
  puede entrar un rol»*.
- **Tres ayudantes de evidencia duplicados por tercera vez.** Normalizar un dato declarado, atar la
  evidencia al build y resolver referencias huérfanas están ahora en el check de D6, en el `lib/` de
  D7 y en el de D8: unas 60 líneas por tres, y la próxima regla condicional las hace cuatro. Es un
  ítem nuevo de `Pendientes/Fix-Harness/PENDIENTES-FH.md` con su arreglo para
  `harness-staff-engineer` y con la razón de no hacerlo acá: tocaría dos cambios ya verificados desde
  adentro de un tercero.
- **`controles/` no llega a un proyecto instalado.** Con D8 son **veintiséis** controles que declaran
  `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Es el ítem 2, ya
  actualizado con el número nuevo.
- **El mecanismo del token no se puede resolver en ningún proyecto todavía.** No está en ningún
  extracto ni en el catálogo del Anexo II. Cualquier corrida real de hoy sale
  `TOKEN_MECHANISM_UNRESOLVED`, que es lo correcto y también significa que el check no se ejercita de
  punta a punta hasta que alguien consiga ese dato.
- **`active` y la clasificación del inventario son datos declarados.** Una ruta viva declarada
  inactiva sale del conjunto de bypasses con una afirmación de quien la declaró. El check exige que
  la declaración exista; que sea cierta no lo puede saber.
- **El harness confía en la etiqueta de la fuente.** El mismo límite que D7 declaró, heredado entero:
  una observación de ausencia etiquetada como dato estructurado apaga la regla. Cerrado hoy **sólo
  para D5**.
- **Una rama del check que ningún escenario reclama.** `if por_el_endpoint != mecanismo_id` —un
  camino que declara un mecanismo distinto del del proyecto— se puede desactivar sin poner nada en
  rojo. No es un incumplimiento: es una decisión libre que ningún escenario de la spec pide. Queda
  constatada.

## Lo que ningún test cubre y se mira con los ojos

- **Que un servicio real rechace la llamada sin token.** Lo que este check verifica es que la sonda
  exista, esté atada al build y no venga mockeada. La corrida la hace una persona o una skill, y este
  cambio no llama a ningún servicio ni emite ningún token.
- **Que el inventario de endpoints esté completo de verdad.** Un bypass que nadie enumeró no lo
  encuentra este check: lo que hace es exigir que el inventario declare de dónde sale y negarse a
  concluir cuando se declara incompleto. Quién arma ese inventario y con qué cuidado es lo que decide
  si D8 sirve.
- **Que la policy se lea como una obligación y no como un instructivo de integración.** Es el
  artefacto que un modelo carga como instrucciones, y si se lee como una guía, el día que alguien
  busque el mecanismo adentro lo va a esperar encontrar.
