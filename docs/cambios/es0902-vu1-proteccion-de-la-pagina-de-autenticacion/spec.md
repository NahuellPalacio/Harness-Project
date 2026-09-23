# ES0902 Vu1 — captcha o bloqueo de usuario, en cada página de autenticación y con evidencia

**Estado:** verificado y cerrado, con E-39 y E-42 contradichos documentados · **Fecha:** 23-09-2026 · **Regla:** ES0902 6.2 §6 Vu1

## Qué problema resuelve

Vu1 es la primera fila de los principios de seguridad de ES0902:

> *"Toda página de autenticación debe contener captcha o bloqueo de usuarios por intentos de sesión,
> funcionalidad que se encuentra contenida en OpenID."* (ES0902 v6.2, pág. 7)

La fila ya está en la matriz —`CONDITIONAL` sobre `authenticationPagePresent`, `dev-security`, una
policy, un check, cero reviews— y sus dos controles están declarados y no construidos:

```
authentication-abuse-protection-required   DECLARED_POLICY_NOT_INSTALLED
authentication-abuse-protection            DECLARED_CHECK_NOT_INSTALLED
```

Hoy Vu1 no cumple nunca, que es lo correcto, y no puede decir por qué. Tampoco hay quién resuelva
`authenticationPagePresent`: la señal está declarada en la matriz y nada la produce.

Y Vu1 tiene seis formas baratas de ponerse en verde, que son las que este cambio cierra:

1. **La `o` leída como `y`, o al revés.** La regla es alternativa: captcha **o** bloqueo.
   Exigir los dos inventa una exigencia; aceptar cualquier otra cosa la vacía.
2. **La capacidad por el mecanismo.** "Keycloak soporta protección contra fuerza bruta" no es un
   bloqueo activo en esa página.
3. **Otro control por el que nombra la regla.** WAF, límite por IP, throttling, cuotas del gateway,
   MFA, complejidad de contraseña, huella de dispositivo, puntaje de bots: sirven, y no son los dos
   que nombra Vu1.
4. **Una página por todas.** El login ciudadano protegido no tapa al del backoffice, ni al viejo que
   sigue publicado.
5. **OIDC por Vu1.** Que el estándar diga que la funcionalidad "se encuentra contenida en OpenID" no
   convierte a C1 en `PASS` de Vu1.
6. **El umbral inventado.** Cinco intentos, quince minutos: el estándar no dice ninguno.

Y hay una séptima, que no es barata sino peligrosa: probar un bloqueo es bloquear una cuenta. Una
prueba de intentos fallidos contra producción o contra un usuario real es un incidente.

## Qué queda afuera

- **Un segundo inventario de superficies.** Las páginas salen del inventario de C1,
  `authentication-surfaces.json`, leído con el mismo cargador y el mismo schema que usa el check de
  C1. El registro de Vu1 guarda **evidencia de protección por `surfaceId`**, no superficies: una
  entrada que nombra una superficie que C1 no tiene no crea una página, deja la cobertura sin
  resolver.
- **Tocar C1.** Ni su schema, ni su inventario, ni su check. Vu1 **importa** del check de C1 el
  cargador del inventario y la regla del catálogo de evidencia; no lee su resultado ni lo corre.
- **Implementar captcha o bloqueo.** El check mira evidencia. Si la página es del proveedor de
  identidad, la protección se evidencia en el proveedor, y nada empuja a la aplicación a duplicarla.
- **Ejecutar pruebas de intentos fallidos.** El módulo no abre conexiones ni lanza procesos. Lee la
  evidencia de una prueba ya hecha y decide si esa prueba era segura; la compuerta de riesgo de
  herramientas sigue siendo la de siempre para quien la ejecute.
- **Umbrales.** Cantidad de intentos, duración del bloqueo, cuándo aparece el captcha, cuándo se
  reinicia: nada se escribe. Lo que traiga la evidencia sale tal cual, marcado como no normativo.
