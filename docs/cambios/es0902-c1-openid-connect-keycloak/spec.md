# ES0902 C1 — OpenID Connect con el Keycloak de DGSEI, por superficie y con evidencia

**Estado:** verificado y cerrado · **Fecha:** 22-09-2026 · **Regla:** ES0902 6.2 §3 C1

## Qué problema resuelve

C1 es la tercera fila de ES0902 y la primera que habla del código:

> `ES0902-3-C1` — la autenticación de las aplicaciones usa OpenID Connect; en los ambientes del
> GCABA el proveedor de identidad autorizado y obligatorio es el Keycloak que administra DGSEI; la
> aplicación usa los flujos que correspondan, se registra en el servidor que corresponde y respeta
> las políticas de autenticación, autorización y protección de recursos de ASI. Las versiones nuevas
> migran del servicio OpenID anterior y delegan el ingreso de credenciales al portal nuevo.

La fila está clasificada desde la línea base de ES0902 —`CONDITIONAL` sobre `authenticationPresent`,
`dev-security` y `dev-integration`, tres policies, dos checks— y de sus cinco controles sólo existen
los dos que comparte con ES0901 D2. Los otros tres están declarados y no construidos:

```
openid-connect-authentication-required   DECLARED_POLICY_NOT_INSTALLED
dgsei-keycloak-provider-required         DECLARED_POLICY_NOT_INSTALLED
oidc-keycloak-integration                DECLARED_CHECK_NOT_INSTALLED
```

Así, hoy C1 no puede cumplir nunca, que es lo correcto, y tampoco puede decir **por qué**: no hay
nada que mire si una aplicación habla OpenID Connect, contra quién, registrada dónde y con qué flujo.

Y C1 tiene cinco formas baratas de ponerse en verde, que son las que este cambio cierra:

1. **La librería por el protocolo.** Una dependencia de OIDC, una clase de configuración del
   framework, un README o una configuración copiada de un ejemplo no prueban que la aplicación
   autentique con OpenID Connect.
2. **El hostname por la autoridad.** Un issuer que contiene `keycloak` o que "parece interno" no
   prueba que sea el Keycloak que administra DGSEI para ese ambiente.
3. **El `client_id` por el registro.** Un literal en la configuración no prueba que el cliente esté
   registrado en el servidor que corresponde.
4. **El default del framework por el flujo.** Que el framework elija un flujo no dice que sea el que
   corresponde a ese cliente.
5. **La aplicación por la superficie.** Un login que cumple no tapa a un segundo login que nadie
   miró, y una aplicación mixta —frontend ciudadano, backoffice institucional— no se resuelve entera
   de un solo lado.

Y hay una sexta, que no es barata sino peligrosa: C1 dice *"las aplicaciones"* y ES0901 v6.3 §8.2
separa la autenticación ciudadana de la institucional. Aplicar C1 a una superficie ciudadana sin más
reemplaza en silencio el camino que exige D1; declararla fuera de C1 sin más la saca del estándar de
seguridad. Las dos cosas son decidir por la normativa.

## Qué queda afuera

- **Un inventario precargado.** `authentication-surfaces.json` se instala **vacío**, igual que
  `security-control-authority.json` y `database-profiles.json`. Qué superficies de login tiene un
  proyecto, con qué proveedor, qué cliente y qué flujo, es dato del proyecto; un harness que llega
  con eso puesto contestó por el proyecto. No hay en el repositorio otro inventario equivalente con
  el que integrarlo: `project-context.schema.json` no describe superficies de autenticación.
- **Un segundo `authenticationPresent`, un segundo `authentication-delegation` o una segunda
  `credential-entry-delegation-required`.** Se reusan los de D2, que ya declaran las dos fuentes
  en el registro. Un detector de lo mismo con otro nombre es la forma más rápida de que dos reglas
  contesten distinto del mismo sistema.
- **Tocar el check de D2.** `authentication-delegation.py` no cambia: el check de C1 **consume** su
  resultado, no lo vuelve a correr ni reimplementa la detección de captura directa.
- **Un flujo universal.** Ni Authorization Code, ni PKCE, ni Client Credentials, ni Implicit, ni
  Hybrid se cablean como "el" flujo de C1: el estándar no define uno. El módulo no tiene ninguna
  constante con un nombre de flujo.
