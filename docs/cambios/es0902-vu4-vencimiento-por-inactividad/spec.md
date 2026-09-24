# ES0902 Vu4 — una sesión inactiva vence sola, aparte del token de OpenID

**Estado:** verificado y cerrado · **Fecha:** 23-09-2026 · **Regla:** ES0902 6.2 §6 Vu4

## Qué problema resuelve

> *"Toda sesión en stand by, tiene que tener un tiempo límite para su utilización. Esto,
> independientemente del límite de tiempo que posee el token de autenticación del OpenID."*
> (ES0902 v6.2, §6)

La fila está en la matriz: `CONDITIONAL` sobre `sessionPresent`, con una policy, un check y cero
reviews. Sus dos controles, `session-inactivity-timeout-required` y `session-inactivity-timeout`,
están declarados y no construidos. `seguridad._vu4` ya separa la evidencia del token de la del
vencimiento, pero nada la produce.

Vu4 tiene seis formas baratas de ponerse en verde, y este cambio las cierra:

1. **El token por la sesión.** Que el access token venza a los N minutos no es que la sesión de la
   aplicación venza. La regla lo dice en su segunda oración.
2. **El SSO por la sesión.** Que venza la sesión de Keycloak tampoco.
3. **La configuración por el comportamiento.** Un `timeout = 900` en un archivo no prueba que la
   sesión vieja deje de servir.
4. **La pantalla por el recurso.** Un modal de "tu sesión expiró" mientras la API sigue aceptando
   la sesión vieja es una sesión viva.
5. **La actividad inventada.** Decidir que mover el mouse, el polling o el refresh del token
   reinician el reloj es escribir una política que el proyecto no escribió.
6. **Una superficie por todas.** La sesión ciudadana en verde no dice nada del backoffice.

Y la peligrosa: probar el vencimiento con una cuenta real, o bajando el timeout de producción para
que la prueba termine antes.

## Qué queda afuera

- **Una duración.** ES0902 no da ningún número, y el check no juzga si una duración evidenciada es
  corta o larga. Ni 5, ni 15, ni 30 minutos.
- **Qué eventos cuentan como actividad.** El check usa la política del proyecto o dice que no la
  sabe.
- **Un segundo inventario de superficies.** Las superficies salen del inventario de C1, leído con su
  cargador, igual que en Vu1 y Vu3.
- **Tocar C1, Vu1, Vu2 o Vu3.** Vu4 importa sus cargadores y no cambia su comportamiento.
- **El vencimiento del SSO del proveedor y el tiempo de vida absoluto de la sesión.** Vu4 gobierna la
  sesión de la aplicación inactiva. Otra fuente que los pida se evalúa por separado.
- **Ejecutar la prueba de vencimiento.** El check lee la evidencia de una prueba ya hecha y decide si
  era segura.
- **Cambiar los agentes de la fila.** El pedido nombra a `dev-security` como agente primario, y la
  matriz instalada declara `dev-security` y `dev-backend`. No se migra: `dev-security` es el dueño
  normativo y `dev-backend` queda como está. Es la misma divergencia que Vu3, y la decide el usuario.
- **Un agente, una skill, una review, o un algoritmo nuevo en `seguridad.py`.** `_vu4` ya existe y
  `ALGORITMOS` sigue en diez.
- **Un subsistema de reporte propio.** El resultado de Vu4 entra al libro de seguridad por los
  productores que ya existen.

## Las decisiones, y por qué

### Cinco dominios, y Vu4 juzga uno

```
APPLICATION_INACTIVITY   lo que Vu4 juzga
OIDC_ACCESS_TOKEN        se informa; solo, no aprueba
OIDC_REFRESH_TOKEN       se informa; solo, no aprueba
IDP_SSO_SESSION          se informa; solo, no aprueba; activo no es FAIL
APPLICATION_SESSION      el modelo de la sesión, lo que enciende la señal
```

Cada evidencia del catálogo dice de qué dominio habla. Solo la de `APPLICATION_INACTIVITY` puede
sostener que la sesión vence.

### La señal sale del inventario de C1, del registro de Vu3 y del de Vu4