- **Equivalencias.** Un control que no es uno de los dos no satisface Vu1. Una evidencia de
  equivalencia de una fuente de GCABA o ASI se informa y evita el `FAIL`, pero no aprueba: decidir
  que otro mecanismo vale lo mismo es decidir la normativa, y el harness no carga ninguna fuente que
  lo haga.
- **Un campo para "efectos esperados conocidos".** El paquete lo pide para una prueba en ejecución y
  el schema provisto no lo trae. `authorized: true` se lee como la autorización de la prueba con sus
  efectos; agregar el campo es cambiar el contrato provisto, y queda anotado en `Pendientes/`.
- **Un algoritmo propio en `seguridad.py`.** Vu1 tiene un check determinista que produce el `PASS`:
  sale por el camino genérico, como O2 y C1. `ALGORITMOS` sigue en diez.
- **Un agente, una skill o una review.** `dev-security` sigue siendo el dueño; la matriz declara cero
  reviews y no se migra.
- **La relación con la revisión de integridad de repositorio.** El paquete dice que puede alimentar
  Vu1; hoy no hay nada que la consuma y sigue siendo una capacidad aparte.

## Las decisiones, y por qué

### La señal sale del inventario de C1, y encender la regla es más barato que apagarla

`authenticationPagePresent` se deriva superficie por superficie:

```
TRUE        credentialEntryDelegated true   -> página del proveedor de identidad
            credentialEntryDelegated false  -> página de la aplicación
            evidencia que establece AUTHENTICATION_PAGE con valor INTERACTIVE
FALSE       evidencia AUTORITATIVA que establece AUTHENTICATION_PAGE con valor NON_INTERACTIVE,
            y credentialEntryDelegated null
UNRESOLVED  nada de lo anterior, o las dos cosas a la vez
```

Y la señal del proyecto: `TRUE` si alguna superficie tiene página; `FALSE` sólo si todas son
`NON_INTERACTIVE` con autoridad y la cobertura consta —o si `authenticationPresent` es `FALSE` con
el inventario vacío—; `UNRESOLVED` en cualquier otro caso, incluido el inventario vacío.

La asimetría es a propósito. `TRUE` hace que la regla aplique: puede salir de una declaración del
inventario. `FALSE` la apaga: tiene que salir de una fuente autoritativa. Delegar el login a Keycloak
**no** es no tener página: el ingreso de credenciales delegado es una página, la del proveedor.

La señal sale como documento de `normative-signal`, producida por `senales.producir`, con evidencia
`REPOSITORY_CONFIGURATION` que cita el inventario por `surfaceId`. Si quien llama pasa además un
valor, se usa sólo si coincide con el derivado; `TRUE` sobre un derivado sin resolver se acepta
(enciende); cualquier otro desacuerdo es `APPLICABILITY_UNRESOLVED`.

### Cada página se evalúa sola, y el agregado es el de la peor

```
una página en FAIL                                    -> FAIL
superficie sin resolver, id repetido, superficie
  detectada y no inventariada, entrada de Vu1 para
  una superficie que C1 no tiene                      -> AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED
todas las páginas con un mecanismo activo             -> PASS
el resto                                              -> el estado sin resolver de las que faltan
```

### La `o` es una `o`

Por página, cada mecanismo sale `ACTIVE`, `INACTIVE` o sin resolver, y el resultado es:

```
captcha activo y bloqueo activo           BOTH_ACTIVE
uno activo, el otro cualquier cosa        CAPTCHA_ACTIVE | LOCKOUT_ACTIVE
los dos inactivos                         NO_ALLOWED_MECHANISM_ACTIVE      -> FAIL
cualquier otra cosa                       PROTECTION_UNRESOLVED
```

Un mecanismo inactivo no tapa al otro activo. Uno inactivo y el otro sin declarar no es `FAIL`: no se
sabe si el otro existe.

### Activo quiere decir evidencia de que está activo, en esa página

Un mecanismo del registro cuenta como activo cuando dice `status: ACTIVE` y cita, en el `evidence`
de su entrada, una evidencia del catálogo que cumple todo esto:

- establece ese mecanismo —`CAPTCHA` o `USER_LOCKOUT_AFTER_FAILED_ATTEMPTS`— con `value: ACTIVE`;
- su `sourceType` es el mismo `evidenceMode` que declara el mecanismo;
- trae referencia, su `scope` es el de la superficie, y nombra la superficie en `surfaceIds`;
- si declara ambiente, es el de la superficie; si declara `outcome`, es `CONFIRMED`;
- si la página es del proveedor, no es `APPLICATION_CONFIGURATION`: la configuración de la
  aplicación no prueba lo que pasa en la página del proveedor.

Una capacidad no es un mecanismo: `value: SUPPORTED` o `AVAILABLE`, o una clase como
`PROVIDER_CAPABILITY`, `LIBRARY_CAPABILITY`, `FRAMEWORK_CAPABILITY`, `README_STATEMENT`,
`SCREENSHOT`, `INFORMAL_STATEMENT`, `AGENT_STATEMENT`, `SKILL_OUTPUT` u `OIDC_CONFIGURED`, no cuentan.
Una evidencia con `value: INACTIVE` establece que el mecanismo está inactivo, y contra un `ACTIVE`
del registro lo deja sin resolver.

### Lo que dice que no pasa por la misma compuerta que lo que dice que sí

Una evidencia con `value: INACTIVE` se lee con las mismas reglas que una con `ACTIVE`: la prueba
en ejecución tiene que ser segura y confirmada, y cualquier otra evidencia con un `outcome` que no
es `CONFIRMED` no se lee. Lo que no se lee no aprueba **ni hace `FAIL`**: deja el mecanismo sin
resolver, con el estado de por qué —prueba insegura, sin objetivo—. Y la contradicción se busca en
todo el catálogo, no sólo en lo que la entrada cita: quien arma el registro no elige qué "no" se
lee. (El refutador, primer pase: E-32 a E-36 salían en `FAIL` con una prueba insegura.)

### Las tres reglas que cierran las clases del segundo pase

El segundo pase encontró dos huecos de la misma familia que el primero, y la respuesta no es un caso
más sino una regla por clase:

1. **Nada con forma de credencial sale, venga de donde venga.** La regla es de salida: el resultado
   entero —y la señal— pasa por el mismo filtro al cerrarse, así que un `surfaceId`, un id de
   evidencia, un `detectedSurfaces`, un error de schema o una clave del registro no la esquivan. La
   forma exige que la clave **termine** en la palabra (`DB_PASSWORD=` sí, `passwordPolicy:` y
   `tokenLifespan=` no) y no cuenta el `:secret:` de un ARN: un umbral o una referencia a un gestor
   de secretos no dejan el registro sin leer. (E-39.)
2. **Lo que nombra la página y no se puede leer impide el `PASS`, esté citado o no; lo que no está
   citado nunca hace `FAIL`.** Una contradicción repetida o mal formada que nadie cita ya no se
   descarta en silencio, y una prueba ajena no se lee con el `runtimeTest` de esta entrada. (E-42.)
3. **Registro y evidencia se contradicen en las dos direcciones.** Un `INACTIVE` declarado contra
   una evidencia legible que dice `ACTIVE` no se elige, igual que al revés; y las equivalencias se
   leen en todo el catálogo, como las contradicciones. (Fuera de la letra del segundo pase.)

### Una entrada del registro no deja apagar la señal

Una entrada del registro de Vu1 dice "acá hay una página". Si nombra una superficie que el
inventario no tiene como página, o si el registro no se puede leer, la señal no queda en `FALSE`
aunque el inventario diga que todo es no interactivo. (Primer pase: E-38.)

### Lo que puede decir que no, y viene ilegible, no se descarta

Es la lección de C1. Un id citado que no resuelve en el catálogo —mal formado, repetido o ausente—
podía ser la evidencia de que el mecanismo está inactivo. Una página que cita algo ilegible queda
`PROTECTION_UNRESOLVED`. Dos entradas del registro para la misma superficie dejan esa página sin
resolver, en cualquier orden. Un registro que no valida contra su schema no se lee: todas las
páginas sin resolver.

