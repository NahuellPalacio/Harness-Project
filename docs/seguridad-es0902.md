# ES0902 v6.2, el estándar de seguridad, en el harness

Qué regla de seguridad le aplica a una unidad de trabajo, con qué resultado, y —sobre todo— qué
cosas el harness **no puede** decidir por sí mismo.

🔴 **Instalado no es cumplido, y cumplido no es homologado.** Están las 21 reglas, el flujo de
evaluación, los entregables y el cruce con ES0901. De los controles que las reglas exigen, seis
ya existen porque los comparten con ES0901: veinte policies, dieciséis checks y dos reviews
están **declarados y no construidos**. Y aunque estuvieran los treinta y ocho en PASS, eso no es
una aprobación de seguridad: la aprobación la da DGSEI, no esto.

## Es otro estándar, no una extensión

ES0901 §7.1 y ES0902 v6.2 son dos estándares de la misma autoridad que se aplican a la misma
unidad. Comparten el runtime —señales, policies, checks, reviews, registro de controles— y no
comparten el archivo ni el espacio de ids:

```
reglas/es0901-7.1-normative-matrix.json   24 filas   G1, G2, D1..D8, P1..P7, C1..C4, M1..M3
reglas/es0902-6.2-normative-matrix.json   21 filas   O1, O2, C1..C3, Vu1..Vu10, Ve1, Ve2, G1..G4
```

**`G1` no identifica una regla.** Los dos tienen G1 y no son la misma, igual que C1, C2 y C3. La
clave global es compuesta y viaja al lado del id local:

```
id       "G1"            lo que dice el estándar, y lo que se cita
ruleKey  "ES0902.G1"     lo que identifica globalmente
```

Las dos hacen falta. La compuesta es la única que sirve para comparar entre estándares; la local
es la única que sirve para volver al texto del estándar sin traducirlo.

## Las 21 reglas

| Grupo | Reglas | Qué preguntan |
|---|---|---|
| Organización | O1, O2 | Si se cumple la normativa de seguridad del GCBA y quién tiene la autoridad del control |
| Calidad | C1, C2, C3 | OIDC con Keycloak de DGSEI, aprobación de seguridad en QA, tecnología aprobada |
| Principios | Vu1…Vu10 | Los diez principios de seguridad de la aplicación |
| Versionado | Ve1, Ve2 | Versión homologada, y consenso de Infraestructura para una versión más nueva |
| Aceptación | G1, G2, G3, G4 | Qué no es una aprobación, el umbral, el reenvío y la reevaluación |

Los diez principios son **diez reglas distintas** y resuelven por separado. Colapsarlos en una
review genérica de seguridad haría desaparecer nueve obligaciones detrás de un solo veredicto.

## El resultado de una regla

```
NOT_APPLICABLE   la aplicabilidad lo dijo, con una señal en FALSE explícito
NON_COMPLIANT    hay un hallazgo abierto que la cita, o un control suyo reportó FAIL
COMPLIANT        todos sus controles declarados tienen evidencia de PASS y no hay hallazgo
OVERRIDDEN       una excepción con respaldo levantó la obligación, y viaja pegada al resultado
UNRESOLVED       cualquier otra cosa
```

🔴 **Lo que falta es `UNRESOLVED`, nunca `NOT_APPLICABLE` ni `COMPLIANT`.** Que nadie haya escrito
que la aplicación maneja sesiones no prueba que no las maneje: prueba que nadie lo escribió. Y una
regla que no declara ningún control **no cumple al vacío**: cumplir sobre un conjunto vacío es la
forma más barata de que un estándar entero salga verde.

La resolución es genérica y hay **nueve** reglas con algoritmo propio, porque el estándar les
declara uno: O1, C2, Ve2, Vu4, Vu9, Vu10, G2, G3 y G4. Viven juntas en `ALGORITMOS`, en un solo
lugar, para que una décima no aparezca sin que nadie la vea.

## O1 y la normativa de TI del GCABA

