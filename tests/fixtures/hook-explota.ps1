# Fixture de prueba: tira una excepcion a proposito.
# Verifica la garantia central del harness: un check roto no rompe la sesion.
# Tiene que salir con codigo 0 y emitir un systemMessage, no un stack trace.

Import-Module (Join-Path $PSScriptRoot '..\..\comun\hooks\lib\Hook.psm1') -Force

Invoke-Hook -EventName 'PostToolUse' -Cuerpo {
    param($e)
    throw 'falla deliberada del check de prueba'
}
