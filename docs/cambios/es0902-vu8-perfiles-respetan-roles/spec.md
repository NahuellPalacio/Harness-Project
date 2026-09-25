# ES0902 Vu8 — los perfiles respetan los roles asignados

**Estado:** verificado y cerrado · **Fecha:** 25-09-2026 · **Regla:** ES0902 6.2 §6 Vu8

## Qué problema resuelve

> *"Los perfiles de usuarios armados en las aplicaciones deben respetar los roles asignados."*
> (ES0902 v6.2, §6, pág. 7)

La fila está en la matriz: `CONDITIONAL` con la señal `applicationRolesPresent`, los agentes
`dev-security` y `dev-backend`, una policy, un check y cero reviews. Los dos controles,
`user-profile-role-enforcement-required` y `role-profile-consistency`, están declarados y no
construidos. El dominio `authorization-roles` del reporte de seguridad ya existe y no tiene de dónde
sacar un resultado.

Vu8 tiene siete formas baratas de ponerse en verde o en rojo, y este cambio las cierra:

1. **El login por la autorización.** Que el usuario entre por Keycloak es C1; que el token traiga un
   claim de rol no prueba que la aplicación lo haga cumplir.
2. **El botón por el servidor.** Esconder un botón de administración no prueba que la API rechace la
   operación.
3. **El nombre del rol por sus permisos.** Que un rol se llame `admin` no dice qué puede hacer.
4. **"No hay enum `Role`" por "no hay roles".** Los roles pueden venir de la base, de grupos, de
   claims o de un conjunto de permisos.
5. **Una semántica de varios roles inventada**: el más alto gana, se suman o se intersecan.
6. **Una propagación inmediata inventada.** Un rol revocado puede seguir vigente hasta el próximo
   refresco, si eso es lo que la aplicación documenta.
7. **La validación de entrada por la autorización.** Eso es Vu5.

Y la peligrosa: probarlo con una cuenta privilegiada real, o dejar un token en la evidencia.

## Qué queda afuera

- **Un framework de RBAC, una anotación, un schema de base, un nombre de claim o una jerarquía de
  roles.** Vu8 mira la consistencia, no la implementación.
- **Una semántica de varios roles o un tiempo de propagación.** Salen de la evidencia del proyecto,
  o quedan sin resolver.
- **El mínimo privilegio más allá del modelo autoritativo.** Si el modelo del proyecto le da mucho a
  un rol, Vu8 no lo discute: compara contra ese modelo.
- **C1 y Vu5.** Pueden compartir evidencia y cada uno conserva su resultado. El check de Vu8 no lee
  ni escribe el de ninguna otra regla.
- **El ambiente de la evidencia estática.** Vu8 mira el modelo de autorización. Solo una prueba en
  runtime tiene que ser de un ambiente de prueba.
- **Ejecutar pruebas.** El check lee la evidencia de una prueba ya hecha y decide si era segura.
- **La severidad.** Una falla de Vu8 es una falla de cumplimiento, sea grave o leve.
- **Un agente, una skill, una review, un algoritmo en `seguridad.py`, un pipeline de reporte o un
  libro nuevo.** Vu8 va por `_generico`, `ALGORITMOS` sigue en diez y entra al libro de siempre.
- **Tocar `controles/lib/evidencia.py`, `refutacion.py` o los checks de C1 y Vu5.** Vu8 los reusa
  sin cambiarlos.

## Las decisiones, y por qué

### La señal sale de evidencia, y apagarla cuesta más que encenderla

`applicationRolesPresent` se deriva de las evidencias que establecen `APPLICATION_ROLES`.

- **`TRUE`**: una evidencia legible dice `PRESENT`, de cualquier clase salvo las débiles
  (`README_STATEMENT`, `AGENT_STATEMENT`, `SKILL_OUTPUT`, `NAMING_CONVENTION`). Una tabla de roles,
  un claim consumido por el backend o un middleware alcanzan.
- **`FALSE`**: una evidencia autoritativa legible dice `ABSENT`, ninguna dice `PRESENT`, el registro
  no tiene superficies y no hay nada ilegible sobre `APPLICATION_ROLES`. Un `SOURCE_CODE` que no
  encuentra un enum `Role` no es autoritativo.
