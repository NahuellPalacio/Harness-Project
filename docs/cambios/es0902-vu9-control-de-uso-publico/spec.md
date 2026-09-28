# ES0902 Vu9 — control de uso de lo público sin autenticación

**Estado:** verificado y cerrado · **Fecha:** 26-09-2026 · **Regla:** ES0902 6.2 §6 Vu9

## Qué problema resuelve

> *"Las aplicaciones que expongan funcionalidades accesibles sin autenticación a través de interfaces
> públicas (web o API), deberán contemplar mecanismos de control de uso que mitiguen riesgos por
> consumo excesivo o automatizado de recursos y garanticen la estabilidad del servicio."*
> (ES0902 v6.2, §6)

La fila está en la matriz: `CONDITIONAL` con la señal `unauthenticatedPublicInterfacePresent`, los
agentes `dev-security`, `dev-backend` y `dev-devops`, una policy, un check y cero reviews. Los dos
controles, `public-interface-abuse-control-required` y `public-interface-abuse-protection`, están
declarados y no construidos. El dominio `sensitive-data-public-interfaces` del reporte ya nombra Vu9
y no tiene de dónde sacar un resultado.

Vu9 tiene siete formas baratas de ponerse en verde o en rojo, y este cambio las cierra:

1. **Un DNS público o un asset estático por "hay funcionalidad pública".** Ninguno de los dos consume
   recursos gobernados.
2. **"Es de solo lectura" por "está afuera".** Una búsqueda pública también se abusa.
3. **Un mecanismo inventado.** Vu9 no pide rate limiting, CAPTCHA, WAF, gateway ni un número.
4. **La configuración por el camino.** Una política en el gateway no protege una ruta que no pasa por
   el gateway, ni un origen alcanzable por detrás.
5. **El botón deshabilitado por el control.** Lo que corre en el navegador no frena a quien llama la
   API directo.
6. **Un test de performance en verde por Vu9 en verde.** Dice algo de estabilidad, nada del control.
7. **La evidencia de DEV por la de PRD.**

Y la peligrosa: probarlo con carga sin límite, contra producción o con datos reales.

## Qué queda afuera

- **Un mecanismo, un producto, un umbral, una cuota, un límite de concurrencia o un SLA.** Vu9 mira
  el resultado del control y su camino, no cuál es. El módulo no tiene ninguna lista de mecanismos.
- **Ejecutar pruebas o generar tráfico.** El check lee la evidencia de una prueba ya hecha y decide si
  era segura. No importa nada que pueda abrir una conexión o lanzar un proceso.
- **Vu1, Vu10 y performance.** Pueden compartir evidencia y cada uno conserva su resultado. El check de
  Vu9 no lee ni escribe el de ninguna otra regla.
- **La severidad.** Un control faltante es una falla de cumplimiento, sea grave o leve.
- **Un agente, una skill, una review, un algoritmo nuevo en `seguridad.py`, un pipeline de reporte,
  un dominio o un libro nuevos.** `ALGORITMOS` sigue en diez, y Vu9 entra al libro de siempre por el
  dominio `sensitive-data-public-interfaces`, que ya lo nombra.
- **La forma vieja de `_vu9` (`abuseControls`).** La línea base la verificó (E-50 y E-51 de
  `es0902-linea-base-de-seguridad`) y sigue igual: quien la use sigue teniendo la misma respuesta. El paquete recomienda
  un grupo "Public Exposure & Abuse Protection": ese es el dominio que existe, y renombrarlo toca a Vu2
  y Vu7.
- **Tocar `controles/lib/evidencia.py`, `refutacion.py` o el check de Vu1.** Vu9 los reusa sin
  cambiarlos. El pendiente del token con prefijo de proveedor sigue abierto.

## Las decisiones, y por qué

### La señal sale de evidencia, y apagarla cuesta más que encenderla

`unauthenticatedPublicInterfacePresent` se deriva de las evidencias que establecen
`PUBLIC_UNAUTHENTICATED_FUNCTIONALITY`.

- **`TRUE`**: una evidencia legible dice `PRESENT`, de cualquier clase salvo las débiles
  (`README_STATEMENT`, `AGENT_STATEMENT`, `SKILL_OUTPUT`, `NAMING_CONVENTION`) y las que no hablan de
  funcionalidad (`PUBLIC_DNS_RECORD`, `STATIC_ASSET_EXPOSURE`, `HEALTH_ENDPOINT`). Que la evidencia
  diga `readOnly: true` no cambia nada: el módulo no lee ese campo.
