# Verificación — D2: delegar el ingreso de credenciales, y decir qué no se puede verificar

**Estado:** cerrado · **Fecha:** 19-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 19-09-2026,
corriendo `.\tests\Invoke-Tests.ps1` —2310/2310—, `python tests/correr.py -k d2_delegacion`
—196/196— y `-k d1_autenticacion` —200/200—, y sondeando por su cuenta, en memoria, los cuatro
escenarios que se le pidió mirar con desconfianza.

**Resultado: 31 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos. Los 31 con
`rojo visto: si`.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `D2` es `CONDITIONAL` sobre `authenticationPresent` y su fila no cambió | sostenido | sí, de módulo | `27_d2_delegacion_credenciales.py::test_e01_d2_es_condicional` |
| E-02 | `TRUE` deja `D2` aplicable y exige sus dos controles | sostenido | sí, específico | `::test_e02_true_hace_aplicable` |
| E-03 | `FALSE` deja `D2` fuera | sostenido | sí, de módulo | `::test_e03_false_hace_no_aplicable` |
| E-04 | Sin señal, `D2` sin resolver con la que falta escrita | sostenido | sí, de módulo | `::test_e04_sin_senal_queda_sin_resolver` |
| E-05 | Una dependencia sola no enciende la señal | sostenido | sí, específico | `::test_e05_una_dependencia_sola_no_enciende_la_senal` |
| E-06 | La misma dependencia con evidencia de uso sí resuelve | sostenido | sí, específico | `::test_e06_la_dependencia_con_evidencia_de_uso_resuelve` |
| E-07 | No hay un segundo framework de señales | sostenido | sí, específico | `::test_e07_no_hay_un_segundo_framework` |
| E-08 | La señal conserva su evidencia y el modo de su productor | sostenido | sí, de módulo | `::test_e08_la_senal_conserva_evidencia_y_productor` |
| E-09 | Credenciales validadas en la aplicación: `FAIL` | sostenido | sí, específico | `::test_e09_credenciales_en_la_aplicacion_fallan` |
| E-10 | Institucional delegado con evidencia DGSEI/Keycloak: `PASS` | sostenido | sí, específico | `::test_e10_institucional_delegado_pasa` |
| E-11 | El endpoint viejo no es proveedor actual | sostenido | sí, específico | `::test_e11_el_endpoint_viejo_no_es_proveedor` |
| E-12 | Flujo ciudadano a nivel gobierno, sin inventar internos | sostenido | sí, específico | `::test_e12_flujo_ciudadano_a_nivel_gobierno` |
| E-13 | Un formulario propio no es delegación | sostenido | sí, las dos mitades | `::test_e13_un_formulario_propio_no_es_delegacion` |
| E-14 | Una dependencia no prueba delegación | sostenido | sí, las dos mitades | `::test_e14_una_dependencia_no_prueba_delegacion` |
| E-15 | Las tres formas de que falte evidencia dan `PARTIAL` | sostenido | sí, las tres | `::test_e15_las_tres_formas_de_que_falte_evidencia` |
| E-16 | La afirmación de un agente, sola, no alcanza | sostenido | sí, las dos mitades | `::test_e16_la_afirmacion_de_un_agente_no_alcanza` |
| E-17 | De los siete estados, `PASS` es el único que aprueba | sostenido | sí, específico | `::test_e17_solo_pass_aprueba` |
| E-18 | Un camino directo activo manda sobre el flujo que cumple | sostenido | sí, las dos mitades | `::test_e18_un_camino_directo_activo_manda` |
| E-19 | Audiencia sin resolver: `AUTHENTICATION_CONTEXT_UNRESOLVED` | sostenido | sí, las dos mitades | `::test_e19_audiencia_sin_resolver` |
| E-20 | `citizenFacing` es contexto secundario y no se redefine | sostenido | sí, las dos mitades | `::test_e20_citizen_facing_es_contexto_secundario` |
| E-21 | La aplicabilidad de `D2` no depende de `citizenFacing` | sostenido | sí, de módulo | `::test_e21_la_aplicabilidad_no_depende_de_citizen_facing` |
| E-22 | `D1` y `D2` aplican juntas, con sus cuatro controles | sostenido | sí, de módulo | `::test_e22_d1_y_d2_aplican_juntas` |
| E-23 | `D2` no duplica la selección de mecanismo de `D1` | sostenido | sí, las tres | `::test_e23_d2_no_duplica_la_seleccion_de_mecanismo` |
| E-24 | Lo que depende de ES0902 se nombra y no anula la delegación | sostenido | sí, las dos mitades | `::test_e24_lo_que_depende_de_es0902` |
| E-25 | No se inventa ninguna regla de ES0902 | sostenido | sí, específico | `::test_e25_no_se_inventa_ninguna_regla_de_es0902` |
| E-26 | La remediación ciudadana declara el hueco y no hace cumplir | sostenido | sí, las cuatro | `::test_e26_la_remediacion_ciudadana_declara_el_hueco` |
| E-27 | `dev-openid-connect` no reemplaza a `dev-miba` | sostenido | sí, las dos mitades | `::test_e27_openid_no_reemplaza_a_miba` |
| E-28 | Los artefactos de `D2` no inventan internos de proveedor | sostenido | sí, específico | `::test_e28_no_se_inventan_internos_de_proveedor` |
| E-29 | La unidad lleva las dos señales, cada una con su evidencia | sostenido | sí, de módulo | `::test_e29_la_unidad_lleva_las_dos_senales` |
| E-30 | Los controles dejan de faltar sin tocar la declaración de `D2` | sostenido | sí, específico | `::test_e30_los_controles_dejan_de_faltar` |
| E-31 | La tupla `ES0901 / 6.3 / 7.1 / D2` se conserva | sostenido | sí, específico | `::test_e31_la_traza_se_conserva` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los 31 escenarios de este
> cambio se vieron en rojo con 30 mutaciones deliberadas sobre seis archivos, cada una revertida; el
> refutador reprodujo cuatro de ellas por su cuenta, en memoria.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-07 podía estar probando la generalidad por el motivo equivocado.** El caso recorre tres
   señales —`authenticationPresent`, `citizenFacing`, `databasePresent`— y exige el mismo
   comportamiento en las tres. Si la tercera no fuera una señal que la matriz declara, `producir()`
   habría devuelto `UNRESOLVED` por `SIGNAL_NOT_DECLARED` y esa iteración habría pasado sin ejercer
   la clase de fuente nueva: el escenario habría quedado verde sin probar lo que afirma. El
   refutador verificó contra la matriz que las tres están declaradas y que las tres pasan por la
   rama de fuente débil.