### Una evidencia del proveedor sirve a todas las páginas que nombra

La reutilización de C1 es esta: la página del proveedor sale de `credentialEntryDelegated` del
inventario de C1, y una sola evidencia de configuración del proveedor puede nombrar en `surfaceIds`
todas las páginas que delegan en él. La propiedad de la página del registro de Vu1 tiene que
coincidir con la que se deriva de C1; si no coinciden, si alguna dice `UNRESOLVED`, o si el
inventario no la dice —`credentialEntryDelegated` en `null`—, la página no pasa: el registro repite
el dueño, no lo pone. (Lo encontró el refutador en el primer pase: E-27.)

### La prueba en ejecución es segura o no cuenta

Una evidencia `AUTHORIZED_RUNTIME_TEST` cuenta sólo si el `runtimeTest` de la entrada es seguro:

```
authorized           true
environment          DEV, QA, HML u OTHER, y el mismo de la superficie
dedicatedTestIdentityRef   presente y no vacío: una identidad de prueba, no un usuario real
result               ausente o CONFIRMED
```

`PRD`, sin ambiente, sin autorización, sin identidad dedicada o sin `runtimeTest`: la prueba no
cuenta y, si era lo único que sostenía la página, la página queda `AUTH_ABUSE_RUNTIME_TEST_UNSAFE`.
Una prueba que no tuvo objetivo —`outcome` o `result` `UNAVAILABLE`— deja `TEST_TARGET_UNAVAILABLE`.
Ninguna de las dos es `FAIL`: la evidencia queda sin resolver.

### El registro se cierra, y no guarda secretos

El schema provisto se cierra con `additionalProperties: false` en las cuatro capas —documento,
superficie, mecanismo, prueba—, como el de C1. Una clave `password` o `token` no entra. Y como los
textos libres pueden llevarlos igual, un registro con un texto que tiene forma de credencial
—`password=`, `DB_PASSWORD=`, `api_token:`, `pwd=`, `secret:`, `Bearer …`, `Basic …`, usuario y
clave en una URL, un JWT, una clave PEM— no se lee y no se repite en la salida. Un error de schema
se informa por cantidad, no por valor, y un texto del inventario de C1 con esa forma sale
`[redactado]`. No es el detector del hook: es una regla estructural del registro, y falla cerrado.

### Los umbrales pasan, y no se vuelven normativa

