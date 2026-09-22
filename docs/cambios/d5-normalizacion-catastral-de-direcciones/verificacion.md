# Verificación — D5, las direcciones del frontend se normalizan con la opción catastral del GCBA

**Estado:** cerrado · **Fecha:** 21-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los emitió
`harness-spec-refuter` el 21-09-2026 en **dos pasadas**, corriendo `.\tests\Invoke-Tests.ps1` y
`python tests/correr.py -k d5`, más sondeos propios con formas que el constructor no eligió: unos
300 casos en la primera pasada y **3024 sistemáticos** en la segunda —los 32 subconjuntos de etapas
de la cadena × 2 modos de token × 3 valores consumidos × 7 etapas declaradas, más 1680
combinaciones de cadena × etapa × proveedor × ejecución × clase de evidencia— y un barrido de 33
caminos de salida del módulo.

**Resultado: 37 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

La primera pasada tumbó **dos escenarios que estaban en verde** —los dos de mecanismo, y ninguno de
los dos tenía un test que lo mirara— más ocho hallazgos que no contradecían ningún escenario y eran
defectos igual. Los doce están arreglados y cada uno tiene su aserción; **ninguno se cerró achicando
un escenario.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | D5 sigue CONDITIONAL y declara los ids que ya estaban | sostenido | sí | `32_d5…py`, y la fila recontada a mano |
| E-02 | TRUE hace aplicable | sostenido | sí | `test_e02_…` |
| E-03 | FALSE deja NOT_APPLICABLE | sostenido | sí | `test_e03_…` |
| E-04 | Sin evidencia, APPLICABILITY_UNRESOLVED | sostenido | sí | `test_e04_…` |
| E-05 | La ausencia nunca es FALSE | sostenido | sí | `test_e05_…`, cinco partes, en el check y en la resolución |
| E-06 | `frontendPresent` en TRUE no alcanza | sostenido | sí | `test_e06_…`, también con completitud declarada |
| E-07 | La derivación desde `frontendPresent` en FALSE | sostenido | sí | `test_e07_…`, once truthy y cuatro ids de señal |
| E-08 | La señal sale de evidencia de un flujo de direcciones | sostenido | sí | `test_e08_…` |
| E-09 | La señal y la evaluación, del mismo alcance | sostenido | sí | `test_e09_…`, ocho partes, y el camino real de una resolución |
| E-10 | Sin proveedor, CADASTRAL_PROVIDER_UNRESOLVED | sostenido | sí | `test_e10_…` |
| E-11 | Sin contrato, INTEGRATION_CONTRACT_MISSING | sostenido | sí | `test_e11_…` |
| E-12 | Un blanco no es un dato, y se normalizan los dos lados | sostenido | sí, de módulo | `test_e12_…`, **dieciocho** campos, uno por uno |
| E-13 | Ningún artefacto de D5 lleva el contrato | sostenido | sí, las tres mitades | `test_e13_…`, seis textos, 50 fugas, 23 textos limpios |
| E-14 | El autocompletado solo no pasa | sostenido | sí | `test_e14_…` |
| E-15 | La llamada a una API de direcciones sola no pasa | sostenido | sí | `test_e15_…` |
| E-16 | Un regex solo no pasa | sostenido | sí | `test_e16_…` |
| E-17 | Lo que hay no es lo que se consume | sostenido | sí | `test_e17_…`, las doce clases una por una |
| E-18 | La cadena completa con el normalizado consumido pasa | sostenido | sí | `test_e18_…`, casos felices que el constructor no eligió |
| E-19 | La llamada ocurre y se guarda el crudo | sostenido | sí | `test_e19_…`, tres formas más el bypass con la cadena a medias |
| E-20 | Un consumido sin rastro no pasa, y no es incumplimiento | sostenido | sí | `test_e20_…`, 19 casos del barrido |
| E-21 | Se exigen el token y la etapa, y el estado es cierto | sostenido | sí | `test_e21_…`, las ocho filas de la tabla sobre 1344 casos |
| E-22 | El caso degenerado pasa y lo dice | sostenido | sí | `test_e22_…`, probado como puerta |
| E-23 | La carga manual de texto libre falla | sostenido | sí | `test_e23_…` |
| E-24 | La edición que se saltea la normalización falla | sostenido | sí | `test_e24_…`, más la llamada condicional |
| E-25 | Los cinco tipos de camino se declaran todos | sostenido | sí | `test_e25_…`, ocho partes, once truthy, nueve malformados |
| E-26 | La cobertura incompleta no pasa | sostenido | sí | `test_e26_…` |
| E-27 | Un camino que cumple no tapa otro | sostenido | sí | `test_e27_…`, los **cuatro** cerrojos |
| E-28 | Lo mockeado no prueba | sostenido | sí | `test_e28_…` |
| E-29 | Sin dónde correr no pasa | sostenido | sí | `test_e29_…`, once truthy |
| E-30 | Nueve estados, y uno aprueba | sostenido | sí | `test_e30_…`, alcanzados sobre 33 caminos |
| E-31 | D5 no afirma nada de la regla del mapa | sostenido | sí | `test_e31_…`, los nueve caminos y las nueve otras salidas |
| E-32 | D5 no afirma nada de la validación duplicada | sostenido | sí | `test_e32_…` |
| E-33 | D5 no crea ni declara ninguna skill | sostenido | sí | `test_e33_…`, más un grep del refutador sobre `skills/` y `agents/` |
| E-34 | La unidad propaga señal, policy y check | sostenido | sí | `test_e34_…`, y el contrato del schema |
| E-35 | Los agentes primarios resuelven por el registro | sostenido | sí | `test_e35_…`, derivados de la matriz |
| E-36 | Los controles dejan de ser un hueco | sostenido | sí | `test_e36_…`, 18 controles recontados a mano |
| E-37 | Todo resultado conserva la traza | sostenido | sí | `test_e37_…`, los 33 caminos y la remediación |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 37 la tienen en `si`,
> con **58 mutaciones** deliberadas y ninguna sin rojo.

