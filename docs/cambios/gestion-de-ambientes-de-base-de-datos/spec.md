# Gestión de ambientes de base de datos

**Estado:** construido, cuatro refutaciones, en la quinta · **Fecha:** 22-09-2026 · **Alcance:** capacidad transversal del harness

## Qué problema resuelve

Hoy el harness no sabe nada de las bases de datos de un proyecto. No sabe cuántos ambientes hay, no
distingue uno de otro, y no tiene ninguna forma de impedir que una operación de escritura se ejecute
contra producción. Si mañana se construye una tool de base de datos, lo único que la separa de
`UPDATE` en PRD son los permisos que tenga el usuario de la conexión — y eso es una decisión que
tomó alguien de infraestructura hace dos años, en otro sistema, para otra cosa.

🔴 **Los permisos nativos de la base son la segunda barrera, no la primera.** Un usuario de solo
lectura en PRD es una buena práctica y no es un control del harness: nadie lo verifica desde acá,
nadie se enteraría si cambiara, y el día que un proyecto configure el mismo usuario para los cuatro
ambientes —que es exactamente lo que pasa— no queda ninguna barrera.

Lo que se construye es la primera: **clasificar toda operación antes de ejecutarla y denegar la que
el ambiente no permite, antes de abrir la conexión.**

```
DEV  ->  FULL
QA   ->  READ_ONLY
HML  ->  READ_ONLY
PRD  ->  READ_ONLY

lo que no esta en esa tabla  ->  DENY / DATABASE_ENVIRONMENT_UNRESOLVED
```

### Esto no es una regla de ES0901

Las ocho reglas instaladas hasta ahora —G1, G2 y D1 a D6— verifican **cumplimiento**: miran evidencia
y dicen si una aplicación cumple. Esto es otra cosa: es una capacidad de runtime que **decide y
deniega**. No tiene señal de aplicabilidad, no tiene policy en `control-registry.json` y no entra en
la matriz normativa.

Toca tres reglas en el futuro y ninguna hoy: `G1` (qué motor y qué versión están homologados), `P7`
(sin lógica de negocio en la base) y `M2` (configuración de ambiente fuera del código). Ninguna de
las tres está construida, y esta capacidad **no las adelanta ni las declara**.

## Qué queda afuera

- **Conectarse a una base de datos.** Este módulo no abre una conexión, no ejecuta una sentencia y no
  trae un driver. Decide si la operación está permitida y devuelve con qué perfil se haría.
  `DATABASE_CONNECTION_FAILED` y `DATABASE_PERMISSION_DENIED` son estados que el módulo declara para
  que quien ejecute los devuelva; no los produce él.
- **Los perfiles de conexión de ningún proyecto.** `reglas/database-profiles.json` se instala
  **vacío**, igual que la tabla de tarifas del Bloque 4: el harness no sabe en qué host vive la base
  de nadie. Sin perfil, `DATABASE_PROFILE_NOT_FOUND`.
- **Un parser de SQL.** Ver la decisión de más abajo. Lo que hay es un barrido que sólo puede
  **subir** la clase de una operación, y lo que no puede clasificar se deniega.
- **Un agente o una skill nueva.** El pedido lo prohíbe (§9). Los dos agentes que la consumen
  —`dev-backend`, `dev-devops`— y las cinco skills que nombra —`dev-data`, `dev-persistence`,
  `dev-environments`, `dev-deployment`, `dev-ci-cd`— **ya están instalados**, los siete.
- **Una segunda escala de riesgo.** Ver la decisión de más abajo: el riesgo y la aprobación salen de
  `tools.py`, que ya existe.
- **Aplicar una migración en QA, HML o PRD.** Nunca, por ningún camino. La promoción es un artefacto
  versionado que viaja por el pipeline, y eso está fuera de esta capacidad.
- **Declarar permisos de capacidad para bases de datos.** `permisos-por-capacidad.json` tiene cuatro
  capacidades y ninguna de base de datos. Eso es un **hueco correcto**: la doctrina de `tools.py` es
  que una capacidad sin permisos declarados devuelve `MISSING_CONTEXT`, no un permiso. Se afirma en
  verde para que quien construya la tool tenga que declararlos.

## Las decisiones, y por qué

### El ambiente desconocido no existe como grado, existe como negación

```
ambiente ausente, vacio, en blancos, con otra capitalizacion o con otro nombre
        ->  DENY, DATABASE_ENVIRONMENT_UNRESOLVED
```

No hay ningún camino por el que un ambiente que la política no declara termine con `read: true`. Es
la única decisión de este cambio que no admite matices, y el escenario que la cubre recorre **todas**
las formas de ambiente no declarado, no una.

🔴 La capitalización se compara en su forma declarada, y `dev` en minúsculas **no** es `DEV`. Puede
parecer hostil y es lo correcto: normalizar la capitalización de un identificador de ambiente es
exactamente el atajo por el que `Prd`, `prod` y `PROD` acaban resolviendo a algo. Si un proyecto usa
otros nombres, los declara; no se adivinan.

### La clase de la operación y el efecto son dos dimensiones, no una

El pedido enumera cinco clases y la compuerta de riesgo que ya existe conoce tres efectos. La
tentación es fundirlas en una escala ordenada de cinco, y eso sería **inventar una segunda doctrina
de riesgo**. Son dos campos:

```
operationClass          READ_ONLY  MUTATING  DESTRUCTIVE  DDL  MIGRATION
effectiveSideEffects    los tres de tools.SIDE_EFFECTS, y nada mas
```

La traducción, que es lo único que la compuerta de riesgo consume:

```
SELECT                              ->  READ_ONLY    efecto READ_ONLY
INSERT, UPDATE                      ->  MUTATING     efecto MUTATING
DELETE con WHERE establecido        ->  MUTATING     efecto MUTATING
DELETE sin WHERE, o sin sentencia   ->  DESTRUCTIVE  efecto DESTRUCTIVE
CREATE, ALTER                       ->  DDL          efecto MUTATING
DROP, TRUNCATE                      ->  DDL          efecto DESTRUCTIVE
MIGRATION                           ->  MIGRATION    efecto MUTATING
MIGRATION declarada irreversible    ->  MIGRATION    efecto DESTRUCTIVE
```

🔴 **La clase decide el permiso; el efecto decide el riesgo.** Son dos preguntas y las contesta cada
una su mecanismo: la clase se cruza contra el bit del ambiente —`read`, `write`, `ddl`,
`migrations`— y el efecto se le pasa a `tools.derivar_riesgo`. Un DDL denegado por el ambiente y un
DDL permitido con aprobación son dos respuestas distintas.

Y la regla monótona se hace cumplir sobre **`effectiveSideEffects`**: si el barrido encuentra algo de
más impacto, el efecto sube. Nunca baja.

### La clasificación se declara y se verifica, y el barrido sólo puede subir

Éste es el centro del cambio y también su límite honesto.

Si la clasificación saliera de parsear el SQL, esto sería un parser de SQL — y un parser que
subclasifica es un agujero de seguridad con forma de control. `SELECT ... INTO`, un `WITH` que
termina en `DELETE`, dos sentencias separadas por `;`, un comentario que esconde una palabra: cada
una de esas formas es una manera de que un `UPDATE` se lea como un `SELECT`.

Si saliera del verbo declarado por quien pide, el control lo evade quien quiera, declarando
`SELECT`.

Así que sale de las dos, con una asimetría:

```
1. el verbo declarado se mapea contra una tabla CERRADA de clases
2. si viene el texto de la sentencia, se barre buscando clases MAS ALTAS
3. la clase final es la MAS ALTA de las dos. El barrido nunca baja una clase
4. lo que el barrido no puede clasificar  ->  DATABASE_OPERATION_UNCLASSIFIED  ->  DENY
```

🔴 **Es la misma asimetría que ya hace cumplir `tools.controlar_riesgo`**: *"el riesgo declarado no
puede ser menor que el derivado. Más alto se respeta, más bajo se rechaza."* No se inventa una
doctrina nueva; se aplica la que el repositorio ya tiene a un dato nuevo.

Y el límite se dice en voz alta: **un barrido no es un parser.** Una sentencia cuya clase el barrido
no puede establecer se **deniega**, no se permite. Es la única postura defendible y es lo que
significa *"missing data must fail closed"*.

### `DELETE` sin alcance establecido es DESTRUCTIVE

El pedido dice *"DELETE → MUTATING or DESTRUCTIVE depending on scope"*. El alcance sale de la
sentencia: un `DELETE` con `WHERE` es MUTATING, uno sin `WHERE` borra la tabla entera y es
DESTRUCTIVE.

🔴 Y cuando no viene la sentencia, el alcance **no se puede establecer**, así que es DESTRUCTIVE. La
alternativa —asumir MUTATING— es asumir lo más favorable sobre un dato que falta, que es la forma
exacta del defecto que este cambio existe para impedir.

### El riesgo y la aprobación salen de la compuerta que ya existe

DEV es FULL y FULL no es *sin restricciones*. Un `DROP SCHEMA` en DEV está permitido por el ambiente
y puede seguir necesitando que una persona decida.

Eso **no se construye de nuevo**. `tools.py` ya tiene la escala —`LOW/MEDIUM/HIGH/CRITICAL`—, la
derivación y la regla de aprobación. La operación de base de datos se traduce a los campos que esa
derivación mira y se la consulta:

```
sideEffects      READ_ONLY | MUTATING | DESTRUCTIVE   (las tres que tools.py ya conoce)
networkAccess    siempre: una base esta del otro lado de la red
secretsRequired  siempre: hace falta una credencial para ejecutar
blastRadius      scope external-system, y productionImpact cuando el ambiente es PRD
```

🔴 **Y lo que devuelve se midió, no se supuso.** Corriendo la implementación actual contra esas
entradas, con `riskLevel` puesto en el derivado:

```
efecto        ambiente        derivado   approvalRequired
READ_ONLY     cualquiera      HIGH       no
MUTATING      DEV/QA/HML      HIGH       no
MUTATING      PRD             CRITICAL   si
DESTRUCTIVE   cualquiera      CRITICAL   si
```

Toda operación de base de datos queda **al menos en HIGH** —porque toca secretos y sale a la red—,
pero eso es lo que la derivación actual **devuelve**, no una afirmación que este cambio agrega. Los
cuatro números van clavados exactos en el test: el día que alguien toque `derivar_riesgo`, este
cambio tiene que enterarse.

