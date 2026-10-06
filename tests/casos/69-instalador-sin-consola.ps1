# Qualification Gate 1, Q2: el instalador bajo powershell.exe -NonInteractive con una consola de
# verdad como stdin. Spec: docs/cambios/flow-governance/qualification-gate-1.md, E-10 a E-16, que
# construye E-01 a E-05 de docs/cambios/instalador-sin-consola/spec.md.
#
# La compuerta corre con stdin redirigido, y un hijo que lo hereda no reproduce el caso. Por eso
# cada corrida acá abre un envoltorio con su propia consola, oculta (Start-Process -WindowStyle
# Hidden), y el instalador hereda esa consola. La sonda de E-16 afirma aparte que el hijo la ve
# como consola: si no, los demás no prueban nada y lo dicen en vez de pasar en silencio.
#
# Cada corrida tiene un tiempo máximo. Pasarlo es colgarse esperando a alguien: se mata el árbol
# de procesos y el escenario falla.

Set-Grupo 'Qualification Gate 1 - el instalador sin nadie a quien preguntar (Q2)'

$scInstalador = Join-Path $script:Raiz 'install.ps1'
$scTimeoutSeg = 180
$scHuellasDeTraza = @('En línea:', 'At line:', 'CategoryInfo', 'FullyQualifiedErrorId', 'Traceback (most recent call last)')

