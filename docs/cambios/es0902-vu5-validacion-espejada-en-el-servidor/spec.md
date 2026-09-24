# ES0902 Vu5 — toda validación del cliente está espejada en el servidor

**Estado:** verificado y cerrado · **Fecha:** 24-09-2026 · **Regla:** ES0902 6.2 §6 Vu5

## Qué problema resuelve

> *"Toda validación del lado del cliente, debe estar espejada del lado del servidor."*
> (ES0902 v6.2, §6)

La fila de Vu5 está en la matriz: `CONDITIONAL` sobre `clientValidationPresent`, con una policy, un
check y cero reviews. Sus dos controles, `client-validation-server-mirroring-required` y
`client-server-validation-parity`, están declarados y no construidos. El mapa cruzado ya declara
`ES0902.Vu5 → ES0901.P5` como `EQUIVALENCE_REVIEW_REQUIRED`.

Vu5 tiene siete formas baratas de ponerse en verde, y este cambio las cierra:

1. **El nombre por la regla.** Que el campo, el DTO o el schema se llamen igual en los dos lados no
   prueba que el servidor valide.
2. **La librería por la ejecución.** Una librería compartida instalada, o un schema importado por
   los dos lados, no dice si el servidor lo ejecuta sobre ese camino.
3. **El atributo por la validación.** Un `required` de HTML o un tipo de TypeScript viven en el
   cliente, y el cliente se saltea.
4. **La transformación por la validación.** Enmascarar, formatear, normalizar o sanitizar en el
   cliente no es validar en el servidor.
5. **El 403 por el rechazo.** Que el servidor responda "no autorizado" no prueba que rechace la
   entrada mal formada.
6. **Un cliente por todos.** El frontend público en verde no dice nada del backoffice ni del móvil.
7. **La dirección al revés.** Vu5 va del cliente al servidor. Exigir que toda validación del
   servidor exista en el cliente es inventar.

Y la peligrosa: probar el servidor con datos reales, con escrituras destructivas o en producción.

## Qué queda afuera

- **La dirección servidor → cliente.** Una validación que solo existe en el servidor no viola Vu5.
- **El código de estado y el mensaje de error.** Vu5 no los define. Lo que importa es que la entrada
  inválida no se procese como válida.
- **Una topología propia.** Los clientes salen del inventario de C1 y de la evidencia de alcance, y
  las operaciones del servidor salen de `interfaces` del contexto de proyecto.
- **Tocar C1, Vu1..Vu4 o ES0901 P5.** P5 no está construido. Vu5 no lee ni escribe su resultado, y
  el mapa cruzado sigue en `EQUIVALENCE_REVIEW_REQUIRED`.
- **La autorización.** Es Vu8. Vu5 no la juzga ni la reemplaza.
- **Ejecutar la prueba contra el servidor.** El check lee la evidencia de una prueba ya hecha y
  decide si era segura.
- **Cambiar los agentes de la fila.** El pedido nombra a `dev-security`. La matriz instalada declara
  `dev-security`, `dev-backend` y `dev-frontend`, y no se migra, igual que en Vu3 y Vu4 por decisión
  del usuario del 23-09-2026.
- **Un agente, una skill, una review o un algoritmo nuevo en `seguridad.py`.** Vu5 va por el camino
  genérico, y `ALGORITMOS` sigue en diez.
- **Un subsistema de reporte propio.** El resultado entra al libro de seguridad por los productores
  que ya existen.

## Las decisiones, y por qué

### Una validación por entrada, y cada una se juzga sola

Cada cliente del registro (`clientSurfaceId`, `clientType`) trae sus validaciones. Cada validación
tiene `validationId`, `inputRef`, `constraint`, `serverMapping`, `parity`, `verificationMode` y
`evidence`, y se evalúa por separado. Un cliente en verde no tapa otro.

### Los clientes que hay que cubrir salen de evidencia que ya existe

