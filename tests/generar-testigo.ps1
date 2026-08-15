<#
.SYNOPSIS
    El testigo: corre la implementacion PowerShell y guarda sus veredictos.

.DESCRIPTION
    Se corre UNA vez, antes de portar nada a Python. Su salida -tres JSON bajo
    tests\fixtures\- es el testigo contra el que se compara la implementacion nueva.
    Volver a correrlo despues de portar no tiene sentido: en ese punto ya no queda
    la implementacion PowerShell "de hoy" contra la que comparar.

    Tres capturas, cada una sobre una pieza del harness que hoy solo existe en
    PowerShell:

      1. Secretos   -> Find-Secreto sobre el corpus de tests\fixtures\corpus-secretos.txt.
      2. Checks     -> Invoke-Checks sobre un proyecto de fixture, un caso por check.
      3. Zonas      -> Measure-Zonas / Measure-FueraDeZonas sobre claude-md-de-prueba.md.
#>
param(
    [string] $SalidaSecretos = (Join-Path $PSScriptRoot 'fixtures\paridad-secretos.json'),
    [string] $SalidaChecks   = (Join-Path $PSScriptRoot 'fixtures\paridad-checks.json'),
    [string] $SalidaZonas    = (Join-Path $PSScriptRoot 'fixtures\paridad-zonas.json'),
    # Por si el proceso completo tarda: permite correr una sola captura por vez.
    [ValidateSet('todos', 'secretos', 'checks', 'zonas')]
    [string] $Solo = 'todos'
)

$ErrorActionPreference = 'Stop'
$raiz = Resolve-Path (Join-Path $PSScriptRoot '..')

Import-Module (Join-Path $raiz 'comun\hooks\lib\Hook.psm1')     -Force
Import-Module (Join-Path $raiz 'comun\hooks\lib\Secretos.psm1') -Force
Import-Module (Join-Path $raiz 'comun\hooks\lib\Reglas.psm1')   -Force
Import-Module (Join-Path $raiz 'comun\hooks\lib\Zonas.psm1')    -Force

$version = (Get-Content (Join-Path $raiz 'VERSION') -Raw).Trim()
$u8      = New-Object System.Text.UTF8Encoding $false

function ConvertTo-JsonTexto {
    <#
    .SYNOPSIS
        Escapa un string para JSON. Uso interno de ConvertTo-JsonManual.
    #>
    param([AllowNull()] [string] $S)
    if ($null -eq $S) { return '""' }
    $sb = New-Object System.Text.StringBuilder
    [void] $sb.Append('"')
    foreach ($ch in $S.ToCharArray()) {
        switch ($ch) {
            '"'  { [void] $sb.Append('\"'); continue }
            '\'  { [void] $sb.Append('\\'); continue }
            "`n" { [void] $sb.Append('\n'); continue }
            "`r" { [void] $sb.Append('\r'); continue }
            "`t" { [void] $sb.Append('\t'); continue }
            default {
                if ([int] $ch -lt 0x20) { [void] $sb.Append('\u{0:x4}' -f [int] $ch) }
                else { [void] $sb.Append($ch) }
            }
        }
    }
    [void] $sb.Append('"')
    return $sb.ToString()
}

function ConvertTo-JsonManual {
    <#
    .SYNOPSIS
        Reemplazo casero de ConvertTo-Json, con indentacion a mano.
    .DESCRIPTION
        ConvertTo-Json se queda colgado en esta maquina apenas el arbol incluye las
        cadenas reales del corpus de secretos -aun sin pasar por Find-Secreto-, y lo
        hace de forma reproducible: se probo en aislamiento, con la mitad del corpus
        y con la otra mitad, y las dos mitades se cuelgan por separado, asi que no es
        una linea puntual. Un serializador propio, del tamano exacto que este script
        necesita (string, bool, entero, diccionario ordenado, array, PSCustomObject,
        $null), evita el cmdlet entero en vez de perseguir la causa.
    #>
    param([AllowNull()] $Valor, [int] $Indent = 0)

    $pad   = '  ' * $Indent
    $padIn = '  ' * ($Indent + 1)

    if ($null -eq $Valor)                              { return 'null' }
    if ($Valor -is [bool])                              { return $(if ($Valor) { 'true' } else { 'false' }) }
    if ($Valor -is [int] -or $Valor -is [long] -or $Valor -is [double]) { return "$Valor" }
    if ($Valor -is [string])                             { return (ConvertTo-JsonTexto $Valor) }

    if ($Valor -is [System.Collections.Specialized.OrderedDictionary] -or $Valor -is [hashtable]) {
        $pares = @(foreach ($k in $Valor.Keys) {
            $padIn + (ConvertTo-JsonTexto "$k") + ': ' + (ConvertTo-JsonManual $Valor[$k] ($Indent + 1))
        })
        if ($pares.Count -eq 0) { return '{}' }
        return "{`n" + ($pares -join ",`n") + "`n$pad}"
    }

    if (($Valor -is [System.Collections.IEnumerable]) -and -not ($Valor -is [string])) {
        $items = @(foreach ($it in $Valor) { $padIn + (ConvertTo-JsonManual $it ($Indent + 1)) })
        if ($items.Count -eq 0) { return '[]' }
        return "[`n" + ($items -join ",`n") + "`n$pad]"
    }

    if ($Valor -is [psobject]) {
        $pares = @(foreach ($p in $Valor.PSObject.Properties) {
            $padIn + (ConvertTo-JsonTexto $p.Name) + ': ' + (ConvertTo-JsonManual $p.Value ($Indent + 1))
        })
        if ($pares.Count -eq 0) { return '{}' }
        return "{`n" + ($pares -join ",`n") + "`n$pad}"
    }

    return (ConvertTo-JsonTexto "$Valor")
}