```
TRUE        una sesión del registro de Vu4 con sessionModel distinto de UNRESOLVED, o una
            superficie cuya señal de Vu3 es TRUE, o evidencia legible de APPLICATION_SESSION
            en PRESENT
FALSE       todas las superficies con evidencia autoritativa de APPLICATION_SESSION en ABSENT, los
            registros de Vu3 y Vu4 vacíos para ellas y la cobertura entera; o authenticationPresent
            en FALSE con el inventario y los registros vacíos
UNRESOLVED  todo lo demás
```

Ni OIDC, ni un backend sin estado, ni los tokens en el cliente apagan la señal. Una sesión móvil
autenticada la enciende igual que una del browser.

### Una sesión por entrada, y ninguna superficie se omite en silencio

Cada entrada del registro es una sesión: `sessionId`, `surfaceRef` a una superficie de C1, sus roles
y su ambiente. Se evalúa cada una por separado, y dos políticas distintas para dos roles son dos
entradas. Una superficie de C1 con sesión y sin ninguna entrada da `SESSION_COVERAGE_UNRESOLVED`.
Una entrada cuya `surfaceRef` no está en el inventario también se evalúa, y su ausencia en C1 se
informa. Además impide el `PASS` con `SESSION_COVERAGE_UNRESOLVED`: si el registro y el inventario
no coinciden, la cobertura no está entera. Nunca hace `FAIL`.

Si una evidencia autoritativa citada `SESSION_ROLE_SCOPE` nombra los roles de una superficie, cada
uno de esos roles tiene que aparecer en alguna entrada de esa superficie. Si no,
`SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED`. No se inventa que todos los roles comparten la misma
duración.

### El resultado de una sesión sale de estos pasos

Se recorren los cinco pasos. Una falla en cualquiera de ellos le gana a un sin resolver de un paso
anterior: `sessionModel` en `UNRESOLVED` junto con un `valueRef` igual al del token da
`TOKEN_TIMEOUT_ONLY`. Si no hay ninguna falla, gana el primer sin resolver en el orden de la lista.

1. **`sessionModel` en `UNRESOLVED`:** `SESSION_INACTIVITY_TIMEOUT_UNRESOLVED`.
2. **`inactivityTimeout.status`:**
   - `NOT_CONFIGURED` con alguna referencia de `oidcTimeouts` da `TOKEN_TIMEOUT_ONLY`, que es
     `FAIL`. Sin ninguna, es `FAIL`.
   - Las dos exigen una evidencia legible y citada que lo establezca, porque lo que dice "no" pasa
     por la misma compuerta que lo que dice "sí".
   - `UNRESOLVED` es `SESSION_INACTIVITY_TIMEOUT_UNRESOLVED`.
3. **Con `CONFIGURED`:**
   - `valueRef` nulo es `SESSION_INACTIVITY_TIMEOUT_UNRESOLVED`: el valor no se infiere.
   - `independentFromOidcTokenTimeout` en `NO`, o un `valueRef` igual en NFC a una de las tres
     referencias de `oidcTimeouts`, es `TOKEN_TIMEOUT_ONLY`: el valor salió del token.
   - `UNRESOLVED` en la independencia es `SESSION_INACTIVITY_TIMEOUT_UNRESOLVED`.
   - El `valueRef` se conserva en la salida como evidencia, sin juzgarlo.
4. **`activitySemantics`:**
   - `DEFINED` o `NOT_REQUIRED` necesitan un `sourceRef` citado, legible, autoritativo y del
     dominio `APPLICATION_INACTIVITY`.
   - Si no lo tienen, o si dicen `UNRESOLVED`, el resultado es `SESSION_ACTIVITY_SEMANTICS_UNRESOLVED`.
   - Una observación de que el mouse, el scroll, el foco, el polling, el refresh del token o un
     heartbeat reinician el reloj no define la semántica. Solo una política citada puede hacerlo.
   - Un ítem que establece `ACTIVITY_RESET_OBSERVATION` no puede ser el `sourceRef` de la semántica,
     aunque establezca también `ACTIVITY_SEMANTICS`. Si se declara observación, no es política.