- **`FALSE`**: una evidencia autoritativa legible dice `ABSENT`, ninguna dice `PRESENT`, el registro
  no tiene superficies y no hay nada ilegible sobre `PUBLIC_UNAUTHENTICATED_FUNCTIONALITY`.
- **`UNRESOLVED`**: todo lo demás, incluido el vacío.

Una señal externa se combina como en Vu8.

### El inventario tiene que estar entero

Con la señal en `TRUE`, el `PASS` exige una evidencia legible `PUBLIC_SURFACE_INVENTORY: COMPLETE`
de una clase que puede decirlo —las autoritativas del proyecto, `ROUTE_INVENTORY`,
`API_SPECIFICATION` o `NETWORK_TOPOLOGY`— que nombra en `surfaces` la superficie pública entera.
Cada superficie que nombra tiene que estar en el registro, y cada superficie del registro en alcance
tiene que estar en el inventario. Sin inventario entero, con uno `INCOMPLETE`, con dos que no
coinciden, con una superficie nombrada sin entrada o con una en alcance que el inventario no nombra,
da `PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`.

Las autoritativas del proyecto son `SECURITY_DOCUMENTATION`, `ARCHITECTURE_DOCUMENTATION`,
`PROJECT_REQUIREMENT`, `PROJECT_CONTRACT`, `ASSESSMENT_FINDING` y `OTHER_AUTHORITATIVE_EVIDENCE`.

### Una superficie entra sola; salir cuesta evidencia

Una superficie del registro con `publiclyReachable: YES` y `authenticationRequired: NO` está en
alcance, sin más: declararla así es pedir más control, no menos. Una superficie que el registro saca
—`publiclyReachable: NO` o `authenticationRequired: YES`— sale solo si cita una evidencia legible que
lo establece (`PUBLIC_REACHABILITY: NO` o `AUTHENTICATION_REQUIRED: YES`) de una clase autoritativa, de
topología o de configuración del servidor, y ninguna evidencia legible de esas clases dice lo
contrario. Si no, y también con `UNRESOLVED` en cualquiera de los dos campos, da
`PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`.

### El registro, cerrado

`public-interface-abuse-protection.json` se instala vacío, con la forma del paquete. El schema es el
del paquete, cerrado con `additionalProperties: false` en todas las capas: no hay campo para un
payload, un script, un token ni un dato personal. Las evidencias viven en el catálogo del caso,
también cerrado. El catálogo tiene `severity` y `readOnly`, que el módulo no lee nunca.

El registro sí tiene dos campos de texto libre, `operationRef` y `controlType`, y desde la primera
refutación **no salen**: el resultado no los necesita, y en texto libre puede ir un dato personal o un
script que la regla de salida compartida no reconoce.

### Nombrar es por id

Un item habla de un control si lo lista en `controls`, y de la superficie entera si no lista controles
y lista la superficie en `surfaces`. Un item que nombra otra superficie habla de otra cosa. **Citarlo
no alcanza** (refutador, pase 1): un item citado que no nombra ni el control ni la superficie no
sostiene nada. Que el control existe y sus dimensiones los dice un item que lista el control en
`controls`: uno que lista solo la superficie habla de la superficie, no del control (pase 2).

### Las clases

- **Del servidor o la infraestructura**: `APPLICATION_CODE`, `APPLICATION_CONFIGURATION`,
  `GATEWAY_CONFIGURATION`, `REVERSE_PROXY_CONFIGURATION`, `WAF_CONFIGURATION`,
  `INGRESS_CONFIGURATION` (router e ingress de OpenShift), `UNIT_TEST`, `INTEGRATION_TEST`,
  `AUTHORIZED_QA_BOUNDED_TEST` y las autoritativas.
- **Del camino**: `NETWORK_TOPOLOGY` más todas las del servidor salvo `UNIT_TEST`.
- **De estabilidad**: las del servidor, más `PERFORMANCE_TEST_REPORT`, `CAPACITY_CONFIGURATION` y
  `OBSERVABILITY_RECORD`.
- **Del cliente**: `CLIENT_SIDE_CONTROL`, `FRONTEND_CODE` y `UI_TEST`. Nunca sostienen nada de Vu9.

`PERFORMANCE_TEST_REPORT`, `CAPACITY_CONFIGURATION` y `OBSERVABILITY_RECORD` solo dicen
estabilidad: no establecen un control, un camino, ni una mitigación.

