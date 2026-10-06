# Qualification Gate 1, Q1: un test del instalador que rompe la fábrica no puede dejar roto el
# árbol, ni aunque lo maten. Spec: docs/cambios/flow-governance/qualification-gate-1.md,
# E-01 a E-09.
#
# Lo que se rompe acá se rompe en copias del temporal (tests\isolated-factory.ps1). El árbol se
# compara byte a byte y con git status antes y después. E-03 mata de verdad a un proceso hijo con
# su copia rota: nunca se mata nada que trabaje sobre el árbol.

. (Join-Path $script:Raiz 'tests\isolated-factory.ps1')

Set-Grupo 'Qualification Gate 1 - la fabrica aislada (Q1)'

$qgRotos = @('comun\hooks\lib\zonas.py', 'comun\hooks\pre-tool-use.py')

function Get-QgHuellaDelArbol {
    <# Los bytes de los dos archivos que E-20/E-27 rompen, y el git status entero del árbol. #>
    $h = [ordered]@{}
    foreach ($r in $qgRotos) { $h[$r] = (Get-FileHash -LiteralPath (Join-Path $script:Raiz $r) -Algorithm SHA256).Hash }
    $h['git status'] = (& git -C $script:Raiz status --porcelain --untracked-files=all 2>&1 | Out-String)
    return ($h | ConvertTo-Json -Compress)
}

function Get-QgCopiasPropias {
    <# Las copias del temporal cuyo dueño es este proceso. #>
    $yo = Get-DuenoDeProceso
    @(Get-ChildItem -LiteralPath ([System.IO.Path]::GetTempPath()) -Directory -Filter ($script:PrefijoFabrica + '*') -ErrorAction SilentlyContinue |
      Where-Object {
          $m = Join-Path $_.FullName $script:MarcaFabrica
          if (-not (Test-Path -LiteralPath $m)) { return $false }
          try { $d = [System.IO.File]::ReadAllText($m) | ConvertFrom-Json } catch { return $false }
          ([int]$d.pid -eq $yo.pid) -and ([string]$d.arranque -eq $yo.arranque)
      })
}

$qgHuellaInicial = Get-QgHuellaDelArbol
$qgRotura = "`ndef (((`n"


# ── E-01 (Q1-A): una aserción que falla después de romper la copia ───────────────
$qgDirE01 = $null
$qgRotaE01 = $false
Invoke-EnFabricaAislada {
    param($f)
    $script:qgDirE01 = $f
    foreach ($r in $qgRotos) { [System.IO.File]::AppendAllText((Join-Path $f $r), $qgRotura) }
    $script:qgRotaE01 = ([System.IO.File]::ReadAllText((Join-Path $f $qgRotos[0]))).Contains('def (((')
    # Una aserción de la suite que falla no tira: registra y el cuerpo sigue hasta el final.
    # Ese es el camino de un test que falla; uno de verdad acá ensuciaría la compuerta.
}
Assert-Verdadero 'QG1 E-01 (Q1-A) la copia se rompio de verdad' $qgRotaE01
Assert-Verdadero 'QG1 E-01 (Q1-A) despues de un fallo, la copia ya no existe' `
    ($qgDirE01 -and -not (Test-Path -LiteralPath $qgDirE01)) "quedo: $qgDirE01"
Assert-Igual 'QG1 E-01 (Q1-A) el arbol quedo byte a byte igual' $qgHuellaInicial (Get-QgHuellaDelArbol)


# ── E-02 (Q1-B, Q1-F): una excepción con la copia rota ───────────────────────────
$qgDirE02 = $null
$qgMensajeE02 = $null
try {
    Invoke-EnFabricaAislada {
        param($f)
        $script:qgDirE02 = $f
        foreach ($r in $qgRotos) { [System.IO.File]::AppendAllText((Join-Path $f $r), $qgRotura) }
        throw 'QG1-E02 explota a proposito'
    }
} catch { $qgMensajeE02 = $_.Exception.Message }
Assert-Igual 'QG1 E-02 (Q1-F) la excepcion sale tal cual, no se la traga la limpieza' 'QG1-E02 explota a proposito' $qgMensajeE02
Assert-Verdadero 'QG1 E-02 (Q1-B) despues de una excepcion, la copia ya no existe' `
    ($qgDirE02 -and -not (Test-Path -LiteralPath $qgDirE02)) "quedo: $qgDirE02"