O1 es la fila más ancha del estándar —*"Se deben respetar los principios y normativas vigentes de
TI del GCABA"*— y la única que no se contesta mirando el sistema. Se contesta mirando **qué
normativa aplica** y **qué se midió contra ella**. Por eso no tiene check: tiene una policy y una
review.

La línea base vive en `reglas/gcba-it-normative-baseline.json` y es un **registro de apoyo**, no
una matriz normativa. No declara reglas, no clasifica nada y nadie resuelve aplicabilidad contra
él. Dice dos cosas de cada fuente, y sólo dos:

```
ES0901 6.3                  LOADED                        el harness tiene el contenido
ES0902 6.2                  LOADED
Resolución 177-ASINF-2013   DECLARED_EXTERNAL_NOT_LOADED  ES0902 la nombra; el contenido no está
Resolución 239-ASINF/2014   DECLARED_EXTERNAL_NOT_LOADED
N° 12/ASINF/17              DECLARED_EXTERNAL_NOT_LOADED
```

🔴 **El contenido de las tres resoluciones no se transcribe, no se resume y no se deduce del texto
que las cita.** Una resolución inventada se lee igual de autoritativa que una real.

Y la vigencia es un campo aparte —`CURRENT`, `SUPERSEDED`, `UNRESOLVED`— cuyo default es
`UNRESOLVED`, también para lo que está cargado: que el harness tenga ES0901 6.3 no le consta que
6.3 sea la versión vigente.

```
fuente aplicable sin cargar        ->  EXTERNAL_NORMATIVE_CONTEXT_REQUIRED
vigencia o sucesión desconocida    ->  NORMATIVE_SUPERSESSION_UNRESOLVED
línea base ausente o ilegible      ->  NORMATIVE_BASELINE_UNRESOLVED
```

Ninguno de los tres puede terminar en `COMPLIANT`. **Con la línea base como vino, toda corrida real
de la review de O1 da `REVIEW_INCOMPLETE`**, y ése es el resultado correcto: lo que lo destraba es
que llegue el contenido autoritativo, no que alguien escriba `LOADED` sin evidencia.

O1 **no reejecuta nada**. Consume los resultados que ES0901 y ES0902 ya produjeron, declarados como
evidencia. Un resultado aplicable en `NON_COMPLIANT` impide cumplir, y ahí la review titula
`NON_COMPLIANT` aunque tenga estados sin resolver al lado —al revés que `revisiones.resolver`, y a
propósito: lo incompleto de O1 es permanente, y si titulara escondería para siempre una falla real
detrás de un estado que no se mueve—.

La excepción contractual es la misma de ES0902, sin cambios: contrato **y** aprobación de ASI, las
dos o ninguna. Concedida, el resultado exceptuado no desaparece: queda como observación, con la
excepción pegada.

Y cumplir O1 no aprueba nada. `COMPLIANT` acá no mueve el estado oficial de la evaluación, que
sigue exigiendo procedencia externa.

## O2 y quién controla la seguridad

O2 —*"El control de la seguridad informática debe estar a cargo de un organismo perteneciente al
GCABA"*— no es una regla sobre el código. Es sobre **quién responde**, y la pregunta no es si el
harness corre controles de seguridad —los corre— sino si la responsabilidad del control está
asignada a un organismo del que **consta** que es del GCABA.

Un harness con `dev-security`, cuatro skills de seguridad y resultados por regla se parece mucho a
esa autoridad. No lo es, y O2 es el control que lo deja escrito.

```
CONTROL AUTHORITY   responde por el control de seguridad del alcance
EJECUCIÓN           escanea, revisa, remedia, prepara evidencia
```

🔴 **El check no tiene ningún campo de ejecutor y no lo va a tener.** Así, *"quien ejecuta no puede
volverse quien responde"* es una propiedad de la forma del archivo y no una costumbre. Un proveedor
declarado con `SECURITY_SCANNING` no cuenta: la única responsabilidad que establece autoridad es
`SECURITY_CONTROL`, que es lo que la regla nombra.

El registro es **del proyecto** y se instala vacío, igual que los perfiles de base:

```
reglas/database-environment-access-policy.json   del HARNESS. Un proyecto no la edita
reglas/database-profiles.json                    del PROYECTO. Se instala VACIO
reglas/security-control-authority.json           del PROYECTO. Se instala VACIO
```

Y hay tres cosas que el check se niega a adivinar:

**La pertenencia al GCABA.** `gcabaMembership: VERIFIED` es una etiqueta que escribe quien edita el
archivo. Lo que la establece es evidencia de una de las seis clases autoritativas. Ni el nombre del
organismo, ni el dominio de un correo, ni el namespace del repositorio, ni el README.

**La contención de alcance.** No hay orden entre `GLOBAL`, `PROJECT`, `SYSTEM`, `APPLICATION`,
`COMPONENT` y `ASSESSMENT`: el objetivo declara su cadena, y una autoridad global cubre a quien la
nombra y a nadie más. Un orden implícito es cómo la autoridad de un proyecto termina cubriendo a
otro.

**La vigencia.** Sin `effectiveTo` no hay vigencia. Ausente no es "para siempre": es una autoridad
sobre la que nadie dijo hasta cuándo, y es la que lleva años sin que nadie mire.

Los nueve estados, y el único que aprueba es el primero:

```
PASS
FAIL                                            consta que la controlante es ajena al GCABA
SECURITY_CONTROL_AUTHORITY_UNRESOLVED           el registro está vacío
GCABA_MEMBERSHIP_UNRESOLVED                     la etiqueta sin evidencia
SECURITY_AUTHORITY_SCOPE_UNRESOLVED             ninguna alcanza al objetivo
SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED    nadie dijo hasta cuándo
SECURITY_AUTHORITY_EVIDENCE_EXPIRED             venció
CONFLICTING_SECURITY_AUTHORITY_EVIDENCE         dos organizaciones, ninguna precedencia
AUTHORITY_EVIDENCE_INSUFFICIENT                 ejecuta, no controla
```

🔴 **Falta de evidencia nunca es `FAIL`.** `FAIL` tiene un único camino y acusa a un organismo de
algo: que consta que la controlante es ajena al GCABA y que ningún organismo del GCABA controla ese
alcance. Todo lo demás que falta tiene su propio estado.

Y `PASS` no aprueba nada más: no es la evaluación de seguridad, no es C2 y no es la homologación de
DGSEI.

## C1 y el Keycloak de DGSEI

C1 pide que la autenticación hable OpenID Connect con el Keycloak que administra DGSEI, con el
cliente registrado en el servidor que corresponde, el flujo que corresponde, la política de ASI
detrás, el ingreso de credenciales delegado y el servicio OpenID anterior migrado. Lo contesta
`oidc-keycloak-integration`, **superficie por superficie**: un login que cumple no tapa a otro que
nadie miró, y un frontend ciudadano con un backoffice institucional son dos cosas.

El inventario es **del proyecto** y se instala vacío:

```
reglas/authentication-surfaces.json      del PROYECTO. Se instala VACIO
```

Vacío con autenticación presente es `AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED`, y también lo es
un inventario que no nombra un flujo que D2 sí vio.

🔴 **Nada se prueba por parecido.** Una dependencia de OIDC no prueba el protocolo; un hostname con
`keycloak` adentro no prueba la autoridad; un `client_id` no prueba el registro; el default del
framework no prueba el flujo. Cada dimensión tiene su tabla de clases de fuente, y lo que no está en
la tabla —README, ejemplo copiado, afirmación de un agente, salida de `dev-openid-connect`— no la
sostiene.

🔴 **No hay flujo universal ni URL de producción.** El flujo lo declara la superficie y lo sostiene
una autoridad que nombra ese mismo flujo. El proveedor autorizado es por ambiente: la evidencia de
producción no autoriza a QA. La única URL del GCBA que el check nombra es la del servicio anterior,
`https://oauth2-server.apps.buenosaires.gob.ar/`: activo en una superficie es `FAIL` con
`OIDC_MIGRATION_REQUIRED`; nombrado en un documento viejo es una observación.

🔴 **D2 se consume, no se corre.** `authentication-delegation` se ejecuta una vez y el check de C1
lee su resultado para el flujo con el id de la superficie.

