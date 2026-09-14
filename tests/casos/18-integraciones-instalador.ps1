# E-29 a E-33 de docs/cambios/integraciones-bootstrap/spec.md.
#
# Va aparte de 03-instalador.ps1 por el mismo motivo que 17-env-instalador.ps1: ese caso
# rompe archivos versionados a proposito, con un finally que no sobrevive a que maten el
# proceso. Aca no se rompe nada del repo.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y no ponerlos es
# la otra mitad de la regla que declara 00-encoding-fuentes.ps1.

Set-Grupo 'Instalador - las integraciones'

$instaladorInteg = Join-Path $script:Raiz 'install.ps1'
$origenPlantilla = Join-Path $script:Raiz 'harnesses\desarrollo\integraciones.plantilla.json'
$origenBin       = Join-Path $script:Raiz 'harnesses\desarrollo\bin'

function Invoke-InstaladorInteg {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorInteg @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function New-ProyectoInteg {
    param([string] $Prefijo)
    $demo = Join-Path ([System.IO.Path]::GetTempPath()) `
                      ($Prefijo + '-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'), "# Proyecto de prueba`r`n")
    return $demo
}

# E-33 necesita que el arbol de origen TENGA bytecode para que la ausencia signifique
# algo: si nadie compilo nada, cualquier filtro pasa. Compilar el bin lo garantiza, y
# __pycache__ esta en el .gitignore, asi que no ensucia el repo.
$python = $null
foreach ($candidato in @('python', 'py', 'python3')) {
    $cmd = Get-Command $candidato -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source; break }
}
if ($python) {
    & $python -m compileall -q $origenBin 2>&1 | Out-Null
}
$pycEnOrigen = @(Get-ChildItem $origenBin -Recurse -File -Filter '*.pyc' -ErrorAction SilentlyContinue)
Assert-Verdadero 'E-33 precondicion: el arbol de origen tiene bytecode compilado' `
    ($pycEnOrigen.Count -gt 0) 'no se pudo compilar: la ausencia de .pyc en destino no probaria nada'

# -- E-29, E-33: instalacion nueva con desarrollo -----------------------------------

$demo = New-ProyectoInteg 'harness-integ'
try {
    $r = Invoke-InstaladorInteg @('-Project', $demo, '-Harness', 'desarrollo', '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    $dirBin  = Join-Path $demo '.claude\harness\bin\desarrollo'
    $cli     = Join-Path $dirBin 'dev-harness.py'
    $rutaCfg = Join-Path $demo '.claude\harness.integraciones.json'

    Assert-Verdadero 'E-29 dev-harness.py quedo instalado' (Test-Path $cli) 'no se copio el bin'
    foreach ($modulo in @('base.py', 'http.py', 'almacen.py', 'config.py', 'jira.py',
                          'gitlab.py', 'registro.py', '__init__.py')) {
        Assert-Verdadero "E-29 el modulo $modulo quedo instalado" `
            (Test-Path (Join-Path $dirBin "integraciones\$modulo")) "falta $modulo"
    }
    Assert-Verdadero 'E-29 harness.integraciones.json quedo creado' (Test-Path $rutaCfg) `
        'no se sembro la configuracion de integraciones'
    if (Test-Path $rutaCfg) {
        Assert-Igual 'E-29 la configuracion sale de la plantilla del harness' `
            ([System.IO.File]::ReadAllText($origenPlantilla)) ([System.IO.File]::ReadAllText($rutaCfg))
    }

    # E-33 mira el LOCKFILE, no el disco. El bytecode que compila el propio instalador al
    # correr los hooks para verificarlos es local y bienvenido -acelera un hook que se paga
    # en cada llamada a herramienta-. Lo que no puede pasar es que viaje bytecode desde la
    # maquina de quien instala y quede inventariado: ahi la instalacion deja de ser
    # reproducible y -Doctor compara hashes de archivos que nadie escribio a mano.
    $lock = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.lock.json'))
    Assert-Verdadero 'E-33 el lockfile no inventaria bytecode' `
        (-not (($lock -match '__pycache__') -or ($lock -match '\.pyc'))) `
        'el lockfile todavia lista bytecode'

    $pycDelHarness = @(Get-ChildItem (Join-Path $demo '.claude\harness\bin') -Recurse -File `
                       -Filter '*.pyc' -ErrorAction SilentlyContinue)
    Assert-Igual 'E-33 el bin no recibe bytecode del repositorio de origen' 0 $pycDelHarness.Count

    # -- E-31: -Update actualiza el bin y no pisa la configuracion ------------------

    $mia = '{ "jira": { "enabled": true, "baseUrl": "https://propia", "usuario": "yo@gcba" } }'
    [System.IO.File]::WriteAllText($rutaCfg, $mia)
    Remove-Item (Join-Path $dirBin 'integraciones\jira.py') -Force

    $r = Invoke-InstaladorInteg @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo
    Assert-Igual 'E-31 -Update no toca harness.integraciones.json' `
        $mia ([System.IO.File]::ReadAllText($rutaCfg))
    Assert-Verdadero 'E-31 -Update repone los modulos del bin' `
        (Test-Path (Join-Path $dirBin 'integraciones\jira.py')) 'jira.py no volvio'

    # -- E-32: -Uninstall borra el bin y deja la configuracion y el .env ------------

    $r = Invoke-InstaladorInteg @('-Project', $demo, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-32 -Uninstall borra dev-harness.py' (-not (Test-Path $cli)) `
        'el bin sobrevivio al -Uninstall'
    Assert-Verdadero 'E-32 -Uninstall conserva harness.integraciones.json' (Test-Path $rutaCfg) `
        'se borro la configuracion de integraciones'
    Assert-Verdadero 'E-32 -Uninstall conserva .env' (Test-Path (Join-Path $demo '.env')) `
        'se borro el .env'
    Assert-Verdadero 'E-33b -Uninstall no deja .claude\harness en pie con bytecode adentro' `
        (-not (Test-Path (Join-Path $demo '.claude\harness'))) `
        'quedo el directorio del harness, con el __pycache__ que genero el propio instalador'
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}

# -- E-30: sin desarrollo, nada de esto ---------------------------------------------

$demoSinDev = New-ProyectoInteg 'harness-integ-sin-dev'
try {
    $r = Invoke-InstaladorInteg @('-Project', $demoSinDev, '-Harness', 'analisis', '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar analisis sale con codigo 0' 0 $r.Codigo

    Assert-Verdadero 'E-30 sin desarrollo, no hay bin de integraciones' `
        (-not (Test-Path (Join-Path $demoSinDev '.claude\harness\bin\desarrollo'))) `
        'se instalo el bin igual'
    Assert-Verdadero 'E-30 sin desarrollo, no hay harness.integraciones.json' `
        (-not (Test-Path (Join-Path $demoSinDev '.claude\harness.integraciones.json'))) `
        'se sembro la configuracion igual'
}
finally {
    if (Test-Path $demoSinDev) { Remove-Item $demoSinDev -Recurse -Force -ErrorAction SilentlyContinue }
}
