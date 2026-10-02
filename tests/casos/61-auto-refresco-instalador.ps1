# E-68 de docs/cambios/conocimiento-auto-refresco/spec.md (KRF-068), y el disparador de -Update.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM (ver
# 00-encoding-fuentes.ps1).
#
# Instala de verdad, sin .env y sin canal: la instalacion tiene que terminar bien y decir que el
# conocimiento queda pendiente, sin anotar una revision que salio bien.

Set-Grupo 'Instalador - revision automatica del conocimiento'

$instaladorKr = Join-Path $script:Raiz 'install.ps1'

function Invoke-InstaladorKr {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorKr @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function Read-AgendaKr {
    param([string] $Proy)
    $ruta = Join-Path $Proy '.claude\runtime\knowledge-refresh.json'
    if (-not (Test-Path -LiteralPath $ruta)) { return $null }
    return ([System.IO.File]::ReadAllText($ruta) | ConvertFrom-Json)
}

$baseKr = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-kr-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$demoKr = Join-Path $baseKr 'proyecto'
New-Item -ItemType Directory -Path $demoKr -Force | Out-Null
[System.IO.File]::WriteAllText((Join-Path $demoKr 'CLAUDE.md'), "# Proyecto de prueba`r`n")

try {
    $r = Invoke-InstaladorKr @('-Project', $demoKr, '-Usuario', 'Ana Prueba')
    Assert-Igual 'E-68 instalar sin red ni canal sale 0' 0 $r.Codigo
    Assert-Contiene 'E-68 dice que el conocimiento queda pendiente' 'Conocimiento: revis' $r.Salida
    Assert-Contiene 'E-68 con el codigo' 'AUTO_REFRESH_CHANNEL_UNAVAILABLE' $r.Salida

    $agenda = Read-AgendaKr $demoKr
    Assert-Verdadero 'E-68 la agenda quedo escrita' ($null -ne $agenda)
    if ($agenda) {
        Assert-Igual 'E-68 el disparador es INSTALL' 'INSTALL' $agenda.trigger
        Assert-Igual 'E-68 sin revision que salio bien' '' ([string]$agenda.lastSuccessfulCheckAt)
        Assert-Igual 'E-68 queda UNRESOLVED' 'UNRESOLVED' $agenda.state
    }
    Assert-Verdadero 'E-68 la politica esta instalada' (Test-Path (Join-Path $demoKr '.claude\harness\reglas\desarrollo\knowledge-refresh-policy.json'))
    Assert-Verdadero 'E-68 y sus dos schemas' ((Test-Path (Join-Path $demoKr '.claude\harness\schemas\knowledge-refresh-policy.schema.json')) -and (Test-Path (Join-Path $demoKr '.claude\harness\schemas\knowledge-refresh-state.schema.json')))

    $estado = [System.IO.File]::ReadAllText((Join-Path $demoKr '.claude\harness.installation.json')) | ConvertFrom-Json
    Assert-Igual 'E-68 la instalacion queda PARTIAL, no READY' 'PARTIAL' $estado.bootstrap.status
    Assert-Verdadero 'E-68 con la revision pendiente a la vista' (@($estado.bootstrap.pendingConditions) -contains 'KNOWLEDGE_REFRESH_UNRESOLVED:AUTO_REFRESH_CHANNEL_UNAVAILABLE')

    $u = Invoke-InstaladorKr @('-Project', $demoKr, '-Update')
    Assert-Igual 'E-14 -Update sale 0' 0 $u.Codigo
    $agenda = Read-AgendaKr $demoKr
    if ($agenda) { Assert-Igual 'E-14 -Update anota HARNESS_UPDATE' 'HARNESS_UPDATE' $agenda.trigger }
}
finally {
    Remove-Item -LiteralPath $baseKr -Recurse -Force -ErrorAction SilentlyContinue
}
