# Fixture de prueba: emite un bloqueo.
# Es la unica forma de salida que impide que la herramienta se ejecute, y en el
# harness real la usa exclusivamente la regla de secretos.

Import-Module (Join-Path $PSScriptRoot '..\..\comun\hooks\lib\Hook.psm1') -Force

Invoke-Hook -EventName 'PreToolUse' -Cuerpo {
    param($e)

    Write-HookDeny -EventName 'PreToolUse' `
                   -Motivo 'Literal con forma de client_secret. Usá una variable de entorno.'
}