- **La URL del portal de producción.** El estándar nombra el portal de identidad de producción; el
  módulo no la escribe. Se escribiría para validarla, y validarla en DEV, QA o HML es exactamente
  inyectarla donde no corresponde. Lo único que el módulo nombra como URL es el servicio OpenID
  **anterior**, que es el que hay que detectar.
- **Los parámetros de identidad.** Tiempo de vida de token, issuer, audiencia, nombres de claims,
  mapeo de roles, scopes, algoritmos, semántica de logout, reglas de protección de recursos: nada de
  eso se escribe. Sin la política de ASI, `ASI_IDENTITY_POLICY_CONTEXT_REQUIRED`.
- **La restricción por árbol o grupo de AD como exigencia.** El estándar la recomienda. Queda como
  recomendación en la salida y no mueve ningún estado; volverla obligatoria exige una política de
  ASI que la haga obligatoria, y este harness no la tiene. El día que exista, entra con ella.
- **Autorización.** C1 autentica. Que el login funcione no dice nada de si la aplicación asigna bien
  sus roles, que es responsabilidad de la aplicación. El resultado lo dice y no lo evalúa.
- **Una reconciliación global entre C1 y D1.** Lo que `cruzada.py` ya declara a nivel de estándar
  sigue igual: sin evidencia autoritativa, `CROSS_STANDARD_INTERPRETATION_REQUIRED`. Este cambio
  agrega la resolución **por superficie**, y lo que la evidencia de un proyecto resuelve vale sólo
  para esa superficie de ese proyecto.
- **Aplicar la migración.** El check detecta el servicio anterior activo y dice que hay que migrar.
  No toca configuración.
- **Un algoritmo propio en `seguridad.py`.** C1 sale por el camino genérico: tiene checks
  deterministas que producen el `PASS`, como O2, G1 y D1 a D8. `ALGORITMOS` sigue con nueve
  entradas.
- **Un agente o una skill.** `dev-security` y `dev-integration` siguen siendo los dueños de la fila.
  `dev-openid-connect` ya existe, puede implementar e inspeccionar, y no es fuente de hechos
  normativos: lo que produce no satisface ninguna dimensión.

## Las decisiones, y por qué

### El inventario es del proyecto, se instala vacío, y cada superficie se evalúa sola

```
reglas/security-control-authority.json   del PROYECTO. Se instala VACIO
reglas/authentication-surfaces.json      del PROYECTO. Se instala VACIO
```

El check evalúa cada superficie por separado y el resultado de la aplicación sale de agregarlas:
una superficie en `FAIL` pone todo en `FAIL`; todas en `PASS` (o gobernadas por D1 con evidencia)
dan `PASS`; cualquier otra cosa queda sin resolver con el estado de la que falta. Un login que
cumple no tapa a otro que no.

El inventario vacío con autenticación presente es `AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED`. Y
también lo es un inventario que no nombra una superficie que otra fuente sí vio: un `flowId` del
resultado de D2 o un id declarado en `detectedSurfaces`. Un inventario con dos superficies con el
mismo id tampoco cubre nada.

### El schema provisto se cierra con `additionalProperties: false`

El schema llega sin `additionalProperties`. Se agrega `false` en las dos capas —el documento y la
superficie—, como se hizo con el registro de O2: una clave de más que se acepta en silencio es un
campo que alguien va a terminar leyendo como si fuera evidencia. Nada más cambia: mismos campos,
mismos requeridos, mismos enums.

### La evidencia es un catálogo aparte, y la superficie la cita por id

El schema provisto guarda la evidencia de una superficie como una lista de strings. Un string no
dice qué clase de fuente es, y sin la clase no hay forma de separar un README de un registro en el
servidor de identidad. Así que esos strings son **ids**, y la evidencia vive en el caso que se le
pasa al check, con la forma que ya usa D2:

```json
{"evidenceId": "reg-1", "sourceType": "DGSEI_IDENTITY_REGISTRATION",
 "reference": "ticket IDM-231", "establishes": ["CLIENT_REGISTRATION"],
 "scope": "tramites", "surfaceIds": ["backoffice"], "environment": "QA", "value": "tramites-bo"}
```

