# D1: la primera regla condicional que necesita una señal de verdad

**Estado:** construido · **Fecha:** 2026-09-19

## Qué problema resuelve

G1 y G2 se pudieron construir porque las dos son `ALWAYS`: aplican siempre y nadie tiene que
decidir si aplican. D1 es la primera regla que se construye y **no aplica siempre**:

> "Todas las aplicaciones que requieran interactuar con el ciudadano deben contar con la
> autenticación única de ciudadano del GCABA." — ES0901 §7.1 D1, pág. 12

La matriz ya declara esa condición desde el cambio `matriz-normativa`:

```json
"applicability": {"mode": "CONDITIONAL", "signals": ["citizenFacing"]}
```

y `matriz.resolver_regla` ya sabe qué hacer con ella. Lo que no existe es **quién produce la
señal**. Hoy `plan.py` le pasa a la matriz un diccionario de booleanos que nadie llena, así que
las 16 reglas condicionales del estándar salen `APPLICABILITY_UNRESOLVED` en toda corrida real.
Es el estado honesto y es también un techo: mientras no haya productor de señales, ninguna regla
condicional puede construirse entera.

Un booleano tampoco alcanza. `{"citizenFacing": true}` no dice quién lo dijo ni contra qué, y una
regla que decide aplicar o no aplicar sobre un booleano sin respaldo se equivoca en silencio en
las dos direcciones: exige autenticación ciudadana a un backoffice, o le saca la exigencia a un
trámite del ciudadano porque nadie escribió la palabra "ciudadano" en el Jira.

Los dos controles que D1 exige —`gcba-citizen-authentication-required` y
`citizen-authentication-mechanism`— están declarados y no existen: se reportan
`DECLARED_POLICY_NOT_INSTALLED` y `DECLARED_CHECK_NOT_INSTALLED`.

## Qué queda afuera

- **`dev-miba`.** No se crea, no se instala y no se completa con información inventada. La skill
  está `DECLARED_NOT_INSTALLED` en el registro de agentes con su motivo —*"Authoritative miBA
  integration information is not available yet"*— y este cambio no lo cambia. Lo que se puede
  hacer sin material autoritativo es verificar **el mecanismo**, no la integración.
- **Los internos de miBA: client ids, claims, redirect URIs, endpoints, logout, procedimiento de
  registro, valores por ambiente.** Escribirlos sin fuente sería exactamente el error que
  `DECLARED_NOT_INSTALLED` está evitando: un archivo que se lee autoritativo y no lo es.
- **D2.** La delegación del ingreso de credenciales es otra regla, con su propia policy y su
  propio check. Que el apartado de autenticación del estándar hable de OpenID Connect no mueve esa
  verificación a D1: sería poner una obligación bajo dos dueños.
- **Los otros productores de señales.** La abstracción nace reusable —`authenticationPresent`,
  `frontendPresent`, `fileHandlingPresent`, `serviceEndpointPresent`, `databasePresent`,
  `batchProcessPresent`— y en este cambio se produce **una sola**: `citizenFacing`. Construir seis
  productores para seis reglas que no se especificaron es diseñar para casos que nadie vio.
- **Detectar `citizenFacing` leyendo el repositorio.** No hay detector. La señal entra como dato
  con su evidencia, igual que el inventario de tecnologías de G1 y que las fuentes de práctica de
  G2. Quien la produzca —el análisis de impacto, la ficha, una persona— es otro cambio.
- **Un campo `citizenFacing` en el contexto de proyecto.** Agregarlo al schema obligaría a llenarlo
  en todos los proyectos ya relevados, y el valor saldría de una inferencia invisible. La señal
  viaja con la unidad de trabajo, no con el perfil del proyecto.
- **Los otros 64 controles declarados.** Siguen declarados y sin construir.

## Las decisiones, y por qué

### La señal es un documento con evidencia, no un booleano

