# Paso 4 del contrato: `interfaces`, `identity_and_access` y `environments`

**Estado:** especificado · **Fecha:** 2026-08-26

> Es el paso 4 de los nueve del capítulo 18 de *QA Agent · Project Context Contract v1.1*. Los
> pasos 1 y 2 están construidos y verificados en
> [`contexto-de-proyecto`](../contexto-de-proyecto/spec.md); los pasos 3 y 5 a 9 siguen afuera.
>
> **Segunda redacción, 2026-08-26.** La primera pasó por `harness-spec-refuter` sin una línea de
> código escrita, contra el árbol. Rindió **8 sostenidos y 2 contradichos** sobre las afirmaciones
> de hecho, y marcó **seis escenarios sin forma de fallar**. Los dos contradichos y los seis
> escenarios están corregidos acá; cada corrección dice de dónde salió.

## Qué problema resuelve

`project-context.json` se escribe y **no lo lee nadie**. El capítulo 17 del documento afirma que
`PROJECT_CONTEXT` es *"un contrato del harness, no un detalle privado del QA Agent"*, y mientras
tenga un solo emisor y cero consumidores esa afirmación no está probada.

El primer consumidor posible es `dev-refutador`, que ya existe y ya verifica contra la norma. El
mapeo campo por campo está en `Pendientes/Ideas-Harness/PENDIENTES-I.md`, y de los campos que
necesita, **tres son exactamente este paso**:

| Campo | Qué skill habilita | Qué puede rendir hoy |
|---|---|---|
| `interfaces` | `dev-api` — rutas, versionado, códigos de estado, cuerpo de error, contrato OpenAPI | nada |
| `identity_and_access` | `dev-identidad` — OpenID contra Keycloak, dónde vive la sesión, qué endpoints quedan públicos | nada |
| `environments` | `dev-ambientes` — distancia a producción, qué aprobaciones necesita un gate | nada |

Hoy los tres viajan como una línea de texto en `gaps_and_conflicts.missing[]` que dice que el
schema v1.0 no los modela. El refutador que quisiera usarlos abre el contrato, encuentra el aviso,
y vuelve a grepear el repositorio — que es exactamente el trabajo que el contrato existe para
ahorrar.

## Qué queda afuera

- **`data_model` (el bloque DATA MODEL del capítulo 09).** Está en el mismo capítulo que
  `interfaces` e `identity_and_access`, pero **no está en el paso 4**: el capítulo 18 ordena
  *"interfaces + auth + environments"*. Entidades, migraciones y campos que importan a una regla
  sólo significan algo con `business_rules`, que es el paso 3.
- **`quality_landscape` (paso 5).** Ahí viven fixtures, Playwright y los tests flaky. El refutador
  no ejecuta nada, así que es el bloque que menos le sirve y el que más caro sale de descubrir.
- **`CHANGE_CONTEXT`, `QA_RUN_REQUEST`, `CONTEXT_REQUIRED` y el refresh incremental (pasos 6 a 9).**
  Sin consumidor no hay quien los emita, y un protocolo sin ninguna de las dos puntas no se prueba.
- **`dev-qa`.** Sigue sin escribirse. Este paso es para el refutador, que es un hermano suyo en otro
  eje —norma contra implementado, no esperado contra implementado— y no un paso hacia él.
- **El bloque `compliance`.** Es el eje que el contrato no modela y está anotado como idea abierta,
  sin decidir entre un bloque propio y un valor `standard` en `sources[].type`. Meterlo acá sería
  contrabandear una decisión no tomada adentro de un paso que el documento sí define.
- **Los valores de ejemplo de la tabla de ENVIRONMENTS.** Ver la decisión de abajo: esa tabla no es
  citable desde la capa de texto del PDF.
- **Ejecutar cualquier cosa para descubrir un ambiente.** El agente lee el repositorio; no levanta
  el sistema, no consulta un OpenShift y no abre una URL. Lo que no está escrito en el árbol se
  declara como hueco.