Una evidencia cuenta para una dimensión de una superficie cuando se dan las seis cosas: la
superficie la cita, declara esa dimensión en `establishes`, su clase es suficiente **para esa
dimensión**, trae referencia, su `scope` es el de la superficie, y —si nombra superficies o ambiente—
nombra los de ésta. `registrationEvidence` es la única lista de donde sale el registro del cliente.

### Qué clase de fuente sostiene qué

```
OIDC_PROTOCOL                  configuración real, metadata del proveedor, prueba de integración,
                               registro en DGSEI, ticket de identidad
PROVIDER_AUTHORITY             registro en DGSEI, ticket de identidad, guía oficial de identidad,
                               contrato de identidad del ambiente
CLIENT_REGISTRATION            registro en DGSEI, ticket de identidad
ENVIRONMENT_IDENTITY           contrato de identidad del ambiente, registro en DGSEI, guía oficial
FLOW_AUTHORITY                 política de ASI, guía oficial, registro en DGSEI, ticket de identidad
ASI_IDENTITY_POLICY            política de ASI
AUDIENCE                       contrato, ticket, checkpoint de identidad, decisión de arquitectura,
                               guía oficial, registro en DGSEI
CROSS_STANDARD_RECONCILIATION  checkpoint, ticket, contrato, decisión de arquitectura, guía oficial,
                               normativa del GCBA
```

Y las que no sostienen nada, nombradas para que el motivo pueda decir **por qué**: dependencia del
repositorio, clase de configuración del framework, afirmación del README, configuración de ejemplo,
forma del hostname, literal de `client_id`, default del framework, afirmación de un agente, salida
de una skill, referencia histórica.

La metadata del proveedor prueba que se habla OIDC con **ese** issuer; no prueba que ese issuer sea
el de DGSEI. Por eso está en la primera fila y no en la segunda.

### La autoridad del proveedor es por ambiente y por valor

La evidencia de proveedor tiene que nombrar el ambiente de la superficie y el mismo proveedor que la
superficie declara en `currentProvider`. Una evidencia de que *otro* issuer es el autorizado no
autoriza a éste, y una evidencia de producción no autoriza a QA. Sin el contrato de identidad del
ambiente —o con el ambiente en `UNRESOLVED`— queda `ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED`.

El flujo se trata igual: la evidencia de autoridad tiene que nombrar el mismo flujo que la
superficie declara. Sin flujo declarado, `OIDC_FLOW_CONTEXT_UNRESOLVED`; con flujo y sin autoridad
que diga que corresponde, `OIDC_FLOW_AUTHORITY_UNRESOLVED`.

### El servicio anterior se detecta por host, y sólo cuando está activo

El servicio OpenID anterior es `https://oauth2-server.apps.buenosaires.gob.ar/`. Una superficie cuyo
`currentProvider` tiene ese host está usando ese servicio **ahora**, y el inventario es el de la
versión que se está construyendo, que es por definición una versión nueva: `FAIL` con
`LEGACY_OPENID_PROVIDER_DETECTED` y `OIDC_MIGRATION_REQUIRED`, y `migration.applied: false`.

La comparación es por host y no por substring: `oauth2-server.apps.buenosaires.gob.ar.otro.com` no
es el servicio anterior. Una evidencia de clase `HISTORICAL_REFERENCE` que lo nombra —un comentario,
un documento viejo, una migración ya hecha— se informa como observación y no cambia ningún estado.

### Qué es `FAIL`, y qué no

`FAIL` tiene tres caminos y los tres son hechos declarados, no ausencias:

```
el proveedor activo de la superficie es el servicio anterior
la aplicación recibe la credencial: credentialEntryDelegated false, o D2 en FAIL para esa superficie
el protocolo declarado de la superficie no es OpenID Connect
```

Todo lo que falta tiene su estado sin resolver. El protocolo se lee como OIDC cuando dice `OIDC` o
`OPENID_CONNECT`, sin importar mayúsculas ni el separador —espacio, guion o guion bajo—; `null` o vacío no es otro protocolo, es no
saberlo.

### Lo que no tiene la forma declarada no cuenta, y toda lista sale ordenada por su contenido