```json
{
  "signalId": "citizenFacing",
  "value": "TRUE",
  "evidence": [{"evidenceId": "ev-1", "sourceType": "JIRA_FICHA_DE_PROYECTO",
                "reference": "GCBA-1234", "claim": "trámite de inicio para el ciudadano"}],
  "producer": {"type": "HUMAN", "id": "..."}
}
```

Tres valores y no dos: `TRUE`, `FALSE`, `UNRESOLVED`. Un booleano no tiene dónde poner el tercero,
y el tercero es el único que la norma de la matriz obliga a distinguir.

`evidence` es obligatorio para `TRUE` y para `FALSE`. Una señal que afirma sin respaldo se degrada
a `UNRESOLVED` con `SIGNAL_EVIDENCE_MISSING`: es lo mismo que el harness ya hace con una revisión
sin fuente citada, y por la misma razón.

### La ausencia de evidencia es `UNRESOLVED`, nunca `FALSE`

Es la regla que ya sostiene `matriz.py` y se repite acá porque acá es donde se puede romper. Que
nadie haya escrito "ciudadano" en ningún lado no prueba que la aplicación no interactúe con el
ciudadano: prueba que nadie lo escribió. Convertir lo ausente en `FALSE` hace desaparecer D1 del
reporte, y una regla que desaparece no se vuelve a buscar.

La consecuencia se acepta: hoy, sin productor real, una unidad de trabajo sale con D1 sin resolver.
Ese es el estado correcto.

### Dos evidencias que se contradicen no se deciden

`SIGNAL_CONFLICT` y `UNRESOLVED`, con las dos conservadas. Elegir la que deja el plan más corto es
el sesgo más barato que puede tener un productor y no deja rastro. Es la misma decisión que
`SOURCE_CONFLICT` en las revisiones de G2.

### Lo que interpreta un modelo no pisa un dato estructurado

Las clases de fuente se parten en dos:

```text
estructuradas     TASK_CONTEXT · PROJECT_CONTEXT · REPOSITORY_CONFIGURATION · HUMAN_CONFIRMATION
interpretadas     JIRA_FICHA_DE_PROYECTO · PROJECT_DOCUMENTATION · AGENT_STATEMENT
```

Si una evidencia estructurada y una interpretada discrepan, gana la estructurada y la
interpretación queda registrada como `SIGNAL_INTERPRETATION_OVERRIDDEN`. No es un conflicto: es
una jerarquía declarada. Un modelo leyendo un PDF no revierte un campo que alguien escribió.

`AGENT_STATEMENT` sola no sostiene ningún valor. Que un agente diga que la aplicación es ciudadana
es una opinión con formato de evidencia.

### La abstracción es genérica; el productor es uno

```text
Matriz normativa      declara el id de la señal
Productor             emite TRUE/FALSE/UNRESOLVED con evidencia
Resolución            mapea a APPLICABLE / NOT_APPLICABLE / APPLICABILITY_UNRESOLVED
Policy y Check        se ejecutan despues de resolver la aplicabilidad
```

Una señal que la matriz no declara se rechaza con `SIGNAL_NOT_DECLARED`: el inventario de señales
válidas sale de la matriz, no de una lista paralela que alguien tiene que acordarse de actualizar.
Meter `citizenFacing` a mano adentro de la policy de D1 habría sido más corto y habría obligado a
escribir todo esto de nuevo para `databasePresent`.

### Los booleanos viejos siguen andando

`matriz.resolver` conserva su contrato: recibe booleanos. Lo nuevo se apoya arriba, en
`normativa.resolucion`, que acepta las dos formas. Cambiarle el tipo a un campo que alguien ya
consume es romper a distancia, y la matriz la consumen tres módulos y dos suites.

### `PARTIAL` no es un aprobado, y por eso la evidencia ausente no es `FAIL`

El check tiene cinco estados y sólo uno aprueba:

```text
PASS                        la evidencia identifica el mecanismo del GCBA
FAIL                        la evidencia muestra otra cosa: credenciales propias
PARTIAL                     hay evidencia y no alcanza para afirmar el mecanismo
NOT_APPLICABLE              citizenFacing = FALSE
APPLICABILITY_UNRESOLVED    citizenFacing = UNRESOLVED
```

