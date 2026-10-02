# E-31, E-38 a E-40, E-62 a E-68 y E-75 de
# docs/cambios/context-bar-consumo-desde-instalacion/spec.md, y la parte de -Update de E-46.
# Cada asercion dice `consumo E-nn`, como en tests/casos/62_context_bar_consumo.py.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM (ver
# 00-encoding-fuentes.ps1). Los textos con tilde se arman con [char].
#
# Instala de verdad, en una ruta con espacios y con un `$`, y corre el comando que quedo
# registrado con `bash -c` y con `powershell.exe -NoProfile -Command`, sin CLAUDE_PROJECT_DIR y
# desde el temporal, como lo corre Claude Code. El stdin lleva `context_window` como lo manda
# Claude Code: la instalacion no dibuja ningun porcentaje, y el primer dibujo con una ventana
# usable si.

Set-Grupo 'Instalador - la Context Bar muestra el consumo'

$instaladorCc = Join-Path $script:Raiz 'install.ps1'
$plantillaCc = Join-Path $script:Raiz 'harnesses\desarrollo\reglas\budget-policy-context-default.json'
$aCc = [string][char]0x00E1
$oCc = [string][char]0x00F3
$utf8Cc = New-Object System.Text.UTF8Encoding $false

function Invoke-InstaladorCc {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorCc @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function Invoke-ShellCc {
    param([string] $Exe, [string[]] $Previos, [string] $Comando, [string] $Json)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Exe
    $psi.Arguments              = (($Previos + @('"' + $Comando + '"')) -join ' ')
    $psi.WorkingDirectory       = [System.IO.Path]::GetTempPath()
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardInput  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding $false
    if ($psi.EnvironmentVariables.ContainsKey('CLAUDE_PROJECT_DIR')) {
        $psi.EnvironmentVariables.Remove('CLAUDE_PROJECT_DIR')
    }
    # La suite puede correr bajo Claude Code, que le pone NO_COLOR a sus herramientas: se prueba el
    # comando como lo corre la statusLine, sin NO_COLOR, y se compara sin las secuencias.
    if ($psi.EnvironmentVariables.ContainsKey('NO_COLOR')) {
        $psi.EnvironmentVariables.Remove('NO_COLOR')
    }
    $p = [System.Diagnostics.Process]::Start($psi)
    $salida = $p.StandardOutput.ReadToEndAsync()
    $p.StandardError.ReadToEndAsync() | Out-Null
    $bytes = (New-Object System.Text.UTF8Encoding $false).GetBytes($Json)
    $p.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
    $p.StandardInput.Close()
    if (-not $p.WaitForExit(60000)) { try { $p.Kill() } catch { }; return [pscustomobject]@{ Codigo = -1; Lineas = @(); Plana = '' } }
    $lineas = @(($salida.Result -split "`r?`n") | Where-Object { $_.Trim() })
    $plana = ''
    if ($lineas.Count -eq 1) { $plana = $lineas[0] -replace '\x1b\[[0-9;]*m', '' }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Lineas = $lineas; Plana = $plana }
}