### El control existe si el servidor lo dice

Un control del registro cuenta si cita una evidencia legible `USE_CONTROL: PRESENT` de una clase del
servidor o la infraestructura que lo nombra. Un `USE_CONTROL: ABSENT` que nombra el control dice que
ese control no existe: el control no cuenta y la superficie queda sin resolver, no en falta. Una del cliente queda en la salida como `clientSide` y
no sostiene nada: un botón, un temporizador o un contador en el navegador no son un control.

`controlType` es texto libre y el módulo no lo lee para decidir. `enforcementLayer` tiene que ser una
capa resuelta; `UNRESOLVED` deja el control sin sostener.

### El camino

Un control sostenido cubre la superficie si además cita una evidencia legible `PATH_BINDING: BOUND`
de una clase del camino que lista la superficie en `surfaces`. Un item de camino que nombra solo el
control no habla de ninguna superficie. Sin eso, la configuración sola no alcanza.

| Evidencia `PATH_BINDING`, legible, de una clase del camino | Resultado |
|-|-|
| `BOUND` citada, y el registro dice `BOUND` | el control cubre la superficie |
| `BYPASS_PRESENT` citada | `ABUSE_CONTROL_BYPASS_PRESENT`, falla |
| `NOT_BOUND` citada | el control no cubre la superficie |
| `BOUND` y `NOT_BOUND` o `BYPASS_PRESENT` a la vez | sin resolver |

Un salteo de cualquier control declarado de la superficie la hace fallar: un control que se puede
saltear no cumple, aunque otro esté en el camino.

### El control falta

`ABUSE_CONTROL_MISSING` es una falla establecida en tres casos, y solo en esos:
- la superficie en alcance declara `controls: []`;
- una evidencia legible y citada, de una clase del servidor o la infraestructura, dice
  `USE_CONTROL: ABSENT` sobre la superficie, sin nombrar un control;
- todos los controles declarados tienen un `PATH_BINDING: NOT_BOUND` citado y legible.

Todo lo demás sin un control que cubra la superficie queda en `PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED`,
incluido el control que solo el cliente sostiene. Declarar `ABUSE_CONTROL_MISSING` en `result` sin la
evidencia no es una falla.

📌 Esto lee el paso 5 del check del paquete —"si no existe enforcement del servidor, `ABUSE_CONTROL_MISSING`"—
como una inexistencia **establecida**. Que el servidor no diga nada no establece que no haya control:
queda sin resolver. VU9-21 y VU9-22 solo piden que no haya `PASS`.

### Las tres dimensiones

`EXCESSIVE_CONSUMPTION_MITIGATION` y `AUTOMATED_CONSUMPTION_MITIGATION` las dicen las clases del
servidor o la infraestructura; `SERVICE_STABILITY`, las de estabilidad. Una dimensión de la
superficie está evidenciada si algún control que la cubre la declara `EVIDENCED` y cita una evidencia
legible de su clase con ese valor que lo nombra, y ninguna evidencia legible de su clase sobre ese
control dice `NOT_EVIDENCED`. Si no, da el estado abierto de la dimensión:
`EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED`, `AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED` o
`SERVICE_STABILITY_EVIDENCE_UNRESOLVED`. Ninguna es falla.

Una sola evidencia puede establecer las dos mitigaciones. Un control compartido —el mismo `controlId`
en varias superficies— se sostiene con la misma evidencia, que nombra el control sin repetirse; el
camino, en cambio, se prueba por superficie.

### El ambiente

El registro declara `environment`, el ambiente que se evalúa. Una evidencia con `environment` distinto
no sostiene nada para ese registro: lo de DEV no prueba QA, HML ni PRD. Una evidencia sin ambiente
—código, configuración del repositorio— vale para cualquiera. Una evidencia de otro ambiente que dice
una falla (regla 8) no hace `FAIL`, pero si se la cita o nombra la superficie impide el `PASS`. La
señal no mira el ambiente: habla de la aplicación. Las huellas de despliegue de la
evidencia usada (`routeVersion`, `configFingerprint`, `buildId`, `imageDigest`) salen en la salida del
control.

### La prueba es segura o no cuenta

Una `AUTHORIZED_QA_BOUNDED_TEST` cuenta si cumple todo esto:
- `authorized: true`;
- `environment` es `DEV`, `QA`, `HML` u `OTHER`;
- `bounded: true` y `stopConditions: true`;
- `syntheticData: true`;
- `destructive` no es `true`.

