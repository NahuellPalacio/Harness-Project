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
