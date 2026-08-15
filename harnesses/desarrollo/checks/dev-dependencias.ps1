<#
.SYNOPSIS
    Check: las dependencias se fijan en una version exacta (ES0901).

.DESCRIPTION
    ES0901 no deja elegir la version de una dependencia: se toma la homologada. Un rango
    -`^1.2.0`, `~1.2.0`, `>=1.2`, `*`- delega esa eleccion al gestor de paquetes, que va a
    resolver distinto en la maquina de quien desarrolla, en el pipeline y en produccion.

    Es de los pocos incumplimientos que no se nota nunca hasta que se nota mal: el build
    anda meses hasta que una version nueva entra sola y rompe algo en el ambiente donde
    duele. Por eso vale un aviso aunque el codigo funcione.

.NOTES
    Avisa, no bloquea. Lo unico que este harness bloquea son los secretos.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [AllowNull()] $Evento,
    [Parameter(Mandatory)] [AllowEmptyString()] [string] $Proyecto,
    [Parameter(Mandatory)] [AllowNull()] $Config
)

Import-Module (Join-Path $PSScriptRoot 'lib\Dev.psm1') -Force

$archivo = Get-ArchivoEscrito -Evento $Evento
if ($null -eq $archivo) { return }
if ($archivo.Nombre -notin @('package.json', 'composer.json')) { return }
if (Test-RutaGenerada -Ruta $archivo.Ruta) { return }

try { $json = $archivo.Texto | ConvertFrom-Json } catch { return }

# Un rango es cualquier cosa que no sea una version completa y unica. Se listan las
# formas y no se niega "lo que no es exacto": asi un valor raro -una ruta, un tag de
# git, un alias de workspace- no se reporta como si fuera un rango.
$formasDeRango = @(
    @{ Patron = '^\^';              Que = 'compatible (^)' },
    @{ Patron = '^~';               Que = 'aproximado (~)' },
    @{ Patron = '^\*$';             Que = 'cualquiera (*)' },
    @{ Patron = '^(>=|<=|>|<)';     Que = 'comparacion' },
    @{ Patron = '\|\|';             Que = 'alternativas (||)' },
    @{ Patron = ' - ';              Que = 'intervalo' },
    @{ Patron = '^\d+\.(x|\*)';     Que = 'comodin de menor' },
    @{ Patron = '^\d+\.\d+\.(x|\*)';Que = 'comodin de parche' }
)

$bloques = @('dependencies', 'devDependencies', 'peerDependencies', 'require', 'require-dev')
$sueltas = New-Object System.Collections.ArrayList

foreach ($b in $bloques) {
    if (-not $json.PSObject.Properties[$b]) { continue }
    $seccion = $json.$b
    if ($null -eq $seccion) { continue }

    foreach ($dep in $seccion.PSObject.Properties) {
        $valor = "$($dep.Value)"
        if (-not $valor) { continue }

        foreach ($f in $formasDeRango) {
            if ($valor -match $f.Patron) {
                [void] $sueltas.Add("$($dep.Name) $valor")
                break
            }
        }
    }
}

if ($sueltas.Count -eq 0) { return }

return @(
    "[ES0901] $($archivo.Nombre): $($sueltas.Count) dependencia(s) con rango en vez de version exacta — " +
    (Format-Lista -Items $sueltas) + ". " +
    "La version la fija el estandar, no el gestor de paquetes: un rango resuelve distinto en tu maquina, " +
    "en el pipeline y en produccion, y la diferencia aparece en el ambiente donde mas duele."
)