🔴 **Ciudadano no es institucional, y el harness no elige.** Una superficie institucional con
evidencia se evalúa contra Keycloak. Cualquier otra, sin una reconciliación autoritativa **para esa
superficie**, queda `CROSS_STANDARD_INTERPRETATION_REQUIRED`: ni se le fuerza Keycloak ni se la
saca de C1. Lo que resuelve la evidencia de un proyecto vale para esa superficie de ese proyecto.

Y autenticar no es autorizar: toda superficie informa `authorization.evaluated: false`, los roles
son de la aplicación, los grupos de AD no se exigen, y la restricción por árbol o grupo de AD sale
como recomendación. `PASS` de C1 no es C2, ni Vu8, ni D1, ni D8, ni la aprobación oficial.

## C2 y la aprobación de seguridad en QA

C2 —*"Las aplicaciones homologadas deben tener el aprobado a nivel seguridad en el ambiente QA"*— lo
contesta `qa-security-approval-evidence`, con el Anexo V de ES0901 como contexto operativo: el
assessment se hace en QA, es obligatorio antes de HML y PRD, y **se repite** ante ciertos cambios.

El registro es **del proyecto** y se instala vacío:

```
reglas/security-approval-evidence.json   del PROYECTO. Se instala VACIO
```

🔴 **Nada interno aprueba.** La procedencia de una aprobación sólo admite
`EXTERNAL_GCABA_SECURITY_AUTHORITY` o `UNRESOLVED`: ni `dev-security`, ni un escáner, ni el CI, ni un
check del harness tienen cómo escribirse. Y la procedencia se ata a O2: la aprobación tiene que citar
la autoridad que O2 resolvió para ese alcance. O2 en `PASS` sin aprobación no es C2 en `PASS`.

🔴 **QA, o no.** DEV, HML, PRD u OTHER es `SECURITY_APPROVAL_NOT_IN_QA`; no saberlo es
`SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED`. El algoritmo de la regla usa los mismos dos nombres.

🔴 **El artefacto se identifica por lo que no cambia.** Commit, build, digest, imagen, release. La
rama y el repositorio no deciden. Otro commit necesita un change set completo desde el aprobado.

🔴 **Una aprobación vieja no se reusa a ciegas.** El resolvedor del Anexo V devuelve **todos** los
motivos con su evidencia —dieciocho tipos—. Los 20 días van con el desarrollo: sin desarrollo no son
motivo, y sin saber si lo hubo quedan `ASSESSMENT_AGE_CONTEXT_UNRESOLVED`. Un modelo puede sumar un
motivo, nunca sacarlo.

🔴 **Un parcial no es total.** Hace falta una cobertura oficial que nombre al candidato.

Lo consumido lleva huella `sha256`, y si cambió desde la decisión anterior es
`SECURITY_APPROVAL_EVIDENCE_CHANGED`. La unidad de trabajo lleva `standards.ES0902.rules.C2` con
referencias, no con el registro. Y `PASS` es C2 y nada más: no son las Vu, no es G2, no es el
despliegue a producción.

## C3 y las herramientas del Estándar de Desarrollo

C3 —*respetar las herramientas versionadas y autorizadas del Estándar de Desarrollo*— no trae
catálogo propio: delega en ES0901. Así que no se construyó un catálogo, ni un inventario, ni un
comparador de versiones. C3 usa los mismos cuatro controles de G1 y el mismo Anexo II, y lo que
agrega es una **puerta**:

```
el ES0901 vigente           gcba-it-normative-baseline.json
el catálogo instalado       annex-ii-technology-catalog.json, su source y su status
los controles que lo leen   los checks de G1, escritos para una versión del Anexo II
```

Los tres tienen que ser de la misma versión, o C3 no pasa:
`DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH`. Es lo que impide que C3 quede congelada en 6.3:
el día que se cargue otro ES0901, catálogo y comparador se mueven con él.

🔴 **Una ejecución, dos agregaciones.** Los dos checks de G1 corren una vez por tecnología; G1 y C3
se agregan por separado de esos resultados, y la agregación no recibe el resultado de la otra regla.

