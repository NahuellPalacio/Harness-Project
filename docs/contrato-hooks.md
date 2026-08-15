# Contrato de hooks

Todo lo que hay que saber para escribir un hook del harness. Verificado punta a punta
por `tests\casos\02-hook-contrato.ps1`.

## Entrada

Claude Code invoca el hook como un proceso del sistema y le pasa **un objeto JSON por
stdin**. Campos comunes a todos los eventos:

```jsonc
{
  "session_id": "...",
  "transcript_path": "C:\\...\\transcript.jsonl",
  "cwd": "C:\\Work\\GCBA\\IGE",
  "hook_event_name": "PostToolUse"
}
```

Y según el evento:

| Evento | Campos propios |
|---|---|
| `SessionStart` | `source` — `startup` / `resume` / `clear` / `compact` |
| `UserPromptSubmit` | `prompt` |
| `PreToolUse` | `tool_name`, `tool_input` |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_response` |

**La forma de `tool_input` cambia según la herramienta.** `Write` trae `file_path` y
`content`; `Edit` trae `old_string` y `new_string`; `Bash` trae `command`. Por eso nunca
se accede a una propiedad directamente: se usa `Get-HookField`, que devuelve un default
en vez de explotar.

Hay payloads reales de cada evento en `tests\payloads\`.

## Salida — tres formas, y solo tres

### 1. Silencio

El caso normal, y el que hay que optimizar. Sin hallazgos, el hook no escribe nada y
sale con código 0. Costo en contexto: cero.

Esto importa más de lo que parece: `PostToolUse` corre después de **cada** escritura de
**cada** sesión. Un hook que siempre dice algo se vuelve ruido de fondo que nadie lee.

### 2. Avisar

```powershell
Write-HookContext -EventName 'PostToolUse' -Texto '[ES0903] `/api/usuario` usa singular y no versiona. Debe ser `/api/v1/users`.'
```

Inyecta el texto en el contexto de Claude sin interrumpir nada. Claude lo lee y corrige
en el turno siguiente. **Es la forma normal de comunicar un incumplimiento.**

> ⚠️ **Solo funciona en `PostToolUse`, `UserPromptSubmit` y `SessionStart`.** En
> `PreToolUse`, la salida en caso de éxito va a la transcripción y el modelo no la ve.
> Por eso **todos los avisos del harness se entregan en `PostToolUse`**, aunque el
> problema se pudiera detectar antes.

### 3. Bloquear

```powershell
Write-HookDeny -EventName 'PreToolUse' -Motivo 'Literal con forma de client_secret. Usá una variable de entorno.'
```

Impide que la herramienta se ejecute. **Reservado exclusivamente a la regla de
secretos.** Ninguna otra regla del harness bloquea.

El motivo se le muestra a Claude, así que tiene que decir **qué hacer**, no qué se
impidió. `usá una variable de entorno` sirve; `operación denegada` no.

## Cómo se escribe un hook

```powershell
Import-Module (Join-Path $PSScriptRoot 'lib\Hook.psm1') -Force

Invoke-Hook -EventName 'PostToolUse' -Cuerpo {
    param($e)

    $ruta = Get-HookField -Evento $e -Ruta 'tool_input.file_path' -Default ''
    if ($ruta -notlike '*.md') { return }        # salir temprano es gratis

    # ... verificar algo ...

    if ($hayHallazgo) {
        Write-HookContext -EventName 'PostToolUse' -Texto $mensaje
    }
}
```

`Invoke-Hook` se encarga de leer stdin, forzar el encoding, atrapar cualquier excepción
y garantizar salida con código 0. **Un check roto nunca rompe la sesión de nadie**: se
reporta una vez con `systemMessage` y se calla hasta el próximo reinicio.

## Portabilidad — tres capas

```
.claude\settings.json          → "$CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd" post-tool-use
                                  nunca contiene una ruta absoluta
.claude\harness\run-hook.cmd   → resuelve el intérprete de ESTA máquina
                                  único artefacto dependiente del equipo. Gitignoreado
.claude\harness\hooks\*.ps1    → la lógica, PowerShell 5.1 estricto
```

El shim completo:

```bat
@echo off
"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive ^
  -ExecutionPolicy Bypass -File "%~dp0hooks\%1.ps1"
```

## Las cinco trampas

Las tres primeras están verificadas por tests porque ya rompieron algo durante la
construcción.

### 1. No toques `[Console]::InputEncoding` ✅ *verificado*

Asignar `InputEncoding` **recrea el objeto `Console.In`**. Cuando stdin viene redirigido
desde una tubería —o sea, siempre, en un hook— esa recreación corrompe la lectura y
`ConvertFrom-Json` falla con *"Primitivo JSON no válido"*.

La entrada se lee con su propio `StreamReader` UTF-8 sobre `OpenStandardInput()`, sin
tocar el estado global. Ya está resuelto adentro de `Read-HookEvent`.

### 2. Los `.ps1` con acentos van en UTF-8 **con BOM** ✅ *verificado*

PowerShell 5.1 lee un `.ps1` sin BOM usando la codepage ANSI. Un archivo en UTF-8 sin
BOM que diga `definición` se carga como `definiciÃ³n`.

Lo insidioso: **un test escrito en ese archivo compara una cadena corrupta contra otra
corrupta de la misma forma, y pasa.** El problema queda tapado por un test en verde.
Pasó exactamente eso acá.

- `tests\casos\00-encoding-fuentes.ps1` lo detecta.
- `scripts\Repair-EncodingFuentes.ps1` lo arregla.
- Un fuente sin caracteres no ASCII no necesita BOM. Las dos opciones son válidas.

### 3. `-NoProfile` no es opcional ✅ *verificado por diseño en el shim*

Si el `$PROFILE` de quien instala imprime un banner, ese texto se mezcla con el JSON de
stdout y el hook falla de una forma que nadie asocia a su perfil de PowerShell. Es el
bug número uno de hooks en Windows.

`-NonInteractive` por la misma razón: cualquier prompt cuelga la sesión de Claude entera.

### 4. `ConvertTo-Json -Depth 10`, siempre explícito

El default de PS 5.1 es 2 y **trunca objetos anidados en silencio**. `Write-HookJson` ya
lo hace; si escribís JSON a mano en algún lado, acordate.

### 5. PowerShell 5.1, no 7

En estas máquinas no hay `pwsh`. No se puede usar operador ternario, `??`, `?.`,
`ConvertFrom-Json -AsHashtable`, ni `Get-Content -Raw -TotalCount` juntos.

Escribir en 5.1 estricto además mantiene los mismos `.ps1` corriendo bajo `pwsh` en
Linux el día que haga falta.

## Correr los tests

```powershell
.\tests\Invoke-Tests.ps1
.\tests\Invoke-Tests.ps1 -Detallado
```

Sale con código 0 si pasa todo, 1 si falla algo. No necesita Pester ni nada instalado.

`install.ps1` lo usa como compuerta: **si los hooks no responden bien, la instalación
falla y revierte.** Un hook roto es peor que ningún hook, porque falla en silencio.