- **Un check nuevo.** Mismo criterio que en el paso anterior: `contexto-armar.py` valida antes de
  escribir, y un check sobre un archivo generado se paga en latencia en cada llamada a herramienta
  de cada sesión.
- **Ampliar `controlar_soporte()` para que recorra el schema entero.** Hoy desciende sólo por
  `properties` e `items`. Es un límite real y está anotado abajo, pero arreglarlo es tocar el
  validador del paso 2, que está verde, dentro de un cambio que no lo necesita: E-02 recorre el
  JSON por su cuenta y no depende de esa función.

## Las decisiones, y por qué

### Tres secciones más en `proyecto.md`, y ninguna superficie nueva

El reparto del paso 2 se mantiene entero: **el agente escribe markdown, el script arma el JSON**.
`proyecto.md` suma `## Interfaces`, `## Identidad y acceso` y `## Ambientes`, con el mismo formato
de bullets etiquetados que ya leen `etiquetas()` y `bullets_sueltos()`.

Se descartó un archivo por bloque. La razón es la que ya fijó el paso 2: dos superficies de autoría
son dos archivos que pueden contradecirse, y el contrato deja de tener un solo generador. Un archivo
más también significa un nombre reservado más que excluir en tres lugares —`leer_fichas()`,
`_fichas_en_disco()` y `_revisar_ficha()`— que viven en archivos que no se pueden importar entre sí.

### Los tres bloques son objetos con `knowledge_status`, no arrays

El documento escribe `interfaces[]` y `environments[]`. Acá son **objetos con `items[]` adentro**,
como ya es `technology`.

El motivo es que un array no puede llevar su propio `knowledge_status`, y sin él la asimetría que
sostiene todo el contrato se pierde: `interfaces: []` a secas es indistinguible entre *"este
proyecto no expone APIs"* y *"nadie miró"*. El capítulo 12 pide justamente lo contrario.

🔴 **Es una desviación de la forma que escribe el PDF y se declara como tal.** Lo que se conserva es
la semántica del capítulo 09 —los campos de cada interfaz— y lo que cambia es el envoltorio.

### `meta.schema_version` pasa a `project-context/1.1`

`schema_version` es un `enum` de un solo valor y el intérprete soporta `enum`, así que el bump es
una edición del schema y de sus tests, no un mecanismo nuevo.

📌 **Son dos ediciones, no una.** El `$id` del schema (línea 3) también lleva la versión. El
refutador lo marcó porque la primera redacción de esta spec nombraba sólo el `enum`.

Es **1.1 y no 2.0** porque el cambio es puramente aditivo: todo documento v1.0 válido sigue siendo
válido salvo por la cadena de versión. Y no hay documento v1.0 en disco fuera de este repositorio,
porque no hay proyecto instalado que haya corrido el recorrido todavía.

🔴 **El día que exista un v1.0 ajeno, lo que corresponde es una migración, no un `enum` más flojo.**
Aceptar las dos versiones en el mismo campo convierte `schema_version` en decorado: un consumidor
que lea `1.0` no sabría si le faltan los bloques o si el emisor era viejo.

### Los tres bloques son `required`, y viajan vacíos con su `knowledge_status`

Es la asimetría que el paso 2 ya fijó en E-13 y que el capítulo 12 del documento pide: **un hueco
declarado es un hueco; un bloque ausente es indistinguible de "acá nadie miró"**.

Un proyecto sin APIs emite `interfaces` con `items: []`, `knowledge_status: missing` y una línea en
`gaps_and_conflicts.missing[]`. No emite un documento sin la clave.

### `interfaces` lo escribe el agente, y no se reusa ningún check

Se evaluó derivar las rutas de `dev-api-rutas.py` y **no se puede**: lo carga `post-tool-use.py`, su
única entrada es `dev.archivo_escrito(evento)` —un path por evento— y devuelve `[]` cuando no hay
archivo escrito. No hay `walk`, no hay `git ls-files`, no hay nada que enumere. Derivar rutas de
verdad significa un parser por framework, que es la pared de siempre —biblioteca estándar y nada
más— y una pared que no vale la pena escalar para un bloque que el agente puede escribir leyendo.

