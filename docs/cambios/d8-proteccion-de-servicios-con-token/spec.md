# D8 — Los servicios están protegidos con sistema de token

**Estado:** verificado y cerrado · **Fecha:** 21-09-2026 · **Regla:** ES0901 6.3 §7.1 D8

## Qué problema resuelve

La regla citable, `ES0901-7.1-D8`, pág. 13, es una oración:

> *"Los servicios deben estar protegidos con sistema de token."*

La matriz declara la fila de D8 con su señal, **una** policy y **un** check desde que se construyó, y
los dos **no existen**: cualquier consulta los reporta como `DECLARED_POLICY_NOT_INSTALLED` y
`DECLARED_CHECK_NOT_INSTALLED`.

Y hay dos trampas propias de esta regla.

**La primera: todo lo que es fácil de detectar acá es evidencia de lo que hay, no de lo que pasa en
el borde del servicio.** Una dependencia de tokens en el manifiesto, un middleware de seguridad
configurado, un endpoint de login que emite tokens, un header que se parsea, un gateway que existe,
un documento que dice *"esta ruta es privada"*: los seis se detectan en segundos y ninguno dice que
la operación protegida se rechace sin token. Un check que los mire se pone verde siempre — y en esta
regla el falso verde es el peor de las nueve instaladas, porque lo que tapa es un servicio abierto.

**La segunda: el defecto típico no está en el camino que alguien probó.** Está en la ruta de al lado
—la versión vieja que quedó activa, el método alterno del mismo controlador, el controlador
secundario que nadie migró, el path que el gateway expone sin pasar por la validación—. Un check que
verifique el camino feliz y agregue, informa `PASS` sobre una aplicación con una puerta abierta.

Y una tercera cosa, que no es trampa sino frontera: **D8 no sabe qué es un token en este proyecto.**
No hay en ningún extracto de este repositorio un mecanismo, un emisor, una audiencia, un algoritmo,
un claim, un tiempo de vida, un formato de header, un rol, un scope, una regla de refresco, una
implementación de gateway ni un código de rechazo. D8 dice *sistema de token* y se detiene ahí.

## Qué queda afuera

- **La tecnología del token.** No se declara ningún mecanismo con nombre, emisor, audiencia,
  algoritmo, claim, tiempo de vida, formato de header, regla de refresco ni implementación de
  gateway. El mecanismo entra como **dato declarado por el proyecto, con su fuente citada**; sin
  eso, `TOKEN_MECHANISM_UNRESOLVED`.
- **Un código de rechazo.** D8 no exige un estado HTTP. Si el contrato autoritativo del proyecto
  define uno, se compara; si no lo define, alcanza que la operación protegida haya sido rechazada.
  Inventar un número sería inventar el contrato.
- **Una lista de endpoints exentos.** D8 no define ninguna. Login, health, readiness, liveness,
  catálogo, webhook y API pública **no** están eximidos por esta regla: un endpoint intencionalmente
  público necesita evidencia autoritativa de excepción, y sin ella queda
  `TOKEN_PROTECTION_EXCEPTION_UNRESOLVED`. Ningún artefacto de D8 lleva un patrón de ruta ni una
  lista de categorías exentas.
- **La autorización.** Que un token válido sea aceptado no prueba que los roles y los scopes estén
  bien. D8 verifica protección con token y nada más: no afirma autorización, no afirma D1, no afirma
  D2, no afirma ES0902 y no afirma una evaluación formal de seguridad.
- **Ejecutar un servicio.** Este cambio no levanta una aplicación, no llama a un endpoint y no emite
  un token. Las sondas entran como dato, igual que en D4, D6 y D7, y quien las ejecute son las
  skills instaladas.
- **Un agente y una skill.** Los tres dueños normativos de la fila —los que la matriz declara— no se
  tocan, y la fila no declara ninguna skill. Este cambio no crea, no modifica y no renombra ninguna
  de las dos cosas.
