# Los ambientes de base de datos en el harness

Esta capacidad contesta una sola pregunta, y la contesta **antes** de que se abra una conexión:
¿esta operación puede correr en este ambiente?

```
DEV  ->  FULL
QA   ->  READ_ONLY
HML  ->  READ_ONLY
PRD  ->  READ_ONLY

lo que la politica no declara  ->  DENY / DATABASE_ENVIRONMENT_UNRESOLVED
```

## Por qué la primera barrera no son los permisos de la base

Un usuario de solo lectura en PRD es una buena práctica y **no es un control del harness**: nadie lo
verifica desde acá, nadie se enteraría si cambiara, y el día que un proyecto configure el mismo
usuario para los cuatro ambientes —que es exactamente lo que pasa— no queda ninguna barrera.

Los permisos nativos son la **segunda** barrera. Esta es la primera.

## Esto no es una regla de ES0901

Las ocho reglas instaladas —G1, G2 y D1 a D6— verifican **cumplimiento**: miran evidencia y dicen si
una aplicación cumple. Esto es otra cosa: es una capacidad de runtime que **decide y deniega**. No
tiene señal de aplicabilidad, no figura en `control-registry.json` y no entra en la matriz normativa.

Toca tres reglas en el futuro y ninguna hoy: `G1` (qué motor y qué versión están homologados), `P7`
(sin lógica de negocio en la base) y `M2` (configuración de ambiente fuera del código).

## Dos dimensiones, no una escala

La tentación es fundir las cinco clases de operación y los tres efectos en una escala ordenada de
cinco. Eso sería inventar una segunda doctrina de riesgo, y **dos escalas de riesgo en el mismo
harness es una escala**: la segunda se usa para justificar lo que la primera no dejaba pasar.

```
operationClass        decide el PERMISO   se cruza contra el bit del ambiente
effectiveSideEffects  decide el RIESGO    se le pasa a tools.derivar_riesgo
```

La traducción:

| verbo | clase | efecto | bit que exige |
|---|---|---|---|
| `SELECT` | `READ_ONLY` | `READ_ONLY` | `read` |
| `INSERT`, `UPDATE` | `MUTATING` | `MUTATING` | `write` |
| `DELETE` con `WHERE` | `MUTATING` | `MUTATING` | `write` |
| `DELETE` sin `WHERE`, o sin sentencia | `DESTRUCTIVE` | `DESTRUCTIVE` | `write` |
| `CREATE`, `ALTER` | `DDL` | `MUTATING` | `ddl` |
| `DROP`, `TRUNCATE` | `DDL` | `DESTRUCTIVE` | `ddl` |
| `MIGRATION` | `MIGRATION` | `MUTATING` | `migrations` |
| `MIGRATION` declarada irreversible | `MIGRATION` | `DESTRUCTIVE` | `migrations` |

## El riesgo sale de la compuerta que ya existe

DEV es `FULL` y `FULL` **no es sin restricciones**. Un `DROP SCHEMA` en DEV está permitido por el
ambiente y puede seguir necesitando que una persona decida.

Eso no se construyó de nuevo. La operación se traduce al contrato que `tools.py` ya sabe leer:

```yaml
sideEffects:     el effectiveSideEffects de arriba
networkAccess:   true          una base esta del otro lado de la red
secretsRequired: true          hace falta una credencial para ejecutar
blastRadius:
  scope: external-system
  productionImpact: true       solo cuando el ambiente es PRD
```

Y lo que la implementación actual devuelve, **medido**:

```
READ_ONLY    cualquier ambiente  ->  HIGH,     sin aprobacion
MUTATING     DEV / QA / HML      ->  HIGH,     sin aprobacion
MUTATING     PRD                 ->  CRITICAL, con aprobacion
DESTRUCTIVE  cualquier ambiente  ->  CRITICAL, con aprobacion
```

Toda operación de base de datos queda al menos en `HIGH` porque toca secretos y sale a la red. Eso
es lo que la derivación **devuelve**, no algo que esta capacidad agregue.

> 🔴 Son dos decisiones distintas y las toman dos mecanismos distintos. **El ambiente** dice si la
> operación puede correr; **la compuerta de riesgo** dice si, pudiendo correr, hace falta que
> alguien la apruebe.

## La clasificación se declara y se verifica

```
verbo declarado
      ↓
tabla CERRADA de nueve verbos
      ↓
barrido opcional de la sentencia
      ↓
efecto efectivo = el MAXIMO de los dos
```

🔴 **El barrido sólo puede subir.** Es la misma asimetría que ya hace cumplir
`tools.controlar_riesgo`: *declarar de menos no baja el riesgo, lo esconde*. Declarar `SELECT` con un
`UPDATE` adentro no convierte un `UPDATE` en un `SELECT`.

🔴 **Y un barrido no es un parser.** Lo que no puede clasificar se **deniega**:
`DATABASE_OPERATION_UNCLASSIFIED`. Una negación falsa es aceptable; un permiso falso no. Eso
significa que habrá SQL legítimo denegado, y es la dirección correcta del error. El día que esto
necesite precisión, lo que hace falta es un parser del motor, no aflojar el barrido.