5. **`verification.result`:**
   - `SESSION_REJECTED`, `REAUTHENTICATION_REQUIRED` o `NEW_SESSION_REQUIRED` cumplen solo si
     citan una evidencia legible de comportamiento, del dominio `APPLICATION_INACTIVITY`, para esa
     sesión y con ese mismo valor.
   - `OLD_INACTIVE_SESSION_STILL_USABLE` es `INACTIVE_SESSION_REMAINS_USABLE`, que es `FAIL`.
   - `TOKEN_TIMEOUT_ONLY` es `FAIL`.
   - `NOT_TESTED` y `UNRESOLVED` son `SESSION_INACTIVITY_TIMEOUT_UNRESOLVED`.

Las clases de comportamiento son estas:
- `AUTHORIZED_RUNTIME_TEST`
- `INTEGRATION_TEST`
- `UNIT_TEST`
- `PROTECTED_ENDPOINT_CHECK`
- `SESSION_STORE_OBSERVATION`
- `ASSESSMENT_FINDING`
- `OTHER_AUTHORITATIVE_EVIDENCE`

No sostienen nada `CONFIGURATION`, `SOURCE_CODE`, `UI_OBSERVATION`, `CLIENT_TIMER`, la configuración
del token o del SSO, un README, un agente o una skill. Con `evidenceMode: CONFIGURATION` y nada
más, la sesión queda sin resolver.

### La pantalla no tapa al recurso

Una evidencia legible que establece que un recurso protegido acepta la sesión vieja después del
intervalo es `INACTIVE_SESSION_REMAINS_USABLE`, aunque el registro diga `REAUTHENTICATION_REQUIRED`
y una `UI_OBSERVATION` muestre el login. Citada, es `FAIL`. No citada, deja la sesión sin resolver.
Es la regla 3 de Vu1: registro y evidencia se contradicen en las dos direcciones.

### Las reglas que ya costaron pases, desde el primer día

1. **Lo que dice "no" pasa por la misma compuerta que lo que dice "sí".** Una prueba insegura o sin
   objetivo no aprueba ni hace `FAIL`, diga lo que diga.
2. **Lo ilegible que nombra la sesión impide el `PASS`, citado o no, y lo no citado nunca hace
   `FAIL`.** "Nombra" es igualdad en NFC. Un id que no es texto es ilegible, nunca una excepción.
3. **Registro y evidencia se contradicen en las dos direcciones.**
4. **Todo id se normaliza a NFC antes de comparar y antes de contar repetidos.**
5. **Un solo paso de bloqueo por el que pasan todas las ramas**, también `NOT_APPLICABLE`. Bloquear
   impide un `PASS` y nunca tapa un `FAIL`.

Los ayudantes salen de `controles/lib/evidencia.py`, y no se copian.

### La prueba es segura o no cuenta

Una `AUTHORIZED_RUNTIME_TEST` cuenta si cumple todo esto:
- `authorized: true`;
- el ambiente es `DEV`, `QA`, `HML` u `OTHER`, y es el de la sesión;
- trae `testIdentityRef`;
- `realUserAccount` no es `true`;
- `rawSecretsLogged` no es `true`;
- `productionTimeoutWeakened` no es `true`.

Si no, es `SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE`. Con `outcome: UNAVAILABLE`, es
`TEST_TARGET_UNAVAILABLE`. Ninguna de las dos es `FAIL`.

### El registro es cerrado, y nada con forma de credencial sale

El registro del paquete se instala vacío. El schema del paquete se cierra con
`additionalProperties: false` en todas sus capas, igual que el de Vu3. Es la única divergencia de
schema que cambia qué valida. `$id` y `description` son anotaciones, como en Vu3. No tiene campo para una cookie, un id de sesión ni un token, y todo lo que sale pasa por la
regla de salida de `evidencia.py`. Que el registro se llame `sessionId` no lo vuelve un secreto: es
el nombre que el proyecto le da a la sesión, no el identificador de una sesión real. Pero si trae la
forma de una credencial, se redacta como cualquier otro id.

### El agregado

- Una sesión en `FAIL` hace `FAIL` el agregado. El estado que se informa es el de la falla:
  `TOKEN_TIMEOUT_ONLY`, `INACTIVE_SESSION_REMAINS_USABLE` o `FAIL`.
- Si no hay ninguna en `FAIL`, una sesión sin resolver impide el `PASS`.
- `PASS` exige cobertura entera y todas las sesiones cumplidas.

La salida sigue la forma de la de Vu3: `control`, `policy`, `rule`, `ruleKey`, `source`,
`sourceText`, `signal`, `signalValue`, `sessions[]`, `issues[]`, `coverage`, `state`, `states[]` y
`reason`. Además tiene `evaluar(caso, …)` y `aprueba(resultado)`.

