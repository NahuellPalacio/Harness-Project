<#
.SYNOPSIS
    Check: las zonas del CLAUDE.md y sus techos.

.DESCRIPTION
    Corre despues de cada escritura sobre el CLAUDE.md del proyecto. Avisa —nunca
    bloquea— cuando una zona paso su techo o cuando falta alguna.

    Sin esto, "mantener chico el CLAUDE.md" es una intencion que dura hasta la primera
    semana ocupada.

.NOTES
    Contrato de un check: recibe -Evento, -Proyecto y -Config, y devuelve cero o mas
    strings. Cada string es un hallazgo que el hook entrega como additionalContext.
    Silencio cuando esta todo bien: el costo tiene que ser proporcional a los problemas
    reales, no al tamano del reglamento.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [AllowNull()] $Evento,
    [Parameter(Mandatory)] [AllowEmptyString()] [string] $Proyecto,
    [Parameter(Mandatory)] [AllowNull()] $Config
)

Import-Module (Join-Path $PSScriptRoot '..\hooks\lib\Zonas.psm1') -Force

$ruta = Get-HookField -Evento $Evento -Ruta 'tool_input.file_path' -Default ''
if (-not $ruta) { return }
if ((Split-Path $ruta -Leaf) -ne 'CLAUDE.md') { return }
if (-not (Test-Path $ruta)) { return }

$texto = [System.IO.File]::ReadAllText($ruta, (New-Object System.Text.UTF8Encoding $false))
$medicion = Measure-Zonas -Texto $texto -Config $Config

# Un CLAUDE.md sin ninguna zona es uno que el harness todavia no organizo. No es un
# error del turno: no se avisa nada.
$conZonas = @($medicion | Where-Object { $_.Existe })
if ($conZonas.Count -eq 0) { return }

$hallazgos = New-Object System.Collections.ArrayList

# Una zona escrita con otro nombre. Si nadie avisa, el proximo -Update agrega la
# canonica al lado y quedan dos: una con el contenido y otra vacia, que es la que se
# mide. Paso al instalar sobre el CLAUDE.md del IGE, y paso en silencio.
$raras = Find-ZonasNoReconocidas -Texto $texto
$conOtroNombre = @($raras | Where-Object { $_.Parecida } | Select-Object -ExpandProperty Parecida)

foreach ($r in $raras) {
    if ($r.Parecida) {
        [void] $hallazgos.Add(
            "[CLAUDE.md] el marcador '$($r.Marcador)' parece ser $($r.Parecida) escrita con otro nombre. " +
            "Mientras se llame asi el harness no la mide. " +
            "Renombrar el marcador de apertura y el de cierre, y correr install.ps1 -Update."
        )
    }
}

# Lo que queda fuera de toda zona no lo mide nadie: no se purga, no baja al
# conocimiento del proyecto y no cuenta contra ningun techo. Un CLAUDE.md de
# trescientas lineas sin marcadores pasa la medicion entera sin una palabra.
$techoFuera = 12
if ($null -ne $Config -and $Config.PSObject.Properties['techoFueraDeZonas']) {
    $techoFuera = [int]$Config.techoFueraDeZonas
}
$fuera = Measure-FueraDeZonas -Texto $texto
if ($techoFuera -gt 0 -and $fuera.Lineas -gt $techoFuera) {
    $muestra = ''
    if ($fuera.Muestra.Count -gt 0) { $muestra = " Empieza en: `"$($fuera.Muestra[0])`"." }
    [void] $hallazgos.Add(
        "[CLAUDE.md] hay $($fuera.Lineas) lineas fuera de toda zona y el techo es $techoFuera.$muestra " +
        "Fuera de una zona no se mide, no se purga y no baja al conocimiento del proyecto: " +
        "mover ese contenido a la zona que le corresponda, o a una skill si no se necesita en cada turno."
    )
}

foreach ($z in ($medicion | Where-Object { $_.Excedida })) {
    [void] $hallazgos.Add(
        "[CLAUDE.md] $($z.Nombre) tiene $($z.Lineas) lineas y su techo es $($z.Techo). " +
        "Este archivo ocupa ventana de contexto toda la sesion: lo que no se necesita en cada turno va en una skill."
    )
}

# Una zona que existe con otro nombre NO esta faltando: esta mal nombrada, y eso ya se
# aviso arriba. Decir las dos cosas manda a correr un -Update que a proposito no la va
# a reponer, y un consejo que no funciona gasta la credibilidad de todos los demas.
$faltantes = @($medicion | Where-Object { -not $_.Existe -and $conOtroNombre -notcontains $_.Nombre })
if ($faltantes.Count -gt 0 -and $conZonas.Count -gt 0) {
    [void] $hallazgos.Add(
        "[CLAUDE.md] falta la zona " + (($faltantes | Select-Object -ExpandProperty Nombre) -join ', ') + ". " +
        "Corre install.ps1 -Update para reponerla."
    )
}

# La cache llena es informacion, no un problema: significa que hay conocimiento sin bajar.
$cache = $medicion | Where-Object { $_.Nombre -eq 'ZONA CACHE' }
if ($cache -and $cache.Existe -and $cache.Techo -gt 0 -and $cache.Lineas -gt ($cache.Techo * 0.75) -and -not $cache.Excedida) {
    [void] $hallazgos.Add(
        "[CLAUDE.md] la cache va por $($cache.Lineas) de $($cache.Techo) lineas. " +
        "Corresponde correr flush-memoria para bajarla al conocimiento del proyecto."
    )
}

return $hallazgos
