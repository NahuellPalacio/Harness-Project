# E-01 a E-06 de docs/cambios/env-credenciales-externas/spec.md.
#
# Pisados por docs/cambios/entorno-primero/spec.md: la plantilla va en un bloque marcado de
# .env.example (E-01, E-03), y OPENSHIFT_TOKEN ya no se reparte (E-04).
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
$marcaIni = '# >>> gcba-harness: integraciones >>>'
$marcaFin = '# <<< gcba-harness: integraciones <<<'

function Get-BloqueDelHarness {
    param([string] $Texto)
    $i = $Texto.IndexOf($marcaIni)
    $f = $Texto.IndexOf($marcaFin)
    if ($i -lt 0 -or $f -le $i) { return $null }
    return $Texto.Substring($i + $marcaIni.Length, $f - $i - $marcaIni.Length).Trim()
}

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
    $r = Invoke-InstaladorEnv @('-Project', $demo, '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    $rutaEnvExample = Join-Path $demo '.env.example'
    $rutaEnv = Join-Path $demo '.env'

    Assert-Verdadero 'E-01 .env.example existe' (Test-Path $rutaEnvExample) '.env.example no se instalo'
    if (Test-Path $rutaEnvExample) {
        Assert-Igual 'E-01 el bloque del harness en .env.example es la plantilla' `
            $textoOrigen.Trim() (Get-BloqueDelHarness ([System.IO.File]::ReadAllText($rutaEnvExample)))
    }

    Assert-Verdadero 'E-04 .env existe' (Test-Path $rutaEnv) '.env no se creo'
    if (Test-Path $rutaEnv) {
        $textoEnv = [System.IO.File]::ReadAllText($rutaEnv)
        Assert-Igual 'E-04 .env nace con las mismas variables que .env.example' $textoOrigen $textoEnv
        Assert-Contiene 'E-04 JIRA_TOKEN queda con placeholder, no vacio a ciegas' 'JIRA_TOKEN=<' $textoEnv
        Assert-Contiene 'E-04 GITLAB_TOKEN idem' 'GITLAB_TOKEN=<' $textoEnv
        Assert-Verdadero 'E-04 sin OPENSHIFT_TOKEN: no hay adaptador' `
            (-not $textoEnv.Contains('OPENSHIFT')) ".env trae una variable de OpenShift"
    }

    # -- E-03, E-05: -Update pisa .env.example y nunca toca .env --------------------

    $marcaDelDesarrollador = "`r`nGITLAB_TOKEN=un-token-que-la-persona-ya-cargo`r`n"
    [System.IO.File]::AppendAllText($rutaEnv, $marcaDelDesarrollador)
    $textoEnvConMarca = [System.IO.File]::ReadAllText($rutaEnv)

    [System.IO.File]::WriteAllText($rutaEnvExample, "# version vieja, para ver que -Update la pisa`r`n")

    $r = Invoke-InstaladorEnv @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo

    $textoExample = [System.IO.File]::ReadAllText($rutaEnvExample)
    Assert-Igual 'E-03 -Update deja en .env.example el bloque con la plantilla actual' `
        $textoOrigen.Trim() (Get-BloqueDelHarness $textoExample)
    Assert-Contiene 'E-03 y lo que el proyecto tenia fuera del bloque sigue' `
        '# version vieja, para ver que -Update la pisa' $textoExample

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