De ahí sale el costo, y hay que decirlo: **`interfaces` sale `inferred`, salvo que haya un archivo
OpenAPI**, en cuyo caso sale `confirmed`. Ese archivo el script ya lo detecta hoy —`CONTRATOS`, en
`contexto-armar.py:114`, le da su propia entrada en `sources[]`— así que `request_contract_ref` y
`response_contract_ref` apuntan a un `source_id` que ya existe, en vez de repetir la ruta.

📌 **`CONTRATOS` matchea por basename exacto** contra `git ls-files`: los seis nombres de tipo
`openapi` son `openapi.{yaml,yml,json}` y `swagger.{yaml,yml,json}`. Un `api/openapi-v2.yaml` no se
detecta. Acota la fixture de E-06 y no cambia la decisión, pero el que construya tiene que saberlo.

📌 **Corregido el 28-08-2026.** Esta nota y el footnote de E-06 decían "ocho nombres" — son seis
(tres extensiones de `openapi` más tres de `swagger`; los otros dos de `CONTRATOS` son `type:
config`, no `openapi`, y no cuentan para esta regla). Lo encontró `harness-spec-refuter` verificando
contra el código ya construido; no cambia ningún veredicto.

### `identity_and_access` no tiene ningún campo donde quepa una credencial

El capítulo 09 lo pone como regla de seguridad: *"PROJECT_CONTEXT referencia secretos o credenciales
por handle/ref; nunca debería contener passwords, tokens o cookies en texto plano"*.

Se aplica al diseño del schema: los usuarios de prueba se modelan como `test_principals[].ref`, y
**no existe un campo `password` ni `token` para llenar**. Lo que no tiene lugar donde escribirse no
se escribe por descuido.

### El detector de secretos **no** se mete adentro del script

Se evaluó que `contexto-armar.py` cargue `comun/hooks/lib/secretos.py` y rechace el documento, y se
descartó por dos motivos:

1. **La regla ya tiene dueño y ya bloquea antes.** `pre-tool-use.py` es el único hook que llama a
   `bloquear()`, y `texto_de_herramienta()` cubre el `content` de un `Write`: una contraseña dentro
   de `proyecto.md` se escanea al escribirse. Un detector en el script correría **después** de esa
   barrera, sobre un archivo que la barrera ya dejó pasar.

   🔴 **Y la barrera no es absoluta**, contra lo que decía la primera redacción de esta spec. Sólo
   `confianza: alta` bloquea; `media` llama a `preguntar()` y una persona puede aprobar. Vale para
   las formas inequívocas, no para todas — lo cual no cambia la decisión, porque el detector en el
   script tendría exactamente el mismo catálogo y el mismo umbral.
2. **Sería un segundo acoplamiento por ruta.** El paso 2 ya carga `mapa-codigo.py` por `__file__` y
   ya declaró ese acoplamiento como riesgo. Sumar un segundo, hacia otro directorio que el
   instalador acomoda distinto, duplica el riesgo para volver a comprobar lo mismo.

### `environment_id` es libre y `kind` es un `enum` corto que normaliza

Hay **dos** contradicciones distintas sobre los ambientes, y las registran dos skills distintas:

- **`dev-seguridad`** (págs. 226-233 de su `SKILL.md`) tiene la que importa acá: ES0901 pág. 3 dice
  cuatro —DEV, QA, HML y PRD—, la pág. 9 dice cuatro con *Testing* en lugar de QA, y la pág. 38
  (Anexo III) dice cinco — Desarrollo, **Calidad**, Homologación, **Producción Interna** y
  **Producción DMZ**. Su regla práctica: *"al pedir un pase, nombrá el ambiente como lo nombra el
  equipo que lo opera y dejá asentada la equivalencia"*.
