# ES0902 C2 — la aprobación de seguridad en QA, atada al artefacto y revalidada por el Anexo V

**Estado:** verificado y cerrado · **Fecha:** 22-09-2026 · **Regla:** ES0902 6.2 §3 C2 · ES0901 6.3 Anexo V

## Qué problema resuelve

> `ES0902-3-C2` — *"Las aplicaciones homologadas deben tener el aprobado a nivel seguridad en el
> ambiente QA."*

Y el Anexo V de ES0901 (pág. 42) le da el contexto operativo: el assessment de seguridad es
obligatorio antes de HML y PRD, se hace en QA, y **se repite** cuando hay desarrollo y pasaron más
de 20 días, cuando se corrigen vulnerabilidades (assessment parcial), cuando hay un incidente de
seguridad, o cuando hay un desarrollo con cambios en funcionalidades o endpoints — con cinco
familias de motivos que lo piden.

Hoy C2 tiene algoritmo propio en `evaluacion.regla_c2`: exige que la declaración sea `QA` y que el
estado oficial sea `APPROVED` con procedencia externa, y después cae en el camino genérico. Sus dos
controles —`qa-security-approval-required` y `qa-security-approval-evidence`— están declarados y
**no existen**, así que C2 no cumple nunca, que es lo correcto. Lo que no puede hacer es decir si una
aprobación **sigue valiendo para lo que se va a promover**:

```
una aprobación de QA de marzo            ¿es de esta aplicación?
                                         ¿de este commit, de este build, de esta imagen?
                                         ¿qué cambió desde entonces, y alguno de esos cambios
                                          es un motivo del Anexo V?
                                         ¿era un assessment parcial de una remediación?
                                         ¿el archivo que se consumió es el mismo que hay hoy?
```

Y hay cinco formas baratas de ponerla en verde que este cambio cierra: que la emita algo interno
(el agente, una skill, un escáner, el CI, un check del harness); que valga una aprobación de otro
ambiente; que valga la de otro release porque el repositorio, la rama o la versión se parecen; que
una aprobación vieja se reuse sin mirar qué cambió; y que un assessment parcial se lea como total.

## Qué queda afuera

- **Una aprobación precargada.** `security-approval-evidence.json` se instala **vacío**, como los
  otros tres registros del proyecto. No hay en el repositorio un almacén equivalente con el que
  integrarlo.
- **Un segundo productor de la señal.** `securityHomologationPresent` ya la declara la matriz y la
  resuelve el runtime genérico de señales. No se escribe un detector nuevo: el check la recibe.
- **Resolver la autoridad organizacional otra vez.** Eso es O2. El check de C2 **recibe** el
  resultado de `security-control-authority-evidence` y lo usa como contexto de procedencia.
- **Calcular el umbral de G2.** C2 no mira cantidades de hallazgos ni severidades. Un
  `G2_THRESHOLD_SATISFIED` no entra a ninguna decisión.
- **La excepción del hotfix.** ES0901 pág. 29 dice que a un hotfix se le hace el assessment *a
  posteriori* del despliegue productivo, y el Anexo V no la contempla: es la contradicción interna 2
  del extracto. No se resuelve acá; un hotfix se evalúa como cualquier otra versión y la
  contradicción queda anotada.
- **Una review.** La matriz declara cero y así sigue.
- **Un agente o una skill.** `dev-security` coordina y no emite aprobaciones.
- **Escribir sobre la evidencia.** El check calcula la huella de lo que consume y compara contra la
  huella que se le pasa; no guarda nada ni reescribe el registro.

## Las decisiones, y por qué

### El registro es del proyecto, se instala vacío, y su schema se cierra

Como el de O2 y el inventario de C1: el schema provisto se instala con `additionalProperties: false`
en el documento, en la aprobación y en el artefacto. Una clave de más que se acepta en silencio es
un campo que alguien termina leyendo como evidencia. `provenanceClass` sólo admite
`EXTERNAL_GCABA_SECURITY_AUTHORITY` o `UNRESOLVED`: un productor interno **no tiene cómo escribirse**
en el registro, y si se escribe como `UNRESOLVED` no aprueba.

