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
            '$env:CLAUDE_PROJECT_DIR' $settings.hooks.PostToolUse[0].hooks[0].command
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
    $hookEditado = Join-Path $demo '.claude\harness\hooks\post-tool-use.py'
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

    # E-26: -Uninstall saca los .py de los hooks y los dos shims.
    Assert-Verdadero 'E-26 no queda run-hook.cmd' (-not (Test-Path (Join-Path $demo '.claude\harness\run-hook.cmd')))
    Assert-Verdadero 'E-26 no queda run-hook.sh'  (-not (Test-Path (Join-Path $demo '.claude\harness\run-hook.sh')))
    Assert-Verdadero 'E-26 no quedan hooks .py'   `
        (@(Get-ChildItem $demo -Recurse -File -Filter '*.py' -ErrorAction SilentlyContinue).Count -eq 0)

    # Lo que SI tiene que sobrevivir a una desinstalacion.
    Assert-Verdadero 'conserva harness.config.json, que es del humano' `
        (Test-Path (Join-Path $demo '.claude\harness.config.json'))
    Assert-Verdadero 'conserva los backups' `
        (Test-Path (Join-Path $demo '.claude\.harness-backup'))
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}


# ── -Doctor sin Python ───────────────────────────────────────────────────────────
#
# -Doctor es la herramienta que diagnostica una máquina rota: si dependiera de lo que
# diagnostica, no arrancaría justo cuando hace falta (E-23). Y esa garantía solo vale si
# nada en el nivel superior del script -lo que corre para CUALQUIER verbo, -Doctor
# incluido- invoca Python (E-23b): una dependencia en la línea 58, diagnóstico muerto
# antes de imprimir la primera línea, sin importar cuán prolijo sea el resto.

Set-Grupo 'Instalador - Doctor sin Python'

$comandoDoctorSinPython = "`$env:PATH = 'C:\no-existe'; & '$instalador' -Doctor 2>&1 | Out-String"
$salidaSinPython = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                                    -Command $comandoDoctorSinPython | Out-String

Assert-Contiene 'E-23 imprime el diagnostico completo' 'PowerShell' $salidaSinPython
Assert-Contiene 'E-23 reporta la falta de Python'       'Python'    $salidaSinPython
Assert-Contiene 'E-23 dice que hacer'                   'instala'  $salidaSinPython

$primeraFuncion = (Select-String -Path $instalador -Pattern '^function ' | Select-Object -First 1).LineNumber
$cabecera = (Get-Content $instalador -TotalCount $primeraFuncion) -join "`n"
Assert-Vacio 'E-23b sin zonas.py ni Resolve-Python en el nivel superior' `
    (($cabecera | Select-String -Pattern 'zonas\.py|Resolve-Python') -join '')


# ── Version minima de Python (E-24) ──────────────────────────────────────────────
#
# Un Python viejo alcanzado en el PATH es una FALLA, no un aviso: los hooks no van a
# correr igual. El mínimo vive en comun/manifest.json, junto a requiereClaudeCode. Se
# prueba con dot-source -no un -Doctor real- porque hace falta simular una versión que
# la máquina que corre la suite probablemente no tenga instalada.

Set-Grupo 'Instalador - version minima de Python'

function Invoke-TestEntornoSimulado {
    param([string] $VersionPython)
    $codigoHijo = @"
. '$instalador'
`$hallazgos = Test-Entorno -PythonSimulado '$VersionPython'
`$hallazgos | ConvertTo-Json -Depth 5 -Compress
"@
    $json = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command $codigoHijo | Out-String
    return @($json | ConvertFrom-Json)
}

$hallazgosViejo = Invoke-TestEntornoSimulado -VersionPython '3.6'
$fallaViejo = @($hallazgosViejo | Where-Object { $_.Nivel -eq 'falla' -and $_.Texto -match 'Python' })
Assert-Igual    'E-24 un Python 3.6 es una falla, no un aviso' 1     $fallaViejo.Count
Assert-Contiene 'E-24 el mensaje dice cual es el minimo'       '3.9' $fallaViejo[0].Texto

$hallazgosNuevo = Invoke-TestEntornoSimulado -VersionPython '3.11'
$fallaNuevo = @($hallazgosNuevo | Where-Object { $_.Nivel -eq 'falla' -and $_.Texto -match 'Python' })
Assert-Igual 'E-24 un Python por encima del minimo no falla' 0 $fallaNuevo.Count


# ── Shims: el interprete real y el POSIX en LF (E-21, E-22) ─────────────────────

Set-Grupo 'Instalador - shims'

$demoShim = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-shim-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
try {
    New-Item -ItemType Directory -Path $demoShim -Force | Out-Null
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $instalador `
                     -Project $demoShim -Harness analisis -Usuario 'Prueba Shim' | Out-Null
    Assert-Igual 'instala para probar los shims' 0 $LASTEXITCODE

    $rutaCmd = Join-Path $demoShim '.claude\harness\run-hook.cmd'
    $txtCmd = [System.IO.File]::ReadAllText($rutaCmd)
    Assert-Vacio    'E-21 el shim no invoca powershell'         (($txtCmd | Select-String 'powershell\.exe') -join '')
    Assert-Contiene 'E-21 el shim lleva un .exe'                '.exe' $txtCmd
    $exe = ([regex]::Match($txtCmd, '"([^"]+\.exe)"')).Groups[1].Value
    Assert-Verdadero 'E-21 el .exe resuelto existe'             (Test-Path $exe)
    Assert-Verdadero 'E-21 no es el shim suelto de PyManager'   ($exe -notmatch '\\PyManager\\')

    $rutaSh = Join-Path $demoShim '.claude\harness\run-hook.sh'
    Assert-Verdadero 'E-22 se genera run-hook.sh' (Test-Path $rutaSh)
    $bytesSh = [System.IO.File]::ReadAllBytes($rutaSh)
    Assert-Igual     'E-22 ningun CR en el shim POSIX' 0 (@($bytesSh | Where-Object { $_ -eq 13 }).Count)
    Assert-Contiene  'E-22 invoca python3' 'python3' ([System.IO.File]::ReadAllText($rutaSh))
}
finally {
    if (Test-Path $demoShim) { Remove-Item $demoShim -Recurse -Force -ErrorAction SilentlyContinue }
}


# ── -Update no deja huerfanos .ps1 (E-25) ────────────────────────────────────────
#
# Un proyecto instalado con una versión vieja del harness -cuando los hooks todavía eran
# .ps1- no puede quedar con esos .ps1 sueltos después de actualizar: el manifiesto nuevo
# ya no los genera, y -Update tiene que sacar lo que sobra.

Set-Grupo 'Instalador - Update sin huerfanos'