Los clientes que hay que cubrir son dos:
- las superficies del inventario de C1, leído con su cargador;
- los que nombra una evidencia autoritativa citada `CLIENT_SURFACE_SCOPE`.

Cada uno se cubre de una de dos maneras:
- **Con una entrada en el registro que trae al menos una validación.** Una entrada vacía no cubre.
- **Con una evidencia autoritativa y legible de `CLIENT_VALIDATION` en `ABSENT` que nombra esa
  superficie.** Si la superficie tiene entrada, esa evidencia tiene que estar citada desde ella. Si
  no tiene entrada, alcanza con que la evidencia nombre la superficie, porque no hay desde dónde
  citarla.

Si falta las dos, da `CLIENT_VALIDATION_COVERAGE_UNRESOLVED`, y la señal nunca da `FALSE` con una
superficie sin cubrir.
Un cliente del registro que no está en ninguno de los dos también se evalúa, y además impide el
`PASS` con el mismo estado: si el registro y el alcance no coinciden, la cobertura no está entera.

### La operación del servidor es una interfaz del contexto de proyecto

`serverMapping.operationRef` tiene que ser igual en NFC a un `interface_id` de
`interfaces.items[]` del contexto de proyecto. Si es nulo, no aparece o el contexto no está, da
`CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED`. No se arma otro inventario de endpoints.

### La señal

```
TRUE        una validación del registro con una evidencia citada y legible de CLIENT_VALIDATION en
            PRESENT; declarativa, generada o de framework cuenta igual
FALSE       todas las superficies del alcance con evidencia autoritativa de CLIENT_VALIDATION en
            ABSENT, el registro vacío para ellas y la cobertura entera
UNRESOLVED  todo lo demás
```

Una dependencia de una librería de validación (`DEPENDENCY_MANIFEST`), sola, no enciende la señal.
Que no aparezcan funciones de validación explícitas no la apaga.

### El resultado de una validación sale de estos pasos

Se recorren los pasos. Una falla en cualquiera de ellos le gana a un sin resolver de un paso
anterior. Si no hay ninguna falla, gana el primer sin resolver en el orden de la lista.

1. **Mapeo:** `operationRef` resuelto, como dice la sección anterior. Si no, da
   `CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED`.
2. **`serverMapping.enforcementStatus`:**
   - `MISSING` da `SERVER_VALIDATION_MISSING`, que es `FAIL`, si una evidencia legible y citada lo
     establece. Lo que dice "no" pasa por la misma compuerta que lo que dice "sí".
   - `UNRESOLVED`, o `PRESENT` sin evidencia que lo sostenga, da `VALIDATION_EQUIVALENCE_UNRESOLVED`.
3. **`parity`:**
   - `EQUIVALENT` cumple si una evidencia citada, legible y de enforcement lo establece para esa
     validación.
   - `SERVER_STRONGER_COMPATIBLE` necesita eso más una evidencia autoritativa citada
     `CONTRACT_COMPATIBILITY` en `COMPATIBLE` para esa validación. Si no la tiene, o si dice
     `INCOMPATIBLE`, da `VALIDATION_EQUIVALENCE_UNRESOLVED`. Un servidor más estricto que rechaza
     entrada válida no es una brecha de seguridad, pero tampoco es espejo.
   - `SERVER_WEAKER`, establecido por una evidencia citada, da `SERVER_VALIDATION_WEAKER`, que es
     `FAIL`. Sin esa evidencia, queda sin resolver.
   - `UNRESOLVED` da `VALIDATION_EQUIVALENCE_UNRESOLVED`.
4. **Prueba directa:** una prueba segura y citada con `outcome: INVALID_INPUT_ACCEPTED` da
   `SERVER_VALIDATION_MISSING`, que es `FAIL`, aunque el registro diga `EQUIVALENT`. Es la regla 3:
   registro y evidencia se contradicen en las dos direcciones.

