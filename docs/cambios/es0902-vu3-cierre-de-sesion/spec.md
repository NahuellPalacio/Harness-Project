# ES0902 Vu3 — cerrar la aplicación o el browser no deja viva la sesión anterior

**Estado:** verificado y cerrado · **Fecha:** 23-09-2026 · **Regla:** ES0902 6.2 §6 Vu3

## Qué problema resuelve

> *"Toda aplicación que se cierra a través de las ventanas o en forma directa del browser, no debe
> dejar la sesión activa."* (ES0902 v6.2, pág. 7)

La fila está en la matriz —`CONDITIONAL` sobre `browserSessionPresent`, `dev-security`, una policy,
un check, cero reviews— y sus dos controles están declarados y no construidos
(`browser-close-session-termination-required`, `browser-close-session-termination`). Nada produce
la señal.

Vu3 tiene siete formas baratas de ponerse en verde, o en rojo, que son las que este cambio cierra:

1. **El logout por el cierre.** Que el botón de salir funcione, o que el logout de OIDC funcione, no
   dice qué pasa cuando el usuario cierra la ventana sin tocarlo.
2. **El hook por el comportamiento.** `beforeunload`, `unload`, `pagehide` y `sendBeacon` en el
   código no prueban que la sesión muera.
3. **La pantalla por la sesión.** Volver a ver el login mientras la API protegida sigue aceptando la
   sesión vieja es una sesión viva.
4. **El almacenamiento por el veredicto.** Una cookie de sesión no aprueba, `localStorage` no
   reprueba: lo que decide es si la sesión vieja se puede usar.
5. **El SSO por la sesión vieja.** Que el proveedor no pida la contraseña al volver no es la sesión
   anterior: puede ser una nueva, creada por un intercambio nuevo.
6. **La pestaña por la ventana.** Vu3 nombra la ventana y el browser; convertirlo en "cerrar
   cualquier pestaña cierra la sesión global" es inventar.
7. **El timeout por el cierre.** Un vencimiento por inactividad es Vu4, y no reemplaza a Vu3.

Y la peligrosa: probar el cierre con una cuenta real, o registrando la cookie, es filtrar la sesión.

## Qué queda afuera

- **Un segundo inventario de superficies.** Las superficies son las de C1, leídas con el cargador de
  C1. El registro de Vu3 guarda evidencia por `surfaceId`.
- **Tocar C1, Vu1 o Vu2.** Vu3 importa el cargador del inventario de C1, como Vu1.
- **Cerrar el SSO del proveedor.** Vu3 gobierna la sesión de la aplicación. Sin otra fuente que lo
  pida, el SSO del proveedor puede seguir activo.
- **Una matriz de browsers.** Ni Chrome, ni Firefox, ni Edge, ni Safari: los clientes salen de la
  evidencia del proyecto.
- **Un mecanismo.** Ni flags de cookie, ni `sessionStorage`, ni revocación de tokens, ni un
  framework de sesión: la policy es de resultado.
- **Ejecutar la prueba de cierre.** El check lee evidencia de una prueba ya hecha y decide si era
  segura.
- **Un campo para "efectos esperados conocidos"** de la prueba: se lee dentro de `authorized: true`,
  como en Vu1.
- **Cambiar los agentes de la fila.** El pedido nombra a `dev-security`; la matriz instalada declara
  `dev-security` y `dev-frontend`. No se migra: `dev-security` es el dueño normativo y `dev-frontend`
  queda como está.
- **Un algoritmo en `seguridad.py`, un agente, una skill o una review.** Camino genérico;
  `ALGORITMOS` sigue en diez. `dev-openid-connect` no se toca: su evidencia entra al catálogo con su
  clase.

## Las decisiones, y por qué

### Cuatro dominios, y Vu3 juzga uno

