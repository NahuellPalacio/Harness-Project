# Verificación — D6, las visualizaciones georreferenciadas usan el Mapa del GCBA

**Estado:** cerrado · **Fecha:** 21-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los emitió
`harness-spec-refuter` el 21-09-2026 en **tres pasadas**, corriendo `.\tests\Invoke-Tests.ps1`,
`python tests/correr.py -k d6`, sondas propias contra el check con formas que el constructor no
eligió, y un contraste de la fila de la matriz contra una copia previa del 18-09.

**Resultado: 31 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

Entre la primera pasada y la última, el refutador tumbó **seis** escenarios que estaban en verde:
dos contradichos y dos sin sustento en la primera, y **dos nuevos en la segunda, causados por el
arreglo de la primera**. Uno de esos dos fue una regresión.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | D6 sigue CONDITIONAL sobre su señal | sostenido | sí | `31_d6…py`, más la copia del 18-09 de la matriz |
| E-02 | TRUE hace aplicable | sostenido | sí | `test_e02_…` |
| E-03 | FALSE deja NOT_APPLICABLE | sostenido | sí | `test_e03_…`, bloque y check |
| E-04 | Sin señal, APPLICABILITY_UNRESOLVED | sostenido | sí | `test_e04_…` |
| E-05 | La ausencia nunca es FALSE | sostenido | sí | `test_e05_…`, cinco caminos |
| E-06 | `frontendPresent` no alcanza | sostenido | sí | `test_e06_…` |
| E-07 | `frontendAddressInputPresent` no alcanza | sostenido | sí | `test_e07_…` |
| E-08 | La señal sale de evidencia de una visualización | sostenido | sí | `test_e08_…` |
| E-09 | Sin identidad, GCBA_MAP_PROVIDER_UNRESOLVED | sostenido | sí | `test_e09_…` |
| E-10 | Sin contrato, MAP_INTEGRATION_CONTRACT_MISSING | sostenido | sí | `test_e10_…` |
| E-11 | Una identidad en blancos no identifica | sostenido | sí | `test_e11_…`, cinco blancos × cuatro campos |
| E-12 | Ningún artefacto lleva el mecanismo | sostenido | sí | `test_e12_…`, seis textos y 44 fugas |
| E-13 | Las coordenadas solas no pasan | sostenido | sí | `test_e13_…` |
| E-14 | La librería instalada no pasa | sostenido | sí | `test_e14_…` |
| E-15 | API GEO es D5 | sostenido | sí | `test_e15_…` |
| E-16 | La captura sola no pasa | sostenido | sí | `test_e16_…` |
| E-17 | La palabra de un agente no pasa | sostenido | sí | `test_e17_…` |
| E-18 | Todas las vistas con el mapa dan PASS | sostenido | sí | `test_e18_…`, con blancos en los tres lados |
| E-19 | Un mapa alterno falla | sostenido | sí | `test_e19_…`, con el cruce en las tres formas |
| E-20 | Una vista que cumple no tapa otra | sostenido | sí | `test_e20_…` |
| E-21 | La cobertura incompleta no pasa | sostenido | sí | `test_e21_…`, seis caminos |
| E-22 | Lo mockeado no prueba | sostenido | sí | `test_e22_…` |
| E-23 | Sin dónde correr no pasa | sostenido | sí | `test_e23_…` |
| E-24 | Nueve estados, uno aprueba | sostenido | sí | `test_e24_…` |
| E-25 | D6 no afirma nada sobre D5 | sostenido | sí | `test_e25_…`, los nueve caminos |
| E-26 | D5 sigue declarado y no instalado | sostenido | sí | `test_e26_…`, y los archivos en `~/Downloads` |
| E-27 | D6 no crea ni declara una skill | sostenido | sí | `test_e27_…`, cuatro cláusulas medibles |
| E-28 | El hueco se declara y no se llena | sostenido | sí | `test_e28_…`, contra el registro en vivo |
| E-29 | La unidad propaga señal, policy y check | sostenido | sí | `test_e29_…`, y una unidad real con `plan.armar` |
| E-30 | Los controles dejan de ser un hueco | sostenido | sí | `test_e30_…`, 16 controles |
| E-31 | Todo resultado conserva la traza | sostenido | sí | `test_e31_…`, los nueve caminos |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 31 la tienen en
> `si`. **Y dos de ellos —E-18 y E-19— tienen un rojo presenciado por el verificador**, no
> declarado por quien construyó: el refutador los vio fallar en la segunda pasada, con los casos
> que escribió él.

## Lo que la verificación encontró y no habría encontrado un test verde

Los seis salieron con la suite en verde.

1. **E-11, contradicho — un espacio pasaba como identidad declarada.** `if not str(x or "")` y
   `" "` es truthy. Un caso con **toda** la identidad en espacios —proveedor, contrato, id de
   vista, proveedor del resultado y de la corrida— llegaba a `PASS`: D6 informaba cumplimiento con
   un proveedor que no nombra nada y no cita en ningún lado. Una línea.

2. **E-20, contradicho — `materiality: MINOR` era una puerta de salida de la regla.** Lo había
   inventado yo: no está en el pedido ni en la spec. El proyecto lo declaraba solo, sin fuente
   exigida, al lado de un inventario al que sí se le exige `source`. Una vista marcada menor
   dibujando con otro mapa daba `PASS` y **no aparecía en ningún campo de la salida**.