Las clases de evidencia de enforcement, que son las únicas que sostienen que el servidor valida,
son estas:
- `SERVER_VALIDATION_CODE`
- `UNIT_TEST`
- `INTEGRATION_TEST`
- `CONTRACT_TEST`
- `AUTHORIZED_QA_DIRECT_REQUEST`
- `OTHER_AUTHORITATIVE_EVIDENCE`

Para `SERVER_VALIDATION_CODE` y los tests, el ítem tiene que nombrar la operación del mapeo y el
`validationId`. No hace falta una prueba en ejecución si la evidencia estática ya es de esta clase.

No sostienen nada:
- `CLIENT_CODE`, `HTML_ATTRIBUTE`, `TYPESCRIPT_TYPE` y `UI_OBSERVATION`;
- `SHARED_SCHEMA_PRESENCE`, `DEPENDENCY_MANIFEST`, `DTO_NAME_MATCH` y `FIELD_NAME_MATCH`;
- `CLIENT_TRANSFORMATION`, que cubre máscara, formato, normalización y sanitización;
- un README, un agente o una skill.

Un schema compartido cuenta solo con una evidencia de enforcement que establece
`SHARED_SCHEMA_SERVER_EXECUTION` para esa operación.

Una restricción del cliente que transforma (`MASKING`, `FORMATTING`, `NORMALIZATION`,
`SANITIZATION`) se juzga como cualquier otra: el servidor tiene que validar por su cuenta el dominio
que el cliente acepta. Si lo hace, sobre el valor ya normalizado, cumple.

### Validar no es autorizar

Una prueba directa sostiene el rechazo solo si dice `rejectedBy: VALIDATION`. Hay dos casos que
nunca prueban que el servidor validó:
- `rejectedBy: AUTHORIZATION`;
- un `responseStatus` de 401 o 403, aunque diga `VALIDATION`.

En los dos, la validación queda sin resolver. Aparte de esa regla, el check no lee ningún código de
estado ni ningún mensaje para decidir.

### La prueba es segura o no cuenta

Una `AUTHORIZED_QA_DIRECT_REQUEST` cuenta si cumple todo esto:
- `authorized: true`;
- el ambiente es `DEV`, `QA`, `HML` u `OTHER`;
- trae `testIdentityRef`, que es un contexto de prueba autorizado;
- `syntheticValues: true`;
- `destructive` no es `true`;
- `realPrivilegedData` no es `true`;
- `rawSecretsLogged` no es `true`.

Si no, da `SERVER_VALIDATION_TEST_UNSAFE`. Con `outcome: UNAVAILABLE`, da `TEST_TARGET_UNAVAILABLE`.
Ninguna de las dos es `FAIL`.

### Las reglas que ya costaron pases, desde el primer día

1. Lo que dice "no" pasa por la misma compuerta que lo que dice "sí".
2. Lo ilegible que nombra la validación impide el `PASS`, citado o no, y lo no citado nunca hace
   `FAIL`. Un id que no es texto es ilegible, nunca una excepción.
3. **Registro y evidencia se contradicen en las dos direcciones**, y en Vu5 una falla establecida
   gana siempre. Si una evidencia citada y legible establece `MISSING`, `SERVER_WEAKER` o
   `INVALID_INPUT_ACCEPTED` para una validación, el resultado es `FAIL`, diga lo que diga el
   registro y diga lo que diga otra evidencia, citada o no. Así, declarar la falla con honestidad
   nunca da un resultado más blando que declarar que cumple. Una evidencia legible no citada que
   dice que falla deja la validación sin resolver, y nunca hace `FAIL`.
4. Todo id se normaliza a NFC antes de comparar y antes de contar repetidos.
5. **Un solo paso de bloqueo por el que pasan todas las ramas**, también `NOT_APPLICABLE`.
   Bloquear impide un `PASS` y nunca tapa un `FAIL`.
   - **Qué bloquea:** una prueba insegura o sin objetivo, y solo si nombra una validación del
     registro o una superficie del alcance. Una prueba que nombra solamente validaciones u
     operaciones que no están en el registro no mueve nada.
   - **Qué estado se informa:** el bloqueo no reemplaza un sin resolver de un paso anterior. Si hay
     uno, ese es el estado que sale, y el del bloqueo queda en `states[]`.
   - **Con la señal en `UNRESOLVED`,** el estado es `APPLICABILITY_UNRESOLVED`.
