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

La resolución es genérica y hay **ocho** reglas con algoritmo propio, porque el estándar les
declara uno: C2, Ve2, Vu4, Vu9, Vu10, G2, G3 y G4. Viven juntas en `ALGORITMOS`, en un solo
lugar, para que una novena no aparezca sin que nadie la vea.

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

bin/orquestacion/seguridad.py    qué regla aplica, y con qué resultado
bin/orquestacion/evaluacion.py   en qué estado está la evaluación, y quién puede moverla
bin/orquestacion/cruzada.py      qué relación hay entre una regla de ES0901 y una de ES0902
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

1. **Treinta y ocho controles declarados y sin construir.** Es el estado correcto de un harness que clasificó antes de construir, y es
   también el hueco más grande que tuvo hasta hoy.
2. **El mapeo de severidades no lo produce nadie todavía.** Sin él, toda corrida real de G2 sale
   `VULNERABILITY_RISK_MAPPING_UNRESOLVED`.
3. **ES0901 P5 no existe.** Su equivalencia con ES0902 Vu5 queda
   `CROSS_STANDARD_CONTROL_BINDING_REQUIRED` hasta que P5 se implemente.
4. **La matriz provista declara un id con dos tipos.**
   `security-vulnerability-acceptance-threshold` sale de G2 como policy **y** como check. El
   archivo no se corrige acá —corregir normativa provista es inventarla—: se reporta
   `SECURITY_CONTROL_ID_TYPE_COLLISION` y aparece dos veces en el reporte de huecos, una por tipo.