- **`dev-ambientes`** tiene otra, sobre el nombre del primero: PC0901 dice **DESA** y la GuiaDGISIS
  opera con **DEV**, y además AD, SADE y Kibana no tienen los cuatro.

🔴 **La primera redacción de esta spec le atribuía a `dev-ambientes` la contradicción de
`dev-seguridad`.** Las tres citas de ES0901 eran correctas; la fuente estaba mal. Lo corrigió el
refutador y es un `contradicho`.

Las dos contradicciones apuntan al mismo diseño: `environment_id` es texto libre —`qa-main`,
`Calidad`, `DESA`, `PRD-DMZ`— y `kind` normaliza a `local | dev | qa | hml | prd | other`. Así un
consumidor filtra sin que el harness resuelva una contradicción del estándar que no le toca
resolver, y sin perder el nombre con que el equipo lo llama.

📌 **La normalización tiene que estar dicha, no librada al que construya.** Un script que mande todo
lo desconocido a `other` cumpliría cualquier enunciado vago — y `other` deja a `kind` inservible
para lo único que justifica que exista. E-11 fija el mapeo.

### Un ambiente `prd` sale siempre `read-only`, y la discrepancia se anota

El capítulo 10 tiene una sola regla dura, y es la razón por la que el bloque existe: *"El QA Agent
solo puede elegir entre targets y capabilities autorizadas por el contexto + harness policies. No
debería poder apuntar arbitrariamente a producción."*

Un límite que sólo vive en la prosa del prompt del consumidor no es un límite —es la misma lección
que dejó `iniciador-code` con sus tres invariantes—. Así que lo fija el emisor: si `proyecto.md`
declara otra cosa para un ambiente `kind: prd`, el script **escribe `read-only` igual** y deja la
discrepancia en `gaps_and_conflicts.conflicts[]`. No la corrige en silencio y no la obedece.

### `base_urls` sólo lleva URLs que estén en un archivo versionado

Una URL que el agente no puede señalar en el árbol es una URL que recordó. El bloque de ambientes es
el lugar más probable donde eso pase, porque las URLs de DEV, QA y HML de un proyecto del GCBA
siguen un patrón que un modelo completa solo.

La regla es la misma que ya rige `sources[]`: cada afirmación con su procedencia. Lo que no se puede
señalar queda afuera y el hueco se declara.

### La tabla de ENVIRONMENTS del PDF no es citable, y por eso se modela un subconjunto

🔴 **La tabla de la pág. 12 se convirtió desalineada.** Los diez nombres de campo extraen como una
lista vertical limpia; los diez valores de ejemplo extraen corridos respecto de su fila, de modo que
`environment_id` queda al lado de un ejemplo que no es suyo. Es el mismo caso que el Anexo II de
ES0901, y se trata igual: **se toman los nombres de campo, no se toman los valores de ejemplo.**

De los diez campos se modelan cinco, y se dice cuáles quedan afuera y por qué:

| Se modela | Se deja afuera |
|---|---|
| `environment_id`, `kind`, `base_urls` | `rate_limits`, `cleanup_strategy`, `availability_notes` |
| `allowed_mutations`, `data_policy` | `db_access`, `external_services` |

Los cinco que entran son los que un agente que **lee** puede observar y los que sostienen la
frontera de política. Los que quedan afuera son hechos operativos: viven en la infraestructura, no
en el árbol, y un agente que los complete los está inventando. `db_access` además es el campo donde
una cadena de conexión entra sola.

### Los tests van a un archivo nuevo, y los títulos llevan el slug

`tests/casos/13_contexto.py` ya lleva **E-01 a E-17 y E-19 de `contexto-de-proyecto`**. Mandar ahí
E-01 a E-17 de este cambio hace que `E-03` signifique dos cosas en el mismo archivo, y rompe la
traza en los dos sentidos: quien greppee un id encuentra dos escenarios que no hablan de lo mismo.
Es el defecto que ya se pagó en 0.14.0, cuando `test_e20b_...` era más viejo que el escenario E-20b
y probaba la premisa contraria.

