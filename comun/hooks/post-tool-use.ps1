# PostToolUse — se dispara despues de una escritura o un comando.
#
# El caballo de batalla: corre los checks de comun y de los harness instalados contra lo
# que se acaba de escribir, y devuelve los hallazgos como additionalContext. Claude los
# lee y corrige en el turno siguiente.
#
# Es el UNICO lugar donde el harness avisa, porque es el unico evento portatil en que
# additionalContext llega de verdad al modelo: en PreToolUse la salida en exito va a la
# transcripcion y nadie la ve.
#
# Si no hay hallazgos: silencio. El costo tiene que ser proporcional a los problemas
# reales, no al tamano del reglamento.

Import-Module (Join-Path $PSScriptRoot 'lib\Hook.psm1')   -Force
Import-Module (Join-Path $PSScriptRoot 'lib\Reglas.psm1') -Force

Invoke-Hook -EventName 'PostToolUse' -Cuerpo {
    param($e)

    $proyecto = Get-HookField -Evento $e -Ruta 'cwd' -Default ''
    if (-not $proyecto) { return }

    $dirChecks = Join-Path $PSScriptRoot '..\checks'
    if (-not (Test-Path $dirChecks)) { return }

    $config    = Get-ConfigProyecto -Proyecto $proyecto
    $hallazgos = Invoke-Checks -Evento $e -DirChecks $dirChecks -Proyecto $proyecto -Config $config

    if ($hallazgos.Count -eq 0) { return }

    Write-HookContext -EventName 'PostToolUse' -Texto ($hallazgos -join "`n")
}
