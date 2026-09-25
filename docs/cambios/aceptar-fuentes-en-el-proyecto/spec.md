# Bloque 1 — una fuente oficial se puede aceptar en el proyecto

**Estado:** verificado y cerrado · **Fecha:** 25-09-2026 · **Bloque:** 1, leyendo al 3

## Qué problema resuelve

En un proyecto instalado, ninguna fuente gestionada puede llegar a `CURRENT`. Lo reportó el proyecto
licba (0.23.0, `comun` + `desarrollo`). La persona responsable entregó los estándares por el canal
oficial, que son los adjuntos de la Ficha APPLICDCON-1. El proyecto los registró con
`fuentes --archivo`, y el reporte de seguridad igual queda `BLOCKED` por B-001: «El conocimiento de
ES0902 no se puede tratar como vigente (FRESHNESS_UNVERIFIED)».

Las tres causas están verificadas en el código el 25-09-2026:

1. **Nadie puede cargar el hash de referencia.** `source-registry.json` trae `sha256: null` en las
   seis fuentes. Con la versión igual, `frescura._estado_de` devuelve `FRESHNESS_UNVERIFIED`, y
   ningún comando registra un hash observado. El registro es del harness: si un proyecto lo edita,
   el `-Update` siguiente lo pisa.
2. **El extracto no llega al proyecto.** `install.ps1` no copia `normativa/`, así que en un
   proyecto `registro_fuentes.ruta_de_extracto` devuelve `None`. Esta causa sola ya alcanza para que
   nada llegue a `CURRENT`.
3. **Una regresión no se puede decidir.** La única decisión que se lee es `POSTPONE`, y `_pospuesta`
   no la aplica a una regresión.

Lo que pedía el reporte sobre ES0901 no se construye como solución para licba. El 25-09-2026 el
usuario confirmó que **la vigente es 6.3**: la Ficha de licba trae una 6.2 vieja, y lo correcto es que
esa fuente siga en `VERSION_REGRESSION`. Aun así, aceptar una regresión tiene que ser posible, con
una decisión explícita y a la vista.

## Qué queda afuera

- **Cargar hashes a mano en `source-registry.json`.** Sin el original presente, eso es exactamente
  lo que el registro existe para impedir.
- **Relajar `_estado_de`.** Un hash ausente sigue siendo `FRESHNESS_UNVERIFIED`. La aceptación no es
  una rama que se saltea la regla: cambia contra qué identidad se compara, y la regla sigue igual.
- **Promover conocimiento.** Aceptar una versión que el harness no tiene extraída (ES0901 6.2, o una
  6.4 futura) deja la fuente en `KNOWLEDGE_PROMOTION_INCOMPLETE`. Construir los derivados de esa
  versión es el slice de promoción, que no es este.
- **ES0901 6.2 en licba.** Se deja como regresión, por la confirmación del usuario.
- **Migrar `sources-state/1.1`.** Los campos nuevos son opcionales, así que un estado viejo sigue
  validando y no hay nada que migrar.

## Las decisiones, y por qué

### La aceptación es una decisión `APPLY`, y vive en el estado del proyecto

`sources-state/1.1` ya declaraba `APPLY` en el enum de `decisions`, y nada lo usaba. Ahora:

```
dev-harness.py fuentes --archivo <dir> --aceptar ES0902 [--por <persona>] [--regresion]
dev-harness.py fuentes APPLICDCON-1 --aceptar ES0902
```

La aceptación se hace sobre la observación **de esa misma corrida**, nunca sobre una guardada: se
acepta lo que se acaba de mirar. Guarda la identidad observada en `decisions.<ID>` de
`.claude/harness.fuentes.json`:

- `observed_version`, `observed_sha256`, `attachmentId` y `filename`
- `channel`: `jira:<FICHA>` o `archivo:<dir>`
- `by`: `--por`, o el `usuario` de `harness.config.json`; sin ninguno de los dos, no hay aceptación
- `at`
- `overridesRegistryVersion`: solo si se aceptó una regresión