### Decide la aprobación más reciente del sujeto, y la de otro sujeto es `FAIL`

El candidato trae `projectId`, `applicationId`, `scope` y su identidad de artefacto. De las
aprobaciones del registro se toman las del mismo proyecto y la misma aplicación, y decide **la más
reciente** por `assessmentDate` (empate: `approvalId`). Una vieja no puede tapar a una nueva: si la
última fue `REJECTED`, una anterior `APPROVED` no la revive.

Si hay aprobaciones y ninguna es del sujeto, es `FAIL`: la evidencia consta y es de otro. Si no hay
ninguna, `SECURITY_APPROVAL_REQUIRED`. Sin identidad del candidato, `SECURITY_APPROVAL_SCOPE_UNRESOLVED`.

### La procedencia se ata a O2 por id

La aprobación sostiene su autoridad cuando se dan las tres cosas: `provenanceClass` es
`EXTERNAL_GCABA_SECURITY_AUTHORITY`, O2 está en `PASS` para ese alcance, y `authorityEvidence` cita
el `authorityId` de la autoridad que O2 resolvió. Si falta cualquiera,
`SECURITY_APPROVAL_AUTHORITY_UNRESOLVED`.

Es la forma de reusar O2 sin reimplementarlo: O2 dice qué organismo del GCABA controla la seguridad
de ese alcance, y C2 exige que la aprobación venga de él. Y la frontera se sostiene en las dos
direcciones: O2 en `PASS` sin aprobación es `SECURITY_APPROVAL_REQUIRED`.

### El ambiente: QA, otro, o no se sabe

```
QA                        sigue
DEV · HML · PRD · OTHER   SECURITY_APPROVAL_NOT_IN_QA
UNRESOLVED o cualquier    SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED
  otra cosa
```

Y `evaluacion.regla_c2` —el algoritmo de la regla, que ya existía— se alinea a los mismos dos
nombres. Emitía `SECURITY_APPROVAL_OUTSIDE_QA` para todo lo que no fuera `QA`, incluido no saberlo.
Dos nombres para lo mismo en el mismo resultado es cómo alguien termina filtrando por uno solo.

### El estado: sólo `APPROVED` sigue; `REJECTED` es `FAIL`

`REJECTED` es un hecho declarado por la autoridad y es `FAIL`. `OFFICIAL_STATUS_UNRESOLVED` es
`SECURITY_APPROVAL_EVIDENCE_UNRESOLVED`. Ningún resultado interno —`INTERNAL_REVIEW_COMPLETE`,
`READY_TO_REQUEST`, `READY_TO_RESUBMIT`, `G2_THRESHOLD_SATISFIED`, un escaneo limpio, un CI verde—
es un valor del enum, y si llegan en el caso se ignoran.

### El alcance: la aprobación tiene que cubrir lo que se promueve

`approval.scope` no puede estar vacío, y el `scope` del candidato tiene que estar contenido en él.
Si no, `SECURITY_APPROVAL_SCOPE_UNRESOLVED`.

### La relación con el artefacto se resuelve con identificadores inmutables

Cinco identificadores cuentan: `commitSha`, `buildId`, `artifactDigest`, `imageDigest`, `releaseId`.
El repositorio y la rama **no**: se informan y no deciden.

```
comparten al menos uno, y ninguno compartido difiere       EXACT
comparten y alguno difiere, con un change set completo
  que va del artefacto aprobado al candidato:
    sin motivo del Anexo V                                 DESCENDANT_WITH_NO_REASSESSMENT_TRIGGER
    con motivo                                             SUPERSEDED_BY_CHANGE
cualquier otra cosa                                        UNRESOLVED -> SECURITY_APPROVAL_ARTIFACT_UNRESOLVED
```

Si la cadena del change set consta y lo que falta es del Anexo V —un cambio sin clasificar, la edad
sin contexto—, decide el estado del resolvedor y no el del artefacto: es el que sabe decir **qué**
falta.

