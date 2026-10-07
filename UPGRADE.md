# Upgrade

Qué hacer al pasar de una versión del harness a la siguiente. Cada entrada dice si el
`-Update` alcanza o si hay algo manual.

El procedimiento normal es siempre el mismo:

```powershell
git -C C:\Work\gcba-harness pull
.\install.ps1 -Doctor
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Update
```

**El `git pull` trae la versión nueva del harness; el `-Update` la lleva a cada proyecto.** Son dos
pasos porque son dos cosas: el repo del harness es uno solo y los proyectos instalados son muchos.
En la máquina donde se escribe el harness los cambios ya están y el `pull` no hace falta.

📌 **Esto decía "no hay `git pull` porque todavía no hay remoto".** Lo hubo desde 0.17.0: el repo
vive en `github.com/NahuellPalacio/Harness-Project`. La frase quedó vieja el día que se publicó.

`-Update` reporta al final los archivos que **no** pisó porque los habías editado a mano.
Quedan como `<archivo>.nuevo` al lado del tuyo, para que hagas el merge vos.

---

## 0.30.0 → 0.31.0

`-Update` alcanza. No hay que migrar nada a mano: el `-Update` instala los módulos del flujo, sus
seis schemas y el matcher nuevo de `PreToolUse` (`^Agent$|^Task$|^mcp__`). Al terminar avisa si
hay que reiniciar Claude Code.

Lo que se nota depende de si el proyecto tiene **estado del flujo**, o sea algo adentro de
`.claude/runtime/tasks/`. Lo crean `contexto`, `plan` y `refute` de `dev-harness.py`.

- **Sin estado del flujo, nada cambia** en lo que bloquea el hook. Solo las llamadas a `Agent`,
  `Task` y a herramientas `mcp__*` pasan ahora por `PreToolUse`, y pagan su arranque.
- **Con estado del flujo:**
  - si la tarea de la sesión está bloqueada, `Write`, `Edit`, los comandos que escriben y la
    delegación se niegan. El motivo dice qué falta;
  - con dos o más tareas, la sesión tiene que decir cuál trabaja. Basta una línea con la clave sola
    (`ABC-123`) o `seguimos con ABC-123`. Si no la dice, se niega con `SESSION_TASK_AMBIGUOUS`;
  - aprobar, elegir o cancelar se escribe en el chat, exacto y en mayúsculas
    (`HARNESS APPROVE ABC-123 <interactionId>`). Un «dale» no aprueba;
  - ninguna herramienta del modelo escribe `.claude/` ni `.git/`. Tampoco un `git config` que
    escribe. `git commit -m "... config ..."` también se niega: se usa `git commit -F <archivo>`;
  - una MCP que nombra `.claude/`, `.git/` o «git config» en un valor se niega, aunque solo lea.
