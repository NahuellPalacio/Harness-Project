# Ciclo completo del instalador sobre un proyecto descartable:
#   -WhatIf -> -Install -> -Doctor -> editar a mano -> -Update -> -Uninstall
#
# Lo que realmente se verifica en cada paso es la promesa que el README le hace a quien
# instala esto en su máquina:
#   · -WhatIf no escribe un byte
#   · lo que el humano tiene en CLAUDE.md y .gitignore no se toca nunca
#   · -Update no pisa en silencio lo que alguien editó
#   · -Uninstall deja el proyecto exactamente como estaba

Set-Grupo 'Instalador — ciclo completo'

$instalador = Join-Path $script:Raiz 'install.ps1'
$demo       = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-test-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))

# Contenido del humano: tiene que sobrevivir a todo el ciclo, intacto.
$claudeHumano = "# CLAUDE.md - Proyecto de prueba`r`n`r`nEsta linea es del humano y no se debe tocar.`r`n"
$gitHumano    = "node_modules/`r`n"

# El harness trata a la persona por su nombre. Los tests corren con stdin redirigido, asi
# que no hay consola para preguntarlo: va por parametro.
$usuarioPrueba = 'Ana Prueba'

function Invoke-Instalador {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instalador @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

try {
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'),  $claudeHumano)
    [System.IO.File]::WriteAllText((Join-Path $demo '.gitignore'), $gitHumano)

    $idHarness = 'analisis'
    if (-not (Test-Path (Join-Path $script:Raiz "harnesses\$idHarness\manifest.json"))) {
        Assert-Verdadero 'existe un harness para probar' $false "falta harnesses\$idHarness"
        return
    }

    # ── -WhatIf no escribe nada ─────────────────────────────────────────────────
    # A proposito SIN -Usuario: como no escribe nada, no puede exigir nada. Ver que
    # alguien va a hacer antes de decidirse tiene que costar cero requisitos.
    $r = Invoke-Instalador @('-Project', $demo, '-Harness', $idHarness, '-WhatIf')
    Assert-Igual '-WhatIf sale con codigo 0 sin pedir el nombre' 0 $r.Codigo
    Assert-Verdadero '-WhatIf no crea .claude' (-not (Test-Path (Join-Path $demo '.claude'))) `
        'escribio algo cuando prometio no escribir nada'

    # ── Instalar ────────────────────────────────────────────────────────────────
    $r = Invoke-Instalador @('-Project', $demo, '-Harness', $idHarness, '-Usuario', $usuarioPrueba)
    Assert-Igual 'la instalacion sale con codigo 0' 0 $r.Codigo
    Assert-Contiene 'verifica que los hooks responden' 'los cuatro hooks responden' $r.Salida

    Assert-Verdadero 'genera settings.json'        (Test-Path (Join-Path $demo '.claude\settings.json'))
    Assert-Verdadero 'genera el lockfile'          (Test-Path (Join-Path $demo '.claude\harness.lock.json'))
    Assert-Verdadero 'genera harness.config.json'  (Test-Path (Join-Path $demo '.claude\harness.config.json'))
    Assert-Verdadero 'genera el lanzador de hooks' (Test-Path (Join-Path $demo '.claude\harness\run-hook.cmd'))

    # El settings.json tiene que ser JSON valido: si no, Claude Code lo ignora entero
    # y el harness queda instalado pero muerto.
    $settingsOk = $true
    $settings = $null
    try {
        $settings = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\settings.json')) | ConvertFrom-Json
    } catch { $settingsOk = $false }
    Assert-Verdadero 'el settings.json generado es JSON valido' $settingsOk

    if ($settingsOk) {
        Assert-Verdadero 'registra los cuatro eventos de hook' `
            ($settings.hooks.PSObject.Properties.Name.Count -eq 4)
        Assert-Contiene 'el comando del hook no lleva ruta absoluta' `
            '$CLAUDE_PROJECT_DIR' $settings.hooks.PostToolUse[0].hooks[0].command
        Assert-Verdadero 'carga las reglas de deny de secretos' `
            ($settings.permissions.deny.Count -gt 0)
    }

    # El lockfile tiene que traer el SHA256 de cada archivo: es lo que hace detectable
    # la deriva entre proyectos, que es la contra de haber elegido copia (ADR-0002).
    $lock = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.lock.json')) | ConvertFrom-Json
    Assert-Verdadero 'el lockfile inventaria archivos' ($lock.archivos.Count -gt 0)
    $sinHash = @($lock.archivos | Where-Object { -not $_.sha256 })
    Assert-Verdadero 'todos los archivos del lockfile tienen SHA256' ($sinHash.Count -eq 0)

    # Lo del humano, intacto.
    $claudeAhora = [System.IO.File]::ReadAllText((Join-Path $demo 'CLAUDE.md'))
    Assert-Contiene 'conserva la linea del humano en CLAUDE.md' 'Esta linea es del humano' $claudeAhora
    Assert-Contiene 'inyecta su bloque marcado en CLAUDE.md'    'HARNESS:COMUN'            $claudeAhora
    Assert-Contiene 'conserva lo del humano en .gitignore' 'node_modules/' `
        ([System.IO.File]::ReadAllText((Join-Path $demo '.gitignore')))

    # El nombre queda guardado y el harness trata a la persona por el.
    $config = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.config.json')) | ConvertFrom-Json
    Assert-Igual 'guarda el nombre de quien lo usa' $usuarioPrueba $config.usuario

    # Sin -Usuario y sin consola para preguntarlo, tiene que abortar explicando en vez de
    # colgarse esperando una respuesta que nadie puede dar.
    $otro = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-sinusuario-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $otro -Force | Out-Null
    try {
        $r = Invoke-Instalador @('-Project', $otro, '-Harness', $idHarness)
        Assert-Igual 'sin -Usuario y sin consola, aborta' 1 $r.Codigo
        Assert-Contiene 'y el error dice como resolverlo' '-Usuario' $r.Salida
        Assert-Verdadero 'y no dejo el proyecto a medio instalar' `
            (-not (Test-Path (Join-Path $otro '.claude\harness.lock.json')))
    }
    finally { Remove-Item $otro -Recurse -Force -ErrorAction SilentlyContinue }

    # Errar la ruta del proyecto es el primer error que comete cualquiera, y desde Git Bash
    # alcanza con olvidar las comillas simples para que las barras invertidas desaparezcan.
    # El error tiene que nombrar la ruta, no la propiedad de un $null.
    $noExiste = Join-Path ([System.IO.Path]::GetTempPath()) ('no-existe-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 6))
    $r = Invoke-Instalador @('-Project', $noExiste, '-Harness', $idHarness, '-Usuario', $usuarioPrueba)
    $plano = ($r.Salida -replace "\r?\n", '')
    Assert-Igual 'una ruta de proyecto inexistente aborta' 1 $r.Codigo
    Assert-Contiene 'y el error dice que el proyecto no existe' 'el proyecto no existe' $plano
    Assert-Contiene 'y nombra la ruta que se paso' $noExiste $plano
    Assert-Verdadero 'y no filtra el error de PowerShell sobre un $null' `
        ($plano -notmatch "propiedad 'Path'") $plano

    # Los assets del harness tienen que llegar a donde Claude Code los lee de verdad:
    # .claude\skills\ y .claude\agents\, no adentro de .claude\harness\.
    $skillsInstaladas = @(Get-ChildItem (Join-Path $demo '.claude\skills') -Recurse -Filter 'SKILL.md' -ErrorAction SilentlyContinue)
    $agentesInstalados = @(Get-ChildItem (Join-Path $demo '.claude\agents') -Filter '*.md' -ErrorAction SilentlyContinue)

    # Se cuentan los de comun MAS los del harness: comun tambien aporta skills y agentes.
    $skillsEnRepo = @(
        @(Get-ChildItem (Join-Path $script:Raiz 'comun\skills') -Recurse -Filter 'SKILL.md' -ErrorAction SilentlyContinue) +
        @(Get-ChildItem (Join-Path $script:Raiz "harnesses\$idHarness\skills") -Recurse -Filter 'SKILL.md' -ErrorAction SilentlyContinue)
    )
    $agentesEnRepo = @(
        @(Get-ChildItem (Join-Path $script:Raiz 'comun\agents') -Filter '*.md' -ErrorAction SilentlyContinue) +
        @(Get-ChildItem (Join-Path $script:Raiz "harnesses\$idHarness\agents") -Filter '*.md' -ErrorAction SilentlyContinue)
    )

    Assert-Igual 'instala todas las skills, de comun y del harness'  $skillsEnRepo.Count  $skillsInstaladas.Count
    Assert-Igual 'instala todos los agentes, de comun y del harness' $agentesEnRepo.Count $agentesInstalados.Count

    # Un agente sin tools declaradas hereda escritura y ejecucion total. En un harness que
    # se instala en 12 repos de un organismo publico, eso no puede pasar por descuido.
    $sinTools = @($agentesInstalados | Where-Object {
        [System.IO.File]::ReadAllText($_.FullName) -notmatch '(?m)^tools:'
    })
    Assert-Verdadero 'todos los agentes instalados declaran tools:' ($sinTools.Count -eq 0) `
        ("sin declarar: " + (($sinTools | Select-Object -ExpandProperty Name) -join ', '))

    # Instalar dos veces seguidas tiene que dar lo mismo que instalar una.
    Invoke-Instalador @('-Project', $demo, '-Harness', $idHarness, '-Usuario', $usuarioPrueba) | Out-Null
    $claudeDosVeces = [System.IO.File]::ReadAllText((Join-Path $demo 'CLAUDE.md'))
    $bloques = ([regex]::Matches($claudeDosVeces, 'HARNESS:COMUN')).Count
    Assert-Igual 'reinstalar no duplica el bloque en CLAUDE.md' 2 $bloques

    # ── Deriva ──────────────────────────────────────────────────────────────────
    $hookEditado = Join-Path $demo '.claude\harness\hooks\post-tool-use.ps1'
    Add-Content -Path $hookEditado -Value '# editado a mano' -Encoding UTF8

    $r = Invoke-Instalador @('-Doctor', '-Project', $demo)
    Assert-Contiene '-Doctor detecta el archivo editado a mano' 'editados a mano' $r.Salida

    # ── -Update respeta lo editado ──────────────────────────────────────────────
    $r = Invoke-Instalador @('-Project', $demo, '-Update')
    Assert-Igual '-Update sale con codigo 0' 0 $r.Codigo
    Assert-Contiene 'la version editada sobrevive al -Update' 'editado a mano' `
        ([System.IO.File]::ReadAllText($hookEditado))
    Assert-Verdadero 'la version nueva queda al lado como .nuevo' (Test-Path ($hookEditado + '.nuevo'))

    # ── -Uninstall deja el proyecto como estaba ─────────────────────────────────
    $r = Invoke-Instalador @('-Project', $demo, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo

    # Las zonas que el instalador creo y nadie lleno se sacan; si tuvieran contenido se
    # quedarian, porque adentro estaria el trabajo de alguien.
    Assert-Igual 'CLAUDE.md vuelve a ser exactamente el del humano' `
        $claudeHumano.Trim() ([System.IO.File]::ReadAllText((Join-Path $demo 'CLAUDE.md')).Trim())
    Assert-Igual '.gitignore vuelve a ser exactamente el del humano' `
        $gitHumano.Trim() ([System.IO.File]::ReadAllText((Join-Path $demo '.gitignore')).Trim())

    Assert-Verdadero 'no queda el lockfile'  (-not (Test-Path (Join-Path $demo '.claude\harness.lock.json')))
    Assert-Verdadero 'no queda settings.json' (-not (Test-Path (Join-Path $demo '.claude\settings.json')))
    Assert-Verdadero 'no quedan archivos .nuevo huerfanos' `
        (@(Get-ChildItem $demo -Recurse -File -Filter '*.nuevo' -ErrorAction SilentlyContinue).Count -eq 0)

    # Lo que SI tiene que sobrevivir a una desinstalacion.
    Assert-Verdadero 'conserva harness.config.json, que es del humano' `
        (Test-Path (Join-Path $demo '.claude\harness.config.json'))
    Assert-Verdadero 'conserva los backups' `
        (Test-Path (Join-Path $demo '.claude\.harness-backup'))
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}
