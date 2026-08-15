# Fixture de prueba: el caso normal, en que no hay nada que decir.
# stdout tiene que quedar COMPLETAMENTE vacio: cualquier byte de mas cuesta contexto
# en cada llamada a herramienta de cada sesion.

Import-Module (Join-Path $PSScriptRoot '..\..\comun\hooks\lib\Hook.psm1') -Force

Invoke-Hook -EventName 'PostToolUse' -Cuerpo {
    param($e)
    # sin hallazgos: no se emite nada
}