```
APPLICATION_SESSION    lo que Vu3 juzga
IDENTITY_PROVIDER      se informa; activo después del cierre no es FAIL
TOKEN_LIFETIME         se informa; no es el veredicto
BROWSER_STORAGE        se informa; ni aprueba ni reprueba solo
```

Cada evidencia del catálogo dice de qué dominio habla. Sólo la de `APPLICATION_SESSION` puede mover
el resultado de una combinación.

### La señal sale del inventario de C1 y del registro, y encender es más barato que apagar

```
TRUE        una superficie con entrada en el registro y un sessionModel que no es UNRESOLVED,
            o con evidencia legible de BROWSER_SESSION en PRESENT
FALSE       todas las superficies con evidencia autoritativa de BROWSER_SESSION en ABSENT, sin
            entrada en el registro y con la cobertura entera; o authenticationPresent en FALSE con
            el inventario y el registro vacíos
UNRESOLVED  todo lo demás
```

Delegar el login a Keycloak no apaga la señal, y un SPA con tokens también tiene sesión en el
browser.

### Superficie, cliente y evento

Por cada superficie con sesión, los clientes salen de una evidencia `SUPPORTED_CLIENT_SCOPE` citada
que los nombra; sin ella, `SUPPORTED_BROWSER_SCOPE_UNRESOLVED`. Por cada cliente de ese alcance se
exigen `APPLICATION_WINDOW_CLOSE` y `BROWSER_CLOSE`. `TAB_CLOSE` se exige sólo si una evidencia
autoritativa citada lo establece como equivalente para esa superficie (`TAB_CLOSE_EQUIVALENT`); si
no, lo que el registro diga de la pestaña se informa y no mueve nada. Una combinación que falta es
`BROWSER_CLOSE_BEHAVIOR_UNRESOLVED`. Un cliente del registro que no está en el alcance se informa y
no se evalúa.

### El resultado de una combinación sale del comportamiento

Una combinación cuenta como cumplida cuando el registro dice `OLD_SESSION_REJECTED` o
`NEW_SESSION_ESTABLISHED_AFTER_AUTH` y cita una evidencia legible que establece `CLOSE_BEHAVIOR` con
ese mismo valor, del dominio `APPLICATION_SESSION`, para esa superficie, ese cliente y ese evento, de
una clase de comportamiento: prueba en ejecución autorizada, observación del almacén de sesiones,
chequeo del endpoint protegido con el artefacto viejo, hallazgo de assessment u otra evidencia
autoritativa.

No sostienen nada: el hook de ciclo de vida, el código fuente, la observación de la pantalla, la
inspección del almacenamiento, la prueba del logout explícito, la evidencia del logout de OIDC, la
configuración del tiempo de vida del token, la observación de la sesión del proveedor, la
configuración del timeout por inactividad, un README, un agente o una skill.

`OLD_SESSION_STILL_ACTIVE` es `FAIL` con `OLD_APPLICATION_SESSION_REMAINS_ACTIVE`: declarado, o
establecido por una evidencia citada y legible. `NOT_APPLICABLE` para un evento exigido necesita una
evidencia autoritativa `CLOSE_EVENT_NOT_APPLICABLE` para esa combinación.

### Las tres reglas de Vu1, desde el primer día

1. **Lo que dice que no pasa por la misma compuerta que lo que dice que sí.** Una prueba insegura o
   sin objetivo no aprueba ni hace `FAIL`, diga lo que diga.
2. **Lo ilegible que nombra la superficie impide el `PASS`, citado o no; lo no citado nunca hace
   `FAIL`.** "Nombra" es igualdad de texto en NFC, no subcadena.
3. **Registro y evidencia se contradicen en las dos direcciones.** Declarado cumplido contra una
   evidencia legible que dice `OLD_SESSION_STILL_ACTIVE`: citada es `FAIL`, no citada deja sin
   resolver; declarado `OLD_SESSION_STILL_ACTIVE` contra una evidencia legible que dice cumplido,
   sin resolver.

### La prueba es segura o no cuenta