🔴 **Dos escalas de riesgo en el mismo harness es una escala de riesgo.** La segunda se usa para
justificar lo que la primera no dejaba pasar.

### La tabla de operaciones es cerrada, y los verbos de metadata no se asumen portables

```
SELECT  INSERT  UPDATE  DELETE  CREATE  ALTER  DROP  TRUNCATE  MIGRATION
```

Nueve, y nada más. `SHOW`, `DESCRIBE` y `EXPLAIN` **no entran**: no son portables entre motores,
cada uno hace algo distinto en cada uno, y un `EXPLAIN ANALYZE` en algunos motores **ejecuta la
sentencia**. Un verbo que el harness no declara cae en `DATABASE_OPERATION_UNCLASSIFIED` y se
deniega.

La inspección de esquema, de metadata y las consultas de diagnóstico que los tres ambientes de
promoción sí permiten se expresan con `SELECT` contra el catálogo. Cuando alguien necesite un verbo
de un motor concreto, se agrega **deliberadamente**, con el motor nombrado — no se infiere que
cualquier verbo que suene a lectura lo sea.

### Los schemas entran tal como vinieron, y para eso se amplía el validador

Los dos schemas del pedido usan `$defs`, `$ref` y `additionalProperties: false`, y el validador del
repositorio —`comun/bin/contexto-armar.py`— no interpretaba ninguna de las tres. Había tres salidas
y una sola es defendible:

```
sacarle additionalProperties al schema   ->  aflojar el schema. Un perfil con un campo
                                             `password` viajaria con el sello puesto
validarlo con un recorrido propio en     ->  duplicar a mano lo que el Bloque 4 ya tuvo
bases.py                                     que escribir a mano por lo mismo
ampliar el validador                     ->  lo que dice su propia doctrina
```

Su docstring lo tiene escrito: *"Se amplía el validador, no se afloja el schema."* Así que el
validador gana tres palabras, **aditivas** —ningún schema existente las usa, así que ningún contrato
cambia de comportamiento—:

```
$defs                  se recorre entero, usado o no
$ref                   SOLO local, a #/$defs/<nombre>, y no convive con otras reglas
additionalProperties   SOLO `false`, y exige `properties`
```

🔴 **`additionalProperties: false` no es azúcar acá: es la mitad de la seguridad de este cambio.** Es
lo que hace que un ambiente que la política no declara se rechace, y que un perfil con una
contraseña en claro se rechace. Sin eso los dos archivos serían decorativos.

Y lo que **no** se soporta se dice en voz alta: un `$ref` a otro archivo o a una URL, y un
`additionalProperties` con un schema como valor. Un validador que sigue una referencia a medias deja
una rama del contrato que nadie mira, que es justo lo que `controlar_soporte` existe para impedir.

📌 Los cuatro archivos de datos y de contrato —la política, los perfiles y los dos schemas— se
instalan **tal como vinieron en el pedido**, sin una coma cambiada. Son la fuente de verdad; la
doctrina vive en `bases.py` y en `docs/bases-de-datos.md`.

### La política es del harness; los perfiles, del proyecto

```
reglas/database-environment-access-policy.json   del HARNESS. Se instala con los cuatro
                                                 ambientes y el default DENY, y un proyecto
                                                 no la edita
reglas/database-profiles.json                    del PROYECTO. Se instala VACIO
```

El pedido lo dice: *"The environment access policy remains Harness-owned."* Un proyecto que pudiera
declarar que su PRD es FULL no tiene ninguna protección, y el archivo se llamaría política sin ser
una.

Los perfiles son lo contrario: el harness no puede saber en qué host vive la base de nadie, así que
se instala vacío y sin perfil hay `DATABASE_PROFILE_NOT_FOUND`. Es el mismo patrón que la
`rateTable` del Bloque 4, que también se instala vacía porque el harness no carga tarifas.

🔴 **Cada ambiente resuelve su propio perfil.** `main-database / DEV` y `main-database / QA` son dos
entradas, no una con un campo de ambiente. Asumir que dos ambientes comparten instancia es cómo un
`UPDATE` que alguien creía de QA llega a PRD.

### `resolver()` no toca el almacén de secretos. Nunca

El perfil lleva **sólo referencias** —`usernameSecretRef`, `passwordSecretRef`— y la resolución del
valor vive en el borde de ejecución, en una función aparte que es la única que habla con
`integraciones/almacen.py`.

Eso hace que la promesa sea **estructural y no una costumbre**: se puede afirmar que `resolver()` no
expone una credencial porque no tiene forma de conseguirla. El escenario que lo cubre lo verifica
sobre el módulo, no sobre una salida.

Y `almacen.py` ya trae la parte difícil desde 0.15.0: *"Ningún método de este módulo imprime,
registra ni mete un valor adentro del texto de una excepción."* Se reutiliza, no se reescribe.

### El invariante de los ambientes de promoción es un producto, no una lista

El pedido enumera veinte escenarios de QA, HML y PRD —`UPDATE` en QA, `DDL` en HML, `DELETE` en
PRD…—. Verificar esa lista es verificar veinte celdas de una tabla y dejar el resto sin mirar.

Lo que se verifica es el **producto entero**: para los tres ambientes de promoción, por cada verbo de
la tabla de clases y por cada clase, ninguna operación que no sea READ_ONLY sale con
`allowed: true`. La lista del pedido queda cubierta y también la celda que nadie escribió.