function Invoke-InstaladorEnConsola {
    <# Corre install.ps1 -Project <nuevo> -Harness analisis <Extra> con -NonInteractive y una consola real como stdin. #>
    param([string[]] $Extra = @())
    $dir = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-consola-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    $proy = Join-Path $dir 'proyecto'
    New-Item -ItemType Directory -Path $proy -Force | Out-Null
    $sonda = Join-Path $dir 'sonda.txt'; $salida = Join-Path $dir 'salida.txt'; $codigo = Join-Path $dir 'codigo.txt'
    $citar = { param($x) "'" + ([string]$x).Replace("'", "''") + "'" }
    $extraTxt = ($Extra | ForEach-Object { if ($_ -like '-*') { $_ } else { & $citar $_ } }) -join ' '
    $envoltorio = Join-Path $dir 'envoltorio.ps1'
    # La sonda y el instalador se lanzan con el mismo prefijo: si uno cambia la forma de recibir
    # stdin, cambia el otro, y E-16 sigue midiendo lo que ve el instalador (refutación, H2).
    $lanzar = '& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass'
    [System.IO.File]::WriteAllText($envoltorio, (@(
        '[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false'
        "$lanzar -Command '[Console]::IsInputRedirected' *> $(& $citar $sonda)"
        "$lanzar -File $(& $citar $scInstalador) -Project $(& $citar $proy) -Harness analisis $extraTxt *> $(& $citar $salida)"
        "[System.IO.File]::WriteAllText($(& $citar $codigo), [string]`$LASTEXITCODE)"
    ) -join "`r`n"), (New-Object System.Text.UTF8Encoding $true))
    try {
        $p = Start-Process powershell.exe -WindowStyle Hidden -PassThru `
                 -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $envoltorio + '"'))
        $termino = $p.WaitForExit($scTimeoutSeg * 1000)
        if (-not $termino) { & taskkill.exe /PID $p.Id /T /F 2>&1 | Out-Null }
        return [pscustomobject]@{
            Termino    = $termino
            Redirigido = if (Test-Path -LiteralPath $sonda) { (Get-Content -LiteralPath $sonda -Raw).Trim() } else { '(sin sonda)' }
            Codigo     = if (Test-Path -LiteralPath $codigo) { (Get-Content -LiteralPath $codigo -Raw).Trim() } else { '(sin codigo)' }
            Salida     = if (Test-Path -LiteralPath $salida) { Get-Content -LiteralPath $salida -Raw } else { '' }
            Claude     = Test-Path -LiteralPath (Join-Path $proy '.claude')
            Lock       = Test-Path -LiteralPath (Join-Path $proy '.claude\harness.lock.json')
        }
    }
    finally { Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue }
}

function Test-SinTraza {
    param([string] $Texto)
    foreach ($h in $scHuellasDeTraza) { if ($Texto.Contains($h)) { return $false } }
    return $true
}


# ── E-11 (Q2-B) / instalador-sin-consola E-01, E-02, E-03 ────────────────────────
$scSinUsuario = Invoke-InstaladorEnConsola

# ── E-16: la premisa. El instalador vio una consola, no un stdin redirigido ──────
Assert-Igual 'QG1 E-16 el hijo tiene una consola de verdad como stdin (si no, Q2 no prueba nada)' 'False' $scSinUsuario.Redirigido

Assert-Verdadero 'QG1 E-11 (Q2-B) sin -Usuario, con consola y -NonInteractive: no se cuelga' $scSinUsuario.Termino
Assert-Igual 'QG1 E-11 (Q2-B) / instalador-sin-consola E-01 sale con codigo 1' '1' $scSinUsuario.Codigo
Assert-Contiene 'QG1 E-11 (Q2-B) / instalador-sin-consola E-01 el error pide -Usuario' '-Usuario' $scSinUsuario.Salida
Assert-Verdadero 'QG1 E-11 (Q2-B) / instalador-sin-consola E-02 no es el mensaje de PowerShell sobre el modo no interactivo' `
    (-not ($scSinUsuario.Salida -match 'modo no interactivo|non-interactive mode')) $scSinUsuario.Salida
Assert-Verdadero 'QG1 E-11 (Q2-B) / instalador-sin-consola E-03 no escribe nada en el proyecto' `
    (-not $scSinUsuario.Claude)


# ── E-15 (Q2-E): la misma corrida otra vez da lo mismo ───────────────────────────
$scOtraVez = Invoke-InstaladorEnConsola
Assert-Igual 'QG1 E-15 (Q2-E) repetida: el mismo codigo' $scSinUsuario.Codigo $scOtraVez.Codigo
Assert-Igual 'QG1 E-15 (Q2-E) repetida: la misma salida' $scSinUsuario.Salida $scOtraVez.Salida


# ── E-12 (Q2-B): una confirmación pedida, sin nadie que confirme, no es un sí ────
$scConfirmar = Invoke-InstaladorEnConsola -Extra @('-Usuario', 'Prueba Consola', '-Confirm')
Assert-Verdadero 'QG1 E-12 (Q2-B) -Confirm sin consola interactiva: no se cuelga' $scConfirmar.Termino
Assert-Verdadero 'QG1 E-12 (Q2-B) -Confirm sin nadie que confirme: sale con error' `
    ($scConfirmar.Codigo -ne '0' -and $scConfirmar.Codigo -ne '(sin codigo)') "codigo $($scConfirmar.Codigo)"
Assert-Verdadero 'QG1 E-12 (Q2-B) -Confirm sin nadie que confirme: no se instala nada (NONINTERACTIVE != AUTO_APPROVE)' `
    (-not $scConfirmar.Claude)
Assert-Contiene 'QG1 E-12 (Q2-D) y el error dice que no se pudo confirmar' '-Confirm' $scConfirmar.Salida


# ── E-12b: lo mismo para -Update, sobre un proyecto instalado ────────────────────
# Agregado después del smoke: -Update leía los hashes con Get-FileHash, que con -Confirm también
# pregunta, y fallaba con el mensaje de PowerShell antes de llegar a la confirmación propia.
$scDirUpd = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-updconfirm-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $scDirUpd -Force | Out-Null
try {
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $scInstalador `
        -Project $scDirUpd -Harness analisis -Usuario 'Prueba Update Confirm' 2>&1 | Out-Null
    $scLockUpd = Join-Path $scDirUpd '.claude\harness.lock.json'
    $scHashUpd = if (Test-Path -LiteralPath $scLockUpd) { (Get-FileHash -LiteralPath $scLockUpd).Hash } else { '' }
    # El stdin del hijo es un pipe vacío que se cierra: no hereda el de la compuerta (refutación, H3).
    $scSalidaUpd = $null | & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $scInstalador `
        -Project $scDirUpd -Update -Confirm 2>&1 | Out-String
    $scCodigoUpd = $LASTEXITCODE
    Assert-Verdadero 'QG1 E-12b -Update -Confirm sin nadie que confirme: sale con error' ($scCodigoUpd -ne 0) "codigo $scCodigoUpd"
    Assert-Verdadero 'QG1 E-12b -Update -Confirm sin nadie que confirme: el lockfile no cambio' `
        ($scHashUpd -and (Test-Path -LiteralPath $scLockUpd) -and (Get-FileHash -LiteralPath $scLockUpd).Hash -eq $scHashUpd)
    Assert-Contiene 'QG1 E-12b -Update -Confirm: el error dice que no se pudo confirmar' '-Confirm' $scSalidaUpd
    Assert-Verdadero 'QG1 E-12b -Update -Confirm: sin traza de PowerShell ni de Python' (Test-SinTraza $scSalidaUpd) $scSalidaUpd

    # E-12c: lo mismo para -Uninstall (refutación, H4).
    $scSalidaUni = $null | & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $scInstalador `
        -Project $scDirUpd -Uninstall -Confirm 2>&1 | Out-String
    $scCodigoUni = $LASTEXITCODE
    Assert-Verdadero 'QG1 E-12c -Uninstall -Confirm sin nadie que confirme: sale con error' ($scCodigoUni -ne 0) "codigo $scCodigoUni"
    Assert-Verdadero 'QG1 E-12c -Uninstall -Confirm sin nadie que confirme: no desinstala (el lockfile sigue igual)' `
        ($scHashUpd -and (Test-Path -LiteralPath $scLockUpd) -and (Get-FileHash -LiteralPath $scLockUpd).Hash -eq $scHashUpd)
    Assert-Contiene 'QG1 E-12c -Uninstall -Confirm: el error dice que no se pudo confirmar' '-Confirm' $scSalidaUni
    Assert-Verdadero 'QG1 E-12c -Uninstall -Confirm: sin traza de PowerShell ni de Python' (Test-SinTraza $scSalidaUni) $scSalidaUni
}
finally { Remove-Item -LiteralPath $scDirUpd -Recurse -Force -ErrorAction SilentlyContinue }


# ── E-13 (Q2-C): stdin cerrado ───────────────────────────────────────────────────
$scDirCerrado = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-stdincerrado-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $scDirCerrado -Force | Out-Null
try {
    $psiSc = New-Object System.Diagnostics.ProcessStartInfo
    $psiSc.FileName = 'powershell.exe'
    $psiSc.Arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $scInstalador + '" -Project "' + $scDirCerrado + '" -Harness analisis'
    $psiSc.UseShellExecute = $false
    $psiSc.CreateNoWindow = $true
    $psiSc.RedirectStandardInput = $true
    $psiSc.RedirectStandardOutput = $true
    $psiSc.RedirectStandardError = $true
    $psiSc.StandardOutputEncoding = New-Object System.Text.UTF8Encoding $false
    $pSc = [System.Diagnostics.Process]::Start($psiSc)
    $pSc.StandardInput.Close()
    $scOut = $pSc.StandardOutput.ReadToEndAsync(); $scErr = $pSc.StandardError.ReadToEndAsync()
    $scTerminoCerrado = $pSc.WaitForExit($scTimeoutSeg * 1000)
    if (-not $scTerminoCerrado) { & taskkill.exe /PID $pSc.Id /T /F 2>&1 | Out-Null }
    $scSalidaCerrado = $scOut.Result + $scErr.Result
    Assert-Verdadero 'QG1 E-13 (Q2-C) con stdin cerrado: no se cuelga' $scTerminoCerrado
    Assert-Igual 'QG1 E-13 (Q2-C) / instalador-sin-consola E-04 con stdin cerrado: sale con codigo 1' 1 $pSc.ExitCode
    Assert-Contiene 'QG1 E-13 (Q2-C) / instalador-sin-consola E-04 y pide -Usuario' '-Usuario' $scSalidaCerrado
    Assert-Verdadero 'QG1 E-13 (Q2-C) y no escribe nada en el proyecto' (-not (Test-Path -LiteralPath (Join-Path $scDirCerrado '.claude')))
}
finally { Remove-Item -LiteralPath $scDirCerrado -Recurse -Force -ErrorAction SilentlyContinue }


# ── E-14 (Q2-D): los errores salen como un mensaje, no como una traza ────────────
Assert-Verdadero 'QG1 E-14 (Q2-D) sin -Usuario: sin traza de PowerShell ni de Python' (Test-SinTraza $scSinUsuario.Salida) $scSinUsuario.Salida
Assert-Verdadero 'QG1 E-14 (Q2-D) con -Confirm: sin traza de PowerShell ni de Python' (Test-SinTraza $scConfirmar.Salida) $scConfirmar.Salida
Assert-Verdadero 'QG1 E-14 (Q2-D) con stdin cerrado: sin traza de PowerShell ni de Python' (Test-SinTraza $scSalidaCerrado) $scSalidaCerrado


# ── E-10 (Q2-A) / instalador-sin-consola E-05: con -Usuario no se pregunta nada ──
$scConUsuario = Invoke-InstaladorEnConsola -Extra @('-Usuario', 'Prueba Consola')
Assert-Verdadero 'QG1 E-10 (Q2-A) con -Usuario, consola y -NonInteractive: no se cuelga' $scConUsuario.Termino
Assert-Igual 'QG1 E-10 (Q2-A) / instalador-sin-consola E-05 sale con codigo 0' '0' $scConUsuario.Codigo
Assert-Verdadero 'QG1 E-10 (Q2-A) / instalador-sin-consola E-05 instala: deja el lockfile' $scConUsuario.Lock
Assert-Verdadero 'QG1 E-10 (Q2-A) no pregunta el nombre' (-not $scConUsuario.Salida.Contains('Cómo te llamás')) $scConUsuario.Salida