Así que los tests nuevos van a **`tests/casos/15_contexto_paso4.py`**, y cada título nombra el id
**con su slug**: `E-03 (paso-4): ...`. Lo detectó el refutador y no lo tenía la primera redacción.

### El instalador no se toca

El paso 2 ya agregó la línea que copia el directorio entero —`install.ps1:1102`, un `Copy-Arbol`
sobre `comun/schemas`—, así que un schema v1.1 se reparte solo y `harness.lock.json` lo inventaría
sin que el instalador cambie nada.

📌 **La clave `schemas` del `aporta` de `comun/manifest.json` no interviene.** `grep -c aporta
install.ps1` da **0**: `aporta` es decorativo en los tres manifiestos, está anotado en
`PENDIENTES-FH.md` y sigue abierto. Quien lea esta decisión buscando el mecanismo tiene que ir a la
línea de copia, no al manifiesto.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/project-context.schema.json` | v1.1: `interfaces`, `identity_and_access` y `environments` como bloques `required`, cada uno con su `knowledge_status`. La versión cambia en **dos** lugares: el `enum` de `schema_version` y el `$id` |
| `comun/bin/contexto-armar.py` | Tres lectores de `proyecto.md`, los tres bloques, la normalización de `kind`, la regla de `prd` → `read-only` con su conflicto, la colisión de `interface_id`, el `owning_component` inexistente, el filtro de `base_urls` contra los versionados, y `missing[]` que pasa de anunciar cinco bloques a anunciar dos |
| `harnesses/desarrollo/agents/dev-iniciador-code.md` | Tres secciones más para escribir, con qué mirar en cada una y la regla de que un hueco se declara y no se completa |
| `docs/codebase/proyecto.md` | El de este repositorio, con las tres secciones |
| `docs/codebase/project-context.json` | Regenerado en v1.1 |
| `tests/casos/15_contexto_paso4.py` | **Archivo nuevo.** Los escenarios de abajo, con el slug en cada título |
| `tests/casos/14-contexto-instalador.ps1` | Una línea: la versión que el schema instalado declara |

## Escenarios verificables

### El schema v1.1

- **E-01** — Un documento con `meta.schema_version: project-context/1.0` no se escribe: el `enum` lo
  rechaza y el script nombra el campo. · rojo visto: si
- **E-02** — El schema v1.1 no usa, **en ninguna rama**, una palabra fuera de las seis que el
  intérprete valida —`type`, `properties`, `required`, `items`, `enum`, `pattern`—.
  · rojo visto: si

  📌 El test recorre el JSON entero por su cuenta y **no** se apoya en `controlar_soporte()`: esa
  función desciende sólo por `properties` e `items`, así que no alcanza al archivo completo. Del
  refutador, que marcó que "el schema entero" era más de lo que la función recorre.
- **E-03** — Cada uno de los tres bloques es `required`: sacando **cualquiera de los tres** de un
  documento válido, el script sale con código 1 y nombra el bloque que falta. Son tres casos.
  · rojo visto: si

  Del refutador: la primera redacción decía "los tres" y pedía el observable de uno solo, así que un
  test que ejercitara únicamente `interfaces` lo satisfacía literal.

### Interfaces

- **E-04** — Dos entradas de `## Interfaces` con el mismo `interface_id` no producen dos entradas
  con el mismo id: el script conserva la primera, descarta la segunda y nombra la colisión en
  `gaps_and_conflicts.conflicts[]`. · rojo visto: si

  🔴 El escenario **fija el comportamiento** porque el schema no puede: el intérprete no soporta
  `uniqueItems`. La primera redacción decía que la unicidad la garantizaba el script sin decir qué
  hacía ante un duplicado, así que lo que se construyera iba a ser la aserción.
- **E-05** — Un `type` fuera de `http | graphql | event | webhook | cli` no se escribe: el `enum` lo
  rechaza. Se prueba sobre una fixture **con al menos una interfaz**. · rojo visto: si

  📌 Sobre `items: []` el enunciado es vacuamente verdadero y lo sería para siempre. Es la mitad del
  defecto que el refutador encontró en el E-04 original.
