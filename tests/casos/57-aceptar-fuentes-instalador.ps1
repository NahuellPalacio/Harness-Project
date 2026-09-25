# E-16, E-17 y E-18 de docs/cambios/aceptar-fuentes-en-el-proyecto/spec.md.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM (ver
# 00-encoding-fuentes.ps1).
#
# Instala de verdad, porque el bug era exactamente ese: en el repositorio todo andaba y en un
# proyecto instalado ninguna fuente podia llegar a CURRENT. La prueba corre el dev-harness.py
# INSTALADO, no el del repositorio.

Set-Grupo 'Instalador - aceptar fuentes en el proyecto'

$instaladorAf = Join-Path $script:Raiz 'install.ps1'

function Invoke-InstaladorAf {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorAf @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function Invoke-FuentesAf {
    param([string] $Proy, [string[]] $Argumentos)
    $cli = Join-Path $Proy '.claude\harness\bin\desarrollo\dev-harness.py'
    $salida = & python $cli fuentes @Argumentos --proyecto $Proy 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function Read-FuentesAf {
    param([string] $Proy)
    return ([System.IO.File]::ReadAllText((Join-Path $Proy '.claude\harness.fuentes.json')) | ConvertFrom-Json)
}

function Get-LineaDeVersionAf {
    param([string] $Ruta)
    foreach ($l in [System.IO.File]::ReadAllLines($Ruta)) {
        if ($l -match '^>\s*[Vv]ersi') { return $l }
    }
    return $null
}

$baseAf = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-af-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$demoAf = Join-Path $baseAf 'proyecto'
$pdfsAf = Join-Path $baseAf 'ficha'
New-Item -ItemType Directory -Path $demoAf -Force | Out-Null
New-Item -ItemType Directory -Path $pdfsAf -Force | Out-Null
[System.IO.File]::WriteAllText((Join-Path $demoAf 'CLAUDE.md'), "# Proyecto de prueba`r`n")
[System.IO.File]::WriteAllText((Join-Path $pdfsAf 'ES0902 - Estandar de Seguridad V6.2.pdf'), 'original ES0902 6.2')

try {
    $r = Invoke-InstaladorAf @('-Project', $demoAf, '-Harness', 'desarrollo', '-Usuario', 'Ana Prueba')
    Assert-Igual 'la instalacion sale 0' 0 $r.Codigo

    # -- E-16: los seis extractos llegan, con su linea de version ---------------------------
    $extractosRepo = @(Get-ChildItem (Join-Path $script:Raiz 'normativa\extractos') -Filter '*.md' | Sort-Object Name)
    $dirExtractos = Join-Path $demoAf '.claude\harness\normativa\extractos'
    Assert-Igual 'E-16 son seis extractos en el repositorio' 6 $extractosRepo.Count
    foreach ($e in $extractosRepo) {
        $instalado = Join-Path $dirExtractos $e.Name
        Assert-Verdadero ('E-16 el extracto ' + $e.Name + ' esta instalado') (Test-Path -LiteralPath $instalado)
        if (Test-Path -LiteralPath $instalado) {
            Assert-Igual ('E-16 ' + $e.Name + ' declara la misma version') (Get-LineaDeVersionAf $e.FullName) (Get-LineaDeVersionAf $instalado)
        }
    }

    $f = Invoke-FuentesAf $demoAf @('--archivo', $pdfsAf)
    Assert-Igual 'E-16 fuentes sale 0' 0 $f.Codigo
    Assert-Verdadero 'E-16 ningun extracto faltante' (-not ($f.Salida -match 'no esta en este arbol'))
    Assert-Igual 'E-16 sin aceptar, ES0902 queda como hoy' 'FRESHNESS_UNVERIFIED' (Read-FuentesAf $demoAf).sources.ES0902.state

    # -- E-17: la reproduccion del bug, cerrada ------------------------------------------------
    $f = Invoke-FuentesAf $demoAf @('--archivo', $pdfsAf, '--aceptar', 'ES0902')
    Assert-Igual 'E-17 aceptar sale 0' 0 $f.Codigo
    $estado = Read-FuentesAf $demoAf
    Assert-Igual 'E-17 ES0902 queda CURRENT en el proyecto instalado' 'CURRENT' $estado.sources.ES0902.state
    Assert-Igual 'E-17 quien acepto sale del usuario configurado' 'Ana Prueba' $estado.decisions.ES0902.by
    Assert-Igual 'E-17 el canal es el directorio' ('archivo:' + $pdfsAf) $estado.decisions.ES0902.channel

    # -- E-18: la aceptacion sobrevive a -Update y -Doctor no la marca ------------------------
    $antes = [System.IO.File]::ReadAllText((Join-Path $demoAf '.claude\harness.fuentes.json'))
    $u = Invoke-InstaladorAf @('-Project', $demoAf, '-Update')
    Assert-Igual 'E-18 -Update sale 0' 0 $u.Codigo
    $despues = [System.IO.File]::ReadAllText((Join-Path $demoAf '.claude\harness.fuentes.json'))
    Assert-Igual 'E-18 -Update no toca harness.fuentes.json' $antes $despues
    $f = Invoke-FuentesAf $demoAf @('--archivo', $pdfsAf)
    Assert-Igual 'E-18 despues del -Update ES0902 sigue CURRENT' 'CURRENT' (Read-FuentesAf $demoAf).sources.ES0902.state
    $d = Invoke-InstaladorAf @('-Project', $demoAf, '-Doctor')
    Assert-Verdadero 'E-18 -Doctor no marca harness.fuentes.json' (-not ($d.Salida -match 'harness\.fuentes\.json'))
    Assert-Verdadero 'E-18 -Doctor no marca los extractos como alterados' (-not ($d.Salida -match 'extractos\\[^\s]+\.md.*(modific|alterad)'))
}
finally {
    Remove-Item -LiteralPath $baseAf -Recurse -Force -ErrorAction SilentlyContinue
}