Una aplicación ciudadana sin ninguna evidencia de flujo de autenticación queda `PARTIAL`, no
`FAIL`. `FAIL` es para la evidencia que contradice la regla; `PARTIAL` es para la que falta. La
distinción importa porque se resuelven con personas distintas: una la arregla quien desarrolla, la
otra la completa quien releva. Y no afloja nada, porque **ninguno de los dos es un PASS**: la única
forma de pasar D1 es mostrar el mecanismo.

### El mecanismo se verifica; la integración no

El estándar dice, en su apartado de integraciones (§8, pág. 18): *"Toda aplicación que genere una
interacción con el ciudadano debe contar con la autenticación con BAID en su frontend"*, y que miBA
provee ese servicio *"siguiendo las especificaciones de OpenID Connect"*. Eso alcanza para
preguntar **si el flujo ciudadano usa el mecanismo del GCBA**. No alcanza para verificar cómo está
integrado, y este cambio no lo promete.

📌 El pedido de instalación nombra la sección de apoyo como `8.2 Authentication`. El extracto
normativo del repositorio sostiene `§8`, pág. 18, y no sostiene el `.2`. Se declara `"8"` con la
página: un número de sección inventado es una cita falsa igual que un texto inventado.

### Autenticación institucional no es autenticación ciudadana

El mismo apartado, una página después, manda lo contrario para lo que no es ciudadano: Active
Directory y Keycloak vía el OpenID de la DGSEI. Son dos mecanismos distintos para dos públicos
distintos. Un flujo institucional en una aplicación ciudadana no satisface D1 y tampoco lo viola
por sí solo: no es evidencia del flujo ciudadano, y se ignora para esta regla.

### La remediación que necesita miBA se declara, no se improvisa