- **Un módulo compartido.** D8 instala un check y no necesita un `lib/`. Los tres ayudantes que
  comparte con D6 y D7 —normalizar un dato declarado, atar la evidencia al build, resolver
  referencias huérfanas— quedan duplicados por tercera vez, y eso se anota como pendiente para
  `harness-staff-engineer` en vez de refactorizar dos cambios ya verificados dentro de éste.
- **La compuerta de completitud de alcance para un FALSE.** Sigue cerrada sólo para D5. D8 hereda el
  mismo límite que D7 declaró y lo declara igual — ver los riesgos.

## Las decisiones, y por qué

### El check resuelve su identidad contra la matriz, y falla cerrado si no puede

Es lo que D8 tiene de propio frente a las nueve reglas instaladas. D6 y D7 llevan sus ids escritos
adentro del módulo; el check de D8 los **deriva**:

```
de la matriz     el id de la policy, el id del check, la señal, los agentes dueños
                 y la tupla normativa entera -estándar, versión, sección-
del módulo       sólo su propio id, que es lo que el registro necesita para encontrar el archivo
```

El propio id se verifica contra la fila: si la matriz no declara `service-token-protection` como
check de D8, el módulo **no se arroga** el binding. Y si la fila no se puede resolver —la matriz no
está, no se lee, no tiene la fila, declara más de una señal— el resultado es
`D8_MATRIX_BINDING_UNRESOLVED` y **no se evalúa nada más**.

🔴 **Esa compuerta corre primero, antes de la señal.** Al revés no tendría sentido: sin saber de qué
señal depende la regla, preguntar por su valor es preguntar por un nombre que el módulo se inventó.
Es el único check de los diez instalados cuya primera compuerta no es la aplicabilidad.

📌 La consecuencia se acepta y se declara: **es el único camino de D8 cuyo resultado no lleva la
tupla normativa**, porque la tupla sale de la matriz que no se pudo leer. Lleva el estado, el motivo
y el id del módulo, y dice que la tupla falta.

### El comportamiento protegido tiene identidad propia, y por eso un bypass se ve

Un endpoint no se identifica por su URL: se identifica por **qué comportamiento protegido alcanza**.

```
behaviorId   el comportamiento protegido. Lo comparten todos los caminos que llegan a el
endpointId   un camino
kind         PRIMARY · ALTERNATE_URL · ALTERNATE_METHOD · LEGACY_ROUTE · VERSIONED_ROUTE
             SECONDARY_CONTROLLER · GATEWAY_EXPOSED · ADMINISTRATIVE · UPLOAD_DOWNLOAD
```

Un bypass es, entonces, algo que el check puede **derivar** en vez de buscar: un camino activo que
comparte `behaviorId` con otro y no exige token. No hay que reconocer una URL vieja, ni parsear un
verbo, ni saber cómo se ve un gateway. Las nueve clases entran en el inventario y ninguna se trata
distinto — el `kind` se informa para que el que lee sepa por dónde entró, no para decidir.

🔴 **Y el check no informa rutas ni verbos.** Compara identificadores, como D6 y D7. Lo que sale en
el resultado son ids, así que un `FAIL` de D8 no publica el mapa de puertas abiertas de una
aplicación.

### Tres respuestas sobre la exigencia, no dos

```
required: false   el camino declara que NO exige token  ->  FAIL. Es un camino abierto probado
required: true    con el mecanismo del proyecto         ->  se verifica con sus sondas
no declarado      nadie dijo si exige                   ->  sin resolver, y el agregado no pasa
```

La del medio es la que importa. Convertir *"nadie lo declaró"* en un `FAIL` sería inventar el hecho;
convertirlo en un `PASS` sería el falso verde que esta regla busca. Se queda sin resolver, con su
motivo propio —`TOKEN_REQUIREMENT_UNDECLARED`— para que quien remedia sepa que lo que falta es un
dato y no un arreglo.

### Un camino inactivo no es un bypass, pero la inactividad se declara

`active` es un dato del inventario, y un camino que no dice si está activo **no se da por
desactivado**: queda sin resolver. Dar por muerta una ruta que nadie apagó es exactamente el defecto
que esta regla busca.

### El rechazo se verifica, el código de rechazo sólo si hay contrato

Cada endpoint gobernado trae sus sondas:

```
NO_TOKEN        la operación protegida tiene que ser rechazada
INVALID_TOKEN   la operación protegida tiene que ser rechazada
VALID_TOKEN     el camino protegido previsto tiene que funcionar
```

El contrato del mecanismo puede declarar un código de rechazo. Si lo declara, la sonda tiene que
coincidir; si no lo declara, **alcanza el rechazo** y el código se informa sin juzgarlo. Ninguna
constante de este cambio es un número de estado HTTP.

Y las dos negativas son obligatorias: sin `NO_TOKEN` o sin `INVALID_TOKEN` el endpoint no llega a
`PASS`. La positiva sola es el falso verde más caro de esta regla — un token válido que funciona no
dice nada sobre qué pasa sin token.

### Lo que está instalado no prueba lo que se rechaza

```
TOKEN_ENFORCEMENT_PROBE    prueba. Es la unica que prueba
HUMAN_CONFIRMATION         acompana
CODE_PATH_REVIEW           acompana

REPOSITORY_DEPENDENCY      inerte: una libreria de tokens no es un endpoint protegido
SECURITY_MIDDLEWARE_CONFIG inerte: configurar no es rechazar
TOKEN_ISSUANCE             inerte: emitir un token no protege nada
LOGIN_ENDPOINT             inerte: que haya login no dice que lo demas exija token
AUTH_HEADER_PARSING        inerte: leer un header no es validarlo
GATEWAY_PRESENT            inerte: que haya gateway no dice por donde pasa el trafico
ROUTE_DOCUMENTATION        inerte: un documento que dice "privada" no la protege
AGENT_STATEMENT            inerte: una opinion con formato de evidencia
```

La sonda declara su modo —`REAL` o `MOCKED`— y una sonda mockeada **no llega a `PASS`**: documenta
el caso y no prueba que el servicio rechace. Es el eje que D6 tiene y que D7 no necesitó, y acá el
pedido lo pide explícitamente.

Y la sonda se ata al build, como en D6 y D7: una corrida sobre otro build es una corrida sobre otro
sistema.

### Ningún endpoint se exime solo

No hay una lista de rutas exentas adentro de ningún artefacto de D8. Un endpoint declarado público
necesita su excepción declarada con id, fuente de la lista y referencia; sin eso,
`TOKEN_PROTECTION_EXCEPTION_UNRESOLVED`, sea un login, un health, un readiness, un liveness, un
catálogo, un webhook o una API pública.

🔴 **Las seis categorías se nombran en la policy y en la documentación como lo que NO se exime**, y
no aparecen en ninguna estructura de datos del check. La diferencia importa: nombrarlas en prosa es
decirle a quien lee que su intuición está equivocada; ponerlas en una lista sería construir la
exención que el pedido prohíbe.

### Un PASS de D8 dice una sola cosa

```
D8         el endpoint exige token, y sin token no pasa
NO dice    que los roles esten bien, ni los scopes
NO dice    que D1 se cumpla -que mecanismo de autenticacion le toca a la aplicacion-
NO dice    que D2 se cumpla -que la credencial no se escriba en la aplicacion-
NO dice    que ES0902 se cumpla, ni que haya una evaluacion de seguridad aprobada
```

El resultado lleva **sólo** la tupla de D8 y no nombra ninguna otra regla ni ningún otro estándar,
igual que D6 no nombra a D5. Y resolver D8 no cambia la aplicabilidad de D1 ni de D2 ni el estado de
sus controles. Un caso que declara la autorización **sin verificar** puede dar `PASS` en D8: eso no
es un agujero, es el alcance de la regla, y está dicho.

### La señal se produce con el productor genérico

`senales.py` resuelve cualquier señal declarada, con evidencia y con su productor, desde D1. D8 no
agrega una rama por id de señal. Lo que sí agrega es qué cuenta como evidencia de un endpoint
—controlador, router, contrato de servicio, ruta de gateway, mapeo del framework, descubrimiento en
runtime, test, alcance confirmado por una persona— y eso va en la policy y en la documentación.

