# E-34 y E-35 de docs/cambios/orquestacion-nucleo/spec.md.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y no ponerlos es
# la otra mitad de la regla que declara 00-encoding-fuentes.ps1.

Set-Grupo 'Instalador - el nucleo de orquestacion'

$instaladorOrq = Join-Path $script:Raiz 'install.ps1'

function Invoke-InstaladorOrq {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorOrq @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function New-ProyectoOrq {
    param([string] $Prefijo)
    $demo = Join-Path ([System.IO.Path]::GetTempPath()) `
                      ($Prefijo + '-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'), "# Proyecto de prueba`r`n")
    return $demo
}

$demo = New-ProyectoOrq 'harness-orq'
try {
    $r = Invoke-InstaladorOrq @('-Project', $demo, '-Harness', 'desarrollo', '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    # -- E-34: los modulos, el schema y las reglas ---------------------------------

    $dirOrq = Join-Path $demo '.claude\harness\bin\desarrollo\orquestacion'
    foreach ($modulo in @('__init__.py', 'plan.py', 'capacidades.py', 'modelo.py',
                          'consumo.py', 'normativa.py', 'roster.py')) {
        Assert-Verdadero "E-34 el modulo $modulo quedo instalado" `
            (Test-Path (Join-Path $dirOrq $modulo)) "falta $modulo"
    }

    Assert-Verdadero 'E-34 rutas.py, que comparten contexto y orquestacion, tambien' `
        (Test-Path (Join-Path $demo '.claude\harness\bin\desarrollo\rutas.py')) 'falta rutas.py'

    $schema = Join-Path $demo '.claude\harness\schemas\orchestration-plan.schema.json'
    Assert-Verdadero 'E-34 el schema del plan quedo instalado' (Test-Path $schema) `
        'no se instalo orchestration-plan.schema.json'
    if (Test-Path $schema) {
        Assert-Igual 'E-34 el schema es el del repositorio, byte a byte' `
            ([System.IO.File]::ReadAllText((Join-Path $script:Raiz 'comun\schemas\orchestration-plan.schema.json'))) `
            ([System.IO.File]::ReadAllText($schema))
    }

    # Las reglas de un harness van a reglas/<id>/, al lado de las de comun.
    $dirReglas = Join-Path $demo '.claude\harness\reglas\desarrollo'
    foreach ($regla in @('es0901-7.1.json', 'roster.json')) {
        Assert-Verdadero "E-34 la regla $regla quedo instalada" `
            (Test-Path (Join-Path $dirReglas $regla)) "falta $regla"
    }
    Assert-Verdadero 'E-34 y las de comun siguen en su lugar' `
        (Test-Path (Join-Path $demo '.claude\harness\reglas\secretos.patrones.json')) `
        'el catalogo de secretos se movio'

    Assert-Verdadero 'E-34 el agente dev-orchestrator quedo instalado' `
        (Test-Path (Join-Path $demo '.claude\agents\dev-orchestrator.md')) `
        'no se instalo el agente'

    # -- E-35: los planes resueltos sobreviven -------------------------------------

    $dirPlanes = Join-Path $demo '.claude\planes'
    New-Item -ItemType Directory -Path $dirPlanes -Force | Out-Null
    $unPlan = Join-Path $dirPlanes 'GCBA-1234.json'
    $contenido = '{ "meta": { "task_key": "GCBA-1234" } }'
    [System.IO.File]::WriteAllText($unPlan, $contenido)

    $r = Invoke-InstaladorOrq @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-35 -Update no borra los planes' (Test-Path $unPlan) `
        'el -Update se llevo puesto .claude\planes'
    if (Test-Path $unPlan) {
        Assert-Igual 'E-35 -Update los deja identicos' $contenido `
            ([System.IO.File]::ReadAllText($unPlan))
    }
    Assert-Verdadero 'E-35 -Update repone las reglas del harness' `
        (Test-Path (Join-Path $dirReglas 'roster.json')) 'roster.json no volvio'

    $r = Invoke-InstaladorOrq @('-Project', $demo, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-35 -Uninstall tampoco los borra' (Test-Path $unPlan) `
        'el -Uninstall se llevo puesto un plan resuelto'
    Assert-Verdadero 'E-35 -Uninstall si borra las reglas del harness' `
        (-not (Test-Path $dirReglas)) 'las reglas instaladas sobrevivieron al -Uninstall'
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}