Si no, da `PUBLIC_ABUSE_TEST_UNSAFE`. Con `outcome: UNAVAILABLE`, da `TEST_TARGET_UNAVAILABLE`.
Ninguna de las dos es `FAIL` ni `PASS`. Una prueba no es obligatoria: la configuración y el camino
alcanzan.

### La superficie: su estado

1. El alcance: dentro, fuera sostenido, o sin resolver.
2. El control y el camino: falta, salteo, cubre o sin resolver.
3. Las tres dimensiones, en ese orden.
4. Lo declarado. `PASS` exige `result: PROTECTED` y `verificationMode` distinto de `NOT_VERIFIED`.

Si lo que falta en el paso 2 o en una dimensión es justo lo que decía una prueba citada que no se pudo
leer —insegura o sin objetivo— sobre eso mismo, el paso dice
`PUBLIC_ABUSE_TEST_UNSAFE` o `TEST_TARGET_UNAVAILABLE` en lugar de su sin resolver. No es un bloqueo:
una prueba que habla de otra cosa no cambia lo que falta en ese paso (refutador, pase 1). En el paso 2,
lo que falta es, control por control, la existencia (`USE_CONTROL`) si no consta, y si consta, el
camino (`PATH_BINDING`). Una capa sin resolver no la arregla ninguna prueba (pase 2).

Una falla establecida en cualquier paso le gana a un sin resolver anterior; entre fallas, gana
`ABUSE_CONTROL_BYPASS_PRESENT` y después `ABUSE_CONTROL_MISSING`. Sin fallas, gana el primer sin
resolver de este orden: `PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`,
`PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED`, `EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED`,
`AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED`, `SERVICE_STABILITY_EVIDENCE_UNRESOLVED`,
`PUBLIC_ABUSE_TEST_UNSAFE`, `TEST_TARGET_UNAVAILABLE`. Manda esta lista, no el orden de los pasos: un
paso 4 sin resolver le gana a una dimensión sin resolver del paso 3 (pase 2). Una superficie fuera de alcance sostenida es
`NOT_APPLICABLE` y no pesa en el agregado.

🔴 Una superficie con el alcance sin resolver no puede fallar: sin saber si es pública y sin
autenticación, no se sabe si necesita un control. Queda en
`PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`, diga lo que diga su evidencia de control. Con la
señal en `TRUE` y ninguna superficie en alcance, el agregado da ese mismo estado.

### Las reglas que ya costaron pases, desde el primer día

Las de Vu8, con la 2 y la 8 unificadas desde la primera refutación, que encontró tres respuestas
distintas según la forma de lo ilegible:
1. Lo que dice "no" pasa por la misma compuerta que lo que dice "sí".
2. **Lo ilegible —mal formado, repetido, con `outcome` fuera de lo legible, o una prueba insegura o sin
   objetivo— pesa si se lo cita o si toca la superficie o uno de sus controles, diga lo que diga.** Toca
   si lista la superficie en `surfaces` o uno de sus controles en `controls`, liste lo que liste además:
   nombrar otra superficie no lo saca si nombra un control compartido (pase 2). Si
   pesa, impide el `PASS`; nunca hace `FAIL`. Un id que no es texto es ilegible, nunca una excepción.
3. La falla establecida gana siempre, diga lo que diga el registro. Una no citada deja la superficie
   sin resolver.
4. Todo id se normaliza a NFC antes de comparar y antes de contar repetidos.
5. Hay un solo paso de bloqueo. Nunca tapa un `FAIL` y nunca reemplaza un sin resolver anterior.
6. Hay una sola regla de salida de secretos, la de `controles/lib/evidencia.py`, sin tocarla.
7. Un item con `outcome` fuera de lo legible es ilegible, prueba incluida.
8. **Lo legible no citado pesa solo si dice una falla.** Dice una falla solo un item del servidor, la
   infraestructura o el camino que dice `USE_CONTROL: ABSENT`, `PATH_BINDING: BYPASS_PRESENT` o
   `PATH_BINDING: NOT_BOUND`. Pesa, y deja sin resolver, nunca en `FAIL`. El cliente, una de
   estabilidad y un `NOT_EVIDENCED` nunca dicen una falla.

### `_vu9` le cede la palabra al check

