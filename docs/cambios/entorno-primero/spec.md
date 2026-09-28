# Bloque 1 — la configuración de las integraciones sale del `.env`

**Estado:** verificado y cerrado · **Fecha:** 28-09-2026 · **Bloque:** 1

## Qué problema resuelve

Hoy conectar Jira o GitLab pide dos archivos y una terminal:

- La base URL, el usuario y si la integración está habilitada van en
  `.claude/harness.integraciones.json`, que carga `dev-harness.py setup` preguntando por `input()`.
- El token va en el `.env`, que carga el mismo `setup` por `getpass`.
- Sin una terminal interactiva el `setup` aborta (`_exigir_terminal`), así que un proyecto que
  recibe los valores de otra forma —un script, una máquina donde los inyecta otra cosa— no tiene
  camino que no sea editar a mano un JSON que el harness trata como suyo.

La persona tiene que saber qué va en cada archivo, y el harness no le dice qué falta por nombre de
variable: `validar_conexion` dice `Falta configurar Jira Cloud: baseUrl, JIRA_TOKEN. Corre el setup
del harness.`, que mezcla una clave del JSON con una variable del `.env`.

Este cambio deja **un solo archivo que la persona completa**, el `.env` local, y convierte el JSON
en una proyección que el harness genera:

```
.env (de la persona, detrás de permissions.deny)
  ↓  integraciones/entorno.py — resolvedor determinista, ni agente ni skill
  ├── SECRET        → no se copia a ningún lado; el adapter lo pide a AlmacenSecretos
  └── PUBLIC_CONFIG → .claude/harness.integraciones.json (proyección sanitizada, generada)
                         ↓
               IntegracionJira / IntegracionGitLab (sin cambios de auth ni de sondeo)
                         ↓
               .claude/harness.capacidades.json
```

El paquete de entrada son `block-1-environment-first-integration-bootstrap.md`,
`integration-environment-contract.schema.json`, `integration-environment-contract.seed.json` y
`prompt-install-block-1-environment-first-integration-bootstrap.md`. El `harness.env.example` que
el prompt nombra **no venía**: su contenido está en el `.md` y se integra al `.env.example` que el
harness ya reparte.

## Qué queda afuera

- **OpenShift.** No hay adapter. El contrato lista solo lo que tiene uno (Jira y GitLab), y la línea
  `OPENSHIFT_TOKEN` reservada sale del `.env.example`: listar una variable sin integración sugiere
  que hay algo que configurar. Es el mismo criterio que ya declara `bienvenida.INTEGRACIONES`. Un
  `.env` existente que la tenga no se toca.
- **Un helper que escriba en el `.env`.** El paquete lo permite como opcional (agregar
  placeholders, o los valores públicos del JSON viejo). No se hace: toda escritura en un archivo
  que es de la persona es una ruta más para romperlo, y la capa `LEGACY` (ver decisiones) evita que
  un proyecto existente quede sin integraciones mientras migra. La persona copia de `.env.example`.
- **El `setup` interactivo, también como opción de compatibilidad.** Se retira entero. Pedir un
  token por consola era la única razón para exigir una terminal, y mantenerlo detrás de una bandera
  deja dos caminos para cargar lo mismo con semánticas distintas (el interactivo escribía el JSON
  que ahora se regenera). `AlmacenSecretos.set/remove` quedan en la interfaz.
- **Otro almacén de secretos o un segundo parser de `.env`.** Se reusa `AlmacenSecretos` y su
  parser pasa a ser una función compartida.
- **Cambiar la auth, la validación o el descubrimiento de Jira y GitLab.** Cambia de dónde sale la
  configuración, no qué se hace con ella.
- **Aflojar `permissions.deny`, el PreToolUse o el rechazo de `--token`.** Nada de esto se toca.
- **Validar el contrato con un intérprete de JSON Schema completo.** El resolvedor valida la forma
  a mano, igual que el resto de los `reglas/` del harness; el schema queda como documento y lo
  cumple la suite con el intérprete de subconjunto.