- **`UNRESOLVED`**: todo lo demás, incluido el vacío.

Una señal externa se combina como en Vu6: si coincide, vale; un `TRUE` externo sobre un
`UNRESOLVED` derivado, vale; cualquier otra diferencia deja `UNRESOLVED`.

### El registro, cerrado

`role-profile-consistency.json` se instala vacío, con la forma del paquete. El schema se cierra con
`additionalProperties: false` en todas las capas: no hay campo para un token, una contraseña ni un
dato personal. Las evidencias viven en el catálogo del caso, también cerrado. El catálogo tiene un
campo `severity` que el módulo no lee nunca.

### La fuente de los roles

Una superficie resuelve su `roleAssignmentSource` solo si declara `RESOLVED` con un `sourceRef`, y
cita una evidencia legible `ROLE_ASSIGNMENT_SOURCE` con ese mismo `value` en NFC, de una clase que
puede decirlo:
- las autoritativas del proyecto: `SECURITY_DOCUMENTATION`, `ARCHITECTURE_DOCUMENTATION`,
  `PROJECT_REQUIREMENT`, `PROJECT_CONTRACT`, `ACCESS_CONTROL_MATRIX`, `ASSESSMENT_FINDING`,
  `OTHER_AUTHORITATIVE_EVIDENCE`;
- `APPLICATION_DATABASE_SCHEMA`, `BACKOFFICE_ASSIGNMENT_CONFIGURATION`,
  `IDENTITY_PROVIDER_CONFIGURATION` e `INTEGRATION_CONTRACT`.

No lo dicen `SOURCE_CODE`, `NAMING_CONVENTION`, `AUTHENTICATION_SUCCESS`, `TOKEN_CLAIM_PRESENCE`, ni
las débiles. Otra evidencia que puede decirlo y nombra otra fuente para la superficie la deja sin
resolver. La evidencia de la fuente trae en `roles` los roles que esa fuente asigna. Sin fuente da
`ROLE_ASSIGNMENT_SOURCE_UNRESOLVED`.

### Lo esperado: el mapeo

Cada `mapping` es un rol o un conjunto de roles. Su acceso esperado sale de una evidencia citada y
legible `ROLE_PROFILE_MAPPING` que nombra el mapping, trae `value` igual al `expectedProfileRef` y
declara `operations` y `dataScopes`. Puede decirlo una clase autoritativa o
`ROLE_PROFILE_CONFIGURATION`. Dos evidencias que pueden decirlo y no coinciden en perfil,
operaciones o alcances lo dejan sin resolver. El nombre del rol no define nada.

Cada rol de la fuente necesita estar en algún mapping, y cada rol de un mapping necesita estar en la
fuente. Si no, da `ROLE_PROFILE_MAPPING_UNRESOLVED`. Sin mapeo, también.

### Lo efectivo: el acceso, por operación y por alcance de datos

Una evidencia `ACCESS` dice `ALLOWED` o `DENIED` sobre `operations` o `dataScopes` de un mapping.

- **Del servidor**: `BACKEND_AUTHORIZATION_CODE`, `BACKEND_AUTHORIZATION_CONFIGURATION`,
  `UNIT_AUTHORIZATION_TEST`, `INTEGRATION_AUTHORIZATION_TEST`, `API_AUTHORIZATION_TEST`,
  `AUTHORIZED_QA_ROLE_TEST`, `ASSESSMENT_FINDING` y `OTHER_AUTHORITATIVE_EVIDENCE`.
- **Del cliente**: `FRONTEND_ROLE_GUARD`, `UI_VISIBILITY_CONFIGURATION` y `UI_TEST`.
- **No dicen nada de acceso**: `AUTHENTICATION_SUCCESS`, `TOKEN_CLAIM_PRESENCE`,
  `INPUT_VALIDATION`, `NAMING_CONVENTION` ni las débiles.