2. **E-21 cubre su tercer valor por ausencia, no por declaración.** El bucle nombra `UNRESOLVED`,
   pero para ese caso omite `citizenFacing` del diccionario en vez de pasar un documento de señal
   con `value: "UNRESOLVED"`. Son dos entradas distintas. El refutador probó a mano la forma que
   falta y el comportamiento es el mismo: `D2` queda igualmente aplicable y `D1` igualmente sin
   resolver. La proposición se sostiene; el hueco es de forma de entrada.
3. **Dos de los siete estados sólo se ejercen sintéticamente.** `NOT_APPLICABLE` y
   `APPLICABILITY_UNRESOLVED` se prueban como diccionarios `{"state": X}` contra `aprueba()`;
   ninguna llamada real a `evaluar` del caso 27 pasa la señal en `FALSE` ni sin resolver, así que
   las ramas que los producen no las corre ningún test. Es la misma forma del hallazgo 3 del
   veredicto de D1. No cambia el veredicto —el texto de E-17 afirma algo sobre `aprueba()` y no
   lleva el "en ningún camino" que sí tenía su par en D1— y queda abierto abajo.
4. **La marca `rojo visto` de este cambio no tiene registro propio.** En D1 las 29 mutaciones
   quedaron documentadas en su `verificacion.md`; acá el directorio del cambio sólo tenía `spec.md`
   cuando el refutador rindió. La marca es una declaración, no un check, y el refutador la cargó
   como la spec la declara —lo que corresponde— dejando dicho que no la respaldaba ningún registro.
   Este archivo la respalda ahora.

