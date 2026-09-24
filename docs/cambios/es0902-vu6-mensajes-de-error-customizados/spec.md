# ES0902 Vu6 — todo mensaje de error que ve un consumidor está customizado

**Estado:** verificado y cerrado · **Fecha:** 24-09-2026 · **Regla:** ES0902 6.2 §6 Vu6

## Qué problema resuelve

> *"Todos los mensajes de error deben estar customizados."* (ES0902 v6.2, §6)

La fila de Vu6 está en la matriz: `CONDITIONAL` sobre `userFacingErrorPresent`, con una policy, un
check y cero reviews. Sus dos controles, `custom-error-messages-required` y
`custom-error-message-compliance`, están declarados y no construidos.

Vu6 tiene seis formas baratas de ponerse en verde, y este cambio las cierra:

1. **El handler por el comportamiento.** Que exista un manejador central de errores no dice qué ve
   el consumidor en el camino que el manejador no cubre.
2. **El frontend por la API.** Una pantalla de error prolija no tapa un payload de API con el stack
   trace.
3. **El 200 amable.** Convertir todo error en un `200` con un mensaje lindo esconde el estado real a
   los balanceadores. ES0901 lo prohíbe expresamente.
4. **La lista de palabras.** Buscar `Exception` o `at java.` en un texto no prueba nada en ninguna de
   las dos direcciones.
5. **El log por el mensaje.** Un stack trace en un log interno protegido no es un mensaje al
   consumidor. Uno que se reenvía al consumidor sí lo es.
6. **La redacción inventada.** Vu6 no fija el texto, el idioma, el componente, el schema JSON ni el
   código de estado.

Y la peligrosa: tirar abajo infraestructura, o usar datos reales, para provocar un error y ver la
página.

## Qué queda afuera

- **El texto, el idioma, el componente visual, el schema del error y el código exacto.** Vu6 no los
  define y el check no los exige.
- **Los logs internos protegidos.** Pueden tener todo el detalle técnico, y Vu6 no los juzga.
- **Tocar C1, Vu1..Vu5 o ES0901.** La regla de ES0901 sobre errores HTTP no enmascarados (§11,
  pág. 22) entra como fuente de apoyo citada, no como resultado. Vu6 no lee ni escribe el resultado
  de ninguna regla de ES0901.
- **Vu7.** La divulgación de datos privados del software de base es otra regla. Pueden compartir
  evidencia, pero nunca el resultado.
- **Ejecutar las pruebas.** El check lee la evidencia de una prueba ya hecha y decide si era segura.
- **Cambiar los agentes de la fila.** La matriz declara `dev-security`, `dev-backend` y
  `dev-frontend`, y no se migra, igual que en Vu3..Vu5.
- **Un agente, una skill, una review o un algoritmo nuevo en `seguridad.py`.** Vu6 va por el camino
  genérico, y `ALGORITMOS` sigue en diez.
- **Un subsistema de reporte propio.** El resultado entra al libro de seguridad por los productores
  que ya existen. El dominio "Validación y manejo de errores" ya incluye a Vu6.

## Las decisiones, y por qué

### Una superficie por entrada, y cada escenario se juzga solo

Cada superficie del registro (`surfaceId`, `consumerType`, `owner`) trae sus escenarios. Cada
escenario tiene `scenarioId`, `errorType`, `result`, `httpStatusRef`, `technicalDetailExposure`,
`verificationMode` y `evidence`. Una superficie en verde no tapa otra, y un escenario en verde no
tapa otro de la misma superficie.

### Qué hay que cubrir, y cómo se cubre

Hay que cubrir estas superficies:
- las del inventario de C1, leído con su cargador;
- las `interface_id` de `interfaces.items[]` del contexto de proyecto que una evidencia autoritativa
  citada `ERROR_SURFACE_SCOPE` nombra;
- las que nombra una `ERROR_SURFACE_SCOPE` citada.

