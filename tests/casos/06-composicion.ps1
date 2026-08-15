# Dos harness en el mismo proyecto.
#
# El README promete que un proyecto puede tener los dos a la vez, y que eso es lo que va a
# pasar cuando un repo de relevamiento reciba su primer codigo. Ese escenario es incremental
# por naturaleza: primero analisis, y desarrollo despues.
#
# Lo que se verifica es que el segundo -Harness NO borre al primero, ni del CLAUDE.md, ni del
# lockfile, ni del inventario que -Doctor y -Uninstall usan.
#
# Este archivo se escribe en ASCII puro a proposito: sin caracteres no ASCII no hace falta
# BOM, y no puede fallar por la trampa de encoding de PowerShell 5.1.

Set-Grupo 'Composicion - dos harness en el mismo proyecto'

$instalador = Join-Path $script:Raiz 'install.ps1'
$demo = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-comp-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))

$usuarioPrueba = 'Ana Prueba'

# Frases sin acentos, tomadas del bloque de CLAUDE.md de cada harness. Son la evidencia de
# que las reglas de ese harness llegaron al archivo.
$marcaAnalisis   = 'La maqueta manda'
$marcaDesarrollo = 'por nombre DNS'

function Invoke-InstaladorComp {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instalador @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

try {
    $faltan = @()
    foreach ($id in @('analisis', 'desarrollo')) {
        if (-not (Test-Path (Join-Path $script:Raiz "harnesses\$id\manifest.json"))) { $faltan += $id }
    }
    if ($faltan.Count -gt 0) {
        Assert-Verdadero 'existen los dos harness para probar' $false ('faltan: ' + ($faltan -join ', '))
        return
    }

    New-Item -ItemType Directory -Path $demo -Force | Out-Null

    # -- Los dos juntos, en un solo comando --------------------------------------
    # Es la forma que ya funcionaba. Se verifica primero para que un fallo de la parte
    # incremental no se confunda con que la composicion no existe.
    $r = Invoke-InstaladorComp @('-Project', $demo, '-Harness', 'analisis,desarrollo', '-Usuario', $usuarioPrueba)
    Assert-Igual 'instalar los dos juntos sale con codigo 0' 0 $r.Codigo

    $claude = [System.IO.File]::ReadAllText((Join-Path $demo 'CLAUDE.md'))
    Assert-Contiene 'juntos: el CLAUDE.md trae las reglas de analisis'   $marcaAnalisis   $claude
    Assert-Contiene 'juntos: el CLAUDE.md trae las reglas de desarrollo' $marcaDesarrollo $claude

    $lock = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.lock.json')) | ConvertFrom-Json
    Assert-Verdadero 'juntos: el lock lista analisis'   ($lock.harness -contains 'analisis')
    Assert-Verdadero 'juntos: el lock lista desarrollo' ($lock.harness -contains 'desarrollo')

    Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $demo -Force | Out-Null

    # -- Incremental: primero analisis, desarrollo despues -----------------------
    $r = Invoke-InstaladorComp @('-Project', $demo, '-Harness', 'analisis', '-Usuario', $usuarioPrueba)
    Assert-Igual 'instalar analisis sale con codigo 0' 0 $r.Codigo

    $lockAntes = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.lock.json')) | ConvertFrom-Json
    $archivosAntes = @($lockAntes.archivos | ForEach-Object { $_.ruta })
    $skillAnalisis = @($archivosAntes | Where-Object { $_ -like '*hu-escribir*' })
    Assert-Verdadero 'analisis dejo su skill en el inventario' ($skillAnalisis.Count -gt 0)

    # El segundo harness, SIN nombrar al primero. Es el caso real: el repo ya tenia analisis
    # y recibe su primer codigo meses despues.
    $r = Invoke-InstaladorComp @('-Project', $demo, '-Harness', 'desarrollo', '-Usuario', $usuarioPrueba)
    Assert-Igual 'agregar desarrollo despues sale con codigo 0' 0 $r.Codigo

    # Conservar en silencio es tan sorpresivo como borrar en silencio: quien pidio un solo
    # harness tiene que enterarse de que el proyecto queda con dos.
    Assert-Contiene 'avisa que conserva el harness que ya estaba' 'ya instalado' $r.Salida

    # -- Lo que no se puede haber perdido ----------------------------------------
    $claude = [System.IO.File]::ReadAllText((Join-Path $demo 'CLAUDE.md'))
    Assert-Contiene 'el segundo harness no borra las reglas del primero' $marcaAnalisis   $claude
    Assert-Contiene 'y suma las suyas al mismo bloque'                   $marcaDesarrollo $claude

    $lockDespues = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.lock.json')) | ConvertFrom-Json
    Assert-Verdadero 'el lock conserva analisis'    ($lockDespues.harness -contains 'analisis')
    Assert-Verdadero 'el lock suma desarrollo'      ($lockDespues.harness -contains 'desarrollo')
    Assert-Verdadero 'el lock conserva comun'       ($lockDespues.harness -contains 'comun')

    # El orden no puede depender del camino. Instalar los dos juntos y llegar al mismo
    # conjunto en dos pasos tienen que producir el MISMO archivo: si no, el bloque del
    # CLAUDE.md cambia de orden segun como se llego, y un -Update produce un diff fantasma.
    Assert-Igual 'el orden del lock es canonico, no el de instalacion' `
        'comun,analisis,desarrollo' ($lockDespues.harness -join ',')

    $posAnalisis   = $claude.IndexOf($marcaAnalisis)
    $posDesarrollo = $claude.IndexOf($marcaDesarrollo)
    Assert-Verdadero 'y el bloque del CLAUDE.md sigue ese mismo orden' `
        ($posAnalisis -lt $posDesarrollo) `
        "analisis en $posAnalisis, desarrollo en $posDesarrollo"

    # Un archivo instalado que queda fuera del inventario es un huerfano: -Doctor deja de
    # vigilarlo y -Uninstall no lo borra. Es la parte silenciosa del problema.
    $archivosDespues = @($lockDespues.archivos | ForEach-Object { $_.ruta })
    $huerfanos = @($skillAnalisis | Where-Object { $archivosDespues -notcontains $_ })
    Assert-Verdadero 'la skill de analisis sigue inventariada' ($huerfanos.Count -eq 0) `
        ('quedaron fuera del lockfile: ' + ($huerfanos -join ', '))

    # El bloque se reemplaza, no se acumula: una sola marca de apertura.
    $marcas = ([regex]::Matches($claude, 'HARNESS:COMUN')).Count
    Assert-Igual 'el bloque marcado sigue siendo uno solo' 2 $marcas

    # -- -Update despues de componer mantiene los dos ----------------------------
    $r = Invoke-InstaladorComp @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo

    $claude = [System.IO.File]::ReadAllText((Join-Path $demo 'CLAUDE.md'))
    Assert-Contiene '-Update conserva las reglas de analisis'   $marcaAnalisis   $claude
    Assert-Contiene '-Update conserva las reglas de desarrollo' $marcaDesarrollo $claude
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}