## E-25, y hasta dónde llega su `sostenido`

Se lo pidió explícitamente: *¿declarar `VALIDACIONES_DE_ES0902` es lo contrario de inventar la
norma, o es inventarla por otra vía?*

**Lo que queda probado:** el check no emite ni un requisito de ES0902. La lista nombra ids de
preguntas que el check declina; la salida dice que no sabe, nunca qué exige. Esa es exactamente la
proposición de E-25.

**Lo que no queda probado por nadie:** que `PASSWORD_POLICY`, `TOKEN_SIGNING_REQUIREMENTS`,
`SESSION_SECURITY`, `CIPHER_REQUIREMENTS` y `SECURITY_ASSESSMENT` pertenezcan de verdad al alcance
de ES0902. `normativa/extractos/ES0901.md:440` remite a ES0902 para la delegación institucional
—*"(Ver ES0902 - Estándar de Seguridad)"*— y no enumera los temas. Que §8 remite está respaldado;
qué cinco ids concretos caen ahí lo escribió una persona.

El escenario no afirma que la lista sea correcta, así que no es incumplimiento. Queda escrito para
que el `sostenido` no se lea como más de lo que es. La spec ya lo nombra en sus riesgos: *esa lista
la escribe alguien y puede crecer.*

## Lo que queda abierto, anotado y no escondido

1. **Los dos estados de `D2` que ningún test produce de verdad.** `NOT_APPLICABLE` y
   `APPLICABILITY_UNRESOLVED` salen de ramas de `authentication-delegation.py` que ninguna llamada
   real ejercita. Anotado en `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
2. **`FUENTES_INSUFICIENTES` del check de D1 dice menos de lo que el código hace.** No lista
   `REPOSITORY_DEPENDENCY`, mientras el de D2 sí. No cambia comportamiento en ninguno de los dos
   —la compuerta real es la whitelist `sourceType in FUENTES_SUFICIENTES`, así que en D1 la clase
   nueva ya es insuficiente por omisión—, pero es una constante declarativa que quedó desactualizada
   el día que se partió la clase. El archivo de D1 está verificado y cerrado, así que no se toca sin
   re-verificarlo. Anotado en `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
3. **Ni D1 ni D2 están en `HEAD`.** El refutador lo deja dicho: "aditiva" está verificado contra D1
   tal como quedó construido en esta sesión, no contra una versión liberada. Lo mismo vale para "la
   fila de la matriz no cambió", que se sostiene por igualdad de valores y no por diff, porque
   `es0901-7.1-normative-matrix.json` sigue sin trackear.
4. **La separación con D1 no la hace cumplir nada.** Está escrita, está testeada con un caso, y el
   día que alguien agregue a D2 una verificación de mecanismo ciudadano el test sigue verde. La
   spec lo declara en sus riesgos.
5. **`controles/` sigue sin llegar a un proyecto instalado.** Los dos controles de D2 se suman a los
   ocho que ya estaban en esa situación. Es el ítem 2 de la tabla de prioridades de
   `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

## Lo que ningún test cubre y se mira con los ojos

- **Si los cinco ids de `VALIDACIONES_DE_ES0902` son los correctos.** Sólo lo cierra traer ES0902
  como fuente declarada, y eso arranca por cerrar su extracto como fiel.
- **Si el flujo declarado es el que la aplicación tiene.** El check lee un relevamiento; que el
  `credentialEntry` diga `DELEGATED` y la aplicación tenga un formulario propio escondido es algo
  que sólo ve quien abre el código.
- **Si `AUTHENTICATION_CONTEXT_UNRESOLVED` y `ES0902_CONTEXT_REQUIRED` se vuelven el cajón de lo
  incómodo.** Se ve corriendo D2 sobre proyectos reales y mirando la distribución de estados, no en
  la suite.
