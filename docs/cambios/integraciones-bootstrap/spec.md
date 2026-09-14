# Bloque 1 — Bootstrap e integraciones: Jira Cloud y GitLab

**Estado:** especificado · **Fecha:** 14-09-2026

## Qué problema resuelve

0.15.0 dejó el enchufe y nada enchufado: un `.env` con seis variables que ningún código lee. Hoy el
harness no puede contestar la única pregunta que importa antes de que un agente intente usar una
herramienta externa:

> ¿Qué integraciones tengo configuradas, cuáles funcionan y qué capacidades puedo usar?

Sin esa respuesta, la alternativa es que cada agente arme su propia llamada a Jira o a GitLab, con
su propio manejo de credenciales, y descubra que el token venció en el medio de una tarea. Este
cambio construye la base: un asistente de configuración, una abstracción de almacenamiento de
secretos, dos adapters con diagnóstico real, y un registro central que solo habilita lo que se pudo
validar.

El límite es exactamente ese. Al terminar, el harness arranca, valida, descubre y declara
`HARNESS READY`. Lo que haga después con esas capacidades es otro cambio.

## Qué queda afuera

- **Todo el Bloque 2.** `TaskContext`, resolución de tickets, Ficha de Proyecto, recuperación de
  HUs, procesamiento documental, orquestación y agent loops. Construirlos ahora sería decidir la
  forma de un consumidor que todavía no existe, y este cambio ya es grande.
- **Ningún agente consume el registro todavía.** Las capacidades quedan escritas en un archivo; qué
  agente las lee y cómo se le entregan las tools es la decisión que abre el Bloque 2. Anticiparla
  acá la tomaría sin discutirla.
- **OpenShift no tiene adapter.** El pedido nombra Jira y GitLab. `OPENSHIFT_TOKEN` se queda en el
  `.env` sin consumidor, y es la prueba barata de que sumar un tercero no toca el núcleo: si
  agregarlo obligara a modificar el bootstrap, el diseño está mal y conviene enterarse antes de
  construir el cuarto.
- **Solo lectura.** Ninguna capacidad escribe: nada de crear issues, comentar, abrir MRs ni mover
  estados. Mínimo privilegio, y una operación destructiva expuesta en la fase donde todavía nadie
  sabe quién la va a invocar es la forma más barata de romper un proyecto ajeno.
- **Sin MCP.** Explícito en el pedido, y coherente con ADR-0008: un servidor MCP es un proceso más
  que tiene que estar levantado para que el harness funcione.
- **Sin Windows Credential Manager, Vault ni secret manager corporativo.** La abstracción
  `AlmacenSecretos` existe justamente para que cambiar el backend después no toque a nadie más; el
  backend de hoy es el `.env` que 0.15.0 ya dejó protegido por tres capas. Traer DPAPI o Vault ahora
  sería infraestructura para un requisito que nadie pidió.
- **Sin caché de validación.** Cada corrida revalida contra la API. Cachear obliga a decidir cuánto
  dura la caché y a explicar por qué el harness dice `AVAILABLE` sobre un token que venció hace una
  hora.
- **Sin archivo de log histórico.** Ver las decisiones.
- **Sin schema JSON versionado del registro.** Ver las decisiones.
- **Sin lanzador corto.** El comando se invoca con
  `python .claude/harness/bin/desarrollo/dev-harness.py`, largo y explícito, igual que
  `contexto-armar.py`. Un shim `.cmd`/`.sh` como el de los hooks es trabajo aparte y no cambia
  ninguna de las decisiones de este cambio.

## Las decisiones, y por qué

### El token no entra nunca por la línea de comandos

`--token` existe en el parser con un solo propósito: rechazarlo y explicar por qué. Un argumento de
línea de comandos queda en el historial del shell, en la lista de procesos de la máquina, en la
transcripción de una sesión de Claude Code si fue el agente quien lo tipeó, y en el texto que el
hook `PreToolUse` inspecciona. El token se pide por `getpass`, que no hace eco y no toca ninguna de
esas cuatro superficies.

La alternativa considerada era aceptarlo para poder automatizar el setup en CI. Se descartó: no hay
CI que instale este harness hoy, y el día que lo haya, el camino correcto es la variable de entorno
—que el almacén ya lee y que le gana al archivo— y no un argumento.

### La configuración se separa del secreto, en dos archivos distintos

