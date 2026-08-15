# Tests unitarios de comun\hooks\lib\Hook.psm1, sin subprocesos.

Set-Grupo 'Hook.psm1 — funciones'

Import-Module (Join-Path $script:Raiz 'comun\hooks\lib\Hook.psm1') -Force

$evento = @'
{
  "session_id": "s1",
  "cwd": "C:\\Work\\GCBA\\IGE",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "docs\\hu.md", "content": "hola" }
}
'@ | ConvertFrom-Json


# ── Get-HookField ───────────────────────────────────────────────────────────────
# Es la funcion que mas se usa y la que evita que un check explote por una propiedad
# ausente. Los eventos de Claude Code cambian de forma segun la herramienta.

Assert-Igual 'lee una propiedad de primer nivel' `
    'Write' (Get-HookField -Evento $evento -Ruta 'tool_name')

Assert-Igual 'lee una propiedad anidada' `
    'docs\hu.md' (Get-HookField -Evento $evento -Ruta 'tool_input.file_path')

Assert-Igual 'devuelve el default si la propiedad no existe' `
    'nada' (Get-HookField -Evento $evento -Ruta 'tool_input.no_existe' -Default 'nada')

Assert-Igual 'devuelve el default si el camino se corta a mitad' `
    'nada' (Get-HookField -Evento $evento -Ruta 'no_existe.tampoco.esto' -Default 'nada')

Assert-Igual 'devuelve el default ante un evento nulo' `
    'nada' (Get-HookField -Evento $null -Ruta 'tool_name' -Default 'nada')


# ── Forma de la salida ──────────────────────────────────────────────────────────
# Las tres formas validas, y solo esas tres. Se capturan redirigiendo la consola.

function Get-SalidaDe {
    param([scriptblock] $Bloque)
    $sb  = New-Object System.Text.StringBuilder
    $sw  = New-Object System.IO.StringWriter($sb)
    $ant = [Console]::Out
    try {
        [Console]::SetOut($sw)
        & $Bloque
    }
    finally {
        [Console]::SetOut($ant)
        $sw.Dispose()
    }
    return $sb.ToString()
}

$salidaAviso = Get-SalidaDe { Write-HookContext -EventName 'PostToolUse' -Texto 'ojo con esto' }
$aviso = $salidaAviso | ConvertFrom-Json

Assert-Igual 'el aviso declara su evento' `
    'PostToolUse' $aviso.hookSpecificOutput.hookEventName
Assert-Igual 'el aviso lleva el texto en additionalContext' `
    'ojo con esto' $aviso.hookSpecificOutput.additionalContext

$salidaVacia = Get-SalidaDe { Write-HookContext -EventName 'PostToolUse' -Texto '   ' }
Assert-Vacio 'un texto en blanco no emite nada' $salidaVacia

$salidaDeny = Get-SalidaDe { Write-HookDeny -EventName 'PreToolUse' -Motivo 'usá una variable de entorno' }
$deny = $salidaDeny | ConvertFrom-Json

Assert-Igual 'el bloqueo declara permissionDecision deny' `
    'deny' $deny.hookSpecificOutput.permissionDecision
Assert-Igual 'el bloqueo conserva el motivo con acentos' `
    'usá una variable de entorno' $deny.hookSpecificOutput.permissionDecisionReason


# ── Profundidad del JSON ────────────────────────────────────────────────────────
# ConvertTo-Json en PS 5.1 trunca a profundidad 2 por defecto, en silencio. Si el
# modulo perdiera el -Depth 10, este test lo agarra.

$salidaProfunda = Get-SalidaDe {
    Write-HookContext -EventName 'PostToolUse' -Texto 'nivel de prueba'
}
Assert-Contiene 'la salida no queda truncada por profundidad' `
    'additionalContext' $salidaProfunda
