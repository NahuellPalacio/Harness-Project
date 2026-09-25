# E-07, E-08, E-26, E-31, E-32 y E-36 de docs/cambios/bloque-1-context-bar/spec.md.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM (ver
# 00-encoding-fuentes.ps1). Los textos del instalador se comparan por su parte ASCII.
#
# Instala de verdad, en una ruta con espacios y con un `$`, y corre el comando que quedo
# registrado con `bash -c` y con `powershell.exe -NoProfile -Command`, sin CLAUDE_PROJECT_DIR y
# desde el temporal: como lo corre Claude Code, que no promete ni la variable ni el directorio.
# La prueba es independiente de la del instalador: lo que dice el instalador de si mismo no
# prueba nada.

Set-Grupo 'Instalador - la Context Bar'

$instaladorCb = Join-Path $script:Raiz 'install.ps1'

function Invoke-InstaladorCb {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instaladorCb @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

function Invoke-ShellCb {
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
    $p = [System.Diagnostics.Process]::Start($psi)
    $salida = $p.StandardOutput.ReadToEndAsync()
    $p.StandardError.ReadToEndAsync() | Out-Null
    $bytes = (New-Object System.Text.UTF8Encoding $false).GetBytes($Json)
    $p.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
    $p.StandardInput.Close()
    if (-not $p.WaitForExit(60000)) { try { $p.Kill() } catch { }; return [pscustomobject]@{ Codigo = -1; Salida = '' } }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Salida = $salida.Result }
}

function Find-BashCb {
    # El bash de Git para Windows, no el de WSL que puede estar primero en el PATH.
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

function Read-EstadoCb {
    param([string] $Proy)
    return ([System.IO.File]::ReadAllText((Join-Path $Proy '.claude\harness.installation.json')) | ConvertFrom-Json)
}

function Invoke-PythonCb {
    param([string[]] $Argumentos)
    $salida = & python @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida.Trim(); Codigo = $LASTEXITCODE }
}

$baseCb = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-cb-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$demoCb = Join-Path $baseCb 'proyecto con espacios $y'
New-Item -ItemType Directory -Path $demoCb -Force | Out-Null
[System.IO.File]::WriteAllText((Join-Path $demoCb 'CLAUDE.md'), "# Proyecto de prueba`r`n")