Lo que se compara son las operaciones esperadas, las `protectedOperationRefs` del mapping y las que
una evidencia citada da por permitidas. Con los alcances de datos es lo mismo, con `dataScopeRefs`.
Una operación es protegida si está en `protectedOperationRefs`. Un alcance de datos es siempre
protegido.

| Caso | Del servidor | Resultado |
|-|-|-|
| esperada | `ALLOWED` | consistente |
| esperada | `DENIED` | `UNDER_PRIVILEGED_PROFILE` |
| no protegida, sin servidor | cliente `ALLOWED` o `DENIED` | consistente |
| no esperada | `ALLOWED`, con el cliente en `DENIED` | `DIRECT_ACCESS_BYPASSES_ROLE` |
| no esperada | `ALLOWED` | `OVER_PRIVILEGED_PROFILE` |
| no esperada | `DENIED` | consistente |
| protegida, sin servidor | cualquier cliente | sin resolver |
| cualquiera | `ALLOWED` y `DENIED` a la vez | sin resolver |

Lo que no tiene fila queda sin resolver. Cuando hay evidencia del servidor, esa manda: una del
cliente, citada o no, no cambia el resultado de esa operación. La del cliente se lee aparte y queda
en la salida como evidencia separada.

🔴 Una diferencia de presentación local, sin recurso ni operación protegida detrás, no es una falla
de Vu8 (el check del paquete, §6). Por eso la fila del cliente solo no tiene `OVER` ni `UNDER`. Una
operación que el servidor permite y no se espera es `OVER` aunque no esté en `protectedOperationRefs`.

### Varios roles

`multiRoleSemantics` cuenta solo si declara `RESOLVED` o `NOT_APPLICABLE` y cita una evidencia
legible `MULTI_ROLE_SEMANTICS` con el mismo valor. Puede decirlo una clase autoritativa,
`IDENTITY_PROVIDER_CONFIGURATION` o `ROLE_PROFILE_CONFIGURATION`. Si no, da
`MULTI_ROLE_PROFILE_UNRESOLVED`. Un mapping de dos roles con `NOT_APPLICABLE` también queda sin
resolver.

🔴 El módulo nunca calcula el perfil de un conjunto desde los de sus roles. Un mapping de varios
roles necesita su propio `ROLE_PROFILE_MAPPING`.

### Los cambios de rol

`roleChangeSemantics` funciona igual, con `ROLE_CHANGE_SEMANTICS`, y además la puede decir
`SESSION_CONFIGURATION`. Sin eso da `ROLE_CHANGE_PROPAGATION_UNRESOLVED`.

Una evidencia del servidor `ROLE_CHANGE_ACCESS` dice qué pasó con un rol revocado:
- `REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH`: el rol revocado sigue vigente más allá de la ventana
  documentada. Con la semántica `RESOLVED`, da `OVER_PRIVILEGED_PROFILE`;
- `REVOKED_ROLE_EFFECTIVE_WITHIN_REFRESH` o `REVOKED_ROLE_NOT_EFFECTIVE`: consistente.

Con la semántica sin resolver, o en `NOT_APPLICABLE`, nada de eso hace `FAIL`. El módulo no compara
tiempos.

### La prueba es segura o no cuenta

Una `AUTHORIZED_QA_ROLE_TEST` cuenta si cumple todo esto:
- `authorized: true`;
- `environment` es `DEV`, `QA`, `HML` u `OTHER`;
- `syntheticIdentities: true`;
- `destructive` no es `true`;
- `realPrivilegedAccount` no es `true`;
- `rawCredentialsLogged` no es `true`.

Si no, da `ROLE_PROFILE_TEST_UNSAFE`. Con `outcome: UNAVAILABLE`, da `TEST_TARGET_UNAVAILABLE`.
Ninguna de las dos es `FAIL` ni `PASS`. Una prueba no es obligatoria: la evidencia estática alcanza.

### El mapping: su estado

1. La fuente de la superficie, y que los roles del mapping estén en ella.
2. Varios roles: la semántica.
3. Lo esperado.
4. La comparación, operación por operación y alcance por alcance.
5. El cambio de rol.
6. Lo declarado. Consistente exige `result: CONSISTENT` y `verificationMode` distinto de
   `NOT_VERIFIED`.