🔴 **Las semánticas de G1 no se reescriben.** Deprecada sale deprecada y la regla cumple con
observaciones; más nueva no es autorizada; la versión que asigna DGSEI no se inventa. Sin
inventario, C3 queda sin resolver, nunca `NOT_APPLICABLE`.

C3 tiene algoritmo propio —el décimo de `ALGORITMOS`— en `bin/orquestacion/estandar_de_desarrollo.py`,
porque `seguridad.py` no sabe del Anexo II a propósito. Y conforme en C3 no mueve C2, Vu7, Vu10 ni G2.

## Vu1 y la página de autenticación

Vu1 —*"Toda página de autenticación debe contener captcha o bloqueo de usuarios por intentos de
sesión, funcionalidad que se encuentra contenida en OpenID"*— lo contesta
`authentication-abuse-protection`, **página por página**. Es una `o`: captcha activo, bloqueo activo,
o los dos. Los dos inactivos es `FAIL`.

Las páginas salen del inventario de C1, leído con el mismo cargador: no hay un segundo inventario.
La señal `authenticationPagePresent` se deriva de ahí, y encenderla es más barato que apagarla. Un
login delegado a Keycloak **es** una página —la del proveedor—; apagar la regla exige evidencia
autoritativa de que la superficie no es interactiva. El registro de Vu1 guarda la evidencia de
protección por `surfaceId`, es **del proyecto** y se instala vacío:

```
reglas/authentication-abuse-protection.json   del PROYECTO. Se instala VACIO
```

🔴 **Activo, no soportado.** "Keycloak soporta protección contra fuerza bruta" no es un bloqueo
activo. Cuenta la evidencia de que el mecanismo está activo, de la clase que el mecanismo declara, que
nombra la página. La configuración de la aplicación no prueba la página del proveedor, y una sola
evidencia del proveedor sirve a todas las páginas que nombra: no se duplica en la aplicación.

🔴 **Otros controles no son Vu1.** WAF, límite por IP, throttling, cuotas, huella de dispositivo,
puntaje de bots, MFA y complejidad de contraseña se informan como sustitutos y no satisfacen nada.
Una equivalencia de GCABA o ASI evita el `FAIL` y no aprueba.

🔴 **Ningún umbral y ninguna prueba.** El check no tiene números ni ejecuta nada. Lo que la evidencia
diga de intentos o tiempos sale tal cual con `normative: false`. Una prueba de intentos fallidos
cuenta sólo si fue autorizada, fuera de `PRD`, en el ambiente de la página y con una identidad de
prueba dedicada; si no, `AUTH_ABUSE_RUNTIME_TEST_UNSAFE`, que no es `FAIL`.

El registro cierra sus cuatro capas y no se lee si trae un texto con forma de credencial. Y `PASS`
de Vu1 no es C1, ni al revés: OIDC configurado no protege una página.

## Vu2 y el dato sensible en tránsito

Vu2 —*"Todo dato sensible no puede ser enviado en texto plano"*— lo contesta
`sensitive-data-transport-protection`, **camino por camino y salto por salto**. El registro es del
proyecto y se instala vacío:

```
reglas/sensitive-data-transmission.json   del PROYECTO. Se instala VACIO
```

🔴 **Sensible lo dice una autoridad.** El estándar no define qué es un dato sensible y el harness no
inventa una taxonomía: una clase es sensible o no cuando el registro lo declara y una fuente
autoritativa citada dice lo mismo. Un nombre de campo, un escáner de secretos o un README no
clasifican: `SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED`. Para apagar la regla hace falta la misma
autoridad.

🔴 **Salto por salto.** `navegador --HTTPS--> ingreso --HTTP--> backend` es `FAIL`: el borde no tapa
el salto interno. Cada salto necesita su propia evidencia, y la cadena de saltos tiene que estar
entera.

🔴 **Codificar no es cifrar.** Base64, URL, hex, compresión, serialización, JWT sólo firmado y
ofuscación sobre `http` son en claro. Un hash no es cifrar el transporte. `https` con sólo la forma de
la URL, o con el código fuente como única evidencia, no alcanza; la validación de certificado o de
hostname apagada impide el `PASS`.