Una `AUTHORIZED_RUNTIME_TEST` cuenta si `authorized: true`, el ambiente es `DEV`, `QA`, `HML` u
`OTHER` y es el de la superficie en C1, trae `testIdentityRef`, `realUserAccount` no es `true` y
`rawSecretsLogged` no es `true`. Si no, `BROWSER_SESSION_TERMINATION_TEST_UNSAFE`. Con `outcome:
UNAVAILABLE`, `TEST_TARGET_UNAVAILABLE`. Ninguna es `FAIL`.

### El catálogo es cerrado y el registro también

El catálogo no tiene campo para una cookie ni un token; el schema provisto se cierra con
`additionalProperties: false` en sus cuatro capas. Y la regla de salida única de Vu2: nada con forma
de credencial sale, venga de donde venga. Los ayudantes de evidencia —catálogo cerrado, igualdad en
NFC, regla de salida— van a `controles/lib/evidencia.py` en vez de copiarse una tercera vez.

### Lo que dejó el primer pase

- **Para Vu3 la sesión es la credencial.** La regla de salida reconoce también una cookie o un id de
  sesión (`JSESSIONID=`, `sid=`, `Cookie: SESSION=`), el código de autorización (`code=`,
  `authorization_code=`) y un `id_token_hint`. `status_code=` no.
- **Todo id se normaliza a NFC antes de comparar y antes de contar.** Dos ids de evidencia iguales en
  NFC son el mismo id repetido: no cuentan en ninguna de sus versiones. Citar en NFD es citar.
- **Cada superficie del inventario se evalúa con la suya**, también si el id está repetido: tomar la
  primera hacía depender el resultado del orden.
- **`bin/` no depende de `controles/`.** El instalador todavía no copia `controles/`; sin la lib la
  unidad se arma igual, con el estado y sin ningún id.
- **Registro y evidencia, también con `NOT_APPLICABLE`:** un cierre declarado no aplicable contra una
  evidencia legible que dice que la sesión vieja sigue viva queda sin resolver.
- **Lo que no se evalúa no mueve nada**, tampoco por una referencia colgada: una pestaña no exigida
  o un cliente fuera del alcance.
- **Lo que no se pudo leer y dice que hay sesión no deja apagar la señal**, y una prueba ajena e
  insegura que dice "rechazada" no bloquea: bloquea lo que la entrada cita o lo que dice que no.

### La unidad de trabajo lleva `rules.Vu3`

`standards.ES0902.rules.Vu3` con `applicability`, `result`, `surfaces` y `evidence`: ids y estados,
nunca contenido. Se proyecta sólo un resultado que dice ser del check de Vu3.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/browser-session-termination.json` | El registro del proyecto, instalado vacío |
| `comun/schemas/browser-session-termination.schema.json` | Su contrato, cerrado en las cuatro capas |
| `harnesses/desarrollo/reglas/es0902-vu3-*.md` | Gobierno, señal y procedimiento, como vinieron |
| `harnesses/desarrollo/controles/policies/browser-close-session-termination-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/browser-close-session-termination.py` | La señal y el check |
| `harnesses/desarrollo/controles/lib/evidencia.py` | Catálogo cerrado, igualdad en NFC, regla de salida |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu3` en la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles |
| `docs/seguridad-es0902.md` | Vu3 |
| `tests/casos/47_es0902_vu3_cierre_de_sesion.py` | Los escenarios |

## Escenarios verificables