## Las decisiones, y por qué

### El contrato es un archivo de `reglas/`, y declara cada campo

`harnesses/desarrollo/reglas/integration-environment-contract.json` se instala en
`.claude/harness/reglas/desarrollo/` y se pisa en cada `-Update`, como todo `reglas/`. Su forma es
`comun/schemas/integration-environment-contract.schema.json`, la del paquete con un agregado
opcional: `format: "url"` en un campo, para que la base URL se valide.

Cada campo declara `PUBLIC_CONFIG` o `SECRET`. La heurística de nombres de `config.py`
(`TOKEN`, `SECRET`, `PASSWORD`…) queda como segunda línea: **si un campo `PUBLIC_CONFIG` tiene
nombre o variable con forma de secreto, no se proyecta** (`ENV_PUBLIC_PROJECTION_REJECTED_SECRET`)
y la integración queda sin configurar. Lo explícito `SECRET` gana siempre.

Al seed del paquete se le agrega un campo que ya existe en el código: `gitlabProyecto`
(`GITLAB_PROJECT`, `PUBLIC_CONFIG`, no obligatorio). Lo usa el contexto de tarea, vivía en el JSON
que ahora se regenera, y sin él se perdería en la primera regeneración.

Un id del contrato sin adapter, o un adapter sin entrada en el contrato, es `ENV_CONTRACT_INVALID`:
la CLI sale con 2 y no escribe capacidades. Se prefirió fallar a ignorar: un contrato que nombra
una integración que el código no tiene es un contrato de otra versión.

### La precedencia, con una capa de migración

```
PROCESS_ENV > DOTENV > LEGACY > SAFE_DEFAULT > NOT_CONFIGURED
```

La del paquete es `PROCESS_ENV > DOTENV > SAFE_DEFAULT`. Se inserta `LEGACY` por debajo del `.env`
por una razón: este harness ya está instalado en proyectos que tienen la base URL y el usuario en
el JSON viejo. Sin la capa, el `-Update` los deja con Jira `NOT_CONFIGURED` hasta que alguien migre
a mano. Con la capa siguen andando, y el estado dice qué variables faltan para terminar.

`LEGACY` es la regla "legacy config is migration assistance only" en su forma más estrecha:

- Nunca le gana a un valor del entorno ni del `.env`.
- Solo lee claves públicas del contrato (`legacyConfigKey`), nunca una con forma de secreto.
- Se consume: cuando el `.env` trae la variable, esa entrada sale del bloque `legado` de la
  proyección y no vuelve, aunque después se borre del `.env`.

Un JSON sin la marca `schema_version` de la proyección es el archivo viejo. En su primera
regeneración sus valores públicos pasan al bloque `legado` y el archivo queda en su lugar, con su
nombre. Una proyección ya generada **no** es fuente: lo que el harness escribió no puede volver a
entrar como si lo hubiera escrito una persona.

Que la variable esté en el entorno del proceso y también en el `.env` no es un conflicto: gana el
proceso, que es lo que `AlmacenSecretos.get` ya hacía. Sí es conflicto
(`ENV_CONFIGURATION_CONFLICT`) que el `.env` defina **dos veces** una variable del contrato con
valores distintos: `AlmacenSecretos` se queda con la primera, y la persona que editó la segunda no
se entera.

### Los booleanos, cerrados

`HARNESS_JIRA_ENABLED` y `HARNESS_GITLAB_ENABLED` aceptan `true/false`, `1/0`, `yes/no`, `on/off`,
sin importar mayúsculas. Cualquier otra cosa es `ENV_ENABLED_FLAG_INVALID` y la integración queda
sin configurar, sin red. Una cadena no vacía no es `true`. Un placeholder `<...>` es ausente, como
ya lo era para un token. Sin la variable en ninguna capa, el default del contrato es `false`.

