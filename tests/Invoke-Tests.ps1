<#
.SYNOPSIS
    Corre los tests del harness.

.DESCRIPTION
    Sin dependencias: no hace falta Pester ni nada instalado. Carga cada archivo de
    tests\casos\ y acumula resultados.

    Sale con codigo 0 si pasa todo, 1 si falla algo. install.ps1 lo usa como compuerta.

.EXAMPLE
    .\tests\Invoke-Tests.ps1
    .\tests\Invoke-Tests.ps1 -Detallado
#>
[CmdletBinding()]
param(
    [switch] $Detallado
)

$ErrorActionPreference = 'Stop'

# UTF-8 en toda la cadena. Sin esto los tests de encoding pasan o fallan por razones
# equivocadas y no se puede confiar en el resultado.
$utf8 = New-Object System.Text.UTF8Encoding $false
try { [Console]::OutputEncoding = $utf8 } catch { }
$OutputEncoding = $utf8

$script:Raiz       = Split-Path -Parent $PSScriptRoot
$script:Resultados = New-Object System.Collections.ArrayList
$script:GrupoActual = '(sin grupo)'


function Set-Grupo {
    param([Parameter(Mandatory)][string] $Nombre)
    $script:GrupoActual = $Nombre
}


function Add-Resultado {
    param([string] $Nombre, [bool] $Ok, [string] $Detalle)
    [void] $script:Resultados.Add([pscustomobject]@{
        Grupo   = $script:GrupoActual
        Nombre  = $Nombre
        Ok      = $Ok
        Detalle = $Detalle
    })
}


function Assert-Igual {
    param([string] $Nombre, $Esperado, $Obtenido)
    $ok = ([string]$Esperado -ceq [string]$Obtenido)
    $detalle = ''
    if (-not $ok) { $detalle = "esperado <$Esperado> / obtenido <$Obtenido>" }
    Add-Resultado -Nombre $Nombre -Ok $ok -Detalle $detalle
}


function Assert-Contiene {
    param([string] $Nombre, [string] $Aguja, [string] $Pajar)
    $ok = ($Pajar -and $Pajar.Contains($Aguja))
    $detalle = ''
    if (-not $ok) { $detalle = "no contiene <$Aguja>; obtenido <$Pajar>" }
    Add-Resultado -Nombre $Nombre -Ok $ok -Detalle $detalle
}


function Assert-Vacio {
    param([string] $Nombre, [string] $Valor)
    $ok = [string]::IsNullOrEmpty($Valor)
    $detalle = ''
    if (-not $ok) { $detalle = "esperaba vacio; obtenido <$Valor>" }
    Add-Resultado -Nombre $Nombre -Ok $ok -Detalle $detalle
}


function Assert-Verdadero {
    param([string] $Nombre, [bool] $Condicion, [string] $Detalle = '')
    Add-Resultado -Nombre $Nombre -Ok $Condicion -Detalle $Detalle
}