Una falla establecida en cualquier paso le gana a un sin resolver anterior. Sin fallas, gana el
primer sin resolver de este orden:
`ROLE_ASSIGNMENT_SOURCE_UNRESOLVED`, `ROLE_PROFILE_MAPPING_UNRESOLVED`,
`MULTI_ROLE_PROFILE_UNRESOLVED`, `ROLE_CHANGE_PROPAGATION_UNRESOLVED`, `ROLE_PROFILE_TEST_UNSAFE`,
`TEST_TARGET_UNAVAILABLE`. El `result` de un mapping es uno de `CONSISTENT`,
`OVER_PRIVILEGED_PROFILE`, `UNDER_PRIVILEGED_PROFILE`, `DIRECT_ACCESS_BYPASSES_ROLE` o `UNRESOLVED`.
El `state` de un mapping es `PASS`, el estado de la falla o el sin resolver.

### Las reglas que ya costaron pases, desde el primer día

Las seis primeras son las de Vu3 a Vu7, sin cambios. La séptima salió de la primera refutación, y
la octava de la segunda, que encontró tres respuestas distintas a la misma pregunta:
1. Lo que dice "no" pasa por la misma compuerta que lo que dice "sí".
2. Lo ilegible que nombra el mapping o la superficie impide el `PASS`, citado o no, y lo no citado
   nunca hace `FAIL`. Un id que no es texto es ilegible, nunca una excepción.
3. La falla establecida gana siempre: un acceso de más, citado y legible, es `FAIL` diga lo que diga
   el registro. Uno no citado deja el mapping sin resolver.
4. Todo id se normaliza a NFC antes de comparar y antes de contar repetidos.
5. Hay un solo paso de bloqueo. Bloquea una prueba insegura o sin objetivo que nombra algo del
   registro y que pesa, con la regla 8. Nunca tapa un `FAIL` y nunca reemplaza un sin resolver
   anterior.
7. Un item con `outcome` fuera de lo legible (`UNAVAILABLE`, `INCONCLUSIVE`, `REFUTED`) es
   ilegible, de la clase que sea, prueba incluida. Si pesa, con la regla 8, impide el `PASS`. Nunca
   hace `FAIL`.
8. **Una sola respuesta a "¿este item pesa?"**, para el bloqueo, lo ilegible y lo no citado. Pesa
   si se lo cita, o si nombra el mapping y dice una falla. Dice una falla solo un item del servidor
   que permite algo no esperado, niega algo esperado, o dice que un rol revocado sigue vigente más
   allá de la ventana. Sin lo esperado resuelto, cualquier permiso del servidor cuenta. El cliente
   nunca dice una falla por sí solo, legible o no: con servidor manda el servidor, y sin servidor una
   operación protegida queda sin resolver y una opción local no falla.
6. Hay una sola regla de salida de secretos, la de `controles/lib/evidencia.py`, sin tocarla.

### La salida no guarda una credencial

La salida pasa por la regla de salida de `controles/lib/evidencia.py`, sin tocarla. Esa regla
reconoce las formas con palabra clave, `Bearer`, un JWT, una URL con usuario y contraseña y la
cabecera de una clave PEM. No reconoce un token con prefijo de proveedor ni una contraseña sin nada
que la marque, y ninguna regla puede reconocer lo segundo.

Por eso, desde la primera refutación, `testIdentityRef` no sale: es el campo libre más expuesto y el
resultado no lo necesita. Ampliar la lib es un cambio aparte, anotado en `PENDIENTES-FH.md`, porque
cambia la regla que comparten Vu3 a Vu8 y se refuta sola.

### El agregado, la unidad, el reporte y la refutación atómica

- **Una falla** en cualquier mapping hace fallar el agregado, con el primer estado de este orden:
  `DIRECT_ACCESS_BYPASSES_ROLE`, `OVER_PRIVILEGED_PROFILE`, `UNDER_PRIVILEGED_PROFILE`.
- **Un sin resolver material** impide el `PASS`: una superficie, un mapping, una fuente o una
  semántica, o una superficie nombrada por la señal sin entrada en el registro.