- **E-06** — Con un `openapi.yaml` **commiteado** en la fixture, el `request_contract_ref` de la
  interfaz que lo nombra es el `source_id` que `fuentes_de_contrato()` emite, y no una ruta
  repetida. · rojo visto: si

  📌 `CONTRATOS` matchea por basename exacto sobre `git ls-files`: la fixture usa uno de los seis
  nombres de tipo `openapi` y el archivo tiene que estar commiteado, no sólo escrito.
- **E-07** — Una interfaz cuyo `owning_component` nombre un componente que **no existe** en
  `architecture.components[]` se escribe con el campo vacío y con la discrepancia en
  `gaps_and_conflicts.conflicts[]`; otra que nombre uno que **sí existe** lo conserva. La fixture
  lleva las dos. · rojo visto: si

  🔴 Sin las dos mitades el escenario no tiene forma de fallar: la primera redacción decía "o está
  vacío", y un script que vaciara siempre el campo la satisfacía permanentemente. Es el modo de
  falla de E-10 de `iniciador-code`, textual.
- **E-08** — Sin sección `## Interfaces` en `proyecto.md`, el bloque viaja igual: la clave presente,
  `items: []`, `knowledge_status: missing` y una línea en `gaps_and_conflicts.missing[]`. El bloque
  no se omite. · rojo visto: si

### Identidad y acceso

- **E-09** — `identity_and_access` tiene `auth_model`, `roles[]`, `test_principals[]`,
  `access_by_environment[]` y `knowledge_status`, y **ninguna propiedad del schema, en ninguna rama,
  se llama** `password`, `token`, `secret`, `credential` ni `cookie`. · rojo visto: si

  📌 Es lo que un test puede sostener. Que *no quepa* una credencial no lo prueba ningún test: un
  campo de texto libre acepta cualquier cosa. Lo previene el diseño y lo ataja `pre-tool-use.py` al
  escribirse `proyecto.md`. Del refutador, que marcó que la segunda mitad del E-08 original no la
  alcanzaba ningún test.
- **E-10** — Sobre una fixture cuyos tres bloques nuevos lleven cadenas **con forma de credencial**,
  el detector de `comun/reglas/secretos.patrones.json` las encuentra con `confianza: alta`. Y sobre
  el `project-context.json` de `docs/codebase/` de este repositorio no encuentra ninguna.
  · rojo visto: si

  🔴 **El control positivo es la fixture, no este repositorio.** Acá los tres bloques van a salir
  vacíos o casi —no hay APIs, ni modelo de auth, ni ambientes—, y escanear tres bloques vacíos pasa
  el día que se escribe y pasa para siempre. Del refutador.

### Ambientes

- **E-11** — `kind` normaliza, y el escenario dice a qué: `Calidad` → `qa`; `Producción Interna` y
  `Producción DMZ` → `prd`; `DESA` y `Desarrollo` → `dev`; y sólo lo que no matchea ninguna forma
  conocida cae en `other`. `environment_id` conserva el nombre original en los cinco casos.
  · rojo visto: si

  🔴 Del refutador: sin el mapeo escrito, un script que mande todo a `other` pasa — y `other` deja a
  `kind` inservible para el filtrado que es lo único que justifica que exista.
- **E-12** — Un ambiente con `kind: prd` sale con `allowed_mutations: read-only` **aunque
  `proyecto.md` declare otra cosa**, y esa discrepancia queda escrita en
  `gaps_and_conflicts.conflicts[]` nombrando el ambiente. · rojo visto: si
- **E-13** — Una URL de `base_urls` que no aparezca en ningún archivo versionado del repositorio no
  llega al contrato, y su ausencia se declara en `gaps_and_conflicts.missing[]`. La fixture lleva
  dos URLs: una en un archivo commiteado y otra en ninguno. · rojo visto: si

