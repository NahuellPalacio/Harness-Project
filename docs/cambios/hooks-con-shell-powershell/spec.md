# Los hooks se registran para PowerShell, y el instalador prueba el comando que registró

**Estado:** verificado y cerrado · **Fecha:** 24-09-2026 · **Origen:** reporte del Portal IGE del 24-09-2026

## Qué problema resuelve

En una máquina con Windows donde Claude Code no encuentra Git Bash, **ningún hook del harness corre
nunca**. Tampoco corre el bloqueo de secretos, que es lo único que el harness impide.

Lo relevó el Portal IGE el 24-09-2026 con gcba-harness 0.20.0, Claude Code 2.1.281, Windows 11 y
PowerShell 5.1. El backup de la 0.11.0 tiene el mismo comando. En las cuatro sesiones de ese proyecto
no hay un solo `hook_success`, y la sesión `6cf7240f` junta 67 `hook_non_blocking_error`:

```
SessionStart:startup                  1
UserPromptSubmit                     10
PreToolUse:Write / PostToolUse:Write  9 / 9
PreToolUse:Edit  / PostToolUse:Edit  19 / 19
PreToolUse:PowerShell                 0   (49 llamadas a PowerShell, ninguna paso por el hook)
```

El error es siempre el mismo:

```
+ "$CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd" session-start
+                                                    ~~~~~~~~~~~~~
Token 'session-start' inesperado en la expresión o la instrucción.
```

Tiene dos causas, las dos en `comun/settings/hooks.plantilla.json` y en `New-SettingsProyecto`:

1. **El comando está en sintaxis de bash.** Sin `args`, Claude Code corre el comando en Git Bash, o
   en PowerShell si no encuentra Git Bash. En PowerShell, una cadena entre comillas al principio de
   la línea es una expresión y no una invocación. Además, `$CLAUDE_PROJECT_DIR` es una variable
   vacía, porque la de entorno se escribe `$env:CLAUDE_PROJECT_DIR`.
2. **Los filtros no nombran la herramienta `PowerShell`.** Los dos dicen
   `Write|Edit|MultiEdit|NotebookEdit|Bash`, así que un comando de PowerShell no pasa por
   `pre-tool-use` ni por `post-tool-use`, aunque el comando del hook estuviera bien.

Y la razón de que esto viva desde la 0.11: `Test-HooksInstalados` lanza `run-hook.cmd` directo, con
`ProcessStartInfo`, y **nunca prueba el comando que quedó escrito en `settings.json`**. El
instalador verificaba el lanzador, no el registro.

## Qué queda afuera

- **El lado Python.** `texto_de_herramienta()` ya lee `tool_input.command`, que es el campo que usa
  la herramienta `PowerShell`, y ningún hook ni ningún check filtra por `tool_name`.
- **WSL, macOS y Linux.** `install.ps1` instala en Windows, y hoy `settings.json` tampoco nombra
  `run-hook.sh`. Registrar un comando de bash para cuando el proyecto se abre desde WSL es otro
  cambio.
- **La forma con `args` y sin shell.** Está documentada y sin probar. No se sabe si Claude Code lanza
  un `.cmd` sin shell. La forma con `"shell": "powershell"` sí está probada a mano.
- **Subir `requiereClaudeCode`.** Nadie sabe desde qué versión existe el campo `shell` de los hooks:
  la documentación no lo dice y el changelog disponible cubre de la 2.1.273 a la 2.1.281. Queda
  como definición pendiente en `PENDIENTES-FH.md`, sin inventar una versión.

## Las decisiones, y por qué

### El shell se fija, no se adivina

Cada hook se registra así:

```json
{
  "type": "command",
  "shell": "powershell",
  "command": "& \"$env:CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd\" session-start; exit $LASTEXITCODE"
}
```

- **Por qué se fija el shell.** El que usa Claude Code por defecto depende de la máquina: Git Bash si
  lo encuentra, PowerShell si no. PowerShell viene con cualquier Windows, y fijarlo saca esa
  variable del medio.
- **Por qué `$env:CLAUDE_PROJECT_DIR` y no `${CLAUDE_PROJECT_DIR}`.** La forma con llaves pega la
  ruta adentro del texto del comando, y PowerShell la interpreta como código: una ruta con `$`, con
  acento grave o con apóstrofo se rompe. Con la variable de entorno, la ruta llega como un valor y
  PowerShell no la interpreta.
- **Por qué `; exit $LASTEXITCODE`.** PowerShell 5.1 convierte cualquier código distinto de cero en
  1. Hoy el harness sale siempre con 0 y bloquea con JSON, pero así el código de salida se conserva
  si algún día hace falta.

### Los dos filtros de herramientas nombran `PowerShell`

`Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell`. Donde la herramienta no existe, esa alternativa
nunca matchea y no cuesta nada.

### El instalador prueba el comando registrado, no el lanzador

