# Reporte de seguridad: del libro al tablero

**Estado:** verificado y cerrado · **Fecha:** 23-09-2026 · **Paquete:** `security-reporting-dashboard-package`

## Qué problema resuelve

El harness ya produce casi toda la evidencia de seguridad que un reporte necesita, pero cada pieza
vive en su módulo y nadie las junta:

```
resultado por regla ES0902     orquestacion/seguridad.py      resultados() -> 21 reglas
aprobacion de QA (C2)          controles/checks/qa-security-approval-evidence.py
flujo de evaluacion, G2..G4    orquestacion/evaluacion.py
integridad del repositorio     orquestacion/integridad.py
frescura de la normativa       orquestacion/frescura.py       .claude/harness.fuentes.json
contabilidad de la tarea       contabilidad/                  .claude/runtime/accounting/<task>/
```

Hoy no se puede contestar, sin leer seis módulos a mano:

```
en que estado de seguridad esta la tarea GCBA-1234
que la bloquea
cuanto de lo aplicable se evaluo, y cuanto de eso quedo resuelto
hay aprobacion oficial de DGSEI, o solo revision interna
con que version de ES0902 se evaluo, y esa version esta verificada
```

Y hay una trampa que el paquete nombra y este cambio tiene que ser incapaz de cometer: un número
único de "seguridad 87/100" promedia una falla crítica con veinte reglas en verde y la esconde.

## Qué queda afuera

- **Correr los checks.** Nada del harness ejecuta hoy los checks contra un proyecto real: la
  evidencia se le pasa a `seguridad.resultados()` a mano. Este cambio construye los productores
  que convierten la salida estructurada de un check, una regla, una revisión o una evaluación en un
  evento del libro, pero no los enchufa a un ejecutor que no existe. Es el mismo corte que hizo el
  Bloque 4.
- **Un PDF binario.** El harness es solo stdlib y no tiene generador de PDF. Decisión del usuario
  del 23-09-2026: sale un `security-status.html` autocontenido con CSS de impresión, y el PDF se
  obtiene imprimiendo esa página. Sumar `reportlab` o `weasyprint` rompe la regla de dependencias y
  obliga al instalador a traerlas.
- **Nuevas reglas, agentes o skills.** El paquete lo prohíbe expresamente: el reporte presenta lo
  que ya existe.
- **Los controles de Vu4..Vu10, Ve2 y G1..G4.** Siguen sin check. En el tablero van a salir como
  `UNRESOLVED` o `NOT_EVALUATED`, y eso es verdad, no un defecto del reporte.
- **El hash aceptado de ES0902.** `source-registry.json` tiene `sha256: null` para las seis
  fuentes (pendiente ya anotado), así que la frescura de ES0902 da `FRESHNESS_UNVERIFIED` y el
  estado del sistema da `BLOCKED` hasta que alguien acepte el hash. Arreglarlo es de ese pendiente,
  no de este cambio.
- **Un `executionId`.** No existe en el Bloque 4. La unión se hace por `taskId`, y el evento guarda
  `executionId` nulo hasta que exista un ejecutor que lo emita.
- **Un schema unificado de hallazgo de seguridad.** No existe, y diseñarlo excede un reporte. El
  libro recibe el ciclo de vida del hallazgo como eventos con `findingIds`, `severity`, `confidence`
  y `result`, y no inventa campos del hallazgo.
- **Dos causas de `BLOCKED` que el paquete nombra.** "Conflicto de promoción o integridad de
  seguridad" y "no se puede establecer el alcance de la evaluación" no tienen hoy ningún módulo del
  harness que las produzca. Además, el schema del evento exige `scope.project`, así que un libro
  sin alcance no se puede escribir. Queda para cuando exista quien emita esas condiciones.
- **La instalación de `controles/` en los proyectos.** Es un pendiente abierto aparte. El reporte
  vive en `bin/`, que sí se instala, y no importa nada de `controles/`.

## Las decisiones, y por qué

### El reporte es un paquete nuevo en `bin/`, al lado de `contabilidad/`

`harnesses/desarrollo/bin/reporte_seguridad/`. Se descartó meterlo en `orquestacion/`, porque ese
paquete arma planes y decide resultados, y el reporte no decide ningún resultado: los copia.
Tampoco se hizo un subcomando del Bloque 4: la seguridad no es contabilidad, y el paquete pide
expresamente que no se dupliquen.

### El libro copia el patrón del Bloque 4 y no su código