`seguridad.py` ya tenía un algoritmo para Vu9, de la línea base: sin una lista `abuseControls` con un
mecanismo y su evidencia, la regla da `NON_COMPLIANT`. Con el check instalado eso convertía todo sin
resolver del check en una falla, porque la salida del check no trae esa lista. Se consideró hacer que
`para_seguridad` inventara la lista, y se descartó: declarar un mecanismo cuando el check no lo
sostiene es mentir en la evidencia. Se consideró borrar la rama, y se descartó: la línea base la
verificó y la usan sus tests.

Queda así: si la evidencia trae el resultado de un check de la fila y no trae `abuseControls`, `_vu9`
va por el genérico y manda el check. Con `abuseControls`, todo sigue como estaba.

### El agregado, la unidad, el reporte y la refutación atómica

- **Una falla** en cualquier superficie hace fallar el agregado, con el primer estado de este orden:
  `ABUSE_CONTROL_BYPASS_PRESENT`, `ABUSE_CONTROL_MISSING`.
- **Un sin resolver material** impide el `PASS`.
- **El registro vacío con la señal en `TRUE`** da `PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`.
- **La unidad** lleva `rules.Vu9` con `applicability`, `result`, `surfaces` y `evidence`.
- **El reporte**: la salida pasada por `seguridad.resultado("Vu9", …)` y por `desde_regla` entra al
  libro de siempre, en el dominio `sensitive-data-public-interfaces`.
- **La refutación atómica**: `para_refutacion` traduce la salida a una entrada de `checks.json` atada
  a la huella y la revisión de la unidad. Un `PASS` o un `FAIL` cierran la unidad sin refutador. Un
  sin resolver la deja en una sola unidad pendiente, con el alcance declarado y nada más.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/public-interface-abuse-protection.json` | El registro, instalado vacío |
| `comun/schemas/public-interface-abuse-protection.schema.json` | Su contrato: el del paquete, cerrado en todas las capas |
| `harnesses/desarrollo/reglas/es0902-vu9-governance.md`, `es0902-vu9-unauthenticated-public-interface-present-signal.md` y `es0902-vu9-public-interface-abuse-protection-check.md` | Gobierno, señal y procedimiento, como vinieron |
| `harnesses/desarrollo/controles/policies/public-interface-abuse-control-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/public-interface-abuse-protection.py` | El check, la señal y las dos traducciones |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu9` en la unidad |
| `harnesses/desarrollo/bin/orquestacion/seguridad.py` | `_vu9` le cede la palabra al check |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles |
| `docs/seguridad-es0902.md` | Vu9 |
| `tests/casos/58_es0902_vu9_control_de_uso_publico.py` | Los escenarios |

## Escenarios verificables