3. **E-20, contradicho — la vista de afuera con el campo vacío.** `alternos_afuera` miraba sólo lo
   que la vista declaraba, así que dejar ese campo en blanco desarmaba la guarda entera: una vista
   fuera del inventario, con una corrida real reportando otro mapa, terminaba en `PASS` sin un solo
   aviso. La doctrina que E-19 fija —la corrida manda sobre lo declarado— vivía únicamente en la
   evaluación por vista.

4. **E-12, sin sustento — el sujeto, no los patrones.** El barrido leía dos de los artefactos. La
   fila de la matriz y `docs/normativa-7.1.md` son artefactos de D6 según la propia tabla de la
   spec, y nadie los miraba. Y de 18 formas crudas que el refutador probó, **15 escapaban**: una
   URL sin esquema, un puerto, una IP, `wmts`, `tileMatrixSet`, un CRS sin la etiqueta, un nombre
   de proveedor partido o pegado, `pnpm`, un `Token` sin `Bearer`.

5. **E-27, sin sustento — un conteo no ve una modificación.** El escenario decía "las 27 quedan
   idénticas" y lo único medido era `len(instaladas) == 27`.

6. **E-18 y E-19, contradichos por el arreglo de E-11 — normalizar un lado es peor que no
   normalizar ninguno.** `declarado()` quedó aplicado a los operandos y no a los dos valores contra
   los que se compara:
   - un proveedor con blancos que `proveedor_valido` **aceptaba** no podía igualar nunca al que la
     vista declaraba, así que un caso correcto salía `FAIL` por proveedor alterno: una afirmación
     falsa sobre el proyecto, con la tupla normativa de D6 adosada;
   - una vista con el id padeado se caía por el agujero del medio —`ids` normalizado, `por_vista`
     en crudo—: no entraba como gobernada ni como de afuera, y un bypass probado se informaba como
     `GOVERNED_VIEW_NOT_EXECUTED`. **Eso es una regresión**: la versión anterior, con todo en
     crudo, mandaba ese resultado a las vistas de afuera y avisaba. El arreglo convirtió un estado
     que avisaba en uno que calla.

Y tres que aparecieron al construir o al mutar:

7. **El barrido de E-12 encontró un nombre de modelo en un docstring de `costos.py`** —de otro
   cambio— y una fuga propia: `opus` como ejemplo. El invariante funcionando sobre su autor.

8. **Una clave JSON lleva comilla antes del `:`.** `"sdk": "mapa-gcba-js"` inyectado en la fila de
   la matriz escapaba al patrón, que esperaba la palabra pegada al separador. Apareció al poner la
   mutación donde el dato vive de verdad.

9. **Cuatro patrones no llevaban `(?i)`.** En código, la forma normal de escribir esto es una
   constante en mayúscula: `HTTPS://MAPA.GCBA.GOB.AR/BASE` y `/tiles/{Z}/{X}/{Y}.png` escapaban
   enteros. Era una dimensión completa del barrido, no una forma suelta.

## Lo que queda abierto, anotado y no escondido

Todo en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, con su repro y su fecha:

| Qué | Por qué está abierto |
|---|---|
| D5 no está instalado | Sus cuatro artefactos están en `~/Downloads` desde el 20-09-2026. Es la única regla con controles declarados en la matriz y no construidos, y **afirmado en verde** en E-26 |
| `controles/` no llega a un proyecto instalado | Con D6 son dieciséis controles que declaran `INSTALLED` y afuera serían `CONTROL_FILE_MISSING`. Es el ítem 2 de la tabla de prioridades y este cambio lo empeora en dos |
| Un `sourceType` con blancos baja un FAIL a PARTIAL y borra el rastro | Es la misma forma del bug de E-18/E-19, en un campo que la spec deja afuera de la normalización a propósito. Las dos posturas se defienden y no hay escenario que la cubra |
| "D6 no tocó ninguna skill" no lo afirma ningún test | E-27 se angostó a lo medible, declarado en el docstring del test. No hay línea base: el árbol de skills está entero sin trackear |
| El proveedor no se puede resolver en ningún proyecto todavía | El Mapa del GCBA no está en ningún extracto ni en el catálogo del Anexo II. Cualquier corrida real de hoy sale `GCBA_MAP_PROVIDER_UNRESOLVED` |

## Lo que ningún test cubre y se mira con los ojos

- **Que la aplicación use el Mapa del GCBA de verdad.** Este check verifica que la evidencia de esa
  corrida exista, esté atada al build, declare su proveedor y no venga mockeada. Lo que dibujó la
  pantalla lo dice una corrida real, y hasta que alguien consiga la identidad del proveedor el
  check no se va a ejercitar de punta a punta.
- **Si el inventario de vistas está completo.** El check exige que se declare con su fuente y
  detecta las vistas que aparecen fuera de él dibujando con otro mapa. Que la fuente enumere todas
  las vistas materiales del sistema lo sabe quien conoce el sistema.
- **La frontera con el check de D5.** `frontendAddressInputPresent` está declarada, así que E-07 y
  E-25 son verificables. Que los dos checks no se contaminen entre sí no se puede probar todavía:
  uno de los dos no existe.