🔴 **Nada criptográfico se inventa y nada se prueba con datos reales.** Ni versión de TLS, ni suites,
ni tamaños de clave. Una prueba cuenta si fue sintética, autorizada y sin captura del payload; si no,
`SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE`, que no es `FAIL`. El catálogo de evidencia es cerrado —no hay
campo donde guardar un payload— y nada con forma de credencial sale en el resultado.

## Vu3 y el cierre de la ventana o del browser

Vu3 —*"Toda aplicación que se cierra a través de las ventanas o en forma directa del browser, no debe
dejar la sesión activa"*— lo contesta `browser-close-session-termination`, **superficie por
superficie, cliente por cliente y cierre por cierre**. Las superficies son las de C1; el registro de
Vu3 es del proyecto y se instala vacío:

```
reglas/browser-session-termination.json   del PROYECTO. Se instala VACIO
```

🔴 **Juzga la sesión de la aplicación.** La del proveedor de identidad, el tiempo de vida del token y
el almacenamiento del browser se informan aparte. Que el SSO del proveedor siga activo no es `FAIL`:
una sesión nueva creada por un intercambio nuevo no es la sesión vieja.

🔴 **El logout no es el cierre, el hook no es el comportamiento, la pantalla no es la sesión.** Un
botón de salir que funciona, un `beforeunload` o volver a ver el login no aprueban. Cuenta la
evidencia de comportamiento: el endpoint protegido que rechaza el artefacto viejo, el almacén de
sesiones, una prueba autorizada. La API que sigue aceptando la sesión vieja es `FAIL`.

🔴 **Ventana y browser, no cualquier pestaña, y los clientes los dice el proyecto.** La pestaña se
exige sólo con evidencia de que es un cierre equivalente. El módulo no nombra ningún browser.

🔴 **Vu3 no es Vu4 ni C1.** Un timeout por inactividad no reemplaza el cierre. La unidad de trabajo
lleva `standards.ES0902.rules.Vu3` con aplicabilidad, resultado, superficies y evidencia por id.

## La frontera que no se cruza

El harness hace las capas 1 y 2; la 3 no es suya.

```
Capa 1   los controles de seguridad del harness
Capa 2   la evaluación interna, automatizada
Capa 3   la evaluación oficial de GCBA / DGSEI      <- esto no es el harness
```

Lo que el harness **sí** puede declarar:

```
INTERNAL_REVIEW_COMPLETE   READY_TO_REQUEST   READY_TO_RESUBMIT   G2_THRESHOLD_SATISFIED
```

Lo que **no** puede declarar, ni un escaneo automático, ni una review de `dev-security`, ni el
cálculo del umbral:

```
REQUESTED   IN_ASSESSMENT   RESUBMITTED   APPROVED   REJECTED
```

La guarda es estructural, no una convención: **un estado oficial exige procedencia externa
declarada con evidencia**, y un productor interno no la tiene por construcción. Sin eso queda
`OFFICIAL_STATUS_UNRESOLVED` y se dice quién lo intentó. Una lista de estados prohibidos por
productor se desactualiza en silencio el día que aparece un productor nuevo, y el productor nuevo
queda permitido.

## El umbral de G2 no es una aprobación

```
ningún hallazgo por encima de LOW
Y
hasta 10 hallazgos LOW
->  G2_THRESHOLD_SATISFIED
```

Y el estado oficial **no se mueve**. Son dos hechos distintos y ES0902 los separa en dos reglas.

El umbral sólo se calcula si las severidades del escáner están mapeadas de forma **autoritativa**
a las categorías de riesgo de ES0902. Sin ese mapeo no se calcula —ni siquiera se publica un
conteo— y queda `VULNERABILITY_RISK_MAPPING_UNRESOLVED`: decidir que el `medium` de una
herramienta es el `LOW` del estándar es una equivalencia que tiene que firmar alguien.