- **El plan pasa a `orchestration-plan/2.1`.** Suma `BLOCKED` como estado del plan y `blockers` en
  la unidad. Lo que pasa con un plan guardado en `.claude\planes\`:
  - **un 2.0 de 0.30.0** se lee, pero `refute --compile` sale con 2 y `PLAN_NOT_READY`: no trae
    las precondiciones del flujo. Se resuelve con
    `python .claude\harness\bin\desarrollo\dev-harness.py plan <KEY> --replanificar <propuesta> --motivo "<por qué>"`,
    que lo escribe como 2.1 con la versión siguiente y su historia;
  - **un 2.0 o un 1.0 con `DELEGATING` o una unidad `READY`** se rechaza igual que en 0.30.0;
  - **una aprobación desde `flujo`** sobre un plan 2.0 también lo escribe como 2.1.
- **`plan` con una fuente exigida en alerta de integridad escribe el plan `BLOCKED`.** Una fuente
  seguida y no exigida ya no corta, solo avisa.
- **Un ciclo o una dependencia rota en la propuesta sale con 2**, no con 1.
- **El Bloque 4 y la Context Bar muestran `N/D`** donde antes había un `0` o un parcial.
- **Un script que corría `install.ps1 -NonInteractive` sin `-Usuario` sale 1** con el diagnóstico,
  también desde una consola. Con `-Confirm` y sin nadie a quien preguntar, sale con error y no
  instala nada.

## 0.29.0 → 0.30.0

`-Update` alcanza para un proyecto instalado: no hay que migrar nada a mano. Si hace falta reiniciar
Claude Code, el `-Update` lo avisa al final.

Lo que hay que saber es qué pasa con los planes guardados en `.claude\planes\`, porque el contrato
del plan sube de versión mayor.

🔴 **`orchestration-plan` pasa de 1.0 a 2.0.** Es la versión del contrato del plan, no la de HARNESS.
El plan tiene ahora tres estados, y la unidad otros tres. Salen los estados que 0.29.0 declaraba y
nunca escribía, como `DELEGATING` en el plan y `READY` en la unidad. `plan` escribe solo 2.0, y un
plan guardado cae en uno de estos tres casos:

- **Un plan 1.0 que escribió HARNESS 0.29.0.** Sus estados existen en 2.0, así que:
  - `refute --compile` lo sigue leyendo y no lo reescribe solo por leerlo. Compila las mismas
    unidades que antes, con la misma `cacheKey` y los mismos veredictos;
  - `--replanificar` lo migra: lo escribe como 2.0, con `plan_version` + 1 y la historia entera.

  No hay que hacer nada.
- **Un plan 1.0 válido para el schema viejo, pero con un estado retirado**, como `DELEGATING` o una
  unidad en `READY`:
  - se rechaza con código 2, y el mensaje nombra el campo y el valor;
  - no se convierte a otro estado: no hay un estado 2.0 que signifique eso;
  - hay que regenerarlo:

    ```powershell
    python .claude\harness\bin\desarrollo\dev-harness.py plan <KEY> --propuesta <archivo>
    ```

  HARNESS 0.29.0 nunca escribió esos estados, así que esto solo le pasa a un plan editado a mano o
  escrito por otra herramienta.
- **Un plan con otra versión, o sin `schema_version`.** Se rechaza con código 2, nombrando la
  versión. Hay que regenerarlo igual.

**Qué toca un rechazo.** No toca el plan, la refutación (`.claude\refutaciones\<KEY>\`) ni su caché:
la regla de lectura corre antes de cualquier escritura. Lo que no se deshace es lo que ya escribió
la compuerta normativa en esa misma corrida, porque no hay un rollback global.

**Lo que antes se aceptaba y ahora sale con código 2, sin escribir nada:**

- `seguridad` con una clave que no es una TaskKey válida (`OBRA-91` sí; `OBRA91` u `OBRA-` no);
- `contabilidad` con una clave que no es una TaskKey ni el UUID de una sesión de Claude Code. La
  `statusLine` no cambia;
- `plan --propuesta` y `--replanificar` con dos unidades con el mismo id, o con una unidad de un
  dominio que no está en `domains`. Hasta 0.29.0 el plan se escribía igual. Si un script o una
  propuesta guardada dependía de eso, hay que corregir la propuesta.

## 0.28.0 → 0.29.0

`-Update` alcanza para un proyecto instalado. Lo manual está en los scripts que pasen `-Harness`, y
en reiniciar Claude Code después del `-Update`.

- 🔴 **El parámetro `-Harness` ya no existe.** Pasarlo sale con 1, sin escribir nada, y con el error
  de PowerShell:

  ```
  No se encuentra ningún parámetro que coincida con el nombre del parámetro 'Harness'.
  ```

  Hay que sacarlo de cualquier script, `.cmd` o CI que lo use. El harness es uno solo, y se instala
  así:

  ```powershell
  .\install.ps1 -Project <ruta> -Usuario <nombre>
  ```

  Los argumentos sin nombre también dejan de andar: `-Project` y `-Usuario` van siempre con su
  nombre.

- 🔴 **Si el proyecto tenía `analisis`, el `-Update` lo retira.** El proyecto pasa a tener el producto
  entero (`comun` y `desarrollo`), y salen:
  - las skills y agentes `hu-escribir`, `hu-redactor` y `hu-refutador`;
  - las reglas de "Trabajo funcional" del bloque `HARNESS:COMUN` del `CLAUDE.md`, que pasan a ser las
    de "Trabajo técnico". El `CLAUDE.md` anterior queda en el backup de esa corrida.

  `harness.config.json` no se toca. Si habías editado a mano alguno de esos archivos, queda en disco
  y la salida lo nombra, pero sale del inventario: `-Doctor` y `-Uninstall` dejan de mirarlo. Mirá el
  lockfile antes de actualizar: si en `.claude\harness.lock.json` el campo `harness` lista
  `analisis`, quien usa el proyecto tiene que saberlo antes.

- **La Context Bar queda en `RELOAD_REQUIRED`.** Hay que cerrar y volver a abrir la sesión de Claude
  Code para que la active. El `-Update` lo avisa: *Reiniciá la sesión de Claude Code para activarla.*

- 🔴 **Volver a 0.28.0 no se puede con `-Update`.** El lockfile nuevo no tiene el campo `harness`, y el
  `-Update` y el `-Doctor -Project` del instalador de 0.28.0 mueren al leerlo, antes de tocar nada.
  Para volver, primero se desinstala con este instalador y después se reinstala con el de 0.28.0:

  ```powershell
  .\install.ps1 -Project <ruta> -Uninstall
  # con el repo del harness en 0.28.0:
  .\install.ps1 -Project <ruta> -Harness desarrollo -Usuario <nombre>
  ```

## 0.27.0 → 0.28.0

`-Update` alcanza. Lo nuevo se ve al terminar:

- **Si el proyecto no tenía `.claude/harness.presupuesto.json`, el `-Update` lo crea**, solo con
  umbrales de contexto: `WARNING` al 70% y `ERROR` al 90%, sin límites de plata.
- **Si ya tenía una política, no se toca.** Si le faltan los umbrales de contexto, `setup` lo dice.
  Para agregarlos sin cambiar nada más:

  ```powershell
  python .claude\harness\bin\desarrollo\dev-harness.py presupuesto --context-defaults
  ```

- **La Context Bar queda en `RELOAD_REQUIRED`** hasta que Claude Code corre el renderizador nuevo
  (`1.2.0`). El porcentaje aparece con la primera respuesta de Claude después de eso.

## 0.26.0 → 0.27.0

`-Update` alcanza. No hay que hacer nada a mano. Lo nuevo se ve al terminar:

- **El `-Update` revisa el conocimiento** contra el último canal que funcionó, y dice si quedó
  revisado o pendiente. Con un canal de Jira puede tardar lo que tarda Jira. Si no contesta, la
  instalación sigue.
- **La Context Bar pasa a mostrar colores** cuando `Ctx` o `Budget` están en alerta. Para verla
  como antes, sin colores, hay que definir `NO_COLOR` en el entorno.

## 0.25.0 → 0.26.0

`-Update` alcanza para que nada deje de andar: la URL y el usuario del `harness.integraciones.json`
viejo se siguen leyendo como capa de migración. Hay un paso manual por desarrollador, que se puede
hacer cuando convenga: **pasar la configuración al `.env`.** Se copian del bloque nuevo de
`.env.example` las variables que falten y se completan:

```dotenv
HARNESS_JIRA_ENABLED=true
JIRA_BASE_URL=https://tu-organizacion.atlassian.net
JIRA_USER=tu.email@buenosaires.gob.ar
HARNESS_GITLAB_ENABLED=true
GITLAB_BASE_URL=https://gitlab.tu-organizacion.gob.ar
```

Después, `setup` confirma que no falta nada:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py setup
```

