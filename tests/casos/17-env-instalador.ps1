# E-01 a E-06 de docs/cambios/env-credenciales-externas/spec.md.
#
# Va aparte de 03-instalador.ps1 por el mismo motivo que 11-codebase-instalador.ps1 y
# 14-contexto-instalador.ps1: ese caso rompe archivos versionados a proposito para
# probar el -Update, con un finally que no sobrevive a que maten el proceso. Aca no se
# rompe nada del repo.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y no ponerlos es
# la otra mitad de la regla que declara 00-encoding-fuentes.ps1.

Set-Grupo 'Instalador - las credenciales externas'

$instalador = Join-Path $script:Raiz 'install.ps1'
$origenEnvExample = Join-Path $script:Raiz 'harnesses\desarrollo\.env.example'
$textoOrigen = [System.IO.File]::ReadAllText($origenEnvExample)

function Invoke-InstaladorEnv {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instalador @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function New-ProyectoDescartable {
    param([string] $Prefijo)
    $demo = Join-Path ([System.IO.Path]::GetTempPath()) `
                      ($Prefijo + '-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'), "# Proyecto de prueba`r`n")
    return $demo
}

# -- E-01, E-04: instalacion nueva con desarrollo ------------------------------------

$demo = New-ProyectoDescartable 'harness-env'
try {
    $r = Invoke-InstaladorEnv @('-Project', $demo, '-Harness', 'desarrollo', '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    $rutaEnvExample = Join-Path $demo '.env.example'
    $rutaEnv = Join-Path $demo '.env'

    Assert-Verdadero 'E-01 .env.example existe' (Test-Path $rutaEnvExample) '.env.example no se instalo'
    if (Test-Path $rutaEnvExample) {
        Assert-Igual 'E-01 .env.example es identico byte a byte a la plantilla' `
            $textoOrigen ([System.IO.File]::ReadAllText($rutaEnvExample))
    }

    Assert-Verdadero 'E-04 .env existe' (Test-Path $rutaEnv) '.env no se creo'
    if (Test-Path $rutaEnv) {
        $textoEnv = [System.IO.File]::ReadAllText($rutaEnv)
        Assert-Igual 'E-04 .env nace con las mismas variables que .env.example' $textoOrigen $textoEnv
        Assert-Contiene 'E-04 JIRA_TOKEN queda con placeholder, no vacio a ciegas' 'JIRA_TOKEN=<' $textoEnv
        Assert-Contiene 'E-04 GITLAB_TOKEN idem' 'GITLAB_TOKEN=<' $textoEnv
        Assert-Contiene 'E-04 OPENSHIFT_TOKEN idem' 'OPENSHIFT_TOKEN=<' $textoEnv
    }

    # -- E-03, E-05: -Update pisa .env.example y nunca toca .env --------------------

    $marcaDelDesarrollador = "`r`nGITLAB_TOKEN=un-token-que-la-persona-ya-cargo`r`n"
    [System.IO.File]::AppendAllText($rutaEnv, $marcaDelDesarrollador)
    $textoEnvConMarca = [System.IO.File]::ReadAllText($rutaEnv)

    [System.IO.File]::WriteAllText($rutaEnvExample, "# version vieja, para ver que -Update la pisa`r`n")

    $r = Invoke-InstaladorEnv @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo

    Assert-Igual 'E-03 -Update pisa .env.example con la plantilla actual' `
        $textoOrigen ([System.IO.File]::ReadAllText($rutaEnvExample))

    Assert-Igual 'E-05 -Update no toca .env: sigue con la marca del desarrollador' `
        $textoEnvConMarca ([System.IO.File]::ReadAllText($rutaEnv))

    # -- E-06: -Uninstall no se lleva ni .env ni .env.example ------------------------

    $r = Invoke-InstaladorEnv @('-Project', $demo, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo

    Assert-Verdadero 'E-06 -Uninstall conserva .env.example' (Test-Path $rutaEnvExample) `
        '.env.example no sobrevivio a -Uninstall'
    Assert-Verdadero 'E-06 -Uninstall conserva .env' (Test-Path $rutaEnv) `
        '.env no sobrevivio a -Uninstall'
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}

# -- E-02: sin desarrollo, ni .env.example ni .env -----------------------------------

$demoSinDev = New-ProyectoDescartable 'harness-env-sin-dev'
try {
    $r = Invoke-InstaladorEnv @('-Project', $demoSinDev, '-Harness', 'analisis', '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar analisis sale con codigo 0' 0 $r.Codigo

    Assert-Verdadero 'E-02 sin desarrollo, no hay .env.example' `
        (-not (Test-Path (Join-Path $demoSinDev '.env.example'))) '.env.example se instalo igual'
    Assert-Verdadero 'E-02 sin desarrollo, no hay .env' `
        (-not (Test-Path (Join-Path $demoSinDev '.env'))) '.env se instalo igual'
}
finally {
    if (Test-Path $demoSinDev) { Remove-Item $demoSinDev -Recurse -Force -ErrorAction SilentlyContinue }
}