Una superficie queda cubierta de una de dos maneras:
- **Con una entrada que trae un escenario `UNEXPECTED_ERROR`**, más cada `errorType` que una
  evidencia autoritativa citada `ERROR_PATH_SCOPE` nombre para esa superficie. El error inesperado
  se exige siempre, porque es el camino por el que sale la página por defecto y porque es el que
  nombra ES0901.
- **Con una evidencia autoritativa y legible de `USER_FACING_ERROR` en `ABSENT`** que nombra la
  superficie. Si la superficie tiene entrada, esa evidencia tiene que estar citada desde ella.

Si falta, da `ERROR_SURFACE_COVERAGE_UNRESOLVED`. Una entrada del registro que no está en el alcance
también se evalúa, y además impide el `PASS` con el mismo estado, sin hacer nunca `FAIL`.

### La señal

```
TRUE        una superficie con una evidencia citada y legible de USER_FACING_ERROR en PRESENT, que
            no sea de la clase INTERNAL_LOG
FALSE       todas las superficies del alcance con evidencia autoritativa de USER_FACING_ERROR en
            ABSENT, el registro vacío para ellas y la cobertura entera
UNRESOLVED  todo lo demás; tambien un alcance vacio
```

Que un framework maneje los errores no apaga la señal. Que un camino devuelva solo el código de
estado tampoco.

### El resultado de un escenario sale de estos pasos

Se recorren los pasos. Una falla en cualquiera de ellos le gana a un sin resolver de un paso
anterior. Si no hay ninguna falla, gana el primer sin resolver en el orden de la lista.

1. **La exposición.**
   - Un `DEFAULT_ERROR_EXPOSED`, `RAW_TECHNICAL_ERROR_EXPOSED` o `INFRASTRUCTURE_DETAIL_EXPOSED`
     establecido por una evidencia citada y legible de comportamiento es `FAIL`, con ese estado.
   - `technicalDetailExposure: DETECTED` establecido de la misma manera da
     `INFRASTRUCTURE_DETAIL_EXPOSED`.
2. **El customizado.** `CUSTOMIZED_SAFE` cumple solo si una evidencia citada y legible de
   comportamiento lo establece para esa superficie y ese escenario. `UNRESOLVED`, o
   `CUSTOMIZED_SAFE` sin ese sostén, da `ERROR_CUSTOMIZATION_UNRESOLVED`.
3. **La semántica HTTP.** Aplica solo a una superficie HTTP: `API_CONSUMER`, o una con evidencia de
   que responde por HTTP.
   - Un `UNEXPECTED_ERROR` con una evidencia citada que establece un `HTTP_STATUS_CLASS` de éxito
     (`2xx`) o de redirección (`3xx`) es `HTTP_ERROR_SEMANTICS_MASKED`, que es `FAIL`. La fuente es
     ES0901 §11, que dice que el estado de error no se reemplaza.
   - Para cualquier otro `errorType`, se enmascara solo si una evidencia autoritativa citada
     `API_ERROR_CONTRACT` dice que el escenario es un error, y el estado observado es de éxito.
   - Sin contrato, no se juzga ningún código. Nunca se exige un código exacto.

Las clases de evidencia de comportamiento, que son las únicas que sostienen qué ve el consumidor,
son estas:
- `ERROR_HANDLER_MAPPING`, que tiene que nombrar la superficie y el `errorType`;
- `UNIT_TEST`, `INTEGRATION_TEST` y `CONTRACT_TEST`;
- `AUTHORIZED_QA_RUNTIME_TEST`;
- `EXPOSED_OUTPUT_OBSERVATION`;
- `INTERNAL_DIAGNOSTIC_FORWARDED`;
- `ASSESSMENT_FINDING`;
- `OTHER_AUTHORITATIVE_EVIDENCE`.

No sostienen nada:
- `ERROR_HANDLER_PRESENCE`, que dice que hay un manejador central y no qué camino cubre;
- `FRAMEWORK_OWNERSHIP`, `SOURCE_CODE` y `CONFIGURATION`;
- `INTERNAL_LOG`;
- un README, un agente o una skill.