### La unidad de trabajo lleva `rules.Vu4`

`standards.ES0902.rules.Vu4` lleva `applicability`, `result`, `sessions` y `evidence`: ids y
estados, nunca contenido. Se proyecta solo un resultado que dice ser del check de Vu4.

### El reporte de seguridad lo recibe como cualquier regla

La salida de Vu4, pasada por `seguridad.resultado("Vu4", …)` y por
`reporte_seguridad.productores.desde_regla`, entra al mismo `security-ledger.ndjson` como un
`RULE_EVALUATION` de `ES0902.Vu4`. No se agrega ningún módulo a `reporte_seguridad/`. El dominio
"Identidad y sesión" ya incluye a Vu4.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/session-inactivity-timeout.json` | El registro del proyecto, instalado vacío |
| `comun/schemas/session-inactivity-timeout.schema.json` | Su contrato, cerrado en todas las capas |
| `harnesses/desarrollo/reglas/es0902-vu4-*.md` | Gobierno, señal y procedimiento, como vinieron |
| `harnesses/desarrollo/controles/policies/session-inactivity-timeout-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/session-inactivity-timeout.py` | La señal y el check |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu4` en la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles |
| `docs/seguridad-es0902.md` | Vu4 |
| `tests/casos/49_es0902_vu4_vencimiento_por_inactividad.py` | Los escenarios |

## Escenarios verificables