6. **Hay una sola regla de salida de secretos**, la de `controles/lib/evidencia.py`, que también
   redacta las claves de un diccionario. Los ayudantes no se copian.
   - Sigue reconociendo la contraseña que fijó E-03b, y suma `contrasenia`, `pw` y `pin` seguidos
     de `:` o `=`.
   - Para una palabra en castellano (`contraseña`, `contrasenia`, `clave`) y para `pass`, un espacio
     solo no alcanza como separador: tiene que haber `:`, `=`, `=>`, `:=`, `>` o una comilla.
   - Así "la clave del trámite es obligatoria", "se valida la contraseña mínima de 8" y
     "pass-through del valor" salen enteras. `--password x` y `set password x` se siguen
     redactando.

### El registro es cerrado

El registro del paquete se instala vacío. El schema del paquete se cierra con
`additionalProperties: false` en todas sus capas, igual que el de Vu4. Es la única divergencia de
schema que cambia qué valida; `$id` y `description` son anotaciones. `constraint.description` es
texto libre, y pasa por la regla de salida como cualquier otro texto.

### El agregado

- Una validación en `FAIL` hace `FAIL` el agregado, y el estado que se informa es el de la falla.
- Si no hay ninguna en `FAIL`, una sin resolver impide el `PASS`.
- `PASS` exige cobertura entera y todas las validaciones cumplidas.

La salida sigue la forma de la de Vu4, con `clients[]` en vez de `sessions[]`.

### Los límites con otras reglas

- **P5 de ES0901.** Vu5 no lee ni escribe el resultado de P5. El mapa cruzado conserva
  `EQUIVALENCE_REVIEW_REQUIRED`, y una evidencia compartida no copia el resultado final de ninguna
  de las dos.
- **Vu6, Vu8, OWASP y la aprobación.** El `PASS` de Vu5 no pone en `PASS` a Vu6 (manejo de
  errores), a Vu8 (roles y autorización), a Vu10 (OWASP) ni a la aprobación oficial.

### La unidad de trabajo lleva `rules.Vu5`, y el reporte lo recibe como cualquier regla

`standards.ES0902.rules.Vu5` lleva `applicability`, `result`, `clients` y `evidence`: ids y
estados, nunca contenido. La salida pasada por `seguridad.resultado("Vu5", …)` y por
`reporte_seguridad.productores.desde_regla` entra al mismo libro. El dominio "Validación y manejo
de errores" ya incluye a Vu5.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/client-server-validation-parity.json` | El registro del proyecto, instalado vacío |
| `comun/schemas/client-server-validation-parity.schema.json` | Su contrato, cerrado en todas las capas |
| `harnesses/desarrollo/reglas/es0902-vu5-*.md` | Gobierno, señal y procedimiento, como vinieron |
| `harnesses/desarrollo/controles/policies/client-validation-server-mirroring-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/client-server-validation-parity.py` | La señal y el check |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu5` en la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles |
| `docs/seguridad-es0902.md` | Vu5 |
| `tests/casos/50_es0902_vu5_validacion_espejada.py` | Los escenarios |

## Escenarios verificables

Numerados como el pedido: `E-nn` es `VU5-nn`. Los que agrega esta spec van después del 62.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu5`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `clientValidationPresent`, `client-validation-server-mirroring-required` y
  `client-server-validation-parity` están exactos en la matriz, el registro de controles y el
  módulo. Los agentes primarios son los de la matriz, en este orden: `dev-security`, que es el dueño
  normativo, `dev-backend` y `dev-frontend`. · rojo visto: si