Un solo verbo de escritura, `agregar`. Es append-only por construcción, deduplica por `eventId`,
valida contra el schema y redacta con la misma `contexto/limpieza.redactar_arbol` y el mismo
catálogo. No se reusa el `libro.py` de contabilidad porque ese valida contra
`execution-accounting-event`. Se reusa la limpieza, que es la parte que no puede divergir.

El archivo se llama `security-ledger.ndjson`, como pide el paquete, bajo
`.claude/runtime/security/<taskId>/`: al lado de `accounting/`, nunca en la raíz del proyecto.

### Nadie escribe un evento a mano: solo los productores

Cada evento lleva `details.producer`, de una lista cerrada, y `evidenceFingerprints`, el sha256 de
la salida estructurada de la que salió. `agregar` rechaza un evento sin productor de la lista o sin
huella. Los productores reciben la salida de una función del harness, no texto: `desde_regla`
recibe lo que devuelve `seguridad.resultado`, y así con el resto.

Se descartó confiar en que "el LLM no inventa". Es la defensa del paquete y no es mecánica. Esta
tampoco es completa: se nombra en Riesgos.

### El resultado de una regla lo traduce una tabla, y lo que no se evaluó es `NOT_EVALUATED`

`seguridad.RESULTADOS` usa `COMPLIANT / NON_COMPLIANT / UNRESOLVED / OVERRIDDEN / NOT_APPLICABLE`.
El tablero usa `PASS / FAIL / UNRESOLVED / NOT_APPLICABLE / NOT_EVALUATED`.

| Del motor | Al tablero |
|---|---|
| `COMPLIANT` | `PASS` |
| `NON_COMPLIANT` | `FAIL` |
| `UNRESOLVED` | `UNRESOLVED` |
| `OVERRIDDEN` | `UNRESOLVED` |
| `NOT_APPLICABLE` | `NOT_APPLICABLE` |
| regla sin ningún `RULE_EVALUATION` en el libro | `NOT_EVALUATED` |

`OVERRIDDEN` baja a `UNRESOLVED` porque el tablero no tiene dónde mostrar una excepción, y
convertirla en `PASS` sería copiar una aprobación que el reporte no puede verificar. Cada fila
guarda además `sourceResult` con el valor original del motor, así que la excepción no se pierde.

Si hay varios eventos de la misma regla, gana el último **en el orden del libro**, no el de
`timestamp` mayor: el orden del archivo es determinista y el reloj no.

### El resultado de una regla sale solo de un evento de esa regla

