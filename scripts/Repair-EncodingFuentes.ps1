<#
.SYNOPSIS
    Arregla el encoding de los fuentes .ps1 y .psm1 del repo.

.DESCRIPTION
    Windows PowerShell 5.1 lee un .ps1 sin BOM usando la codepage ANSI del sistema.
    Un archivo guardado en UTF-8 sin BOM que diga "definición" se carga como
    "definiciÃ³n", y cada mensaje del harness llega ilegible al contexto.

    Este script busca los fuentes que tienen caracteres no ASCII sin BOM y les agrega
    el BOM, conservando el contenido.

    El test tests\casos\00-encoding-fuentes.ps1 detecta el problema; este script lo
    corrige. Corrolo despues de escribir un check nuevo con texto en español.

.EXAMPLE
    .\scripts\Repair-EncodingFuentes.ps1 -WhatIf
    .\scripts\Repair-EncodingFuentes.ps1
#>
[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = 'Stop'

$raiz   = Split-Path -Parent $PSScriptRoot
$conBom = New-Object System.Text.UTF8Encoding $true
$sinBom = New-Object System.Text.UTF8Encoding $false

$fuentes = Get-ChildItem $raiz -Recurse -Include '*.ps1', '*.psm1' |
           Where-Object { $_.FullName -notlike '*\.git\*' }

$tocados = 0

foreach ($f in $fuentes) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)

    $tieneBom = ($bytes.Length -ge 3 -and
                 $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)

    $tieneNoAscii = $false
    foreach ($b in $bytes) {
        if ($b -gt 127) { $tieneNoAscii = $true; break }
    }

    if (-not $tieneNoAscii -or $tieneBom) { continue }

    $relativo = $f.FullName.Replace($raiz + '\', '')

    if ($PSCmdlet.ShouldProcess($relativo, 'agregar BOM UTF-8')) {
        $texto = [System.IO.File]::ReadAllText($f.FullName, $sinBom)
        [System.IO.File]::WriteAllText($f.FullName, $texto, $conBom)
        Write-Host ('  BOM agregado -> ' + $relativo) -ForegroundColor Yellow
    }

    $tocados++
}

if ($tocados -eq 0) {
    Write-Host 'Todos los fuentes estan bien.' -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host ("$tocados archivo(s) corregido(s).") -ForegroundColor Green
}
