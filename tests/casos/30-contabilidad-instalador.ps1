# E-39 de docs/cambios/bloque-4-contabilidad-de-ejecucion/spec.md.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y no ponerlos es
# la otra mitad de la regla que declara 00-encoding-fuentes.ps1.
#
# El test de python controla que los archivos cuelguen de lo que el instalador copia. Esto
# instala de verdad: es la unica forma de decir que el bloque LLEGA a un proyecto.

Set-Grupo 'Instalador - la contabilidad de ejecucion'

$instaladorCont = Join-Path $script:Raiz 'install.ps1'

function Invoke-InstaladorCont {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorCont @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

$demoCont = Join-Path ([System.IO.Path]::GetTempPath()) `
                      ('harness-cont-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $demoCont -Force | Out-Null
[System.IO.File]::WriteAllText((Join-Path $demoCont 'CLAUDE.md'), "# Proyecto de prueba`r`n")

try {
    $r = Invoke-InstaladorCont @('-Project', $demoCont, '-Harness', 'desarrollo',
                                 '-Usuario', 'Ana Prueba')
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    # -- E-39: el paquete entero, con sus adaptadores -------------------------------

    $dirCont = Join-Path $demoCont '.claude\harness\bin\desarrollo\contabilidad'
    foreach ($modulo in @('__init__.py', 'eventos.py', 'libro.py', 'agregacion.py',
                          'costos.py', 'tiempo.py', 'presupuesto.py', 'reporte.py',
                          'barra.py')) {
        Assert-Verdadero "E-39 el modulo $modulo quedo instalado" `
            (Test-Path (Join-Path $dirCont $modulo)) "falta $modulo"
    }

    $dirAdap = Join-Path $dirCont 'adaptadores'
    foreach ($modulo in @('__init__.py', 'contrato.py', 'registro.py', 'claude_code.py',
                          'codex.py')) {
        Assert-Verdadero "E-39 el adaptador $modulo quedo instalado" `
            (Test-Path (Join-Path $dirAdap $modulo)) "falta adaptadores\$modulo"
    }

    # Los dos schemas, byte a byte como estan en el repositorio.
    foreach ($schema in @('execution-accounting-event.schema.json', 'budget-policy.schema.json')) {
        $instalado = Join-Path $demoCont ".claude\harness\schemas\$schema"
        Assert-Verdadero "E-39 $schema quedo instalado" (Test-Path $instalado) "falta $schema"
        if (Test-Path $instalado) {
            Assert-Igual "E-39 $schema es el del repositorio, byte a byte" `
                ([System.IO.File]::ReadAllText((Join-Path $script:Raiz "comun\schemas\$schema"))) `
                ([System.IO.File]::ReadAllText($instalado))
        }
    }

    # -- E-39: y corre desde ahi ----------------------------------------------------

    # Una transcripcion minima con la trampa adentro: dos lineas del mismo mensaje.
    $fuente = Join-Path $demoCont 'sesion.jsonl'
    $linea = '{"type":"assistant","sessionId":"s-1","timestamp":"2026-09-20T10:00:00",' +
             '"message":{"id":"msg_1","model":"m-1","usage":{"input_tokens":10,' +
             '"output_tokens":100,"cache_read_input_tokens":5000,' +
             '"cache_creation_input_tokens":200}}}'
    [System.IO.File]::WriteAllText($fuente, ($linea + "`n" + $linea + "`n"))

    $cli = Join-Path $demoCont '.claude\harness\bin\desarrollo\dev-harness.py'
    Assert-Verdadero 'E-39 la CLI quedo instalada' (Test-Path $cli) 'falta dev-harness.py'

    $salida = & python $cli contabilidad 'GCBA-1' '--ingerir' $fuente '--reporte' `
                       '--proyecto' $demoCont 2>&1 | Out-String
    Assert-Igual 'E-39 contabilidad sale con codigo 0' 0 $LASTEXITCODE

    $dirLibro = Join-Path $demoCont '.claude\runtime\accounting\GCBA-1'
    foreach ($archivo in @('ledger.jsonl', 'summary.json', 'execution-cost.md')) {
        Assert-Verdadero "E-39 se escribio $archivo desde el proyecto instalado" `
            (Test-Path (Join-Path $dirLibro $archivo)) "falta $archivo"
    }

    # La trampa del doble conteo tambien vale instalado: dos lineas, un mensaje, 100 tokens.
    $resumen = Get-Content (Join-Path $dirLibro 'summary.json') -Raw | ConvertFrom-Json
    Assert-Igual 'E-39 el output no se conto dos veces' 100 $resumen.tokens.outputTokens
    Assert-Igual 'E-39 y la ventana es una foto' 5210 $resumen.context.contextTokens

    # -- E-56 de docs/cambios/reporte-de-seguridad/spec.md: el reporte llega ------

    $lockSeg = Get-Content (Join-Path $demoCont '.claude\harness.lock.json') -Raw | ConvertFrom-Json
    $rutasLock = @($lockSeg.archivos | ForEach-Object { $_.ruta })
    $esperadosSeg = @(
        '.claude\harness\bin\desarrollo\reporte_seguridad\__init__.py',
        '.claude\harness\bin\desarrollo\reporte_seguridad\libro.py',
        '.claude\harness\bin\desarrollo\reporte_seguridad\productores.py',
        '.claude\harness\bin\desarrollo\reporte_seguridad\resumen.py',
        '.claude\harness\bin\desarrollo\reporte_seguridad\reporte.py',
        '.claude\harness\reglas\desarrollo\security-report-domains.json',
        '.claude\harness\schemas\security-ledger-event.schema.json',
        '.claude\harness\schemas\security-summary.schema.json',
        '.claude\harness\schemas\security-report.schema.json')
    foreach ($esperado in $esperadosSeg) {
        Assert-Verdadero "E-56 $esperado esta en el lockfile" ($rutasLock -contains $esperado) `
            "el lockfile no lista $esperado"
        Assert-Verdadero "E-56 $esperado quedo instalado" `
            (Test-Path (Join-Path $demoCont $esperado)) "falta $esperado"
    }

    # Y corre desde el arbol instalado: la matriz, los dominios y los schemas se encuentran ahi.
    $salida = & python $cli seguridad 'GCBA-1' '--reporte' '--proyecto' $demoCont 2>&1 | Out-String
    Assert-Igual 'E-56 seguridad corre desde el proyecto instalado' 0 $LASTEXITCODE
    $dirSeg = Join-Path $demoCont '.claude\runtime\security\GCBA-1'
    foreach ($archivo in @('security-summary.json', 'security-status.md', 'security-status.html')) {
        Assert-Verdadero "E-56 se escribio $archivo desde el proyecto instalado" `
            (Test-Path (Join-Path $dirSeg $archivo)) "falta $archivo"
    }

    # -- E-39: el libro sobrevive a un -Update y a un -Uninstall -------------------

    $r = Invoke-InstaladorCont @('-Project', $demoCont, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-39 -Update no borra el libro contable' `
        (Test-Path (Join-Path $dirLibro 'ledger.jsonl')) 'el -Update se llevo el ledger'

    $r = Invoke-InstaladorCont @('-Project', $demoCont, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo
    Assert-Verdadero 'E-39 -Uninstall tampoco lo borra' `
        (Test-Path (Join-Path $dirLibro 'ledger.jsonl')) 'el -Uninstall se llevo el ledger'
    Assert-Verdadero 'E-39 -Uninstall si se lleva el paquete' `
        (-not (Test-Path $dirCont)) 'el paquete sobrevivio al -Uninstall'
}
finally {
    if (Test-Path $demoCont) {
        Remove-Item $demoCont -Recurse -Force -ErrorAction SilentlyContinue
    }
}