El `details` de un mecanismo sale en el resultado tal cual, con `normative: false` y la clase de la
fuente. El módulo no tiene ningún número, ningún campo de intentos ni de duración, y un mecanismo
sin `details` pasa igual.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/authentication-abuse-protection.json` | El registro del proyecto, instalado vacío |
| `comun/schemas/authentication-abuse-protection.schema.json` | Su contrato, el provisto con `additionalProperties: false` en las cuatro capas |
| `harnesses/desarrollo/reglas/es0902-vu1-governance.md` | El paquete de gobierno, como vino |
| `harnesses/desarrollo/reglas/es0902-vu1-authentication-page-present-signal.md` | La señal, como vino |
| `harnesses/desarrollo/reglas/es0902-vu1-authentication-abuse-protection-check.md` | El procedimiento del check, como vino |
| `harnesses/desarrollo/controles/policies/authentication-abuse-protection-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/authentication-abuse-protection.py` | La señal derivada y el check |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles, declarados |
| `docs/seguridad-es0902.md` | Vu1 |
| `tests/casos/44_es0902_vu1_proteccion_de_autenticacion.py` | Los escenarios |

La matriz no se toca, `ALGORITMOS` tampoco, y el check de C1 tampoco.

Se reescriben las afirmaciones que hoy están en verde y dejan de ser ciertas: los controles —40 →
42—, los de forma singular, los checks en disco —16 → 17— y los huecos de ES0902 —29 → 27—, donde
estén clavados.

## Escenarios verificables

Numerados igual que el pedido: `E-nn` es `VU1-nn`.

### La fila, que no se toca

- **E-01** — La clave de la fila es exactamente `ES0902.Vu1`, y todo resultado del check la
  conserva. · rojo visto: si
- **E-02** — La única señal de Vu1 es exactamente `authenticationPagePresent`, y es la que el check
  produce y consulta. · rojo visto: si
- **E-03** — El agente primario es exactamente `dev-security`, la policy
  `authentication-abuse-protection-required` y el check `authentication-abuse-protection`, con esos
  ids en la matriz, en el registro de controles y en el módulo. · rojo visto: si
- **E-04** — No se inventa nada: diez agentes, las mismas skills de `dev-security`, los mismos
  directorios de skills, cero reviews en la fila y ninguna review nueva en disco.
  · rojo visto: si

### La señal

- **E-05** — La señal sale del inventario de C1: con una superficie con página resuelve `TRUE`,
  cita esa superficie por `surfaceId`, y sin el inventario —o con uno que no valida— es
  `UNRESOLVED`; y el documento que produce, pasado por `senales`, enciende la fila en la matriz.
  · rojo visto: si
- **E-06** — Una superficie que delega el ingreso de credenciales al proveedor pone la señal en
  `TRUE` con la página del proveedor. · rojo visto: si
- **E-07** — Superficies no interactivas con evidencia autoritativa ponen la señal en `FALSE` y el
  check en `NOT_APPLICABLE`; la misma afirmación de una fuente no autoritativa —README, agente—, o
  la misma superficie con `credentialEntryDelegated` en verdadero, no la apagan.
  · rojo visto: si
- **E-08** — Con el inventario vacío, con una superficie cuya interactividad no consta, o con una
  superficie detectada que el inventario no tiene, la señal no es `FALSE`; y el check con una
  superficie sin resolver al lado de una página da `AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED`.
  · rojo visto: si

### Cada página

- **E-09** — Una página que cumple no tapa a otra sin resolver: el agregado es el de la que falta, y
  cada una trae su propio estado. · rojo visto: si
- **E-10** — Una página vieja o secundaria del inventario entra como cualquier otra: sin protección,
  impide el `PASS`; y una detectada que no está en el inventario deja la cobertura sin resolver.
  · rojo visto: si

### Captcha o bloqueo

- **E-11** — Captcha activo solo satisface la página: `CAPTCHA_ACTIVE`. · rojo visto: si
- **E-12** — Bloqueo activo solo satisface la página: `LOCKOUT_ACTIVE`. · rojo visto: si
- **E-13** — Los dos activos satisfacen la página: `BOTH_ACTIVE`. · rojo visto: si
- **E-14** — Es una `o`: uno activo con el otro inactivo, sin resolver o sin declarar pasa, en las
  dos combinaciones. · rojo visto: si
- **E-15** — Los dos inactivos es `FAIL` con `NO_ALLOWED_MECHANISM_ACTIVE` y
  `AUTHENTICATION_ABUSE_PROTECTION_INACTIVE`; uno inactivo y el otro sin declarar no es `FAIL`; y
  los dos declarados inactivos contra una evidencia legible que dice activo tampoco.
  · rojo visto: si
- **E-16** — Una capacidad del proveedor no aprueba: la clase `PROVIDER_CAPABILITY`, o una
  configuración del proveedor con `value: SUPPORTED`, dejan la página sin resolver.
  · rojo visto: si
- **E-17** — Una capacidad de librería o framework no aprueba: `LIBRARY_CAPABILITY`,
  `FRAMEWORK_CAPABILITY` y una dependencia del repositorio, las tres una por una.
  · rojo visto: si

### Otros controles no son Vu1

- **E-18** — Un WAF solo no satisface Vu1: la página no pasa y el WAF sale como sustituto
  observado. · rojo visto: si
- **E-19** — Un límite por IP solo no satisface Vu1. · rojo visto: si
- **E-20** — MFA solo no satisface Vu1. · rojo visto: si
- **E-21** — La complejidad de contraseña sola no satisface Vu1. · rojo visto: si
- **E-22** — Un control de bots, throttling, cuota de gateway o huella de dispositivo no satisface
  Vu1; tampoco una evidencia con esa clase que dice establecer captcha; tampoco un mecanismo de otro
  tipo en el registro —el schema lo rechaza—; y una evidencia de equivalencia de GCABA o ASI evita
  el `FAIL` pero no aprueba —cualquiera sea el control que declare equivalente, y aunque la entrada
  no la cite—, una sin autoridad no lo evita, y `ACTIVE`, `INACTIVE` o un mecanismo no son un
  control equivalente. · rojo visto: si

### Umbrales

- **E-23** — No se inventa una cantidad de intentos: el módulo no tiene literales numéricos que no
  sean 0 o 1, y ninguna salida tiene un campo de intentos. · rojo visto: si
- **E-24** — No se inventa una duración de bloqueo: ninguna salida ni literal operativo nombra
  duración, minutos o segundos. · rojo visto: si
- **E-25** — No se inventa un umbral de captcha: un captcha condicional sin `details` pasa, y no
  aparece ningún umbral en la salida. · rojo visto: si
- **E-26** — Un umbral que trae la evidencia sale tal cual en el resultado, con `normative: false`,
  y no cambia ningún estado. · rojo visto: si

### C1 y el proveedor

- **E-27** — La página del proveedor sale del inventario de C1, y una sola evidencia de
  configuración del proveedor que nombra varias páginas delegadas las sostiene a todas; sin
  `credentialEntryDelegated`, el dueño que declara el registro no alcanza y la página no pasa.
  · rojo visto: si
- **E-28** — A una página del proveedor no se le pide nada de la aplicación: pasa sin ninguna
  evidencia de la aplicación, y la configuración de la aplicación no la sostiene.
  · rojo visto: si
- **E-29** — OIDC configurado no es Vu1: una superficie con protocolo OIDC y proveedor Keycloak, sin
  evidencia de protección, no pasa; `OIDC_CONFIGURED` no sostiene nada; y el resultado conserva la
  frase de la fuente sobre OpenID. · rojo visto: si
- **E-30** — `PASS` de C1 no es `PASS` de Vu1: el caso que aprueba C1, pasado a Vu1 sin registro de
  protección, no pasa; los controles de C1 en `PASS` no ponen a Vu1 en `COMPLIANT`; y `evaluar` no
  recibe ningún resultado de C1: el único literal operativo que nombra a C1 —por `C1`, `keycloak`
  u `oidc-`— es el archivo del que se importa el cargador del inventario. · rojo visto: si
- **E-31** — `PASS` de Vu1 no es `PASS` de C1: con los dos controles de Vu1 en `PASS`, C1 sigue sin
  cumplir, y el caso que aprueba Vu1 no aprueba C1. · rojo visto: si

### La prueba en ejecución

- **E-32** — Una prueba en `PRD` no cuenta y deja `AUTH_ABUSE_RUNTIME_TEST_UNSAFE`; y el módulo no
  importa nada con que ejecutarla —red, procesos— y de `os` no usa más que `os.path`. · rojo visto: si
- **E-33** — Una prueba sin identidad de prueba dedicada no cuenta y deja
  `AUTH_ABUSE_RUNTIME_TEST_UNSAFE`. · rojo visto: si
- **E-34** — Una prueba autorizada en QA con identidad dedicada, en el ambiente de la superficie,
  sostiene la página. · rojo visto: si
- **E-35** — Sin autorización, sin ambiente, en otro ambiente que el de la superficie, o sin
  `runtimeTest`: `AUTH_ABUSE_RUNTIME_TEST_UNSAFE`, las cuatro. · rojo visto: si
- **E-36** — Una prueba insegura o sin objetivo no es `FAIL`: queda
  `AUTH_ABUSE_RUNTIME_TEST_UNSAFE` o `TEST_TARGET_UNAVAILABLE`, también cuando la prueba dice que el
  mecanismo está inactivo, en cada una de las condiciones inseguras; y una evidencia inactiva que no
  se confirmó tampoco hace `FAIL`. La prueba segura que dice inactivo sí cuenta. · rojo visto: si

### El registro

- **E-37** — El registro se instala vacío y valida; con una página y el registro vacío, la página
  queda `AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED`. El schema rechaza una clave de más en las
  cuatro capas. · rojo visto: si
- **E-38** — La evidencia se ata por `surfaceId` de C1: una entrada para una superficie que C1 no
  tiene deja la cobertura sin resolver —y no deja apagar la señal, tampoco con el inventario vacío
  o no interactivo, ni con el registro ilegible—; una evidencia que no nombra la superficie no la
  sostiene; y dos entradas para la misma superficie la dejan sin resolver. · rojo visto: si
- **E-39** — Ningún secreto se guarda ni se repite: una clave `password` o `token` no valida; un
  texto con forma de credencial —también con prefijo, como `DB_PASSWORD=`, o en una URL— deja el
  registro sin leer y no aparece en la salida; un error de schema no repite el valor; ningún texto
  con esa forma sale en ningún campo del resultado ni de la señal, venga del inventario de C1, del
  registro, del catálogo o de `detectedSurfaces`; y un umbral o una referencia a un gestor de
  secretos no tienen esa forma.
  · rojo visto: si

### El agregado

- **E-40** — Todas las páginas aplicables tienen que pasar para el `PASS`. · rojo visto: si
- **E-41** — Una página en `FAIL` pone todo en `FAIL`, aunque las otras pasen.
  · rojo visto: si
- **E-42** — Una página sin resolver impide el `PASS`, y una evidencia ilegible citada por la página
  también, y una evidencia que dice inactivo aunque la entrada no la cite, y una ilegible —repetida o
  mal formada— que nombra la página aunque nadie la cite; lo no citado nunca hace `FAIL`.
  · rojo visto: si
- **E-43** — La misma evidencia da el mismo resultado: dos corridas iguales, y desordenar
  superficies, entradas, mecanismos y evidencia no cambia nada — tampoco con ids repetidos.
  · rojo visto: si
- **E-44** — La trazabilidad `ES0902 / 6.2 / 6 / Vu1` y `ES0902.Vu1` viaja en todo resultado, por
  todos los caminos, y en el bloque normativo de la unidad de trabajo. · rojo visto: si

## Cómo se verifica

Los cuarenta y cuatro pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva `· verificación:
lectura`: todo lo que este cambio construye es determinista.

🔴 **Un caso que aprueba, roto de muchas maneras.** El archivo de tests arma dos páginas que
aprueban —una del proveedor con bloqueo, una de la aplicación con captcha— y las rompe. E-11 a E-13
las miran en `PASS`.

🔴 Los ids y los estados van clavados por literal en el test.

🔴 E-24 y E-30 dicen **literal operativo**: la prosa del módulo nombra C1 y umbrales a
propósito, para declarar la frontera.

## Riesgos conocidos

- **Nadie produce la evidencia todavía.** El registro llega vacío: toda corrida real con página da
  `AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED`, y es lo primero que alguien va a querer aflojar
  declarando `ACTIVE` sin evidencia —que tampoco alcanza—.
- **`reglas/` se sobrescribe en cada `-Update`.** El registro hereda la deuda ya anotada para los de
  O2, C1 y C2.
- **Vu1 depende del módulo de C1.** Importa su cargador y su catálogo: un cambio de forma del
  catálogo de C1 cambia Vu1. Es el precio de no tener dos inventarios.
- **La regla de secretos es estructural.** Mira formas conocidas; un secreto con otra forma pasa.
  El schema cerrado es la defensa principal.
- **El catálogo de clases de fuente es del harness.** Qué clase sostiene un mecanismo es una decisión
  de este cambio, no del estándar.