function Write-Testigo {
    param([Parameter(Mandatory)] $Doc, [Parameter(Mandatory)] [string] $Ruta)
    $json = (ConvertTo-JsonManual $Doc) + "`n"
    [System.IO.File]::WriteAllText($Ruta, $json, $u8)
}

function ConvertTo-RutaRelativa {
    <#
    .SYNOPSIS
        Ruta relativa a la raiz del repo, con barras normales.
    .DESCRIPTION
        [System.IO.Path]::GetRelativePath no existe en .NET Framework -solo en .NET
        Core/5+-, y PowerShell 5.1 corre sobre .NET Framework: llamarlo revienta con
        "no contiene ningun metodo llamado 'GetRelativePath'". Se arma a mano.
    #>
    param([Parameter(Mandatory)] [string] $Ruta)
    $raizTexto  = ((Resolve-Path $raiz).Path).TrimEnd('\', '/')
    $rutaTexto  = ((Resolve-Path $Ruta).Path)
    $rel = $rutaTexto
    if ($rutaTexto.StartsWith($raizTexto, [System.StringComparison]::OrdinalIgnoreCase)) {
        $rel = $rutaTexto.Substring($raizTexto.Length).TrimStart('\', '/')
    }
    return ($rel -replace '\\', '/')
}


if ($Solo -in @('todos', 'secretos')) {
# -- Testigo 1: secretos --------------------------------------------------------
# Find-Secreto sobre cada linea del corpus. El corpus junta las 29 cadenas de
# tests\casos\04-secretos.ps1 (Assert-Detecta + Assert-NoDetecta, concatenaciones ya
# resueltas) mas 2 cadenas de contenido tomadas de tests\payloads\.

$catalogo = Import-PatronesSecretos -Ruta (Join-Path $raiz 'comun\reglas\secretos.patrones.json')
$corpus   = Get-Content (Join-Path $PSScriptRoot 'fixtures\corpus-secretos.txt') -Encoding UTF8

$casosSecretos = foreach ($t in $corpus) {
    if (-not $t) { continue }
    $h = Find-Secreto -Texto $t -Catalogo $catalogo
    if ($null -eq $h) {
        [ordered]@{ texto = $t; hallazgo = $false }
    } else {
        [ordered]@{ texto = $t; hallazgo = $true; id = $h.Id; confianza = $h.Confianza; muestra = $h.Muestra }
    }
}

Write-Testigo -Doc ([ordered]@{ generado = $version; casos = @($casosSecretos) }) -Ruta $SalidaSecretos
Write-Host "testigo de secretos escrito: $SalidaSecretos ($($casosSecretos.Count) casos)"
}


if ($Solo -in @('todos', 'checks')) {
# -- Testigo 2: checks ----------------------------------------------------------
# Un caso por cada uno de los cinco checks instalados, contra un archivo real del
# proyecto de fixture tests\fixtures\proyecto-checks\, para que Get-ArchivoEscrito
# -que lee del disco, no del evento- tenga algo que leer.
#
# Cada evento tiene la forma de tests\payloads\post-tool-use-write.json (PostToolUse
# / Write / tool_input.file_path + content) pero con el file_path apuntando al
# archivo de fixture real: el payload guardado en el repo usa una ruta que no existe
# en disco, y los checks salen temprano si Test-Path falla.

$proyectoChecks = Resolve-Path (Join-Path $PSScriptRoot 'fixtures\proyecto-checks')

function New-EventoEscritura {
    param([Parameter(Mandatory)] [string] $RutaArchivo)
    $contenido = [System.IO.File]::ReadAllText($RutaArchivo, $u8)
    return [pscustomobject]@{
        session_id      = 'testigo-checks'
        cwd              = "$proyectoChecks"
        hook_event_name = 'PostToolUse'
        tool_name       = 'Write'
        tool_input      = [pscustomobject]@{ file_path = $RutaArchivo; content = $contenido }
    }
}

function Get-CasoCheck {
    param(
        [Parameter(Mandatory)] [string] $Check,
        [Parameter(Mandatory)] [string] $DirChecks,
        [Parameter(Mandatory)] [string] $RutaCheck,
        [Parameter(Mandatory)] [string] $Archivo,
        $Config = $null
    )

    $rutaArchivo = Join-Path $proyectoChecks $Archivo
    $evento      = New-EventoEscritura -RutaArchivo $rutaArchivo
    # Sin @() extra: Invoke-Checks ya devuelve la ArrayList con "return ,$hallazgos".
    # Envolverla de nuevo en @() la mete adentro de un array de un elemento y
    # .Count pasa a valer 1 (la ArrayList entera) en vez de la cantidad real.
    $hallazgos   = Invoke-Checks -Evento $evento -DirChecks $DirChecks -Proyecto "$proyectoChecks" -Config $Config

    return [ordered]@{
        check     = $Check
        ruta      = (ConvertTo-RutaRelativa -Ruta $RutaCheck)
        payload   = 'post-tool-use-write.json'
        proyecto  = (ConvertTo-RutaRelativa -Ruta $proyectoChecks)
        config    = $Config
        hallazgos = @($hallazgos)
    }
}

$dirChecksComun      = Join-Path $raiz 'comun\checks'
$dirChecksDesarrollo = Join-Path $raiz 'harnesses\desarrollo\checks'

$casosChecks = @(
    (Get-CasoCheck -Check 'claude-md-zonas' -DirChecks $dirChecksComun `
        -RutaCheck (Join-Path $dirChecksComun 'claude-md-zonas.ps1') `
        -Archivo 'CLAUDE.md' -Config ([pscustomobject]@{ techoZonaFija = 5 })),

    (Get-CasoCheck -Check 'dev-accesibilidad-html' -DirChecks $dirChecksDesarrollo `
        -RutaCheck (Join-Path $dirChecksDesarrollo 'dev-accesibilidad-html.ps1') `
        -Archivo 'pagina.html'),

    (Get-CasoCheck -Check 'dev-api-rutas' -DirChecks $dirChecksDesarrollo `
        -RutaCheck (Join-Path $dirChecksDesarrollo 'dev-api-rutas.ps1') `
        -Archivo 'rutas.ts'),

    (Get-CasoCheck -Check 'dev-dependencias' -DirChecks $dirChecksDesarrollo `
        -RutaCheck (Join-Path $dirChecksDesarrollo 'dev-dependencias.ps1') `
        -Archivo 'package.json'),

    (Get-CasoCheck -Check 'dev-infra-en-codigo' -DirChecks $dirChecksDesarrollo `
        -RutaCheck (Join-Path $dirChecksDesarrollo 'dev-infra-en-codigo.ps1') `
        -Archivo 'config.ts')
)

Write-Testigo -Doc ([ordered]@{ generado = $version; casos = $casosChecks }) -Ruta $SalidaChecks
Write-Host "testigo de checks escrito: $SalidaChecks ($($casosChecks.Count) casos, $(($casosChecks | ForEach-Object { $_.hallazgos.Count } | Measure-Object -Sum).Sum) hallazgos)"
}


if ($Solo -in @('todos', 'zonas')) {
# -- Testigo 3: zonas -----------------------------------------------------------
# Reimport defensivo: claude-md-zonas.ps1 (corrido en la seccion de checks, arriba)
# hace su propio Import-Module -Force de este mismo modulo, y esa segunda carga deja
# a Measure-Zonas / Measure-FueraDeZonas sin resolverse en este scope. Se lo vuelve a
# traer antes de usarlo.
Import-Module (Join-Path $raiz 'comun\hooks\lib\Zonas.psm1') -Force

$rutaMd = Join-Path $PSScriptRoot 'fixtures\claude-md-de-prueba.md'
$texto  = [System.IO.File]::ReadAllText($rutaMd, $u8)

$configZonas = [pscustomobject]@{
    techoZonaFija   = 60
    techoZonaMapa   = 40
    techoZonaIndice = 30
    techoZonaCache  = 30
}

$medicion = Measure-Zonas -Texto $texto -Config $configZonas
$fuera    = Measure-FueraDeZonas -Texto $texto

$zonas = [ordered]@{}
foreach ($z in $medicion) { $zonas[$z.Nombre] = $z.Lineas }

$docZonas = [ordered]@{
    generado     = $version
    archivo      = 'tests/fixtures/claude-md-de-prueba.md'
    zonas        = $zonas
    fueraDeZonas = $fuera.Lineas
}

Write-Testigo -Doc $docZonas -Ruta $SalidaZonas
Write-Host "testigo de zonas escrito: $SalidaZonas"
}