Un `CHECK_EVALUATION` no le pone resultado a ninguna regla, ni a la suya ni a las que comparten el
control por `normativeSources`. Solo un `RULE_EVALUATION` con `normative.rule = X` define el
resultado de X. Es la regla del paquete ("no se copia el resultado final de otra regla porque
comparten controles") hecha estructura: no existe el camino que lo copiaría.

### Bloquea toda regla aplicable en FAIL

Decisión del usuario del 23-09-2026. ES0902 es obligatoria, así que no hay archivo de
configuración que diga qué regla bloquea. Las condiciones de bloqueo, cada una con su fuente, son:

| Condición | Fuente | Empuja el estado a |
|---|---|---|
| frescura de ES0902 en estado bloqueante, o sin estado de conocimiento | `knowledge` | `BLOCKED` |
| integridad `TRUSTED_BASELINE_UNRESOLVED` en modo `SECURITY_INCIDENT` | `repository-integrity` | `BLOCKED` |
| regla aplicable en `FAIL` | `ES0902.<id>` | `ACTION_REQUIRED` |
| hallazgo `CRITICAL` abierto o reabierto | `finding` | `ACTION_REQUIRED` |
| hallazgo abierto con `blocking: true` de su productor | `finding` | `ACTION_REQUIRED` |
| integridad `MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE` o `SUSPICIOUS_BEHAVIOR_DETECTED` | `repository-integrity` | `ACTION_REQUIRED` |
| evaluación en `REASSESSMENT_REQUIRED` | `assessment` | `ACTION_REQUIRED` |

Un hallazgo `HIGH` o menor no bloquea si su productor no lo marcó así: el paquete pide no asumir
que todo hallazgo bloquea.

### El estado del sistema tiene una precedencia fija

```
alguna condicion que empuja a BLOCKED                                   -> BLOCKED
si no, regla aplicable UNRESOLVED o NOT_EVALUATED, evidencia material
       sin resolver, o integridad REVIEW_INCOMPLETE                     -> REVIEW_INCOMPLETE
si no, alguna condicion que empuja a ACTION_REQUIRED                    -> ACTION_REQUIRED
si no                                                                   -> READY_FOR_SECURITY_REVIEW
```

"Material" es un `EVIDENCE_STATE` con `blocking: true` y resultado `MISSING`, `CONFLICTING`,
`UNRESOLVED` o `UNSAFE_TEST_SKIPPED`. Con la precedencia del paquete, una regla en FAIL más una sin
evaluar da `REVIEW_INCOMPLETE`, no `ACTION_REQUIRED`. El FAIL no se esconde por eso: está en la
lista de bloqueos y en el mapa de calor.

### Tres estados separados, y ninguno se deduce de otro

El estado del sistema, el de la evaluación y el de la aprobación oficial se calculan por separado.
`READY_FOR_SECURITY_REVIEW` no toca la aprobación, y `G2_THRESHOLD_SATISFIED` tampoco.

El estado de la evaluación sale del último `ASSESSMENT_STATE`, que lleva el estado de
`evaluacion.ESTADOS`:

| `evaluacion` | Reporte |
|---|---|
| `NOT_STARTED`, `INTERNAL_ASSESSMENT` | `NOT_REQUESTED` |
| `READY_TO_REQUEST` | `READY_TO_REQUEST` |
| `REQUESTED`, `IN_ASSESSMENT`, `RESUBMITTED` | `ASSESSMENT_IN_PROGRESS` |
| `FINDINGS_RECEIVED`, `REMEDIATION`, `REJECTED` | `REASSESSMENT_REQUIRED` |
| `READY_TO_RESUBMIT` | `READY_TO_RESUBMIT` |
| `APPROVED` con productor de `PRODUCTORES_EXTERNOS` | `EXTERNAL_APPROVAL_EVIDENCED` |
| `APPROVED` con productor interno, `OFFICIAL_STATUS_UNRESOLVED`, un valor desconocido o ningún evento | `ASSESSMENT_STATE_UNRESOLVED` |

Hay dos ajustes sobre la tabla:
- Si el estado base es interno, está en `NOT_REQUESTED` o `READY_TO_REQUEST`, y el último cálculo
  de G2 dio `satisfied: true`, el estado es `G2_THRESHOLD_SATISFIED`.
- Si el check de C2 dio `SECURITY_REASSESSMENT_REQUIRED`, el estado es `REASSESSMENT_REQUIRED`,
  gane lo que gane la tabla.

La aprobación oficial sale del último `APPROVAL_EVIDENCE`, que lleva la salida del check de C2
más el productor, el ambiente y el release de la aprobación. Las filas se leen en orden y gana la
primera que se cumple:

| # | Evidencia | Aprobación |
|---|---|---|
| 1 | ningún `APPROVAL_EVIDENCE` | `NOT_AVAILABLE` |
| 2 | C2 `SECURITY_APPROVAL_EVIDENCE_CHANGED` o `SECURITY_REASSESSMENT_REQUIRED` | `EXTERNAL_APPROVAL_STALE` |
| 3 | C2 distinto de `PASS`, productor que no es de `PRODUCTORES_EXTERNOS`, o ambiente de la aprobación distinto de `QA` | `UNRESOLVED` |
| 4 | C2 `PASS`, externo, en `QA`, con un release distinto del `releaseId` del alcance, estando los dos presentes | `EXTERNAL_APPROVAL_STALE` |
| 5 | C2 `PASS`, externo, en `QA`, y release igual al del alcance o alguno de los dos ausente | `EXTERNAL_APPROVAL_EVIDENCED` |

El ambiente se compara contra `QA` y no contra el del alcance: ES0902 C2 exige la aprobación en QA,
cualquiera sea el ambiente que se está reportando. `STALE` es una aprobación que fue válida y ya
no lo es: la de otro release, o la que C2 da por cambiada o a reevaluar. Una aprobación que nunca
valió, como la de un productor interno o la emitida en `HML`, es `UNRESOLVED`.

### La cobertura son dos números, y sin denominador es `null`

```
aplicables = PASS + FAIL + UNRESOLVED + NOT_EVALUATED
intentadas = PASS + FAIL + UNRESOLVED
resueltas  = PASS + FAIL
assessmentCoveragePct  = 100 * intentadas / aplicables
evidenceResolutionPct  = 100 * resueltas  / aplicables
```

Se redondea a un decimal con `ROUND_HALF_UP`. Con `aplicables = 0` los dos porcentajes son
`null` y el reporte dice `N/D`. El schema del paquete los declara `number`. Se amplían a
`["number", "null"]`, que es la única divergencia de schema con el paquete.

### El resumen es una función pura de sus entradas, y la huella las cubre a todas

Las entradas son cuatro: el libro, la matriz, `security-report-domains.json` y, si existe, el
`summary.json` del Bloque 4 de la tarea. `generatedAt` es el `timestamp` del último evento, no la
hora del reloj. `snapshotFingerprint` es `sha256:` más el hash de las cuatro entradas en ese orden,
cada una precedida por su nombre y su largo. La del Bloque 4 lleva además una marca de presencia:
un `summary.json` ausente y uno de 0 bytes dan huellas distintas.
`reportId` es `SEC-<taskId>-<12 primeros hex de la huella>`. Las claves se escriben ordenadas.

Con eso, las mismas entradas dan el mismo `security-summary.json` byte a byte, y dos resúmenes
distintos nunca comparten huella. Una huella que no cubre lo que se muestra no identifica la
foto.

### El conocimiento entra al libro como un evento más

`desde_frescura(doc)` convierte la entrada `ES0902` de `harness.fuentes.json` en un
`KNOWLEDGE_STATE` con estos campos:
- `version`;
- `freshness`: el estado tal cual;
- `blocking`: el de `frescura`;
- `sourceIntegrity`, derivado así:

| Frescura | `sourceIntegrity` |
|---|---|
| `SOURCE_INTEGRITY_ALERT`, `SOURCE_CHANGED_SAME_VERSION` | `ALERT` |
| `FRESHNESS_UNVERIFIED` | `UNVERIFIED` |
| `CURRENT` | `VERIFIED` |
| cualquier otro | `UNRESOLVED` |

Se descartó que el resumen lea `harness.fuentes.json` directamente: dejaría de ser una función de
la foto del libro.

### La integridad del repositorio renombra un solo estado

`NO_SUSPICIOUS_CHANGE_FOUND` sale como `NO_SUSPICIOUS_INDICATORS_DETECTED`. Los otros cuatro
estados de `integridad.ESTADOS` salen igual. Sin evento de integridad, el panel dice
`NOT_EVALUATED` y no cambia el estado del sistema, porque la integridad es una capacidad y no una
regla. El texto del panel para `NO_SUSPICIOUS_INDICATORS_DETECTED` dice "no se detectaron
indicadores", nunca "no hay código malicioso".

### Los dominios son una agrupación fija, no normativa

`harnesses/desarrollo/reglas/security-report-domains.json` pone cada una de las 21 reglas en un
solo dominio:

| Dominio | Reglas |
|---|---|
| Gobierno | O1, O2 |
| Identidad y sesión | C1, Vu1, Vu3, Vu4 |
| Datos sensibles e interfaces públicas | Vu2, Vu7, Vu9 |
| Validación y manejo de errores | Vu5, Vu6 |
| Autorización y roles | Vu8 |
| OWASP / seguridad de aplicación | Vu10 |
| Tecnología y versiones | C3, Ve1, Ve2 |
| Evaluación de seguridad | C2, G1, G2, G3, G4 |

### El Bloque 4 se referencia, no se recalcula

El resumen guarda `block4ExecutionRef = "task:<taskId>"` solo si existe
`.claude/runtime/accounting/<taskId>/summary.json`. El reporte muestra la tarjeta de ejecución
copiando los valores de ese archivo tal cual. Si no existe, la tarjeta no aparece. El paquete de
reporte no abre nada del Bloque 4 para escribir.

### El reporte sale en español, con los enums en inglés

ADR-0011: lo lee una persona. El template del paquete está en inglés; se traduce la prosa y los
rótulos. Los valores de estado (`BLOCKED`, `PASS`) son identificadores de contrato y no se
traducen. Es el mismo criterio que el Bloque 4.

### El HTML es la página, y todo número sale del resumen

`security-status.md` y `security-status.html` se generan desde `security-summary.json`, y solo
desde ahí: el renderizador no importa `seguridad`, `evaluacion`, `integridad`, `frescura` ni el
libro. La página 1 sigue `security-dashboard-page-1-spec.md`. Cada valor lleva
`data-field="<ruta en el resumen>"` para que un test pueda compararlo contra el resumen.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/security-ledger-event.schema.json` | El evento del libro, `security-ledger-event/1.0`, dentro del subconjunto del validador |
| `comun/schemas/security-summary.schema.json` | El resumen, `security-summary/1.0`, con los porcentajes admitiendo `null` |
| `comun/schemas/security-report.schema.json` | El contrato de renderizado, `security-report/1.0` |
| `harnesses/desarrollo/bin/reporte_seguridad/__init__.py` | Frontera del paquete: qué hace y qué no |
| `harnesses/desarrollo/bin/reporte_seguridad/libro.py` | `agregar`, `leer`, la carpeta por tarea; append-only y redacción |
| `harnesses/desarrollo/bin/reporte_seguridad/productores.py` | `desde_regla`, `desde_check`, `desde_revision`, `desde_hallazgo`, `desde_evaluacion`, `desde_g2`, `desde_aprobacion`, `desde_integridad`, `desde_frescura` |
| `harnesses/desarrollo/bin/reporte_seguridad/resumen.py` | La foto del libro más la matriz dan `security-summary.json` |
| `harnesses/desarrollo/bin/reporte_seguridad/reporte.py` | El resumen da `security-status.md` y `security-status.html` |
| `harnesses/desarrollo/reglas/security-report-domains.json` | Los ocho dominios del reporte |
| `harnesses/desarrollo/bin/dev-harness.py` | Subcomando `seguridad <TASK> [--conocimiento] [--resumen] [--reporte]` |
| `tests/casos/48_reporte_de_seguridad.py` | Los escenarios de abajo |
| `docs/reporte-de-seguridad.md` | Cómo se lee el reporte, para una persona |

## Escenarios verificables

Entre paréntesis va el id del paquete, `SR-nn`.

### El libro

- **E-01** — El libro es append-only: después de agregar un evento, los bytes que ya había quedan
  idénticos y el paquete no tiene ninguna función que reescriba o borre el libro. Un `eventId` que
  ya está no entra dos veces. (SR-01) · rojo visto: si
- **E-02** — Un evento al que le falta cualquiera de `schema_version`, `eventId`, `timestamp`,
  `eventType`, `taskId`, `scope` o `result`, o que trae un `eventType` fuera del enum, se rechaza y
  el libro queda igual. (SR-02) · rojo visto: si
- **E-03** — En un evento con una contraseña, un token Bearer, una clave privada PEM, una cookie
  `JSESSIONID=` o un `sessionid=` en `details` o en `evidenceRefs`, ninguno de esos valores llega al
  disco. Una clave sensible (`password`, `token`, `secret`, `cookie`, `sessionId`, `privateKey`)
  dentro de `details` llega con el valor `[redactado]`. (SR-03) · rojo visto: si
- **E-03b** — Una contraseña se reconoce por la palabra que la anuncia, no por la sintaxis que la
  rodea. Si aparece una de `password`, `passwd`, `pwd`, `pass`, `passphrase`, `contraseña` o `clave`
  (sin distinguir mayúsculas, sin letra ni dígito pegado antes, y sin letra, dígito ni `_` pegado
  después: `db_password` cuenta y `password_hash` no), se redacta el primer
  valor que la sigue en la misma línea. Entre la palabra y el valor puede haber cualquier
  combinación de espacios, comillas, `:`, `=`, `=>`, `:=`, `>` y `-`. El valor termina en un
  espacio, una comilla, `<`, `,` o `;`. Entre las formas que la regla tiene que cubrir, cada una
  con su test:
  - `'password' => 'x'`
  - `<password>x</password>`
  - `--password x`
  - `set password x`
  - `pass=x`
  - `clave: x`

  Redactar de más en prosa ("la password del usuario" pierde "del") es el error aceptado. Esta
  regla cierra la lista: una sintaxis que no la cumple es un pendiente del catálogo, no un
  contradicho de E-03. · rojo visto: si
- **E-04** — Un evento sin `details.producer` de la lista cerrada, o sin `evidenceFingerprints`, se
  rechaza. (SR-05, la mitad de productores) · rojo visto: si

### El resumen

- **E-05** — Dos corridas del resumen sobre el mismo libro y la misma matriz dan el mismo
  `security-summary.json` byte a byte, incluidos `generatedAt`, `reportId` y
  `snapshotFingerprint`. (SR-04) · rojo visto: si
- **E-05b** — Cambiar un solo byte del `summary.json` del Bloque 4 o de
  `security-report-domains.json`, o crear o borrar el `summary.json` del Bloque 4, con el mismo
  libro y la misma matriz, cambia `snapshotFingerprint` y `reportId`. · rojo visto: si
- **E-06** — El paquete `reporte_seguridad` no importa ningún cliente de modelo ni hace red: sus
  imports son de la stdlib o del harness. (SR-05) · rojo visto: si
- **E-07** — Ni el resumen ni su schema tienen una clave que se llame `score`, `grade`, `rating`
  o `riskScore`, ni un valor numérico global del sistema. (SR-06) · rojo visto: si
- **E-08** — Con 20 reglas `PASS` y una `NOT_APPLICABLE`, `applicableRules` es 20.
  (SR-07) · rojo visto: si
- **E-09** — Una regla `UNRESOLVED` suma a `attemptedRules` y no a `resolvedRules`.
  (SR-08) · rojo visto: si
- **E-10** — Una regla sin evento suma a `applicableRules` y no a `attemptedRules`.
  (SR-09) · rojo visto: si
- **E-11** — Con las 21 reglas `NOT_APPLICABLE`, los dos porcentajes son `null` y el reporte dice
  `N/D`, nunca `100%`. (SR-10) · rojo visto: si
- **E-12** — Un resumen generado valida contra `security-summary.schema.json`, y los tres schemas
  pasan enteros por `controlar_soporte`. · rojo visto: si

### El estado del sistema

- **E-13** — Una frescura de ES0902 bloqueante da `BLOCKED` aunque las 21 reglas estén en `PASS`.
  (SR-11) · rojo visto: si
- **E-14** — Sin ningún `KNOWLEDGE_STATE` en el libro, el estado es `BLOCKED`, no
  `READY_FOR_SECURITY_REVIEW`. · rojo visto: si
- **E-15** — Con el conocimiento vigente, veinte reglas `PASS` y una `NOT_EVALUATED`, el estado es
  `REVIEW_INCOMPLETE`. Lo mismo pasa con un `EVIDENCE_STATE` material `MISSING` en vez de la
  regla sin evaluar. (SR-12) · rojo visto: si
- **E-16** — Con el conocimiento vigente, veinte reglas `PASS` y una `FAIL`, el estado es
  `ACTION_REQUIRED` y hay un bloqueo con `source: "ES0902.<id>"`. (SR-13) · rojo visto: si
- **E-17** — Con el conocimiento vigente, todas las aplicables en `PASS`, sin hallazgos que
  bloqueen y sin evidencia material pendiente, el estado es `READY_FOR_SECURITY_REVIEW`.
  (SR-14) · rojo visto: si
- **E-18** — En ese mismo caso, `officialApprovalStatus` es `NOT_AVAILABLE` y el reporte muestra
  el aviso de que la revisión interna no es aprobación oficial. (SR-15) · rojo visto: si

### La evaluación y la aprobación

- **E-19** — Un G2 con `satisfied: true` da `assessmentState = G2_THRESHOLD_SATISFIED` y deja la
  aprobación en `NOT_AVAILABLE`. (SR-16) · rojo visto: si
- **E-20** — Un `APPROVED` de un productor interno no da `EXTERNAL_APPROVAL_EVIDENCED` en ninguno
  de los dos campos. Uno de `GCBA_DGSEI` con C2 `PASS` en QA sí. (SR-17) · rojo visto: si
- **E-21** — Un C2 con `SECURITY_APPROVAL_EVIDENCE_CHANGED` o `SECURITY_REASSESSMENT_REQUIRED` da
  `EXTERNAL_APPROVAL_STALE`. (SR-18) · rojo visto: si
- **E-22** — Una aprobación externa en `HML`, o en QA con un release distinto del `releaseId` del
  alcance, no da `EXTERNAL_APPROVAL_EVIDENCED`. (SR-19) · rojo visto: si
- **E-22b** — Las cinco filas de la tabla de aprobación se aplican en orden:
  - una externa en `HML` da `UNRESOLVED`;
  - una interna en `QA` da `UNRESOLVED`, también con otro release;
  - una externa en `QA` de otro release da `EXTERNAL_APPROVAL_STALE`;
  - un C2 `SECURITY_APPROVAL_EVIDENCE_CHANGED` da `EXTERNAL_APPROVAL_STALE`, también con productor interno;
  - una externa en `QA` sin `releaseId` en el alcance da `EXTERNAL_APPROVAL_EVIDENCED`.

  · rojo visto: si
- **E-23** — Un C2 con `SECURITY_REASSESSMENT_REQUIRED` da `assessmentState =
  REASSESSMENT_REQUIRED` aunque el último estado de la evaluación sea `READY_TO_REQUEST`, y suma un
  bloqueo con `source: "assessment"`. (SR-20) · rojo visto: si

### El mapa de calor

- **E-24** — `normative.rules` tiene exactamente las 21 claves de la matriz, en el orden del
  estándar, aunque el libro no traiga ningún evento. (SR-21) · rojo visto: si
- **E-25** — Un `CHECK_EVALUATION` en `PASS` de un control compartido por C3 y Ve1 no le pone
  resultado a ninguna de las dos. Un `RULE_EVALUATION` de C3 en `PASS` deja Ve1 en
  `NOT_EVALUATED`. (SR-22) · rojo visto: si
- **E-26** — Una regla `UNRESOLVED` y otra `OVERRIDDEN` salen como `UNRESOLVED` en el resumen, en
  el md y en el HTML. `sourceResult` conserva `OVERRIDDEN`. (SR-23) · rojo visto: si
- **E-27** — Una regla sin evento sale como `NOT_EVALUATED` en el resumen, en el md y en la grilla
  del HTML. (SR-24) · rojo visto: si
- **E-28** — El reporte muestra el estándar, la versión, la frescura y `sourceIntegrity` que están
  en `knowledge`. (SR-25) · rojo visto: si

### El conocimiento

- **E-29** — `desde_frescura` sobre una entrada `FRESHNESS_UNVERIFIED` da
  `sourceIntegrity = UNVERIFIED`, y el estado del sistema no es `READY_FOR_SECURITY_REVIEW`.
  (SR-26) · rojo visto: si
- **E-30** — Una entrada `SOURCE_INTEGRITY_ALERT` da `sourceIntegrity = ALERT`, estado `BLOCKED`
  y un bloqueo con `source: "knowledge"` en la página 1. (SR-27) · rojo visto: si
- **E-31** — Una entrada `CURRENT` da `sourceIntegrity = VERIFIED` y no agrega bloqueo: el estado
  sale de las reglas. (SR-28) · rojo visto: si

### Los hallazgos y los bloqueos

- **E-32** — Un hallazgo `LOW` con `confidence: HIGH` y otro `CRITICAL` con `confidence: LOW`
  conservan cada uno su severidad y su confianza en `findings.items`. Ningún campo mezcla las dos.
  (SR-29) · rojo visto: si
- **E-33** — Un hallazgo `CRITICAL` abierto con las 21 reglas en `PASS` da `ACTION_REQUIRED`, un
  bloqueo con `source: "finding"` y `CRITICAL: 1` en la página 1. (SR-30) · rojo visto: si
- **E-34** — `blockingConditions` es una lista propia: cada ítem tiene `blockerId`, `source`,
  `title`, `state` y `evidenceRefs`. Un hallazgo `HIGH` sin `blocking: true` cuenta en
  `totalsBySeverity` y no está en la lista. (SR-31) · rojo visto: si
- **E-35** — Un hallazgo creado, resuelto y actualizado a abierto sale con estado `REOPENED`, y
  cuenta en `reopened` y no en `open`. (SR-32) · rojo visto: si
- **E-36** — Un hallazgo resuelto sigue en `findings.items` con su `findingId`, su estado
  `RESOLVED` y sus `evidenceRefs`. (SR-33) · rojo visto: si

### La integridad del repositorio

- **E-37** — Una integridad `TRUSTED_BASELINE_UNRESOLVED` sale así en el panel. En modo
  `SECURITY_INCIDENT` da `BLOCKED`. En otro modo no bloquea, pero sigue visible.
  (SR-34) · rojo visto: si
- **E-38** — `NO_SUSPICIOUS_CHANGE_FOUND` sale como `NO_SUSPICIOUS_INDICATORS_DETECTED`, y ni el
  md ni el HTML afirman la ausencia de código malicioso. (SR-35) · rojo visto: si
- **E-39** — `MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE` sale con su propio rótulo, suma un bloqueo
  con `source: "repository-integrity"` y cuenta en `confirmedMalicious`. (SR-36) · rojo visto: si

### La evidencia

- **E-40** — `evidence.verified`, `missing`, `conflicting`, `unsafeTestsSkipped` y `unresolved`
  cuentan el último `EVIDENCE_STATE` de cada `evidenceRef`. El mismo libro da siempre los mismos
  números. (SR-37) · rojo visto: si
- **E-41** — Un check cuyo estado termina en `_TEST_UNSAFE` produce además un `EVIDENCE_STATE`
  `UNSAFE_TEST_SKIPPED`, y el contador sale en el md y en el HTML. (SR-38) · rojo visto: si
- **E-42** — Un `EVIDENCE_STATE` material `UNRESOLVED` impide `READY_FOR_SECURITY_REVIEW`. Uno no
  material, con `blocking: false`, suma al contador y no cambia el estado. (SR-39) · rojo visto: si

### El md y el HTML

- **E-43** — Cada valor de la tabla ejecutiva de `security-status.md` es igual al campo del resumen
  que le corresponde, y cambiar un campo del resumen cambia el md. (SR-40) · rojo visto: si
- **E-44** — Cada elemento del HTML con `data-field` muestra el valor de esa ruta en el resumen.
  El renderizador no importa ningún módulo que calcule estado. (SR-41) · rojo visto: si
- **E-45** — El md y el HTML muestran `snapshotFingerprint` y `reportId`. (SR-42) · rojo visto: si
- **E-46** — El alcance muestra el proyecto, el ambiente, la rama, el commit y el release que trae
  el libro. (SR-43) · rojo visto: si
- **E-47** — Un campo de alcance ausente o nulo sale como `desconocido`, nunca vacío ni omitido.
  (SR-44) · rojo visto: si

### El Bloque 4

- **E-48** — Con un `summary.json` del Bloque 4 para la tarea, la tarjeta de ejecución muestra sus
  valores tal cual. El paquete no importa `contabilidad.agregacion` ni `contabilidad.costos`, y sin
  ese archivo `block4ExecutionRef` es `null` y la tarjeta no aparece. (SR-45) · rojo visto: si
- **E-49** — Correr el subcomando completo deja los bytes de `.claude/runtime/accounting/` sin
  cambios. (SR-46) · rojo visto: si
- **E-50** — Un `sk-ant-…` o un `AKIA…` en `details` de un evento no llega al libro.
  (SR-47) · rojo visto: si

### La página 1

- **E-51** — La página 1 del HTML tiene siempre las cuatro tarjetas primarias
  (`systemSecurityState`, `blockingConditions`, `coverage`, `officialApprovalStatus`), también con
  un libro vacío. (SR-48) · rojo visto: si
- **E-52** — Con bloqueos, la página 1 muestra hasta cinco en un panel propio y un `+N más` con los
  que sobran. Sin bloqueos, el panel dice que no hay. (SR-49) · rojo visto: si
- **E-53** — Si la aprobación no es `EXTERNAL_APPROVAL_EVIDENCED`, el pie dice que la revisión
  interna del harness no es aprobación oficial de GCBA/DGSEI. Si lo es, no lo dice.
  (SR-50) · rojo visto: si

### La CLI y la instalación

- **E-54** — `dev-harness.py seguridad GCBA-1 --conocimiento --resumen --reporte`, sobre un
  proyecto con `harness.fuentes.json`, deja en `.claude/runtime/security/GCBA-1/` los cuatro
  archivos (`security-ledger.ndjson`, `security-summary.json`, `security-status.md`,
  `security-status.html`) y sale con código 0. · rojo visto: si
- **E-55** — Un `taskId` con `..`, `/` o `\` se rechaza antes de tocar el disco.
  · rojo visto: si
- **E-56** — `reporte_seguridad/` y `security-report-domains.json` llegan a un proyecto instalado:
  están en el lockfile después de `install.ps1`. · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/48_reporte_de_seguridad.py`, con el id en
el título del test. Ninguno lleva `· verificación: lectura`: el reporte es determinista por
diseño, y un escenario que necesitara leer una corrida de un modelo contradiría E-06. E-56 se
prueba en el caso del instalador que ya arma un proyecto temporal.

## Riesgos conocidos

- **El productor no sabe si su entrada es verdadera.** `desde_regla` exige la forma de la salida
  de `seguridad.resultado` y huellea lo que recibe, pero un modelo con acceso al intérprete puede
  armar ese dict a mano. La huella prueba de qué salió el evento, no que eso haya salido de correr
  el check. La defensa completa es el ejecutor, que no existe.
- **El tablero va a salir en `BLOCKED` en cualquier proyecto real** mientras ES0902 no tenga hash
  aceptado. Es verdad y el reporte lo explica, pero una persona puede leerlo como un defecto del
  reporte.
- **Trece reglas sin check** dejan `REVIEW_INCOMPLETE` casi por construcción. El número de
  cobertura va a ser bajo, y está bien que lo sea.
- **La redacción depende del catálogo de secretos.** Un formato de credencial que el catálogo no
  conoce entra al libro. Las claves sensibles de `details` se redactan por nombre, pero un secreto
  metido en `result` o en `title` depende solo del catálogo.
- **`OVERRIDDEN` baja a `UNRESOLVED`.** Una excepción autorizada de verdad va a figurar como
  pendiente, y el estado del sistema no llega a `READY` mientras exista. Se prefirió eso a mostrar
  un `PASS` que el reporte no puede sostener.
