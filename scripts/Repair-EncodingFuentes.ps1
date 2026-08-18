<#
.SYNOPSIS
    Arregla el encoding de los fuentes .ps1 y .psm1 del repo.

.DESCRIPTION
    Windows PowerShell 5.1 lee un .ps1 sin BOM usando la codepage ANSI del sistema.
    Un archivo guardado en UTF-8 sin BOM que diga "definición" se carga como
    "definiciÃ³n", y cada mensaje del harness llega ilegible al contexto. Para los
    .ps1 y .psm1 que quedan, la regla es la de siempre: caracteres no ASCII sin BOM
    se corrigen agregando el BOM.

    Python es al reves: SIEMPRE lee un .py en UTF-8, no depende de la codepage del
    sistema, asi que ahi el BOM sobra -y en el peor caso, se cuela como caracter en
    el primer token de algo que concatena el archivo sin filtrarlo-. Para los .py del
    harness, este script hace lo opuesto: si tienen BOM, se lo saca.

    El test tests\casos\00-encoding-fuentes.ps1 detecta los dos problemas; este script
    los corrige. Corrolo despues de escribir un check nuevo con texto en español, o
    despues de guardar un .py con un editor que le agrega BOM por costumbre.

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

$tocados = 0

# ── .ps1 / .psm1 con acentos: agregar el BOM que les falta ──────────────────────

$fuentesPs = Get-ChildItem $raiz -Recurse -Include '*.ps1', '*.psm1' |
             Where-Object { $_.FullName -notlike '*\.git\*' }

foreach ($f in $fuentesPs) {
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

# ── .py del harness con BOM: sacarselo ───────────────────────────────────────────

$fuentesPy = Get-ChildItem $raiz -Recurse -Filter '*.py' -File |
             Where-Object { $_.FullName -notmatch '\\\.git\\' -and $_.FullName -notmatch '\\tests\\out\\' -and $_.FullName -notmatch '\\__pycache__\\' }

foreach ($f in $fuentesPy) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)

    $tieneBom = ($bytes.Length -ge 3 -and
                 $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)

    if (-not $tieneBom) { continue }

    $relativo = $f.FullName.Replace($raiz + '\', '')

    if ($PSCmdlet.ShouldProcess($relativo, 'quitar BOM')) {
        $texto = [System.IO.File]::ReadAllText($f.FullName, $conBom)
        [System.IO.File]::WriteAllText($f.FullName, $texto, $sinBom)
        Write-Host ('  BOM quitado -> ' + $relativo) -ForegroundColor Yellow
    }

    $tocados++
}

if ($tocados -eq 0) {
    Write-Host 'Todos los fuentes estan bien.' -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host ("$tocados archivo(s) corregido(s).") -ForegroundColor Green
}
