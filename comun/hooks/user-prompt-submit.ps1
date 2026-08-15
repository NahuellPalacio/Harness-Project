# UserPromptSubmit — se dispara con cada mensaje del usuario.
#
# Un solo trabajo: RUTEO. Si lo que se pidio corresponde a una skill instalada, lo dice
# en una linea. Si no matchea nada, silencio absoluto.
#
# Presupuesto: 0 o 1 linea. Corre en cada mensaje: cualquier cosa de mas se paga en
# todos los turnos de todas las sesiones.
#
# Un secreto que el humano tipeo se AVISA, no se bloquea. Bloquear lo que alguien
# escribio a mano es la via mas rapida a que desinstalen el harness.

Import-Module (Join-Path $PSScriptRoot 'lib\Hook.psm1') -Force

Invoke-Hook -EventName 'UserPromptSubmit' -Cuerpo {
    param($e)

    $prompt = Get-HookField -Evento $e -Ruta 'prompt' -Default ''
    if ([string]::IsNullOrWhiteSpace($prompt)) { return }

    # El ruteo por disparadores de skill se agrega cuando existan las skills.
    # Hasta entonces este hook calla, que es exactamente lo que tiene que hacer
    # cuando no tiene nada util que decir.
}