$demoUpdate = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-update-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
try {
    New-Item -ItemType Directory -Path $demoUpdate -Force | Out-Null
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $instalador `
                     -Project $demoUpdate -Harness analisis -Usuario 'Prueba Update' | Out-Null

    # Simula lo que dejaría una instalación de una versión anterior a la migración a Python.
    New-Item -ItemType File -Path (Join-Path $demoUpdate '.claude\harness\hooks\pre-tool-use.ps1') -Force | Out-Null

    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $instalador `
                     -Project $demoUpdate -Update | Out-Null

    $huerfanos = @(Get-ChildItem (Join-Path $demoUpdate '.claude\harness') -Recurse -Filter '*.ps1' -ErrorAction SilentlyContinue)
    Assert-Igual 'E-25 -Update no deja ningun .ps1 huerfano' 0 $huerfanos.Count

    Assert-Verdadero 'E-25 conserva harness.config.json' (Test-Path (Join-Path $demoUpdate '.claude\harness.config.json'))
    Assert-Verdadero 'E-25 conserva los backups'          (Test-Path (Join-Path $demoUpdate '.claude\.harness-backup'))
}
finally {
    if (Test-Path $demoUpdate) { Remove-Item $demoUpdate -Recurse -Force -ErrorAction SilentlyContinue }
}


# ── -Uninstall sin Python (E-26b) ─────────────────────────────────────────────────
#
# -Uninstall es la herramienta que corre justo cuando algo anda mal, y "el Python que el
# instalador fijó ya no está" es uno de los motivos por los que alguien la usaría. No puede
# depender de lo mismo que el harness necesita para andar: la única parte que usa Python es
# la limpieza de zonas del CLAUDE.md, y esa es la única que se saltea si no hay intérprete
# -avisando qué quedó sin hacer y por qué- nunca abortando la desinstalación entera.

Set-Grupo 'Instalador - Uninstall sin Python'