Es la regla que cierra una clase de huecos y no un caso: el refutador encontró en dos pases seguidos
un campo con otra forma —`surfaceIds` como string, que se compara por substring— y una lista que
salía en el orden de la entrada —dos superficies con el mismo id—. El catálogo de evidencia no pasa
por ningún schema, así que su forma la controla el check: una evidencia a la que le falta un campo
obligatorio o que trae uno con otra forma **no cuenta en ninguna dimensión** y se informa como mal
formada. Y toda lista de la salida se ordena por su contenido completo, no sólo por su id.

### Un id de evidencia repetido no cuenta en ninguna de sus versiones

Elegir una —la primera, la última— hace depender el resultado del orden de la entrada: un README con
el mismo id que una política de ASI la tapa o queda tapado según cómo venga. Las dos quedan afuera y
el resultado lo dice en `issues`, que salen ordenadas. (Lo encontró el refutador en el primer pase:
E-50.)

### Lo que puede decir que no, y viene torcido, deja la dimensión sin resolver

La regla que cierra la clase del cuarto pase. Para la evidencia, descartar lo torcido es fallar
cerrado: la evidencia sólo suma. Pero un flujo de D2 o el resultado de una prueba pueden decir que
**no**, y descartarlos es fallar abierto: un `FAIL` con el `flowId` mal escrito desaparecía y el
`PASS` de al lado aprobaba (lo encontró el refutador en el cuarto pase: E-28). Así que un resultado
de D2 torcido en cualquier parte no se lee y deja la delegación sin resolver en todas las
superficies; una prueba de integración cuenta sólo cuando dice `CONFIRMED`; un `detectedSurfaces`
torcido deja la cobertura sin resolver; y una superficie que cita evidencia ilegible no se resuelve
por reconciliación (quinto pase: E-15 y E-43).

### D2 se consume, no se corre, y se consume entero

Si D2 trae varios flujos con el id de la superficie —los evalúa por separado—, se miran todos:
cualquier `FAIL` manda, `PASS` sólo si pasan todos. Tomar el primero dejaba que uno delegado tapara
al que captura la contraseña según el orden (lo encontró el refutador en el tercer pase: E-27). Y el
resultado de D2 pasa por la misma regla de forma que el catálogo: lo torcido no cuenta.

### D2 se consume, no se corre

El check recibe el resultado de `authentication-delegation` ya ejecutado y busca el flujo con el
mismo id que la superficie. D2 en `PASS` para ese flujo satisface la dimensión; en `FAIL`, la
superficie falla; ausente u otro estado, `PARTIAL` con motivo `CREDENTIAL_DELEGATION_UNRESOLVED`.
`credentialEntryDelegated: true` en el inventario no alcanza solo: es una declaración, y la
verificación ya existe.

El resultado del control compartido no decide el de ninguna regla. `cruzada.resultado_por_fuente`
ya lo anota por fuente con `ruleResult: None`, y el camino genérico de `seguridad.py` exige los
cinco controles de C1: D2 en `PASS` no pone a C1 en `COMPLIANT`, y el check de C1 en `PASS` no pone
a D2 en nada.

### La audiencia se resuelve por superficie, y fuera de lo institucional con evidencia se falla cerrado

```
INSTITUTIONAL con evidencia de AUDIENCE          se evalúa C1 directamente
cualquier otra cosa, con reconciliación          KEYCLOAK_OIDC   -> se evalúa C1
  autoritativa para esa superficie               ES0901_D1       -> NOT_APPLICABLE, gobernada por D1
cualquier otra cosa, sin reconciliación          CROSS_STANDARD_INTERPRETATION_REQUIRED
```

La evidencia de audiencia y la de reconciliación tienen que **nombrar la superficie** en
`surfaceIds`. Sin eso no resuelven ninguna: una evidencia que no nombra superficies valdría para
toda superficie del proyecto que la cite, y la cita la escribe quien arma el inventario — es una
declaración, no evidencia. (Lo encontró el refutador en el primer pase: E-43.)

`CITIZEN`, `MIXED`, `UNRESOLVED` e `INSTITUTIONAL` sin evidencia caen en la misma bolsa. Una
audiencia declarada sin evidencia no sabe si D1 gobierna esa superficie, y elegir por ella es
exactamente la decisión que no le toca al harness. La reconciliación vale para la superficie y el
`scope` que nombra, y para nada más: la de un proyecto no resuelve la de otro.

