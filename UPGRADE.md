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
