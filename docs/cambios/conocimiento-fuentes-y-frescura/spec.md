# El sustrato de conocimiento confiable: fuentes, integridad y frescura

**Estado:** especificado · **Fecha:** 2026-09-23

## Qué problema resuelve

El Bloque 1 arranca con las integraciones y termina ahí. Nada en el harness sabe **de qué
documento salió lo que el harness afirma**, ni si ese documento sigue siendo el que se extractó.

Hoy eso se ve en tres lugares:

- `normativa/extractos/ES0902.md` dice «Versión 6.2 · extractado el 2026-08-12» en prosa, y esa
  línea no la lee ningún módulo. Si mañana la DGISIS publica 6.3, el harness sigue contestando
  con 6.2 y no tiene cómo enterarse.
- `harnesses/desarrollo/reglas/control-registry.json` tiene 42 controles y cada uno declara
  `normativeSources[{standard, version}]`. Son 42 declaraciones de versión que nadie compara
  contra nada: no existe el lado contra el cual compararlas.
- `gcba-it-normative-baseline.json` declara `ES0901 6.3` y `ES0902 6.2` a mano. Es el único
  lugar del harness que dice qué versión tiene cargada, y lo dice sin hash, sin fecha de
  verificación y sin canal de origen.

El resultado es que el harness **no puede distinguir estar desactualizado de estar al día**. Y
esa es la peor de las dos formas de estar desactualizado: la otra, saberlo, es tolerable.

Este cambio construye el sustrato determinista de esa distinción —registro de fuentes, índice
inverso de procedencia, descubrimiento, integridad y resolución de frescura— y nada más.

## Qué queda afuera

- **La construcción de candidatos, `dev-knowledge-builder`, la refutación y la promoción.** El
  pedido de instalación lo dice explícitamente: primero el sustrato determinista, y el agente
  no se genera antes. Un constructor sin registro de fuentes construye contra nada.
- **El gate de `READY` del Bloque 3 y los `knowledgeGaps[]`.** Acá se resuelve y se emite el
  estado; conectarlo al plan es el slice de adapters. Emitir el estado y bloquear el plan son
  dos cambios con dos formas de fallar distintas, y mezclarlos hace que un test verde no diga
  cuál de los dos anda.
- **SessionStart y las decisiones (`aplicar` / `posponer`).** El aviso necesita un estado en
  disco que todavía no existe. Se construye el archivo primero y se lo lee después.
- **`--html`.** El pedido lo nombra y no dice quién lo lee. El harness no emite HTML en ninguna
  parte; una salida sin lector es una superficie que hay que mantener para nadie.
- **El árbol `tecnologias/`.** No existe todavía. El registro admite `kind: tecnologia` porque
  el schema lo declara, y no se inventa ninguna entrada: una fuente sin documento es una fuente
  que nadie puede verificar.
- **Instalar `normativa/` en un proyecto.** `normativa/fuentes/LEEME.md` dice que la carpeta es
  de la fábrica y que el harness funciona sin ella. Este cambio no la muda: la frescura de una
  norma se resuelve donde vive el extracto.
- **Cambiar el veredicto de ES0902 O1.** La línea base deja de declarar la versión de una fuente
  gestionada y pasa a leerla del registro. `currency` no se toca: sigue siendo declarada.

## Las decisiones, y por qué

### El registro de fuentes es la autoridad, y la línea base lo consume

`gcba-it-normative-baseline.json` ya declara `ES0901 6.3` y `ES0902 6.2`. Agregar
`source-registry.json` con las mismas versiones son dos mapeos de lo mismo, y el día que
difieran los dos van a tener razón.

Se resuelve en un solo sentido: **el registro de fuentes es dueño de la identidad** —id, kind,
versión, sha256, extracto, estado— y la línea base deja de declarar `version` para una fuente
gestionada; la resuelve por el registro. Lo que la línea base conserva es lo suyo: si el
contenido autoritativo está cargado (`LOADED` / `DECLARED_EXTERNAL_NOT_LOADED`), quién la dicta,
y si consta que sigue vigente.