`fuentes` ya reusa las `decisions` de la corrida anterior, y ni `-Update` ni `-Doctor` tocan ese
archivo. La aceptación sobrevive sin nada más.

Se descartó escribirla en `source-registry.json`, porque es del harness: `-Doctor` la marcaría como
alterada y el `-Update` siguiente la pisaría.

### Contra qué se compara

Una aceptación **vigente** reemplaza a la versión y el hash de fábrica como referencia. El resto del
árbol de `_estado_de` no cambia: versión, hash, extracto y derivados se comparan contra esa
referencia.

La aceptación deja de valer si cambia cualquiera de estas cosas:

- la versión observada;
- el hash observado;
- el adjunto o el archivo (cuando se registró);
- la versión de fábrica que la regresión pisó (con `overridesRegistryVersion`).

Tampoco vale si falta la versión o el hash. En todos esos casos la fuente vuelve a compararse contra
la fábrica, que es exactamente el comportamiento de hoy.

🔴 **La aceptación no tapa una alerta de integridad.** Si la fábrica declara un hash para esa misma
versión y el observado es otro, el estado sigue siendo `SOURCE_INTEGRITY_ALERT`.

### Qué se puede aceptar

Solo se acepta una observación que se encontró, con versión y con hash. Si la fábrica ya tiene hash
para esa versión, además tiene que coincidir.

Se rechaza en estos casos:

- sin canal;
- `SOURCE_MISSING`;
- `VERSION_UNRESOLVED`;
- sin hash observado;
- `SOURCE_INTEGRITY_ALERT`;
- `SOURCE_CHANGED_SAME_VERSION`;
- `RETIRED`.

Una versión **anterior** a la de fábrica se rechaza sin `--regresion`. Con `--regresion` queda
registrada qué versión de fábrica se pisó.

Si se rechaza, el comando sale con 2 y no escribe nada.

### Aceptar lo que el harness no tiene extraído es `KNOWLEDGE_PROMOTION_INCOMPLETE`

Si la aceptación es vigente pero el extracto activo o algún derivado declaran otra versión, el estado
es `KNOWLEDGE_PROMOTION_INCOMPLETE`: el documento ya se aceptó y el harness todavía no promovió su
conocimiento. Bloquea, y `stale_derived` dice cuáles derivados faltan. Sin aceptación, ese mismo
desacuerdo sigue siendo `UPDATE_AVAILABLE`, como hoy.

En el estado, `registry_version` sigue siendo la de fábrica, y la versión aceptada va aparte en
`acceptance`. Así se ve qué esperaba la fábrica.

### Los extractos se instalan

`install.ps1` copia `normativa/extractos/` a `.claude/harness/normativa/extractos/`, y el
`extract` del registro se resuelve en el proyecto igual que en el repositorio. La cuarta condición
sigue siendo la misma en los dos árboles: la versión que el extracto declara en su encabezado.

La alternativa descartada era declarar las fuentes `norma` como de fábrica, y en un proyecto evaluar
la cuarta condición contra la versión que declaran los derivados instalados. Se descartó por tres
razones:

- La regla de las cinco condiciones quedaba con dos definiciones, una por árbol. La que se aplicaba
  en el proyecto era la más débil, porque los derivados ya se miran en la quinta condición.
- Hacía falta que el código supiera en qué árbol está.
- Los extractos son destilado propio en markdown. El `.gitignore` y el `LEEME` de `normativa/fuentes/`
  ya dicen que son lo que se distribuye. Los PDF siguen sin instalarse.

### El reporte de seguridad muestra la procedencia

`productores.desde_frescura` lleva la aceptación en los detalles del `KNOWLEDGE_STATE`. La sección
de conocimiento de `security-summary.json`, y sus secciones en el md y el html, suman esto:

- el SHA-256 aceptado
- el canal
- quién aceptó y cuándo
- la versión que esperaba el registro