G3 y G4 no se colapsan. En un reenvío se recontrola el **100%** de los hallazgos previos,
conservando su identidad y su evidencia de retest; con un reporte previo, una evaluación nueva es
de **alcance completo** y los hallazgos nuevos entran. Las dos siguen evaluando G2.

## La excepción aprobada por ASI

Una regla de ES0902 se puede levantar sólo con las **dos** mitades:

```
evidencia de contrato    PROJECT_CONTRACT · GCBA_NORMATIVE · SIGNED_AGREEMENT
+
aprobación de ASI        ASI_APPROVAL
```

Una sola nunca alcanza. Y **la configuración local del proyecto no es ninguna de las dos**: un
proyecto que se exime a sí mismo escribiendo un archivo en su propio repositorio no tiene una
excepción, tiene un archivo. Sin las dos mitades queda
`SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED`, y mientras esté pendiente la regla no cumple aunque
todos sus controles estén en PASS.

Una excepción alcanza **sólo** a las reglas que nombra en `affectedRules`. No derrama.

## Entregables y WAF

La sección 5 pide un paquete distinto por tipo de activo:

```
WEB_SERVICE  E1     WEB_APPLICATION  E2     MOBILE_APPLICATION  E3
SERVER       E4     TOTEM            E5
```

Los tipos **no son excluyentes**. Un sistema que es aplicación web y servicio web entrega la
**unión** de E1 y E2, nunca el conjunto más chico. Elegir el más chico es el sesgo que deja la
preparación más corta y no deja rastro.

Aplicación web y servicio web exigen además el formulario de política de WAF que provee el equipo
de Prevención. **Sus campos no se inventan**: sin la plantilla queda `WAF_FORM_CONTEXT_REQUIRED`,
y ese estado bloquea `READY_TO_REQUEST`.

## El cruce con ES0901

`reglas/es0902-cross-standard-map.json` declara ocho relaciones. Tres formas de convivir:

| Relación | Qué pasa |
|---|---|
| `CONTROL_REUSE` / `OVERLAP_REUSE` | El control se ejecuta **una vez** y su resultado se anota por fuente |
| `POTENTIAL_CONFLICT` | No se reconcilia sin evidencia autoritativa |
| `NO_AUTO_PASS` | Pasar de un lado nunca aprueba del otro |

Seis controles quedaron compartidos y se declaran una sola vez en el registro, con todas sus
fuentes:

```
approved-technology-required           ES0901.G1 + ES0902.C3 + ES0902.Ve1
homologated-version-required           ES0901.G1 + ES0902.C3 + ES0902.Ve1
technology-homologation                ES0901.G1 + ES0902.C3 + ES0902.Ve1
technology-version-compliance          ES0901.G1 + ES0902.C3 + ES0902.Ve1
credential-entry-delegation-required   ES0901.D2 + ES0902.C1
authentication-delegation              ES0901.D2 + ES0902.C1
```

🔴 **Compartir la ejecución no es compartir el resultado.** Que ES0901 D2 dé PASS no pone en PASS
a ES0902 C1: la aplicabilidad de cada regla se resolvió por separado y la evidencia que satisface
a una puede no satisfacer a la otra.

Y el conflicto que **no** se resuelve: ES0901 D1 pide autenticación ciudadana del GCBA, ES0902 C1
pide OpenID Connect con Keycloak de DGSEI. Con las dos aplicables y sin evidencia autoritativa,
`CROSS_STANDARD_INTERPRETATION_REQUIRED`. No se inventa realm, ni client, ni issuer, ni flow.

## Dónde mirar

