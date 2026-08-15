<#
.SYNOPSIS
    Carga y ejecucion de los checks que aportan comun y los harness instalados.

.DESCRIPTION
    Los hooks son cuatro y son infraestructura. Los checks son N y son reglas. La
    separacion existe para que agregar una regla no pueda romper el manejo de stdin, el
    encoding ni el control de errores.

    Contrato de un check: un .ps1 con param(-Evento, -Proyecto, -Config) que devuelve
    cero o mas strings. Cada string es un hallazgo.
#>

Set-StrictMode -Version 2.0

# Presupuesto de salida. PostToolUse corre despues de cada escritura de cada sesion:
# una tanda larga de avisos deja de leerse y el harness se vuelve ruido de fondo.
$script:MaxHallazgos = 8


function Get-ConfigProyecto {
    <#
    .SYNOPSIS
        Lee harness.config.json del proyecto. Devuelve $null si no hay.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Proyecto)

    if (-not $Proyecto) { return $null }
    $ruta = Join-Path $Proyecto '.claude\harness.config.json'
    if (-not (Test-Path $ruta)) { return $null }

    try {
        return ([System.IO.File]::ReadAllText($ruta, (New-Object System.Text.UTF8Encoding $false)) | ConvertFrom-Json)
    } catch { return $null }
}


function Invoke-Checks {
    <#
    .SYNOPSIS
        Corre todos los checks instalados y devuelve los hallazgos juntos.
    .DESCRIPTION
        Un check que truena no puede tumbar a los demas ni a la sesion: se lo saltea y
        se sigue. Es la misma garantia que da Invoke-Hook, un nivel mas adentro.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowNull()] $Evento,
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $DirChecks,
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Proyecto,
        [Parameter(Mandatory)] [AllowNull()] $Config
    )

    $hallazgos = New-Object System.Collections.ArrayList
    if (-not $DirChecks -or -not (Test-Path $DirChecks)) { return ,$hallazgos }

    $checks = @(Get-ChildItem $DirChecks -Recurse -File -Filter '*.ps1' -ErrorAction SilentlyContinue |
                Sort-Object FullName)

    foreach ($c in $checks) {
        try {
            $salida = & $c.FullName -Evento $Evento -Proyecto $Proyecto -Config $Config
            foreach ($s in @($salida)) {
                if ($s -and ("$s").Trim()) { [void] $hallazgos.Add(("$s").Trim()) }
            }
        }
        catch {
            # Un check roto se saltea en silencio. Reportarlo en cada escritura seria
            # peor que el problema que quiso evitar.
        }

        if ($hallazgos.Count -ge $script:MaxHallazgos) { break }
    }

    if ($hallazgos.Count -gt $script:MaxHallazgos) {
        $recorte = $hallazgos.GetRange(0, $script:MaxHallazgos)
        return ,$recorte
    }
    return ,$hallazgos
}


Export-ModuleMember -Function @('Get-ConfigProyecto', 'Invoke-Checks')