## Lo que la verificación encontró y no habría encontrado un test verde

Los doce salieron con los 707 del grupo y los 4747 de la suite en verde.

1. **E-09, contradicho — la guarda de alcance se evadía por un lado y era inalcanzable por el
   otro.** `alcance_coherente` hacía `continue` sobre lo que no fuera un diccionario, así que
   `evaluar(caso, True)` —la forma vieja de una señal, que el propio módulo declara soportar— salía
   `PASS` sin declarar ningún alcance. Y del otro lado, `senales.resolver_una` **no copiaba
   `scope`**: el campo que este cambio le agrega al schema existía en el documento y desaparecía en
   la resolución, así que toda corrida real —las que llegan por `normativa.resolucion`— salía
   `SCOPE_UNDECLARED` y la cláusula de la relación declarada era inalcanzable. El mecanismo quedaba
   **estricto donde el dato no podía cumplir y laxo donde no se declaró nada.**

2. **E-21, contradicho — el orden de las guardas no implementaba la tabla de decisión de la propia
   spec.** Tres formas:
   - con una etapa faltante, un bypass **probado** —la llamada ocurrió, hay respuesta, y el token
     consumido es el crudo— se informaba como `NORMALIZATION_CHAIN_INCOMPLETE`: el estado de lo que
     no se sabe, puesto sobre algo que sí se sabe;
   - un `or` entre «sin respuesta» y «sin resultado normalizado» hacía que una cadena que **sí**
     llega al normalizado saliera `FAIL` con un detalle que decía *"no hay resultado normalizado"*;
   - cuando la etapa declarada contradecía al token, mandaba la etapa, al revés de lo escrito.

   Ninguno filtraba un `PASS`. Lo que estaba mal era **qué estado se informa**, y E-20 ya dice por
   qué eso importa: *afirmar incumplimiento sin saberlo es una afirmación falsa con la tupla
   normativa adosada.*

3. **Doce comparaciones sin normalizar, y dos informaban un motivo falso.** `buildId` con un blanco
   decía *"es de otro build"* sobre una evidencia que era de ese build, y `mode: " REAL "` decía que
   la corrida era mockeada cuando declaraba `REAL`. Es la mitad de la lección de D6/E-11 que
   importa: la versión cruda avisaba, y normalizar a medias convierte un motivo verdadero en uno
   falso.

4. **Tres puertas abrían con un truthy.** `complete`, `absent` y `available` se leían por
   veracidad, así que un `"absent": "false"` —escrito por quien quería decir que el camino **no**
   está ausente— sacaba ese tipo de camino entero de la verificación, y un `"available": "no"` daba
   `PASS`. La primera es la peor de las tres porque su sentido de falla **hace desaparecer la regla
   del reporte.**

5. **La derivación publicaba una constante como origen.** No le miraba el `signalId` a la señal que
   recibía, así que pasarle **cualquier** otra señal en FALSE derivaba igual y le atribuía el FALSE a
   `frontendPresent`. E-07 dice *"la derivación nombra de dónde salió"*; nombraba siempre lo mismo.

6. **Un tipo de camino declarado dos veces evadía su validación.** La primera entrada quedaba sin
   validar mientras el recorrido de flujos seguía viendo las dos: un flujo **sin id** llegaba a ser
   gobernado con el id vacío.

7. **Un resultado sobre un flujo declarado inactivo desaparecía de la salida entera.** No estaba en
   `flows`, no estaba en `ignoredResults`, no lo nombraba ningún aviso, y el conjunto salía `PASS`.
   Era la última forma que le quedaba a la puerta de salida que D6 tuvo que sacar.