function Invoke-HookEnProceso {
    <#
    .SYNOPSIS
        Corre un hook como proceso hijo, con el JSON por stdin. Como lo hace Claude Code.
    .DESCRIPTION
        Se usa System.Diagnostics.Process en vez de un pipe de PowerShell porque hay que
        controlar explicitamente el encoding de stdin y stdout. Un pipe comun usa la
        codepage ANSI y los tests de acentos darian falsos negativos.
    #>
    param(
        [Parameter(Mandatory)][string] $Script,
        [Parameter(Mandatory)][AllowEmptyString()][string] $JsonEntrada
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $psi.Arguments              = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $Script + '"'
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardInput  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding $false
    $psi.StandardErrorEncoding  = New-Object System.Text.UTF8Encoding $false

    $proceso = [System.Diagnostics.Process]::Start($psi)

    $escritor = New-Object System.IO.StreamWriter(
        $proceso.StandardInput.BaseStream,
        (New-Object System.Text.UTF8Encoding $false))
    $escritor.Write($JsonEntrada)
    $escritor.Flush()
    $escritor.Close()

    $salida = $proceso.StandardOutput.ReadToEnd()
    $errores = $proceso.StandardError.ReadToEnd()
    $proceso.WaitForExit()

    return [pscustomobject]@{
        Salida  = $salida
        Errores = $errores
        Codigo  = $proceso.ExitCode
    }
}


function Clear-MarcasHarness {
    <#
    .SYNOPSIS
        Borra las marcas de "ya avise de este error en esta sesion".
    .DESCRIPTION
        El aviso de hook roto se emite una sola vez por sesion y deja marca en disco.
        Un test que verifica ese aviso tiene que arrancar sin marcas previas, o pasa
        o falla segun lo que haya corrido antes.
    #>
    $dir = Join-Path $env:TEMP 'gcba-harness'
    if (Test-Path $dir) {
        Get-ChildItem $dir -Filter '*.avisado' -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}


function Get-Payload {
    param([Parameter(Mandatory)][string] $Nombre)
    $ruta = Join-Path $PSScriptRoot ('payloads\' + $Nombre)
    return [System.IO.File]::ReadAllText($ruta, (New-Object System.Text.UTF8Encoding $false))
}


function Get-Fixture {
    param([Parameter(Mandatory)][string] $Nombre)
    return (Join-Path $PSScriptRoot ('fixtures\' + $Nombre))
}


# ── Correr los casos ────────────────────────────────────────────────────────────

Write-Host ''
Write-Host 'gcba-harness - tests' -ForegroundColor Cyan
Write-Host ''

Clear-MarcasHarness

$casos = Get-ChildItem (Join-Path $PSScriptRoot 'casos') -Filter '*.ps1' -ErrorAction SilentlyContinue |
         Sort-Object Name

if (-not $casos) {
    Write-Host 'No hay casos en tests\casos\.' -ForegroundColor Yellow
    exit 1
}

foreach ($caso in $casos) {
    try {
        . $caso.FullName
    }
    catch {
        Set-Grupo $caso.BaseName
        Add-Resultado -Nombre 'el archivo de casos se pudo cargar' -Ok $false -Detalle $_.Exception.Message
    }
}


# ── Resumen ─────────────────────────────────────────────────────────────────────

$fallados = @($script:Resultados | Where-Object { -not $_.Ok })
$grupos   = $script:Resultados | Group-Object Grupo

foreach ($g in $grupos) {
    $malos = @($g.Group | Where-Object { -not $_.Ok })
    if ($malos.Count -eq 0) {
        Write-Host ('  OK    ' + $g.Name + '  (' + $g.Count + ')') -ForegroundColor Green
    } else {
        Write-Host ('  FALLA ' + $g.Name + '  (' + $malos.Count + '/' + $g.Count + ')') -ForegroundColor Red
    }

    if ($Detallado) {
        foreach ($r in $g.Group) {
            $marca = '        · '
            if ($r.Ok) { Write-Host ($marca + $r.Nombre) -ForegroundColor DarkGray }
            else       { Write-Host ($marca + $r.Nombre) -ForegroundColor Red }
        }
    }
}

if ($fallados.Count -gt 0) {
    Write-Host ''
    Write-Host 'Fallos:' -ForegroundColor Red
    foreach ($f in $fallados) {
        Write-Host ('  [' + $f.Grupo + '] ' + $f.Nombre) -ForegroundColor Red
        if ($f.Detalle) { Write-Host ('      ' + $f.Detalle) -ForegroundColor DarkYellow }
    }
}

Write-Host ''
$total = $script:Resultados.Count
$ok    = $total - $fallados.Count
if ($fallados.Count -eq 0) {
    Write-Host ("$ok/$total pasaron.") -ForegroundColor Green
    exit 0
} else {
    Write-Host ("$ok/$total pasaron. $($fallados.Count) fallaron.") -ForegroundColor Red
    exit 1
}