- **El registro vacío con la señal en `TRUE`** da `ROLE_ASSIGNMENT_SOURCE_UNRESOLVED`.
- **La unidad** lleva `rules.Vu8` con `applicability`, `result`, `surfaces` y `evidence`.
- **El reporte**: la salida pasada por `seguridad.resultado("Vu8", …)` y por `desde_regla` entra al
  libro de siempre, en el dominio `authorization-roles`.
- **La refutación atómica**: `para_refutacion` traduce la salida a una entrada de `checks.json`,
  atada a la huella y la revisión de la unidad. El estado es `PASS` o `FAIL`, y un sin resolver
  queda tal cual. Un `PASS` o un `FAIL` cierran la unidad sin refutador. Un sin resolver la deja en
  una sola unidad pendiente, con el alcance declarado y nada más.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/role-profile-consistency.json` | El registro, instalado vacío |
| `comun/schemas/role-profile-consistency.schema.json` | Su contrato: el del paquete, cerrado en todas las capas |
| `harnesses/desarrollo/reglas/es0902-vu8-governance.md`, `es0902-vu8-application-roles-present-signal.md` y `es0902-vu8-role-profile-consistency-check.md` | Gobierno, señal y procedimiento, como vinieron |
| `harnesses/desarrollo/controles/policies/user-profile-role-enforcement-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/role-profile-consistency.py` | El check, la señal y las dos traducciones |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu8` en la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles |
| `docs/seguridad-es0902.md` | Vu8 |
| `tests/casos/56_es0902_vu8_perfiles_y_roles.py` | Los escenarios |

## Escenarios verificables