Los dos caminos de `FAIL` que no dependen de la audiencia —el servicio anterior activo y la captura
directa de credenciales— se miran **antes** que la audiencia: los dos están prohibidos en los dos
contextos.

### La autorización queda afuera, y dicho

Toda superficie evaluada informa `authorization.evaluated: false` y quién asigna los roles según la
superficie. Si `applicationRoleOwnership` dice algo que no es `APPLICATION`, sale como observación:
el paso 9 del paquete lo pide verificar y el criterio de `PASS` del paquete no lo incluye. La
restricción por árbol o grupo de AD sale en `recommendations` con `binding: RECOMMENDATION`.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/authentication-surfaces.json` | El inventario del proyecto, instalado vacío |
| `comun/schemas/authentication-surface.schema.json` | Su contrato, el provisto con `additionalProperties: false` en las dos capas |
| `harnesses/desarrollo/reglas/es0902-c1-governance.md` | El paquete de gobierno de C1, como vino |
| `harnesses/desarrollo/reglas/es0902-c1-cross-standard-identity-resolution.md` | La resolución cruzada por superficie, como vino |
| `harnesses/desarrollo/controles/policies/openid-connect-authentication-required.md` | La policy de OIDC |
| `harnesses/desarrollo/controles/policies/dgsei-keycloak-provider-required.md` | La policy del proveedor de DGSEI |
| `harnesses/desarrollo/controles/checks/oidc-keycloak-integration.py` | El check: diecisiete estados, por superficie, consumiendo D2 |
| `harnesses/desarrollo/reglas/control-registry.json` | Los tres controles nuevos de C1, declarados |
| `docs/seguridad-es0902.md` | C1, el inventario vacío y la frontera con D1 |
| `tests/casos/41_es0902_c1_openid_connect.py` | Los escenarios de acá abajo |

La matriz **no se toca**, `seguridad.ALGORITMOS` **tampoco**, y `authentication-delegation.py`
**tampoco**.

Y se reescriben las afirmaciones que hoy están en verde y dejan de ser ciertas: el conteo de
controles —35 → 38— en `31_d6/E-30`, `32_d5/E-36`, `33_bases/E-32`, `34_d7/E-42`, `35_d8/E-37`,
`36_p1/E-39`, `37_es0902/E-13` y `E-14`, `39_es0902_o1/E-28` y `40_es0902_o2/E-28`; los controles
de forma singular —29 → 32— en `37_es0902/E-13`; lo que `ES0902.C1` alcanza —los dos de D2 más sus
tres propios— en `37_es0902/E-14`; los checks en disco —14 → 15— en `39_es0902_o1/E-04`; y el reporte de
huecos de ES0902 —34 → 31— en `37_es0902/E-70`, `39_es0902_o1/E-28` y `40_es0902_o2/E-28`.

## Escenarios verificables

Numerados igual que el pedido de instalación: `E-nn` es `C1-nn`.

### La fila, que no se toca

- **E-01** — La clave de la fila es exactamente `ES0902.C1`, y el resultado del check la conserva.
  · rojo visto: si
- **E-02** — La única señal de C1 es `authenticationPresent`, la misma que declara ES0901 D2, y no
  aparece ninguna señal de autenticación nueva: las dos matrices siguen declarando las tres que ya
  había —`authenticationPresent` y las dos de Vu, que dicen otra cosa—. · rojo visto: si
- **E-03** — Sin la señal, C1 queda `APPLICABILITY_UNRESOLVED`, en la matriz y en el check.
  · rojo visto: si
- **E-04** — Con la señal en falso, C1 es `NOT_APPLICABLE`, en la matriz y en el check.
  · rojo visto: si
- **E-05** — Los agentes primarios siguen siendo exactamente `dev-security` y `dev-integration`.
  · rojo visto: si
- **E-06** — La fila declara exactamente tres policies, con estos ids literales:
  `openid-connect-authentication-required`, `dgsei-keycloak-provider-required` y
  `credential-entry-delegation-required`. · rojo visto: si
- **E-07** — La fila declara exactamente dos checks, `oidc-keycloak-integration` y
  `authentication-delegation`, y cero reviews. · rojo visto: si
- **E-08** — No se crea ningún agente ni ninguna skill: diez agentes, las mismas skills de
  `dev-security` y `dev-integration`, y los mismos directorios de skills. · rojo visto: si

### Lo que se reusa de D2

- **E-09** — `credential-entry-delegation-required` aparece una sola vez en el registro, con un
  solo archivo, y no hay otra policy de delegación de credenciales. · rojo visto: si
- **E-10** — `authentication-delegation` aparece una sola vez, y el check de C1 no lo vuelve a
  ejecutar: sin el resultado de D2 la dimensión de delegación queda sin resolver aunque el
  inventario diga que delega. · rojo visto: si
- **E-11** — Los dos controles compartidos declaran `ES0901.D2` y `ES0902.C1` como fuentes, y los
  tres nuevos declaran sólo `ES0902 / 6.2 / 3 / C1`. · rojo visto: si
- **E-12** — El resultado del control compartido no decide el de la regla: anotado por fuente,
  ninguna hereda `ruleResult`; con D2 en `PASS` y el check de C1 sin evidencia, C1 no cumple; y el
  check de C1 con el D2 entero en `PASS` no pasa si le falta otra dimensión. · rojo visto: si

### El inventario

- **E-13** — El inventario se instala vacío y valida contra su schema; con autenticación presente
  y el inventario vacío el resultado es `AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED`. El schema
  rechaza una clave de más en las dos capas y una audiencia o un ambiente que no son del enum.
  · rojo visto: si
- **E-14** — Varias superficies se evalúan por separado: cada una trae su propio estado y sus
  propias dimensiones, y cambiar la evidencia de una no cambia el resultado de la otra.
  · rojo visto: si
- **E-15** — Una superficie que cumple no tapa a otra sin resolver: el resultado agregado es el de
  la que falta, no `PASS`. Y una superficie que otra fuente vio —un flujo de D2 o un id en
  `detectedSurfaces`— y que el inventario no nombra deja la cobertura sin resolver, igual que un
  `detectedSurfaces` que no es una lista de ids.
  · rojo visto: si

### El protocolo, el proveedor y el registro

- **E-16** — La presencia de una librería no prueba OIDC: dependencia, clase de configuración del
  framework, README y configuración de ejemplo dan `OIDC_PROTOCOL_EVIDENCE_UNRESOLVED`, las cuatro
  probadas una por una. · rojo visto: si
- **E-17** — Configuración real, metadata del proveedor o una prueba de integración prueban el
  protocolo, cada una sola; una prueba de integración sólo prueba con `outcome: CONFIRMED`
  explícito —la que falló, la que no tuvo objetivo y la que no declara resultado no lo prueban—. Un protocolo declarado que no es OIDC es `FAIL`. · rojo visto: si
- **E-18** — Un hostname con forma de Keycloak no prueba la autoridad: la forma del hostname, la
  metadata del proveedor y una evidencia autoritativa de **otro** proveedor dan
  `KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED`. · rojo visto: si
- **E-19** — La evidencia autoritativa de DGSEI para ese proveedor y ese ambiente satisface la
  dimensión del proveedor. · rojo visto: si
- **E-20** — Un `client_id` no prueba el registro: con `clientIdReference` y sin evidencia de
  registro, o con un literal de `client_id` como evidencia, `OIDC_CLIENT_REGISTRATION_UNRESOLVED`.
  · rojo visto: si
- **E-21** — El registro en el servidor de DGSEI o el ticket de identidad, citados en
  `registrationEvidence`, satisfacen la dimensión; la misma evidencia citada sólo en `evidence` no.
  · rojo visto: si

### El flujo

- **E-22** — No hay un flujo universal: el módulo no tiene ningún literal con un nombre de flujo, y
  dos superficies con flujos distintos, cada una con su autoridad, pasan las dos.
  · rojo visto: si
- **E-23** — Un default del framework no prueba que el flujo corresponda:
  `OIDC_FLOW_AUTHORITY_UNRESOLVED`. · rojo visto: si
- **E-24** — Sin flujo declarado, `OIDC_FLOW_CONTEXT_UNRESOLVED`. · rojo visto: si
- **E-25** — Con flujo declarado y sin autoridad que diga que corresponde —o con autoridad para otro
  flujo—, `OIDC_FLOW_AUTHORITY_UNRESOLVED`. · rojo visto: si
- **E-26** — Con autoridad para el mismo flujo, la dimensión del flujo queda satisfecha y la
  superficie pasa. · rojo visto: si

### La delegación y el servicio anterior

- **E-27** — Una superficie que recibe la contraseña es `FAIL`: por el inventario, y por D2 en
  `FAIL` para ese flujo — también cuando D2 trae más de un flujo con ese id y sólo uno falla, en
  cualquier orden. · rojo visto: si
- **E-28** — La delegación sale del resultado de D2 para los flujos con el mismo id que la
  superficie, y el resultado lo informa con el control y el estado de D2; un resultado de D2 mal
  formado —aunque lo esté en un solo flujo— no hace caer el check, no se lee, deja la delegación
  sin resolver en todas las superficies y la cobertura sin resolver, y se informa. · rojo visto: si
- **E-29** — El servicio anterior como proveedor activo es `FAIL` con
  `LEGACY_OPENID_PROVIDER_DETECTED` y `OIDC_MIGRATION_REQUIRED`, también con toda la otra evidencia
  en regla. · rojo visto: si
- **E-30** — Una referencia histórica al servicio anterior no falla: sale como observación y la
  superficie pasa. Un host que sólo contiene el del servicio anterior no es el servicio anterior.
  · rojo visto: si
- **E-31** — La migración no se aplica: el resultado dice `applied: false`, el caso que entra no
  cambia, y el módulo no abre ningún archivo para escribir. · rojo visto: si

### El ambiente y la política de ASI

- **E-32** — La URL de producción no se fuerza en QA, HML ni DEV: una evidencia de proveedor de
  producción no autoriza a una superficie de QA, y el módulo no tiene ninguna URL del GCBA salvo la
  del servicio anterior. · rojo visto: si
- **E-33** — Sin contrato de identidad del ambiente, o con el ambiente en `UNRESOLVED`,
  `ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED`. · rojo visto: si
- **E-34** — Sin política de ASI de autenticación, autorización y protección de recursos,
  `ASI_IDENTITY_POLICY_CONTEXT_REQUIRED`; y una afirmación del README o de un agente no la
  reemplaza. · rojo visto: si
- **E-35** — No se inventa ningún parámetro: ninguna salida y ningún literal operativo del módulo
  nombran tiempo de vida de token, claims, scopes de OAuth, algoritmos de firma, issuer ni logout.
  `scope` y `audience` son campos del inventario provisto —el proyecto y el público de la
  superficie— y no parámetros de token. · rojo visto: si

### Autenticación no es autorización

- **E-36** — Una superficie en `PASS` informa `authorization.evaluated: false`: autenticar no prueba
  autorizar. · rojo visto: si
- **E-37** — La asignación de roles queda como responsabilidad de la aplicación: se informa, y un
  dueño que no es `APPLICATION` sale como observación sin volverse una aprobación de roles.
  · rojo visto: si
- **E-38** — El uso de grupos de AD no se exige: una superficie sin grupos de AD pasa.
  · rojo visto: si
- **E-39** — La restricción por árbol o grupo de AD sale como recomendación, con
  `binding: RECOMMENDATION`, y no cambia ningún estado. · rojo visto: si

### Ciudadano e institucional

- **E-40** — Una superficie institucional con evidencia de audiencia se evalúa directamente contra
  Keycloak/OIDC y puede pasar. · rojo visto: si
- **E-41** — Una superficie ciudadana no reemplaza a D1: sin reconciliación no pasa, no se evalúa
  Keycloak sobre ella, y el resultado no dice que D1 se cumpla. · rojo visto: si
- **E-42** — Ciudadana, mixta, sin resolver, o institucional sin evidencia, y sin reconciliación
  para esa superficie: `CROSS_STANDARD_INTERPRETATION_REQUIRED`, las cuatro. · rojo visto: si
- **E-43** — La reconciliación de un proyecto vale sólo para su `scope` y sus superficies: la misma
  evidencia no resuelve una superficie de otro proyecto ni otra superficie del mismo, y una
  reconciliación o una evidencia de audiencia que no nombra superficies —o que las nombra con otra
  forma que una lista de textos— no resuelve ninguna; y una superficie que cita un id que no
  resuelve en el catálogo —mal formado, repetido, con el propio id torcido o ausente— no se
  resuelve por reconciliación, porque ese podía ser el que la contradecía; tampoco si una
  reconciliación con autoridad trae una resolución que no es `KEYCLOAK_OIDC` ni `ES0901_D1`.
  · rojo visto: si
- **E-44** — Un frontend ciudadano y un backoffice institucional en la misma aplicación se evalúan
  por separado: el backoffice pasa, el frontend queda sin resolver, y el agregado no es `PASS`.
  · rojo visto: si
- **E-45** — Ningún checkpoint de proyecto se vuelve doctrina: el módulo no guarda nada entre
  corridas, y el mismo proyecto evaluado sin la evidencia vuelve a quedar sin resolver.
  · rojo visto: si

### Los límites

- **E-46** — `dev-openid-connect` puede ejecutar y no crea verdad normativa: la salida de una skill
  o la afirmación de un agente no satisfacen ninguna dimensión, y el módulo no lee el registro de
  agentes. · rojo visto: si
- **E-47** — `PASS` de C1 no es `PASS` de C2, ni de Vu8, ni de D1, ni de D8: ningún literal
  operativo nombra C2, Vu8 ni D8; una salida en `PASS` no nombra ninguna de las cuatro; y C2 sigue
  sin cumplir con C1 en `PASS`. D1 aparece en un solo lugar, `governedBy: ES0901.D1`, cuando la
  evidencia de un proyecto resuelve una superficie por el camino ciudadano — y eso dice quién la
  gobierna, no que D1 se cumpla. · rojo visto: si
- **E-48** — `PASS` de C1 no es aprobación oficial: ningún valor del resultado es un estado oficial
  de `evaluacion`, y ningún productor interno puede mover el estado oficial. · rojo visto: si
- **E-49** — La trazabilidad `ES0902 / 6.2 / §3 / C1` y `ES0902.C1` viaja en todo resultado del
  check, por todos los caminos, y en el bloque normativo de una unidad de trabajo del plan.
  · rojo visto: si
- **E-50** — La misma evidencia da el mismo resultado: dos corridas iguales son idénticas, y
  desordenar las superficies o la evidencia no cambia nada — tampoco con un id de evidencia repetido,
  con evidencia citada que no existe, ni con dos superficies con el mismo id; y un id repetido no
  cuenta aunque una de sus versiones esté mal formada. · rojo visto: si

## Cómo se verifica

Los cincuenta pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva `· verificación: lectura`: todo
lo que este cambio construye es determinista.

🔴 **Un caso que aprueba, roto de muchas maneras.** Como en O2: el archivo de tests arma UNA
superficie institucional que pasa y la rompe dimensión por dimensión. Un archivo que sólo arma casos
que fallan pasa con un check que nunca aprueba.

🔴 Los ids y los estados van **clavados por literal** en el test, no recorridos desde las constantes
del módulo.

🔴 E-22, E-32, E-35, E-46 y E-47 dicen **literal operativo**: la prosa del módulo nombra flujos,
C2 y `dev-openid-connect` a propósito, para declarar la frontera.

## Riesgos conocidos

- **La evidencia no la produce nadie todavía.** El inventario y el catálogo llegan declarados, igual
  que en O2 y en D1 a D8. Mientras el inventario esté vacío, toda corrida real con autenticación da
  `AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED`.
- **`reglas/` se sobrescribe en cada `-Update`.** `authentication-surfaces.json` hereda la misma
  deuda que `database-profiles.json` y `security-control-authority.json`, ya anotada en
  `Pendientes/`.
- **La mayoría de las superficies ciudadanas va a quedar sin resolver.** Es lo que el paquete pide
  mientras C1 y D1 no tengan una reconciliación autoritativa, y es lo primero que alguien va a
  querer aflojar declarando `INSTITUTIONAL` sin evidencia — que tampoco alcanza.
- **El catálogo de clases de fuente es del harness.** Qué clase sostiene qué dimensión es una
  decisión de este cambio, no del estándar. Está escrita en una tabla y en la spec para que se
  pueda discutir; no se deduce.