Que dos identificadores compartidos se contradigan —mismo commit, otro digest— no es `EXACT`.

### El resolvedor del Anexo V devuelve el conjunto de motivos, no un booleano

Recibe lo que pasó desde el assessment —cambios y eventos, cada uno con su categoría y su
evidencia— y devuelve los dieciocho tipos de motivo que el paquete deriva del Anexo V, **todos los
que apliquen**, con la evidencia de cada uno:

```
REUSE_ALLOWED                   el change set está completo y ningún motivo aplica
REASSESSMENT_REQUIRED           al menos uno aplica  -> SECURITY_REASSESSMENT_REQUIRED
ASSESSMENT_VALIDITY_UNRESOLVED  falta saber algo     -> el estado de lo que falta
```

Un cambio o evento con fecha anterior o igual al assessment no es un motivo: ya lo vio. Sin fecha,
cuenta.

Una categoría fuera de la lista, o ninguna, es `ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED`. Y
`NOT_A_TRIGGER` —decir que un cambio no es motivo— sólo vale si lo clasificó algo determinista o una
persona: **una clasificación de un modelo no puede suprimir un motivo**, y cuando lo intenta queda
sin clasificar.

`REUSE_ALLOWED` no es una aprobación: dice que no se encontró motivo en evidencia completa.

### Los 20 días van con el desarrollo

El Anexo V no dice que las aprobaciones vencen a los 20 días: dice *"haya un desarrollo y
transcurran más de 20 días"*.

```
hubo desarrollo y pasaron más de 20 días      DEVELOPMENT_OVER_20_DAYS
no hubo desarrollo y pasaron más de 20 días   no es motivo
no se sabe si hubo desarrollo, y pasaron > 20 ASSESSMENT_AGE_CONTEXT_UNRESOLVED
hubo desarrollo y las fechas no se leen       ASSESSMENT_AGE_CONTEXT_UNRESOLVED
declara que no hubo y trae cambios            ASSESSMENT_AGE_CONTEXT_UNRESOLVED
```

Un change set con cambios es desarrollo aunque no lo diga. Las fechas son `YYYY-MM-DD`.

### Un assessment parcial no aprueba el release entero

`assessmentType: PARTIAL` —o ausente, o `UNRESOLVED`— exige una cobertura explícita: una entrada de
`partialCoverage` para esa aprobación, de procedencia externa, con referencia, que nombre un
identificador inmutable del candidato. Sin eso, `PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED`. Sólo `FULL`
no la necesita.

### La huella de lo consumido

El check calcula `sha256` sobre la aprobación consumida serializada con claves ordenadas, y la
devuelve con `approvalId` y `evidenceReference`. Si el caso trae la huella de una decisión anterior
para esa aprobación y no coincide, `SECURITY_APPROVAL_EVIDENCE_CHANGED`: hay que volver a evaluar.

### La unidad de trabajo lleva referencias, no contenido

`normativa.resolucion` acepta, además de las señales, el resultado del check de C2, y pone en
`standards.ES0902.rules.C2` la aplicabilidad, el resultado, la referencia y la huella de la
aprobación, la relación con el artefacto, el resolvedor —`required` y los motivos— y los ids de la
evidencia. No copia el registro ni la evidencia. Sin resultado, el bloque queda sin resolver. Lo de
arriba del bloque y `seguridad.resolver` no cambian de forma.

### Lo que no tiene la forma declarada no cuenta, y lo que puede decir que no, no se descarta

Heredado de C1, donde costó ocho pases del refutador. El registro pasa por su schema; lo demás que
entra por el caso —el candidato, los cambios, las coberturas— se controla en el check:

- un cambio mal formado —sin categoría de texto, sin evidencia, con un campo de otra forma— sigue
  siendo un cambio, **no se puede suprimir**, y queda `ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED`;
  `changes` que no es una lista, también;
- una cobertura parcial mal formada no cubre nada;
- un `scope` del candidato que no es una lista de textos no es un alcance;
- toda lista de la salida —los motivos, la evidencia, las observaciones— sale ordenada por su
  contenido.