Numerados como el pedido: `E-nn` es `VU4-nn`. Los que agrega esta spec van después del 57.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu4`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `sessionPresent`, `session-inactivity-timeout-required` y `session-inactivity-timeout`
  están exactos en la matriz, el registro de controles y el módulo. Los agentes primarios son los
  de la matriz, en este orden: `dev-security`, que es el dueño normativo, y `dev-backend`.
  · rojo visto: si
- **E-03** — No hay ningún agente, skill ni review nuevo, y `ALGORITMOS` sigue en diez.
  · rojo visto: si

### La señal

- **E-04** — Una sesión de aplicación autenticada en el registro pone la señal en `TRUE`, la cita, y
  pasada por `senales` enciende la fila. · rojo visto: si
- **E-05** — Una sesión `TOKEN_BASED_APPLICATION_SESSION` de browser enciende la señal.
  · rojo visto: si
- **E-06** — Una sesión de una app móvil autenticada enciende la señal. · rojo visto: si
- **E-07** — Una evidencia de backend sin estado, o de login delegado a OIDC, no apaga la señal.
  · rojo visto: si
- **E-08** — Evidencia autoritativa de que no hay sesión de aplicación en ninguna superficie, con los
  registros vacíos y la cobertura entera, apaga la señal y deja el check en `NOT_APPLICABLE`. Una
  fuente débil no la apaga. · rojo visto: si
- **E-09** — Con autenticación presente y la semántica de sesión sin establecer, la señal es
  `UNRESOLVED` y el check da `APPLICABILITY_UNRESOLVED`. · rojo visto: si

### La cobertura

- **E-10** — Las superficies salen del inventario de C1, leído con su cargador, y una superficie
  cuya señal de Vu3 es `TRUE` cuenta como superficie con sesión. El módulo no define un inventario
  propio. · rojo visto: si
- **E-11** — Una sesión de backoffice declarada en el registro se evalúa aunque la ciudadana cumpla,
  y aparece en `sessions[]`. · rojo visto: si
- **E-12** — Una superficie de C1 con sesión y sin ninguna entrada en el registro da
  `SESSION_COVERAGE_UNRESOLVED`. · rojo visto: si

### El token no es la sesión

- **E-13** — El vencimiento de la aplicación y el del access token salen por separado en la
  sesión, y una evidencia del access token sola no sostiene ningún vencimiento de la aplicación.
  · rojo visto: si
- **E-14** — Lo mismo con el refresh token. · rojo visto: si
- **E-15** — Lo mismo con el SSO del proveedor. · rojo visto: si
- **E-16** — Con `NOT_CONFIGURED` y una referencia de token, citado y establecido, da
  `TOKEN_TIMEOUT_ONLY`, que es `FAIL`. Con `independentFromOidcTokenTimeout: NO`, lo mismo.
  · rojo visto: si
- **E-17** — Un `valueRef` igual a la referencia del access token no aprueba: da
  `TOKEN_TIMEOUT_ONLY`. · rojo visto: si
- **E-18** — Una evidencia de que venció la sesión de Keycloak, sola, no aprueba.
  · rojo visto: si
- **E-19** — Un vencimiento independiente, configurado, con su semántica y con su comportamiento
  evidenciado, cumple la sesión. · rojo visto: si

### La duración

- **E-20** — El módulo no tiene ninguna duración: ninguna constante ni literal numérico de minutos
  o segundos decide un resultado. Una sesión con `valueRef: "cfg:timeout-3m"` y otra con
  `"cfg:timeout-8h"` dan el mismo resultado. · rojo visto: si
- **E-21** — `CONFIGURED` con `valueRef` nulo da `SESSION_INACTIVITY_TIMEOUT_UNRESOLVED`, y
  `UNRESOLVED` en el estado también. · rojo visto: si
- **E-22** — El `valueRef` sale tal cual en la sesión evaluada. · rojo visto: si
- **E-23** — Ninguna duración evidenciada da `FAIL` por corta o por larga. · rojo visto: si

### La actividad

- **E-24** — Una observación de que el movimiento del mouse reinicia el reloj, sin política citada,
  deja `SESSION_ACTIVITY_SEMANTICS_UNRESOLVED`. · rojo visto: si
- **E-25** — Lo mismo con el scroll. · rojo visto: si
- **E-26** — Lo mismo con el polling en segundo plano. · rojo visto: si
- **E-27** — Lo mismo con el refresh del token. · rojo visto: si
- **E-28** — Lo mismo con un heartbeat. · rojo visto: si
- **E-29** — Una política del proyecto citada, que define la actividad (incluso si dice que el
  refresh del token cuenta), resuelve la semántica. · rojo visto: si
- **E-30** — `activitySemantics` en `UNRESOLVED`, o `DEFINED` sin `sourceRef` citado y legible, da
  `SESSION_ACTIVITY_SEMANTICS_UNRESOLVED`. · rojo visto: si

### El comportamiento después del vencimiento

- **E-31** — Con `evidenceMode: CONFIGURATION` y una evidencia de configuración como única cita, la
  sesión no cumple. · rojo visto: si
- **E-32** — `SESSION_REJECTED` citado con una evidencia de comportamiento que lo establece cumple.
  · rojo visto: si
- **E-33** — `REAUTHENTICATION_REQUIRED` en las mismas condiciones cumple. · rojo visto: si
- **E-34** — `NEW_SESSION_REQUIRED` en las mismas condiciones cumple. · rojo visto: si
- **E-35** — `OLD_INACTIVE_SESSION_STILL_USABLE` es `INACTIVE_SESSION_REMAINS_USABLE` y `FAIL`.
  · rojo visto: si
- **E-36** — Una `UI_OBSERVATION` del login más una evidencia citada de que el endpoint protegido
  acepta la sesión vieja da `INACTIVE_SESSION_REMAINS_USABLE`, aunque el registro diga
  `REAUTHENTICATION_REQUIRED`. · rojo visto: si
- **E-37** — Un `CLIENT_TIMER` o `enforcementLayer: frontend` sin evidencia de comportamiento en el
  recurso no aprueba. · rojo visto: si

### Los roles

- **E-38** — Dos entradas de la misma superficie para dos roles se evalúan cada una con su
  política, y salen las dos en `sessions[]`. · rojo visto: si
- **E-39** — La sesión ciudadana cumplida y la de administración en `FAIL` dan `FAIL`.
  · rojo visto: si
- **E-40** — Un `SESSION_ROLE_SCOPE` citado que nombra un rol sin entrada da
  `SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED`. · rojo visto: si

### Los límites

- **E-41** — `PASS` de Vu3 no es `PASS` de Vu4: con el cierre cumplido y sin vencimiento, Vu4 no
  aprueba. · rojo visto: si
- **E-42** — `PASS` de Vu4 no es `PASS` de Vu3. · rojo visto: si
- **E-43** — `PASS` de C1 no es `PASS` de Vu4. · rojo visto: si
- **E-44** — `PASS` de Vu4 no es `PASS` de C1. · rojo visto: si
- **E-45** — Ningún literal operativo del módulo exige cerrar el SSO del proveedor, y una sesión
  cumple con el SSO del proveedor activo. · rojo visto: si

### La prueba

- **E-46** — Una prueba en `PRD` no cuenta y da `SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE`. El módulo
  no ejecuta nada. · rojo visto: si
- **E-47** — Una prueba con `realUserAccount: true` no cuenta. · rojo visto: si
- **E-48** — Una prueba autorizada en QA con identidad dedicada sostiene la sesión.
  · rojo visto: si
- **E-49** — Nada con forma de credencial sale: una cookie, un id de sesión, un access o refresh
  token, un código de autorización o una contraseña en un id o en un texto se redacta, en la
  salida, en la señal y en `rules.Vu4`. "Una contraseña" es la forma que fijó E-03b del reporte de
  seguridad: la anuncian `password`, `passwd`, `pwd`, `pass`, `passphrase`, `contraseña` o `clave`.
  Enmendado el 24-09-2026 por decisión del usuario, con la regla 6 de Vu5: después de `pass` o de
  una palabra en castellano, un espacio solo no es separador.
  Un id también se redacta cuando sale como clave de un diccionario. · rojo visto: si
- **E-61** — Una sesión cuya `surfaceRef` no está en el inventario de C1 impide el `PASS` con
  `SESSION_COVERAGE_UNRESOLVED`. Un ítem que se declara `ACTIVITY_RESET_OBSERVATION` no resuelve la
  semántica aunque también declare `ACTIVITY_SEMANTICS`. · rojo visto: si
- **E-50** — Una prueba con `productionTimeoutWeakened: true` no cuenta. · rojo visto: si
- **E-51** — Sin autorización, sin identidad, en otro ambiente o con secretos registrados, da
  `SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE`. · rojo visto: si
- **E-52** — Una prueba insegura o sin objetivo no es `FAIL`, también cuando dice
  `OLD_INACTIVE_SESSION_STILL_USABLE`. · rojo visto: si

### El agregado

- **E-53** — Una sesión en `FAIL` hace `FAIL` el agregado. · rojo visto: si
- **E-54** — Una sesión sin resolver impide el `PASS`. · rojo visto: si
- **E-55** — La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales
  en NFC. · rojo visto: si
- **E-56** — La trazabilidad `ES0902 / 6.2 / 6 / Vu4` viaja en todo resultado, y la unidad de
  trabajo lleva `rules.Vu4` con aplicabilidad, resultado, sesiones y evidencia por id.
  · rojo visto: si
- **E-57** — La salida del check, pasada por `seguridad.resultado` y
  `reporte_seguridad.productores.desde_regla`, entra como `RULE_EVALUATION` de `ES0902.Vu4` al mismo
  libro. `reporte_seguridad/` no tiene ningún archivo nuevo. · rojo visto: si

### Lo que agrega esta spec

- **E-58** — Una evidencia ilegible que nombra la sesión, citada o no, impide el `PASS`, también
  cuando el `evidenceId` es una lista o un dict: nunca levanta una excepción. · rojo visto: si
- **E-59** — El bloqueo es uno solo para todas las ramas: una prueba insegura que dice
  `OLD_INACTIVE_SESSION_STILL_USABLE` impide un `NOT_APPLICABLE` igual que un `PASS`, y nunca tapa
  un `FAIL`. · rojo visto: si
- **E-60** — El registro vacío instalado valida contra el schema, y una clave de más en cualquier
  capa no valida. · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/49_es0902_vu4_vencimiento_por_inactividad.py`,
con el id en el título del test. Ninguno es sobre una corrida de un modelo, así que ninguno lleva
`· verificación: lectura`.

## Riesgos conocidos

- **El check depende de que el proyecto declare sus sesiones.** Una sesión que nadie registra y que
  C1 no inventaría no se ve.
- **`sessionId` es un nombre del registro, no un secreto**, pero un proyecto puede escribir ahí un
  id real. La regla de salida lo redacta si tiene forma de credencial. Si no la tiene, sale.
- **Exigir evidencia de comportamiento hace que casi toda sesión real quede sin resolver** hasta que
  haya una prueba. Es verdad, y el reporte de seguridad lo va a mostrar como `UNRESOLVED`.
