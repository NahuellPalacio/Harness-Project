# E-30, E-61, E-63, E-64 y E-65 de docs/cambios/entorno-primero/spec.md: lo que el instalador
# hace con el .env, el .env.example, el contrato y la proyeccion.
#
# Va aparte de 03-instalador.ps1 por el mismo motivo que 17-env-instalador.ps1: ese caso
# rompe archivos versionados a proposito, con un finally que no sobrevive a que maten el
# proceso. Aca no se rompe nada del repo.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y no ponerlos es
# la otra mitad de la regla que declara 00-encoding-fuentes.ps1.

Set-Grupo 'Instalador - la configuracion sale del .env'

$instaladorEnt = Join-Path $script:Raiz 'install.ps1'
$plantillaEnt  = [System.IO.File]::ReadAllText((Join-Path $script:Raiz 'harnesses\desarrollo\.env.example'))
$contratoEnt   = Join-Path $script:Raiz 'harnesses\desarrollo\reglas\integration-environment-contract.json'
$marcaIniEnt   = '# >>> gcba-harness: integraciones >>>'
$marcaFinEnt   = '# <<< gcba-harness: integraciones <<<'

function Invoke-InstaladorEnt {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorEnt @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function Get-BloqueEnt {
    param([string] $Texto)
    $i = $Texto.IndexOf($marcaIniEnt)
    $f = $Texto.IndexOf($marcaFinEnt)
    if ($i -lt 0 -or $f -le $i) { return $null }
    return $Texto.Substring($i + $marcaIniEnt.Length, $f - $i - $marcaIniEnt.Length).Trim()
}

$demoEnt = Join-Path ([System.IO.Path]::GetTempPath()) `
                     ('harness-entorno-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $demoEnt -Force | Out-Null
try {
    [System.IO.File]::WriteAllText((Join-Path $demoEnt 'CLAUDE.md'), "# Proyecto de prueba`r`n")
    # Un .env.example propio del proyecto, de antes de instalar el harness.
    $rutaExampleEnt = Join-Path $demoEnt '.env.example'
    [System.IO.File]::WriteAllText($rutaExampleEnt, "# del proyecto`r`nMI_VARIABLE=1`r`n")

    $r = Invoke-InstaladorEnt @('-Project', $demoEnt, '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo
    $textoExample = [System.IO.File]::ReadAllText($rutaExampleEnt)
    Assert-Contiene 'E-63 el .env.example del proyecto conserva lo suyo' 'MI_VARIABLE=1' $textoExample
    Assert-Igual 'E-63 y suma el bloque del harness' $plantillaEnt.Trim() (Get-BloqueEnt $textoExample)
    Assert-Contiene 'E-65 la instalacion dice de donde sale la configuracion' `
        'ENVIRONMENT_FIRST (.env local)' $r.Salida

    # Un .env de la persona, sin las variables nuevas, con comentarios, comillas y CRLF, y el
    # harness.integraciones.json que completaba antes de esta version.
    $rutaEnvEnt = Join-Path $demoEnt '.env'
    $envPropio = "# mi .env`r`nJIRA_TOKEN=un-token-que-la-persona-ya-cargo`r`n  OTRA='con comillas'`r`n"
    [System.IO.File]::WriteAllText($rutaEnvEnt, $envPropio)
    $bytesEnv = [System.IO.File]::ReadAllBytes($rutaEnvEnt)
    $rutaCfgEnt = Join-Path $demoEnt '.claude\harness.integraciones.json'
    [System.IO.File]::WriteAllText($rutaCfgEnt,
        '{ "jira": { "enabled": true, "baseUrl": "https://propia.atlassian.net" } }')
    $rutaCapEnt = Join-Path $demoEnt '.claude\harness.capacidades.json'
    if (Test-Path $rutaCapEnt) { Remove-Item $rutaCapEnt -Force }
    [System.IO.File]::WriteAllText($rutaExampleEnt,
        $textoExample.Replace('HARNESS_JIRA_ENABLED=false', 'UNA_LINEA_VIEJA=1'))

    $r = Invoke-InstaladorEnt @('-Project', $demoEnt, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo

    $bytesDespues = [System.IO.File]::ReadAllBytes($rutaEnvEnt)
    Assert-Igual 'E-30 -Update deja el .env del mismo largo' $bytesEnv.Length $bytesDespues.Length
    Assert-Verdadero 'E-30 E-61 -Update no cambia un byte del .env' `
        ([System.Linq.Enumerable]::SequenceEqual([byte[]]$bytesEnv, [byte[]]$bytesDespues)) `
        'el .env cambio con el -Update'

    $contratoInstalado = Join-Path $demoEnt '.claude\harness\reglas\desarrollo\integration-environment-contract.json'
    Assert-Verdadero 'E-63 el contrato quedo instalado' (Test-Path $contratoInstalado) 'falta el contrato'
    if (Test-Path $contratoInstalado) {
        Assert-Igual 'E-63 el contrato instalado es el de la fabrica' `
            ([System.IO.File]::ReadAllText($contratoEnt)) ([System.IO.File]::ReadAllText($contratoInstalado))
    }
    $textoExample = [System.IO.File]::ReadAllText($rutaExampleEnt)
    Assert-Igual 'E-63 -Update repone el bloque' $plantillaEnt.Trim() (Get-BloqueEnt $textoExample)
    Assert-Contiene 'E-63 y lo del proyecto sigue' 'MI_VARIABLE=1' $textoExample

    $proyeccion = [System.IO.File]::ReadAllText($rutaCfgEnt) | ConvertFrom-Json
    Assert-Igual 'E-64 el JSON viejo quedo convertido en proyeccion' `
        'integration-projection/1.0' $proyeccion.schema_version
    Assert-Igual 'E-64 con lo que falta migrar' 'https://propia.atlassian.net' $proyeccion.legado.jira.baseUrl

    Assert-Verdadero 'E-65 el -Update escribio harness.capacidades.json' (Test-Path $rutaCapEnt) `
        'no se revalido'
    if (Test-Path $rutaCapEnt) {
        $cap = [System.IO.File]::ReadAllText($rutaCapEnt) | ConvertFrom-Json
        Assert-Igual 'E-65 con el modo' 'ENVIRONMENT_FIRST' $cap.configurationMode
        Assert-Igual 'E-65 y la variable que falta' 'JIRA_USER' (@($cap.integraciones.jira.faltan) -join ',')
    }
    Assert-Contiene 'E-65 el -Update dice lo que falta' 'falta JIRA_USER' $r.Salida
    Assert-Verdadero 'E-65 y nunca el token' (-not $r.Salida.Contains('un-token-que-la-persona-ya-cargo')) `
        'el -Update imprimio el token'
}
finally {
    if (Test-Path $demoEnt) { Remove-Item $demoEnt -Recurse -Force -ErrorAction SilentlyContinue }
}