### Lo que el primer pase del refutador cerró

El primer pase contradijo tres escenarios y encontró seis casos más de la misma clase —algo que
puede decir que no llega ilegible y se pierde—. Se cerraron todos con la misma regla:

- **Las fechas de todas las aprobaciones del sujeto** tienen que leerse, no sólo la elegida: una
  rechazada más nueva con la fecha mal escrita se ordenaba por texto y la vieja aprobaba (E-24).
- **Un `development` que no es `true`, `false` o nulo** es no saber si hubo desarrollo, comparado
  por identidad porque `1 == True` en Python (E-26). Y **otro commit es desarrollo**: declarar que
  no hubo y no listar cambios esquivaba los 20 días. Una evaluación anterior al assessment no es
  una edad.
- **Dos aprobaciones del mismo día, o con el mismo id,** no se eligen por orden de entrada ni por
  el texto del id (E-55).
- **O2 en `PASS` tiene que ser de este alcance**: la cabeza de su cadena —el alcance que O2
  evaluó— es la aplicación del candidato como `APPLICATION` o su proyecto como `PROJECT`. Un O2 de
  otro proyecto, de la aplicación hermana, uno cuya cadena contradice el proyecto del candidato,
  o uno torcido, no es procedencia (E-13, segundo y tercer pase).
- **Una aprobación del sujeto escrita de otra forma** —un espacio invisible, un acento, otro
  separador— se reconoce por su forma canónica y deja todo sin resolver: podía ser la rechazada más
  nueva (E-24, tercer pase). La forma canónica sólo sirve para fallar cerrado, nunca para aceptar
  un id en lugar de otro.
- **La unidad copia la referencia con sus tres campos de texto** y nada más (E-56, tercer pase).
- **La decisión anterior**, si viene y no se lee, obliga a volver a evaluar (E-54).
- **Una cobertura parcial** sigue la misma regla que el artefacto: un commit ajeno al lado de un
  release igual no cubre (E-49).
- **Un alcance hecho de textos vacíos** no cubre nada (E-20).
- **La unidad de trabajo** sólo proyecta un resultado que dice ser del check de C2 y no trae un
  estado oficial; si la regla no aplica o no se sabe, el resultado es ese (E-56).
- **Una entrada de otra forma no rompe**: `internalResults` que no es una lista, un O2 con la
  autoridad como texto, una evidencia de la unidad que no es un diccionario.

### El orden de las preguntas

Señal · registro · sujeto · campos · procedencia · ambiente · estado · alcance · artefacto ·
Anexo V · parcial · huella. El primer filtro que no pasa decide el estado; los motivos del Anexo V
se informan enteros aunque decida otro.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/security-approval-evidence.json` | El registro del proyecto, instalado vacío |
| `comun/schemas/security-approval-evidence.schema.json` | Su contrato, el provisto con `additionalProperties: false` en las tres capas |
| `harnesses/desarrollo/reglas/es0902-c2-governance.md` | El paquete de gobierno, como vino |
| `harnesses/desarrollo/reglas/es0902-c2-security-homologation-present-signal.md` | La señal, como vino |
| `harnesses/desarrollo/reglas/es0902-c2-assessment-validity-resolver.md` | El resolvedor del Anexo V, como vino |
| `harnesses/desarrollo/controles/policies/qa-security-approval-required.md` | La policy |
| `harnesses/desarrollo/controles/checks/qa-security-approval-evidence.py` | El check y el resolvedor |
| `harnesses/desarrollo/bin/orquestacion/evaluacion.py` | `regla_c2` con los dos nombres; la proyección para la unidad |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` · `plan.py` | `rules.C2` en el bloque de la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles, declarados |
| `docs/seguridad-es0902.md` | C2 |
| `tests/casos/42_es0902_c2_aprobacion_en_qa.py` | Los escenarios |

La matriz no se toca y `ALGORITMOS` tampoco: C2 ya estaba en él.