🔴 **Un script que le respondía a las preguntas de `setup` deja de funcionar**: `setup` ya no lee de
stdin. Los valores tienen que venir del `.env` o del entorno del proceso.

## 0.24.0 → 0.25.0

`-Update` alcanza. Trae dos registros nuevos del proyecto en `reglas/`, uno para Vu9 y otro para Vu10,
que se instalan sin contenido. Llenarlos no es parte de la actualización.

## 0.23.0 → 0.24.0

`-Update` alcanza, y trae los extractos normativos al proyecto. Hay un paso manual por proyecto:
**aceptar las fuentes oficiales.** Ninguna se acepta sola, porque aceptarla es una decisión de la
persona responsable, y queda registrado con su nombre.

```powershell
# con los PDF que entregó el canal oficial del proyecto, en una carpeta:
python .claude\harness\bin\desarrollo\dev-harness.py fuentes --archivo <carpeta> --aceptar ES0902
# o directo desde la Ficha de Proyecto en Jira:
python .claude\harness\bin\desarrollo\dev-harness.py fuentes <TICKET> --aceptar ES0902
```

- **Quién acepta** sale de `usuario` en `harness.config.json`, o de `--por <persona>`.
- **Solo se acepta lo que coincide con lo vigente.** Si el canal del proyecto trae una versión
  anterior a la del harness, la fuente queda en `VERSION_REGRESSION`, y así tiene que quedar hasta
  que llegue la vigente. `--regresion` existe para el caso en que el proyecto decida lo contrario,
  y queda a la vista.