La versión que se muestra es la aceptada. Con la fuente aceptada, `CURRENT` no bloquea, así que
B-001 desaparece sin tocar la regla de bloqueo.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/orquestacion/frescura.py` | `aceptacion_vigente`, `aceptable`, `decision_de_aceptacion`, referencia aceptada y `KNOWLEDGE_PROMOTION_INCOMPLETE` |
| `harnesses/desarrollo/bin/dev-harness.py` | `fuentes --aceptar <ID[,ID]> [--por] [--regresion]` y el canal en `ficha.channel` |
| `comun/schemas/source-state.schema.json` | Campos opcionales en `decisions`, `acceptance` por fuente y `ficha.channel` |
| `harnesses/desarrollo/bin/reporte_seguridad/productores.py`, `resumen.py`, `reporte.py` | La procedencia en el conocimiento |
| `comun/schemas/security-summary.schema.json` | Los campos de procedencia de `knowledge` |
| `install.ps1` | Copia `normativa/extractos/` |
| `tests/casos/57_aceptar_fuentes.py` | Los escenarios del resolvedor, la CLI y el reporte |
| `tests/casos/57-aceptar-fuentes-instalador.ps1` | Los escenarios del proyecto instalado |

## Escenarios verificables

### Aceptar

- **E-01** — En el repositorio, `fuentes --archivo <dir> --aceptar ES0902` sobre un original 6.2 deja
  ES0902 en `CURRENT`. En `decisions.ES0902` queda `APPLY` con la versión, el SHA-256, el archivo, el
  canal `archivo:<dir>`, quién y cuándo. · rojo visto: si
- **E-02** — Una segunda corrida de `fuentes --archivo <dir>`, sin `--aceptar`, sobre el mismo
  original, deja ES0902 en `CURRENT`: la aceptación se reusa. · rojo visto: si
- **E-03** — Si cambia un byte del original aceptado, la aceptación deja de valer: ES0902 vuelve a
  `FRESHNESS_UNVERIFIED` y la evidencia lo dice. · rojo visto: si
- **E-04** — Si la versión observada pasa a otra (un original 6.3), la aceptación deja de valer y el
  estado se compara contra la fábrica. · rojo visto: si
- **E-05** — Con la misma versión y el mismo hash pero otro `attachmentId`, la aceptación deja de
  valer. · rojo visto: si
- **E-06** — `--aceptar` sale con 2 y no escribe nada en estos casos: sin canal, con la fuente
  ausente, sin versión, sin hash observado, y sin `--por` ni `usuario` configurado. · rojo visto: si
- **E-07** — Con una decisión `APPLY` escrita a mano sin hash, o con otra versión, el estado no pasa
  a `CURRENT`. No hay camino de evidencia ausente a `CURRENT`. · rojo visto: si
- **E-08** — Con un hash de fábrica para la misma versión distinto del observado, `--aceptar` sale con
  2. Una decisión `APPLY` escrita a mano no tapa `SOURCE_INTEGRITY_ALERT`. · rojo visto: si

### Regresiones y promoción

- **E-09** — Sobre una regresión (ES0901 6.2 contra 6.3 de fábrica), `--aceptar` sin `--regresion`
  sale con 2 y la fuente sigue en `VERSION_REGRESSION`. · rojo visto: si
- **E-10** — Con `--regresion`, la decisión registra `overridesRegistryVersion = 6.3`. El estado es
  `KNOWLEDGE_PROMOTION_INCOMPLETE` y bloquea. `registry_version` sigue en 6.3, `acceptance.version`
  es 6.2 y `stale_derived` nombra los derivados de 6.3. · rojo visto: si
- **E-11** — Si la versión de fábrica deja de ser la que la regresión pisó, la aceptación deja de
  valer. · rojo visto: si
- **E-12** — Aceptar una versión posterior a la de fábrica, con un extracto que declara la anterior,
  da `KNOWLEDGE_PROMOTION_INCOMPLETE`. Sin aceptación, da `UPDATE_AVAILABLE`. · rojo visto: si

### Sin aceptación, como hoy

- **E-13** — Sin ninguna decisión, los estados y la evidencia de las seis fuentes reales son los
  mismos que devuelve la resolución de 0.23.0 sobre el mismo directorio: ES0902
  `FRESHNESS_UNVERIFIED`, y ES0901 y ES0903 `VERSION_REGRESSION` con originales 6.2 y 2.1.
  · rojo visto: si
- **E-14** — `POSTPONE` sobre la misma identidad de un `UPDATE_AVAILABLE` da `ACKNOWLEDGED_PENDING`,
  que bloquea. Sobre otra identidad, no alcanza. · rojo visto: si
- **E-15** — Una entrada sin versión de fábrica, con la fuente observada, da `NEW_SOURCE`. Aceptada,
  con extracto y derivados en esa versión, da `CURRENT`. · rojo visto: si

### El proyecto instalado

- **E-16** — Después de instalar, `.claude/harness/normativa/extractos/` tiene los seis extractos,
  cada uno con la misma línea de versión que en el repositorio, y `fuentes --archivo` no avisa de
  ningún extracto faltante. · rojo visto: si
- **E-17** — En un proyecto instalado, `fuentes --archivo <dir> --aceptar ES0902` con un original
  6.2 deja ES0902 en `CURRENT`. Es la reproducción del bug. · rojo visto: si
- **E-18** — Después de un `-Update`, `harness.fuentes.json` conserva la aceptación, ES0902 sigue en
  `CURRENT` en la corrida siguiente, y `-Doctor` no marca ese archivo. · rojo visto: si

### El reporte de seguridad

- **E-19** — Con ES0902 aceptada, `seguridad <TAREA> --conocimiento --reporte` no tiene ninguna
  condición de bloqueo de conocimiento. `knowledge` trae la versión, el SHA-256, el canal, quién,
  cuándo y la versión que esperaba el registro, y el md los muestra en «Conocimiento normativo».
  · rojo visto: si
- **E-20** — Sin aceptación, el mismo reporte sigue teniendo la condición de conocimiento con
  `FRESHNESS_UNVERIFIED`. · rojo visto: si

### Contrato y presentación

- **E-21** — Un `harness.fuentes.json` con una aceptación valida contra `sources-state/1.1`, y un
  estado de 0.23.0 sin los campos nuevos también. Una clave no declarada dentro de la decisión se
  rechaza. · rojo visto: si
- **E-22** — La salida de `fuentes --aceptar` sin `--json` está en español y dice qué se aceptó,
  quién y por qué canal. Los estados salen en su forma canónica. · rojo visto: si
- **E-23** — `.\tests\Invoke-Tests.ps1` sale con 0. · rojo visto: no consta

## Cómo se verifica

Todos los escenarios van por la suite:

- E-01 a E-15 y E-19 a E-22, en `tests/casos/57_aceptar_fuentes.py`.
- E-16 a E-18, que necesitan un proyecto instalado, en `tests/casos/57-aceptar-fuentes-instalador.ps1`.
- E-23 es la suite misma.

Ningún escenario lleva `· verificación: lectura`.

## Riesgos conocidos

- **Una aceptación es tan buena como quien la da.** El harness registra quién, cuándo y por qué
  canal, y la invalida si el documento cambia. Lo que no puede saber es si el documento que se
  aceptó era de verdad el vigente. Lo de ES0901 en licba lo muestra: la Ficha traía uno viejo.
- **`--regresion` es la salida fácil.** Quedó explícita, registrada y en el estado. Pero nadie la
  impide.
- **Instalar los extractos los hace legibles en el proyecto.** Son destilado propio y públicos en el
  repositorio, así que no es una fuga. Sí es una superficie nueva que `-Update` tiene que mantener.