Es la lección de las ocho reglas anteriores: **invariante sobre el paquete, no enumeración.**

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/orquestacion/bases.py` | El resolvedor: política, clasificación, perfil, riesgo y estados |
| `harnesses/desarrollo/reglas/database-environment-access-policy.json` | La política, del harness, con los cuatro ambientes y el default DENY |
| `harnesses/desarrollo/reglas/database-profiles.json` | Los perfiles, vacío |
| `comun/schemas/database-environment-access-policy.schema.json` | El contrato de la política, del pedido |
| `comun/schemas/database-profile.schema.json` | El contrato de un perfil: sólo referencias, del pedido |
| `comun/bin/contexto-armar.py` | `$defs`, `$ref` local y `additionalProperties: false` — el único cambio a un módulo compartido |
| `docs/bases-de-datos.md` | Cómo se resuelve un ambiente y por qué la política no se edita |
| `tests/casos/33_bases_de_datos.py` | Los escenarios de acá abajo |

No se toca la matriz normativa, ni `control-registry.json`, ni `agent-registry.json`, ni ninguna
skill, ni ningún agente.

## Escenarios verificables

Entre paréntesis, el `DB-nn` del pedido de instalación.

### La política y los cuatro ambientes

- **E-01** — La política instala exactamente los cuatro ambientes del pedido con sus modos, su
  default `DENY`, y vive en `reglas/` del harness. (§2) · rojo visto: si
- **E-02** — DEV resuelve `FULL`, con `read`, `write`, `ddl` y `migrations` en verdadero. (DB-01)
  · rojo visto: si
- **E-03** — QA resuelve `READ_ONLY`. (DB-02) · rojo visto: si
- **E-04** — HML resuelve `READ_ONLY`. (DB-03) · rojo visto: si
- **E-05** — PRD resuelve `READ_ONLY`. (DB-04) · rojo visto: si
- **E-06** — Un ambiente que la política no declara se deniega con
  `DATABASE_ENVIRONMENT_UNRESOLVED`, y **ninguna** forma de ambiente no declarado —ausente, vacío,
  en blancos, con otra capitalización, con otro nombre, o un objeto donde va un texto— resuelve a
  DEV ni a `FULL`. (DB-05, §2) · rojo visto: si

### La clasificación, antes de ejecutar

- **E-07** — Las cinco clases de operación y los tres efectos son **dos campos distintos**:
  `operationClass` con sus cinco valores, `effectiveSideEffects` con los tres de
  `tools.SIDE_EFFECTS` y ninguno más. La tabla cerrada de nueve verbos cubre las cinco clases, y la
  traducción de cada verbo a su clase y a su efecto es la de la tabla de arriba —`CREATE`/`ALTER` a
  MUTATING, `DROP`/`TRUNCATE` a DESTRUCTIVE, `MIGRATION` a MUTATING salvo declarada irreversible—.
  (§4, §2 del v2) · rojo visto: si
- **E-08** — Un verbo que la tabla no declara se deniega con
  `DATABASE_OPERATION_UNCLASSIFIED`, y lo mismo un verbo ausente, vacío, en blancos, con otra
  capitalización o que no sea texto. En particular `SHOW`, `DESCRIBE` y `EXPLAIN` **no** están en la
  tabla y fallan cerrados: no son portables entre motores. (DB-27)
  · rojo visto: si
- **E-09** — El barrido de la sentencia sólo puede **subir** la clase: un `SELECT` declarado con un
  `UPDATE` adentro sale MUTATING, y un `UPDATE` declarado con un `SELECT` adentro sigue siendo
  MUTATING. · rojo visto: si
- **E-10** — Una sentencia con varias sentencias toma la clase más alta de todas, y si alguna no se
  puede clasificar se deniega el pedido entero. · rojo visto: si
- **E-11** — Un `DELETE` cuyo alcance no se puede establecer es `DESTRUCTIVE`, no `MUTATING`: con
  `WHERE` es MUTATING, sin `WHERE` es DESTRUCTIVE, y sin sentencia también.
  · rojo visto: si
- **E-12** — La decisión se toma **antes** de la ejecución: `resolver()` no importa ningún driver,
  no abre ninguna conexión, no llama al almacén de secretos y no ejecuta nada. Se verifica sobre el
  módulo, no sobre una salida. (DB-28, §4) · rojo visto: si

### DEV, que es FULL y no es sin restricciones

- **E-13** — `SELECT` en DEV se permite. (DB-06) · rojo visto: si
- **E-14** — `UPDATE` en DEV se permite. (DB-07) · rojo visto: si
- **E-15** — `ALTER` en DEV se permite, y si hace falta aprobación lo dice la compuerta de riesgo y
  no el ambiente. (DB-08) · rojo visto: si
- **E-16** — Una operación destructiva en DEV sigue pasando por la compuerta que ya existe: el nivel
  sale de `tools.derivar_riesgo` y `approvalRequired` de `tools.exige_aprobacion_humana`, con la
  escala de `tools.RIESGOS` y **sin una segunda escala**. Un `DROP` en DEV sale permitido por el
  ambiente y con aprobación exigida. Y los cuatro valores que la implementación actual devuelve van
  clavados exactos —READ_ONLY HIGH sin aprobación; MUTATING HIGH sin aprobación fuera de PRD;
  MUTATING en PRD CRITICAL con aprobación; DESTRUCTIVE CRITICAL con aprobación—, medidos y no
  supuestos, para que tocar `derivar_riesgo` obligue a volver acá. (DB-09)
  · rojo visto: si
- **E-17** — El descubrimiento de esquema en DEV es `READ_ONLY`, se permite, y puede preceder a
  cualquier mutación. (DB-29) · rojo visto: si

### QA, HML y PRD

- **E-18** — `SELECT` se permite en los tres. (DB-10, DB-16, DB-20) · rojo visto: si
- **E-19** — `INSERT`, `UPDATE` y `DELETE` se deniegan en los tres con
  `DATABASE_WRITE_NOT_ALLOWED`. (DB-11, DB-12, DB-13, DB-17, DB-21, DB-22)
  · rojo visto: si
- **E-20** — `CREATE`, `ALTER`, `DROP` y `TRUNCATE` se deniegan en los tres con
  `DATABASE_DDL_NOT_ALLOWED`. (DB-14, DB-18, DB-23) · rojo visto: si
- **E-21** — La ejecución de una migración se deniega en los tres con
  `DATABASE_MIGRATION_NOT_ALLOWED`. (DB-15, DB-19, DB-24) · rojo visto: si
- **E-22** — Los tres siguen sirviendo para inspección de esquema, de metadata, consultas de
  diagnóstico y de validación, y eso se expresa con `SELECT` contra el catálogo: la tabla es
  **cerrada**, y los verbos de metadata de un motor concreto —`SHOW`, `DESCRIBE`, `EXPLAIN`— no se
  asumen portables y caen en `DATABASE_OPERATION_UNCLASSIFIED` en los cuatro ambientes, DEV
  incluido. (DB-30) · rojo visto: si
- **E-23** — 🔴 **El producto entero, no la lista del pedido**: para los tres ambientes de
  promoción, por cada verbo de la tabla de clases, ninguna operación que no clasifique `READ_ONLY`
  sale con `allowed: true`, y cada denegación lleva el estado que le corresponde a su clase.
  · rojo visto: si

### Los perfiles y los secretos

- **E-24** — Cada ambiente resuelve su propio perfil, y dos ambientes de la misma base lógica no
  comparten instancia: el perfil de uno no contesta por el otro. (DB-26)
  · rojo visto: si
- **E-25** — Sin perfil para ese par de base lógica y ambiente, `DATABASE_PROFILE_NOT_FOUND`, y el
  archivo que el harness instala está **vacío**. (§10) · rojo visto: si
- **E-26** — El perfil lleva sólo referencias: ningún campo del perfil ni de la salida de ningún
  camino del módulo lleva un valor con forma de credencial, y el barrido corre sobre **toda** salida
  del módulo. (DB-25, §6) · rojo visto: si
- **E-27** — `resolver()` no habla con el almacén de secretos, y la única función que lo hace es la
  del borde de ejecución. (§6) · rojo visto: si
- **E-28** — Una referencia que el almacén no tiene da `DATABASE_SECRET_UNRESOLVED` en el borde de
  ejecución, y la resolución del ambiente no cambia por eso. (§10) · rojo visto: si

### La promoción y las fronteras

- **E-29** — Ninguna migración se aplica en QA, HML ni PRD por ningún camino, y la denegación nombra
  que el cambio va como artefacto versionado por el proceso de despliegue. (§8)
  · rojo visto: si
- **E-30** — El flujo DEV-first está declarado y **ordenado**, el descubrimiento precede a la
  mutación, y el orden no es una lista suelta sino el que el módulo expone. (§7)
  · rojo visto: si
- **E-31** — No se crea ningún agente ni ninguna skill: la cuenta de las dos no cambia, los dos
  agentes y las cinco skills que el pedido nombra ya existen, y ningún archivo nuevo declara un
  dueño. (§9) · rojo visto: si
- **E-32** — La política es del harness: vive en `reglas/`, ningún archivo de agente ni de skill la
  declara ni la duplica, y esta capacidad no entra en la matriz normativa ni en el registro de
  controles. (§1, §9) · rojo visto: si

### Los estados y el fail-closed

- **E-33** — Los diez estados de falla existen, ninguno se solapa y ninguno viene con
  `allowed: true`. (§10) · rojo visto: si
- **E-34** — 🔴 **Todo dato faltante falla cerrado**: se recorre el producto de campos ausentes,
  vacíos y en blancos del pedido, y **ninguna** combinación produce `allowed: true`. (§10)
  · rojo visto: si
- **E-35** — Todo resultado conserva el ambiente, la base lógica, el verbo declarado, la
  `operationClass` **y** el `effectiveSideEffects` —los dos campos, siempre—, y `allowed` nunca es
  verdadero para una clase que el modo del ambiente no habilita. · rojo visto: si

### El contrato de los schemas

- **E-36** — El validador lee los dos schemas del pedido **tal como vinieron**: resuelve `$ref`
  local contra `$defs`, recorre los `$defs` usados y los que no, y hace cumplir
  `additionalProperties: false`. Con eso, un ambiente que la política no declara y un perfil con un
  campo de más —una contraseña en claro, por ejemplo— se **rechazan**. Lo que el validador no
  soporta lo dice: un `$ref` a otro archivo o a una URL, un `additionalProperties` con un schema
  como valor, un `$ref` que convive con otras reglas y un `additionalProperties: false` sin
  `properties`. Y la ampliación es aditiva: los contratos que ya existían siguen validando igual.
  · rojo visto: si

- **E-37** — La compuerta arranca en un **árbol instalado**, con `reglas/` colgando de
  `.claude/harness/reglas/<id>/` y no del repositorio. · rojo visto: sí

## Lo que cambió después de la primera refutación

La primera pasada dio **30 sostenidos, 4 contradichos —E-10, E-11, E-29, E-36— y 2 sin sustento
—E-23, E-26—**, más cinco hallazgos sin escenario. Lo que se arregló, escrito acá porque un
arreglo que vive sólo en el código y en los tests deja la spec mintiendo:

| Qué | Dónde queda |
|---|---|
| La ruta de una regla sale de `roster.ruta_de_regla` y no de `rutas.localizar` sin raíces | **E-37**, nuevo |
| `INTO`, `OUTFILE` y `DUMPFILE` suben el efecto de una lectura declarada | E-10 |
| `/*!` —que MySQL ejecuta— y un `statement` que no es texto se deniegan | E-10 |
| El `WHERE` de un `DELETE` se busca con profundidad de paréntesis y con los literales tapados | E-11 |
| `remediation` viaja en la salida en vez de ser una constante del módulo | E-29 |
| El contrato de la salida pasa a **seis** bloques, con `remediation` | E-32, E-35 |
| El estado de denegación específico de la clase se **deriva** y se asierta | E-23 |
| El barrido de fugas cubre **todas** las funciones públicas, derivadas del módulo | E-26 |
| `$ref` se resuelve hasta el final de la cadena y un ciclo se rechaza | E-36 |
| `additionalProperties: false` exige `properties` no vacío | E-36 |

## Lo que cambió después de la segunda refutación

La segunda dio **33 sostenidos, 3 contradichos —E-09, E-10, E-11— y 1 sin sustento —E-37, que
estaba construido y no escrito acá—**. Los tres contradichos tenían dos raíces, y las dos eran
fail-open en el módulo cuya doctrina entera es fail-closed:

**Una comilla bajaba la clase.** El barrido quitaba los comentarios **antes** de tapar los
literales, así que un `--` o un `/*` adentro de un literal se comía todo lo que seguía:

```
SELECT '--x' ; UPDATE t SET a=1     salia READ_ONLY y PERMITIDO en los cuatro ambientes
SELECT '--' ; DROP TABLE t          salia READ_ONLY y PERMITIDO en PRD
```

No es que el barrido no subiera: **bajaba**. Y no hay orden correcto entre dos pasadas —tapando
literales primero, la comilla de `-- it's fine` se aparea con la siguiente del texto y se traga lo
que haya en el medio—, así que ahora se recorre el texto **una sola vez** y en cada posición gana
lo que empieza primero, que es lo que hace un motor. Un literal o un comentario de bloque **sin
cerrar** deja el pedido sin clasificar: taparlo hasta el final escondería lo que venga después.

**El paréntesis que cierra la CTE perdía el alcance.** El arreglo anterior cubría "el `WHERE` está
en la CTE y el `DELETE` afuera" y no su imagen espejo:

```
WITH d AS (DELETE FROM a RETURNING *) SELECT * FROM d WHERE id > 5
```

Ese `DELETE` borra la tabla entera y salía `MUTATING` —HIGH sin aprobación en DEV, cuando
corresponde CRITICAL con aprobación— porque `max(0, profundidad - 1)` perdía la única señal de que
se había salido del alcance. Ahora un paréntesis que cierra más de lo que se abrió **termina** la
búsqueda, y se comprueban **todos** los `DELETE` de la sentencia, no el primero.

## Lo que cambió después de la tercera refutación

La tercera dio **34 sostenidos, 3 contradichos —E-09, E-10, E-11— y 0 sin sustento**. Otra vez una
sola raíz, y otra vez la misma especie: **el enmascarado conocía dos formas de encomillar y los
motores tienen cinco.**

```
SELECT $$--$$ AS c; DROP TABLE t       salia READ_ONLY y PERMITIDO en los cuatro ambientes
SELECT $tag$--$tag$ AS c; DROP TABLE t lo mismo, con el dollar-quoting con tag de postgres
SELECT 1 AS `--`; DROP TABLE t         lo mismo, con un alias de MySQL
SELECT 1 AS [--]; DROP TABLE t         lo mismo, con uno de T-SQL
DELETE FROM a WHERE id=$$--$$; DELETE FROM b   -> MUTATING, HIGH, sin aprobacion en DEV
```

Un `--` adentro de una forma que el barrido no conoce no es un comentario para el motor y sí para
el barrido, que se come el resto de la línea con el `;` adentro. Y `engine` es un string libre en
`database-profile.schema.json`: **ningún motor está fuera de alcance**.

🔴 **Dos cosas que este apartado afirmaba quedaron medidas como falsas en la cuarta refutación, y
se corrigen acá en vez de borrarse:**

- *"Para el corchete no es inerte… es una negación falsa, no un permiso falso."* Era las dos cosas.
  El mismo bucle que evitaba denegar `[a]]; DROP TABLE t]` de T-SQL permitía el `DROP` de
  `SELECT ARRAY[[1],[2]]; DROP TABLE t` en Postgres, donde `]]` no es un escape sino dos arrays
  que cierran.
- *"El `#` de MySQL queda sin manejar porque no manejarlo deniega de más."* También permitía de
  más: adentro de un `#` puede haber un `/*` que el barrido sí manejaba, y ése tapaba lo que
  venía detrás.

La refutación además atacó lo que ya estaba y aguantó: 21 sondas sobre `_alcance_desde` sin un solo
fail-open, 200.000 entradas aleatorias comprobando que el enmascarado conserva el largo y las
posiciones, y 300.000 comprobando que la cerradura de la comilla doblada es **inerte para las
formas simétricas** —lo es, y el código lo dice—. Para el corchete **no** es inerte, y el comentario
que decía lo contrario estaba mal: sin ella, `[a]]; DROP TABLE t]` —que es un solo identificador de
T-SQL— se parte y sale un `DROP` que nunca existió. Es una negación falsa, no un permiso falso, y
por eso ninguna aserción la agarraba.

Y encontró cuatro aserciones que probaban otra cosa, todas corregidas:

| Qué probaba | Qué prueba ahora |
|---|---|
| El riesgo en DEV, que es `HIGH/False` tanto para `READ_ONLY` como para `MUTATING` | La **clase** en DEV, que discrimina en las siete filas |
| `EFECTOS == tools.SIDE_EFFECTS`, con `EFECTOS is tools.SIDE_EFFECTS` ya en `True` | Que sean **el mismo objeto**, que es la proposición |
| E-33 verificaba dos de sus tres cláusulas | Los seis estados del resolvedor provocados, y ninguno con `allowed: true` |
| E-31 barría `bases.py` y el escenario habla de todos los archivos nuevos | Los **seis** archivos del cambio |

## Lo que cambió después de la cuarta refutación

La cuarta dio otra vez **34 sostenidos y 3 contradichos —E-09, E-10, E-11—**, con seis formas
nuevas de la misma especie:

```
SELECT 1--2; DROP TABLE t                       MySQL exige un blanco tras el segundo guion
SELECT 'a\' -- ' ; DROP TABLE t                 `\'` es comilla escapada en MySQL y en E'...'
SELECT 1 /* /* */ -- */ ; DROP TABLE t          Postgres ANIDA los comentarios de bloque
SELECT ARRAY[[1],[2]]; DROP TABLE t             `]]` no es un escape: son dos arrays que cierran
SELECT a$$b; DROP TABLE t; SELECT c$$d          `a$$b` es un identificador legal de MySQL
SELECT 1 # /*\n; DROP TABLE t; SELECT 1 /* */   el `#` esconde un `/*` que si se manejaba
```

### Se cambió el mecanismo, no se agregó la séptima forma

Cuatro pasadas seguidas encontraron **la misma especie** por una comilla distinta cada vez, y cada
arreglo agregó una forma esperando que fuera la última. No lo era y no iba a serlo: **dónde termina
un literal lo decide el dialecto**, y `engine` es un string libre. Un barrido de tokens no puede
contestar esa pregunta, y seguir agregando formas era aceptar una pasada más cada vez.

Así que el enmascarado **dejó de ser la red**:

```
_enmascarar          una AYUDA para no denegar de mas: que un DROP adentro de una cadena no suba
_candidatos_crudos   la RED: lee el texto sin enmascarar nada y toma el verbo que ABRE cada sentencia
clase final          el maximo entre las dos lecturas
```

Un error de enmascarado ahora sólo puede producir una **negación falsa** —la dirección que el
pedido de instalación declara aceptable— y nunca un permiso falso. Las seis formas de arriba, y
las de las tres pasadas anteriores, salen por la lectura cruda sin que el enmascarado sepa nada de
ellas.

🔴 **Sólo el verbo que ABRE cada sentencia, no todos los que aparecen.** El ataque siempre esconde
una *sentencia*, y una sentencia empieza por su verbo. Contar todos convertiría
`WHERE accion = 'DELETE'` en una operación destructiva, que es una negación falsa cara y evitable.
Y un primer token que la tabla no declara **se ignora** en la lectura cruda, porque partir el texto
crudo por `;` parte también los literales.

### Dos cosas que se sacaron, y por qué

- **El corchete dejó de ser una forma de comilla.** Como *quoting* es de T-SQL; en Postgres y MySQL
  es subíndice de array, y tratarlo como comilla hacía que `SELECT ARRAY[[1,2],[3,4]]` —nada
  exótico— cayera denegado en los cuatro ambientes. Con la lectura cruda ya no hace falta para la
  seguridad. Se eligió el error que le pasa al motor más usado, y el de T-SQL queda declarado.
- **Un `$$` sin cerrar ya no deja el texto sin establecer.** `SELECT $$PLSQL_LINE FROM dual` es una
  directiva válida de Oracle, no texto malformado. Una comilla sin cerrar sí lo es y se sigue
  denegando; un dollar-quote que no cierra simplemente no era un dollar-quote.

### Lo que el diseño cuesta, medido

**Un `;` adentro de un literal, seguido de un verbo de la tabla, se deniega.**

```
SELECT 'a''; DROP TABLE t' FROM t    ->  DESTRUCTIVE, denegado en promocion
```

Para Postgres eso es una sola sentencia —la comilla doblada no cierra— y para un motor que lea
`''` distinto son dos. **El harness no puede saber cuál**, y cuando las dos lecturas discrepan se
toma la peligrosa. Es lo que el pedido de instalación dice con todas las letras: *una negación
falsa es aceptable y un permiso falso no*. Está fijado en `E-09` bajo el nombre `EL_PRECIO`, junto
con la comprobación de que el enmascarado sigue leyendo esas sentencias como una sola —o sea que
el precio es sólo ése y no se pagó de más.

## Cómo se verifica

Los 37 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

🔴 **Primero en rojo, y con la suite entera corrida.** El pedido lo exige y es la única forma de que
la marca `rojo visto` de un cambio nuevo signifique algo sin inventar una mutación: se escribe
`tests/casos/33_bases_de_datos.py` **antes** de `bases.py`, se corre, y el grupo entero tiene que
fallar porque la capacidad no existe. Recién después se construye. Lo que la pasada de mutaciones
agrega arriba de eso es el rojo **por escenario**, que un rojo global no da.

Tres escenarios son **productos y no listas**, y son los que sostienen el cambio: E-06 recorre todas
las formas de ambiente no declarado, E-23 recorre ambientes × verbos para los tres ambientes de
promoción, y E-34 recorre las formas de dato faltante. Si alguno de los tres se degradara a una
lista, el resto de los escenarios seguiría en verde y el control dejaría de ser un control.

E-12, E-26 y E-27 se verifican **sobre el módulo** —qué importa, qué llama, qué no—, no sobre una
salida. Una promesa sobre lo que un módulo no hace no se prueba mirando lo que devolvió una vez.

### Lo que encontró la pasada de mutaciones

**69 mutaciones en la primera pasada, 11 mas en la segunda y 2 en la tercera; los 37 escenarios
tienen un rojo presenciado.** Cuatro no encontraron rojo en la
primera vuelta, y dos eran huecos del test:

```
E-06  sacar la guarda de `read is not True` no ponia nada en rojo: ninguna politica del
      fixture tiene un ambiente sin lectura, asi que la guarda -correcta, porque los dos modos
      implican lectura- no la miraba nadie. Ahora hay seis formas de ambiente DECLARADO pero
      no usable.