El barrido cubre varias sentencias separadas por `;`, un `WITH` que termina en una operación que
muta, los comentarios —que se quitan, porque quitar de más sube el impacto y quitar de menos lo
baja—, y el alcance de un `DELETE`. Si **alguna** sentencia del pedido no se puede clasificar, se
deniega el pedido **entero**.

### La tabla es cerrada

```
SELECT  INSERT  UPDATE  DELETE  CREATE  ALTER  DROP  TRUNCATE  MIGRATION
```

Nueve, y nada más. `SHOW`, `DESCRIBE` y `EXPLAIN` **no entran**: no son portables entre motores, y
`EXPLAIN ANALYZE` en algunos **ejecuta la sentencia**. La inspección de esquema y de metadata que los
tres ambientes de promoción sí permiten se expresa con `SELECT` contra el catálogo. Cuando alguien
necesite el verbo de un motor concreto, se agrega **deliberadamente**, con el motor nombrado.

## El ambiente es exacto

```
DEV   valido
dev   DATABASE_ENVIRONMENT_UNRESOLVED
Prd   DATABASE_ENVIRONMENT_UNRESOLVED
PROD  DATABASE_ENVIRONMENT_UNRESOLVED
```

No se normaliza la capitalización ni se quitan los blancos. Puede parecer hostil y es lo correcto:
normalizar el identificador de un ambiente es el atajo por el que `prod`, `Prd` y `PROD` acaban
resolviendo a algo. Si un proyecto usa otros nombres, los declara; no se adivinan.

## La política es del harness; los perfiles, del proyecto

```
reglas/database-environment-access-policy.json   del HARNESS. Un proyecto no la edita
reglas/database-profiles.json                    del PROYECTO. Se instala VACIO
```

Un proyecto que pudiera declarar que su PRD es `FULL` no tiene ninguna protección, y el archivo se
llamaría política sin ser una. Los perfiles son lo contrario: el harness no puede saber en qué host
vive la base de nadie, así que se instalan vacíos y sin perfil hay `DATABASE_PROFILE_NOT_FOUND`.

🔴 **Cada par de base lógica y ambiente es una entrada distinta.** `main-database/DEV` y
`main-database/QA` no son la misma. Asumir que dos ambientes comparten instancia es cómo un `UPDATE`
que alguien creía de QA llega a PRD.

Los dos contratos —`comun/schemas/database-environment-access-policy.schema.json` y
`database-profile.schema.json`— llevan `additionalProperties: false`, y eso no es azúcar: es lo que
hace que un ambiente que la política no declara se rechace, y que un perfil con una contraseña en
claro se rechace.

## El resolvedor no resuelve secretos

`resolver()` devuelve **referencias**: `usernameSecretRef`, `passwordSecretRef`. No importa un
driver, no abre una conexión, no ejecuta una sentencia y **no importa el almacén de secretos**.

La función del borde de ejecución, `resolver_secreto(referencia, almacen)`, **recibe** el almacén.
Con eso, *el resolvedor no puede conseguir una credencial* es una propiedad de la forma del archivo
y no una costumbre que alguien tenga que recordar.

Y el valor no vuelve en el resultado: vuelve si la referencia se pudo resolver. Un mensaje que dice
*"no se pudo resolver DB_PASSWORD=abc123"* acaba de publicar el secreto en la consola, en la
transcripción de la sesión y en el contexto del modelo.

## El flujo DEV primero

```
resolve-dev-profile
 -> schema-discovery
 -> change-plan
 -> migration-artifact
 -> risk-classification
 -> apply-in-dev
 -> schema-validation
 -> tests
 -> promotion-artifact
```

DEV es el único ambiente donde el harness puede hacer un cambio directo. QA, HML y PRD **no se mutan
nunca** por esta vía: un cambio de base para esos ambientes viaja como artefacto de migración
versionado por el proceso de despliegue que ya existe.

## Los diez estados, y los cuatro que no son de acá

```
DATABASE_ENVIRONMENT_UNRESOLVED     el resolvedor
DATABASE_PROFILE_NOT_FOUND          el resolvedor
DATABASE_OPERATION_UNCLASSIFIED     el resolvedor
DATABASE_WRITE_NOT_ALLOWED          el resolvedor
DATABASE_DDL_NOT_ALLOWED            el resolvedor
DATABASE_MIGRATION_NOT_ALLOWED      el resolvedor

DATABASE_SECRET_UNRESOLVED          el borde de ejecucion
DATABASE_CONNECTION_FAILED          el borde de ejecucion
DATABASE_PERMISSION_DENIED          el borde de ejecucion
DATABASE_SCHEMA_DISCOVERY_FAILED    el borde de ejecucion
```

Los cuatro últimos necesitan una conexión, un almacén o una base contestando. Están declarados acá
para que quien ejecute los devuelva y no invente otros. **Ninguno viene con `allowed: true`.**

## Lo que todavía no se puede usar

No hay tool de base de datos, no hay perfiles cargados en ningún proyecto, y
`permisos-por-capacidad.json` **no declara** ninguna capacidad de base de datos. Eso último es un
hueco correcto: la doctrina de `tools.py` es que una capacidad sin permisos declarados devuelve
`MISSING_CONTEXT`, no un permiso. Se agrega cuando exista la tool, no antes.

Lo que se instaló es la compuerta. Lo que pase por ella todavía no existe.