### Los secretos no entran a ninguna estructura

El resolvedor sabe de un `SECRET` si está y de qué capa viene. El valor no se guarda en ningún
objeto que devuelva. El adapter lo sigue pidiendo a `AlmacenSecretos.get`, que es el único camino.
Lo que se compara en memoria —un duplicado del `.env`, un valor público igual a un secreto— se
compara y se tira.

### La proyección es determinista y no se reescribe si no cambió

JSON con claves ordenadas, un bloque por integración con `enabled` y sus campos públicos resueltos,
la lista de variables del contrato (nombres) y, si queda algo por migrar, `legado`. Se escribe solo
si el texto cambió. `config.py` sigue siendo quien la lee, y `ClaveProhibida` sigue rechazando una
clave con forma de secreto antes de escribirla.

### `setup` y `reconfigurar` muestran, no preguntan

`setup` imprime el modo (`ENVIRONMENT_FIRST`), la ruta del `.env` y, por integración, cada variable
con `presente`/`ausente` y la capa de donde sale. Después valida. `reconfigurar <integración>` hace
lo mismo para una, dice qué editar y revalida. Ninguno lee de stdin ni imprime un valor.

### El estado general sabe del `.env` sin abrirlo

`bienvenida.py` agrega `integrationConfiguration` al estado: el modo, si el `.env` existe
(`os.path.isfile`), si el modelo puede leerlo (las reglas `Read(./.env)` y `Read(./.env.*)` de
`permissions.deny` en `.claude/settings.json`) y el estado de la proyección. Cada integración suma
`missing`, los nombres de variable que faltan, que salen del registro de capacidades. Un `.env`
legible por el modelo es la condición pendiente `ENV_MODEL_READABLE`.

### El instalador no escribe el `.env` que ya existe

- `.env.example`: la plantilla del harness va entre marcas `# >>> gcba-harness: integraciones >>>`
  y `# <<< gcba-harness: integraciones <<<`. Sin archivo, se crea; con las marcas, se reemplaza el
  bloque; con la copia que dejaba el harness antes de esta versión, se reemplaza entera; con un
  `.env.example` propio del proyecto, se agrega el bloque al final.