8. **Un dato malformado rompía el módulo en lugar de fallar cerrado.** Un `paths` que viene como
   diccionario o un `flows` como lista de strings daba `AttributeError`, y ninguno de los nueve
   estados cubre eso.

9. **Doce puntos ciegos del barrido de E-13**, ninguno presente en el árbol y los doce formas crudas
   de contrato: un tiempo escrito en palabras, una duración con unidad corta, un verbo HTTP con una
   ruta, una URL como valor de JSON, `Basic` y un JWT, una contraseña o un usuario declarados, un
   CRS por su nombre, otros códigos de proyección, cuatro gestores de paquetes más, un paquete con
   versión, y un nombre de campo catastral en mayúscula.

10. **La cuenta de E-36 omitía un tipo de control.** Contaba `policies + checks` y no `reviews`: hoy
    da lo mismo porque los dos reviews declarados están instalados, así que ninguna aserción lo
    notaba. El sujeto ahora se **deriva** de las claves de la matriz.

Y tres que encontró la pasada de mutaciones antes que el refutador, todos huecos del test y no del
mecanismo: E-06 no tenía el caso que importa —`frontendPresent` en TRUE **con** completitud
declarada—; E-34 afirmaba sobre el dato y no sobre el **contrato**, así que sacar `scope` del schema
no ponía nada en rojo; y E-05 lo afirmaba en el check y no en la resolución, que es por donde la
señal viaja a un plan.

📌 **Y el arreglo de la primera pasada cerró un hallazgo de rebote.** Con el `scope` conservado, la
parte 5 de E-05 dejó de pasar por la guarda de alcance y ahora prueba la proposición de su propio
escenario. Es lo contrario de lo que pasó en D6, donde el arreglo de una pasada fue el hallazgo de
la siguiente.

## Lo que queda abierto, anotado y no escondido

Todo en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, con su repro y su fecha:

| Qué | Por qué está abierto |
|---|---|
| El contrato de integración no se puede resolver en ningún proyecto | El harness no tiene cómo se ve usar la opción catastral. Toda corrida real de hoy sale `INTEGRATION_CONTRACT_MISSING`, que es correcto y también significa que el check no se ejercita de punta a punta. La identidad, en cambio, sí es citable desde la pág. 19 |
| El caso degenerado no discrimina | Con el crudo y el normalizado en el mismo token, *consumir el crudo* y *consumir el normalizado* son indistinguibles. Pasa con su aviso, y está clavado **en verde** en E-22 |
| `controles/` no llega a un proyecto instalado | Con D5 son dieciocho controles que declaran `INSTALLED` y afuera serían `CONTROL_FILE_MISSING`. Es el ítem 2 de la tabla de prioridades y este cambio lo empeora en dos |
| La completitud de alcance sigue abierta para las demás reglas | D5 la exige; el pendiente general de *nada exige «unless project coverage is known to be complete»* no se cierra acá. Queda como precedente de la primera de sus dos salidas |
| La evidencia de corrida no exige `reference` ni `claim` | Una `NORMALIZED_ADDRESS_RUN` con los dos en blanco prueba igual. La policy los lista y ningún escenario los exige |
| Las ocho `Outcomes` de la policy no son los nueve estados del check | Son dos listas con nombres distintos y nadie las compara. E-30 mira las del check |
| El barrido de E-13 no se puede ensanchar sin excepciones | La transcripción del estándar lleva URLs de verdad, `docs/secretos.md` habla de secretos y `docs/contrato-hooks.md` mide latencias. El sujeto son los seis textos de D5 a propósito |

## Lo que ningún test cubre y se mira con los ojos

- **Que el token del valor consumido corresponda de verdad al valor que la aplicación guardó.** El
  check verifica que los tokens sean coherentes, que la etapa declarada coincida y que la evidencia
  esté atada al build y no venga mockeada. Quién produce esos tokens es quien instrumenta la
  corrida, y que no mienta no lo puede probar este módulo.
- **Si el inventario de caminos está completo.** El check exige que los cinco tipos se declaren con
  su fuente y detecta los flujos que aparecen fuera del inventario. Que la fuente enumere todos los
  flujos materiales del sistema lo sabe quien conoce el sistema.
- **Que D5 no haya modificado ninguna skill.** E-33 se angostó a lo medible y lo dice en su
  docstring: un conteo no ve una modificación, y en este árbol git no puede ayudar porque las 27
  skills están sin trackear. El refutador lo corroboró con un grep y dio cero, pero eso es una
  lectura, no un test.
- **Qué va a pasar el primer día que un productor real escriba `available: 1`.** Con las tres
  puertas exigidas `is True`, ese reporte recibe `TEST_TARGET_UNAVAILABLE`. Es la dirección segura y
  está declarado en E-29; queda dicho para que a nadie lo sorprenda.