$demoUninstSinPython = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-uninst-sp-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
try {
    New-Item -ItemType Directory -Path $demoUninstSinPython -Force | Out-Null
    # Un CLAUDE.md previo, para que la instalación deje un backup de verdad que verificar.
    [System.IO.File]::WriteAllText((Join-Path $demoUninstSinPython 'CLAUDE.md'), "# CLAUDE.md previo`r`n")

    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $instalador `
                     -Project $demoUninstSinPython -Harness analisis -Usuario 'Prueba Sin Python' | Out-Null

    $comandoDesinstalarSinPython = "`$env:PATH = 'C:\no-existe'; & '$instalador' -Project '$demoUninstSinPython' -Uninstall 2>&1 | Out-String"
    $salidaDesinstalar = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                                          -Command $comandoDesinstalarSinPython | Out-String
    $codigoDesinstalar = $LASTEXITCODE

    Assert-Igual 'E-26b -Uninstall sin Python no aborta' 0 $codigoDesinstalar
    Assert-Verdadero 'E-26b saca los .py' `
        (@(Get-ChildItem $demoUninstSinPython -Recurse -Filter '*.py' -ErrorAction SilentlyContinue).Count -eq 0)
    Assert-Verdadero 'E-26b saca run-hook.cmd' `
        (-not (Test-Path (Join-Path $demoUninstSinPython '.claude\harness\run-hook.cmd')))
    Assert-Verdadero 'E-26b saca run-hook.sh' `
        (-not (Test-Path (Join-Path $demoUninstSinPython '.claude\harness\run-hook.sh')))
    Assert-Verdadero 'E-26b conserva harness.config.json' `
        (Test-Path (Join-Path $demoUninstSinPython '.claude\harness.config.json'))
    Assert-Verdadero 'E-26b conserva los backups' `
        (Test-Path (Join-Path $demoUninstSinPython '.claude\.harness-backup'))
    Assert-Contiene 'E-26b avisa que no pudo limpiar las zonas, y por que' 'Python' $salidaDesinstalar
}
finally {
    if (Test-Path $demoUninstSinPython) { Remove-Item $demoUninstSinPython -Recurse -Force -ErrorAction SilentlyContinue }
}


# ── -Doctor mide la latencia de un hook (E-25b) ──────────────────────────────────
#
# El p50 de un hook real sobre un payload real es el numero que justifica todo este
# cambio -Python en vez de PowerShell-. Si nadie lo mide, la promesa de latencia queda
# en intencion. -Doctor nunca bloquea por esto: informa, y avisa si pasa el umbral.

Set-Grupo 'Instalador - Doctor mide latencia'

$rDoctorLatencia = Invoke-Instalador @('-Doctor')
Assert-Contiene 'E-25b reporta latencia' 'latencia de hook' $rDoctorLatencia.Salida
Assert-Igual    'E-25b no bloquea'       0                  $rDoctorLatencia.Codigo


# ── -Update que falla no puede destruir antes de saber que puede construir ───────
#
# Hallazgo del revisor: E-25 (arriba) borra .claude\harness\ ANTES de reinstalar. Si
# Invoke-Instalar tira por cualquier motivo que no sea "los hooks no responden" -falta
# Python, zonas.py falla, un id invalido, prefijos repetidos: todos usan throw- esa
# excepcion se propaga y el borrado nunca se deshace. El proyecto queda sin harness, y
# lo que el humano habia editado a mano -que solo vivia en la variable $guardados de ese
# proceso- se pierde para siempre. Un -Update que falla tiene que dejar el proyecto como
# estaba, no a mitad de camino.

Set-Grupo 'Instalador - Update que falla no destruye'

$demoUpdateFalla = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-update-falla-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
try {
    New-Item -ItemType Directory -Path $demoUpdateFalla -Force | Out-Null
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $instalador `
                     -Project $demoUpdateFalla -Harness analisis -Usuario 'Prueba Update Falla' | Out-Null

    # Trabajo humano: un hook editado a mano, que -Update tiene que conservar.
    $hookEditadoFalla = Join-Path $demoUpdateFalla '.claude\harness\hooks\pre-tool-use.py'
    Add-Content -Path $hookEditadoFalla -Value '# editado a mano, no se puede perder' -Encoding UTF8

    # El mismo truco de E-23: sin Python alcanzable, Invoke-Instalar tira temprano
    # (Test-Entorno lo detecta como falla) antes de escribir un solo archivo nuevo.
    $comandoUpdateSinPython = "`$env:PATH = 'C:\no-existe'; & '$instalador' -Project '$demoUpdateFalla' -Update 2>&1 | Out-String"
    $salidaUpdateFalla = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                                          -Command $comandoUpdateSinPython | Out-String
    $codigoUpdateFalla = $LASTEXITCODE

    Assert-Verdadero 'E-30 -Update sin Python sale con codigo de fallo' ($codigoUpdateFalla -ne 0) `
        "codigo obtenido: $codigoUpdateFalla"
    Assert-Verdadero 'E-30 el proyecto sigue teniendo .claude\harness\' `
        (Test-Path (Join-Path $demoUpdateFalla '.claude\harness'))
    Assert-Verdadero 'E-30 el hook editado a mano sigue existiendo' (Test-Path $hookEditadoFalla)
    if (Test-Path $hookEditadoFalla) {
        Assert-Contiene 'E-30 y conserva la edicion humana' 'no se puede perder' `
            ([System.IO.File]::ReadAllText($hookEditadoFalla))
    }
    Assert-Verdadero 'E-30 conserva harness.config.json' `
        (Test-Path (Join-Path $demoUpdateFalla '.claude\harness.config.json'))
}
finally {
    if (Test-Path $demoUpdateFalla) { Remove-Item $demoUpdateFalla -Recurse -Force -ErrorAction SilentlyContinue }
}


# ── La definición de zonas vive en un solo lado (E-17) ───────────────────────────
#
# Zonas.psm1 se borró en la Task 10 porque install.ps1 pasó a leer la definición de
# comun/hooks/lib/zonas.py. Si algún día reaparece una segunda definición -otro lugar
# que empareje el nombre de una zona con la clave de su techo- las dos quedan
# desincronizadas en silencio, que es justo lo que la migración cerró.
#
# Una DEFINICIÓN empareja el nombre de la clave del techo con el valor de esa clave en la
# misma expresión, en cualquiera de los dos idiomas que tuvo esta definición -JSON/Python
# hoy, PowerShell en la Zonas.psm1 ya borrada-. Un VALOR de configuración o de test nombra
# la clave compuesta entera, pero no la empareja con ningún separador inmediatamente
# después de la palabra que identifica al techo sola: ahí lo que sigue es el resto del
# nombre de la clave, no un separador. Esa ausencia es lo que distingue un valor de una
# definición, y es lo que el patrón de abajo verifica.
#
# El patrón se arma por concatenación -mismo truco que 04_secretos.py usa con los
# literales de secretos, por la misma razón- para que este archivo no pueda, él mismo,
# contener la forma completa que busca. Es la lección de la primera versión de este test:
# describía las dos formas escritas tal cual, a modo de ejemplo, en este mismo comentario
# -y el propio comentario se detectaba a sí mismo como si fuera la definición real-.

Set-Grupo 'Composicion - la definicion de zonas vive en un solo lado (E-17)'

$fragmentoClave = '["'']?[Tt]ec' + 'ho["'']?\s*[:=]\s*["'']'
$fragmentoValor = 'tec' + 'hoZonaFija["'']'
$patronDefinicionZona = $fragmentoClave + $fragmentoValor
$archivosFuente = Get-ChildItem $script:Raiz -Recurse -File -Include '*.py', '*.ps1', '*.psm1' -ErrorAction SilentlyContinue |
                  Where-Object { $_.FullName -notlike '*\.git\*' -and $_.FullName -notlike '*\__pycache__\*' }

$conDefinicionDeZona = @()
foreach ($f in $archivosFuente) {
    $t = [System.IO.File]::ReadAllText($f.FullName)
    if ($t -match $patronDefinicionZona) {
        $conDefinicionDeZona += $f.FullName.Replace($script:Raiz + '\', '')
    }
}

Assert-Igual 'E-17 solo zonas.py define el par nombre/techo de una zona' `
    'comun\hooks\lib\zonas.py' ($conDefinicionDeZona -join ', ')


# ── zonas.py roto aborta sin dejar un CLAUDE.md a medias (E-20) ──────────────────
#
# Si la invocación a zonas.py falla, la instalación aborta con el mensaje del error: no
# se instala un CLAUDE.md a medias. Criterio fijado acá porque no era obvio del código:
# el CLAUDE.md tiene que quedar EXACTAMENTE como estaba, sin el bloque HARNESS:COMUN ni
# las zonas vacías que el instalador agrega después de invocar zonas.py -un archivo con
# el bloque puesto pero sin las zonas no está corrupto, pero tampoco intacto, y "casi
# intacto" es peor que "no tocado": no hay forma de saber, mirándolo, si terminó de
# instalarse o no.
#
# Rotura temporal y reversible de comun/hooks/lib/zonas.py -no es mío, y tiene que quedar
# bit a bit igual al terminar-: un error de sintaxis, que ninguna defensa en tiempo de
# ejecución puede atrapar porque Python ni siquiera puede compilarlo.

Set-Grupo 'Instalador - zonas.py roto aborta sin CLAUDE.md a medias (E-20)'

$rutaZonasPy = Join-Path $script:Raiz 'comun\hooks\lib\zonas.py'
$bytesZonasOriginales = [System.IO.File]::ReadAllBytes($rutaZonasPy)
$demoZonasRotas = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-zonasrotas-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$claudeMdPrevioE20 = "# CLAUDE.md - previo a la instalacion`r`n`r`nEsta linea es del humano.`r`n"

try {
    New-Item -ItemType Directory -Path $demoZonasRotas -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demoZonasRotas 'CLAUDE.md'), $claudeMdPrevioE20)

    [System.IO.File]::AppendAllText($rutaZonasPy, "`ndef (((`n")

    $rZonasRotas = Invoke-Instalador @('-Project', $demoZonasRotas, '-Harness', 'analisis', '-Usuario', 'Prueba Zonas Rotas')

    Assert-Igual 'E-20 la instalacion aborta' 1 $rZonasRotas.Codigo
    Assert-Contiene 'E-20 el mensaje nombra el error de zonas.py' 'zonas.py' $rZonasRotas.Salida
    Assert-Igual 'E-20 el CLAUDE.md queda exactamente como estaba' `
        $claudeMdPrevioE20 ([System.IO.File]::ReadAllText((Join-Path $demoZonasRotas 'CLAUDE.md')))
    Assert-Verdadero 'E-20 no deja lockfile' `
        (-not (Test-Path (Join-Path $demoZonasRotas '.claude\harness.lock.json')))
}
finally {
    [System.IO.File]::WriteAllBytes($rutaZonasPy, $bytesZonasOriginales)
    if (Test-Path $demoZonasRotas) { Remove-Item $demoZonasRotas -Recurse -Force -ErrorAction SilentlyContinue }
}

$bytesZonasFinales = [System.IO.File]::ReadAllBytes($rutaZonasPy)
Assert-Igual 'E-20 zonas.py quedo exactamente igual' `
    ([System.BitConverter]::ToString($bytesZonasOriginales)) ([System.BitConverter]::ToString($bytesZonasFinales))


# ── La compuerta revierte si un hook responde mal (E-27) ─────────────────────────
#
# Test-HooksInstalados es lo que hace que "instalado" signifique "funciona": si algún
# hook no responde con JSON válido y código 0, la instalación entera se revierte y no
# deja un harness a medias. El revisor lo verificó a mano rompiendo pre-tool-use.py para
# que emita una salida que no es JSON; esto lo deja clavado en la suite.
#
# Misma técnica que E-20: rotura temporal y reversible de un archivo que no es mío
# -comun/hooks/pre-tool-use.py-, con un error de sintaxis que ninguna defensa en tiempo
# de ejecución de lib.hook puede atrapar -es justo el punto: el hook no puede ni arrancar.

Set-Grupo 'Instalador - la compuerta revierte un hook roto (E-27)'

$rutaHookRoto = Join-Path $script:Raiz 'comun\hooks\pre-tool-use.py'
$bytesHookOriginales = [System.IO.File]::ReadAllBytes($rutaHookRoto)
$demoHookRoto = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-hookroto-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))

try {
    New-Item -ItemType Directory -Path $demoHookRoto -Force | Out-Null

    [System.IO.File]::AppendAllText($rutaHookRoto, "`ndef (((`n")

    $rHookRoto = Invoke-Instalador @('-Project', $demoHookRoto, '-Harness', 'analisis', '-Usuario', 'Prueba Hook Roto')

    Assert-Igual 'E-27 la instalacion sale con codigo de fallo' 1 $rHookRoto.Codigo
    Assert-Contiene 'E-27 avisa que revierte' 'Revirtiendo' $rHookRoto.Salida
    Assert-Verdadero 'E-27 no deja lockfile' `
        (-not (Test-Path (Join-Path $demoHookRoto '.claude\harness.lock.json')))
    Assert-Verdadero 'E-27 no deja .claude\harness a medias' `
        (-not (Test-Path (Join-Path $demoHookRoto '.claude\harness')))
    # bloque-1-bienvenida E-01, la mitad de la instalacion revertida.
    Assert-Verdadero 'bienvenida E-01 revertida por un hook roto: no deja harness.installation.json' `
        (-not (Test-Path (Join-Path $demoHookRoto '.claude\harness.installation.json')))
}
finally {
    [System.IO.File]::WriteAllBytes($rutaHookRoto, $bytesHookOriginales)
    if (Test-Path $demoHookRoto) { Remove-Item $demoHookRoto -Recurse -Force -ErrorAction SilentlyContinue }
}

$bytesHookFinales = [System.IO.File]::ReadAllBytes($rutaHookRoto)
Assert-Igual 'E-27 pre-tool-use.py quedo exactamente igual' `
    ([System.BitConverter]::ToString($bytesHookOriginales)) ([System.BitConverter]::ToString($bytesHookFinales))


# ── Los hooks se registran para PowerShell, y la compuerta prueba lo registrado ─────
#
# Spec: docs/cambios/hooks-con-shell-powershell/spec.md, E-01..E-11. Y del lado del
# instalador, docs/cambios/bloque-1-bienvenida/spec.md: E-01, la mitad de E-02, E-18,
# E-19 (la mitad del borrado) y E-24.
#
# Hasta la 0.20 ningún hook corrió en una máquina sin Git Bash: el comando registrado era
# sintaxis de bash, y la compuerta lanzaba run-hook.cmd directo en vez de probar lo que
# quedaba escrito en settings.json. Por eso cada comando de acá se corre con
# Invoke-HpsComando, que vive en este archivo y no en install.ps1: si el test usara la
# misma función que la compuerta, un error en esa función daría verde de los dos lados.

Set-Grupo 'Instalador - hooks registrados para PowerShell'

$hpsVersion = ([System.IO.File]::ReadAllText((Join-Path $script:Raiz 'VERSION'))).Trim()
$hpsMatcher = 'Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell'
$hpsEventos = [ordered]@{
    SessionStart     = 'session-start'
    UserPromptSubmit = 'user-prompt-submit'
    PreToolUse       = 'pre-tool-use'
    PostToolUse      = 'post-tool-use'
}
$hpsPayloads = @{
    SessionStart     = 'session-start.json'
    UserPromptSubmit = 'user-prompt-submit.json'
    PreToolUse       = 'pre-tool-use-write.json'
    PostToolUse      = 'post-tool-use-write.json'
}
$hpsUtf8 = New-Object System.Text.UTF8Encoding $false


function Invoke-HpsProceso {
    <# Un proceso con el payload por stdin y CLAUDE_PROJECT_DIR; la salida en bytes. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Proyecto, [string] $Json)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.WorkingDirectory       = $Proyecto
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardInput  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.EnvironmentVariables['CLAUDE_PROJECT_DIR'] = $Proyecto

    $p = [System.Diagnostics.Process]::Start($psi)
    $err = $p.StandardError.ReadToEndAsync()
    $entrada = $hpsUtf8.GetBytes($Json)
    $p.StandardInput.BaseStream.Write($entrada, 0, $entrada.Length)
    $p.StandardInput.Close()
    $memoria = New-Object System.IO.MemoryStream
    $p.StandardOutput.BaseStream.CopyTo($memoria)
    $p.WaitForExit()
    $bytes = $memoria.ToArray()
    return [pscustomobject]@{
        Codigo = $p.ExitCode; Bytes = $bytes; Salida = $hpsUtf8.GetString($bytes); Errores = $err.Result
    }
}


function Invoke-HpsComando {
    <# Un comando registrado, como lo corre Claude Code con "shell": "powershell". El texto
       va codificado para que llegue exacto: pasado con -Command, PowerShell 5.1 se come
       comillas dobles de la línea de comandos. #>
    param([string] $Comando, [string] $Proyecto, [string] $Json)
    $powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $codificado = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($Comando))
    return (Invoke-HpsProceso -Archivo $powershell -Argumentos ('-NoProfile -NonInteractive -EncodedCommand ' + $codificado) `
                              -Proyecto $Proyecto -Json $Json)
}


function Invoke-HpsLanzador {
    <# run-hook.cmd directo, sin pasar por lo registrado: la referencia de E-11. #>
    param([string] $Proyecto, [string] $Hook, [string] $Json)
    return (Invoke-HpsProceso -Archivo (Join-Path $Proyecto '.claude\harness\run-hook.cmd') -Argumentos $Hook `
                              -Proyecto $Proyecto -Json $Json)
}


function Get-HpsHooks {
    <# Cada hook registrado en el settings.json del proyecto, con su evento y su filtro. #>
    param([string] $Proyecto)
    $s = [System.IO.File]::ReadAllText((Join-Path $Proyecto '.claude\settings.json')) | ConvertFrom-Json
    $lista = @()
    foreach ($ev in @($hpsEventos.Keys)) {
        if (-not $s.hooks.PSObject.Properties[$ev]) { continue }
        foreach ($g in @($s.hooks.$ev)) {
            $matcher = $null
            if ($g.PSObject.Properties['matcher']) { $matcher = $g.matcher }
            foreach ($h in @($g.hooks)) {
                $lista += [pscustomobject]@{ Evento = $ev; Matcher = $matcher; Hook = $h }
            }
        }
    }
    return ,$lista
}


function Get-HpsComandoViejo {
    param([string] $Evento)
    return '"$CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd" ' + $hpsEventos[$Evento]
}


function Set-HpsSettings {
    <# Reescribe los comandos del settings.json. -Viejo deja exactamente lo que escribía la
       plantilla de antes: sin shell, el comando de bash y los filtros sin PowerShell. #>
    param([string] $Proyecto, [switch] $Viejo, [scriptblock] $Comando)
    $ruta = Join-Path $Proyecto '.claude\settings.json'
    $s = [System.IO.File]::ReadAllText($ruta) | ConvertFrom-Json
    foreach ($ev in @($hpsEventos.Keys)) {
        foreach ($g in @($s.hooks.$ev)) {
            if ($Viejo -and $g.PSObject.Properties['matcher'] -and $g.matcher -eq $hpsMatcher) {
                $g.matcher = 'Write|Edit|MultiEdit|NotebookEdit|Bash'
            }
            foreach ($h in @($g.hooks)) {
                if ($Viejo) {
                    $h.command = Get-HpsComandoViejo $ev
                    $h.PSObject.Properties.Remove('shell')
                } else {
                    $h.command = (& $Comando $ev)
                }
            }
        }
    }
    [System.IO.File]::WriteAllText($ruta, (ConvertTo-Json -InputObject $s -Depth 20), $hpsUtf8)
}


function Test-HpsJsonOVacio {
    param([string] $Texto)
    if (-not $Texto.Trim()) { return $true }
    try { $Texto | ConvertFrom-Json | Out-Null; return $true } catch { return $false }
}


function Get-HpsMensaje {
    <# El systemMessage de una salida de session-start, o ''. #>
    param($Resultado)
    if (-not $Resultado.Salida.Trim()) { return '' }
    $j = $Resultado.Salida | ConvertFrom-Json
    if ($j.PSObject.Properties['systemMessage'] -and $j.systemMessage) { return [string]$j.systemMessage }
    return ''
}


function Invoke-HpsSesion {
    <# Una sesión que arranca en el proyecto, por el comando registrado de SessionStart. #>
    param([string] $Proyecto)
    $cmd = ((Get-HpsHooks $Proyecto) | Where-Object { $_.Evento -eq 'SessionStart' } | Select-Object -First 1).Hook.command
    $payload = ConvertTo-Json -Compress -InputObject ([ordered]@{
        session_id = 'hps-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 6)
        cwd = $Proyecto; hook_event_name = 'SessionStart'; source = 'startup' })
    return (Invoke-HpsComando -Comando $cmd -Proyecto $Proyecto -Json $payload)
}


function Get-HpsErroresDeSchema {
    <# Los errores de validar harness.installation.json contra su schema, con el mismo
       validador que usa el resto de la suite (comun/bin/contexto-armar.py). '[]' si valida. #>
    param([string] $Proyecto)
    $py = Join-Path ([System.IO.Path]::GetTempPath()) ('hps-schema-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 6) + '.py')
    $codigo = @'
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("armador_hps", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
with open(sys.argv[2], encoding="utf-8") as f:
    esquema = json.load(f)
m.controlar_soporte(esquema)
with open(sys.argv[3], encoding="utf-8") as f:
    doc = json.load(f)
sys.stdout.write(json.dumps(m.validar(doc, esquema)))
'@
    try {
        [System.IO.File]::WriteAllText($py, $codigo, $hpsUtf8)
        $r = Invoke-HpsProceso -Archivo 'python' `
            -Argumentos ('"' + $py + '" "' + (Join-Path $script:Raiz 'comun\bin\contexto-armar.py') + '" "' +
                         (Join-Path $script:Raiz 'comun\schemas\harness-installation-state.schema.json') + '" "' +
                         (Join-Path $Proyecto '.claude\harness.installation.json') + '"') `
            -Proyecto $Proyecto -Json ''
        if ($r.Codigo -ne 0) { return "el validador fallo: $($r.Errores)" }
        return $r.Salida.Trim()
    } finally {
        Remove-Item $py -Force -ErrorAction SilentlyContinue
    }
}


function Get-HpsEstado {
    param([string] $Proyecto)
    return ([System.IO.File]::ReadAllText((Join-Path $Proyecto '.claude\harness.installation.json')) | ConvertFrom-Json)
}


$hpsDemo    = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-hps-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
# E-04: espacios, un apostrofo y un $. Con ${CLAUDE_PROJECT_DIR} pegado adentro del texto
# del comando, PowerShell interpretaria esta ruta como codigo.
$hpsRaro    = Join-Path ([System.IO.Path]::GetTempPath()) ("harness hps 'o `$x " + [System.Guid]::NewGuid().ToString('N').Substring(0, 6))
$hpsRevert  = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-hps-rev-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$hpsScripts = @()
# Con tildes a proposito: E-11 compara bytes, y sin un caracter fuera de ASCII en la salida
# la comparacion no distinguiria UTF-8 de nada.
$hpsUsuario = 'Íñigo Pérez'

try {
    New-Item -ItemType Directory -Path $hpsDemo -Force | Out-Null
    $r = Invoke-Instalador @('-Project', $hpsDemo, '-Harness', 'analisis', '-Usuario', $hpsUsuario)
    Assert-Igual 'instala el proyecto de los hooks registrados' 0 $r.Codigo
    Assert-Contiene 'la compuerta dice que probo lo registrado' 'con el comando que quedó en settings.json' $r.Salida

    # ── bloque-1-bienvenida E-01 / E-02: el estado que deja una instalacion buena ──
    $rutaEstadoHps = Join-Path $hpsDemo '.claude\harness.installation.json'
    Assert-Verdadero 'bienvenida E-01 deja .claude\harness.installation.json' (Test-Path $rutaEstadoHps)
    if (Test-Path $rutaEstadoHps) {
        $estado = Get-HpsEstado $hpsDemo
        Assert-Igual 'bienvenida E-01 installed: true'                  'True'      ([string]$estado.installed)
        Assert-Igual 'bienvenida E-01 firstRunShown: false'             'False'     ([string]$estado.welcome.firstRunShown)
        Assert-Igual 'bienvenida E-01 la version es la de VERSION'      $hpsVersion $estado.installedVersion
        Assert-Igual 'bienvenida E-02 lo que escribe el instalador valida contra el schema' '[]' (Get-HpsErroresDeSchema $hpsDemo)
    }
    $lockHps = [System.IO.File]::ReadAllText((Join-Path $hpsDemo '.claude\harness.lock.json')) | ConvertFrom-Json
    Assert-Verdadero 'bienvenida E-01 el estado no entra al lockfile (lo reescribe cada sesion)' `
        (@($lockHps.archivos | Where-Object { $_.ruta -like '*harness.installation.json' }).Count -eq 0)

    # ── E-01 / E-02: lo que queda registrado ────────────────────────────────────
    $hooks = Get-HpsHooks $hpsDemo
    Assert-Igual 'E-01 hay un hook por cada uno de los cuatro eventos' 4 $hooks.Count
    foreach ($h in $hooks) {
        $cmd = [string]$h.Hook.command
        $shell = ''
        if ($h.Hook.PSObject.Properties['shell']) { $shell = [string]$h.Hook.shell }
        Assert-Igual     "E-01 $($h.Evento) fija shell: powershell" 'powershell' $shell
        Assert-Verdadero "E-01 $($h.Evento) empieza con & y `$env:CLAUDE_PROJECT_DIR" `
            ($cmd.StartsWith('& "$env:CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd"')) $cmd
        Assert-Verdadero "E-01 $($h.Evento) termina con ; exit `$LASTEXITCODE" ($cmd.EndsWith('; exit $LASTEXITCODE')) $cmd
        Assert-Verdadero "E-01 $($h.Evento) no usa `$CLAUDE_PROJECT_DIR sin env:" `
            ($cmd -notmatch '\$CLAUDE_PROJECT_DIR') $cmd
        Assert-Verdadero "E-01 $($h.Evento) no usa `${" (-not $cmd.Contains('${')) $cmd
        Assert-Verdadero "E-01 $($h.Evento) llama a su hook" ($cmd.Contains('run-hook.cmd" ' + $hpsEventos[$h.Evento] + ';')) $cmd
    }
    foreach ($ev in @('PreToolUse', 'PostToolUse')) {
        $m = @($hooks | Where-Object { $_.Evento -eq $ev } | Select-Object -ExpandProperty Matcher)
        Assert-Igual "E-02 el filtro de $ev nombra PowerShell, exacto" $hpsMatcher ($m -join ' / ')
    }

    # La invariante de portabilidad: settings.json no lleva ninguna ruta de esta maquina.
    $textoSettingsHps = [System.IO.File]::ReadAllText((Join-Path $hpsDemo '.claude\settings.json'))
    $txtCmdHps = [System.IO.File]::ReadAllText((Join-Path $hpsDemo '.claude\harness\run-hook.cmd'))
    $exeHps = ([regex]::Match($txtCmdHps, '"([^"]+\.exe)"')).Groups[1].Value
    Assert-Verdadero 'settings.json no lleva la ruta del proyecto' (-not $textoSettingsHps.Contains($hpsDemo))
    Assert-Verdadero 'settings.json no lleva la ruta de Python'    ($exeHps -and -not $textoSettingsHps.Contains($exeHps))
    Assert-Verdadero 'settings.json no lleva ninguna ruta con unidad' ($textoSettingsHps -notmatch '[A-Za-z]:(\\\\|/)')

    # ── E-03: cada comando registrado corre ─────────────────────────────────────
    foreach ($h in $hooks) {
        $r = Invoke-HpsComando -Comando $h.Hook.command -Proyecto $hpsDemo -Json (Get-Payload $hpsPayloads[$h.Evento])
        Assert-Igual     "E-03 $($h.Evento) sale con 0" 0 $r.Codigo
        Assert-Verdadero "E-03 $($h.Evento) responde JSON valido o nada" (Test-HpsJsonOVacio $r.Salida) $r.Salida
        # Con 0 y la salida vacia tambien sale un comando que no encontro run-hook.cmd:
        # `exit $LASTEXITCODE` da 0 cuando ningun programa llego a correr. Lo delata el
        # error de PowerShell en stderr.
        Assert-Verdadero "E-03 $($h.Evento) PowerShell no reporta ningun error" ($r.Errores -notmatch '<S S="Error">') $r.Errores
    }

    # ── E-05: el comando viejo, corrido igual, falla ────────────────────────────
    # Sin esto, E-03 no probaria que la forma de correrlo distingue un comando que anda de
    # uno que no.
    foreach ($ev in @($hpsEventos.Keys)) {
        $r = Invoke-HpsComando -Comando (Get-HpsComandoViejo $ev) -Proyecto $hpsDemo -Json (Get-Payload $hpsPayloads[$ev])
        Assert-Verdadero "E-05 el comando viejo de $ev falla" ($r.Codigo -ne 0) "codigo $($r.Codigo)"
    }

    # ── E-10: un secreto en un comando de PowerShell, por el comando registrado ─
    # El token se arma por partes: un fuente que dispara el detector de secretos no se
    # puede editar donde el harness esta instalado.
    $tokenHps = 'glp' + 'at-' + 'Q7w8E9r0T1y2U3i4O5p6A7s8'
    $cmdPre = ($hooks | Where-Object { $_.Evento -eq 'PreToolUse' } | Select-Object -First 1).Hook.command
    foreach ($caso in @(@{ Rotulo = 'con el secreto'; Texto = "`$env:GITLAB_TOKEN = '$tokenHps'"; Deny = $true },
                        @{ Rotulo = 'sin secreto';    Texto = 'Get-ChildItem .';                 Deny = $false })) {
        $payload = ConvertTo-Json -Compress -Depth 5 -InputObject ([ordered]@{
            session_id = 'hps-e10'; cwd = $hpsDemo; hook_event_name = 'PreToolUse'
            tool_name = 'PowerShell'; tool_input = [ordered]@{ command = $caso.Texto } })
        $r = Invoke-HpsComando -Comando $cmdPre -Proyecto $hpsDemo -Json $payload
        $decision = ''
        if ($r.Salida.Trim()) {
            $j = $r.Salida | ConvertFrom-Json
            if ($j.PSObject.Properties['hookSpecificOutput'] -and $j.hookSpecificOutput.PSObject.Properties['permissionDecision']) {
                $decision = [string]$j.hookSpecificOutput.permissionDecision
            }
        }
        Assert-Igual "E-10 PowerShell $($caso.Rotulo): sale con 0" 0 $r.Codigo
        if ($caso.Deny) {
            Assert-Igual 'E-10 PowerShell con un secreto de confianza alta sale denegado' 'deny' $decision
        } else {
            Assert-Verdadero 'E-10 PowerShell sin secreto no se deniega' ($decision -ne 'deny') $decision
        }
    }

    # ── E-11: las tildes llegan igual por lo registrado que por el lanzador ─────
    # La sesion con el cwd del proyecto escribe la marca de la bienvenida: se restaura el
    # archivo entre las dos corridas para que las dos vean el mismo estado.
    $bytesEstadoHps = [System.IO.File]::ReadAllBytes($rutaEstadoHps)
    $payloadSesion = ConvertTo-Json -Compress -InputObject ([ordered]@{
        session_id = 'hps-e11'; cwd = $hpsDemo; hook_event_name = 'SessionStart'; source = 'startup' })
    $cmdSs = ($hooks | Where-Object { $_.Evento -eq 'SessionStart' } | Select-Object -First 1).Hook.command
    $porRegistro = Invoke-HpsComando -Comando $cmdSs -Proyecto $hpsDemo -Json $payloadSesion
    [System.IO.File]::WriteAllBytes($rutaEstadoHps, $bytesEstadoHps)
    $porLanzador = Invoke-HpsLanzador -Proyecto $hpsDemo -Hook 'session-start' -Json $payloadSesion
    [System.IO.File]::WriteAllBytes($rutaEstadoHps, $bytesEstadoHps)
    Assert-Igual 'E-11 session-start por lo registrado sale con 0' 0 $porRegistro.Codigo
    Assert-Contiene 'E-11 la salida trae las tildes, en UTF-8' $hpsUsuario $porRegistro.Salida
    Assert-Contiene 'E-11 y la marca de la bienvenida' '✓' $porRegistro.Salida
    Assert-Igual 'E-11 byte a byte igual que por el lanzador directo' `
        ([System.BitConverter]::ToString($porLanzador.Bytes)) ([System.BitConverter]::ToString($porRegistro.Bytes))

    # ── E-07: la compuerta lee settings.json, no lanza run-hook.cmd ─────────────
    $hpsCompuerta = Join-Path ([System.IO.Path]::GetTempPath()) ('hps-compuerta-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 6) + '.ps1')
    $hpsScripts += $hpsCompuerta
    [System.IO.File]::WriteAllText($hpsCompuerta, @'
param([string] $Instalador, [string] $Proyecto)
. $Instalador
$problemas = Test-HooksInstalados -Project $Proyecto
[Console]::Out.Write([string]$problemas.Count)
'@, $hpsUtf8)
    $rutaSettingsHps = Join-Path $hpsDemo '.claude\settings.json'
    $rutaShimHps     = Join-Path $hpsDemo '.claude\harness\run-hook.cmd'
    $bytesSettingsHps = [System.IO.File]::ReadAllBytes($rutaSettingsHps)
    $bytesShimHps     = [System.IO.File]::ReadAllBytes($rutaShimHps)
    function Invoke-HpsCompuerta {
        $s = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $hpsCompuerta `
                              -Instalador $instalador -Proyecto $hpsDemo 2>&1 | Out-String
        return $s.Trim()
    }
    try {
        Assert-Igual 'E-07 con lo que instalo, la compuerta no ve problemas' '0' (Invoke-HpsCompuerta)

        # settings.json roto, lanzador sano. El shell se deja: lo unico roto es el comando.
        Set-HpsSettings -Proyecto $hpsDemo -Comando { param($ev) Get-HpsComandoViejo $ev }
        $directo = Invoke-HpsLanzador -Proyecto $hpsDemo -Hook 'session-start' -Json (Get-Payload 'session-start.json')
        Assert-Igual 'E-07 el lanzador directo sigue andando' 0 $directo.Codigo
        Assert-Igual 'E-07 y aun asi la compuerta falla en los cuatro' '4' (Invoke-HpsCompuerta)

        # Al reves: lanzador roto, y comandos registrados que no lo nombran. Si la compuerta
        # lanzara run-hook.cmd por su cuenta, esto fallaria.
        Set-HpsSettings -Proyecto $hpsDemo -Comando { param($ev) "[Console]::Out.Write('{}')" }
        [System.IO.File]::WriteAllText($rutaShimHps, "@exit /b 7`r`n")
        $directo = Invoke-HpsLanzador -Proyecto $hpsDemo -Hook 'session-start' -Json (Get-Payload 'session-start.json')
        Assert-Igual 'E-07 el lanzador directo ahora esta roto' 7 $directo.Codigo
        Assert-Igual 'E-07 y la compuerta no lo lanza: corre solo lo registrado' '0' (Invoke-HpsCompuerta)
    } finally {
        [System.IO.File]::WriteAllBytes($rutaSettingsHps, $bytesSettingsHps)
        [System.IO.File]::WriteAllBytes($rutaShimHps, $bytesShimHps)
    }

    # ── bloque-1-bienvenida E-19: borrar el archivo vuelve a mostrar la bienvenida ─
    $r = Invoke-HpsSesion $hpsDemo
    Assert-Contiene 'bienvenida E-19 la primera sesion muestra la bienvenida' 'GCBA Development Harness' (Get-HpsMensaje $r)
    $r = Invoke-HpsSesion $hpsDemo
    Assert-Verdadero 'bienvenida E-19 la segunda ya no' (-not (Get-HpsMensaje $r).Contains('GCBA Development Harness'))
    Remove-Item $rutaEstadoHps -Force -ErrorAction SilentlyContinue
    $r = Invoke-HpsSesion $hpsDemo
    Assert-Contiene 'bienvenida E-19 borrado el archivo, vuelve la bienvenida' 'GCBA Development Harness' (Get-HpsMensaje $r)
    Remove-Item $rutaEstadoHps -Force -ErrorAction SilentlyContinue
    $r = Invoke-Instalador @('-Project', $hpsDemo, '-Update')
    Assert-Igual 'bienvenida E-19 -Update sin el archivo sale con 0' 0 $r.Codigo
    Assert-Verdadero 'bienvenida E-19 -Update sin el archivo lo vuelve a escribir' (Test-Path $rutaEstadoHps)
    if (Test-Path $rutaEstadoHps) {
        Assert-Igual 'bienvenida E-19 y es una primera vez: firstRunShown false' 'False' `
            ([string](Get-HpsEstado $hpsDemo).welcome.firstRunShown)
    }
    $r = Invoke-HpsSesion $hpsDemo
    Assert-Contiene 'bienvenida E-19 y la sesion siguiente muestra la bienvenida' 'GCBA Development Harness' (Get-HpsMensaje $r)
    Assert-Igual 'bienvenida E-19 que deja firstRunShown true' 'True' ([string](Get-HpsEstado $hpsDemo).welcome.firstRunShown)

    # ── E-08 / E-09 / bienvenida E-18: un proyecto de la version anterior ───────
    # Como lo dejo una instalacion vieja de verdad: el settings.json viejo CON su hash en el
    # lockfile (si no, -Update lo tomaria por editado a mano y no lo pisaria), la version
    # anterior en el lockfile y en el estado, y la bienvenida ya vista.
    Set-HpsSettings -Proyecto $hpsDemo -Viejo
    $rutaLockHps = Join-Path $hpsDemo '.claude\harness.lock.json'
    $lockViejo = [System.IO.File]::ReadAllText($rutaLockHps) | ConvertFrom-Json
    foreach ($a in $lockViejo.archivos) {
        if ($a.ruta -eq '.claude\settings.json') { $a.sha256 = (Get-FileHash -Path $rutaSettingsHps -Algorithm SHA256).Hash }
    }
    $lockViejo.version = '0.19.0'
    [System.IO.File]::WriteAllText($rutaLockHps, (ConvertTo-Json -InputObject $lockViejo -Depth 20), $hpsUtf8)
    $estadoViejo = Get-HpsEstado $hpsDemo
    $estadoViejo.installedVersion = '0.19.0'
    [System.IO.File]::WriteAllText($rutaEstadoHps, (ConvertTo-Json -InputObject $estadoViejo -Depth 20), $hpsUtf8)

    $r = Invoke-Instalador @('-Doctor', '-Project', $hpsDemo)
    Assert-Contiene 'E-08 -Doctor con el settings.json viejo informa que los hooks no corren' `
        'los hooks registrados en settings.json no corren' $r.Salida
    Assert-Igual 'E-08 y lo cuenta como falla' 1 $r.Codigo

    $r = Invoke-Instalador @('-Project', $hpsDemo, '-Update')
    Assert-Igual 'E-09 -Update sale con 0' 0 $r.Codigo
    $hooksNuevos = Get-HpsHooks $hpsDemo
    Assert-Verdadero 'E-09 -Update deja los comandos nuevos' `
        (@($hooksNuevos | Where-Object { ([string]$_.Hook.command).StartsWith('& "$env:CLAUDE_PROJECT_DIR/') }).Count -eq 4)
    Assert-Verdadero 'E-09 y los filtros con PowerShell' `
        (@($hooksNuevos | Where-Object { $_.Matcher -eq $hpsMatcher }).Count -eq 2)
    $lockNuevo = [System.IO.File]::ReadAllText($rutaLockHps) | ConvertFrom-Json
    $shaLock = @($lockNuevo.archivos | Where-Object { $_.ruta -eq '.claude\settings.json' } | Select-Object -ExpandProperty sha256)
    Assert-Igual 'E-09 el hash de settings.json en el lockfile coincide con el archivo' `
        (Get-FileHash -Path $rutaSettingsHps -Algorithm SHA256).Hash ($shaLock -join ',')

    $r = Invoke-Instalador @('-Doctor', '-Project', $hpsDemo)
    Assert-Verdadero 'E-08 -Doctor con el settings.json nuevo no informa nada de los hooks' `
        (-not $r.Salida.Contains('no corren')) $r.Salida
    Assert-Contiene 'E-08 y dice que responden' 'los cuatro hooks registrados en settings.json responden' $r.Salida

    $estado = Get-HpsEstado $hpsDemo
    Assert-Igual 'bienvenida E-18 -Update conserva firstRunShown: true' 'True' ([string]$estado.welcome.firstRunShown)
    $upgradeFrom = $null
    if ($estado.welcome.PSObject.Properties['upgradeFrom']) { $upgradeFrom = $estado.welcome.upgradeFrom }
    Assert-Igual 'bienvenida E-18 y anota de que version viene' '0.19.0' $upgradeFrom
    Assert-Igual 'bienvenida E-18 con la version nueva' $hpsVersion $estado.installedVersion
    Assert-Igual 'bienvenida E-02 lo que escribe el -Update valida contra el schema' '[]' (Get-HpsErroresDeSchema $hpsDemo)

    $mensaje = Get-HpsMensaje (Invoke-HpsSesion $hpsDemo)
    $lineas = @($mensaje -split "`n")
    Assert-Igual 'bienvenida E-18 la sesion siguiente avisa la actualizacion' `
        "Harness GCBA actualizado: 0.19.0 → $hpsVersion ✓" $lineas[0]
    Assert-Igual 'bienvenida E-18 y la linea, nada mas' 2 $lineas.Count
    Assert-Verdadero 'bienvenida E-18 no repite la bienvenida' (-not $mensaje.Contains('GCBA Development Harness')) $mensaje
    $mensaje = Get-HpsMensaje (Invoke-HpsSesion $hpsDemo)
    Assert-Verdadero 'bienvenida E-18 una sola vez' (-not $mensaje.Contains('actualizado')) $mensaje

    # ── bloque-1-bienvenida E-24: -Uninstall lo borra ────────────────────────────
    $r = Invoke-Instalador @('-Project', $hpsDemo, '-Uninstall')
    Assert-Igual 'bienvenida E-24 -Uninstall sale con 0' 0 $r.Codigo
    Assert-Verdadero 'bienvenida E-24 -Uninstall borra harness.installation.json' (-not (Test-Path $rutaEstadoHps))
    Assert-Verdadero 'bienvenida E-24 y conserva harness.config.json' (Test-Path (Join-Path $hpsDemo '.claude\harness.config.json'))

    # ── E-04: una ruta con espacios, un apostrofo y un $ ─────────────────────────
    New-Item -ItemType Directory -Path $hpsRaro -Force | Out-Null
    $r = Invoke-Instalador @('-Project', $hpsRaro, '-Harness', 'analisis', '-Usuario', 'Prueba Rara')
    Assert-Igual 'E-04 instala en la ruta rara (su compuerta ya corrio lo registrado)' 0 $r.Codigo
    if (Test-Path (Join-Path $hpsRaro '.claude\settings.json')) {
        foreach ($h in (Get-HpsHooks $hpsRaro)) {
            $r = Invoke-HpsComando -Comando $h.Hook.command -Proyecto $hpsRaro -Json (Get-Payload $hpsPayloads[$h.Evento])
            Assert-Igual     "E-04 $($h.Evento) sale con 0 en la ruta rara" 0 $r.Codigo
            Assert-Verdadero "E-04 $($h.Evento) responde JSON valido o nada" (Test-HpsJsonOVacio $r.Salida) $r.Salida
            Assert-Verdadero "E-04 $($h.Evento) PowerShell no reporta ningun error" ($r.Errores -notmatch '<S S="Error">') $r.Errores
        }
        Assert-Contiene 'E-04 session-start lee el proyecto de la ruta rara' 'Prueba Rara' (Invoke-HpsSesion $hpsRaro).Salida
    }

    # ── E-06: un comando registrado que no corre revierte la instalacion ──────────
    # La costura: install.ps1 cargado con dot-source adentro de una funcion avanzada (sin
    # eso no hay $PSCmdlet y Invoke-Instalar no arranca), con New-SettingsProyecto
    # envuelta para que deje el comando viejo. El shell queda: lo unico roto es el comando.
    New-Item -ItemType Directory -Path $hpsRevert -Force | Out-Null
    $hpsCostura = Join-Path ([System.IO.Path]::GetTempPath()) ('hps-costura-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 6) + '.ps1')
    $hpsScripts += $hpsCostura
    [System.IO.File]::WriteAllText($hpsCostura, @'
param([string] $Instalador, [string] $Proyecto)
function Invoke-HpsCostura {
    [CmdletBinding(SupportsShouldProcess)] param()
    . $Instalador -Project $Proyecto -Usuario 'Prueba Revertida'
    $real = ${function:New-SettingsProyecto}
    function New-SettingsProyecto {
        param([string] $RutaSettings)
        & $real -RutaSettings $RutaSettings
        $s = [System.IO.File]::ReadAllText($RutaSettings) | ConvertFrom-Json
        foreach ($ev in @($s.hooks.PSObject.Properties)) {
            foreach ($g in @($ev.Value)) {
                foreach ($h in @($g.hooks)) {
                    $h.command = [regex]::Replace([string]$h.command,
                        '^& "\$env:CLAUDE_PROJECT_DIR(/\.claude/harness/run-hook\.cmd)" (\S+); exit \$LASTEXITCODE$',
                        '"$$CLAUDE_PROJECT_DIR$1" $2')
                }
            }
        }
        [System.IO.File]::WriteAllText($RutaSettings, (ConvertTo-Json -InputObject $s -Depth 20))
    }
    Invoke-Instalar -Ids analisis | Out-Null
}
try { Invoke-HpsCostura; exit 0 } catch { [Console]::Out.WriteLine($_.Exception.Message); exit 1 }
'@, $hpsUtf8)
    $salidaRevert = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $hpsCostura `
                                     -Instalador $instalador -Proyecto $hpsRevert 2>&1 | Out-String
    $codigoRevert = $LASTEXITCODE
    Assert-Igual    'E-06 la instalacion sale con codigo de fallo' 1 $codigoRevert
    Assert-Contiene 'E-06 falla por el comando registrado, no por otra cosa' 'SessionStart: el comando registrado salió con código' $salidaRevert
    Assert-Contiene 'E-06 y revierte' 'Revirtiendo' $salidaRevert
    Assert-Verdadero 'E-06 no deja settings.json' (-not (Test-Path (Join-Path $hpsRevert '.claude\settings.json')))
    Assert-Verdadero 'E-06 no deja el lockfile'   (-not (Test-Path (Join-Path $hpsRevert '.claude\harness.lock.json')))
    Assert-Verdadero 'E-06 no deja hooks'         (-not (Test-Path (Join-Path $hpsRevert '.claude\harness')))
    Assert-Verdadero 'bienvenida E-01 revertida: no deja harness.installation.json' `
        (-not (Test-Path (Join-Path $hpsRevert '.claude\harness.installation.json')))
}
finally {
    foreach ($d in @($hpsDemo, $hpsRaro, $hpsRevert)) {
        if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction SilentlyContinue }
    }
    foreach ($s in $hpsScripts) { Remove-Item -LiteralPath $s -Force -ErrorAction SilentlyContinue }
}