Se descartó lo contrario —que la línea base absorbiera el registro— porque sus fuentes no son
las mismas: las tres resoluciones de la ASI entran ahí sin documento y sin versión, y una
entrada así no tiene identidad que verificar.

### `currency` no se deriva de la frescura

La tentación es obvia: si el canal configurado muestra la misma versión y el mismo hash,
escribir `currency: CURRENT`. No se hace.

`currency` en O1 significa «consta que esta normativa sigue vigente». Que el adjunto de la Ficha
no haya cambiado no es constancia de vigencia: es constancia de que **el canal observable no
cambió**. Derivar lo primero de lo segundo es exactamente la afirmación que el invariante
prohíbe —«éste es el documento más nuevo que existe»— dicha con otras palabras.

La frescura emite su propio estado, en su propio archivo, y O1 sigue fallando cerrado como hoy.

### El hash es el del archivo original, nunca el del extracto

El extracto es destilado propio: se reescribe cuando se lo mejora, sin que la fuente cambie. Un
hash sobre el markdown cambia cada vez que alguien corrige una coma, y no cambia cuando el PDF
se reemplaza por otro con el mismo nombre. Mide lo contrario de lo que hace falta medir.

### Primero la metadata, el documento después

Bajar seis PDF en cada corrida para hashearlos es una llamada de red por documento cada vez que
alguien abre una sesión. La regla es: metadata relevante sin cambios no baja nada; versión mayor
o identidad de adjunto cambiada obliga a trabajo; **misma versión con identidad cambiada baja y
hashea antes de decidir**, porque es justo el caso en que la metadata no alcanza.

### Lo que no se puede establecer no es `CURRENT`

El estado por defecto ante evidencia ausente no es «sin cambios». Sin versión resoluble es
`VERSION_UNRESOLVED`; sin poder consultar el canal es `FRESHNESS_UNVERIFIED`; sin la fuente en
la Ficha es `SOURCE_MISSING`. Ninguno es `CURRENT` y ninguno se degrada a `CURRENT` por
insistencia.

### Ningún `derived[]` escrito a mano

La procedencia ya está en el árbol: los 42 controles declaran `normativeSources[]`, las matrices
declaran su estándar y su versión, y un agente o una skill pueden declarar `sources:` en su
frontmatter. El índice inverso se **calcula** de eso. Una lista `derived[]` en el registro es una
segunda declaración de lo mismo que envejece sola.

### El descubrimiento devuelve datos; la frescura resuelve; la CLI imprime

`integraciones/fuentes.py` no importa nada de `orquestacion/` y no imprime: recibe el registro
como argumento y devuelve observaciones. La resolución vive en `orquestacion/frescura.py` y es
una función de la evidencia. La única que habla con la persona es `dev-harness.py`, como el resto
del bloque.

### Dos escenarios ajenos cambian de mecanismo; uno cambia de exigencia

Mover la versión al registro y ampliar el validador toca tres escenarios ya verificados. No son
del mismo tipo y no conviene contarlos juntos.

**Cambian de dónde leen, y afirman lo mismo:**

- **O1 E-07** afirmaba «ES0901 está cargado, en 6.3, con su autoridad» leyendo el campo del
  archivo. Ahora lo lee por `linea_base.version_de`. La afirmación es idéntica.
- **C3 E-16, E-17, E-24 y E-39** forjaban una línea base que decía 6.4 para probar el desfase.
  Después de este cambio esa declaración no significa nada, así que el escenario habría pasado
  contra la versión de verdad: los cuatro se escriben ahora contra un registro forjado.

**Cambia lo que exige:**