try {
    $r = Invoke-InstaladorCb @('-Project', $demoCb, '-Harness', 'desarrollo', '-Usuario', 'Ana Prueba')
    Assert-Igual 'la instalacion con la Context Bar sale 0' 0 $r.Codigo

    $rutaSenal = Join-Path $demoCb '.claude\runtime\contextbar.json'
    $bienvenidaCb = Join-Path $demoCb '.claude\harness\hooks\lib\bienvenida.py'
    $cliCb = Join-Path $demoCb '.claude\harness\bin\desarrollo\dev-harness.py'

    # -- E-26: recien instalada, sin senal de vida -----------------------------------------
    Assert-Contiene 'E-26 la instalacion dice que puede hacer falta reiniciar' `
        'Context Bar configurada. Reinici' $r.Salida
    Assert-Verdadero 'E-26 no hay senal de vida: la prueba del instalador no dejo ninguna' `
        (-not (Test-Path -LiteralPath $rutaSenal))
    Assert-Verdadero 'E-26 ni un libro de la prueba' `
        (-not (Test-Path -LiteralPath (Join-Path $demoCb '.claude\runtime')))
    $estado = Read-EstadoCb $demoCb
    Assert-Igual 'E-26 la barra queda RELOAD_REQUIRED' 'RELOAD_REQUIRED' $estado.runtimeComponents.contextBar.state
    Assert-Igual 'E-26 con reloadRequired' 'True' ([string]$estado.runtimeComponents.contextBar.reloadRequired)
    Assert-Igual 'E-26 y probada en los shells' 'True' ([string]$estado.runtimeComponents.contextBar.commandTested)
    $h = Invoke-PythonCb @($cliCb, 'harness', '--proyecto', $demoCb)
    Assert-Igual 'E-26 harness sale 0' 0 $h.Codigo
    Assert-Contiene 'E-26 harness dice REQUIERE REINICIO' 'REQUIERE REINICIO' $h.Salida
    Assert-Contiene 'E-26 y la accion' 'Context Bar configurada. Reinici' $h.Salida

    # -- E-36: el comando registrado, en los dos shells ------------------------------------
    $settings = [System.IO.File]::ReadAllText((Join-Path $demoCb '.claude\settings.json')) | ConvertFrom-Json
    $comando = ''
    if ($settings.PSObject.Properties['statusLine']) { $comando = [string]$settings.statusLine.command }
    Assert-Verdadero 'E-36 la barra queda registrada como statusLine' ([bool]$comando)
    Assert-Verdadero 'E-36 arranca con un ejecutable, no con una cadena entre comillas' `
        ($comando -and $comando -notmatch "^[`"'&]") $comando
    Assert-Verdadero 'E-36 usa barras /' (-not $comando.Contains('\')) $comando
    Assert-Verdadero 'E-36 sus argumentos van entre comillas simples: el renderizador y su huella' `
        ($comando -match "^\S+ '[^']+' '[0-9a-f]{64}'$") $comando
    Assert-Igual 'E-41 el comando lleva la huella de su propio bloque' `
        $estado.runtimeComponents.contextBar.configurationFingerprint ($comando -replace "^.* '([0-9a-f]{64})'$", '$1')
    Assert-Contiene 'E-36 con la ruta absoluta del proyecto' `
        (($demoCb -replace '\\', '/') + '/.claude/harness/bin/desarrollo/contabilidad/statusline.py') $comando
    Assert-Contiene 'E-36 el instalador lo probo en los dos' 'corre y dibuja en Git Bash y PowerShell' $r.Salida

    $sesionCb = 's-cb54-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8)
    $fuenteCb = Join-Path $baseCb 'sesion.jsonl'
    $lineaCb = '{"type":"assistant","sessionId":"' + $sesionCb + '","timestamp":"2026-09-24T10:00:00",' +
               '"message":{"id":"msg_1","model":"m-cb54","usage":{"input_tokens":10,"output_tokens":100,' +
               '"cache_read_input_tokens":5000,"cache_creation_input_tokens":200}}}'
    [System.IO.File]::WriteAllText($fuenteCb, $lineaCb + "`n", (New-Object System.Text.UTF8Encoding $false))
    $jsonCb = '{"session_id":"' + $sesionCb + '","transcript_path":"' + ($fuenteCb -replace '\\', '/') + '"}'

    $bashCb = Find-BashCb
    Assert-Verdadero 'E-36 hay Git Bash para probar el comando' ([bool]$bashCb) 'no se encontro bash.exe de Git'
    $shellsCb = @(@{ Nombre = 'powershell -NoProfile -Command'
                     Exe = (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')
                     Previos = @('-NoProfile', '-Command') })
    if ($bashCb) { $shellsCb += @{ Nombre = 'bash -c'; Exe = $bashCb; Previos = @('-c') } }
    # Una senal del mismo segundo que el registro no prueba nada (E-41): se deja pasar el segundo.
    Start-Sleep -Milliseconds 1100
    foreach ($sh in $shellsCb) {
        $x = Invoke-ShellCb -Exe $sh.Exe -Previos $sh.Previos -Comando $comando -Json $jsonCb
        $lineas = @(($x.Salida -split "`r?`n") | Where-Object { $_.Trim() })
        Assert-Igual "E-36 $($sh.Nombre): sale 0" 0 $x.Codigo
        Assert-Igual "E-36 $($sh.Nombre): dibuja una linea" 1 $lineas.Count
        Assert-Verdadero "E-36 $($sh.Nombre): con lo que ingirio el Bloque 4, no el aviso sin datos" `
            ($lineas.Count -eq 1 -and $lineas[0].StartsWith('HARNESS | m-cb54 | ')) $x.Salida
    }
    $senal = [System.IO.File]::ReadAllText($rutaSenal) | ConvertFrom-Json
    Assert-Igual 'E-36 y dejo la senal de vida de esa sesion' $sesionCb $senal.sessionId
    Assert-Igual 'E-36 con la huella del statusLine registrado' `
        $estado.runtimeComponents.contextBar.configurationFingerprint $senal.configurationFingerprint

    # -- E-08: un -Update sin cambios no marca reinicio ------------------------------------
    $antes = Read-EstadoCb $demoCb
    $r = Invoke-InstaladorCb @('-Project', $demoCb, '-Update')
    Assert-Igual 'E-08 el -Update sale 0' 0 $r.Codigo
    $despues = Read-EstadoCb $demoCb
    Assert-Igual 'E-08 ninguna huella cambio' `
        (ConvertTo-Json $antes.runtimeComponents.contextBar.fingerprints -Compress) `
        (ConvertTo-Json $despues.runtimeComponents.contextBar.fingerprints -Compress)
    Assert-Igual 'E-08 no marca reinicio' 'False' ([string]$despues.runtimeComponents.contextBar.reloadRequired)
    Assert-Verdadero 'E-08 ni queda RELOAD_REQUIRED' ($despues.runtimeComponents.contextBar.state -ne 'RELOAD_REQUIRED') `
        $despues.runtimeComponents.contextBar.state
    Assert-Igual 'E-08 ni cambia la fecha de validacion' `
        $antes.runtimeComponents.contextBar.lastValidatedAt $despues.runtimeComponents.contextBar.lastValidatedAt
    Assert-Verdadero 'E-08 y el aviso no pide reiniciar' (-not $r.Salida.Contains('Context Bar configurada. Reinici'))
    Assert-Igual 'E-08 la prueba del -Update dejo la senal como estaba' $sesionCb `
        (([System.IO.File]::ReadAllText($rutaSenal) | ConvertFrom-Json).sessionId)

    # -- E-31: un cambio en el bloque statusLine cambia configurationFingerprint -----------
    $huellaCanonica = $despues.runtimeComponents.contextBar.configurationFingerprint
    # Lo que habria registrado una version anterior con otro comando: se escribe, se registra
    # y despues settings.json vuelve a ser el instalado, byte a byte. Editarlo y dejarlo seria
    # otra cosa: -Update conserva lo que la persona edito a mano.
    $rutaSettingsCb = Join-Path $demoCb '.claude\settings.json'
    $settingsInstalado = [System.IO.File]::ReadAllBytes($rutaSettingsCb)
    # El comando cambiado lleva, como el de verdad, su propia huella al final.
    $baseOtro = ($comando -replace " '[0-9a-f]{64}'$", '') + " '--otro'"
    $s = [System.IO.File]::ReadAllText((Join-Path $demoCb '.claude\settings.json')) | ConvertFrom-Json
    $s.statusLine.command = $baseOtro
    [System.IO.File]::WriteAllText((Join-Path $demoCb '.claude\settings.json'), (ConvertTo-Json $s -Depth 20),
                                   (New-Object System.Text.UTF8Encoding $false))
    $huellaNueva = (Invoke-PythonCb @($bienvenidaCb, 'huella', $demoCb)).Salida
    $comandoOtro = "$baseOtro '$huellaNueva'"
    $s.statusLine.command = $comandoOtro
    [System.IO.File]::WriteAllText((Join-Path $demoCb '.claude\settings.json'), (ConvertTo-Json $s -Depth 20),
                                   (New-Object System.Text.UTF8Encoding $false))
    Assert-Igual 'E-31 escribir la huella como argumento no la cambia' $huellaNueva `
        (Invoke-PythonCb @($bienvenidaCb, 'huella', $demoCb)).Salida
    Assert-Verdadero 'E-31 el bloque cambiado tiene otra huella' `
        ($huellaNueva -match '^[0-9a-f]{64}$' -and $huellaNueva -ne $huellaCanonica) $huellaNueva
    $reg = Invoke-PythonCb @($bienvenidaCb, 'registrar', $demoCb, '--barra-probada')
    Assert-Igual 'E-31 el registro sale 0' 0 $reg.Codigo
    $e = Read-EstadoCb $demoCb
    Assert-Igual 'E-31 configurationFingerprint es la del bloque nuevo' $huellaNueva `
        $e.runtimeComponents.contextBar.configurationFingerprint
    Assert-Igual 'E-31 y la huella statusLine guardada tambien' $huellaNueva `
        $e.runtimeComponents.contextBar.fingerprints.statusLine

    # -- E-07: el -Update que cambia el statusLine marca reinicio --------------------------
    # El -Update vuelve a escribir el statusLine de esta version: para el estado guardado, el
    # bloque cambio. Es lo que pasa cuando una version nueva registra otro comando. Antes se
    # salda el reinicio que dejo E-31 -la barra se dibuja con el bloque cambiado-: si no, el
    # reloadRequired de abajo ya estaba y no prueba nada del -Update.
    $shellPs = $shellsCb[0]
    Start-Sleep -Milliseconds 1100
    Invoke-ShellCb -Exe $shellPs.Exe -Previos $shellPs.Previos -Comando $comandoOtro -Json $jsonCb | Out-Null
    Invoke-PythonCb @($bienvenidaCb, 'registrar', $demoCb, '--barra-probada') | Out-Null
    Assert-Igual 'E-07 antes del -Update: sin reinicio pendiente' 'False' `
        ([string](Read-EstadoCb $demoCb).runtimeComponents.contextBar.reloadRequired)
    [System.IO.File]::WriteAllBytes($rutaSettingsCb, $settingsInstalado)
    $r = Invoke-InstaladorCb @('-Project', $demoCb, '-Update')
    Assert-Igual 'E-07 el -Update sale 0' 0 $r.Codigo
    $e = Read-EstadoCb $demoCb
    Assert-Igual 'E-07 vuelve el statusLine de esta version' $huellaCanonica `
        $e.runtimeComponents.contextBar.configurationFingerprint
    Assert-Igual 'E-07 marca reloadRequired' 'True' ([string]$e.runtimeComponents.contextBar.reloadRequired)
    Assert-Igual 'E-07 RELOAD_REQUIRED' 'RELOAD_REQUIRED' $e.runtimeComponents.contextBar.state
    Assert-Contiene 'E-07 y lo dice' 'Context Bar configurada. Reinici' $r.Salida

    # -- E-41: el comando viejo, que sigue corriendo en una sesion sin reiniciar, no lo saca --
    Start-Sleep -Milliseconds 1100
    Invoke-ShellCb -Exe $shellPs.Exe -Previos $shellPs.Previos -Comando $comandoOtro -Json $jsonCb | Out-Null
    Invoke-PythonCb @($bienvenidaCb, 'registrar', $demoCb, '--barra-probada') | Out-Null
    $e = Read-EstadoCb $demoCb
    Assert-Igual 'E-41 despues del -Update, el comando viejo deja RELOAD_REQUIRED' 'RELOAD_REQUIRED' `
        $e.runtimeComponents.contextBar.state
    Assert-Igual 'E-41 y reloadRequired' 'True' ([string]$e.runtimeComponents.contextBar.reloadRequired)

    # -- E-32: un cambio en la version del renderizador se detecta -------------------------
    # Primero se salda el reinicio: la barra se dibuja con la configuracion nueva y el
    # registro, sin cambios, lo anota.
    Invoke-ShellCb -Exe $shellPs.Exe -Previos $shellPs.Previos -Comando $comando -Json $jsonCb | Out-Null
    Invoke-PythonCb @($bienvenidaCb, 'registrar', $demoCb, '--barra-probada') | Out-Null
    $e = Read-EstadoCb $demoCb
    Assert-Igual 'E-32 antes: sin reinicio pendiente' 'False' ([string]$e.runtimeComponents.contextBar.reloadRequired)
    $versionAntes = $e.runtimeComponents.contextBar.integrationVersion
    $huellaAntes = $e.runtimeComponents.contextBar.fingerprints.renderer
    $renderizador = Join-Path $demoCb '.claude\harness\bin\desarrollo\contabilidad\statusline.py'
    $texto = [System.IO.File]::ReadAllText($renderizador)
    $texto = [regex]::Replace($texto, '(?m)^INTEGRATION_VERSION = "[^"]+"', 'INTEGRATION_VERSION = "9.9.9"')
    [System.IO.File]::WriteAllText($renderizador, $texto, (New-Object System.Text.UTF8Encoding $false))
    $reg = Invoke-PythonCb @($bienvenidaCb, 'registrar', $demoCb, '--barra-probada')
    Assert-Igual 'E-32 el registro sale 0' 0 $reg.Codigo
    $e = Read-EstadoCb $demoCb
    Assert-Igual 'E-32 la version nueva del renderizador' '9.9.9' $e.runtimeComponents.contextBar.integrationVersion
    Assert-Verdadero 'E-32 distinta de la de antes' ($versionAntes -ne '9.9.9') $versionAntes
    Assert-Verdadero 'E-32 la huella del renderizador cambio' `
        ($e.runtimeComponents.contextBar.fingerprints.renderer -ne $huellaAntes)
    Assert-Igual 'E-32 y marca reinicio' 'True' ([string]$e.runtimeComponents.contextBar.reloadRequired)
    Assert-Igual 'E-32 RELOAD_REQUIRED' 'RELOAD_REQUIRED' $e.runtimeComponents.contextBar.state
}
finally {
    Remove-Item $baseCb -Recurse -Force -ErrorAction SilentlyContinue
}
