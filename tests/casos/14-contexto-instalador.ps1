# E-18 de docs/cambios/contexto-de-proyecto/spec.md.
#
# El schema es un aporta nuevo de comun/, al lado de hooks, reglas, checks y bin. Lo que
# se prueba aca es que efectivamente se reparte y que el lockfile lo anota: un contrato
# que el instalador no lleva es un contrato que en el proyecto no existe, y el agente
# que lo invoque va a fallar recien cuando alguien corra el recorrido.
#
# Va aparte de 03-instalador.ps1 por el mismo motivo que 11-codebase-instalador.ps1: ese
# caso rompe archivos versionados a proposito para probar el -Update, con un finally que
# no sobrevive a que maten el proceso. Aca no se rompe nada del repo.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y no ponerlos es
# la otra mitad de la regla que declara 00-encoding-fuentes.ps1.

Set-Grupo 'Instalador - el contrato del contexto'

$instalador = Join-Path $script:Raiz 'install.ps1'
$demo = Join-Path ([System.IO.Path]::GetTempPath()) `
                  ('harness-ctx-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$relSchema = '.claude\harness\schemas\project-context.schema.json'
$relScript = '.claude\harness\bin\contexto-armar.py'

function Invoke-InstaladorCtx {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instalador @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

try {
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'), "# Proyecto de prueba`r`n")

    $r = Invoke-InstaladorCtx @('-Project', $demo, '-Harness', 'desarrollo',
                                '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    # E-18: el schema aterriza en su propio directorio. Va aparte de reglas/ a proposito
    # -son cuatro contratos los que van a vivir ahi- y visible, porque el contrato es del
    # harness y no un detalle privado del agente que lo consume.
    $rutaSchema = Join-Path $demo $relSchema
    Assert-Verdadero 'E-18 el schema queda en .claude\harness\schemas' `
        (Test-Path $rutaSchema) 'el schema no se instalo'

    # Y es el archivo de verdad, no uno vacio con el nombre puesto.
    #
    # El if no es defensa de mas: sin el, cuando el schema NO esta -que es justamente el
    # rojo de este escenario- el ReadAllText levanta y se lleva puesto el resto del caso.
    # El runner lo reporta como "el archivo de casos se pudo cargar: false", que es rojo
    # igual pero no dice cual escenario fallo. Un caso tiene que degradar contando lo que
    # encontro, no explotar en el primer hueco.
    if (Test-Path $rutaSchema) {
        $schema = [System.IO.File]::ReadAllText($rutaSchema) | ConvertFrom-Json
        Assert-Igual 'E-18 el schema instalado declara su version' `
            'project-context/1.1' $schema.'$id'
    } else {
        Assert-Verdadero 'E-18 el schema instalado declara su version' $false `
            'no hay schema que leer'
    }

    # El script que lo consume viaja con el, y en el mismo directorio que mapa-codigo.py:
    # contexto-armar.py resuelve el schema como ..\schemas desde su propia ubicacion, asi
    # que si alguno de los dos se moviera, la ruta relativa deja de resolver.
    Assert-Verdadero 'E-18 contexto-armar.py queda al lado de mapa-codigo.py' `
        (Test-Path (Join-Path $demo $relScript)) 'el script no se instalo'
    Assert-Verdadero 'E-18 y mapa-codigo.py sigue ahi' `
        (Test-Path (Join-Path $demo '.claude\harness\bin\mapa-codigo.py')) `
        'se movio el mapa'

    # E-18: el lockfile lo inventaria. Sin eso, -Update no lo actualiza y -Uninstall no
    # se lo lleva: queda un archivo huerfano que nadie sabe de donde salio.
    $lock = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.lock.json')) |
            ConvertFrom-Json
    $enLock = @($lock.archivos | Where-Object { $_.ruta -eq $relSchema })
    Assert-Igual 'E-18 el schema figura una vez en el lockfile' 1 $enLock.Count
    Assert-Verdadero 'E-18 y con su SHA256' `
        ($enLock.Count -eq 1 -and -not [string]::IsNullOrWhiteSpace($enLock[0].sha256)) `
        'el schema quedo en el lockfile sin hash'

    # -- -Update lo vuelve a dejar ---------------------------------------------------
    if (Test-Path $rutaSchema) { Remove-Item $rutaSchema -Force }
    $r = Invoke-InstaladorCtx @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-18 -Update repone el schema borrado' `
        (Test-Path $rutaSchema) 'el -Update no lo repuso'

    # -- Y -Uninstall se lo lleva ----------------------------------------------------
    $r = Invoke-InstaladorCtx @('-Project', $demo, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-18 -Uninstall se lleva el schema' `
        (-not (Test-Path $rutaSchema)) 'el schema sobrevivio a -Uninstall'
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}