Se reescriben: 38 → 40 controles en `31_d6/E-30`, `32_d5/E-36`, `33_bases/E-32`, `34_d7/E-42`,
`35_d8/E-37`, `36_p1/E-39`, `37_es0902/E-13` y `E-14`, `39_es0902_o1/E-28`, `40_es0902_o2/E-28`;
los de forma singular —32 → 34— en `37_es0902/E-13`; los checks en disco —15 → 16— en
`39_es0902_o1/E-04`; los huecos —31 → 29— en `37_es0902/E-70`, `39_es0902_o1/E-28`,
`40_es0902_o2/E-28`; y el estado fuera de QA en `37_es0902/E-29`.

## Escenarios verificables

`E-nn` es `C2-nn` del pedido.

### La fila

- **E-01** — La clave es exactamente `ES0902.C2`, en la matriz y en el resultado del check. · rojo visto: si
- **E-02** — La única señal es exactamente `securityHomologationPresent`, y el check pregunta por
  ella. · rojo visto: si
- **E-03** — El agente es exactamente `dev-security`, la policy `qa-security-approval-required` y el
  check `qa-security-approval-evidence`. · rojo visto: si
- **E-04** — Ningún agente, skill ni review nuevos: diez agentes, las mismas skills, cero reviews en
  la fila. · rojo visto: si
- **E-05** — Sin la señal, `APPLICABILITY_UNRESOLVED`, en la matriz y en el check. · rojo visto: si
- **E-06** — Con la señal en falso, `NOT_APPLICABLE`, en la matriz y en el check. · rojo visto: si
- **E-07** — Que falte la aprobación no vuelve falsa la aplicabilidad: con la señal en verdadero y
  el registro vacío el resultado es `SECURITY_APPROVAL_REQUIRED`, no `NOT_APPLICABLE`. · rojo visto: si

### Nada interno aprueba

- **E-08** — Una aprobación de `dev-security` no aprueba: no se puede escribir su procedencia, y
  escrita como `UNRESOLVED` queda `SECURITY_APPROVAL_AUTHORITY_UNRESOLVED`; y `estado_oficial` con
  `DEV_SECURITY_AGENT` no llega a `APPROVED`. · rojo visto: si
- **E-09** — Un escaneo limpio no aprueba: como resultado interno no cambia nada, y
  `AUTOMATED_SCAN` no emite `APPROVED`. · rojo visto: si
- **E-10** — Un CI en verde no aprueba: como resultado interno no cambia nada, y la procedencia no
  admite escribirlo; y resultados internos que no vienen como lista no rompen el check. · rojo visto: si
- **E-11** — `READY_TO_REQUEST` no satisface C2, ni como estado de la aprobación ni como resultado
  interno. · rojo visto: si
- **E-12** — `G2_THRESHOLD_SATISFIED` solo no satisface C2, y el módulo no mira hallazgos. · rojo visto: si
- **E-13** — Hace falta procedencia externa: sin `EXTERNAL_GCABA_SECURITY_AUTHORITY`, sin O2 en
  `PASS` para este alcance, o sin citar la autoridad de O2, `SECURITY_APPROVAL_AUTHORITY_UNRESOLVED`;
  un O2 de otro alcance —otro proyecto, o la aplicación hermana del mismo— o torcido tampoco es
  procedencia: cuenta el alcance que O2 evaluó, con su tipo. · rojo visto: si

### QA

- **E-14** — Una aprobación oficial en QA sigue: con todo lo demás en regla, `PASS`. · rojo visto: si
- **E-15** — En DEV, `SECURITY_APPROVAL_NOT_IN_QA`. · rojo visto: si
- **E-16** — En HML, `SECURITY_APPROVAL_NOT_IN_QA`. · rojo visto: si
- **E-17** — En PRD, `SECURITY_APPROVAL_NOT_IN_QA`, también en el algoritmo de la regla. · rojo visto: si
- **E-18** — Con el ambiente sin resolver, `SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED`, en el check y
  en el algoritmo de la regla. · rojo visto: si