- **E-03** — No hay ningún agente, skill ni review nuevo, y `ALGORITMOS` sigue en diez.
  · rojo visto: si

### La señal

- **E-04** — Una validación explícita del cliente, citada con su evidencia, enciende la señal, y
  pasada por `senales` enciende la fila. · rojo visto: si
- **E-05** — Una validación declarativa o generada, evidenciada, enciende la señal.
  · rojo visto: si
- **E-06** — Un `DEPENDENCY_MANIFEST` con una librería de validación, solo, no enciende la señal.
  · rojo visto: si
- **E-07** — Evidencia autoritativa de `CLIENT_VALIDATION` en `ABSENT` para todo el alcance, con el
  registro vacío y la cobertura entera, apaga la señal y deja el check en `NOT_APPLICABLE`. Una
  fuente débil no la apaga. · rojo visto: si
- **E-08** — Un alcance con clientes sin registro ni ausencia autoritativa, y sin ninguna validación
  presente, da la señal `UNRESOLVED`. · rojo visto: si

### La dirección

- **E-09** — Solo las validaciones del cliente generan exigencias: el check no tiene ningún camino
  que parta de una validación del servidor. · rojo visto: si
- **E-10** — Una evidencia de validación que existe solo en el servidor no cambia el resultado.
  · rojo visto: si
- **E-11** — Con todas las validaciones del cliente cumplidas y validaciones extra solo en el
  servidor, da `PASS`. · rojo visto: si

### La paridad

- **E-12** — `required` en el cliente y en el servidor, `EQUIVALENT` y con evidencia de
  enforcement, cumple. · rojo visto: si
- **E-13** — El cliente exige un valor y el servidor acepta `null`: `SERVER_WEAKER` establecido da
  `SERVER_VALIDATION_WEAKER`, que es `FAIL`. · rojo visto: si
- **E-14** — Un enum en el cliente y un string libre en el servidor da `FAIL`, igual que E-13.
  · rojo visto: si
- **E-15** — Una cota inferior en el cliente y ninguna en el servidor da `FAIL`, igual que E-13.
  · rojo visto: si
- **E-16** — Con `maxLength` de 100 en el cliente y 80 en el servidor, declarado
  `SERVER_STRONGER_COMPATIBLE` y sin `CONTRACT_COMPATIBILITY`, da
  `VALIDATION_EQUIVALENCE_UNRESOLVED`. · rojo visto: si
- **E-17** — Lo mismo, con una `CONTRACT_COMPATIBILITY` autoritativa en `COMPATIBLE`, cumple.
  · rojo visto: si
- **E-18** — Con `CONTRACT_COMPATIBILITY` en `INCOMPATIBLE`, queda sin resolver y no cumple.
  · rojo visto: si
- **E-19** — `enforcementStatus: MISSING`, establecido, da `SERVER_VALIDATION_MISSING`, que es `FAIL`.
  · rojo visto: si
- **E-20** — `parity: UNRESOLVED` da `VALIDATION_EQUIVALENCE_UNRESOLVED`. · rojo visto: si

### Lo que se parece y no es

- **E-21** — Un `FIELD_NAME_MATCH`, solo, no aprueba. · rojo visto: si
- **E-22** — Un `DTO_NAME_MATCH`, solo, no aprueba. · rojo visto: si
- **E-23** — Un `DEPENDENCY_MANIFEST` de la librería compartida, solo, no aprueba. · rojo visto: si
- **E-24** — Un `SHARED_SCHEMA_PRESENCE`, solo, no aprueba. · rojo visto: si
- **E-25** — Una evidencia de enforcement que establece `SHARED_SCHEMA_SERVER_EXECUTION` para la
  operación sostiene la paridad. · rojo visto: si
- **E-26** — Un `HTML_ATTRIBUTE` `required`, solo, no aprueba. · rojo visto: si
- **E-27** — Un `TYPESCRIPT_TYPE`, solo, no aprueba. · rojo visto: si

