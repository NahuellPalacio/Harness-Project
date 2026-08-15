# PreToolUse — se dispara antes de cada llamada a herramienta que matchee.
#
# EXCLUSIVAMENTE el bloqueo de secretos. Nada mas entra aca.
#
# Tres razones para que sea asi:
#   1. Es la puerta: una sola cosa la cruza. Toda la complejidad va en PostToolUse.
#   2. Avisar desde aca no sirve: la salida en exito va a la transcripcion y el modelo
#      no la ve. Los avisos se entregan en PostToolUse.
#   3. Latencia: dispara antes de cada llamada. Cada regla de mas se paga siempre.
#
# Este hook cubre lo que `permissions.deny` no puede ver: el secreto que Claude esta por
# ESCRIBIR, que no vive en ninguna ruta prohibida. Los dos se instalan siempre y ninguno
# reemplaza al otro:
#
#     deny protege lo que no se debe leer.
#     este hook protege lo que no se debe escribir.

Import-Module (Join-Path $PSScriptRoot 'lib\Hook.psm1')     -Force
Import-Module (Join-Path $PSScriptRoot 'lib\Secretos.psm1') -Force

Invoke-Hook -EventName 'PreToolUse' -Cuerpo {
    param($e)

    $texto = Get-TextoDeHerramienta -Evento $e
    if ([string]::IsNullOrWhiteSpace($texto)) { return }

    $catalogo = Import-PatronesSecretos -Ruta (Join-Path $PSScriptRoot '..\reglas\secretos.patrones.json')
    $hallazgo = Find-Secreto -Texto $texto -Catalogo $catalogo
    if ($null -eq $hallazgo) { return }

    $mensaje = $hallazgo.Motivo + ' [' + $hallazgo.Id + ': ' + $hallazgo.Muestra + ']'

    if ($hallazgo.Confianza -eq 'alta') {
        Write-HookDeny -EventName 'PreToolUse' -Motivo $mensaje
    } else {
        # Ambiguo: decide la persona. Bloquear de mas es como se pierde un harness.
        Write-HookAsk -EventName 'PreToolUse' -Motivo $mensaje
    }
}