🔴 **Y el `signalId` se mira.** Es la lección de D7: una señal de otra regla en TRUE no hace evaluar
nada, queda `APPLICABILITY_UNRESOLVED` con `SIGNAL_IDENTITY_MISMATCH`. Sin eso, pasarle
`authenticationPresent` haría que D8 informara cumplimiento atribuido a una señal que nunca llegó.

### Se reutiliza la infraestructura, no se construye una segunda

`senales.py` resuelve la señal, `matriz.py` la aplicabilidad y el binding, `controles.py` el
registro y `registro_agentes.resolver_ruteo` el ruteo. No se agrega ningún módulo de orquestación,
no se abre un segundo inventario de controles y no se crea un `lib/`.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/controles/policies/service-token-protection-required.md` | La policy de D8, con su frontera de mecanismo, de excepción y de alcance |
| `harnesses/desarrollo/controles/checks/service-token-protection.py` | El check: diez estados, binding contra la matriz, cobertura, sondas y bypasses |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles de D8, declarados |
| `docs/normativa-7.1.md` | D8, el binding desde la matriz, lo que no se exime y lo que un PASS no dice |
| `tests/casos/35_d8_proteccion_con_token.py` | Los escenarios de acá abajo |

La matriz **no se toca**: su fila de D8 ya declara la señal, la policy, el check y los tres agentes
dueños desde que se construyó. Este cambio la **lee**, que es distinto.

Y se reescriben las afirmaciones que hoy están en verde y dejan de ser ciertas: el conteo de
controles declarados —24 → 26— en `31_d6/E-30`, `32_d5/E-36`, `33_bases/E-32` y `34_d7/E-42`, y el
conteo de reglas con todos sus controles construidos —nueve → diez— en `32_d5/E-36`. Está así a
propósito: quien instala una regla tiene que tocar un test que pasaba.

## Escenarios verificables

Entre paréntesis, el `D8-nn` del pedido de instalación.

### La matriz y el binding

- **E-01** — El check resuelve su identidad contra la fila de D8: el id de la policy, el id del
  check, la señal, los agentes dueños y la tupla normativa salen de la matriz, y el módulo no lleva
  escrito el id de la policy ni el nombre de la señal. (D8-01, D8-06, D8-07, D8-08)
  · rojo visto: si
- **E-02** — Sin fila de D8 resoluble el resultado es `D8_MATRIX_BINDING_UNRESOLVED`, no se evalúa
  nada más, y es el único camino cuyo resultado declara que le falta la tupla. Son **nueve** formas:
  siete entran como documento —sin la fila, sin el estándar, con dos señales, sin señales, sin
  declarar este check, sin ninguna policy, y el documento vacío— y **dos entran por la ruta**: la
  matriz ausente y la matriz ilegible, que son las únicas que ejercitan el manejo de un error al
  leerla. (§ binding) · rojo visto: si
- **E-03** — La compuerta del binding corre **antes** que la señal: sin matriz y sin señal, el
  estado es el del binding y no `APPLICABILITY_UNRESOLVED`. (§ binding) · rojo visto: si
- **E-04** — La fila no se edita: D8 sigue `CONDITIONAL` sobre `serviceEndpointPresent`, con sus tres
  agentes, su policy y su check, `CLASSIFIED`, y con exactamente las claves que tiene toda fila de
  diseño. (D8-01) · rojo visto: si

### La señal y la aplicabilidad

- **E-05** — La señal en TRUE hace a D8 aplicable, con su policy y su check. (D8-02)
  · rojo visto: si
- **E-06** — La señal en FALSE lo deja `NOT_APPLICABLE`, y el check también. (D8-03)
  · rojo visto: si
- **E-07** — Sin la señal, `APPLICABILITY_UNRESOLVED` con el nombre de la que falta. (D8-04)
  · rojo visto: si
- **E-08** — La ausencia nunca es FALSE: sin evidencia se degrada a UNRESOLVED, una señal que la
  matriz no declara se rechaza, y ninguna de las tres frases de ausencia —no se encontró un
  controlador, no hay archivo de contrato, no hay un literal de ruta— la baja a FALSE por ninguna de
  las dos clases débiles. El límite de la etiqueta queda declarado, como en D7. (D8-05)
  · rojo visto: si
- **E-09** — Ninguna otra señal de la matriz sustituye a `serviceEndpointPresent`: entregada al
  check, queda `APPLICABILITY_UNRESOLVED` con `SIGNAL_IDENTITY_MISMATCH`. · rojo visto: si

### Ningún agente, ninguna skill

- **E-10** — D8 no crea ni modifica un agente ni una skill: la fila no declara `skills`, los tres
  dueños son los que la matriz ya declaraba, siguen siendo 27 las skills instaladas, y los nombres
  que los artefactos mencionan ya están en el registro de agentes. (D8-09)
  · rojo visto: si

### Lo que no prueba nada

- **E-11** — Una dependencia de tokens en el manifiesto, sola, no da `PASS`. (D8-10)
  · rojo visto: si
- **E-12** — Un middleware de seguridad declarado, solo, no da `PASS`. (D8-11)
  · rojo visto: si
- **E-13** — La emisión de un token y un endpoint de login, solos, no dan `PASS`. (D8-12)
  · rojo visto: si
- **E-14** — Las ocho clases inertes, una por una, no dan `PASS`: incluidas el parseo del header, la
  presencia del gateway, la documentación que dice *privada* y la palabra de un agente. (§)
  · rojo visto: si

### La cobertura de endpoints

- **E-15** — Inventario incompleto —sin inventario, sin endpoints, sin fuente, con endpoints sin id,
  sin comportamiento, con una clase desconocida, con actividad sin declarar o declarado incompleto—
  deja `SERVICE_ENDPOINT_COVERAGE_UNRESOLVED`. (D8-13) · rojo visto: si
- **E-16** — Las nueve clases de camino —nombradas una por una, no leídas de la constante que el
  escenario verifica— entran en el inventario, y ninguna queda afuera de la verificación. (§)
  · rojo visto: si

### El mecanismo, que no se inventa

- **E-17** — Sin mecanismo de token declarado —o sin fuente de la lista, o sin referencia, o sin
  punto de aplicación, o en blancos—, `TOKEN_MECHANISM_UNRESOLVED`. (D8-14)
  · rojo visto: si
- **E-18** — Ninguno de los artefactos de D8 —la policy, el check, las dos filas del registro, la
  fila de la matriz y la sección de `docs/normativa-7.1.md`— nombra una tecnología de token, un
  emisor, una audiencia, un algoritmo, un claim, un tiempo de vida, un formato de header, un rol, un
  scope, una regla de refresco, un producto de gateway, un localizador de red, una ruta, un verbo
  HTTP ni un código de estado; y tampoco los lleva ningún resultado que el check produzca. Las
  quince cosas que la lista enumera tienen su patrón, **incluidos el rol y el scope**, y el barrido
  no se dispara con prosa correcta: ni con `alcance`, que es la palabra del idioma, ni con las
  formas en las que `scope` y `role` son discurso y no un valor —`In scope:`, `Out of scope:`, `the
  scope of`, `the role of`— ni con una clave estructural `scope: {`. (D8-23, D8-24)
  · rojo visto: si
- **E-19** — El código de rechazo no se exige sin contrato: con un contrato que lo define la sonda
  tiene que coincidir, sin contrato alcanza el rechazo, y el check no declara ninguna constante
  numérica. (D8-24) · rojo visto: si

### La ejecución

- **E-20** — `NO_TOKEN` alcanzando el comportamiento protegido da `FAIL`. (D8-15)
  · rojo visto: si
- **E-21** — `INVALID_TOKEN` alcanzando el comportamiento protegido da `FAIL`. (D8-16)
  · rojo visto: si
- **E-22** — `VALID_TOKEN` aporta la evidencia positiva y, con las dos negativas cubiertas y traza
  real, el endpoint da `PASS`. (D8-17) · rojo visto: si
- **E-23** — Faltando cualquiera de las dos sondas negativas, el endpoint no llega a `PASS`; y sin
  objetivo donde correr, `TEST_TARGET_UNAVAILABLE`. (§) · rojo visto: si
- **E-24** — Lo mockeado se distingue de lo real y no llega a `PASS`. (D8-25)
  · rojo visto: si

### Los bypasses

- **E-25** — Camino feliz protegido más una ruta alterna que declara que no exige token da `FAIL`,
  y el resultado nombra el comportamiento alcanzado por los dos. Una ruta alterna que **no declara**
  si exige no da `FAIL` ni `PASS`: queda `PARTIAL` con `TOKEN_REQUIREMENT_UNDECLARED`. (D8-18)
  · rojo visto: si
- **E-26** — El bypass por método alterno da `FAIL`. (D8-19) · rojo visto: si
- **E-27** — El bypass por ruta legacy y por ruta versionada se detecta. (D8-20)
  · rojo visto: si
- **E-28** — Las ocho clases que no son la primaria —nombradas una por una— fallan por igual cuando
  alcanzan un comportamiento protegido sin exigir token: es un invariante sobre el producto, no ocho
  ejemplos. (D8-18, D8-19, D8-20) · rojo visto: si
- **E-29** — Un camino declarado inactivo no es un bypass; uno que no declara su actividad no se da
  por desactivado y deja la cobertura sin resolver. (§) · rojo visto: si

### Los endpoints públicos

- **E-30** — Un endpoint declarado público sin excepción autoritativa —o con excepción sin fuente de
  la lista, sin referencia o en blancos— queda `TOKEN_PROTECTION_EXCEPTION_UNRESOLVED`. (D8-21)
  · rojo visto: si
- **E-31** — Ninguna de las siete categorías se exime sola: login, health, readiness, liveness,
  catálogo, webhook y API pública quedan sin resolver igual que cualquier otra. (D8-22)
  · rojo visto: si
- **E-32** — Ningún artefacto de D8 lleva una lista de categorías exentas ni un patrón de ruta, y el
  check no ramifica por el nombre de un endpoint. (D8-22) · rojo visto: si

### La frontera de lo que D8 afirma

- **E-33** — Un `PASS` de D8 no afirma autorización: un caso que declara los roles y los scopes sin
  verificar pasa igual, y el resultado no lleva ningún veredicto de autorización. (D8-26)
  · rojo visto: si
- **E-34** — Un `PASS` de D8 no implica D1 ni D2: no cambia su aplicabilidad, no cambia el estado de
  sus controles, y ninguna cadena que el módulo pueda producir nombra a ninguna de las dos —se
  barren **todas** sus cadenas literales, no los diez resultados de muestra—. (D8-27)
  · rojo visto: si
- **E-35** — Un `PASS` de D8 no implica ES0902 ni una aprobación de seguridad: **ninguna** cadena
  que el módulo pueda producir nombra otro estándar ni declara una aprobación —el vocabulario
  incluye *aprobación*, que es la palabra con la que está escrito el escenario, y las dos únicas
  cadenas legítimas que lo llevan adentro, una fuente de cobertura y una skill instalada, están
  nombradas una por una en vez de excluidas por su forma—. (D8-28) · rojo visto: si

### La propagación, el registro y la trazabilidad

- **E-36** — La unidad de trabajo propaga la policy y el check exactos que la matriz declara, y la
  forma vieja —booleanos— sigue funcionando. (D8-29) · rojo visto: si
- **E-37** — Después de instalar, los dos controles dejan de figurar como no instalados, son
  veintiséis los declarados, son diez las reglas con todos sus controles construidos, y no queda
  ningún archivo de control sin declarar. (D8-30) · rojo visto: si
- **E-38** — Todo resultado del check conserva `ES0901 / 6.3 / 7.1 / D8`, en todos sus caminos menos
  el del binding sin resolver, que es el único que no puede y lo dice. (D8-31)
  · rojo visto: si
- **E-39** — Los diez estados existen, se alcanzan todos, el único que aprueba es `PASS`, y ningún
  estado sin resolver se convierte en `PASS`. (§ estados) · rojo visto: si

## Cómo se verifica

Los 39 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

E-18 y E-32 tienen **tres** mitades, como el guard de D6 y el de D7: los textos limpios, las formas
de fuga **en crudo** —sin acomodarlas al patrón— y los textos legítimos que **no** tienen que
disparar. Sin la segunda, la primera se degrada en silencio el día que alguien afloje un patrón; sin
la tercera, el barrido se pone en rojo con prosa correcta y alguien lo apaga.

📌 El primer veredicto dejó cinco escenarios **sin sustento** —E-02, E-16, E-18, E-34 y E-35— y
ninguno contradicho: en los cinco el comportamiento era el que la spec pide y lo que faltaba era el
mecanismo que lo sostuviera. Las tres causas, que son las que conviene no repetir:

```
una constante que el test RECORRE en vez de clavar   E-16, y la nota de E-28
un item del escenario sin patron en el barrido       E-18: el rol y el scope
una afirmacion universal MUESTREADA sobre diez       E-34 y E-35, mas la palabra que faltaba
```

El segundo veredicto los sostuvo a los cinco y dejó dos observaciones que **también se cerraron**,
porque las dos eran de la misma familia: el patrón de `scope` se disparaba con `In scope:`, que es
prosa que este repositorio escribe todo el tiempo en sus artefactos en inglés —un barrido que falla
sin motivo es uno que alguien apaga—, y el corte de E-35 por *"tiene un espacio"* dejaba afuera los
329 literales sin espacio del módulo, que son justamente los `reason` y los `state` que un resultado
publica. Ahora las formas de discurso se sacan antes de barrer y las dos cadenas legítimas están
nombradas.

E-09, E-14, E-15, E-16, E-28, E-31, E-38 y E-39 son **invariantes sobre un producto**, no ejemplos
elegidos: recorren todas las señales de la matriz, las ocho clases inertes, las ocho formas de
inventario incompleto, las nueve clases de camino, las siete categorías que no se eximen y todos los
caminos del check. Donde la cobertura es combinatoria, el ejemplo elegido a mano es el que deja
pasar la forma que nadie pensó.

## Riesgos conocidos

- **El mecanismo del token no se puede resolver en ningún proyecto todavía.** No está en ningún
  extracto ni en el catálogo del Anexo II. En cualquier corrida real de hoy, D8 va a salir
  `TOKEN_MECHANISM_UNRESOLVED`, que es lo correcto y también significa que el check no se va a
  ejercitar de punta a punta hasta que alguien consiga ese dato.
- **El inventario de endpoints lo arma alguien, y de eso depende todo.** Un bypass que no está en el
  inventario no lo encuentra este check: lo que hace es exigir que el inventario declare de dónde
  sale y negarse a concluir cuando se declara incompleto. Es la misma deuda de G1 a D7, y lo que la
  destraba es el análisis de impacto.
- **`active` es un dato declarado.** Una ruta viva declarada inactiva sale del conjunto de bypasses
  con una afirmación de quien la declaró. Queda citada y es refutable, y el check exige que la
  declaración exista; que sea cierta no lo puede saber.
- **El harness confía en la etiqueta de la fuente.** Igual que en D7: una observación de ausencia
  etiquetada como dato estructurado apaga la regla, y `senales.py` no distingue eso de un alcance
  declarado completo. Cerrarlo pide exigir completitud de alcance para todo FALSE, cerrado hoy
  **sólo para D5**. Está dicho en `docs/normativa-7.1.md` y E-08 lo prueba en las dos direcciones.
- **`controles/` no llega a un proyecto instalado.** Con D8 son **veintiséis** controles que declaran
  `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Es el ítem 2 de la tabla
  de prioridades, tiene su propia spec, y este cambio lo empeora en dos y lo dice.
- **Tres ayudantes duplicados por tercera vez.** Normalizar un dato declarado, atar la evidencia al
  build y resolver referencias huérfanas están ahora en el check de D6, en el `lib/` de D7 y en el
  check de D8. Se anota como pendiente para `harness-staff-engineer`; unificarlos adentro de D8
  sería tocar dos cambios ya verificados.
- **Que el servicio rechace de verdad lo dice una sonda real.** Lo que este check verifica es que la
  sonda exista, esté atada al build y no venga mockeada.
