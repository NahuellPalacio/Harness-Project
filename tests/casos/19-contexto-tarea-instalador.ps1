# E-32 y E-33 de docs/cambios/contexto-de-tarea/spec.md.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y no ponerlos es
# la otra mitad de la regla que declara 00-encoding-fuentes.ps1.

Set-Grupo 'Instalador - el contexto de tarea'

$instaladorCtx = Join-Path $script:Raiz 'install.ps1'

function Invoke-InstaladorCtx {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorCtx @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function New-ProyectoCtx {
    param([string] $Prefijo)
    $demo = Join-Path ([System.IO.Path]::GetTempPath()) `
                      ($Prefijo + '-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'), "# Proyecto de prueba`r`n")
    return $demo
}

$demo = New-ProyectoCtx 'harness-ctx'
try {
    $r = Invoke-InstaladorCtx @('-Project', $demo, '-Harness', 'desarrollo', '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    # -- E-33: los modulos del resolvedor y el schema del contrato ------------------

    $dirContexto = Join-Path $demo '.claude\harness\bin\desarrollo\contexto'
    foreach ($modulo in @('__init__.py', 'comun.py', 'limpieza.py', 'tarea.py',
                          'proyecto.py', 'documentos.py', 'repositorio.py', 'ensamblador.py')) {
        Assert-Verdadero "E-33 el modulo $modulo quedo instalado" `
            (Test-Path (Join-Path $dirContexto $modulo)) "falta $modulo"
    }
    $schema = Join-Path $demo '.claude\harness\schemas\task-context.schema.json'
    Assert-Verdadero 'E-33 el schema del TaskContext quedo instalado' (Test-Path $schema) `
        'no se instalo task-context.schema.json'
    if (Test-Path $schema) {
        Assert-Igual 'E-33 el schema es el del repositorio, byte a byte' `
            ([System.IO.File]::ReadAllText((Join-Path $script:Raiz 'comun\schemas\task-context.schema.json'))) `
            ([System.IO.File]::ReadAllText($schema))
    }

    # El validador que usa el ensamblador tiene que estar del lado instalado tambien:
    # se importa por ruta desde comun/bin, y si no viaja el contrato no se puede validar.
    Assert-Verdadero 'E-33 contexto-armar.py, que es el validador, tambien esta' `
        (Test-Path (Join-Path $demo '.claude\harness\bin\contexto-armar.py')) `
        'sin el no se puede validar el TaskContext en un proyecto instalado'

    # -- E-32: los contextos resueltos sobreviven a -Update y a -Uninstall ---------

    $dirContextos = Join-Path $demo '.claude\contextos'
    New-Item -ItemType Directory -Path $dirContextos -Force | Out-Null
    $unContexto = Join-Path $dirContextos 'GCBA-1234.json'
    $contenido = '{ "meta": { "task_key": "GCBA-1234" } }'
    [System.IO.File]::WriteAllText($unContexto, $contenido)

    $r = Invoke-InstaladorCtx @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-32 -Update no borra los contextos' (Test-Path $unContexto) `
        'el -Update se llevo puesto .claude\contextos'
    if (Test-Path $unContexto) {
        Assert-Igual 'E-32 -Update los deja identicos' $contenido `
            ([System.IO.File]::ReadAllText($unContexto))
    }

    $r = Invoke-InstaladorCtx @('-Project', $demo, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-32 -Uninstall tampoco los borra' (Test-Path $unContexto) `
        'el -Uninstall se llevo puesto un contexto resuelto'
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}