### Lo que ya existía y no se rompe

- **E-14** — `gaps_and_conflicts.missing[]` lleva exactamente **dos declaraciones de bloque no
  modelado** —`business_rules` y `quality_landscape`— y ninguna de los tres de este cambio.
  · rojo visto: si

  🔴 **Se cuentan las declaraciones, no las entradas.** `missing[]` lleva además las fichas
  huérfanas: hoy tiene **seis** entradas para cinco declaraciones. Un test sobre `len(missing) == 2`
  está mal hoy mismo y va a estar mal cualquier día que aparezca una huérfana. Del refutador.

  Reemplaza a E-13b de `contexto-de-proyecto`, que afirmaba lo mismo sobre cinco bloques. **No lo
  debilita**: conserva su proposición sobre los dos que quedan y agrega la mitad negativa que E-13b
  no tenía — que los tres ya modelados no deben declararse.
- **E-15** — `meta.context_hash` **cambia** cuando cambia el bloque `environments` ya calculado, y
  no sólo porque cambiaron los bytes de `proyecto.md`. · rojo visto: si

  🔴 **Reescrito el 28-08-2026, durante el propio pase de `rojo visto`.** La primera versión
  comparaba el hash de dos corridas cuyo `proyecto.md` difería sólo en `## Ambientes`, y **no
  servía**: `meta.docs_revision` hashea todos los `.md` de `docs/codebase/` —`proyecto.md`
  incluido, en `hash_de_fichas()`—, así que reescribir `proyecto.md` mueve el hash general **sin
  importar** si `armar()` sella `context_hash` antes o después de sumar los tres bloques nuevos. Se
  comprobó rompiendo exactamente ese bug —los tres bloques reemplazados por objetos vacíos y fijos,
  desconectados de lo parseado— y el escenario, tal como estaba escrito, siguió en verde.

  La versión que queda mantiene `proyecto.md` **byte a byte idéntico** entre las dos corridas
  —`docs_revision` fijo— y varía en cambio el contenido de un archivo versionado *fuera* de
  `docs/codebase/`, para que la única fuente posible de un hash distinto sea el `environments` ya
  calculado. Sobre esa versión, la misma mutación **sí** se ve: el script crashea con
  `IndexError` justo donde `environments.items` se asume no vacío, que es el rojo más elocuente
  posible para ese defecto.
  Es lo que falla si alguien agrega los bloques a `doc` **después** de `contexto-armar.py:694`,
  que es donde se sella el hash. La otra mitad —que el hash se calcule sin `context_hash` ni
  `generated_at`— es E-04 del cambio anterior y no se repite acá.
- **E-16** — Un `[[wiki]]`, o un enlace relativo a una ficha que no existe, adentro de una de las
  tres secciones nuevas **sí** dispara hallazgo de `dev-codebase-forma.py`; y una sección que enlace
  una ficha hermana que existe, no. · rojo visto: si

  📌 El corte temprano de `dev-codebase-forma.py:115-119` deja a `proyecto.md` corriendo únicamente
  `_revisar_enlaces`: las cuatro secciones y la línea del índice no pueden fallar por ahí, así que
  afirmar que no fallan no prueba nada. Del refutador.

### El instalador

- **E-17** — Tras `install.ps1 -Update`, el schema instalado declara `project-context/1.1` y su
  SHA256 figura en `harness.lock.json`. · rojo visto: si

  📌 Es E-18 del cambio anterior con el valor cambiado. La cláusula *"sin que `install.ps1` haya
  cambiado"* **salió del escenario**: es una propiedad del diff, no del sistema corriendo, y ningún
  test de esta suite puede observarla. Queda dicha en las decisiones, que es donde corresponde. Del
  refutador.

### Lo que sólo se puede leer