```
reglas/es0902-6.2-normative-matrix.json       las 21 reglas
reglas/es0902-cross-standard-map.json          las ocho relaciones con ES0901
reglas/es0902-security-deliverables.json       E1..E5 y el WAF
reglas/es0902-security-governance.md           la arquitectura de gobierno, como vino
reglas/es0902-security-assessment-workflow.md  el flujo, como vino
reglas/es0902-o1-governance.md                 el gobierno de O1, como vino
reglas/gcba-it-normative-baseline.json         las cinco fuentes de TI del GCABA y su estado
reglas/es0902-o2-governance.md                 el gobierno de O2, como vino
reglas/security-control-authority.json         la autoridad de control. Del PROYECTO, vacío
reglas/es0902-c1-governance.md                 el gobierno de C1, como vino
reglas/es0902-c1-cross-standard-identity-resolution.md  la resolución por superficie, como vino
reglas/authentication-surfaces.json            las superficies de login. Del PROYECTO, vacío
reglas/es0902-c2-governance.md                 el gobierno de C2, como vino
reglas/es0902-c2-security-homologation-present-signal.md  la señal, como vino
reglas/es0902-c2-assessment-validity-resolver.md          el resolvedor del Anexo V, como vino
reglas/security-approval-evidence.json         las aprobaciones de seguridad. Del PROYECTO, vacío
reglas/es0902-c3-governance.md                 el gobierno de C3, como vino
reglas/es0902-c3-control-source-binding.json   la ligadura de C3 con G1, como vino
reglas/es0902-vu1-governance.md                el gobierno de Vu1, como vino
reglas/es0902-vu1-authentication-page-present-signal.md   la señal, como vino
reglas/es0902-vu1-authentication-abuse-protection-check.md  el procedimiento, como vino
reglas/authentication-abuse-protection.json    la protección de cada página. Del PROYECTO, vacío
reglas/es0902-vu2-governance.md                el gobierno de Vu2, como vino
reglas/es0902-vu2-sensitive-data-transmission-present-signal.md  la señal, como vino
reglas/es0902-vu2-sensitive-data-transport-protection-check.md   el procedimiento, como vino
reglas/sensitive-data-transmission.json        las clases de datos y sus caminos. Del PROYECTO, vacío
reglas/es0902-vu3-governance.md                el gobierno de Vu3, como vino
reglas/es0902-vu3-browser-session-present-signal.md       la señal, como vino
reglas/es0902-vu3-browser-close-session-termination-check.md  el procedimiento, como vino
reglas/browser-session-termination.json        el cierre de sesión de cada superficie. Del PROYECTO, vacío

bin/orquestacion/seguridad.py    qué regla aplica, y con qué resultado
bin/orquestacion/evaluacion.py   en qué estado está la evaluación, y quién puede moverla
bin/orquestacion/cruzada.py      qué relación hay entre una regla de ES0901 y una de ES0902
bin/orquestacion/linea_base.py   qué normativa de TI del GCABA hay, y qué dice la review de O1
bin/orquestacion/estandar_de_desarrollo.py  la línea base tecnológica de C3, y su agregación
```

El bloque normativo de una unidad expone los dos estándares y **conserva su forma anterior**:

```json
"normative": {
  "standard": { "id": "ES0901", "version": "6.3", "section": "7.1" },
  "applicableRules": ["..."],
  "standards": {
    "ES0901": { "..." },
    "ES0902": { "..." }
  }
}
```

Lo de arriba sigue siendo lo de ES0901, exactamente igual que antes. `standards` se suma al lado:
cambiarle el tipo a un campo que alguien ya lee es romper a distancia.

## Lo que quedó anotado y no escondido

1. **Veintinueve controles declarados y sin construir** —eran treinta y ocho hasta que O1, O2, C1
   y C2 instalaron los suyos—. Es el estado correcto de un harness que clasificó antes de construir, y es
   también el hueco más grande que tuvo hasta hoy.
2. **El mapeo de severidades no lo produce nadie todavía.** Sin él, toda corrida real de G2 sale
   `VULNERABILITY_RISK_MAPPING_UNRESOLVED`.
3. **ES0901 P5 no existe.** Su equivalencia con ES0902 Vu5 queda
   `CROSS_STANDARD_CONTROL_BINDING_REQUIRED` hasta que P5 se implemente.
4. **La matriz provista declara un id con dos tipos.**
   `security-vulnerability-acceptance-threshold` sale de G2 como policy **y** como check. El
   archivo no se corrige acá —corregir normativa provista es inventarla—: se reporta
   `SECURITY_CONTROL_ID_TYPE_COLLISION` y aparece dos veces en el reporte de huecos, una por tipo.