### Transformar no es validar

- **E-28** — Una máscara del cliente con solo `CLIENT_TRANSFORMATION` como evidencia no cumple.
  · rojo visto: si
- **E-29** — Lo mismo con la sanitización. · rojo visto: si
- **E-30** — Lo mismo con la normalización. · rojo visto: si
- **E-31** — Una `NORMALIZATION` del cliente con evidencia de que el servidor valida el dominio ya
  normalizado cumple. · rojo visto: si

### Validar no es autorizar

- **E-32** — Una prueba con `rejectedBy: AUTHORIZATION` no sostiene la validación.
  · rojo visto: si
- **E-33** — Una prueba con `responseStatus: 403`, sola, no sostiene la validación, aunque diga
  `rejectedBy: VALIDATION`. · rojo visto: si
- **E-34** — Una prueba segura con un contexto de prueba autorizado, que llega a la validación y la
  ve rechazar, sostiene la validación. · rojo visto: si
- **E-35** — El `PASS` de Vu5 no pone en `PASS` a Vu8: el resultado de Vu8 no cambia.
  · rojo visto: si

### La prueba directa

- **E-36** — Una prueba directa segura con `INVALID_INPUT_ACCEPTED` da `FAIL`, aunque el registro
  diga `EQUIVALENT`. · rojo visto: si
- **E-37** — Una prueba directa segura con `INVALID_INPUT_REJECTED` y `rejectedBy: VALIDATION`
  sostiene la validación. · rojo visto: si
- **E-38** — Dos pruebas con mensajes de error distintos a los del cliente dan el mismo resultado:
  el mensaje no decide. · rojo visto: si
- **E-39** — Un rechazo por validación con `responseStatus` 400, con 422 o sin código da el mismo
  resultado. · rojo visto: si
- **E-40** — Una evidencia citada de que el servidor procesó como válida una entrada mal formada da
  `FAIL`. · rojo visto: si

### Los clientes

- **E-41** — El frontend público cumplido y el backoffice con una validación en `FAIL` dan `FAIL`.
  · rojo visto: si
- **E-42** — Un cliente móvil se evalúa con sus propias validaciones y sale en `clients[]`.
  · rojo visto: si
- **E-43** — Lo mismo con un cliente legado. · rojo visto: si
- **E-44** — Un `operationRef` que no está en `interfaces` del contexto de proyecto, o sin contexto,
  da `CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED`. · rojo visto: si

### La prueba segura

- **E-45** — Una prueba en `PRD` no cuenta y da `SERVER_VALIDATION_TEST_UNSAFE`. El módulo no
  ejecuta nada. · rojo visto: si
- **E-46** — Una prueba en QA con `syntheticValues: true` y el resto seguro cuenta.
  · rojo visto: si
- **E-47** — Una prueba con `destructive: true` no cuenta. · rojo visto: si
- **E-48** — Una prueba con `realPrivilegedData: true` no cuenta, y ninguna condición de la prueba
  segura exige datos reales. · rojo visto: si
- **E-49** — Sin autorización, sin contexto de prueba, sin valores sintéticos o con secretos
  registrados, da `SERVER_VALIDATION_TEST_UNSAFE`. · rojo visto: si
- **E-50** — Una prueba insegura no es `FAIL`, también cuando dice `INVALID_INPUT_ACCEPTED`.
  · rojo visto: si

### Los límites

- **E-51** — Con un resultado de P5 en `PASS` o en `FAIL` en la evidencia, el de Vu5 no cambia. El
  mapa cruzado sigue en `EQUIVALENCE_REVIEW_REQUIRED`. · rojo visto: si
- **E-52** — El `PASS` de Vu5 no pone en `PASS` a P5. · rojo visto: si
- **E-53** — Una evidencia citada por Vu5 y por otra regla no copia el resultado final: la otra
  regla sigue con el suyo. · rojo visto: si