- **E-18** — El contrato de un recorrido real no **inventa** interfaces, roles ni ambientes: cada
  entrada de los tres bloques se puede señalar en un archivo del proyecto recorrido.
  · rojo visto: no consta
  · verificación: lectura — el sujeto es una corrida de un modelo, y la suite no invoca al agente

  📌 La lectura mira lo que la suite no alcanza: si el agente dedujo una ruta, un rol o un ambiente
  que ningún archivo respalda. **El filtro mecánico de `base_urls` ya lo sostiene E-13** y
  re-chequearlo gasta la corrida. Del refutador.

## Cómo se verifica

**Por la suite, E-01 a E-17.** Todos son propiedades de un archivo generado por un script
determinista, del schema, o del reparto del instalador. Se prueban sobre fixtures escritas a mano;
E-10 suma como control negativo la salida real de `docs/codebase/` de este repositorio, con la
salvedad que el propio escenario declara.

**Por lectura, E-18 solamente**, según [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md).
Lo firma alguien que no construyó, con fecha.

## Riesgos conocidos

- 🔴 **Este cambio suma una lectura sin firmar a CATORCE que ya traban el cierre**, no a diez.
  Nueve en [`iniciador-code`](../iniciador-code/lectura.md), una en
  [`contexto-de-proyecto`](../contexto-de-proyecto/lectura.md) y **cuatro en
  [`mapa-de-nodos`](../mapa-de-nodos/lectura.md)** —E-01, E-18, E-19 y E-20, y ese directorio
  tampoco tiene `verificacion.md`—. La primera redacción de esta spec decía diez, y el encabezado de
  la spec de `contexto-de-proyecto` también: **las dos se equivocan por cuatro**. Que
  `mapa-de-nodos` esté sin firmar "a propósito" no la saca de la pila; ADR-0009 no tiene categoría
  para una lectura deliberadamente vacía. Del refutador, y es un `contradicho`.

  La mitigación no es técnica y hay que decidirla antes de construir: o las catorce se firman
  primero, o este cambio queda especificado y sin construir. Construirlo con la pila creciendo es
  cómo un `leído` deja de significar algo.
- **`docs/codebase/project-context.json` no está versionado.** `git ls-files --error-unmatch` falla
  y `git status` lo da como `??`. E-10 de esta spec lo nombra sin la palabra "versionado" por eso, y
  **E-19 de `contexto-de-proyecto` sí la usa y hoy es falsa** — su test sólo afirma `is_file()`, así
  que la palabra no pesa en la suite pero sí en lo que la spec promete. Lo encontró el refutador y
  es un defecto del cambio anterior, no de éste.
- **`interfaces` sale `inferred` en todo proyecto sin OpenAPI**, que es la mayoría. Un consumidor
  que trate `inferred` como `confirmed` va a fallar rutas que el agente dedujo. El contrato lo dice
  en el campo; que alguien lo lea no lo garantiza nada.
- **`controlar_soporte()` no recorre el schema entero**, sólo desciende por `properties` e `items`.
  E-02 no depende de esa función, así que este cambio no queda expuesto — pero el validador del paso
  2 sí lo está, para cualquier schema futuro con una construcción en otra rama.
- **La tabla de ENVIRONMENTS del PDF no es citable**, así que el subconjunto de cinco campos es una
  lectura de los nombres, no una transcripción de la tabla. Si alguien necesita los diez campos con
  sus ejemplos, se abre la pág. 12 del PDF.
- **El eje regulatorio sigue sin lugar.** Este paso le da tres bloques al refutador y no le da dónde
  decir contra qué versión de qué estándar está rindiendo. Queda en `PENDIENTES-I.md`, sin decidir.
- **El bump a v1.1 invalida cualquier documento v1.0 en disco.** Hoy no hay ninguno fuera de este
  repositorio. El día que lo haya, la respuesta correcta es una migración, no aflojar el `enum`.
- **`prd` → `read-only` es una política del emisor sobre un contrato que declara conocimiento.**
  Es la única regla de este cambio donde el script no describe lo que encontró sino que impone lo que
  corresponde. Está acotada a un campo y deja rastro en `conflicts[]`, pero es una excepción al
  principio y por eso está escrita acá.