`.claude/harness.integraciones.json` lleva `enabled`, `baseUrl` y `usuario`. El `.env` lleva los
tokens y nada más. Las tres `*_BASE_URL` que 0.15.0 puso en el `.env` se mudan.

No es prolijidad: el agente **puede** leer el primero y **no puede** leer el segundo —
`permissions.deny` tapa `.env` y `.env.*`. Con las URLs adentro del `.env`, el harness le esconde al
agente hasta con qué instancia de Jira habla el proyecto, que no es un secreto y es información
útil. Con la separación, cada archivo queda del lado correcto de una frontera que ya existía.

El costo es real y se acepta: un proyecto instalado con 0.15.0 que ya completó `JIRA_BASE_URL` en su
`.env` tiene que mover ese valor. Son tres líneas y `UPGRADE.md` las dice.

### Cinco estados, nunca un booleano

`NOT_CONFIGURED`, `AUTHENTICATION_FAILED`, `CONNECTION_FAILED`, `PERMISSION_DENIED`, `AVAILABLE`.
Un booleano contesta "no anda" a cuatro preguntas distintas que se arreglan de cuatro formas
distintas: completar la configuración, generar un token nuevo, revisar la red o la VPN, o pedir
permisos. El harness ya tomó esta decisión una vez, en el detector de secretos: dos niveles de
confianza en vez de bloquear todo, porque la respuesta correcta depende del caso.

### El motivo nunca sale del cuerpo de la respuesta

Cada estado trae un `motivo` tomado de un diccionario fijo del código. El cuerpo que devolvió el
servidor no se copia, ni se resume, ni se adjunta. Un servidor puede devolver el token adentro de un
mensaje de error, y ese cuerpo terminaría en la salida de consola, en el JSON del registro y, si un
agente lo lee, en el contexto del modelo. Se pierde detalle de diagnóstico y se gana que no haya
ninguna ruta por la que un secreto se escape a un archivo.

### El transporte HTTP se inyecta

`pedir(url, headers, timeout, transporte=None)`. En producción el transporte es `urllib.request`;
en la suite es una función que devuelve códigos y cuerpos fijos. Sin esto, probar los cinco estados
exigiría una instancia real de Jira, una red, y un token que venza a pedido — es decir, no se
probarían. Es la misma maniobra que el harness ya usa con los hooks y sus payloads.

### La capacidad se declara en el código y se espeja en el manifiesto

`capacidadesSoportadas` en `harnesses/desarrollo/manifest.json` es lo que el harness **soporta**; el
registro que se genera en cada corrida es lo que está **disponible**. Las dos listas tienen que
coincidir y un test lo comprueba: el manifiesto documenta y la suite impide que documente una
mentira. Se descartó que el manifiesto fuera la única fuente —el código tendría que leerlo desde
`.claude/harness/manifiestos/` en tiempo de ejecución, y eso ata el módulo a una ruta de instalación
que no existe cuando corre la suite.

### Degradación controlada: una integración caída no voltea el harness

`estado` sale con código 0 aunque Jira esté inalcanzable. Lo que cambia es qué capacidades quedan
`ENABLED`. El código 2 se reserva para una falla del harness mismo —configuración ilegible, `.env`
que no se puede escribir—, que es lo único que la persona tiene que arreglar antes de seguir. Un
harness que se cae entero porque venció un token no se usa la segunda semana; es el mismo criterio
por el que los hooks salen siempre con 0.

### Los eventos van a stdout; no hay archivo de log

`validacion.inicio`, `validacion.ok`, `validacion.falla`, `capacidad.habilitada`,
`capacidad.deshabilitada` y `harness.listo` se emiten en una línea estable por evento, y el último
resultado queda persistido en el registro con su fecha. Un archivo de log trae rotación, tamaño,
permisos y una ruta más que limpiar en `-Uninstall`, para un dato que hoy nadie consulta. Si mañana
hace falta traza histórica, redirigir stdout a un archivo ya alcanza.

### Sin schema versionado del registro, todavía

`comun/schemas/` existe y `contexto-armar.py` trae su propio validador de un subconjunto de JSON
Schema. Son ochenta líneas más para un documento que hoy escribe y lee el mismo código. El día que
un agente distinto lo consuma —Bloque 2— el schema entra primero, por el mismo motivo por el que
entró el de `project-context`. El documento ya lleva `schema_version` para que ese día no sea una
migración.

