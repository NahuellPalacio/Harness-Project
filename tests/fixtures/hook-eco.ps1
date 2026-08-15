# Fixture de prueba: hace eco de la ruta y el contenido del evento.
# Sirve para verificar el camino completo stdin -> parseo -> additionalContext -> stdout.

Import-Module (Join-Path $PSScriptRoot '..\..\comun\hooks\lib\Hook.psm1') -Force

Invoke-Hook -EventName 'PostToolUse' -Cuerpo {
    param($e)

    $ruta      = Get-HookField -Evento $e -Ruta 'tool_input.file_path' -Default '(sin ruta)'
    $contenido = Get-HookField -Evento $e -Ruta 'tool_input.content'   -Default '(sin contenido)'

    Write-HookContext -EventName 'PostToolUse' -Texto "eco|$ruta|$contenido"
}