Una `FRAMEWORK_OWNERSHIP` o un `owner: FRAMEWORK_DEFAULT` no hacen `FAIL` por sí solos: si la
configuración del proyecto customiza la salida y una evidencia de comportamiento lo muestra, cumple.
El comportamiento que se ve le gana a lo que se supone.

### Nada de listas de palabras

El check no busca ninguna palabra en ningún texto para decidir. La clasificación sale de lo que
establece cada evidencia. Una evidencia cuyo `reference` dice `java.lang.NullPointerException` y
establece `CUSTOMIZED_SAFE` cumple igual.

### El log no es el mensaje, salvo que se reenvíe

Una evidencia `INTERNAL_LOG` con un stack trace ni enciende la señal ni hace `FAIL`. Una
`INTERNAL_DIAGNOSTIC_FORWARDED` que dice que el diagnóstico interno llega al consumidor es evidencia
de exposición, y se juzga en el paso 1. Citada y legible, es `RAW_TECHNICAL_ERROR_EXPOSED` diga lo
que diga su `value`, y nunca sostiene un `CUSTOMIZED_SAFE`: un diagnóstico interno que llega al
consumidor no es un mensaje customizado. No citada, deja el escenario sin resolver. (Enmendado el
24-09-2026, después del primer pase.)

La salida del check, la señal y `rules.Vu6` llevan ids y estados, nunca el texto de una evidencia.
Así el libro de seguridad no recibe detalle sensible de ningún log.

### La prueba es segura o no cuenta

Una `AUTHORIZED_QA_RUNTIME_TEST` cuenta si cumple todo esto:
- `authorized: true`;
- el ambiente es `DEV`, `QA`, `HML` u `OTHER`;
- `syntheticData: true`;
- `destructive` no es `true`;
- `infrastructureOutageInduced` no es `true`;
- `realPersonalData` no es `true`;
- `realSecrets` no es `true`;
- `rawSecretsLogged` no es `true`.

Si no, da `ERROR_MESSAGE_TEST_UNSAFE`. Con `outcome: UNAVAILABLE`, da `TEST_TARGET_UNAVAILABLE`.
Ninguna de las dos es `FAIL`. Un error de validación, un recurso inexistente o una petición inválida
son escenarios seguros, y ninguna condición exige provocar una caída.

### Las reglas que ya costaron pases, desde el primer día

Son las mismas seis de Vu5, sin cambios:
1. Lo que dice "no" pasa por la misma compuerta que lo que dice "sí".
2. Lo ilegible que nombra la superficie o el escenario impide el `PASS`, citado o no, y lo no citado
   nunca hace `FAIL`. Un id que no es texto es ilegible, nunca una excepción.
3. Registro y evidencia se contradicen en las dos direcciones, y la falla establecida gana siempre:
   una exposición citada y legible es `FAIL` diga lo que diga el registro. Una no citada deja el
   escenario sin resolver.
4. Todo id se normaliza a NFC antes de comparar y antes de contar repetidos.
5. Hay un solo paso de bloqueo, que nunca tapa un `FAIL` y nunca reemplaza un sin resolver de un
   paso anterior. Bloquea una prueba insegura o sin objetivo que nombra algo del registro o del
   alcance **y** que está citada, o que dice que hay una exposición. Es la regla de Vu3 y de Vu5:
   una prueba ajena e insegura que dice "customizado" no bloquea.
6. Hay una sola regla de salida de secretos, `controles/lib/evidencia.py`, con las claves de
   diccionario incluidas.

### El registro es cerrado

El registro del paquete se instala vacío. El schema del paquete se cierra con
`additionalProperties: false` en todas sus capas. Es la única divergencia de schema que cambia qué
valida; `$id` y `description` son anotaciones.

### El agregado

- **`FAIL`.** Un escenario en `FAIL` hace `FAIL` el agregado, y el estado que se informa es el de la
  falla.
- **Sin resolver.** Si no hay ninguna falla, un escenario o una superficie sin resolver impide el
  `PASS`.