- **Bases de datos E-36** enumeraba lo que el validador tiene que declarar no soportado y
  nombraba «un `additionalProperties` con un schema como valor». Este cambio lo hace soportado,
  así que esa cláusula **deja de ser cierta del árbol** y su spec queda contradiciendo al código.
  No es una pérdida de cobertura —el resto de E-36 sigue en pie y el mapa ahora valida en los dos
  sentidos—, pero es una exigencia que se retira, no un mecanismo que se muda. Se deja escrito
  en los dos lados: acá y en `docs/cambios/gestion-de-ambientes-de-base-de-datos/spec.md`, con la
  fecha y el cambio que la superó. Una spec que dice lo contrario del árbol hace que la próxima
  refutación falle con razón.

### Se amplía el validador, no se afloja el schema

El contrato del paquete declara `sources` y `decisions` como mapas de id a objeto, y eso en JSON
Schema es `additionalProperties: <schema>`, que `contexto-armar.py` hoy rechaza. Reescribir el
contrato como arreglo para esquivarlo es aflojar el schema para no tocar el validador —
exactamente lo que el comentario de `SIN_CLAVES_DE_MAS` dice que no se hace—. Se amplía el
validador.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/source-registry.schema.json` | El contrato `source-registry/1.1`: una entrada por fuente gestionada, con kind, versión, sha256 y extracto |
| `comun/schemas/source-state.schema.json` | El contrato `sources-state/1.1` del estado runtime, con los doce estados posibles |
| `harnesses/desarrollo/reglas/source-registry.json` | Las fuentes gestionadas que el harness tiene de verdad. `sha256: null` donde el original no está |
| `harnesses/desarrollo/bin/orquestacion/registro_fuentes.py` | Carga y valida el registro. La autoridad de identidad de una fuente |
| `harnesses/desarrollo/bin/orquestacion/procedencia.py` | El índice inverso: de una fuente a sus controles, filas de matriz, policies, checks, reviews, agentes y skills — y cuáles quedaron viejos |
| `harnesses/desarrollo/bin/integraciones/fuentes.py` | El descubrimiento: compara la metadata de la Ficha contra el registro y decide qué bajar. Mecánico, sin modelo, sin imprimir |
| `harnesses/desarrollo/bin/orquestacion/frescura.py` | Integridad y resolución de frescura. Escribe `.claude/harness.fuentes.json` |
| `harnesses/desarrollo/bin/orquestacion/linea_base.py` | Deja de declarar la versión de una fuente gestionada: la resuelve por el registro |
| `harnesses/desarrollo/reglas/gcba-it-normative-baseline.json` | Sin `version` en ES0901 y ES0902: la dice el registro |
| `comun/bin/contexto-armar.py` | El validador interpreta `additionalProperties` con schema, o falla declarándolo |
| `harnesses/desarrollo/bin/dev-harness.py` | El comando `fuentes [--json] [--archivo <dir>]` |
| `tests/casos/45_conocimiento_fuentes.py` | Los escenarios de acá |
| `tests/casos/39_es0902_o1_normativa_gcba.py` | E-07 lee la versión de ES0901 y ES0902 por `linea_base.version_de`, que ahora la resuelve por el registro |
| `tests/casos/43_es0902_c3_herramientas_versionadas.py` | E-16, E-17, E-24 y E-39 expresan «el harness está en 6.4» en el registro de fuentes y no en la línea base |
| `tests/casos/33_bases_de_datos.py` | E-36 deja de exigir que `additionalProperties` con schema se rechace, y exige que valide |

## Escenarios verificables

### El registro de fuentes

- **E-01** — El registro valida contra `source-registry/1.1`, y una fuente cuyo original no está
  en la máquina entra con `sha256: null` y no con un hash calculado sobre otra cosa.
  · rojo visto: si
- **E-02** — Cada fuente aparece una sola vez: dos entradas con el mismo `id` —una por versión—
  hacen que el registro no cargue. · rojo visto: si
- **E-03** — El registro no persiste ninguna lista de derivados: agregarle un `derived[]` lo
  invalida. · rojo visto: si
- **E-04** — La línea base de O1 ya no declara la versión de ES0901 ni de ES0902, y la que emite
  `linea_base.cargar()` para esas dos sale del registro de fuentes.
  · rojo visto: si
- **E-05** — Con el árbol como viene, el resultado de O1 es el mismo antes y después del cambio:
  `REVIEW_INCOMPLETE`, por las mismas dos razones. · rojo visto: si
- **E-06** — Una fuente del registro cuyo `extract` no existe en disco se diagnostica con su id y
  su ruta, y no se la trata como cargada. · rojo visto: si

### El índice inverso de procedencia

- **E-07** — Desde `ES0901`, el índice devuelve los controles que lo declaran en
  `normativeSources[]`, y ninguno de los que no. · rojo visto: si
- **E-08** — Desde un estándar, el índice devuelve las filas de su matriz con sus policies, sus
  checks y sus reviews. · rojo visto: si
- **E-09** — Un agente y una skill que declaran `sources: [ES0901@6.3]` en su frontmatter salen
  en el índice de esa fuente. · rojo visto: si
- **E-10** — Un control que declara `ES0901@6.3` mientras el registro dice `6.4` sale como
  derivado desactualizado, con las dos versiones a la vista. · rojo visto: si
- **E-11** — Un id que nadie declara devuelve un impacto vacío, no el árbol entero.
  · rojo visto: si

### El descubrimiento

- **E-12** — Con la metadata relevante sin cambios —mismo `attachmentId`, mismo nombre, mismo
  tamaño, misma versión— no se baja ningún adjunto. · rojo visto: si
- **E-13** — Una versión observada mayor que la del registro deja `UPDATE_AVAILABLE`.
  · rojo visto: si
- **E-14** — Sin versión resoluble —ni por patrón de nombre ni por la sección de la Ficha— el
  estado es `VERSION_UNRESOLVED`, y nunca «sin cambios». · rojo visto: si
- **E-15** — Misma versión con identidad de adjunto distinta: se baja y se hashea **antes** de
  resolver. · rojo visto: si
- **E-16** — Una fuente gestionada que no está entre los adjuntos de la Ficha deja
  `SOURCE_MISSING`. · rojo visto: si
- **E-17** — `--archivo <dir>` resuelve sin Jira: nombre de archivo y SHA-256 del contenido
  alcanzan, y no se toca la red. · rojo visto: si
- **E-18** — El descubrimiento no escribe en Jira: no transiciona, no comenta, no sube adjuntos.
  Los únicos verbos que usa son de lectura. · rojo visto: si
- **E-19** — El descubrimiento devuelve datos y no imprime: su salida no toca stdout ni stderr.
  · rojo visto: si

### La integridad

- **E-20** — Misma versión y hash distinto del aceptado deja `SOURCE_INTEGRITY_ALERT`, y no hay
  entrada que lo lleve a `CURRENT`. · rojo visto: si
- **E-21** — Misma versión y mismo hash puede quedar `CURRENT`. · rojo visto: si
- **E-22** — Una versión observada menor que la aceptada deja `VERSION_REGRESSION` y no se
  promueve sola. · rojo visto: si
- **E-23** — El hash que se guarda y se compara es el del archivo original: el del markdown del
  extracto da distinto y no se usa en ninguna comparación. · rojo visto: si

### La resolución de frescura

- **E-24** — `CURRENT` exige las cinco condiciones —fuente descubierta, versión resuelta,
  integridad aceptada, extracto activo que coincide en versión y hash, cero derivados que
  bloqueen—; sacando cualquiera de las cinco, el estado deja de ser `CURRENT`.
  · rojo visto: si
- **E-25** — Sin poder consultar el canal configurado el estado es `FRESHNESS_UNVERIFIED`, con su
  motivo, y nunca `CURRENT`. · rojo visto: si
- **E-26** — Un derivado desactualizado impide `CURRENT` aunque la fuente esté intacta.
  · rojo visto: si
- **E-27** — La misma evidencia da el mismo resultado: dos resoluciones sobre la misma entrada
  devuelven el mismo estado, el mismo riesgo y el mismo impacto, en el mismo orden.
  · rojo visto: si
- **E-28** — Todo estado emitido se puede trazar a id, versión observada, versión del registro,
  hash y evidencia: ninguno sale sin con qué contradecirlo. · rojo visto: si
- **E-29** — No existe combinación de evidencia ausente que produzca `CURRENT`: recorridos todos
  los estados, el único que lo alcanza es el que tiene las cinco condiciones.
  · rojo visto: si

### El estado en disco

- **E-30** — `.claude/harness.fuentes.json` valida contra `sources-state/1.1`, y un estado que no
  está en el enum no se escribe. · rojo visto: si
- **E-31** — El validador de subconjunto interpreta `additionalProperties` con un schema como
  valor: valida las claves del mapa contra él y rechaza la que no cumple.
  · rojo visto: si
- **E-32** — El documento se escribe redactado: un secreto en el nombre de un adjunto no queda en
  claro en el archivo. · rojo visto: si
- **E-33** — `pending_count` sale de los estados, no de quien escribe el documento: declararlo en
  cero con una fuente en alerta no se sostiene. · rojo visto: si
- **E-34** — Ninguna ruta, clave ni mensaje de lo que se construye nombra SharePoint.
  · rojo visto: si

### La CLI

- **E-35** — `dev-harness.py fuentes` escribe el estado y sale 0 aunque haya fuentes en alerta:
  una fuente desactualizada no es una falla del harness. · rojo visto: si
- **E-36** — Con `--json` el documento sale por stdout y todo lo demás por stderr.
  · rojo visto: si

## Cómo se verifica

Los treinta y seis escenarios pasan por la suite, en `tests/casos/45_conocimiento_fuentes.py`.
Ninguno lleva `· verificación: lectura`: no hay ninguno cuyo sujeto sea una corrida de un modelo.
El descubrimiento es mecánico por decisión de diseño y la resolución de frescura es una función
de la evidencia, así que todo lo de acá es alcanzable por un test determinista.

E-18 y E-34 se verifican leyendo el código construido —qué verbos HTTP usa, qué rutas nombra—,
lo cual es un test sobre el árbol, no una lectura firmada: la suite ya lo hace en otros lados
con `ast` y con grep sobre los archivos.

## Riesgos conocidos

- **El registro nace sin un solo hash.** Los PDF originales están gitignoreados y esta máquina
  puede no tenerlos. Todas las entradas arrancan con `sha256: null`, y eso significa que la
  integridad no se puede verificar hasta que alguien acepte un original. El diseño lo declara
  —evidencia incompleta, nunca `CURRENT`— pero el primer efecto visible del cambio es que el
  harness admite que no sabe.
- **La versión sale del nombre del archivo.** `filenamePattern` es una heurística sobre cómo la
  DGISIS nombra sus PDF. Si cambia la convención, todas las fuentes caen a
  `VERSION_UNRESOLVED` a la vez. Falla cerrado, que es lo que se quiere, pero falla en bloque.
- **La Ficha de Proyecto sigue siendo una suposición.** Está como pendiente número 17: nadie
  escribió una en un Jira real. El descubrimiento contra la Ficha se prueba con transporte
  falso, igual que los dos adapters.
- **El índice inverso no ve lo que nadie declaró.** Un control sin `normativeSources[]` no sale
  en ningún impacto. Hoy `controles.py` ya lo diagnostica como `CONTROL_NORMATIVE_SOURCE_MISSING`,
  pero el índice no lo repite: quien lea sólo el impacto puede leer «no afecta a nadie» donde
  dice «nadie declaró».