- **Después, el reporte de seguridad:** `seguridad <TAREA> --conocimiento --reporte`. Con ES0902
  aceptada ya no aparece B-001.

Con Jira Cloud, después del `-Update` conviene correr `estado`: dice por qué falta cada capacidad.

## 0.22.0 → 0.23.0

`-Update` alcanza. Lo único que cambia de forma es la salida de `dev-refutador`: ya no es una tabla
Markdown, sino un objeto JSON por unidad (`refutation-verdict/1.0`). Si en el proyecto había algo que
leía la tabla, tiene que pasar a `dev-harness.py refute <KEY> --summary` o `--status --json`.

Para usar la refutación atómica, escribí `.claude/refutaciones/<KEY>/scope.json` con los archivos de
cada unidad de trabajo, y después corré `refute <KEY> --compile`.

## 0.21.0 → 0.22.0

`-Update` alcanza, y después hay que **reiniciar la sesión de Claude Code** para que aparezca la
Context Bar. Hasta que la barra se dibuje por primera vez, la bienvenida y `harness` dicen
`REQUIERE REINICIO`.

🔴 **El `-Update` registra un `statusLine` en el `.claude/settings.json` del proyecto.** La
configuración del proyecto le gana a la del usuario, así que si tenías una barra de estado propia
en `~/.claude/settings.json`, en este proyecto deja de verse. Ese `statusLine` lleva la ruta absoluta
del proyecto y la de Python: si movés el proyecto de carpeta, corré `-Update` otra vez.

Cómo comprobarlo:
- `.\install.ps1 -Doctor -Project <proyecto>` muestra el estado de la barra y cuánto tarda en
  dibujarse.
- En la sesión siguiente, abajo de la terminal aparece una línea `HARNESS | …`, y
  `dev-harness.py harness` dice `Context Bar ACTIVA`.
- La barra es de la terminal de Claude Code. No se promete que aparezca en la extensión de VS Code.

## 0.20.0 → 0.21.0

`-Update` alcanza. No hay pasos manuales ni nada que borrar.

🔴 **En Windows sin Git Bash, hasta la 0.20.0 ningún hook corría**, tampoco el bloqueo de secretos:
el comando que quedaba en `.claude\settings.json` era sintaxis de bash, y los filtros no nombraban la
herramienta `PowerShell`. `settings.json` se regenera en cada `-Update`, así que el `-Update` deja el
comando nuevo (`"shell": "powershell"`, `& "$env:CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd" …`)
y su hash al día en `harness.lock.json`, sin tocar nada a mano.

Cómo comprobarlo:

- **Antes de abrir una sesión:** `.\install.ps1 -Doctor -Project C:\Work\GCBA\MiProyecto` corre los
  comandos registrados como los corre Claude Code y dice `los cuatro hooks registrados en settings.json
  responden`. Con el `settings.json` viejo dice que no corren.
- **En la sesión siguiente:** abrí Claude Code en el proyecto y usá cualquier herramienta. En la
  transcripción de esa sesión (el `.jsonl` de `~\.claude\projects\`) tienen que aparecer entradas
  `hook_success`; con el comando viejo solo aparecían `hook_non_blocking_error`.

La sesión siguiente al `-Update` también muestra, una sola vez, `Harness GCBA actualizado: 0.20.0 →
0.21.0 ✓` y la línea de estado. El estado vive en `.claude\harness.installation.json`, que el
`-Update` conserva y el `-Uninstall` borra. `dev-harness.py harness` lo muestra, y `setup` ya no dice
`HARNESS READY` fijo: dice el estado de ahora.

## 0.19.0 → 0.20.0

`-Update` alcanza. No hay pasos manuales ni nada que borrar. El subcomando nuevo,
`dev-harness.py seguridad`, llega con el `-Update`.

## 0.18.0 → 0.19.0

`-Update` alcanza para todo lo nuevo, y hay **un paso manual**: borrar las skills que dejaron de
existir.

🔴 **`-Update` copia y no borra.** Las ocho skills de `desarrollo` que esta versión reemplaza siguen
en el proyecto después de actualizar, al lado de las 27 nuevas:

```powershell
$viejas = 'dev-ambientes','dev-api','dev-identidad','dev-pantalla',
          'dev-repositorio','dev-seguridad','dev-tramites-asi','dev-versiones'
foreach ($s in $viejas) { Get-ChildItem "C:\Work\GCBA\MiProyecto\.claude\skills\$s" -ErrorAction SilentlyContinue }
```

Antes de borrar, mirá que no las hayas editado a mano. `dev-api` **sigue existiendo** con otro
contenido: esa no se borra, la pisa el `-Update`. Las otras siete se borran:

```powershell
foreach ($s in $viejas | Where-Object { $_ -ne 'dev-api' }) {
    Remove-Item "C:\Work\GCBA\MiProyecto\.claude\skills\$s" -Recurse -Force
}
```

Lo que aparece en un proyecto con `desarrollo` instalado: los ocho agentes `dev-*` nuevos, las 27
skills, los módulos nuevos de `orquestacion/` y `contabilidad/`, los 17 schemas nuevos y las
reglas del harness. `reglas/database-profiles.json` se instala **vacío**, a propósito: los
perfiles de base son del proyecto.

📌 **Los controles normativos no llegan todavía.** `controles/` no lo copia el instalador, así que
en un proyecto instalado los 31 controles figuran como `CONTROL_FILE_MISSING`. Está anotado en
`Pendientes/Fix-Harness/PENDIENTES-FH.md` y no es algo que se arregle a mano.

---

## 0.17.0 → 0.18.0

`-Update` alcanza. No hay paso manual, y todo lo que suma es aditivo.

Lo que aparece en un proyecto con `desarrollo` instalado: los módulos de `orquestacion/` bajo
`.claude\harness\bin\desarrollo\`, el contrato `orchestration-plan.schema.json` en
`.claude\harness\schemas\`, las reglas del harness en
`.claude\harness\reglas\desarrollo\` y el agente `dev-orchestrator`.

Para planificar una tarea que ya tiene contexto resuelto:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py plan GCBA-1234 --plantilla
python .claude\harness\bin\desarrollo\dev-harness.py plan GCBA-1234 --propuesta prop.json
```

El plan queda en `.claude\planes\GCBA-1234.json`, que **no se versiona** y que ni el `-Update`
ni el `-Uninstall` borran.

Tres claves nuevas que un proyecto ya instalado **no** va a ver, porque `harness.config.json` no se
reescribe nunca:

```json
"modelRouting":      { "perfiles": { "low_cost": "", "standard": "", "reasoning": "", "premium": "" } },
"consumptionPolicy": { "mode": "automatic", "autoApprove": ["low_cost", "standard"],
                       "requireHumanApproval": ["reasoning", "premium"],
                       "sessionBudget": { "premiumCallsAllowed": 0, "maxRetries": 3 } },
"llmRuntime":        { "provider": "", "version": "", "detected": false }
```

Sin ellas funciona igual, con esos mismos valores por defecto. **Vale la pena poner los perfiles**:
mientras estén vacíos, cada plan avisa que no hay modelo declarado para ningún tier, que es lo
honesto — el harness no sabe qué modelos existen en tu runtime y no los inventa.

🔴 **Si vas a tocar `consumptionPolicy`, mirá bien `autoApprove`.** Poner `premium` ahí hace que el
harness use el tier más caro sin preguntar y sin gastar presupuesto. Es una configuración
deliberada y está soportada; lo que no hay que hacer es ponerla creyendo que la compuerta sigue
puesta.

---

## 0.16.0 → 0.17.0

`-Update` alcanza. No hay paso manual, y todo lo que suma es aditivo.

Lo que aparece en un proyecto con `desarrollo` instalado: los módulos de `contexto/` bajo
`.claude\harness\bin\desarrollo\`, y el contrato `task-context.schema.json` en
`.claude\harness\schemas\`.

Para resolver el contexto de una tarea:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py contexto GCBA-1234
```

Queda en `.claude\contextos\GCBA-1234.json`, que **no se versiona** —es contenido de Jira— y
que ni el `-Update` ni el `-Uninstall` borran.

Tres claves nuevas que un proyecto ya instalado **no** va a ver, porque `harness.config.json` no se
reescribe nunca. Agregalas a mano si las necesitás:

```json
"fichaTipoDeIssue": "Ficha de Proyecto",
"campoCriteriosAceptacion": "",
"topeTextoDocumento": 20000
```

Sin ellas funciona igual: el tipo de ficha usa ese mismo default, el tope también, y el campo de
criterios vacío significa que los criterios salen vacíos con su hueco declarado — que es lo honesto
mientras nadie diga en qué campo de Jira viven.

Y una más, opcional, adentro del bloque `gitlab` de `.claude\harness.integraciones.json`:

```json
"gitlabProyecto": "grupo/proyecto"
```

Es el repositorio del proyecto. Sin eso se intenta sacar de la Ficha de Proyecto; si tampoco está
ahí, la sección técnica del contexto queda vacía con su hueco.

---

## 0.15.0 → 0.16.0

🔴 **Hay un paso manual, y es el único: mover tus base URL del `.env` al archivo de configuración.**

`-Update` pisa `.env.example` con la plantilla nueva —que ahora trae solo los tres `*_TOKEN`— y no
toca tu `.env`, así que las líneas `JIRA_BASE_URL=…`, `GITLAB_BASE_URL=…` y `OPENSHIFT_SERVER_URL=…`
que hayas completado siguen ahí y dejan de leerse. El harness no las lee del `.env` ni siquiera como
caída: leerlas sería mantener vivo el formato que este cambio viene a separar.

La forma corta, después del `-Update`:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py setup
```

Te va a preguntar la base URL y el usuario —los tokens, si ya estaban cargados, los reconoce y no te
los vuelve a pedir— y los escribe en `.claude\harness.integraciones.json`. Después borrá a mano de
tu `.env` las tres líneas `*_BASE_URL`, que ya no las usa nadie.

La forma larga, si preferís no correr el asistente: creá
`.claude\harness.integraciones.json` con la forma que tiene
`harnesses\desarrollo\integraciones.plantilla.json` y completá `baseUrl` y `usuario` vos.

Para ver cómo quedó todo:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py estado
```

Dos cosas más que trae el `-Update`, sin nada que hacer de tu lado:

- Los módulos nuevos aparecen en `.claude\harness\bin\desarrollo\`. Si no tenés instalado el
  harness `desarrollo`, no llega nada de esto
- El harness dejó de copiar bytecode al proyecto. Un `-Doctor` justo después del `-Update` puede
  reportar menos archivos que antes: es eso, y es lo correcto

---

## 0.14.0 → 0.15.0

`-Update` alcanza. No hay paso manual, pero sí dos archivos nuevos en la **raíz** del proyecto —no
adentro de `.claude/`— y solo si el proyecto tiene instalado el harness `desarrollo`:

- `.env.example` — la plantilla del harness. Se pisa en cada `-Update`, como cualquier otro
  contenido repartido
- `.env` — el tuyo. Se crea vacío la primera vez y **no se vuelve a tocar nunca**. Si ya lo tenías
  con tus tokens adentro, el `-Update` lo deja byte a byte igual

Ninguno de los dos entra al lockfile, así que tampoco los borra un `-Uninstall`. Completá `.env` en
tu máquina: Claude no puede leerlo —`permissions.deny` lo tapa— y el `.gitignore` del harness ya lo
excluye del repositorio.

Si tu proyecto ya excluía `.env` de otra forma, revisá que el bloque del harness en tu `.gitignore`
no haya quedado duplicado. No rompe nada, pero ensucia.

---

## 0.13.0 → 0.14.0

`-Update` alcanza. No hay paso manual.

Lo que suma, todo aditivo: el harness `desarrollo` gana un agente (`dev-iniciador-code`), un
quinto check (`dev-codebase-forma.py`) y una línea condicionada en `SessionStart` que sólo
aparece mientras `docs/codebase/indice.md` no exista en el proyecto. Un proyecto que ya tenía
`harness.config.json` no ve la clave nueva `rutaCodebase` sola —el instalador no pisa un archivo
existente—, pero el agente y el hook resuelven el mismo default sin ella, así que no hace falta
tocar nada a mano.

El primer recorrido en un proyecto instalado se dispara solo, avisado por `SessionStart`: corre
`dev-iniciador-code` una vez y deja `docs/codebase/` con las fichas, el índice, el mapa de nodos
(`mapa.html`) y el contrato (`project-context.json`). No consume nada de la ventana de la sesión
que lo pidió, más allá del aviso de una línea.

---

## 0.12.0 → 0.13.0

**Rompe.** Agrega un requisito y cambia el contrato de los checks. `-Update` alcanza para
recibir el harness nuevo, pero si escribiste un check propio hay un paso manual.

**Python ≥ 3.9 pasa a ser requisito de instalación**, no solo de ejecución: `install.ps1`
resuelve el intérprete y lo usa para leer las zonas del `CLAUDE.md`. `-Doctor` lo verifica y
falla con instrucciones si no está o es anterior a 3.9. Correr `-Doctor` antes que nada:

```powershell
.\install.ps1 -Doctor
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Update
```

**Si escribiste un check propio en `.ps1`, hay que portarlo.** Los cuatro hooks, los cinco
checks del harness y sus bibliotecas pasaron de PowerShell a Python. El contrato de un check
cambió de forma:

```powershell
param($Evento, $Proyecto, $Config)   ->   devuelve cero o mas strings
```
```python
def verificar(evento, proyecto, config) -> list[str]
```

Un `.ps1` en el directorio de checks deja de descubrirse: `lib/reglas.py` solo carga `.py`. El
detalle completo, con las trampas de Python que hay que conocer para escribirlo, está en
[docs/contrato-hooks.md](docs/contrato-hooks.md).

**Qué no cambia:** el catálogo de secretos, los umbrales, los mensajes y el veredicto de cada
regla — el port se hizo a paridad de comportamiento a propósito, defectos incluidos. Si un
check tuyo depende de algo del harness que no sea el contrato de arriba (una función de
`Zonas.psm1`, por ejemplo), mirá `lib/zonas.py`, que es su reemplazo directo.

**Lo que trae de arrastre:** `run-hook.sh` — el shim que faltaba. Una sesión de Claude Code
sobre WSL, macOS o Linux, contra un proyecto instalado desde Windows, ya arranca los hooks.
Necesita `python3` en el `PATH` de esa sesión.

---

## 0.8.0 → 0.9.0

`-Update` alcanza. Pero después de correrlo puede aparecer un aviso nuevo, y conviene saber
qué significa antes de verlo.

**Si tu `CLAUDE.md` es anterior al harness**, es probable que tenga zonas escritas con otro
nombre. El aviso se ve así:

```
AVISO CLAUDE.md: <!-- CACHÉ --> parece ser tu ZONA CACHE con otro nombre.
->    no se agregó ZONA CACHE para no dejarte dos. Renombrá el marcador
      —el de apertura y el de cierre— y corré -Update.
```

Se arregla en diez segundos: renombrás los dos marcadores y volvés a correr `-Update`. Hasta
que lo hagas, esa zona **no se mide** — pero tu contenido está intacto y nadie lo tocó.

**El otro aviso nuevo mide lo que quedó fuera de toda zona.** Si tenés un `CLAUDE.md` largo
escrito antes del harness, va a decirte cuántas líneas están afuera. No es urgente y no bloquea
nada: fuera de una zona el contenido sigue funcionando, lo que no hace es medirse ni purgarse.

**Clave nueva de configuración:** `techoFueraDeZonas` (12 por defecto). Como
`harness.config.json` no se toca nunca —ni en `-Update`— la clave no va a aparecer en un
proyecto ya instalado. No hace falta hacer nada: el valor por defecto viaja en código. Si querés
otro techo, agregala a mano a tu `harness.config.json`.

---

## Sin versión previa → 0.1.0

Nada que migrar. El repo todavía no instala nada.

---

## 0.6.0 → 0.7.0

`-Update` alcanza. No hay paso manual.

Lo que cambia de comportamiento: **`-Harness` pasa a ser aditivo.** Antes, instalar dejaba el
proyecto con exactamente los harness nombrados en el comando; ahora suma los que ya estaban
y lo anuncia. El cambio arregla el caso incremental —un repo con `analisis` que recibe su
primer código— que antes borraba el primer harness en silencio.

Si algún proyecto quedó en ese estado roto, el síntoma es que el bloque de `CLAUDE.md` no
tiene las reglas del harness que instalaste primero, y `.claude\skills\` o `.claude\agents\`
tienen archivos que el `harness.lock.json` no lista. Se arregla nombrando los dos:

```powershell
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis,desarrollo
```

Los archivos huérfanos que hayan quedado de antes **no los borra el instalador**: no están en
ningún inventario, así que no puede probar que son suyos. Se van con un `-Uninstall` seguido
de una instalación limpia, o a mano mirando qué sobra.

---

## Migraciones pendientes, para cuando corresponda

Cosas que quedaron **fuera de alcance** del harness pero que conviene hacer. No las ejecuta
el instalador: son decisiones de cada uno.

### Los subagentes globales sin `tools:` declaradas

En `~\.claude\agents\` hay 19 subagentes y solo 3 declaran `tools:`. Los otros 16 heredan
acceso total de escritura y ejecución sobre cualquier repo. `install.ps1 -Doctor` los lista.

La migración es agente por agente: agregarles `tools:` con lo mínimo que necesitan, y
`model:` cuando la tarea no justifica el modelo más caro. Los tres que ya están bien sirven
de molde.

### `~\.claude\` no tiene control de versiones

Los 19 agentes, las skills propias y el `CLAUDE.md` de usuario viven en un solo disco, sin
git y sin respaldo. Un `git init` ahí adentro es gratis y no rompe nada.

Es independiente de este harness, pero es la red de contención que hoy no existe.

### Los repos de proyecto sin `git`

Fuera de alcance por decisión. El harness lo detecta y lo avisa al abrir sesión, pero no
corre `git init` por su cuenta: crear un repositorio donde hay secretos y binarios pesados es
una decisión que hay que tomar mirando, no automatizar.