### El código va en `harnesses/desarrollo/bin/`

Sigue el precedente de 0.15.0: las credenciales externas las reparte `desarrollo`, no `comun`. Se
consideró el núcleo en `comun/` con los adapters en `desarrollo` —`analisis` declara `gestorTickets`
en su manifiesto y también podría querer hablar con Jira— y se dejó afuera: hoy sería una frontera
inventada entre dos partes que nadie pidió separar, y moverla después es un rename con la suite
verde de testigo.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/dev-harness.py` | El punto de entrada: `setup`, `estado`, `reconfigurar`, con `--json` y `--proyecto`. Lo único que habla con la persona |
| `harnesses/desarrollo/bin/integraciones/http.py` | Cliente HTTP sobre `urllib.request`, con timeout y transporte inyectable. Nunca vuelca headers |
| `harnesses/desarrollo/bin/integraciones/almacen.py` | `AlmacenSecretos`: `get`, `set`, `exists`, `remove` sobre el `.env`, con `os.environ` por encima |
| `harnesses/desarrollo/bin/integraciones/config.py` | `ConfigIntegraciones`: lee y escribe `.claude/harness.integraciones.json` y rechaza toda clave con forma de secreto |
| `harnesses/desarrollo/bin/integraciones/base.py` | El contrato `Integracion`, los cinco estados y el mapeo desde una respuesta HTTP |
| `harnesses/desarrollo/bin/integraciones/jira.py` | `IntegracionJira`: auth Basic, validación contra `/rest/api/3/myself`, tres capacidades |
| `harnesses/desarrollo/bin/integraciones/gitlab.py` | `IntegracionGitLab`: auth `PRIVATE-TOKEN`, validación contra `/api/v4/user`, cuatro capacidades |
| `harnesses/desarrollo/bin/integraciones/registro.py` | `RegistroCapacidades`: registra, consulta, cruza soportadas contra disponibles y escribe `.claude/harness.capacidades.json` |
| `harnesses/desarrollo/integraciones.plantilla.json` | La configuración inicial que el instalador siembra una sola vez |
| `harnesses/desarrollo/.env.example` | Se reduce a los tres `*_TOKEN`; las `*_BASE_URL` se van a la configuración |
| `harnesses/desarrollo/manifest.json` | `capacidadesSoportadas` con las siete, y `timeoutIntegraciones` en `config` |
| `install.ps1` | Copia `harnesses/<id>/bin`, siembra `harness.integraciones.json`, y `Copy-Arbol` deja de copiar bytecode |
| `docs/integraciones.md` | Cómo se configura, qué significa cada estado y cómo se agrega la próxima integración |
| `tests/casos/18_integraciones.py` | Los escenarios de almacén, configuración, adapters, descubrimiento y registro |
| `tests/casos/18-integraciones-instalador.ps1` | Los escenarios de instalación, `-Update` y `-Uninstall` |

## Escenarios verificables

### El almacén de secretos

- **E-01** — `get` de una variable presente en el `.env` devuelve su valor; de una ausente devuelve
  `None`. · rojo visto: si
- **E-01b** — Un valor vacío o un placeholder entre ángulos —el que reparte `.env.example`— se lee
  como ausente, no como token. · rojo visto: si
- **E-02** — Con la misma variable definida en el `.env` y en el entorno del proceso, gana la del
  entorno. · rojo visto: si
- **E-03** — `set` sobre una clave que ya existe reescribe solo esa línea: los comentarios, el orden
  y las demás variables del archivo quedan idénticos. · rojo visto: si
- **E-04** — `set` sobre una clave ausente la agrega y el resto del archivo no se mueve.
  · rojo visto: si
- **E-05** — `remove` borra la línea y `exists` devuelve falso después. · rojo visto: si
- **E-06** — Ni la representación del almacén ni el texto de ninguna excepción que levante contienen
  el valor de un secreto. · rojo visto: si

### La configuración

- **E-07** — Un `harness.integraciones.json` inexistente da una configuración vacía, no un error, y
  cada integración sale `NOT_CONFIGURED`. · rojo visto: si
- **E-08** — Guardar una clave cuyo nombre contiene `TOKEN`, `SECRET`, `PASSWORD` o `CREDENTIAL`
  levanta error y deja el archivo sin tocar. · rojo visto: si
- **E-09** — Guardar la configuración de una integración no toca las claves de las otras, ni las que
  el harness no conoce. · rojo visto: si

### El cliente HTTP

- **E-10** — Contra un servidor local en `127.0.0.1`, `pedir` devuelve el código de estado y el
  cuerpo tal cual, para 200 y para 401. · rojo visto: si
- **E-11** — Un transporte que levanta un error de red produce una respuesta con código 0 y su clase
  de error, nunca una excepción que salga del módulo. · rojo visto: si

### El contrato de una integración

- **E-12** — Sin `baseUrl` o sin token, el estado es `NOT_CONFIGURED` **y el transporte no se invoca
  ni una vez**. · rojo visto: si
- **E-13** — Con `enabled` en falso, el estado es `NOT_CONFIGURED` con su motivo, sin salir a la
  red. · rojo visto: si
- **E-14** — Los cuatro estados restantes salen del código de respuesta: 200 es `AVAILABLE`, 401 es
  `AUTHENTICATION_FAILED`, 403 es `PERMISSION_DENIED`, y un timeout, un error de DNS o un 5xx son
  `CONNECTION_FAILED`. · rojo visto: si
- **E-15** — Jira manda `Authorization: Basic` con `usuario:token` en base64; GitLab manda el token
  en el header `PRIVATE-TOKEN`. Ninguno de los dos lo manda en la URL. · rojo visto: si
- **E-16** — Ningún motivo de ningún estado contiene el token, ni siquiera cuando el servidor lo
  devuelve adentro del cuerpo de la respuesta de error. · rojo visto: si

### El descubrimiento de capacidades

- **E-17** — Una integración que no está `AVAILABLE` no descubre ninguna capacidad y no hace ni una
  llamada de sondeo. · rojo visto: si
- **E-18** — Jira `AVAILABLE` con el sondeo de adjuntos respondiendo 403 registra `jira.issue.read`
  y `jira.issue.search`, y no registra `jira.attachment.read`. · rojo visto: si
- **E-18b** — Si `/search/jql` responde 410 se prueba `/rest/api/3/search`, y las capacidades de
  búsqueda se declaran recién cuando alguno de los dos contesta. · rojo visto: si
- **E-19** — GitLab deriva sus capacidades de los scopes reales del token: `read_api` habilita las
  cuatro; un token con solo `read_repository` habilita `gitlab.repository.read` y ninguna otra.
  · rojo visto: si
- **E-20** — Si el endpoint de scopes responde 404 —GitLab viejo—, se cae al sondeo por endpoints y
  se registra lo que respondió 200. · rojo visto: si

### El registro de capacidades

- **E-21** — Una capacidad soportada cuya integración no está `AVAILABLE` figura en el registro como
  `DISABLED`, nunca ausente. · rojo visto: si
- **E-22** — `disponibles()` devuelve solo las `ENABLED`, y `por_integracion` las agrupa por su
  integración. · rojo visto: si
- **E-23** — Las capacidades que declara el manifiesto y las que declaran los adapters son
  exactamente las mismas. · rojo visto: si

### La degradación y la segunda corrida

- **E-24** — Con Jira inalcanzable y GitLab válido, `estado` sale con código 0, declara
  `HARNESS READY` y deja las capacidades de GitLab `ENABLED` y las de Jira `DISABLED`.
  · rojo visto: si
- **E-25** — Con la configuración completa y los tokens presentes, `setup` no lee de stdin: corre con
  la entrada cerrada y no falla ni se cuelga. · rojo visto: si
- **E-26** — `reconfigurar gitlab` no modifica ni la configuración ni el token de Jira.
  · rojo visto: si
- **E-26b** — Una primera corrida completa del asistente: se responden las preguntas, la
  configuración queda guardada, el token queda en el `.env` y no aparece ni en la salida ni en el
  archivo de configuración. · rojo visto: si
- **E-27** — `--token` es rechazado con un mensaje que explica por qué, con código distinto de 0, y
  sin escribir ningún archivo. · rojo visto: si
- **E-28** — Una configuración ilegible da código 2 y un mensaje que nombra el archivo y qué hacer,
  en vez de una traza de Python. · rojo visto: si

### El instalador

- **E-29** — Con `desarrollo` instalado, quedan `dev-harness.py` y los módulos de `integraciones/`
  bajo `.claude/harness/bin/desarrollo/`, y `harness.integraciones.json` en `.claude/`.
  · rojo visto: si
- **E-30** — Sin `desarrollo`, no queda nada de eso. · rojo visto: si
- **E-31** — Un `-Update` sobre un proyecto que ya tiene `harness.integraciones.json` lo deja
  idéntico, y actualiza los módulos del `bin`. · rojo visto: si
- **E-32** — `-Uninstall` borra el `bin` instalado y no toca `.env` ni `harness.integraciones.json`.
  · rojo visto: si
- **E-33** — El lockfile no inventaría bytecode: ni una entrada `__pycache__` ni `.pyc`, ni
  siquiera instalando desde un árbol donde la suite ya corrió. · rojo visto: si

  📌 **El escenario decía "ninguna instalación deja un `.pyc` en el proyecto", y eso era falso
  por una razón buena.** El propio instalador corre los cuatro hooks y los checks para
  verificarlos, y el intérprete compila adentro del proyecto: doce archivos que nadie copió —
  cinco de `hooks/lib`, siete de la corrida de los checks. Ese
  bytecode es local, del intérprete de esa máquina, y acelera un hook que se paga en cada llamada
  a herramienta — sacarlo sería pagar latencia para que un test cierre. Lo que el pendiente
  denunciaba es otra cosa: bytecode **copiado** desde la máquina de quien instala y anotado en el
  lockfile, que vuelve la instalación irreproducible. El escenario se corrigió para decir eso, y
  lo que quedaba suelto —que ese bytecode local sobreviviera a `-Uninstall`— se convirtió en
  E-33b.

- **E-33b** — `-Uninstall` no deja `.claude/harness` en pie: el bytecode que el harness generó al
  correr se borra con él. · rojo visto: si

### Los secretos

- **E-34** — El `.env.example` reducido sigue sin disparar ningún patrón del catálogo.
  · rojo visto: si

## Cómo se verifica

Los treinta y ocho son deterministas y ninguno depende de una corrida de un modelo: no hay
escenario de lectura en este cambio.

- **E-01 a E-28** corren en `tests/casos/18_integraciones.py`, contra el `.env` y la configuración
  de un directorio temporal, y con un transporte falso que devuelve códigos y cuerpos fijos. E-10 es
  la única excepción: levanta un `http.server` en `127.0.0.1` para ejercitar `urllib` de verdad.
- **E-29 a E-33b** corren en `tests/casos/18-integraciones-instalador.ps1` sobre proyectos
  descartables, igual que el resto de la suite de instalador.
- **E-34** corre en `tests/casos/04_secretos.py`, que ya lee el `.env.example` real y entero.

Ningún test sale a una red que no sea `127.0.0.1`.

## Riesgos conocidos

- **Ningún escenario prueba contra un Jira o un GitLab real.** La suite prueba el mapeo de estados y
  de capacidades, no la API. La primera corrida contra una instancia real puede encontrar un
  endpoint movido: `/rest/api/3/search` fue reemplazado por `/rest/api/3/search/jql` en Jira Cloud, y
  `/api/v4/personal_access_tokens/self` no existe en GitLab viejo. Los dos casos tienen caída a un
  camino alternativo, y las dos caídas están probadas — pero probadas contra un transporte falso.
- **`permissions.deny` tapa `Read(./.env.*)` y eso incluye `.env.example`.** Anotado en
  `PENDIENTES-FH.md` al cerrar 0.15.0; este cambio lo empeora un poco, porque ahora la plantilla es
  lo único que le dice a alguien qué tokens hacen falta.
- **La migración de las `*_BASE_URL` es manual.** Un proyecto instalado con 0.15.0 que ya las
  completó tiene que moverlas al archivo de configuración. El harness no las lee del `.env` ni
  siquiera como caída: leerlas sería mantener vivo el formato que este cambio viene a separar.
- **El token se valida cuando alguien corre el comando, no cuando vence.** Un token que expira a la
  mañana deja el registro mintiendo hasta la próxima corrida. Cachear no lo arregla; lo arregla que
  el consumidor revalide, y el consumidor es el Bloque 2.
- **`timeoutIntegraciones` es un solo número para todas las llamadas.** Una instancia lenta detrás
  de VPN puede dar `CONNECTION_FAILED` cuando el problema es la latencia. Se acepta: el remedio es
  subir el número en `harness.config.json`, y está documentado.