- **`PASS`.** Exige cobertura entera y todos los escenarios cumplidos.

La salida sigue la forma de la de Vu5, con `surfaces[]`.

### Los límites con otras reglas

El `PASS` de Vu6 no pone en `PASS` a Vu5, a Vu7, a Vu10 ni a la aprobación oficial. El de Vu5 no pone
en `PASS` a Vu6. Una evidencia de un error de validación puede estar citada por Vu5 y por Vu6, y
cada regla conserva su resultado.

### La unidad de trabajo lleva `rules.Vu6`, y el reporte lo recibe como cualquier regla

`standards.ES0902.rules.Vu6` lleva `applicability`, `result`, `surfaces` y `evidence`, con ids y
estados. La salida pasada por `seguridad.resultado("Vu6", …)` y por
`reporte_seguridad.productores.desde_regla` entra al mismo libro.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/custom-error-message-evidence.json` | El registro, instalado vacío |
| `comun/schemas/custom-error-message-evidence.schema.json` | Su contrato, cerrado en todas las capas |
| `harnesses/desarrollo/reglas/es0902-vu6-*.md` | Gobierno, señal y procedimiento, como vinieron |
| `harnesses/desarrollo/controles/policies/custom-error-messages-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/custom-error-message-compliance.py` | La señal y el check |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu6` en la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles |
| `docs/seguridad-es0902.md` | Vu6 |
| `tests/casos/52_es0902_vu6_mensajes_de_error.py` | Los escenarios |

## Escenarios verificables