function Find-BashCc {
    try {
        $dir = Split-Path -Parent (Get-Command git -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
        for ($i = 0; $i -lt 3 -and $dir; $i++) {
            $c = Join-Path $dir 'bin\bash.exe'
            if (Test-Path -LiteralPath $c) { return $c }
            $dir = Split-Path -Parent $dir
        }
    } catch { }
    $c = Join-Path $env:ProgramFiles 'Git\bin\bash.exe'
    if (Test-Path -LiteralPath $c) { return $c }
    return $null
}

function Read-JsonCc {
    param([string] $Ruta)
    return ([System.IO.File]::ReadAllText($Ruta) | ConvertFrom-Json)
}

function Get-ComandoCc {
    param([string] $Proy)
    $s = Read-JsonCc (Join-Path $Proy '.claude\settings.json')
    if ($s.PSObject.Properties['statusLine']) { return [string]$s.statusLine.command }
    return ''
}

function Get-EstadoBarraCc {
    # El estado que resuelve la CLI instalada, sin sesion: la de la ultima senal de vida.
    param([string] $Proy)
    $cli = Join-Path $Proy '.claude\harness\bin\desarrollo\dev-harness.py'
    $crudo = & python $cli harness --json --proyecto $Proy 2>$null | Out-String
    try { return ($crudo | ConvertFrom-Json).runtimeComponents.contextBar } catch { return $null }
}

function Get-FotosCc {
    param([string] $Proy, [string] $Sesion)
    $ruta = Join-Path $Proy (".claude\runtime\accounting\" + $Sesion + '\ledger.jsonl')
    if (-not (Test-Path -LiteralPath $ruta)) { return 0 }
    return @([System.IO.File]::ReadAllLines($ruta) | Where-Object { $_.Contains('"CONTEXT_WINDOW_OBSERVED"') }).Count
}

function New-TranscripcionCc {
    param([string] $Ruta, [string] $Sesion)
    $linea = '{"type":"assistant","sessionId":"' + $Sesion + '","timestamp":"2026-09-30T10:00:00",' +
             '"message":{"id":"msg_1","model":"m-cb62","usage":{"input_tokens":10,"output_tokens":100,' +
             '"cache_read_input_tokens":5000,"cache_creation_input_tokens":200}}}'
    [System.IO.File]::WriteAllText($Ruta, $linea + "`n", $utf8Cc)
}

function Get-StdinCc {
    # El stdin de la statusLine. -Ventana: 'ninguna' (sin context_window), 'vacia' (antes de la
    # primera respuesta: current_usage null y los dos totales en 0) o 'usable' (134000 de 200000).
    param([string] $Sesion, [string] $Transcripcion, [string] $Ventana)
    $json = '{"session_id":"' + $Sesion + '","transcript_path":"' + ($Transcripcion -replace '\\', '/') + '"'
    if ($Ventana -eq 'vacia') {
        $json += ',"context_window":{"context_window_size":200000,"total_input_tokens":0,' +
                 '"total_output_tokens":0,"current_usage":null,"used_percentage":0,"remaining_percentage":100}'
    } elseif ($Ventana -eq 'usable') {
        $json += ',"context_window":{"context_window_size":200000,"total_input_tokens":120000,' +
                 '"total_output_tokens":14000,"used_percentage":60,"remaining_percentage":40,' +
                 '"current_usage":{"input_tokens":12,"output_tokens":14000,"cache_creation_input_tokens":900,' +
                 '"cache_read_input_tokens":119088}}'
    }
    return $json + '}'
}

$baseCc = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-cc62-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$demoCc = Join-Path $baseCc 'proyecto con espacios $y'
$conPoliticaCc = Join-Path $baseCc 'con politica propia'
foreach ($d in @($demoCc, $conPoliticaCc)) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $d 'CLAUDE.md'), "# Proyecto de prueba`r`n")
}