Numerados como el pedido: `E-nn` es `VU3-nn`.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu3`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `browserSessionPresent`, `browser-close-session-termination-required` y
  `browser-close-session-termination`, exactos, en matriz, registro y módulo; y los agentes
  primarios los de la matriz, `dev-security` —el dueño normativo— y `dev-frontend`, en ese orden. · rojo visto: si
- **E-03** — Ningún agente, skill ni review nuevos. · rojo visto: si

### La señal

- **E-04** — Una superficie con sesión autenticada en el browser pone la señal en `TRUE`, la cita, y
  pasada por `senales` enciende la fila. · rojo visto: si
- **E-05** — El login delegado a OIDC no apaga la señal. · rojo visto: si
- **E-06** — Un SPA con sesión por tokens (`TOKEN_BASED_APPLICATION_SESSION`) enciende la señal.
  · rojo visto: si
- **E-07** — Evidencia autoritativa de que no hay sesión en el browser, para todas las superficies,
  apaga la señal y deja el check en `NOT_APPLICABLE`; una fuente débil no. · rojo visto: si
- **E-08** — Con el `sessionModel` en `UNRESOLVED` y sin otra evidencia, la señal es `UNRESOLVED`.
  · rojo visto: si

### Los dominios

- **E-09** — Sesión de la aplicación y del proveedor se informan por separado, y la del proveedor
  activa después del cierre no hace `FAIL`. · rojo visto: si
- **E-10** — El tiempo de vida del token no es el veredicto: con sólo esa evidencia la combinación
  queda sin resolver. · rojo visto: si
- **E-11** — No se exige cerrar el SSO del proveedor: ningún literal operativo nombra un logout
  global, y una combinación cumple sin evidencia del proveedor. · rojo visto: si
- **E-12** — `NEW_SESSION_ESTABLISHED_AFTER_AUTH` con evidencia cumple, y es distinto de
  `OLD_SESSION_STILL_ACTIVE`. · rojo visto: si

### Los eventos y los clientes

- **E-13** — Sin `APPLICATION_WINDOW_CLOSE` para un cliente del alcance,
  `BROWSER_CLOSE_BEHAVIOR_UNRESOLVED`. · rojo visto: si
- **E-14** — Sin `BROWSER_CLOSE`, lo mismo. · rojo visto: si
- **E-15** — `TAB_CLOSE` no se exige sin evidencia de equivalencia: su ausencia no bloquea y un
  `OLD_SESSION_STILL_ACTIVE` en la pestaña no hace `FAIL`; con la equivalencia, se exige.
  · rojo visto: si
- **E-16** — Los clientes salen de la evidencia del proyecto: el módulo no nombra ningún browser, y
  un cliente del registro que no está en el alcance no se evalúa. · rojo visto: si
- **E-17** — Sin evidencia de alcance, `SUPPORTED_BROWSER_SCOPE_UNRESOLVED`; con dos que no
  coinciden, también. · rojo visto: si

### El logout explícito

- **E-18** — Un botón de logout que funciona, solo, no aprueba. · rojo visto: si
- **E-19** — El logout del proveedor OIDC, solo, no aprueba. · rojo visto: si
- **E-20** — La evidencia de `dev-openid-connect` entra por su clase y sostiene el modelo de sesión,
  no el cierre; y no hay ninguna skill nueva. · rojo visto: si
- **E-21** — `explicitLogoutEvidenceRefs` sale como contexto y no cambia ningún estado.
  · rojo visto: si

### El almacenamiento

- **E-22** — Una cookie de sesión sola no aprueba. · rojo visto: si
- **E-23** — `sessionStorage` solo no aprueba. · rojo visto: si
- **E-24** — `localStorage` solo no reprueba. · rojo visto: si
- **E-25** — Un artefacto persistente que restaura la sesión vieja, con evidencia de comportamiento,
  es `FAIL`. · rojo visto: si
- **E-26** — Una sesión del servidor que sigue aceptada después del cierre es `FAIL`.
  · rojo visto: si
- **E-27** — El artefacto rechazado después del cierre cumple la combinación. · rojo visto: si

### La sesión vieja

- **E-28** — La pantalla de login con la API protegida aceptando la sesión vieja es `FAIL`.
  · rojo visto: si
- **E-29** — La pantalla de login con la sesión vieja rechazada puede pasar; la pantalla sola, no.
  · rojo visto: si
- **E-30** — Volver con un intercambio nuevo y una sesión nueva no es reusar la vieja.
  · rojo visto: si
- **E-31** — La sesión vieja que vuelve sin establecerse de nuevo es `FAIL`. · rojo visto: si

### Los hooks

- **E-32** — `beforeunload` solo no aprueba. · rojo visto: si
- **E-33** — `unload` solo no aprueba. · rojo visto: si
- **E-34** — `pagehide` solo no aprueba. · rojo visto: si
- **E-35** — `sendBeacon` solo no aprueba. · rojo visto: si
- **E-36** — La evidencia de comportamiento le gana al hook: con el hook presente y el comportamiento
  en `OLD_SESSION_STILL_ACTIVE`, `FAIL`. · rojo visto: si

### La prueba

- **E-37** — Una prueba en `PRD` no cuenta; el módulo no ejecuta nada. · rojo visto: si
- **E-38** — Una prueba con una cuenta real no cuenta. · rojo visto: si
- **E-39** — Una prueba autorizada en QA con identidad dedicada sostiene la combinación.
  · rojo visto: si
- **E-40** — Nada con forma de credencial sale, venga de donde venga —también una cookie o un id de
  sesión, un código de autorización o un `id_token_hint`—, `status_code=` no tiene esa forma, y el
  catálogo no acepta un campo para guardar una cookie o un token. · rojo visto: si
- **E-41** — Sin autorización, sin identidad, en otro ambiente, con secretos registrados o con cuenta
  real: `BROWSER_SESSION_TERMINATION_TEST_UNSAFE`. · rojo visto: si
- **E-42** — Una prueba insegura o sin objetivo no es `FAIL`, también cuando dice
  `OLD_SESSION_STILL_ACTIVE`. · rojo visto: si

### Los límites

- **E-43** — Un timeout por inactividad no reemplaza a Vu3, y el módulo no tiene números.
  · rojo visto: si
- **E-44** — `PASS` de Vu3 no es `PASS` de Vu4. · rojo visto: si
- **E-45** — `PASS` de C1 no es `PASS` de Vu3. · rojo visto: si
- **E-46** — `PASS` de Vu3 no es `PASS` de C1. · rojo visto: si

### El agregado

- **E-47** — Una combinación que cumple no tapa a una que falla: `FAIL`. · rojo visto: si
- **E-48** — Una combinación sin resolver impide el `PASS`, y una evidencia ilegible que nombra la
  superficie también, citada o no; dos ids de evidencia iguales en NFC son un repetido, en cualquier
  combinación de valores, y citar en NFD es citar; y un `NOT_APPLICABLE` contra una evidencia que dice
  que la sesión vieja sigue viva no pasa. · rojo visto: si
- **E-49** — La misma evidencia da el mismo resultado, en cualquier orden, también con la misma
  superficie repetida en el inventario o con dos iguales en NFC. · rojo visto: si
- **E-50** — La trazabilidad `ES0902 / 6.2 / 6 / Vu3` viaja en todo resultado, y la unidad de
  trabajo lleva `rules.Vu3` con aplicabilidad, resultado, superficies y evidencia por id, sin
  secretos —tampoco una cookie de sesión—; y sin `controles/lib/` la unidad se arma igual, con el
  estado y sin ids. · rojo visto: si

## Cómo se verifica

Los cincuenta por `.\tests\Invoke-Tests.ps1`. El archivo de tests arma una superficie con dos
clientes y los dos eventos, todo cumplido, y la rompe combinación por combinación.

## Riesgos conocidos

- **Nadie produce la evidencia todavía.** El registro llega vacío.
- **La tabla de clases de fuente es del harness.**
- **Vu3 depende del módulo de C1 y de `controles/lib/`**, que el instalador no copia: el ítem 2 de
  `PENDIENTES-FH.md` se agranda.
- **La regla de salida queda en la lib y también en Vu1 y Vu2** hasta que se migren. Anotado.