### El sujeto y el artefacto

- **E-19** — Una aprobación de otro proyecto o de otra aplicación es `FAIL`. · rojo visto: si
- **E-20** — Con el alcance de la aprobación vacío o hecho de textos vacíos, o sin cubrir el del
  candidato, `SECURITY_APPROVAL_SCOPE_UNRESOLVED`. · rojo visto: si
- **E-21** — La rama sola no alcanza: con la misma rama y el mismo repositorio y ningún
  identificador inmutable compartido, `SECURITY_APPROVAL_ARTIFACT_UNRESOLVED`. · rojo visto: si
- **E-22** — El mismo commit, o el mismo digest, establece `EXACT`; dos compartidos que se
  contradicen no. · rojo visto: si
- **E-23** — Sin relación resoluble —otro commit y sin change set completo—,
  `SECURITY_APPROVAL_ARTIFACT_UNRESOLVED`. · rojo visto: si
- **E-24** — Una aprobación vieja no se reusa a ciegas: otro commit con un change set que trae un
  motivo es `SUPERSEDED_BY_CHANGE` y `SECURITY_REASSESSMENT_REQUIRED`; una aprobación anterior no
  tapa a una más reciente rechazada; y una del sujeto con la fecha ilegible, o una que es del
  sujeto escrita de otra forma —igual una vez que se le sacan acentos, caracteres de formato, caja y
  separadores—, deja todo en `SECURITY_APPROVAL_EVIDENCE_UNRESOLVED`. · rojo visto: si

### Los motivos del Anexo V

- **E-25** — Desarrollo y más de 20 días: `DEVELOPMENT_OVER_20_DAYS`. · rojo visto: si
- **E-26** — Más de 20 días sin desarrollo no es motivo; sin saber si hubo desarrollo —o con un
  valor de `development` que no se reconoce—, `ASSESSMENT_AGE_CONTEXT_UNRESOLVED`; otro commit es
  desarrollo aunque el change set venga vacío; y una evaluación anterior al assessment no es una
  edad. · rojo visto: si
- **E-27** — Remediación de vulnerabilidades: `VULNERABILITY_REMEDIATION`. · rojo visto: si
- **E-28** — Incidente de seguridad: `SECURITY_INCIDENT`. · rojo visto: si
- **E-29** — Cambio de funcionalidad: `FUNCTIONALITY_CHANGED`. · rojo visto: si
- **E-30** — Endpoint agregado o modificado: `ENDPOINT_ADDED_OR_MODIFIED`. · rojo visto: si
- **E-31** — Parámetro de formulario o API: `FORM_OR_API_PARAMETER_CHANGED`. · rojo visto: si
- **E-32** — Integración externa o webhook: `EXTERNAL_INTEGRATION_CHANGED`. · rojo visto: si
- **E-33** — Iframe o embed: `IFRAME_OR_EXTERNAL_EMBED_ADDED`. · rojo visto: si
- **E-34** — Script de terceros: `THIRD_PARTY_SCRIPT_ADDED`. · rojo visto: si
- **E-35** — CORS, CSP o cookies: `SECURITY_POLICY_CHANGED`. · rojo visto: si
- **E-36** — Roles o permisos: `ROLE_OR_PERMISSION_CHANGED`. · rojo visto: si
- **E-37** — Dependencia, framework o SDK: `DEPENDENCY_CHANGED`. · rojo visto: si
- **E-38** — Migración de infraestructura: `INFRASTRUCTURE_MIGRATED`. · rojo visto: si
- **E-39** — Protocolo de comunicación: `COMMUNICATION_PROTOCOL_CHANGED`. · rojo visto: si
- **E-40** — Carga o descarga de archivos: `FILE_UPLOAD_OR_DOWNLOAD_ADDED`. · rojo visto: si
- **E-41** — Flujo sensible: `SENSITIVE_FLOW_CHANGED`. · rojo visto: si
- **E-42** — Flujo de autenticación: `AUTHENTICATION_FLOW_CHANGED`. · rojo visto: si

  Del E-25 al E-42 cada motivo se prueba **desde el caso que aprueba**: con él, `PASS` pasa a
  `SECURITY_REASSESSMENT_REQUIRED` y el motivo sale con su evidencia. Los dieciocho, y
  `FRONTEND_OR_BACKEND_SECTION_REMOVED` también, aunque el pedido no le puso número.