- `.env`: se crea una vez si no existe y no se vuelve a tocar.
- `harness.integraciones.json`: el instalador deja de sembrarlo. Lo genera el bootstrap.
- Al terminar una instalación o un `-Update` con `desarrollo`, corre
  `dev-harness.py estado --resumen`: regenera la proyección, revalida y dice qué falta y qué
  variables son nuevas en el contrato. Si falla, avisa y la instalación sigue.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/integration-environment-contract.schema.json` | La forma del contrato |
| `harnesses/desarrollo/reglas/integration-environment-contract.json` | Jira y GitLab, cada campo clasificado |
| `harnesses/desarrollo/bin/integraciones/entorno.py` | El resolvedor: capas, booleanos, faltantes, proyección, códigos `ENV_*` |
| `harnesses/desarrollo/bin/integraciones/almacen.py` | El parser del `.env` como función compartida; `get` igual |
| `harnesses/desarrollo/bin/integraciones/config.py` | Lee la proyección; mensajes que mandan al `.env` |
| `harnesses/desarrollo/bin/integraciones/base.py` | Faltantes por nombre de variable y "Completá las variables faltantes en el .env local." |
| `harnesses/desarrollo/bin/integraciones/registro.py` | `faltan` por integración en `harness.capacidades.json` |
| `harnesses/desarrollo/bin/dev-harness.py` | Bootstrap desde el resolvedor; `setup`/`reconfigurar` sin preguntas; `estado --resumen` |
| `harnesses/desarrollo/.env.example` | Banderas, variables públicas y tokens con placeholder; sin OpenShift |
| `harnesses/desarrollo/integraciones.plantilla.json` | Se borra |
| `comun/hooks/lib/bienvenida.py` | `integrationConfiguration`, `missing`, `ENV_MODEL_READABLE`, sección Configuración |
| `comun/schemas/harness-installation-state.schema.json` | `integrationConfiguration` |
| `install.ps1` | Bloque marcado en `.env.example`, sin sembrar la proyección, `estado --resumen` al final |
| `tests/casos/60_entorno_primero.py` | Los escenarios de biblioteca y CLI |
| `tests/casos/60-entorno-instalador.ps1` | Los del instalador |

## Escenarios verificables

Los ids siguen el orden de `ENV-001`…`ENV-071` del paquete: `E-nn` es `ENV-0nn`.

### Lo que no se agrega

- **E-01** — `setup`, `estado` y `reconfigurar` imprimen `Modo de configuración: ENVIRONMENT_FIRST`
  y `harness.capacidades.json` lo registra. · rojo visto: si
- **E-02** — El cambio no agrega ningún agente: los `agents/*.md` de la fábrica son los mismos que
  en `426ebeb`. · rojo visto: si
- **E-03** — El cambio no agrega ninguna skill: los `skills/*/SKILL.md` de la fábrica son los mismos
  que en `426ebeb`. · rojo visto: si
- **E-04** — El bootstrap valida con `IntegracionJira` e `IntegracionGitLab`: con el `.env`
  completo, las URLs que pide el transporte son las de `/rest/api/3/myself` y `/api/v4/user`.
  · rojo visto: si
- **E-05** — Una capacidad soportada de una integración no validada figura `DISABLED`, nunca
  ausente, y las siete soportadas siguen en el documento. · rojo visto: si

### De dónde sale cada valor

- **E-06** — `JIRA_BASE_URL` del `.env` llega a la configuración del adapter como `baseUrl`, con
  fuente `DOTENV`. · rojo visto: si
- **E-07** — `JIRA_USER` del `.env` llega como `usuario`, con fuente `DOTENV`. · rojo visto: si
- **E-08** — La configuración que recibe el adapter de Jira no tiene el token; el token que usa sale
  de `AlmacenSecretos.get("JIRA_TOKEN")`, y ni el resultado del resolvedor ni su `repr` lo llevan.
  · rojo visto: si
- **E-09** — `GITLAB_BASE_URL` del `.env` llega al adapter de GitLab como `baseUrl`.
  · rojo visto: si
- **E-10** — Igual que E-08 para `GITLAB_TOKEN` y el adapter de GitLab. · rojo visto: si

### La precedencia

- **E-11** — Con la variable en el entorno del proceso y en el `.env`, gana la del proceso y la
  fuente es `PROCESS_ENV`, sin `ENV_CONFIGURATION_CONFLICT`. · rojo visto: si
- **E-12** — El default del contrato (`enabled: false`) se usa solo si la bandera no está en el
  proceso, ni en el `.env`, ni en el JSON viejo; con cualquiera de esas, la fuente es esa capa.
  · rojo visto: si
- **E-13** — Una variable pública que no está en ninguna capa no aparece en la configuración del
  adapter ni en la proyección: no se completa con un valor inventado. · rojo visto: si
- **E-14** — Un valor vacío o un placeholder `<...>` cuenta como ausente, para una bandera, una
  variable pública y un token. · rojo visto: si

### Las banderas

- **E-15** — Con `HARNESS_JIRA_ENABLED=false` y el resto de Jira vacío, el estado es
  `NOT_CONFIGURED`, la lista de faltantes está vacía y el transporte no recibe ninguna llamada de
  Jira. · rojo visto: si
- **E-16** — Con la bandera en `true` y las tres variables de Jira, el bootstrap valida contra el
  servidor y queda `AVAILABLE`. · rojo visto: si
- **E-17** — Con la bandera en `true` y sin `JIRA_USER`, el estado es `NOT_CONFIGURED`, sin red.
  · rojo visto: si
- **E-18** — En ese caso la salida y `harness.capacidades.json` nombran `JIRA_USER`, y el motivo
  dice `Completá las variables faltantes en el .env local.` · rojo visto: si
- **E-19** — `HARNESS_JIRA_ENABLED=quizas` deja Jira `NOT_CONFIGURED` con
  `ENV_ENABLED_FLAG_INVALID` en el motivo, sin red, y GitLab se resuelve igual.
  · rojo visto: si
- **E-20** — `true`, `TRUE`, `1`, `yes`, `On` se leen verdadero; `false`, `False`, `0`, `NO`, `off`
  falso; `si`, `2`, `enabled` son inválidos. · rojo visto: si

### La proyección

- **E-21** — Con Jira resuelto, la proyección tiene `jira.baseUrl` y `jira.usuario` con los valores
  del `.env`. · rojo visto: si
- **E-22** — El texto de la proyección no contiene el valor de `JIRA_TOKEN` ni el nombre de campo
  `token`. · rojo visto: si
- **E-23** — La proyección tiene `gitlab.baseUrl`. · rojo visto: si
- **E-24** — El texto de la proyección no contiene el valor de `GITLAB_TOKEN`. · rojo visto: si
- **E-25** — Un contrato que clasifica un campo como `SECRET` nunca lo proyecta, aunque su nombre
  no tenga forma de secreto. · rojo visto: si
- **E-26** — Un campo `PUBLIC_CONFIG` cuyo nombre o variable tiene forma de secreto no se proyecta:
  la integración queda con `ENV_PUBLIC_PROJECTION_REJECTED_SECRET`; y `ConfigIntegraciones.guardar`
  sigue levantando `ClaveProhibida`. · rojo visto: si
- **E-27** — Una proyección ya generada con una base URL vieja no le gana al `.env`: después del
  bootstrap vale la del `.env`. · rojo visto: si
- **E-28** — Dos resoluciones de la misma entrada producen el mismo texto, byte a byte.
  · rojo visto: si
- **E-29** — Con la configuración sin cambios, un segundo bootstrap no reescribe la proyección: su
  fecha de modificación no cambia. · rojo visto: si

### El `.env` de la persona

- **E-30** — `install.ps1 -Update` sobre un `.env` existente lo deja byte a byte igual.
  · rojo visto: si
- **E-31** — Un bootstrap (`setup`, `estado`, `reconfigurar`) deja el `.env` byte a byte igual,
  con comentarios, comillas y orden. · rojo visto: si
- **E-32** — Las variables del `.env` que no están en el contrato no entran a la resolución
  (ningún atributo de la `Resolucion` ni de sus integraciones las lleva) ni a ningún archivo que
  escribe el bootstrap. El parser recorre el archivo entero: leer la línea no es tomarla. · rojo visto: si
- **E-33** — Cada línea de asignación del `.env.example` es una variable del contrato, con valor
  vacío, `false` o un placeholder `<...>`. · rojo visto: si
- **E-34** — Ningún valor del `.env.example` tiene forma de credencial según
  `secretos.patrones.json`, y no hay ninguna variable de OpenShift. · rojo visto: si

### Sin preguntas y sin valores

- **E-35** — `setup` con stdin sin terminal y el `.env` vacío sale 0, no llama a `input` ni a
  `getpass`, y no pide ningún token. · rojo visto: si
- **E-36** — `setup` lista, por integración, las variables del contrato con `presente`/`ausente`.
  · rojo visto: si
- **E-37** — `reconfigurar jira` muestra las variables de Jira con su capa y su estado, dice que se
  edita el `.env`, y no imprime ninguno de los valores del `.env`, públicos incluidos.
  · rojo visto: si
- **E-38** — `--token` sigue saliendo con 2 sin repetir el valor y sin escribir nada.
  · rojo visto: si
- **E-39** — Con tokens en el `.env`, ni `setup`, ni `estado`, ni `reconfigurar` escriben un token
  en stdout. · rojo visto: si
- **E-40** — Tampoco en stderr, ni con `ENV_FILE_UNREADABLE`, ni con `ENV_CONTRACT_INVALID`.
  · rojo visto: si

### La frontera del modelo

- **E-41** — `comun/settings/permissions.deny.json` sigue negando `Read(./.env)`.
  · rojo visto: si
- **E-42** — Y `Read(./.env.*)`. · rojo visto: si
- **E-43** — Con un `.env` con tokens y base URLs, lo que imprime `session-start.py` no contiene
  ninguno de esos valores. · rojo visto: si
- **E-44** — El `TaskContext` que escribe `contexto` no contiene ningún valor del `.env` salvo los
  públicos que ya viajaban (la base URL); ningún token. · rojo visto: si
- **E-45** — El libro del Bloque 4 que deja `contabilidad --ingerir` en un proyecto con tokens en el
  `.env` no contiene ninguno. (`contexto` no escribe libro del Bloque 4: su frontera es E-44.) · rojo visto: si
- **E-46** — El libro de seguridad que deja `seguridad` no contiene ningún token del `.env`.
  · rojo visto: si
- **E-47** — `pre-tool-use.py` sigue bloqueando un `Write` que pone un token literal en el `.env`.
  · rojo visto: si

### Lo que no cambia en los adapters

- **E-48** — Jira manda `Authorization: Basic base64(JIRA_USER:JIRA_TOKEN)` con los valores
  resueltos del `.env`, y un 401 da `AUTHENTICATION_FAILED`. · rojo visto: si
- **E-49** — GitLab manda `PRIVATE-TOKEN` con el token del `.env`, sin `Authorization`, y un 401 da
  `AUTHENTICATION_FAILED`. · rojo visto: si
- **E-50** — Con scopes `read_api`, GitLab resuelto desde el `.env` habilita sus cuatro capacidades,
  como antes. · rojo visto: si
- **E-51** — Jira sin configurar deja sus tres capacidades `DISABLED`. · rojo visto: si
- **E-52** — GitLab sin configurar deja sus cuatro capacidades `DISABLED`. · rojo visto: si

### La migración

- **E-53** — Con un JSON viejo (sin marca) que tiene `enabled: true`, `baseUrl` y `usuario`, y un
  `.env` con solo `JIRA_TOKEN`, Jira valida con esos valores, la fuente es `LEGACY` y la salida
  nombra las variables que faltan para migrar. · rojo visto: si
- **E-54** — Con el JSON viejo y `JIRA_BASE_URL` en el `.env`, gana el `.env`; y después de borrar
  la variable del `.env`, el valor viejo no vuelve. · rojo visto: si
- **E-55** — Un JSON viejo con una clave `token` o `apiKey` no la lee, no la imprime y no la copia
  a la proyección: con esa clave y sin `JIRA_TOKEN` en el `.env`, Jira queda `NOT_CONFIGURED` con
  `JIRA_TOKEN` en los faltantes y sin red. · rojo visto: si
- **E-56** — Después de la migración `harness.integraciones.json` sigue en el mismo lugar, con la
  marca de proyección. · rojo visto: si

### El estado general

- **E-57** — `harness --json` tiene `integrationConfiguration.configurationMode` =
  `ENVIRONMENT_FIRST`. · rojo visto: si
- **E-58** — `integrationConfiguration.envFilePresent` es `true` con `.env` y `false` sin él, y el
  documento no contiene ningún valor del `.env`. · rojo visto: si
- **E-59** — La bienvenida completa tiene la sección `Configuración` con `Fuente` y `Acceso del
  modelo`, y bajo una integración sin configurar `Faltan:` con los nombres. · rojo visto: si
- **E-60** — Con una integración sin configurar el estado es `PARCIAL`; con las dos disponibles y
  el resto en orden, `LISTO`; con el `.env` legible por el modelo, `ENV_MODEL_READABLE` pendiente.
  · rojo visto: si

### La actualización

- **E-61** — `install.ps1 -Update` no cambia un byte del `.env`, tampoco si le faltan las variables
  nuevas. · rojo visto: si
- **E-62** — Una proyección generada con una lista de variables más corta que la del contrato hace
  que `estado --resumen` diga `Variables nuevas` con los nombres que faltaban en la lista.
  · rojo visto: si
- **E-63** — `-Update` deja en `.claude/harness/reglas/desarrollo/` el contrato de la fábrica, y en
  `.env.example` el bloque marcado igual a la plantilla, conservando lo que el proyecto tenía fuera
  del bloque. · rojo visto: si
- **E-64** — `-Update` sobre un proyecto con el JSON viejo lo deja convertido en proyección.
  · rojo visto: si
- **E-65** — `-Update` deja `harness.capacidades.json` escrito por esa corrida, con `faltan` por
  integración. · rojo visto: si

### Contratos rotos y archivos que no se leen

- **E-66** — El contrato de la fábrica tiene exactamente las integraciones `jira` y `gitlab`, y
  ninguna variable que empiece con `OPENSHIFT`. · rojo visto: si
- **E-67** — Un contrato con una integración sin adapter (`openshift`) es `ENV_CONTRACT_INVALID`: la
  CLI sale con 2, lo nombra, y no escribe `harness.capacidades.json`. · rojo visto: si
- **E-68** — Un contrato roto (JSON inválido, sin `integrations`, una clasificación desconocida, una
  variable repetida) es `ENV_CONTRACT_INVALID`. · rojo visto: si
- **E-69** — Un `.env` que no se puede leer (un directorio, bytes que no son UTF-8) es
  `ENV_FILE_UNREADABLE`: sale con 2, el mensaje nombra el archivo y no trae ningún byte de su
  contenido. · rojo visto: si
- **E-70** — La condición `ENV_MODEL_READABLE` se describe sin ningún valor del `.env`.
  · rojo visto: si

### La compuerta

- **E-71** — `.\tests\Invoke-Tests.ps1` sale en verde, con los dos motores. · rojo visto: no consta

## Cómo se verifica

Todos por la suite. `tests/casos/60_entorno_primero.py` tiene E-01 a E-29, E-31 a E-60 y E-62,
E-66 a E-70; `tests/casos/60-entorno-instalador.ps1` tiene E-30, E-61 y E-63 a E-65. E-02 y E-03
comparan contra el árbol de `426ebeb` con `git ls-tree`. E-71 es la corrida entera. Ninguno se lee:
no hay un modelo en el camino.

Los tests de `18_integraciones.py`, `17-env-instalador.ps1`, `18-integraciones-instalador.ps1` y
`51_bienvenida.py` que fijaban el `setup` interactivo, la siembra del JSON o `OPENSHIFT_TOKEN` se
reescriben con la conducta nueva y dicen `pisado por docs/cambios/entorno-primero/spec.md`.

## Riesgos conocidos

- **`LEGACY` estira la migración.** Un proyecto puede quedarse para siempre con valores en el
  bloque `legado`. El estado lo dice cada vez, pero no obliga.
- **Un valor público borrado con `legado` todavía presente.** Si la persona nunca pasó esa variable
  al `.env` y la quiere vaciar, un `JIRA_BASE_URL=` vacío es ausente y el valor viejo sigue. La
  salida es `HARNESS_JIRA_ENABLED=false` o borrar la proyección.
- **El `-Update` sale a la red.** Revalidar es parte de actualizar, y con Jira y GitLab
  configurados eso puede sumar hasta dos timeouts por integración. Se avisa y no voltea la
  instalación.
- **`permissions.deny` es best-effort.** Cubre lo que Claude Code resuelve como ruta. Una lectura
  indirecta puede escapar, y este cambio no lo empeora ni lo arregla.
- **Local no es sin riesgo.** El `.env` sigue expuesto a lo que tenga acceso a la máquina: backups,
  copias, el entorno del proceso.