El paquete trae la lista `VU8-01` a `VU8-61`. Cada `E-nn` es el `VU8-nn` con el mismo número.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu8`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `applicationRolesPresent`, `user-profile-role-enforcement-required` y
  `role-profile-consistency` están exactos en la matriz, el registro de controles y el módulo.
  · rojo visto: si
- **E-03** — La fila declara `dev-security` y `dev-backend`, en ese orden. · rojo visto: si
- **E-04** — No hay ningún agente, skill, review ni señal nuevos, y `ALGORITMOS` sigue en diez.
  · rojo visto: si

### La señal

- **E-05** — Una evidencia legible `APPLICATION_ROLES: PRESENT` enciende la señal.
  · rojo visto: si
- **E-06** — Un `APPLICATION_DATABASE_SCHEMA` con los roles en la base la enciende.
  · rojo visto: si
- **E-07** — Un `IDENTITY_PROVIDER_CONFIGURATION` con grupos o claims la enciende.
  · rojo visto: si
- **E-08** — Un `SOURCE_CODE` que dice `ABSENT` porque no hay enum `Role` no apaga la señal.
  · rojo visto: si
- **E-09** — Una evidencia autoritativa `ABSENT`, sola, apaga la señal y da `NOT_APPLICABLE`.
  · rojo visto: si
- **E-10** — El vacío, una evidencia débil, o un `ABSENT` con algo ilegible o con una superficie
  registrada dan `UNRESOLVED` y `APPLICABILITY_UNRESOLVED`. · rojo visto: si

### La fuente de los roles

- **E-11** — La fuente resuelta sale en la salida con su `sourceRef` y la evidencia que la sostiene.
  · rojo visto: si
- **E-12** — Un `NAMING_CONVENTION` o un `SOURCE_CODE` que nombra la fuente no la resuelve.
  · rojo visto: si
- **E-13** — Sin fuente, o con dos fuentes autoritativas distintas, da
  `ROLE_ASSIGNMENT_SOURCE_UNRESOLVED`. · rojo visto: si
- **E-14** — Un `AUTHENTICATION_SUCCESS` no resuelve la fuente ni dice nada de acceso.
  · rojo visto: si

### El mapeo

- **E-15** — Un `ROLE_PROFILE_MAPPING` citado resuelve el acceso esperado del mapping.
  · rojo visto: si
- **E-16** — Un rol llamado `admin` sin mapeo no tiene acceso esperado, y el módulo no tiene ninguna
  lista de nombres de rol. · rojo visto: si
- **E-17** — Sin mapeo, o con un rol de la fuente que ningún mapping cubre, da
  `ROLE_PROFILE_MAPPING_UNRESOLVED`. · rojo visto: si
- **E-18** — El módulo no nombra ningún framework, anotación ni claim, y dos implementaciones
  distintas con la misma evidencia dan el mismo resultado. · rojo visto: si
- **E-19** — Un modelo de grupos, uno de claims y uno de conjuntos de permisos llegan a `PASS` con
  la misma forma de evidencia. · rojo visto: si

### La comparación

- **E-20** — Lo esperado igual a lo efectivo da `CONSISTENT` y `PASS`. · rojo visto: si
- **E-21** — Una operación protegida de más, permitida por el servidor, da
  `OVER_PRIVILEGED_PROFILE` y falla. · rojo visto: si
- **E-22** — Un alcance de datos de más, permitido por el servidor, da `OVER_PRIVILEGED_PROFILE`.
  · rojo visto: si
- **E-23** — Una operación esperada que el servidor niega da `UNDER_PRIVILEGED_PROFILE` y falla.
  · rojo visto: si
- **E-24** — La `severity` de la evidencia no cambia ningún estado: un `UNDER` leve falla igual que
  un `OVER` grave. · rojo visto: si
- **E-25** — Un mapping inconsistente hace fallar el agregado aunque los demás cumplan.
  · rojo visto: si

### El servidor y el cliente

- **E-26** — Un botón de administración escondido, solo, no prueba que se niegue una operación
  protegida: queda sin resolver. · rojo visto: si
- **E-27** — Con el cliente negando y el servidor permitiendo, da `DIRECT_ACCESS_BYPASSES_ROLE` y
  falla. · rojo visto: si
- **E-28** — Con el servidor negando la operación al rol que no debe tenerla, cumple.
  · rojo visto: si
- **E-29** — La guarda del cliente y la del servidor salen como evidencia separada, y cuando hay
  servidor, manda el servidor. · rojo visto: si
- **E-30** — Una opción de presentación local, no protegida, se resuelve con evidencia del cliente
  sola, y una diferencia ahí —mostrada sin esperarla o escondida esperándola— no falla.
  · rojo visto: si

### Varios roles

- **E-31** — Dos roles con operaciones `x` e `y` no dan `x ∪ y` sin su propio mapeo.
  · rojo visto: si
- **E-32** — Tampoco dan `x ∩ y`. · rojo visto: si
- **E-33** — Tampoco dan el perfil del rol "más alto". · rojo visto: si
- **E-34** — Con la semántica resuelta y el mapeo propio del conjunto, cumple.
  · rojo visto: si
- **E-35** — Sin semántica sostenida da `MULTI_ROLE_PROFILE_UNRESOLVED`. · rojo visto: si

### Los cambios de rol

- **E-36** — Un rol revocado vigente, sin semántica sostenida, no hace `FAIL`.
  · rojo visto: si
- **E-37** — Con la semántica resuelta, un rol revocado vigente dentro de la ventana cumple.
  · rojo visto: si
- **E-38** — Sin semántica sostenida da `ROLE_CHANGE_PROPAGATION_UNRESOLVED`.
  · rojo visto: si
- **E-39** — Con la semántica resuelta, un rol revocado vigente más allá de la ventana falla.
  · rojo visto: si

### Los límites

- **E-40** — El `PASS` de C1 no pone en `PASS` a Vu8. · rojo visto: si
- **E-41** — El `PASS` de Vu8 no pone en `PASS` a C1. · rojo visto: si
- **E-42** — Un `TOKEN_CLAIM_PRESENCE`, solo, no resuelve ni cumple nada. · rojo visto: si
- **E-43** — El `PASS` de Vu5 no pone en `PASS` a Vu8. · rojo visto: si
- **E-44** — Un `INPUT_VALIDATION` no cuenta como acceso. · rojo visto: si

### La evidencia y la prueba

- **E-45** — Evidencia estática de configuración y de código del servidor sostiene un `PASS`.
  · rojo visto: si
- **E-46** — Tests unitarios y de integración de autorización sostienen un `PASS`.
  · rojo visto: si
- **E-47** — Una prueba autorizada en QA con identidades sintéticas sostiene un `PASS`.
  · rojo visto: si
- **E-48** — Se llega a `PASS` sin ninguna prueba en runtime. · rojo visto: si
- **E-49** — Lo que la regla de salida compartida (`controles/lib/evidencia.py`) reconoce como
  credencial no sale en la salida, la unidad ni el libro, y `testIdentityRef` no sale nunca. El
  schema no admite un campo de más. Un token con prefijo de proveedor (`glpat-`) en otro campo libre
  sí sale: es el pendiente de la lib, y queda clavado en verde. · rojo visto: si
- **E-50** — Una prueba en `PRD`, con una cuenta privilegiada real, destructiva, sin identidades
  sintéticas, no autorizada o con credenciales registradas da `ROLE_PROFILE_TEST_UNSAFE`.
  · rojo visto: si
- **E-51** — Una prueba insegura no es `PASS` ni `FAIL`, también cuando dice que hay acceso de más
  o de menos, citada o no. · rojo visto: si
- **E-51b** — Una evidencia citada con `outcome` `UNAVAILABLE`, `INCONCLUSIVE` o `REFUTED` impide el
  `PASS` y no hace `FAIL`, diga lo que diga. · rojo visto: si

### El agregado

- **E-52** — Un mapping sin resolver impide el `PASS` aunque los demás cumplan.
  · rojo visto: si
- **E-53** — Una superficie sin fuente impide el `PASS` aunque otra la tenga. · rojo visto: si
- **E-54** — La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en
  NFC. · rojo visto: si
- **E-55** — La trazabilidad `ES0902 / 6.2 / 6 / Vu8` viaja en todo resultado y en `rules.Vu8`.
  · rojo visto: si
- **E-56** — La salida pasada por `seguridad.resultado` y `desde_regla` entra como
  `RULE_EVALUATION` de `ES0902.Vu8` al mismo libro, y Vu8 está en `authorization-roles`.
  · rojo visto: si
- **E-57** — `reporte_seguridad/` no tiene ningún archivo nuevo y no hay un segundo libro.
  · rojo visto: si

### La refutación atómica

- **E-58** — Un plan con Vu8 aplicable en una unidad de trabajo compila a una sola unidad de
  `ES0902.Vu8` por alcance, con una skill de `dev-security` o `dev-backend`. · rojo visto: si
- **E-59** — Un `PASS` o un `FAIL` del check, traducido por `para_refutacion`, cierra la unidad sin
  refutador. Un sin resolver la deja pendiente. · rojo visto: si
- **E-60** — La unidad pendiente lleva solo el alcance declarado, y un veredicto de otra regla o con
  evidencia fuera del alcance se rechaza. · rojo visto: si
- **E-61** — El `PASS` de Vu8 no mueve el estado oficial de seguridad. · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/56_es0902_vu8_perfiles_y_roles.py`, con el id
en el título. Ninguno lleva `· verificación: lectura`: E-58 a E-60 prueban el compilador y el
registro de veredictos, no una corrida del refutador.

## Riesgos conocidos

- **Casi todo proyecto real va a quedar sin resolver.** Pocos tienen una matriz de acceso
  autoritativa, y además Vu8 pide la semántica de varios roles y la de cambio de rol.
- **Lo esperado y lo efectivo pueden salir de la misma configuración.** Si el proyecto declara su
  `ROLE_PROFILE_CONFIGURATION` como autoritativa y el servidor la lee, Vu8 compara la configuración
  consigo misma. Solo un test o una prueba miran lo que pasa de verdad.
- **Un token con prefijo de proveedor en `sourceRef`, en un id o en otro campo libre sale tal cual**
  hasta que se amplíe `controles/lib/evidencia.py`.
- **Qué operación es protegida lo dice el registro.** Una operación de servidor que el proyecto no
  lista en `protectedOperationRefs` se trata como de presentación.