E-10  la guarda de "ninguna sentencia clasificable" era inalcanzable en los casos del test: el
      primer token ya filtra todo lo demas. El UNICO camino que llega es un `WITH` cuyo cuerpo
      no lleva ningun verbo de la tabla, y ese caso no estaba.
```

Y dos eran mutaciones sin efecto real, que es distinto de un hueco:

```
$ref no local   la guarda siguiente -"ese $defs no existe"- rechaza igual, asi que sacar la
                primera no cambia el veredicto. Cambia el MENSAJE, y un rechazo que no dice
                por que es un rechazo que alguien no sabe como arreglar: ahora se afirma el
                mensaje, que es lo que hace observable a la guarda.
el remedio      la mutacion estaba mal escrita y no matcheaba. Reapuntada, da rojo en E-29.
```

📌 Y cuatro decisiones salieron de correr los tests por primera vez, no de escribirlos:
`clasificar("DELETE")` sin sentencia es `DESTRUCTIVE` y no lo que decía la tabla —la entrada de la
tabla y la regla de alcance son dos cosas y ahora se afirman las dos—; el producto de E-23 da **18**
celdas permitidas y no 12; `connectionProfile` lleva los **siete** campos del contrato,
`passwordSecretRef` incluido, porque una referencia no es un valor; y el verbo se normaliza mientras
el ambiente no, que es una asimetría deliberada y ahora está declarada con su razón.

🔴 **Y cinco aserciones mías probaban otra cosa**, todas de la misma especie: barrían una palabra del
idioma en vez de los identificadores de la capacidad. `"database"` matcheaba la fila de P7 —*"Business
logic must not reside in the database layer"*—, `READ_ONLY` matcheaba dos skills que lo usan como
efecto de un contrato de tool, y la tabla de los cuatro nombres de ambiente matcheaba a las skills de
despliegue, que los nombran con todo derecho. **El sujeto de un barrido son los identificadores de lo
que se quiere encontrar, no una palabra que el dominio también usa.**

## Riesgos conocidos

- **Un barrido no es un parser, y se dice.** Una sentencia cuya clase el barrido no pueda establecer
  se deniega. Eso significa que habrá SQL legítimo denegado, y es la dirección correcta del error.
  El día que esto necesite precisión, lo que hace falta es un parser del motor, no aflojar el
  barrido.
- **Nadie puede usar esto todavía.** No hay tool de base de datos, no hay perfiles y
  `permisos-por-capacidad.json` no declara ninguna capacidad de base de datos. Lo que se instala es
  la compuerta; lo que pase por ella no existe aún.
- **La capitalización de los ambientes es estricta a propósito**, y va a molestar el primer día que
  un proyecto escriba `prod`. La alternativa es peor.
- **`DATABASE_CONNECTION_FAILED` y `DATABASE_PERMISSION_DENIED` no los produce este módulo.** Están
  declarados para que quien ejecute los devuelva, y hasta que exista ese ejecutor son dos estados
  sin productor — igual que trece de los eventos del Bloque 4. Se anota.