`Test-HooksInstalados` pasa a leer el `settings.json` que se acaba de escribir y corre, por cada uno
de los cuatro hooks, el `command` exacto que quedó registrado. Lo corre con
`powershell.exe -NoProfile -NonInteractive`, con `CLAUDE_PROJECT_DIR` en el entorno y el payload de
ejemplo por stdin. Si alguno sale con otro código que 0 o con una salida que no es JSON, la
instalación se revierte como hoy.

Se descartó seguir probando el lanzador y agregar la prueba del registro al lado: dos pruebas del
mismo camino, una que no mira lo que usa Claude Code, es exactamente lo que dejó pasar esto siete
versiones. `-Doctor` corre la misma verificación.

### `-Update` arregla los proyectos que ya están instalados

`settings.json` se regenera en cada `-Update`, y su hash ya está en el inventario del lockfile. Con
la plantilla corregida, un `-Update` deja el comando bien y el hash al día sin ningún paso manual.
`UPGRADE.md` lo dice, y dice también cómo comprobarlo en la sesión siguiente.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/settings/hooks.plantilla.json` | `"shell": "powershell"`, el comando con `&` y `$env:`, y `PowerShell` en los dos filtros |
| `install.ps1` | `New-SettingsProyecto` con la sintaxis nueva; `Test-HooksInstalados` y `-Doctor` prueban el comando registrado |
| `tests/casos/` (el caso del instalador que ya arma un proyecto) | Los escenarios de abajo |
| `UPGRADE.md` | Que `-Update` alcanza, y cómo comprobarlo |

## Escenarios verificables

- **E-01** — Los cuatro hooks del `settings.json` generado tienen `"shell": "powershell"` y un
  `command` que empieza con `& "$env:CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd"` y termina con
  `; exit $LASTEXITCODE`. Ninguno contiene `$CLAUDE_PROJECT_DIR` sin `env:` ni `${`.
  · rojo visto: si
- **E-02** — Los filtros de `PreToolUse` y de `PostToolUse` son exactamente
  `Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell`. · rojo visto: si
- **E-03** — Cada `command` registrado, corrido con `powershell.exe -NoProfile -NonInteractive`, con
  `CLAUDE_PROJECT_DIR` en el entorno y su payload por stdin, sale con 0 y con JSON válido o vacío.
  · rojo visto: si
- **E-04** — Lo mismo con un proyecto cuya ruta tiene espacios, un apóstrofo y un `$`.
  · rojo visto: si
- **E-05** — El comando viejo (`"$CLAUDE_PROJECT_DIR/…/run-hook.cmd" session-start`), corrido de la
  misma manera, falla. El test lo afirma, para que la prueba de E-03 demuestre que distingue.
  · rojo visto: si
- **E-06** — Si el `command` registrado no corre (el test escribe un `settings.json` con el comando
  viejo antes de la verificación), la instalación se revierte y no deja ni `settings.json`, ni el
  lockfile, ni hooks. · rojo visto: si
- **E-07** — `Test-HooksInstalados` lee el `command` del `settings.json` escrito, y no lanza
  `run-hook.cmd` por su cuenta. Un `settings.json` roto con un `run-hook.cmd` sano hace fallar la
  verificación. · rojo visto: si
- **E-08** — `-Doctor` sobre un proyecto con el `settings.json` viejo informa que los hooks
  registrados no corren. Sobre uno con el nuevo, no informa nada. · rojo visto: si
- **E-09** — Un `-Update` sobre un proyecto instalado con la plantilla vieja deja el `settings.json`
  nuevo, y su hash en `harness.lock.json` coincide con el archivo. · rojo visto: si
- **E-10** — Un evento de `PreToolUse` con `tool_name: "PowerShell"` y un secreto de confianza alta
  en `tool_input.command`, pasado por el comando registrado, sale denegado. · rojo visto: si
- **E-11** — La salida UTF-8 con tildes de `session-start` llega igual byte a byte por el comando
  registrado que por el lanzador directo. · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en el caso del instalador. Queda afuera lo único que la suite
no puede hacer: abrir una sesión de Claude Code con el `settings.json` nuevo y ver `hook_success` en
la transcripción. Eso se mira con los ojos después del `-Update`, con el procedimiento del reporte, y
se anota en la verificación.

## Riesgos conocidos

- **Que Claude Code 2.1.281 respete `"shell": "powershell"` está documentado, pero no probado.** Si
  lo ignora, en una máquina con Git Bash el comando de PowerShell corre en bash y falla al revés.
  Por eso la comprobación en una sesión real es parte del cierre.
- **Arrancar `powershell.exe` suma latencia a cada hook**, más que Git Bash. Se mide con `-Doctor`,
  y si pasa del presupuesto de `pre-tool-use` queda a la vista, sin mover el umbral.
- **Un proyecto instalado y abierto desde WSL** sigue sin hooks, igual que hoy.