El paquete trae la lista `VU9-01` a `VU9-62`. Cada `E-nn` es el `VU9-nn` con el mismo número.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu9`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `unauthenticatedPublicInterfacePresent`, `public-interface-abuse-control-required` y
  `public-interface-abuse-protection` están exactos en la matriz, el registro de controles y el
  módulo, y la fila declara `dev-security`, `dev-backend` y `dev-devops`, en ese orden.
  · rojo visto: si
- **E-03** — No hay ningún agente, skill, review ni señal nuevos, `ALGORITMOS` sigue en diez, y con
  el resultado del check y sin `abuseControls` Vu9 da lo que da el genérico. · rojo visto: si

### La señal

- **E-04** — Una operación de API pública sin autenticación, en evidencia legible, enciende la señal.
  · rojo visto: si
- **E-05** — Una funcionalidad web pública sin autenticación la enciende. · rojo visto: si
- **E-06** — Un `STATIC_ASSET_EXPOSURE` que dice `PRESENT`, solo, no la enciende. · rojo visto: si
- **E-07** — Un `PUBLIC_DNS_RECORD` que dice `PRESENT`, solo, no la enciende. · rojo visto: si
- **E-08** — Una funcionalidad con `readOnly: true` la enciende igual, y una superficie de solo
  lectura sigue en alcance. · rojo visto: si
- **E-09** — Un inventario `INCOMPLETE`, o ninguno, deja la superficie sin resolver
  (`PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`); el vacío, una evidencia débil, o un
  `ABSENT` con algo ilegible o con una superficie registrada dan `APPLICABILITY_UNRESOLVED`; una
  ausencia autoritativa sola da `NOT_APPLICABLE`. · rojo visto: si

### La cobertura

- **E-10** — Una superficie en alcance con `controls: []` da `ABUSE_CONTROL_MISSING` y falla.
  · rojo visto: si
- **E-11** — Una superficie protegida no tapa otra sin control: el agregado falla.
  · rojo visto: si
- **E-12** — Una superficie que el inventario entero nombra y el registro no tiene impide el `PASS`,
  una en alcance que el inventario no nombra también, y una superficie sacada del alcance sin evidencia
  también. · rojo visto: si

### Dónde vive el control

- **E-13** — Un control en la aplicación, sostenido y en el camino, llega a `PASS`. · rojo visto: si
- **E-14** — Un control en el gateway llega a `PASS` si el camino lo prueba. · rojo visto: si
- **E-15** — Un control en el WAF llega a `PASS` si el camino lo prueba. · rojo visto: si
- **E-16** — Un control en el router de OpenShift llega a `PASS` si el camino lo prueba.
  · rojo visto: si
- **E-17** — Un control que no es rate limiting llega a `PASS`: el módulo no nombra ningún mecanismo.
  · rojo visto: si
- **E-18** — Sin CAPTCHA se llega a `PASS`. · rojo visto: si
- **E-19** — Sin WAF se llega a `PASS`. · rojo visto: si
- **E-20** — El módulo no tiene ningún número de pedidos, cuota ni concurrencia, y el mismo control
  con otro límite declarado da el mismo resultado. · rojo visto: si

### El camino y el cliente

- **E-21** — Un botón deshabilitado, solo, no es un control: no hay `PASS`. · rojo visto: si
- **E-22** — Un temporizador en JavaScript, solo, tampoco. · rojo visto: si
- **E-23** — Un origen alcanzable por detrás del control da `ABUSE_CONTROL_BYPASS_PRESENT` y falla.
  · rojo visto: si
- **E-24** — Un control configurado sin evidencia de camino no llega a `PASS`, y uno que el camino no
  atraviesa no cubre la superficie. · rojo visto: si
- **E-25** — Un item citado que no nombra el control ni la superficie no sostiene nada, un camino que
  no lista la superficie no la cubre, y una política compartida del gateway cubre dos superficies con
  una sola evidencia del control y el camino de cada una. · rojo visto: si

### El consumo excesivo y el automatizado

- **E-26** — Sin evidencia de mitigación del consumo excesivo no hay `PASS`. · rojo visto: si
- **E-27** — Una mitigación del consumo excesivo contradicha da
  `EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED` y no falla. · rojo visto: si
- **E-28** — Sin evidencia de mitigación del consumo automatizado no hay `PASS`. · rojo visto: si
- **E-29** — Una mitigación del consumo automatizado sin sostener da
  `AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED` y no falla. · rojo visto: si
- **E-30** — Una cuota del gateway, sin CAPTCHA, sostiene la mitigación automatizada.
  · rojo visto: si
- **E-31** — Una sola evidencia sostiene las dos mitigaciones. · rojo visto: si

### La estabilidad

- **E-32** — Sin evidencia de estabilidad da `SERVICE_STABILITY_EVIDENCE_UNRESOLVED`.
  · rojo visto: si
- **E-33** — El módulo no tiene ningún SLA ni porcentaje. · rojo visto: si
- **E-34** — Una configuración acotada sostiene la estabilidad. · rojo visto: si
- **E-35** — Una prueba de carga acotada en QA sostiene la estabilidad. · rojo visto: si
- **E-36** — Un `PERFORMANCE_TEST_REPORT` en verde, solo, no cierra Vu9. · rojo visto: si
- **E-37** — El `PASS` de Vu9 no cambia el resultado de ninguna otra regla de ES0902 y la salida no
  dice nada de performance. · rojo visto: si

### El ambiente

- **E-38** — La evidencia de DEV no sostiene un registro de QA, HML ni PRD. · rojo visto: si
- **E-39** — Las huellas de despliegue de la evidencia usada salen en la salida. · rojo visto: si
- **E-40** — Se llega a `PASS` con evidencia estática sola, sin ninguna prueba en runtime.
  · rojo visto: si

### La prueba

- **E-41** — Una prueba autorizada, acotada, en QA, con datos sintéticos, sostiene un `PASS`.
  · rojo visto: si
- **E-42** — El módulo no genera ni ejecuta pedidos: no importa nada que abra una conexión o un
  proceso, y no abre nada para escribir. · rojo visto: si
- **E-43** — Una prueba en `PRD` da `PUBLIC_ABUSE_TEST_UNSAFE`. · rojo visto: si
- **E-44** — Una prueba sin datos sintéticos da `PUBLIC_ABUSE_TEST_UNSAFE`. · rojo visto: si
- **E-45** — Una prueba no autorizada, no acotada, sin condiciones de corte, destructiva o sin ambiente
  da `PUBLIC_ABUSE_TEST_UNSAFE`, y dice por qué. · rojo visto: si
- **E-46** — Una prueba insegura o sin objetivo no es `PASS` ni `FAIL`, citada o no, diga lo que diga;
  lo ilegible que toca la superficie o un control suyo impide el `PASS` en todas sus formas; y una
  prueba que habla de otra dimensión no cambia lo que falta.
  · rojo visto: si

### Los límites

- **E-47** — El `PASS` de Vu1 no pone en `PASS` a Vu9. · rojo visto: si
- **E-48** — El `PASS` de Vu9 no pone en `PASS` a Vu1. · rojo visto: si
- **E-49** — La review de Vu10 en `PASS` no pone en `PASS` a Vu9. · rojo visto: si
- **E-50** — El `PASS` de Vu9 no pone en `PASS` a Vu10. · rojo visto: si

### La refutación atómica

- **E-51** — Un plan con Vu9 aplicable compila a una sola unidad de `ES0902.Vu9` por alcance, con una
  skill de `dev-security`, `dev-backend` o `dev-devops`, que declara el check. · rojo visto: si
- **E-52** — Un `PASS` o un `FAIL` del check, traducido por `para_refutacion`, cierra la unidad sin
  refutador. · rojo visto: si
- **E-53** — Un sin resolver deja una sola unidad pendiente con el alcance declarado, y un veredicto de
  otra regla o con evidencia fuera del alcance se rechaza. · rojo visto: si
- **E-54** — Un veredicto guardado no se reusa cuando cambia la huella de la evidencia del alcance.
  · rojo visto: si
- **E-55** — Una unidad sin alcance declarado queda bloqueada y no se refuta el repositorio entero.
  · rojo visto: si

### La salida y el agregado

- **E-56** — La salida pasada por `seguridad.resultado` y `desde_regla` entra como `RULE_EVALUATION`
  de `ES0902.Vu9` al mismo libro, Vu9 está en `sensitive-data-public-interfaces`, y
  `reporte_seguridad/` no tiene ningún archivo nuevo. · rojo visto: si
- **E-57** — `operationRef` y `controlType` no salen, así que un dato personal escrito ahí tampoco, y
  lo que la regla de salida compartida reconoce como credencial no sale en la salida, la
  unidad ni el libro, y el schema no admite un campo de más. · rojo visto: si
- **E-58** — Un item del catálogo con un script o un payload queda mal formado y no sostiene nada, y
  el registro no tiene dónde guardarlo. · rojo visto: si
- **E-59** — Un control faltante o salteado en una superficie hace fallar el agregado aunque las demás
  cumplan. · rojo visto: si
- **E-60** — Una dimensión sin resolver en una superficie impide el `PASS` aunque las demás cumplan.
  · rojo visto: si
- **E-61** — La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en
  NFC, y un id que no es texto no levanta. · rojo visto: si
- **E-62** — La trazabilidad `ES0902 / 6.2 / 6 / Vu9` viaja en todo resultado y en `rules.Vu9`, y el
  `PASS` de Vu9 no mueve el estado oficial de seguridad. · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/58_es0902_vu9_control_de_uso_publico.py`, con
el id en el título. Ninguno lleva `· verificación: lectura`: E-51 a E-55 prueban el compilador, la
caché y el registro de veredictos, no una corrida del refutador.

## Riesgos conocidos

- **Casi todo proyecto real va a quedar sin resolver.** Pocos tienen un inventario entero de lo
  público y evidencia del camino por superficie.
- **El camino lo dice una evidencia, no el tráfico.** Una topología desactualizada que dice `BOUND`
  sostiene el `PASS`. Solo una prueba mira lo que pasa de verdad.
- **Un salteo de un control tumba la superficie aunque otro control de la aplicación siga en el
  camino.** Es conservador a propósito: la policy dice que lo salteable no cumple.
- **Un token con prefijo de proveedor en un id o en otro campo libre sale tal cual** hasta que se
  amplíe `controles/lib/evidencia.py`.