Cuando D1 no pasa y arreglarlo exige saber cómo se integra miBA, el resultado expone
`SPECIALIZED_SKILL_GAP` con la skill que falta. El estado ya existe en el registro de agentes desde
`agent-registry` y no se inventa uno nuevo. 🔴 **Eso no hace cumplir a D1**: el hueco es visible y
el control sigue sin pasar.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/normative-signal.schema.json` | El contrato de una señal: id, valor, evidencia y productor |
| `harnesses/desarrollo/bin/orquestacion/senales.py` | Valida señales, resuelve su valor contra la evidencia y las mapea a aplicabilidad. Genérico: la señal válida es la que declara la matriz |
| `harnesses/desarrollo/controles/policies/gcba-citizen-authentication-required.md` | El contrato de la policy de D1 |
| `harnesses/desarrollo/controles/checks/citizen-authentication-mechanism.py` | El check: evalúa el mecanismo del flujo ciudadano contra la evidencia |
| `harnesses/desarrollo/reglas/control-registry.json` | Suma los dos controles de D1, sin tocar la fila de la matriz |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `resolucion` acepta señales con evidencia además de booleanos |
| `harnesses/desarrollo/bin/orquestacion/plan.py` | La unidad propaga el valor y la evidencia de cada señal |
| `comun/schemas/orchestration-plan.schema.json` | `normative.signals` en la unidad de trabajo |
| `docs/orquestacion.md` | La sección de señales normativas |
| `docs/normativa-7.1.md` | Qué controles existen y qué es una señal desde D1 |
| `tests/casos/26_d1_autenticacion_ciudadana.py` | Los escenarios de este cambio |

## Escenarios verificables

Entre paréntesis, el `D1-nn` del pedido de instalación.

### La señal y su contrato

- **E-01** — `D1` sigue siendo `CONDITIONAL` y su única señal declarada es `citizenFacing`; la fila
  de la matriz no cambia. (D1-01) · rojo visto: si
- **E-02** — Una señal bien formada valida contra su schema, y el schema entra en el subconjunto
  soportado por el validador del harness. · rojo visto: si
- **E-03** — `citizenFacing = TRUE` con evidencia deja `D1` en `applicableRules`. (D1-02)
  · rojo visto: si
- **E-04** — `citizenFacing = FALSE` con evidencia deja `D1` en `notApplicableRules`. (D1-03)
  · rojo visto: si
- **E-05** — Sin señal de `citizenFacing`, `D1` queda en `unresolvedRules` con
  `APPLICABILITY_UNRESOLVED` y la señal que falta escrita al lado. (D1-04)
  · rojo visto: si
- **E-06** — Una señal `UNRESOLVED` no se convierte en `FALSE`: `D1` no aparece en
  `notApplicableRules` en ningún camino. (D1-05) · rojo visto: si
- **E-07** — El resultado de la señal conserva sus referencias de evidencia: `sourceType`,
  `reference` y `claim` de cada una. (D1-06) · rojo visto: si
- **E-08** — Una señal `TRUE` sin ninguna evidencia no afirma: queda `UNRESOLVED` con
  `SIGNAL_EVIDENCE_MISSING`. Lo mismo una `FALSE`. (D1-06) · rojo visto: si
- **E-09** — Dos evidencias que afirman lo contrario dan `SIGNAL_CONFLICT` y `UNRESOLVED`, con las
  dos conservadas. · rojo visto: si
- **E-10** — Una evidencia interpretada que contradice a una estructurada no la pisa: gana la
  estructurada y queda `SIGNAL_INTERPRETATION_OVERRIDDEN`. · rojo visto: si
- **E-11** — Una señal cuyo id la matriz no declara se rechaza con `SIGNAL_NOT_DECLARED` y no entra
  en la resolución. · rojo visto: si
- **E-12** — La abstracción no es de `citizenFacing`: la misma función produce otra señal declarada
  por la matriz —`databasePresent`— y mueve la aplicabilidad de `P7` sin una línea específica de
  esa señal. · rojo visto: si
- **E-13** — Las señales booleanas que ya consume `matriz.resolver` siguen funcionando igual.
  · rojo visto: si

### El check

- **E-14** — Aplicación ciudadana cuyo flujo identifica el mecanismo de autenticación ciudadana del
  GCBA, con evidencia del proyecto: `PASS`. (D1-07) · rojo visto: si
- **E-15** — Aplicación ciudadana con un login de credenciales propias para el ciudadano: `FAIL`.
  (D1-08) · rojo visto: si
- **E-16** — Aplicación ciudadana con evidencia incompleta del proveedor: `PARTIAL`, y `PARTIAL` no
  es un aprobado. (D1-09) · rojo visto: si
- **E-17** — Aplicación interna, de backoffice o de uso de empleados: `NOT_APPLICABLE`. (D1-10)
  · rojo visto: si
- **E-18** — Señal sin resolver: el check devuelve `APPLICABILITY_UNRESOLVED` y no evalúa nada.
  (D1-04) · rojo visto: si
- **E-19** — Autenticación institucional —Active Directory, Keycloak de la DGSEI— sola no satisface
  D1: no llega a `PASS` y el motivo lo dice. (D1-11) · rojo visto: si
- **E-20** — Que exista una dependencia de OIDC en el repositorio no satisface D1: el mecanismo del
  flujo queda sin identificar. (D1-12) · rojo visto: si
- **E-21** — La afirmación de un agente, sola, no satisface D1. (D1-13)
  · rojo visto: si
- **E-22** — Evidencia que pertenece a otra aplicación o a otro ambiente no sostiene el `PASS`.
  · rojo visto: si
- **E-23** — De los cinco estados del check, `PASS` es el único que aprueba; los otros cuatro no se
  reportan como cumplimiento en ningún camino. · rojo visto: si

### Las fronteras

- **E-24** — D1 no mira la delegación del ingreso de credenciales: un flujo con el mecanismo
  correcto pasa D1 aunque no haya nada declarado sobre delegación, y el resultado de D1 no emite
  ningún veredicto de D2. (D1-14) · rojo visto: si
- **E-25** — Que `dev-miba` esté `DECLARED_NOT_INSTALLED` no invalida la instalación estructural de
  los controles de D1: los dos figuran `INSTALLED` en el registro. (D1-15)
  · rojo visto: si
- **E-26** — Una remediación que exige conocimiento específico de miBA devuelve
  `SPECIALIZED_SKILL_GAP` con la skill nombrada, y el resultado de D1 sigue sin cumplir. (D1-16)
  · rojo visto: si
- **E-27** — Nada de D1 crea `dev-miba`: ni el archivo de la skill ni una entrada nueva en el
  registro de agentes. (D1-17) · rojo visto: si
- **E-28** — Los artefactos de D1 no traen client ids, claims, redirect URIs, endpoints, URLs de
  proveedor ni configuración por ambiente. · rojo visto: si

### La propagación y la instalación

- **E-29** — La unidad de trabajo lleva en su bloque normativo el valor, el estado y la evidencia de
  `citizenFacing`, sin cambiarle el tipo a `applicableRules`, `declaredPolicies`, `declaredChecks`
  ni `declaredReviews`, y el plan valida contra su schema. (D1-18) · rojo visto: si
- **E-30** — Antes de instalar, la policy y el check de D1 son `DECLARED_POLICY_NOT_INSTALLED` y
  `DECLARED_CHECK_NOT_INSTALLED`; después desaparecen de la lista de faltantes **sin tocar la
  definición de la regla en la matriz**. (D1-19) · rojo visto: si
- **E-31** — Todo resultado de D1 —señal, policy y check— conserva la tupla
  `ES0901 / 6.3 / 7.1 / D1`. (D1-20) · rojo visto: si

## Cómo se verifica

Los 31 pasan por la suite, en `tests/casos/26_d1_autenticacion_ciudadana.py`. Ninguno necesita
lectura: todo lo que se afirma es estructura, estado y trazabilidad, y nada de eso depende de una
corrida de un modelo.

Las señales, las evidencias y los flujos de los casos se arman en memoria. Lo único que se lee del
árbol es lo que ya está versionado —la matriz, el registro de controles y el registro de agentes—.
Ningún caso escribe en el árbol.

E-28 se verifica en dos mitades. La primera corre los patrones sobre los dos archivos de D1. La
segunda prueba que esos patrones sirvan: inyecta una fuga de cada una de las seis clases —client
id, claim, redirect URI, endpoint, URL de proveedor y configuración por ambiente— y exige que cada
una ponga el caso rojo. Sin esa segunda mitad, E-28 afirma seis clases y patrulla las que alguien
se acordó de escribir; fue lo que el primer veredicto marcó `sin sustento`. Los patrones de forma
de dato van anclados a principio de línea porque los propios artefactos nombran esas palabras en
prosa para negarlas, y un patrón literal se pondría rojo contra el descargo en vez de contra una
fuga.

## Riesgos conocidos

- **Nadie produce señales todavía.** La abstracción existe y no hay quien la alimente. Una unidad
  real sigue saliendo con D1 sin resolver hasta que el análisis de impacto las complete. Se gana el
  camino, no el dato.
- **La evidencia válida no es evidencia buena.** Una referencia a un Jira que no dice lo que el
  `claim` afirma valida igual. Lo que compra el contrato es que la referencia esté escrita y se
  pueda discutir, no que sea cierta.
- **`PARTIAL` puede volverse el estado cómodo.** Es el que no obliga a nada. Si con el tiempo todo
  termina en `PARTIAL`, el check deja de distinguir una aplicación que cumple de una que nadie
  miró. Lo que lo contiene es que `PARTIAL` no aprueba; lo que no lo contiene es nada.
- **La jerarquía estructurada > interpretada supone que lo estructurado está bien.** Un campo mal
  cargado en el contexto de proyecto le gana a una lectura correcta de la ficha. Es la dirección
  menos mala de las dos, y es una decisión, no una verdad.
- **D1 sin `dev-miba` verifica el mecanismo y nada más.** Una aplicación puede pasar D1 declarando
  que usa el mecanismo del GCBA y tener la integración mal hecha. Ese hueco es explícito y sólo lo
  cierra el material autoritativo que todavía no existe.