- **E-43** — Varios motivos salen todos, cada uno con su evidencia, no un booleano. · rojo visto: si
- **E-44** — Una categoría ambigua o ausente es `ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED`. · rojo visto: si
- **E-45** — Una clasificación de un modelo no suprime un motivo: `NOT_A_TRIGGER` de un modelo queda
  sin clasificar, y de una persona o de algo determinista vale. · rojo visto: si
- **E-46** — Con evidencia completa y ningún motivo, `REUSE_ALLOWED`; sin evidencia completa, no. · rojo visto: si

### Parcial, límites, huella y traza

- **E-47** — Un assessment parcial no aprueba un release cambiado: parcial sin cobertura y con
  cambios, no `PASS`. · rojo visto: si
- **E-48** — Parcial, o sin tipo, sin cobertura explícita: `PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED`. · rojo visto: si
- **E-49** — Parcial con cobertura oficial que nombra al candidato sigue: `PASS`; una cobertura
  cuyos identificadores se contradicen con el candidato, o mal formada, no cubre. · rojo visto: si
- **E-50** — O2 en `PASS` no es C2 en `PASS`: sin aprobación, `SECURITY_APPROVAL_REQUIRED`. · rojo visto: si
- **E-51** — C2 en `PASS` no pone ninguna regla Vu en cumplimiento. · rojo visto: si
- **E-52** — C2 en `PASS` no es aprobación de despliegue a producción: ninguna salida la nombra y
  ningún valor es un estado oficial de `evaluacion`. · rojo visto: si
- **E-53** — Lo consumido sale con su huella `sha256`, su id y su referencia, y la huella cambia si
  la aprobación cambia. · rojo visto: si
- **E-54** — Con la huella de una decisión anterior que no coincide, o una decisión anterior que
  no se puede leer, `SECURITY_APPROVAL_EVIDENCE_CHANGED`; y el módulo no escribe archivos. · rojo visto: si
- **E-55** — La misma evidencia da el mismo resultado, en cualquier orden; y dos aprobaciones
  del mismo día o con el mismo id no se eligen: `SECURITY_APPROVAL_EVIDENCE_UNRESOLVED`. · rojo visto: si
- **E-56** — El resultado conserva `ES0902 / 6.2 / §3 / C2` y `ES0901 / 6.3 / Anexo V` por todos los
  caminos, y la unidad de trabajo lleva `rules.C2` con referencias y sin el registro; la unidad no
  proyecta un estado oficial, un estado que el check no emite, un resultado de otro control ni un
  `PASS` de una regla que no aplica. · rojo visto: si

## Cómo se verifica

Los cincuenta y seis por `.\tests\Invoke-Tests.ps1`. Ninguno es de lectura.

🔴 Un caso que aprueba, roto de muchas maneras: la mitad de los escenarios parte de él.

🔴 Los ids, los estados y los dieciocho motivos van clavados por literal en el test.

## Riesgos conocidos

- **Nadie produce la evidencia todavía.** Mientras el registro esté vacío, toda corrida con la
  señal en verdadero da `SECURITY_APPROVAL_REQUIRED`.
- **`reglas/` se sobrescribe en cada `-Update`.** Ahora son cuatro registros del proyecto; el ítem
  de `PENDIENTES-FH.md` se actualiza.
- **La contradicción del hotfix sigue abierta.** Un hotfix con assessment a posteriori da
  `SECURITY_APPROVAL_REQUIRED` hasta que alguien la resuelva en la norma.
- **Atar la procedencia a O2 por id es una decisión de este cambio.** Exige que la aprobación cite
  el `authorityId` del registro de O2; ninguna aprobación real va a traerlo sin que alguien lo
  escriba.