- **E-54** — El `PASS` de Vu5 no dice nada de la autorización: ningún campo de la salida afirma
  roles ni permisos. · rojo visto: si
- **E-55** — El `PASS` de Vu5 no pone en `PASS` a Vu6. · rojo visto: si
- **E-56** — El `PASS` de Vu5 no pone en `PASS` a Vu10. · rojo visto: si
- **E-57** — El `PASS` de Vu5 no cambia la aprobación oficial: C2 y el estado oficial no se mueven.
  · rojo visto: si

### El agregado

- **E-58** — Una validación en `SERVER_VALIDATION_MISSING` o en `SERVER_VALIDATION_WEAKER` hace
  `FAIL` el agregado. · rojo visto: si
- **E-59** — Un mapeo material sin resolver impide el `PASS`. · rojo visto: si
- **E-60** — La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales
  en NFC. · rojo visto: si
- **E-61** — La trazabilidad `ES0902 / 6.2 / 6 / Vu5` viaja en todo resultado, y la unidad de
  trabajo lleva `rules.Vu5` con aplicabilidad, resultado, clientes y evidencia por id.
  · rojo visto: si
- **E-62** — La salida del check, pasada por `seguridad.resultado` y
  `reporte_seguridad.productores.desde_regla`, entra como `RULE_EVALUATION` de `ES0902.Vu5` al mismo
  libro. `reporte_seguridad/` no tiene ningún archivo nuevo. · rojo visto: si

### Lo que agrega esta spec

- **E-63** — Nada con forma de credencial sale, tampoco en `constraint.description` ni como clave
  de un diccionario, en la salida, en la señal y en `rules.Vu5`. · rojo visto: si
- **E-64** — Una evidencia ilegible que nombra la validación, citada o no, impide el `PASS`,
  también cuando el `evidenceId` es una lista o un dict, y nunca levanta una excepción.
  · rojo visto: si
- **E-65** — El bloqueo es uno solo para todas las ramas. Una prueba insegura que dice
  `INVALID_INPUT_ACCEPTED` impide un `NOT_APPLICABLE` igual que un `PASS`, y nunca tapa un `FAIL`.
  · rojo visto: si
- **E-66** — El registro vacío instalado valida contra el schema, y una clave de más en cualquier
  capa no valida. · rojo visto: si
- **E-67** — Un cliente del registro que no está en el alcance de C1 ni en `CLIENT_SURFACE_SCOPE`
  impide el `PASS` con `CLIENT_VALIDATION_COVERAGE_UNRESOLVED`, y nunca hace `FAIL`.
  · rojo visto: si
- **E-68** — La falla establecida gana siempre. Un `SERVER_WEAKER` o un `MISSING` declarados, con la
  evidencia citada que los establece y otra no citada que dice que cumple, dan `FAIL`: el mismo
  resultado que con el registro en `EQUIVALENT` o en `PRESENT`. · rojo visto: si
- **E-69** — Una entrada del registro sin validaciones no cubre su superficie. Un mapeo sin resolver
  más una prueba insegura citada informan `CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED`, con el
  estado de la prueba en `states[]`. · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/50_es0902_vu5_validacion_espejada.py`, con
el id en el título del test. Ninguno es sobre una corrida de un modelo, así que ninguno lleva
`· verificación: lectura`.

## Riesgos conocidos

- **El mapeo depende de `interfaces` del contexto de proyecto**, que el agente escribe leyendo el
  repositorio y que sale `inferred` salvo que haya un OpenAPI. Sin contexto, todo mapeo queda sin
  resolver.
- **El registro lo declara el proyecto.** Una validación del cliente que nadie registra no se ve,
  salvo que su superficie esté en el alcance y quede sin cubrir.
- **La frontera entre `SERVER_VALIDATION_CODE` y un nombre parecido** depende de que la evidencia
  nombre la operación y el `validationId`. Un ítem mal clasificado como código del servidor
  sostiene algo que no probó.