Numerados como el pedido: `E-nn` es `VU6-nn`. Los que agrega esta spec van después del 53.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu6`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `userFacingErrorPresent`, `custom-error-messages-required` y
  `custom-error-message-compliance` están exactos en la matriz, el registro de controles y el
  módulo. Los agentes primarios son los de la matriz, en este orden: `dev-security`, `dev-backend` y
  `dev-frontend`. · rojo visto: si
- **E-03** — No hay ningún agente, skill ni review nuevo, y `ALGORITMOS` sigue en diez.
  · rojo visto: si

### La señal

- **E-04** — Una pantalla de error del frontend evidenciada enciende la señal. · rojo visto: si
- **E-05** — Un payload de error de API evidenciado enciende la señal. · rojo visto: si
- **E-06** — Un error expuesto del móvil o del backoffice enciende la señal. · rojo visto: si
- **E-07** — Una evidencia `INTERNAL_LOG`, sola, no enciende la señal. · rojo visto: si
- **E-08** — Un alcance con superficies sin cubrir y sin ningún error presente da la señal
  `UNRESOLVED`. · rojo visto: si

### El escenario

- **E-09** — Un mensaje controlado por la aplicación, con evidencia de comportamiento, cumple su
  escenario. · rojo visto: si
- **E-10** — Una página de debug del framework expuesta y evidenciada da `DEFAULT_ERROR_EXPOSED` y
  `FAIL`. · rojo visto: si
- **E-11** — Un stack trace expuesto y evidenciado da `RAW_TECHNICAL_ERROR_EXPOSED` y `FAIL`.
  · rojo visto: si
- **E-12** — La página por defecto del servidor o de la plataforma, expuesta sin cambios, da `FAIL`.
  · rojo visto: si
- **E-13** — Una ruta del sistema de archivos expuesta en un error inesperado, evidenciada, da
  `INFRASTRUCTURE_DETAIL_EXPOSED` y `FAIL`. · rojo visto: si
- **E-14** — Lo mismo con una IP interna. · rojo visto: si
- **E-15** — Lo mismo con una excepción de la base o del driver. · rojo visto: si
- **E-16** — Lo mismo con un diagnóstico del contenedor o de la plataforma. · rojo visto: si

### Lo que Vu6 no fija

- **E-17** — Un mensaje customizado que no dice "Ocurrió un error" cumple igual: el módulo no exige
  ningún texto. · rojo visto: si
- **E-18** — Dos mensajes customizados con textos distintos en castellano dan el mismo resultado.
  · rojo visto: si
- **E-19** — Un mensaje customizado en inglés da el mismo resultado que uno en castellano.
  · rojo visto: si
- **E-20** — Dos payloads customizados con formas JSON distintas dan el mismo resultado.
  · rojo visto: si
- **E-21** — El componente de la pantalla no cambia el resultado. · rojo visto: si
- **E-22** — Un error de validación customizado con `400` y otro con `422` dan el mismo resultado, y
  sin contrato ningún código de error se juzga. · rojo visto: si

### Cada superficie por su cuenta

- **E-23** — Un frontend customizado con la API que expone un stack trace da `FAIL`.
  · rojo visto: si
- **E-24** — Una API segura con el backoffice que muestra la página por defecto da `FAIL`.
  · rojo visto: si
- **E-25** — Un escenario cumplido no tapa otro material sin resolver: no da `PASS`.
  · rojo visto: si
- **E-26** — Una superficie del alcance sin escenario `UNEXPECTED_ERROR` da
  `ERROR_SURFACE_COVERAGE_UNRESOLVED`. · rojo visto: si

### Los logs

- **E-27** — Un stack trace en un log interno protegido, solo, no hace `FAIL`. · rojo visto: si
- **E-28** — Un `INTERNAL_DIAGNOSTIC_FORWARDED` que llega al consumidor de la API da `FAIL`, también
  cuando su `value` dice `CUSTOMIZED_SAFE` o solo `USER_FACING_ERROR: PRESENT`, y nunca sostiene un
  escenario.
  · rojo visto: si
- **E-29** — El texto de una evidencia con un stack trace, una IP y una ruta no aparece en la
  salida, en la señal, en `rules.Vu6` ni en el libro de seguridad. Solo aparece su id.
  · rojo visto: si

### La semántica HTTP

- **E-30** — Un cuerpo customizado de un error inesperado con estado `5xx` cumple.
  · rojo visto: si
- **E-31** — Un error inesperado respondido con `2xx`, evidenciado, da
  `HTTP_ERROR_SEMANTICS_MASKED` y `FAIL`. · rojo visto: si
- **E-32** — Customizar el cuerpo no es enmascarar: un cuerpo customizado con el estado de error
  intacto no da `HTTP_ERROR_SEMANTICS_MASKED`. · rojo visto: si
- **E-33** — La regla de ES0901 sobre errores HTTP se cita como fuente de apoyo en la salida, y
  ningún resultado de ES0901 entra ni sale del check. · rojo visto: si

### El manejador y el framework

- **E-34** — Un `ERROR_HANDLER_PRESENCE`, solo, no cumple ningún escenario. · rojo visto: si
- **E-35** — Un `ERROR_HANDLER_MAPPING` que nombra la superficie y el `errorType`, con todos los
  escenarios cubiertos, cumple. · rojo visto: si
- **E-36** — `owner: FRAMEWORK_DEFAULT` con evidencia de comportamiento de que la configuración
  customiza la salida cumple. · rojo visto: si
- **E-37** — Un `ERROR_HANDLER_MAPPING` que dice que customiza, con una observación citada de que
  la salida es el stack trace, da `FAIL`. · rojo visto: si

### La prueba

- **E-38** — Una prueba en QA con un error de validación sintético cuenta. · rojo visto: si
- **E-39** — Una prueba con un recurso inexistente o una petición inválida cuenta.
  · rojo visto: si
- **E-40** — Una prueba con `infrastructureOutageInduced: true` o `destructive: true` no cuenta.
  · rojo visto: si
- **E-41** — Una prueba con `realPersonalData: true` o `realSecrets: true` no cuenta.
  · rojo visto: si
- **E-42** — Sin autorización, en `PRD`, sin datos sintéticos o con secretos registrados, da
  `ERROR_MESSAGE_TEST_UNSAFE`. El módulo no ejecuta nada. · rojo visto: si
- **E-43** — Una prueba insegura no es `FAIL`, también cuando dice `RAW_TECHNICAL_ERROR_EXPOSED`.
  · rojo visto: si

### Los límites

- **E-44** — El `PASS` de Vu5 no pone en `PASS` a Vu6. · rojo visto: si
- **E-45** — El `PASS` de Vu6 no pone en `PASS` a Vu5. · rojo visto: si
- **E-46** — El `PASS` de Vu6 no pone en `PASS` a Vu7. · rojo visto: si
- **E-47** — El `PASS` de Vu6 no pone en `PASS` a Vu10. · rojo visto: si
- **E-48** — El `PASS` de Vu6 no cambia la aprobación oficial. · rojo visto: si

### El agregado

- **E-49** — Una exposición confirmada en cualquier superficie hace `FAIL` el agregado.
  · rojo visto: si
- **E-50** — Un camino material sin resolver impide el `PASS`. · rojo visto: si
- **E-51** — La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales
  en NFC. · rojo visto: si
- **E-52** — La trazabilidad `ES0902 / 6.2 / 6 / Vu6` viaja en todo resultado, y la unidad lleva
  `rules.Vu6` con aplicabilidad, resultado, superficies y evidencia por id. · rojo visto: si
- **E-53** — La salida pasada por `seguridad.resultado` y `desde_regla` entra como
  `RULE_EVALUATION` de `ES0902.Vu6` al mismo libro, y `reporte_seguridad/` no tiene ningún archivo
  nuevo. · rojo visto: si

### Lo que agrega esta spec

- **E-54** — El check no decide por palabras: una evidencia cuyo `reference` contiene
  `java.lang.NullPointerException` y establece `CUSTOMIZED_SAFE` cumple. Una cuyo `reference` es
  neutro y establece `RAW_TECHNICAL_ERROR_EXPOSED` falla. · rojo visto: si
- **E-55** — Nada con forma de credencial sale, tampoco como clave de un diccionario.
  · rojo visto: si
- **E-56** — Una evidencia ilegible que nombra la superficie o el escenario impide el `PASS`, y un
  id que no es texto nunca levanta una excepción. · rojo visto: si
- **E-57** — La falla establecida gana siempre: una exposición citada con el registro en
  `CUSTOMIZED_SAFE` da el mismo `FAIL` que con el registro honesto. · rojo visto: si
- **E-58** — El bloqueo es uno solo. Una prueba insegura que nombra la superficie, y que está
  citada o dice que hay una exposición, impide un `NOT_APPLICABLE` y un `PASS`. Nunca tapa un
  `FAIL` y nunca reemplaza un sin resolver anterior. Una que nombra algo que no está en el registro
  ni en el alcance no mueve nada, y una no citada que dice "customizado" tampoco. (Angostado el
  24-09-2026 a la regla 5, que es la de Vu3 y Vu5.)
  · rojo visto: si
- **E-59** — El registro vacío instalado valida contra el schema, y una clave de más en cualquier
  capa no valida. · rojo visto: si
- **E-60** — Una entrada del registro fuera del alcance impide el `PASS` con
  `ERROR_SURFACE_COVERAGE_UNRESOLVED`. Estar afuera nunca hace `FAIL` por sí solo; una exposición
  establecida en esa entrada sí, por la regla 3. · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/52_es0902_vu6_mensajes_de_error.py`, con el
id en el título del test. Ninguno lleva `· verificación: lectura`.

## Riesgos conocidos

- **Exigir el escenario `UNEXPECTED_ERROR` en cada superficie** deja sin resolver casi todo proyecto
  real hasta que alguien lo pruebe. Es verdad, y es el camino por el que se escapa la página por
  defecto.
- **La frontera entre `ERROR_HANDLER_MAPPING` y `ERROR_HANDLER_PRESENCE`** depende de que la
  evidencia nombre la superficie y el `errorType`. Una evidencia mal clasificada sostiene lo que no
  probó.
- **El enmascaramiento HTTP solo se juzga para el error inesperado, o con contrato.** Un `404`
  convertido en `200` sin contrato no se detecta, y es a propósito: sin contrato el código sería
  inventado.