Assert-Igual 'QG1 E-02 (Q1-B) el arbol quedo byte a byte igual' $qgHuellaInicial (Get-QgHuellaDelArbol)


# ── E-03 (Q1-C): un proceso hijo matado en la ventana, con la copia rota ─────────
#
# El hijo carga el mismo mecanismo, rompe su copia dentro de Invoke-EnFabricaAislada y espera.
# Se lo mata con taskkill /T /F: el finally del hijo no corre, que es justo el caso.
$qgBaseE03 = Join-Path ([System.IO.Path]::GetTempPath()) ('qg1-hijo-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $qgBaseE03 -Force | Out-Null
$qgListo = Join-Path $qgBaseE03 'listo.txt'
$qgHijo = Join-Path $qgBaseE03 'hijo.ps1'
[System.IO.File]::WriteAllText($qgHijo, @"
`$script:Raiz = '$($script:Raiz.Replace("'", "''"))'
. (Join-Path `$script:Raiz 'tests\isolated-factory.ps1')
Invoke-EnFabricaAislada {
    param(`$f)
    foreach (`$r in @('$($qgRotos -join "','")')) { [System.IO.File]::AppendAllText((Join-Path `$f `$r), "``ndef (((``n") }
    [System.IO.File]::WriteAllText('$qgListo.tmp', `$f)
    [System.IO.File]::Move('$qgListo.tmp', '$qgListo')
    Start-Sleep -Seconds 300
}
"@, (New-Object System.Text.UTF8Encoding $true))

$qgDirE03 = $null
$qgRotaE03 = $false
$qgMatado = $false
try {
    $psiQg = New-Object System.Diagnostics.ProcessStartInfo
    $psiQg.FileName = 'powershell.exe'
    $psiQg.Arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $qgHijo + '"'
    $psiQg.UseShellExecute = $false
    $psiQg.RedirectStandardInput = $true
    $psiQg.CreateNoWindow = $true
    $pQg = [System.Diagnostics.Process]::Start($psiQg)
    $pQg.StandardInput.Close()
    $relojQg = [System.Diagnostics.Stopwatch]::StartNew()
    while (-not (Test-Path -LiteralPath $qgListo) -and -not $pQg.HasExited -and $relojQg.Elapsed.TotalSeconds -lt 90) {
        Start-Sleep -Milliseconds 100
    }
    if (Test-Path -LiteralPath $qgListo) {
        $qgDirE03 = [System.IO.File]::ReadAllText($qgListo).Trim()
        $qgRotaE03 = ([System.IO.File]::ReadAllText((Join-Path $qgDirE03 $qgRotos[1]))).Contains('def (((')
    }
    & taskkill.exe /PID $pQg.Id /T /F 2>&1 | Out-Null
    $qgMatado = $pQg.WaitForExit(15000)
}
finally {
    Remove-Item -LiteralPath $qgBaseE03 -Recurse -Force -ErrorAction SilentlyContinue
}
Assert-Verdadero 'QG1 E-03 (Q1-C) el hijo llego a la ventana: su copia estaba rota' $qgRotaE03
Assert-Verdadero 'QG1 E-03 (Q1-C) el hijo murio matado, sin terminar' ($qgMatado -and $pQg.ExitCode -ne 0) "exit $($pQg.ExitCode)"
Assert-Verdadero 'QG1 E-03 (Q1-C) la copia del hijo matado quedo en el temporal (su finally no corrio)' `
    ($qgDirE03 -and (Test-Path -LiteralPath $qgDirE03))
Assert-Igual 'QG1 E-03 (Q1-C) el arbol quedo byte a byte igual despues de matar al hijo' $qgHuellaInicial (Get-QgHuellaDelArbol)


# ── E-04 (Q1-D): la corrida siguiente barre la huérfana y arranca limpia ─────────
$qgDirE04 = New-FabricaAislada
try {
    Assert-Verdadero 'QG1 E-04 (Q1-D) la corrida siguiente borro la copia del hijo matado' `
        ($qgDirE03 -and -not (Test-Path -LiteralPath $qgDirE03)) "quedo: $qgDirE03"
    foreach ($r in $qgRotos) {
        Assert-Igual "QG1 E-04 (Q1-D) la copia nueva trae $r igual al arbol" `
            (Get-FileHash -LiteralPath (Join-Path $script:Raiz $r) -Algorithm SHA256).Hash `
            (Get-FileHash -LiteralPath (Join-Path $qgDirE04 $r) -Algorithm SHA256).Hash
    }
    # La copia es la fábrica entera: cada archivo versionado de lo que install.ps1 lee está.
    $qgFaltan = @()
    $qgVersionados = @(& git -C $script:Raiz ls-files -- $script:PartesDeLaFabrica 2>$null)
    foreach ($v in $qgVersionados) {
        if (-not (Test-Path -LiteralPath (Join-Path $qgDirE04 $v))) { $qgFaltan += $v }
    }
    Assert-Verdadero 'QG1 E-04 (Q1-D) la copia trae cada archivo versionado de las partes que copia' `
        (($qgVersionados.Count -gt 0) -and ($qgFaltan.Count -eq 0)) ("faltan: " + ($qgFaltan -join ', '))
    # Y las partes salen de install.ps1, no de la lista del mecanismo: cada ruta literal que el
    # instalador arma con Join-Path $script:Repo tiene que estar en la copia.
    $qgTextoInstalador = [System.IO.File]::ReadAllText((Join-Path $script:Raiz 'install.ps1'))
    $qgLeidas = @([regex]::Matches($qgTextoInstalador, 'Join-Path \$script:Repo\s+\(?[''"]([^''"$]+)') |
                  ForEach-Object { $_.Groups[1].Value.TrimEnd('\') } | Sort-Object -Unique)
    $qgNoCopiadas = @($qgLeidas | Where-Object { -not (Test-Path -LiteralPath (Join-Path $qgDirE04 $_)) })
    Assert-Verdadero 'QG1 E-04 (Q1-D) la copia trae cada ruta que install.ps1 lee de su carpeta' `
        (($qgLeidas.Count -gt 0) -and ($qgNoCopiadas.Count -eq 0)) ("no copiadas: " + ($qgNoCopiadas -join ', '))
}
finally { Remove-FabricaAislada -Dir $qgDirE04 }


# ── E-05: la limpieza no toca lo que no es huérfano ──────────────────────────────
$qgViva = New-FabricaAislada
$qgSinMarca = Join-Path ([System.IO.Path]::GetTempPath()) ($script:PrefijoFabrica + 'sinmarca-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 6))
New-Item -ItemType Directory -Path $qgSinMarca -Force | Out-Null
try {
    Clear-FabricasHuerfanas | Out-Null
    Assert-Verdadero 'QG1 E-05 la limpieza no borra la copia de un dueno vivo' (Test-Path -LiteralPath $qgViva)
    Assert-Verdadero 'QG1 E-05 la limpieza no borra una carpeta sin marca' (Test-Path -LiteralPath $qgSinMarca)
}
finally {
    Remove-FabricaAislada -Dir $qgViva
    Remove-Item -LiteralPath $qgSinMarca -Recurse -Force -ErrorAction SilentlyContinue
}

# E-05b: un dueño vivo cuyo arranque no se puede leer (una compuerta elevada vista desde una que no
# lo está) es vivo. Agregado tras la refutación (H1). System, pid 4, vive siempre y no deja leer
# su arranque; la premisa se afirma aparte.
Assert-Igual 'QG1 E-05b premisa: el arranque de System (pid 4) es ilegible' 'ilegible' ([string](Get-DuenoDeProceso -IdProceso 4).arranque)
$qgIlegible = Join-Path ([System.IO.Path]::GetTempPath()) ($script:PrefijoFabrica + 'ilegible-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 6))
New-Item -ItemType Directory -Path $qgIlegible -Force | Out-Null
try {
    [System.IO.File]::WriteAllText((Join-Path $qgIlegible $script:MarcaFabrica), '{"pid":4,"arranque":"133700000000000000"}')
    Clear-FabricasHuerfanas | Out-Null
    Assert-Verdadero 'QG1 E-05b la limpieza no borra la copia de un dueno vivo con el arranque ilegible' (Test-Path -LiteralPath $qgIlegible)
}
finally { Remove-Item -LiteralPath $qgIlegible -Recurse -Force -ErrorAction SilentlyContinue }


# ── E-07 (Q1-F): el código de salida de quien falla adentro sale tal cual ────────
$qgBaseE07 = Join-Path ([System.IO.Path]::GetTempPath()) ('qg1-exit-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $qgBaseE07 -Force | Out-Null
$qgDirE07Txt = Join-Path $qgBaseE07 'dir.txt'
$qgHijoE07 = Join-Path $qgBaseE07 'hijo.ps1'
[System.IO.File]::WriteAllText($qgHijoE07, @"
`$script:Raiz = '$($script:Raiz.Replace("'", "''"))'
. (Join-Path `$script:Raiz 'tests\isolated-factory.ps1')
Invoke-EnFabricaAislada {
    param(`$f)
    [System.IO.File]::AppendAllText((Join-Path `$f 'comun\hooks\pre-tool-use.py'), "``ndef (((``n")
    [System.IO.File]::WriteAllText('$qgDirE07Txt', `$f)
    exit 7
}
"@, (New-Object System.Text.UTF8Encoding $true))
try {
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $qgHijoE07 2>&1 | Out-Null
    $qgCodigoE07 = $LASTEXITCODE
    $qgDirE07 = if (Test-Path -LiteralPath $qgDirE07Txt) { [System.IO.File]::ReadAllText($qgDirE07Txt).Trim() } else { $null }
}
finally { Remove-Item -LiteralPath $qgBaseE07 -Recurse -Force -ErrorAction SilentlyContinue }
Assert-Igual 'QG1 E-07 (Q1-F) el codigo de salida del que fallo adentro sale tal cual' 7 $qgCodigoE07
Assert-Verdadero 'QG1 E-07 (Q1-F) y su copia se borro igual' ($qgDirE07 -and -not (Test-Path -LiteralPath $qgDirE07)) "quedo: $qgDirE07"


# ── E-09: la limpieza se niega a borrar algo que no es una copia ─────────────────
$qgNegado = $null
try { Remove-FabricaAislada -Dir $script:Raiz } catch { $qgNegado = $_.Exception.Message }
Assert-Contiene 'QG1 E-09 Remove-FabricaAislada no borra el arbol' 'no es una fábrica aislada' $qgNegado
Assert-Verdadero 'QG1 E-09 el arbol sigue en pie' (Test-Path -LiteralPath (Join-Path $script:Raiz 'install.ps1'))


# ── E-06 (Q1-E): sin restos ──────────────────────────────────────────────────────
$qgPropias = @(Get-QgCopiasPropias)
Assert-Igual 'QG1 E-06 (Q1-E) no queda ninguna copia de esta corrida en el temporal' 0 $qgPropias.Count
Assert-Igual 'QG1 E-06 (Q1-E) el arbol: los mismos bytes y el mismo git status, sin archivos nuevos' `
    $qgHuellaInicial (Get-QgHuellaDelArbol)