try {
    # -- E-31 / E-75: instalar en un proyecto sin politica --------------------------------------
    $rutaPoliticaCc = Join-Path $demoCc '.claude\harness.presupuesto.json'
    $r = Invoke-InstaladorCc @('-Project', $demoCc, '-Usuario', 'Ana Prueba')
    Assert-Igual 'consumo E-31 la instalacion sale 0' 0 $r.Codigo
    Assert-Verdadero 'consumo E-31 deja creada .claude\harness.presupuesto.json' (Test-Path -LiteralPath $rutaPoliticaCc)
    $iguales = (Test-Path -LiteralPath $rutaPoliticaCc) -and
               ([Convert]::ToBase64String([System.IO.File]::ReadAllBytes($rutaPoliticaCc)) -ceq
                [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($plantillaCc)))
    Assert-Verdadero 'consumo E-31 y es la plantilla, byte a byte' $iguales
    $cliCc = Join-Path $demoCc '.claude\harness\bin\desarrollo\dev-harness.py'
    $pres = & python $cliCc presupuesto --proyecto $demoCc 2>&1 | Out-String
    Assert-Igual 'consumo E-32 la politica creada valida con el validador del harness instalado' 0 $LASTEXITCODE
    Assert-Contiene 'consumo E-32 y el harness instalado la reconoce como DEFAULT' 'tica DEFAULT' $pres
    Assert-Contiene 'consumo E-75 la instalacion dice los umbrales de contexto' `
        'Umbrales de contexto configurados: WARNING 70% / ERROR 90%' $r.Salida
    Assert-Contiene 'consumo E-75 y que el porcentaje llega con la primera observacion' `
        ("El porcentaje aparecer$aCc con la primera observaci$($oCc)n de contexto de Claude Code.") $r.Salida
    Assert-Verdadero 'consumo E-75 y no promete ningun Ctx NN%' (-not ($r.Salida -match 'Ctx \d+%')) `
        (([regex]::Matches($r.Salida, 'Ctx \d+%') | ForEach-Object { $_.Value }) -join ', ')
    Assert-Verdadero 'consumo E-31 la politica no entra al lockfile: -Uninstall no la borra y -Update no la compara' `
        (-not (@((Read-JsonCc (Join-Path $demoCc '.claude\harness.lock.json')).archivos | ForEach-Object { $_.ruta }) -contains '.claude\harness.presupuesto.json'))

    # -- E-62 a E-65, E-67 y E-68: el comando registrado, en los dos shells ----------------------
    $comandoCc = Get-ComandoCc $demoCc
    Assert-Verdadero 'consumo E-62 la barra quedo registrada' ([bool]$comandoCc)
    $bashCc = Find-BashCc
    Assert-Verdadero 'consumo E-63 hay Git Bash para probar el comando' ([bool]$bashCc) 'no se encontro bash.exe de Git'
    $shellsCc = @(@{ Nombre = 'powershell -NoProfile -Command'; Escenario = 'E-62'
                     Exe = (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')
                     Previos = @('-NoProfile', '-Command') })
    if ($bashCc) { $shellsCc += @{ Nombre = 'bash -c'; Escenario = 'E-63'; Exe = $bashCc; Previos = @('-c') } }

    # Una senal del mismo segundo que el registro no prueba nada: se deja pasar el segundo.
    Start-Sleep -Milliseconds 1100
    $politicaAntes = @()
    if (Test-Path -LiteralPath $rutaPoliticaCc) { $politicaAntes = [System.IO.File]::ReadAllBytes($rutaPoliticaCc) }
    $ultimaSesionCc = ''
    foreach ($sh in $shellsCc) {
        $sesion = 's-cc62-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8)
        $fuente = Join-Path $baseCc ($sesion + '.jsonl')
        New-TranscripcionCc -Ruta $fuente -Sesion $sesion
        foreach ($v in @('ninguna', 'vacia')) {
            $x = Invoke-ShellCc -Exe $sh.Exe -Previos $sh.Previos -Comando $comandoCc -Json (Get-StdinCc $sesion $fuente $v)
            Assert-Igual "consumo E-64 $($sh.Nombre), ventana $($v): sale 0" 0 $x.Codigo
            Assert-Igual "consumo E-64 $($sh.Nombre), ventana $($v): dibuja una sola linea no vacia" 1 $x.Lineas.Count
            Assert-Verdadero "consumo E-67 $($sh.Nombre), sin observacion de contexto ($v): ningun %" `
                ($x.Plana -and -not $x.Plana.Contains('%')) $x.Plana
            Assert-Verdadero "consumo E-67 $($sh.Nombre), sin observacion ($v): y dibuja la ventana en tokens" `
                ($x.Plana.Contains(' | Ctx 5k | ')) $x.Plana
        }
        Assert-Igual "consumo E-67 $($sh.Nombre): sin observacion no hay foto en el libro" 0 (Get-FotosCc $demoCc $sesion)
        $comandoEntre = Get-ComandoCc $demoCc
        $x = Invoke-ShellCc -Exe $sh.Exe -Previos $sh.Previos -Comando $comandoCc -Json (Get-StdinCc $sesion $fuente 'usable')
        Assert-Igual "consumo $($sh.Escenario) $($sh.Nombre), con una ventana usable: sale 0" 0 $x.Codigo
        Assert-Igual "consumo E-64 $($sh.Nombre), con context_window: dibuja una sola linea no vacia" 1 $x.Lineas.Count
        Assert-Verdadero "consumo $($sh.Escenario) $($sh.Nombre): dibuja Ctx NN%" ($x.Plana -match '\| Ctx \d+% \|') $x.Plana
        Assert-Verdadero "consumo E-67 $($sh.Nombre): el dibujo siguiente, con la observacion, tiene Ctx 67%" `
            ($x.Plana.Contains(' | Ctx 67% | ')) $x.Plana
        Assert-Igual "consumo E-67 $($sh.Nombre): y deja una foto" 1 (Get-FotosCc $demoCc $sesion)
        Assert-Igual "consumo E-68 $($sh.Nombre): entre los dos dibujos el comando registrado es el mismo" $comandoEntre (Get-ComandoCc $demoCc)
        $senal = Read-JsonCc (Join-Path $demoCc '.claude\runtime\contextbar.json')
        Assert-Igual "consumo E-65 $($sh.Nombre): la senal de vida es de ese dibujo" $sesion $senal.sessionId
        Assert-Igual "consumo E-65 $($sh.Nombre): con integrationVersion 1.2.0" '1.2.0' $senal.integrationVersion
        Assert-Igual "consumo E-65 $($sh.Nombre): con la huella del comando" `
            ($comandoCc -replace "^.* '([0-9a-f]{64})'$", '$1') $senal.configurationFingerprint
        Assert-Igual "consumo E-57 $($sh.Nombre): sin NO_COLOR en la statusLine, presentation.ansi ENABLED" `
            'ENABLED' $senal.presentation.ansi
        $ultimaSesionCc = $sesion
    }
    $politicaDespues = @()
    if (Test-Path -LiteralPath $rutaPoliticaCc) { $politicaDespues = [System.IO.File]::ReadAllBytes($rutaPoliticaCc) }
    Assert-Verdadero 'consumo E-68 entre los dibujos no se toco harness.presupuesto.json' `
        ($politicaAntes.Count -gt 0 -and
         [Convert]::ToBase64String([byte[]]$politicaAntes) -ceq [Convert]::ToBase64String([byte[]]$politicaDespues))
    $barraCc = Get-EstadoBarraCc $demoCc
    Assert-Igual 'consumo E-65 la bienvenida toma la senal como prueba: ACTIVE' 'ACTIVE' $barraCc.state
    Assert-Igual 'consumo E-65 y sin reinicio pendiente' 'False' ([string]$barraCc.reloadRequired)

    # -- E-38: instalar en un proyecto que ya tiene una politica ---------------------------------
    $propia = '{' + "`r`n" + '  "policyId": "gcba-tramites",  "currency": "USD", "billingMode": "SUBSCRIPTION",' + "`r`n" +
              '  "task": { "softLimit": 5.0, "hardLimit": 20.0 },' + "`r`n" +
              '  "statusBar": { "warningAt": 0.5, "errorAt": 0.9, "contextWarningAt": 0.6, "contextErrorAt": 0.85 }' + "`r`n" + '}' + "`r`n"
    $rutaPropia = Join-Path $conPoliticaCc '.claude\harness.presupuesto.json'
    New-Item -ItemType Directory -Path (Split-Path -Parent $rutaPropia) -Force | Out-Null
    [System.IO.File]::WriteAllText($rutaPropia, $propia, $utf8Cc)
    $bytesPropia = [System.IO.File]::ReadAllBytes($rutaPropia)
    $r = Invoke-InstaladorCc @('-Project', $conPoliticaCc, '-Usuario', 'Ana Prueba')
    Assert-Igual 'consumo E-38 la instalacion sale 0' 0 $r.Codigo
    Assert-Verdadero 'consumo E-38 la politica que ya habia queda igual, byte a byte' `
        ([Convert]::ToBase64String([System.IO.File]::ReadAllBytes($rutaPropia)) -ceq [Convert]::ToBase64String($bytesPropia))
    Assert-Contiene 'consumo E-38 y la instalacion dice que no la toca' 'harness.presupuesto.json ya exist' $r.Salida
    Assert-Contiene 'consumo E-38 los umbrales que dice son los de esa politica' `
        'Umbrales de contexto configurados: WARNING 60% / ERROR 85%' $r.Salida

    # -- E-39: -Update en un proyecto sin politica ------------------------------------------------
    Remove-Item -LiteralPath $rutaPoliticaCc -Force -ErrorAction SilentlyContinue
    $r = Invoke-InstaladorCc @('-Project', $demoCc, '-Update')
    Assert-Igual 'consumo E-39 el -Update sale 0' 0 $r.Codigo
    Assert-Verdadero 'consumo E-39 el -Update la crea' (Test-Path -LiteralPath $rutaPoliticaCc)
    Assert-Verdadero 'consumo E-39 igual a la plantilla, byte a byte' ((Test-Path -LiteralPath $rutaPoliticaCc) -and
        ([Convert]::ToBase64String([System.IO.File]::ReadAllBytes($rutaPoliticaCc)) -ceq
         [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($plantillaCc))))

    # -- E-40 / E-46: -Update con una politica del proyecto sin umbrales de contexto ----------------
    $sinUmbrales = '{"policyId":"gcba-tramites","currency":"USD","billingMode":"SUBSCRIPTION",' +
                   '"task":{"softLimit":5.0,"hardLimit":20.0},"project":null,' +
                   '"statusBar":{"warningAt":0.5,"errorAt":0.9}}'
    [System.IO.File]::WriteAllText($rutaPoliticaCc, $sinUmbrales, $utf8Cc)
    $bytesSin = [System.IO.File]::ReadAllBytes($rutaPoliticaCc)
    $r = Invoke-InstaladorCc @('-Project', $demoCc, '-Update')
    Assert-Igual 'consumo E-40 el -Update sale 0' 0 $r.Codigo
    $igualSin = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($rutaPoliticaCc)) -ceq [Convert]::ToBase64String($bytesSin)
    Assert-Verdadero 'consumo E-40 una politica sin umbrales de contexto queda igual, byte a byte' $igualSin
    Assert-Verdadero 'consumo E-46 -Update no cambia una politica PROJECT sin umbrales de contexto' $igualSin
    Assert-Contiene 'consumo E-40 y dice por nombre el que falta: contextWarningAt' 'contextWarningAt' $r.Salida
    Assert-Contiene 'consumo E-40 y contextErrorAt' 'contextErrorAt' $r.Salida
    Assert-Verdadero 'consumo E-40 sin prometer umbrales que no hay' (-not $r.Salida.Contains('Umbrales de contexto configurados'))

    # -- E-66: de un renderizador 1.1.0 a 1.2.0 ----------------------------------------------------
    # El proyecto queda como lo dejaba una instalacion con el renderizador 1.1.0: la version en el
    # archivo instalado y en el lockfile, registrada y dibujada. Despues, -Update.
    [System.IO.File]::WriteAllText($rutaPoliticaCc, [System.IO.File]::ReadAllText($plantillaCc), $utf8Cc)
    $bytesDefault = [System.IO.File]::ReadAllBytes($rutaPoliticaCc)
    $renderizadorCc = Join-Path $demoCc '.claude\harness\bin\desarrollo\contabilidad\statusline.py'
    $bienvenidaCc = Join-Path $demoCc '.claude\harness\hooks\lib\bienvenida.py'
    $texto = [System.IO.File]::ReadAllText($renderizadorCc)
    $texto = [regex]::Replace($texto, '(?m)^INTEGRATION_VERSION = "[^"]+"', 'INTEGRATION_VERSION = "1.1.0"')
    [System.IO.File]::WriteAllText($renderizadorCc, $texto, $utf8Cc)
    $rutaLockCc = Join-Path $demoCc '.claude\harness.lock.json'
    $lockCc = Read-JsonCc $rutaLockCc
    foreach ($a in $lockCc.archivos) {
        if ($a.ruta -eq '.claude\harness\bin\desarrollo\contabilidad\statusline.py') {
            $a.sha256 = (Get-FileHash -Path $renderizadorCc -Algorithm SHA256).Hash
        }
    }
    [System.IO.File]::WriteAllText($rutaLockCc, (ConvertTo-Json -InputObject $lockCc -Depth 20), $utf8Cc)
    & python $bienvenidaCc registrar $demoCc --barra-probada 2>&1 | Out-Null
    Start-Sleep -Milliseconds 1100
    $shPs = $shellsCc[0]
    $fuente = Join-Path $baseCc ($ultimaSesionCc + '.jsonl')
    Invoke-ShellCc -Exe $shPs.Exe -Previos $shPs.Previos -Comando $comandoCc -Json (Get-StdinCc $ultimaSesionCc $fuente 'usable') | Out-Null
    & python $bienvenidaCc registrar $demoCc --barra-probada 2>&1 | Out-Null
    $antes = Get-EstadoBarraCc $demoCc
    Assert-Igual 'consumo E-66 antes: el renderizador 1.1.0 registrado' '1.1.0' $antes.integrationVersion
    Assert-Igual 'consumo E-66 antes: y activo con su senal de 1.1.0' 'ACTIVE' $antes.state

    $r = Invoke-InstaladorCc @('-Project', $demoCc, '-Update')
    Assert-Igual 'consumo E-66 el -Update sale 0' 0 $r.Codigo
    Assert-Verdadero 'consumo E-66 el -Update trajo el renderizador 1.2.0' `
        ([System.IO.File]::ReadAllText($renderizadorCc) -match '(?m)^INTEGRATION_VERSION = "1\.2\.0"')
    Assert-Verdadero 'consumo E-66 y no lo trato como editado a mano' (-not (Test-Path -LiteralPath ($renderizadorCc + '.nuevo')))
    Assert-Verdadero 'consumo E-40 el -Update deja la politica por defecto como estaba, byte a byte' `
        ([Convert]::ToBase64String([System.IO.File]::ReadAllBytes($rutaPoliticaCc)) -ceq [Convert]::ToBase64String($bytesDefault))
    $despues = Get-EstadoBarraCc $demoCc
    Assert-Igual 'consumo E-66 despues del -Update: RELOAD_REQUIRED' 'RELOAD_REQUIRED' $despues.state
    Assert-Igual 'consumo E-66 con la version nueva registrada' '1.2.0' $despues.integrationVersion
    Assert-Contiene 'consumo E-66 y el -Update pide reiniciar' 'Context Bar configurada. Reinici' $r.Salida

    # Una senal de 1.1.0 dibujada despues del -Update, con la huella de ahora, no lo saca.
    Start-Sleep -Milliseconds 1100
    $huellaCc = $despues.configurationFingerprint
    & python -c "import importlib.util, sys; s = importlib.util.spec_from_file_location('b', sys.argv[1]); b = importlib.util.module_from_spec(s); s.loader.exec_module(b); b.escribir_senal_de_vida(sys.argv[2], sys.argv[3], b.BLOCK4_OK, '1.1.0', huella=sys.argv[4])" $bienvenidaCc $demoCc $ultimaSesionCc $huellaCc 2>&1 | Out-Null
    Assert-Igual 'consumo E-66 una senal 1.1.0 con la huella nueva no lo saca: sigue RELOAD_REQUIRED' `
        'RELOAD_REQUIRED' (Get-EstadoBarraCc $demoCc).state
    Start-Sleep -Milliseconds 1100
    $x = Invoke-ShellCc -Exe $shPs.Exe -Previos $shPs.Previos -Comando $comandoCc -Json (Get-StdinCc $ultimaSesionCc $fuente 'usable')
    Assert-Igual 'consumo E-66 el comando registrado dibuja con el renderizador 1.2.0' '1.2.0' `
        (Read-JsonCc (Join-Path $demoCc '.claude\runtime\contextbar.json')).integrationVersion
    $final = Get-EstadoBarraCc $demoCc
    Assert-Igual 'consumo E-66 con la senal 1.2.0 y la huella nueva pasa a ACTIVE' 'ACTIVE' $final.state
    Assert-Igual 'consumo E-66 y sin reinicio pendiente' 'False' ([string]$final.reloadRequired)
}
finally {
    Remove-Item $baseCc -Recurse -Force -ErrorAction SilentlyContinue
}
