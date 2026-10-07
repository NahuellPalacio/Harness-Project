# Los escenarios de docs/cambios/harness-unico/spec.md que instalan de verdad: E-05 a E-11,
# E-14 a E-26, E-36 a E-51 y E-53 a E-55. Cada asercion nombra su E-nn. Lo que no instala va en
# tests/casos/63_harness_unico.py.
#
# ASCII puro a proposito: un .ps1 con caracteres no ASCII necesita BOM (ver
# 00-encoding-fuentes.ps1). Los textos del instalador se comparan por su parte ASCII.
#
# La linea de base es ea2dff7 (0.28.0 con Flow Governance): su install.ps1 se extrae con `git archive` a un temporal
# y se instala con el, una vez por variante, y cada escenario trabaja sobre una copia. Sin esa
# historia -un clon superficial- cada escenario que compara contra 0.28.0 falla en rojo con el
# motivo. E-39 corre donde se instalo y no en una copia: el statusLine lleva la ruta absoluta del
# proyecto, y en otra carpeta su huella cambiaria sola.
#
# Las unicas lineas de este archivo que pasan el parametro viejo son las de E-08 y las que
# instalan con el instalador de la base ($huViejo): E-61 lo controla.

Set-Grupo 'harness-unico - un solo producto, instalado'

$huInstalador = Join-Path $script:Raiz 'install.ps1'
$huVersion    = ([System.IO.File]::ReadAllText((Join-Path $script:Raiz 'VERSION'))).Trim()
# Era e5d7a14 (0.28.0 sola). Pisado por docs/cambios/integracion-flow-governance-0-31/spec.md:
# la base es ea2dff7, 0.28.0 con Flow Governance, que es de donde parte esta linea.
$huBase       = 'ea2dff7'
$huTmp        = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-hu-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$huUsuario    = 'Ana Prueba'
$huUtf8       = New-Object System.Text.UTF8Encoding $false
$huSalidas    = New-Object System.Collections.ArrayList     # E-11: todo lo que dijo el instalador nuevo
$huHu         = @('.claude\skills\hu-escribir\SKILL.md', '.claude\agents\hu-redactor.md', '.claude\agents\hu-refutador.md')
$huManifiestosViejos = @('.claude\harness\manifiestos\comun.json', '.claude\harness\manifiestos\desarrollo.json')


function Invoke-HuInstalador {
    <# Corre un install.ps1 por -File, como lo corre una persona. -Registrar suma la salida a E-11. #>
    param([string] $Instalador, [string[]] $Argumentos, [switch] $Registrar)
    # E-08 y E-09 hacen que PowerShell escriba su error de parametros en stderr. Con 2>&1 y
    # Stop -el del runner- ese registro tiraria aca en vez de quedar en la salida.
    $ErrorActionPreference = 'Continue'
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $Instalador @Argumentos 2>&1 | Out-String
    $codigo = $LASTEXITCODE
    if ($Registrar) { [void] $huSalidas.Add($salida) }
    return [pscustomobject]@{ Salida = $salida; Codigo = $codigo }
}


function Invoke-HuProceso {
    <# Un proceso con stdout y stderr en UTF-8, sin pasar por la tuberia de PowerShell: con
       $ErrorActionPreference en Stop, un stderr redirigido de un ejecutable nativo tira. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Directorio = '', [hashtable] $Entorno = @{},
          [string] $Entrada = $null)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardInput  = $true
    $psi.StandardOutputEncoding = $huUtf8
    $psi.StandardErrorEncoding  = $huUtf8
    if ($Directorio) { $psi.WorkingDirectory = $Directorio }
    foreach ($k in $Entorno.Keys) { $psi.EnvironmentVariables[$k] = [string]$Entorno[$k] }
    $p = [System.Diagnostics.Process]::Start($psi)
    $salida  = $p.StandardOutput.ReadToEndAsync()
    $errores = $p.StandardError.ReadToEndAsync()
    if ($null -ne $Entrada) {
        $bytes = $huUtf8.GetBytes($Entrada)
        $p.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
    }
    $p.StandardInput.Close()
    if (-not $p.WaitForExit(300000)) { try { $p.Kill() } catch { }; return [pscustomobject]@{ Codigo = -1; Salida = ''; Errores = 'no termino en 300 s' } }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Salida = $salida.Result; Errores = $errores.Result }
}


function New-HuDir {
    param([string] $Nombre)
    $d = Join-Path $huTmp $Nombre
    New-Item -ItemType Directory -Path $d -Force | Out-Null
    return $d
}


function Copy-HuProyecto {
    param([string] $Origen, [string] $Nombre)
    $d = Join-Path $huTmp $Nombre
    Copy-Item -LiteralPath $Origen -Destination $d -Recurse -Force
    return $d
}


function Read-HuJson {
    <# $null si no existe o no es JSON: un escenario roto no se lleva puestos a los demas. #>
    param([string] $Ruta)
    if (-not (Test-Path -LiteralPath $Ruta)) { return $null }
    try { return ([System.IO.File]::ReadAllText($Ruta, $huUtf8) | ConvertFrom-Json) } catch { return $null }
}


function Get-HuNormalizado {
    <# El texto con CRLF pasado a LF: la spec compara contenido asi (finales de linea). #>
    param([string] $Ruta)
    if (-not (Test-Path -LiteralPath $Ruta)) { return "<no existe $Ruta>" }
    $latin = [System.Text.Encoding]::GetEncoding(28591)
    return $latin.GetString([System.IO.File]::ReadAllBytes($Ruta)).Replace("`r`n", "`n")
}


function Get-HuHash {
    <# sha256 del contenido normalizado. #>
    param([string] $Ruta)
    $latin = [System.Text.Encoding]::GetEncoding(28591)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    return [System.BitConverter]::ToString($sha.ComputeHash($latin.GetBytes((Get-HuNormalizado $Ruta)))).Replace('-', '')
}


function Get-HuLock {
    param([string] $Proyecto)
    return (Read-HuJson (Join-Path $Proyecto '.claude\harness.lock.json'))
}


function Get-HuRutas {
    param([string] $Proyecto)
    $lock = Get-HuLock $Proyecto
    if ($null -eq $lock) { return ,@() }
    return ,@($lock.archivos | ForEach-Object { [string]$_.ruta } | Sort-Object)
}


function Get-HuClaves {
    <# Las claves del lockfile, ordenadas y unidas por coma. #>
    param([string] $Proyecto)
    $lock = Get-HuLock $Proyecto
    if ($null -eq $lock) { return '<sin lockfile>' }
    return ((@($lock.PSObject.Properties.Name) | Sort-Object) -join ',')
}


function Get-HuBloque {
    <# El bloque HARNESS:COMUN del CLAUDE.md, marcadores incluidos, normalizado. #>
    param([string] $Proyecto)
    $t = Get-HuNormalizado (Join-Path $Proyecto 'CLAUDE.md')
    $i = $t.IndexOf('<!-- HARNESS:COMUN')
    $fin = '<!-- /HARNESS:COMUN -->'
    $f = $t.IndexOf($fin)
    if ($i -lt 0 -or $f -lt $i) { return '' }
    return $t.Substring($i, $f + $fin.Length - $i)
}


function Get-HuEstado {
    param([string] $Proyecto)
    return (Read-HuJson (Join-Path $Proyecto '.claude\harness.installation.json'))
}


function Get-HuComponentes {
    <# state y errorCode de los tres componentes de runtime, en una linea comparable. #>
    param([string] $Proyecto)
    $estado = Get-HuEstado $Proyecto
    if ($null -eq $estado) { return '<sin harness.installation.json>' }
    $rc = $estado.runtimeComponents
    $partes = @()
    foreach ($c in @('block4Accounting', 'contextBar', 'securityReporting')) {
        $partes += ($c + '=' + [string]$rc.$c.state + '/' + [string]$rc.$c.errorCode)
    }
    return ($partes -join ' ')
}


function Get-HuArbol {
    <# sha256 exacto de cada archivo del proyecto, para ver si algo cambio un byte (E-50). #>
    param([string] $Proyecto)
    $h = @{}
    foreach ($f in @(Get-ChildItem -LiteralPath $Proyecto -Recurse -File -Force)) {
        $h[$f.FullName.Substring($Proyecto.Length)] = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    }
    return $h
}


function Compare-HuArbol {
    param([hashtable] $Antes, [hashtable] $Despues)
    $diferencias = @()
    foreach ($k in $Antes.Keys) {
        if (-not $Despues.ContainsKey($k)) { $diferencias += "borrado $k" }
        elseif ($Despues[$k] -ne $Antes[$k]) { $diferencias += "cambiado $k" }
    }
    foreach ($k in $Despues.Keys) { if (-not $Antes.ContainsKey($k)) { $diferencias += "nuevo $k" } }
    return ($diferencias -join ', ')
}


# La sonda: lo que se pregunta al bin instalado de un proyecto, en un proceso aparte.
$huSonda = Join-Path $huTmp 'sonda.py'
$huCodigoSonda = @'
import importlib.util, json, os, sys
bin_dir, accion = sys.argv[1], sys.argv[2]
sys.path.insert(0, bin_dir)
o = os.path.join(bin_dir, "orquestacion")
if accion == "registro":
    from orquestacion import registro_agentes as R
    r = R.reporte(desde=os.path.join(o, "registro_agentes.py"))
    out = {"summary": r["summary"], "result": r["result"],
           "orphans": sorted("%s:%s" % (x["id"], x["severity"]) for x in r["orphans"]),
           "undeclared": sorted(x["id"] for x in r["undeclared"])}
elif accion == "controles":
    from orquestacion import controles as C
    out = {"result": C.reporte(desde=os.path.join(o, "controles.py"))["result"]}
elif accion == "roster":
    from orquestacion import roster
    desde = os.path.join(o, "roster.py")
    nombres = ["dev-accesibilidad-html", "dev-api-rutas", "dev-codebase-forma", "dev-dependencias",
               "dev-infra-en-codigo"]
    out = {"checks": {n: roster.existe_check(n, desde) for n in nombres},
           "roster": bool(roster.cargar(desde))}
elif accion == "refutacion":
    from orquestacion import refutacion
    out = refutacion.contrato_del_refutador(os.path.join(o, "refutacion.py"))
elif accion == "timeout":
    spec = importlib.util.spec_from_file_location("cli_hu", os.path.join(bin_dir, "dev-harness.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = {"timeout": m.timeout_de(m.rutas_de(sys.argv[3]))}
sys.stdout.write(json.dumps(out, sort_keys=True))
'@


function Invoke-HuSonda {
    param([string] $Proyecto, [string] $Accion)
    $bin = Join-Path $Proyecto '.claude\harness\bin\desarrollo'
    $r = Invoke-HuProceso -Archivo 'python' -Argumentos ('"' + $huSonda + '" "' + $bin + '" ' + $Accion + ' "' + $Proyecto + '"') `
                          -Entorno @{ PYTHONDONTWRITEBYTECODE = '1' }
    if ($r.Codigo -ne 0) { return "la sonda $Accion fallo: $($r.Errores)" }
    return $r.Salida.Trim()
}


function Invoke-HuCli {
    <# dev-harness.py instalado de un proyecto. #>
    param([string] $Proyecto, [string] $Argumentos)
    $cli = Join-Path $Proyecto '.claude\harness\bin\desarrollo\dev-harness.py'
    return (Invoke-HuProceso -Archivo 'python' -Argumentos ('"' + $cli + '" ' + $Argumentos + ' --proyecto "' + $Proyecto + '"') `
                             -Directorio $Proyecto -Entorno @{ PYTHONDONTWRITEBYTECODE = '1' })
}


function Invoke-HuComando {
    <# Un comando de hook registrado, como lo corre Claude Code con "shell": "powershell". #>
    param([string] $Comando, [string] $Proyecto, [string] $Json)
    $ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $codificado = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($Comando))
    return (Invoke-HuProceso -Archivo $ps -Argumentos ('-NoProfile -NonInteractive -EncodedCommand ' + $codificado) `
                             -Directorio $Proyecto -Entorno @{ CLAUDE_PROJECT_DIR = $Proyecto } -Entrada $Json)
}


function Get-HuComandoDeHook {
    param([string] $Proyecto, [string] $Evento)
    $s = Read-HuJson (Join-Path $Proyecto '.claude\settings.json')
    if ($null -eq $s) { return '' }
    return [string](@($s.hooks.$Evento)[0].hooks[0].command)
}


function Test-HuDeny {
    param([string] $Salida)
    return ($Salida -match '"permissionDecision"\s*:\s*"deny"')
}


function Normalize-HuFechas {
    param([string] $Texto)
    return [regex]::Replace($Texto, '\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?', 'FECHA')
}


# Los escenarios que comparan contra 0.28.0. Sin la linea de base, cada uno falla con el motivo.
$huDeLaBase = @('E-15', 'E-16', 'E-17', 'E-18', 'E-19', 'E-20', 'E-23', 'E-36', 'E-37', 'E-38', 'E-39',
                'E-40', 'E-41', 'E-42', 'E-43', 'E-44', 'E-47', 'E-49', 'E-53', 'E-55')


try {
    New-Item -ItemType Directory -Path $huTmp -Force | Out-Null
    [System.IO.File]::WriteAllText($huSonda, $huCodigoSonda, $huUtf8)

    # -- E-05 ---------------------------------------------------------------------------
    $huParametros = @((Get-Command $huInstalador).Parameters.Keys)
    Assert-Verdadero 'E-05 install.ps1 no declara el parametro Harness' (-not ($huParametros -contains 'Harness')) `
        ($huParametros -join ', ')

    # -- E-08: el parametro viejo, en sus tres formas -----------------------------------
    foreach ($v in @('desarrollo', 'analisis', 'analisis,desarrollo')) {
        $d = New-HuDir ('e08-' + ($v -replace ',', '-'))
        $r = Invoke-HuInstalador $huInstalador @('-Project', $d, '-Harness', $v, '-Usuario', $huUsuario)   # E-08
        Assert-Verdadero "E-08 con $v sale con codigo distinto de 0" ($r.Codigo -ne 0) "codigo $($r.Codigo)"
        Assert-Contiene  "E-08 con $v la salida nombra el parametro" 'Harness' $r.Salida
        Assert-Verdadero "E-08 con $v no crea .claude, CLAUDE.md ni .gitignore" `
            (@(Get-ChildItem -LiteralPath $d -Force).Count -eq 0) (@(Get-ChildItem -LiteralPath $d -Force | ForEach-Object Name) -join ', ')
    }

    # -- E-09: un posicional de mas -----------------------------------------------------
    # Sin -Usuario a proposito: con -Usuario nombrado el posicional no tiene donde caer y falla
    # igual con o sin PositionalBinding=$false. El peligro es este: que caiga en -Usuario.
    $d = New-HuDir 'e09'
    $r = Invoke-HuInstalador $huInstalador @('-Project', $d, 'analisis')
    Assert-Verdadero 'E-09 un posicional de mas sale con codigo distinto de 0' ($r.Codigo -ne 0) "codigo $($r.Codigo)"
    Assert-Verdadero 'E-09 y no escribe nada en el proyecto' (@(Get-ChildItem -LiteralPath $d -Force).Count -eq 0) `
        (@(Get-ChildItem -LiteralPath $d -Force | ForEach-Object Name) -join ', ')

    # -- E-07: -WhatIf ------------------------------------------------------------------
    $d = New-HuDir 'e07'
    $r = Invoke-HuInstalador $huInstalador @('-Project', $d, '-WhatIf') -Registrar
    Assert-Igual     'E-07 -WhatIf sale con 0' 0 $r.Codigo
    Assert-Verdadero 'E-07 -WhatIf no crea nada' (@(Get-ChildItem -LiteralPath $d -Force).Count -eq 0)
    Assert-Contiene  'E-07 -WhatIf lista harness.presupuesto.json' 'harness.presupuesto.json' $r.Salida
    Assert-Verdadero 'E-07 -WhatIf no nombra manifiestos' (-not $r.Salida.Contains('manifiestos')) $r.Salida

    # -- La linea de base: el instalador de e5d7a14 -------------------------------------
    $huBaseOk = $false
    $huMotivo = ''
    $g = Invoke-HuProceso -Archivo 'git' -Argumentos ('-C "' + $script:Raiz + '" cat-file -e ' + $huBase + '^{commit}')
    if ($g.Codigo -ne 0) {
        $huMotivo = "no esta el commit $huBase en este clon (un clon superficial?): no hay contra que comparar"
    } else {
        $zip = Join-Path $huTmp 'base.zip'
        $g = Invoke-HuProceso -Archivo 'git' -Argumentos ('-C "' + $script:Raiz + '" archive --format=zip -o "' + $zip + '" ' + $huBase +
                                                         ' install.ps1 VERSION comun harnesses normativa/extractos tests/payloads tests/medir_barra.py')
        if ($g.Codigo -ne 0) {
            $huMotivo = "git archive $huBase fallo: $($g.Errores)"
        } else {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $huViejoRepo = Join-Path $huTmp 'repo-0.28.0'
            [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $huViejoRepo)
            $huViejo = Join-Path $huViejoRepo 'install.ps1'
            $huBaseOk = $true
        }
    }
    if (-not $huBaseOk) {
        foreach ($e in $huDeLaBase) { Assert-Verdadero "$e la linea de base $huBase esta disponible" $false $huMotivo }
    }

    if ($huBaseOk) {
        $huA  = New-HuDir 'viejo-desarrollo'
        $huAN = New-HuDir 'viejo-analisis-solo'
        $huAD = New-HuDir 'viejo-analisis-y-desarrollo'
        $r = Invoke-HuInstalador $huViejo @('-Project', $huA,  '-Harness', 'desarrollo', '-Usuario', $huUsuario)
        Assert-Igual 'base: 0.28.0 instala desarrollo' 0 $r.Codigo
        $r = Invoke-HuInstalador $huViejo @('-Project', $huAN, '-Harness', 'analisis', '-Usuario', $huUsuario)
        Assert-Igual 'base: 0.28.0 instala analisis' 0 $r.Codigo
        $r = Invoke-HuInstalador $huViejo @('-Project', $huAD, '-Harness', 'analisis,desarrollo', '-Usuario', $huUsuario)
        Assert-Igual 'base: 0.28.0 instala analisis y desarrollo' 0 $r.Codigo

        # Lo que dejo 0.28.0 con desarrollo, antes de que ningun escenario lo toque.
        $huARutas = Get-HuRutas $huA
        $huAHash = @{}
        foreach ($ruta in $huARutas) { $huAHash[$ruta] = Get-HuHash (Join-Path $huA $ruta) }
        $huASettings   = Get-HuNormalizado (Join-Path $huA '.claude\settings.json')
        $huAConfig     = Get-HuNormalizado (Join-Path $huA '.claude\harness.config.json')
        $huABloque     = Get-HuBloque $huA
        $huAEnv        = Get-HuNormalizado (Join-Path $huA '.env')
        $huAEnvEj      = Get-HuNormalizado (Join-Path $huA '.env.example')
        $huAPolitica   = Get-HuNormalizado (Join-Path $huA '.claude\harness.presupuesto.json')
        $huAComp       = Get-HuComponentes $huA
        $huARegistro   = Invoke-HuSonda $huA 'registro'
        $huAControles  = Invoke-HuSonda $huA 'controles'
    }

    # -- Una instalacion nueva ----------------------------------------------------------
    $huB = New-HuDir 'nuevo'
    $rB = Invoke-HuInstalador $huInstalador @('-Project', $huB, '-Usuario', $huUsuario) -Registrar
    Assert-Igual 'E-06 instala con -Project y -Usuario, y sale con 0' 0 $rB.Codigo
    foreach ($rel in @('.claude\harness.lock.json', '.claude\settings.json', '.claude\harness.installation.json')) {
        Assert-Verdadero "E-06 deja $rel" (Test-Path -LiteralPath (Join-Path $huB $rel))
    }
    $huBInstalado = Test-Path -LiteralPath (Join-Path $huB '.claude\harness.lock.json')

    if ($huBInstalado) {
        # E-14
        Assert-Verdadero 'E-14 no hay .claude\harness\manifiestos\' (-not (Test-Path -LiteralPath (Join-Path $huB '.claude\harness\manifiestos')))
        Assert-Igual 'E-14 el lock tiene exactamente version, instalado, backup y archivos' `
            'archivos,backup,instalado,version' (Get-HuClaves $huB)
        $huBRutas = Get-HuRutas $huB

        # E-21 y E-22
        Assert-Contiene 'E-21 verifica los cuatro hooks' 'los cuatro hooks responden correctamente' $rB.Salida
        Assert-Contiene 'E-21 y prueba la Context Bar' 'Context Bar: el comando registrado corre y dibuja' $rB.Salida
        Assert-Contiene 'E-22 corre el resumen de integraciones' 'Integraciones (desde el .env local)' $rB.Salida
        Assert-Contiene 'E-22 y la revision de fuentes' 'Conocimiento:' $rB.Salida
        Assert-Igual 'E-22 con disparador INSTALL' 'INSTALL' ([string](Get-HuEstado $huB).knowledgeRefresh.trigger)

        if ($huBaseOk) {
            # E-15
            $esperadas = @($huARutas | Where-Object { $huManifiestosViejos -notcontains $_ })
            Assert-Igual 'E-15 las rutas del lock son las de 0.28.0 sin los dos manifiestos' ($esperadas -join '|') ($huBRutas -join '|')
            # Eran 259 sobre 0.28.0 sola; sobre ea2dff7 suman los archivos de Flow Governance
            # (integracion-flow-governance-0-31).
            Assert-Igual 'E-15 son 282' 282 $huBRutas.Count

            # E-16
            $tocados = @('.claude\settings.json', '.claude\harness\run-hook.cmd', '.claude\harness\hooks\session-start.py',
                         '.claude\harness\hooks\lib\bienvenida.py', '.claude\harness\bin\desarrollo\dev-harness.py')
            # Un cambio posterior, docs/cambios/canonical-domain-model, modifica a proposito estos
            # archivos instalados (su tabla "Que se construye"). No son excepciones de harness-unico:
            # se saltean para que E-16 siga cuidando lo suyo, que NADA MAS se aparto de 0.28.0.
            # dev-harness.py tambien lo toca, y ya esta entre las cinco de arriba.
            $huTocadosPorModeloDeDominio = @(
                '.claude\agents\dev-orchestrator.md',
                '.claude\harness\bin\desarrollo\contabilidad\libro.py',
                '.claude\harness\bin\desarrollo\contexto\tarea.py',
                '.claude\harness\bin\desarrollo\integraciones\registro.py',
                '.claude\harness\bin\desarrollo\orquestacion\controles.py',
                '.claude\harness\bin\desarrollo\orquestacion\plan.py',
                '.claude\harness\bin\desarrollo\orquestacion\refutacion.py',
                '.claude\harness\reglas\desarrollo\control-registry.json',
                '.claude\harness\schemas\execution-accounting-event.schema.json',
                '.claude\harness\schemas\normative-signal.schema.json',
                '.claude\harness\schemas\orchestration-plan.schema.json',
                # Y docs/cambios/integracion-flow-governance-0-31: el ruteo de agentes se lee de
                # los blockers de ruteo (D4).
                '.claude\harness\bin\desarrollo\flujo\estado.py')
            $distintos = @()
            foreach ($ruta in $huBRutas) {
                if ($tocados -contains $ruta) { continue }
                if ($huTocadosPorModeloDeDominio -contains $ruta) { continue }
                if (-not $huAHash.ContainsKey($ruta)) { $distintos += "$ruta (no estaba)"; continue }
                if ((Get-HuHash (Join-Path $huB $ruta)) -ne $huAHash[$ruta]) { $distintos += $ruta }
            }
            Assert-Vacio 'E-16 cada archivo tiene el contenido de 0.28.0, salvo las cinco excepciones' ($distintos -join ', ')

            # E-18, E-19, E-20, E-23
            Assert-Igual 'E-18 harness.config.json igual al de 0.28.0' $huAConfig (Get-HuNormalizado (Join-Path $huB '.claude\harness.config.json'))
            Assert-Igual 'E-19 .env.example igual al de 0.28.0' $huAEnvEj (Get-HuNormalizado (Join-Path $huB '.env.example'))
            Assert-Igual 'E-19 .env igual al de 0.28.0' $huAEnv (Get-HuNormalizado (Join-Path $huB '.env'))
            Assert-Igual 'E-19 harness.presupuesto.json igual al de 0.28.0' $huAPolitica (Get-HuNormalizado (Join-Path $huB '.claude\harness.presupuesto.json'))
            Assert-Igual 'E-20 el bloque HARNESS:COMUN es el de 0.28.0' $huABloque (Get-HuBloque $huB)
            Assert-Igual 'E-23 los componentes de runtime quedan como en 0.28.0' $huAComp (Get-HuComponentes $huB)

            # E-53 y E-55
            Assert-Igual 'E-53 el registro de agentes instalado da lo mismo que en 0.28.0' $huARegistro (Invoke-HuSonda $huB 'registro')
            $reg = (Invoke-HuSonda $huB 'registro') | ConvertFrom-Json
            # Eran tres sobre 0.28.0 sola: Flow Governance registro dev-iniciador-code
            # (integracion-flow-governance-0-31).
            Assert-Igual 'E-53 los mismos dos huerfanos' 'flush-memoria:ERROR,leer-docs:ERROR' (@($reg.orphans) -join ',')
            Assert-Igual 'E-53 y la misma no declarada' 'instalar-desde-github' (@($reg.undeclared) -join ',')
            Assert-Igual 'E-55 el registro de controles instalado da lo mismo que en 0.28.0' $huAControles (Invoke-HuSonda $huB 'controles')
        }
        $huBloqueNuevo = Get-HuBloque $huB

        # E-54
        $ros = (Invoke-HuSonda $huB 'roster') | ConvertFrom-Json
        foreach ($n in @('dev-accesibilidad-html', 'dev-api-rutas', 'dev-codebase-forma', 'dev-dependencias', 'dev-infra-en-codigo')) {
            Assert-Igual "E-54 roster encuentra el check $n" 'True' ([string]$ros.checks.$n)
        }
        Assert-Igual 'E-54 y el roster no esta vacio' 'True' ([string]$ros.roster)

        # E-25: secretos, por los comandos registrados
        $tokenHu = 'glp' + 'at-' + 'Q7w8E9r0T1y2U3i4O5p6A7s8'
        $cmdPre = Get-HuComandoDeHook $huB 'PreToolUse'
        $payloadSecreto = ConvertTo-Json -Compress -Depth 5 -InputObject ([ordered]@{
            session_id = 'hu-e25'; cwd = $huB; hook_event_name = 'PreToolUse'; tool_name = 'Write'
            tool_input = [ordered]@{ file_path = (Join-Path $huB 'config.txt'); content = "token = $tokenHu" } })
        $x = Invoke-HuComando -Comando $cmdPre -Proyecto $huB -Json $payloadSecreto
        Assert-Igual     'E-25 PreToolUse con un secreto sale con 0' 0 $x.Codigo
        Assert-Verdadero 'E-25 PreToolUse con un secreto responde deny' (Test-HuDeny $x.Salida) $x.Salida
        $x = Invoke-HuComando -Comando $cmdPre -Proyecto $huB -Json (Get-Payload 'pre-tool-use-write.json')
        Assert-Verdadero 'E-25 PreToolUse con pre-tool-use-write.json no bloquea' (-not (Test-HuDeny $x.Salida)) $x.Salida
        $payloads = @(Get-ChildItem (Join-Path $script:Raiz 'tests\payloads') -Filter '*.json')
        foreach ($ev in @('SessionStart', 'UserPromptSubmit', 'PostToolUse')) {
            $cmd = Get-HuComandoDeHook $huB $ev
            foreach ($pl in $payloads) {
                # El cwd se apunta al proyecto de prueba: el de los payloads puede existir en la maquina.
                $j = [System.IO.File]::ReadAllText($pl.FullName, $huUtf8) | ConvertFrom-Json
                $j.cwd = $huB
                $x = Invoke-HuComando -Comando $cmd -Proyecto $huB -Json (ConvertTo-Json -Compress -Depth 10 -InputObject $j)
                Assert-Verdadero "E-25 $ev con $($pl.Name) no responde deny" (-not (Test-HuDeny $x.Salida)) $x.Salida
            }
        }

        # E-26: los checks, por el comando registrado de PostToolUse
        $cmdPost = Get-HuComandoDeHook $huB 'PostToolUse'
        $html = Join-Path $huB 'web\index.html'
        New-Item -ItemType Directory -Path (Split-Path -Parent $html) -Force | Out-Null
        [System.IO.File]::WriteAllText($html, "<html><head><title>x</title></head><body></body></html>`n", $huUtf8)
        $pl = ConvertTo-Json -Compress -Depth 5 -InputObject ([ordered]@{
            session_id = 'hu-e26'; cwd = $huB; hook_event_name = 'PostToolUse'; tool_name = 'Write'
            tool_input = [ordered]@{ file_path = $html; content = 'x' }; tool_response = [ordered]@{ success = $true } })
        $x = Invoke-HuComando -Comando $cmdPost -Proyecto $huB -Json $pl
        Assert-Contiene 'E-26 un .html sin lang dispara dev-accesibilidad-html' 'sin atributo lang' $x.Salida
        $rutaClaude = Join-Path $huB 'CLAUDE.md'
        $claudeAntes = [System.IO.File]::ReadAllBytes($rutaClaude)
        try {
            $relleno = (1..70 | ForEach-Object { "- regla $_" }) -join "`r`n"
            $t = [System.IO.File]::ReadAllText($rutaClaude, $huUtf8)
            $i = $t.IndexOf('<!-- /ZONA FIJA -->')
            Assert-Verdadero 'E-26 el CLAUDE.md instalado tiene ZONA FIJA' ($i -ge 0)
            if ($i -ge 0) {
                [System.IO.File]::WriteAllText($rutaClaude, $t.Substring(0, $i) + $relleno + "`r`n" + $t.Substring($i), $huUtf8)
                $pl = ConvertTo-Json -Compress -Depth 5 -InputObject ([ordered]@{
                    session_id = 'hu-e26'; cwd = $huB; hook_event_name = 'PostToolUse'; tool_name = 'Write'
                    tool_input = [ordered]@{ file_path = $rutaClaude; content = 'x' }; tool_response = [ordered]@{ success = $true } })
                $x = Invoke-HuComando -Comando $cmdPost -Proyecto $huB -Json $pl
                Assert-Contiene 'E-26 una zona pasada de techo dispara claude-md-zonas' 'ZONA FIJA tiene' $x.Salida
            }
        } finally {
            [System.IO.File]::WriteAllBytes($rutaClaude, $claudeAntes)
        }

        # E-49 y E-50 sobre la instalacion nueva
        $arbolAntes = Get-HuArbol $huB
        $r = Invoke-HuInstalador $huInstalador @('-Doctor', '-Project', $huB) -Registrar
        Assert-Contiene 'E-49 -Doctor dice harness instalado y la version, sin ids' "harness instalado (v$huVersion)" $r.Salida
        Assert-Contiene 'E-49 -Doctor da la linea de la Context Bar' 'Context Bar:' $r.Salida
        Assert-Vacio 'E-50 -Doctor -Project no cambia un byte del proyecto' (Compare-HuArbol $arbolAntes (Get-HuArbol $huB))
    }

    # -- E-10 y E-51: sobre una copia del repositorio -----------------------------------
    $huC = New-HuDir 'repo-copia'
    foreach ($rel in @('install.ps1', 'VERSION', 'manifest.json', 'tests\medir_barra.py')) {
        $o = Join-Path $script:Raiz $rel
        if (Test-Path -LiteralPath $o) {
            $dst = Join-Path $huC $rel
            New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
            Copy-Item -LiteralPath $o -Destination $dst -Force
        }
    }
    foreach ($rel in @('comun', 'harnesses', 'normativa\extractos', 'tests\payloads')) {
        $dst = Join-Path $huC $rel
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $script:Raiz $rel) -Destination $dst -Recurse -Force
    }
    $rutaManC = Join-Path $huC 'manifest.json'
    if (-not (Test-Path -LiteralPath $rutaManC)) {
        Assert-Verdadero 'E-51 hay manifest.json en la raiz para editar' $false
        Assert-Verdadero 'E-10 hay un instalador de un solo producto para probar' $false
    } else {
        $datos = Join-Path $huC 'harnesses\datos'
        New-Item -ItemType Directory -Path (Join-Path $datos 'skills\dat-x'), (Join-Path $datos 'agents') -Force | Out-Null
        [System.IO.File]::WriteAllText((Join-Path $datos 'manifest.json'),
            '{"id":"datos","descripcion":"datos","prefijo":"dat","requiereClaudeCode":"2.1.0"}', $huUtf8)
        [System.IO.File]::WriteAllText((Join-Path $datos 'skills\dat-x\SKILL.md'), "---`nname: dat-x`ndescription: x`n---`nx`n", $huUtf8)
        [System.IO.File]::WriteAllText((Join-Path $datos 'agents\dat-y.md'), "---`nname: dat-y`ndescription: y`ntools: Read`n---`ny`n", $huUtf8)
        $man = Read-HuJson $rutaManC
        $man.config.ramaDesarrollo = 'rama-hu-e51'
        $man.config.umbralCobertura = 91
        [System.IO.File]::WriteAllText($rutaManC, (ConvertTo-Json -InputObject $man -Depth 20), $huUtf8)

        $huP = New-HuDir 'proyecto-de-la-copia'
        $r = Invoke-HuInstalador (Join-Path $huC 'install.ps1') @('-Project', $huP, '-Usuario', $huUsuario) -Registrar
        Assert-Igual 'E-10 la copia con harnesses\datos instala' 0 $r.Codigo
        if ($huBInstalado -and (Test-Path -LiteralPath (Join-Path $huP '.claude\harness.lock.json'))) {
            Assert-Igual 'E-10 harnesses\datos no cambia lo que se instala' ($huBRutas -join '|') ((Get-HuRutas $huP) -join '|')
            $cfg = Read-HuJson (Join-Path $huP '.claude\harness.config.json')
            Assert-Igual 'E-51 ramaDesarrollo sale del manifiesto' 'rama-hu-e51' ([string]$cfg.ramaDesarrollo)
            Assert-Igual 'E-51 umbralCobertura sale del manifiesto' '91' ([string]$cfg.umbralCobertura)
        }
        $man.requiereClaudeCode = '99.0.0'
        [System.IO.File]::WriteAllText($rutaManC, (ConvertTo-Json -InputObject $man -Depth 20), $huUtf8)
        $r = Invoke-HuInstalador (Join-Path $huC 'install.ps1') @('-Doctor') -Registrar
        Assert-Verdadero 'E-10 -Doctor no nombra datos' (-not $r.Salida.Contains('datos')) $r.Salida
        if (Get-Command claude -ErrorAction SilentlyContinue) {
            Assert-Verdadero 'E-51 -Doctor falla con requiereClaudeCode 99.0.0' ($r.Codigo -ne 0) "codigo $($r.Codigo)"
            Assert-Contiene  'E-51 por la version de Claude Code' 'es anterior al m' $r.Salida
            Assert-Contiene  'E-51 contra el minimo del manifiesto' '99.0.0' $r.Salida
        } else {
            Assert-Verdadero 'E-51 hay claude en el PATH para probar el minimo' $false 'sin Claude Code no se puede ver la falla por su version'
        }
    }

    # -- E-45, la segunda instalacion de E-19 y E-46, sobre la instalacion nueva --------
    if ($huBInstalado) {
        $rutaLockB = Join-Path $huB '.claude\harness.lock.json'
        $lockB = Get-HuLock $huB
        $lockB | Add-Member -NotePropertyName 'harness' -NotePropertyValue @('comun', 'datos') -Force
        [System.IO.File]::WriteAllText($rutaLockB, (ConvertTo-Json -InputObject $lockB -Depth 20), $huUtf8)
        $r = Invoke-HuInstalador $huInstalador @('-Project', $huB, '-Update') -Registrar
        Assert-Igual 'E-45 -Update con un id desconocido en el lock sale con 0' 0 $r.Codigo
        Assert-Verdadero 'E-45 e instala el producto: el lock nuevo no tiene harness' `
            (-not ((Get-HuClaves $huB) -split ',' -contains 'harness'))

        $rutaEnvB = Join-Path $huB '.env'
        $rutaPolB = Join-Path $huB '.claude\harness.presupuesto.json'
        [System.IO.File]::WriteAllText($rutaEnvB, "HARNESS_JIRA_ENABLED=false`nPROPIO=1`n", $huUtf8)
        [System.IO.File]::WriteAllText($rutaPolB, '{"policyId":"propia"}', $huUtf8)
        $hEnv = (Get-FileHash -LiteralPath $rutaEnvB -Algorithm SHA256).Hash
        $hPol = (Get-FileHash -LiteralPath $rutaPolB -Algorithm SHA256).Hash
        $r = Invoke-HuInstalador $huInstalador @('-Project', $huB, '-Usuario', $huUsuario) -Registrar
        Assert-Igual 'E-19 la segunda instalacion sale con 0' 0 $r.Codigo
        Assert-Igual 'E-19 la segunda instalacion no cambia .env' $hEnv (Get-FileHash -LiteralPath $rutaEnvB -Algorithm SHA256).Hash
        Assert-Igual 'E-19 ni la politica que ya existia' $hPol (Get-FileHash -LiteralPath $rutaPolB -Algorithm SHA256).Hash

        $rutasAntes = Get-HuRutas $huB
        $r = Invoke-HuInstalador $huInstalador @('-Project', $huB, '-Uninstall') -Registrar
        Assert-Igual 'E-46 -Uninstall sale con 0' 0 $r.Codigo
        Assert-Vacio 'E-46 no queda nada de lo que lista el lock' ((@($rutasAntes | Where-Object { Test-Path -LiteralPath (Join-Path $huB $_) })) -join ', ')
        Assert-Verdadero 'E-46 ni harness.installation.json' (-not (Test-Path -LiteralPath (Join-Path $huB '.claude\harness.installation.json')))
        Assert-Verdadero 'E-46 ni .nuevo' (@(Get-ChildItem -LiteralPath $huB -Recurse -Force -Filter '*.nuevo' -ErrorAction SilentlyContinue).Count -eq 0)
        Assert-Verdadero 'E-46 ni __pycache__' (@(Get-ChildItem -LiteralPath (Join-Path $huB '.claude') -Recurse -Force -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue).Count -eq 0)
        foreach ($rel in @('.claude\.harness-backup', '.claude\harness.config.json', '.env', '.env.example', '.claude\harness.presupuesto.json')) {
            Assert-Verdadero "E-46 conserva $rel" (Test-Path -LiteralPath (Join-Path $huB $rel))
        }
        Assert-Verdadero 'E-46 saca el bloque del CLAUDE.md' (-not ([System.IO.File]::ReadAllText((Join-Path $huB 'CLAUDE.md'))).Contains('HARNESS:COMUN'))
        Assert-Verdadero 'E-46 y el del .gitignore' (-not ([System.IO.File]::ReadAllText((Join-Path $huB '.gitignore'))).Contains('gcba-harness'))
    }

    if ($huBaseOk) {
        # -- E-36 a E-40 y E-17: -Update sobre 0.28.0 con desarrollo, en su lugar ----------
        $huSkill = Join-Path $huA '.claude\skills\dev-api\SKILL.md'
        [System.IO.File]::AppendAllText($huSkill, "`n<!-- editado a mano para E-38 -->`n", $huUtf8)
        $refAntes = Invoke-HuSonda $huA 'refutacion'

        # E-39: la barra se dibuja y el registro salda el reinicio, como en 54-context-bar-instalador.ps1.
        $sA = Read-HuJson (Join-Path $huA '.claude\settings.json')
        $cmdBarra = [string]$sA.statusLine.command
        $sesionHu = 's-hu39-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8)
        $fuenteHu = Join-Path $huTmp 'sesion-e39.jsonl'
        [System.IO.File]::WriteAllText($fuenteHu, ('{"type":"assistant","sessionId":"' + $sesionHu + '","timestamp":"2026-10-01T10:00:00",' +
            '"message":{"id":"msg_1","model":"m-hu39","usage":{"input_tokens":10,"output_tokens":100,' +
            '"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}}' + "`n"), $huUtf8)
        $jsonHu = '{"session_id":"' + $sesionHu + '","transcript_path":"' + ($fuenteHu -replace '\\', '/') + '"}'
        Start-Sleep -Milliseconds 1100
        $ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        $x = Invoke-HuProceso -Archivo $ps -Argumentos ('-NoProfile -Command "' + $cmdBarra + '"') -Directorio ([System.IO.Path]::GetTempPath()) -Entrada $jsonHu
        $x = Invoke-HuProceso -Archivo 'python' -Argumentos ('"' + (Join-Path $huA '.claude\harness\hooks\lib\bienvenida.py') + '" registrar "' + $huA + '" --barra-probada')
        $eAntes = Get-HuEstado $huA
        Assert-Igual 'E-39 antes del -Update la barra no pide reinicio' 'False' ([string]$eAntes.runtimeComponents.contextBar.reloadRequired)
        $huellasAntes = $eAntes.runtimeComponents.contextBar.fingerprints

        $propios = @('CLAUDE.md', '.gitignore', '.env', '.env.example', '.claude\harness.config.json', '.claude\harness.presupuesto.json')
        $hAntes = @{}
        foreach ($rel in $propios) { $hAntes[$rel] = (Get-FileHash -LiteralPath (Join-Path $huA $rel) -Algorithm SHA256).Hash }

        $rU = Invoke-HuInstalador $huInstalador @('-Project', $huA, '-Update') -Registrar
        Assert-Igual 'E-36 -Update sobre 0.28.0 con desarrollo sale con 0' 0 $rU.Codigo
        if ($huBInstalado) {
            Assert-Igual 'E-36 deja el inventario de E-15' ($huBRutas -join '|') ((Get-HuRutas $huA) -join '|')
        }
        Assert-Igual 'E-36 y el lock de E-14' 'archivos,backup,instalado,version' (Get-HuClaves $huA)
        foreach ($rel in $propios) {
            Assert-Igual "E-37 no cambia un byte de $rel" $hAntes[$rel] (Get-FileHash -LiteralPath (Join-Path $huA $rel) -Algorithm SHA256).Hash
        }
        Assert-Verdadero 'E-37 y no nombra ningun archivo sacado' (-not $rU.Salida.Contains('ya no son parte del harness')) $rU.Salida
        Assert-Contiene  'E-38 la skill editada conserva su contenido' 'editado a mano para E-38' ([System.IO.File]::ReadAllText($huSkill))
        Assert-Verdadero 'E-38 y la version nueva queda como .nuevo' (Test-Path -LiteralPath ($huSkill + '.nuevo'))
        $eDespues = Get-HuEstado $huA
        Assert-Igual    'E-39 la Context Bar queda RELOAD_REQUIRED' 'RELOAD_REQUIRED' ([string]$eDespues.runtimeComponents.contextBar.state)
        Assert-Contiene 'E-39 y lo dice' 'Context Bar configurada. Reinici' $rU.Salida
        Assert-Verdadero 'E-39 cambio la huella de session-start.py' `
            ([string]$eDespues.runtimeComponents.contextBar.fingerprints.sessionStart -ne [string]$huellasAntes.sessionStart)
        Assert-Igual 'E-39 y no la del statusLine' ([string]$huellasAntes.statusLine) ([string]$eDespues.runtimeComponents.contextBar.fingerprints.statusLine)
        $refDespues = Invoke-HuSonda $huA 'refutacion'
        Assert-Verdadero 'E-40 hay huella del contrato del refutador' ($refAntes -match '"fingerprint": "') $refAntes
        Assert-Igual 'E-40 la huella del refutador no cambia' $refAntes $refDespues
        Assert-Contiene 'E-22 el -Update corre la revision de fuentes' 'Conocimiento:' $rU.Salida
        Assert-Igual 'E-22 con disparador HARNESS_UPDATE' 'HARNESS_UPDATE' ([string]$eDespues.knowledgeRefresh.trigger)

        # E-17: en el mismo directorio, desinstalar y volver a instalar con el instalador nuevo.
        $r = Invoke-HuInstalador $huInstalador @('-Project', $huA, '-Uninstall') -Registrar
        $r = Invoke-HuInstalador $huInstalador @('-Project', $huA, '-Usuario', $huUsuario) -Registrar
        Assert-Igual 'E-17 la instalacion nueva en el mismo directorio sale con 0' 0 $r.Codigo
        $verViejo = [regex]::Replace($huASettings, 'gcba-harness v[0-9][0-9.]*', 'gcba-harness vX')
        $verNuevo = [regex]::Replace((Get-HuNormalizado (Join-Path $huA '.claude\settings.json')), 'gcba-harness v[0-9][0-9.]*', 'gcba-harness vX')
        Assert-Igual 'E-17 settings.json igual al de 0.28.0' $verViejo $verNuevo
        Assert-Contiene 'E-17 con el statusLine de bin\desarrollo' '/.claude/harness/bin/desarrollo/contabilidad/statusline.py' $verNuevo

        # -- E-41, E-42 y E-47: 0.28.0 con analisis y desarrollo ---------------------------
        $ad1 = Copy-HuProyecto $huAD 'ad-e41'
        $r = Invoke-HuInstalador $huInstalador @('-Project', $ad1, '-Update') -Registrar
        Assert-Igual 'E-41 -Update sobre 0.28.0 con analisis y desarrollo sale con 0' 0 $r.Codigo
        $rutas = Get-HuRutas $ad1
        foreach ($rel in $huHu) {
            Assert-Verdadero "E-41 $rel ya no esta en disco" (-not (Test-Path -LiteralPath (Join-Path $ad1 $rel)))
            Assert-Verdadero "E-41 $rel ya no esta en el lock" (-not ($rutas -contains $rel))
            Assert-Contiene  "E-41 la salida nombra $rel" $rel $r.Salida
        }
        Assert-Verdadero 'E-41 ni el directorio de hu-escribir' (-not (Test-Path -LiteralPath (Join-Path $ad1 '.claude\skills\hu-escribir')))
        if ($huBInstalado) { Assert-Igual 'E-41 el bloque del CLAUDE.md es el de E-20' $huBloqueNuevo (Get-HuBloque $ad1) }
        $backup = Join-Path $ad1 ([string](Get-HuLock $ad1).backup)
        Assert-Verdadero 'E-41 el CLAUDE.md anterior esta en el backup de esa corrida' `
            ((Test-Path -LiteralPath (Join-Path $backup 'CLAUDE.md')) -and ([System.IO.File]::ReadAllText((Join-Path $backup 'CLAUDE.md'))).Contains('La maqueta manda'))

        $ad2 = Copy-HuProyecto $huAD 'ad-e42'
        $redactor = Join-Path $ad2 '.claude\agents\hu-redactor.md'
        [System.IO.File]::AppendAllText($redactor, "`n<!-- editado a mano para E-42 -->`n", $huUtf8)
        $r = Invoke-HuInstalador $huInstalador @('-Project', $ad2, '-Update') -Registrar
        Assert-Igual     'E-42 -Update con hu-redactor.md editado sale con 0' 0 $r.Codigo
        Assert-Verdadero 'E-42 hu-redactor.md queda en disco con su contenido' `
            ((Test-Path -LiteralPath $redactor) -and ([System.IO.File]::ReadAllText($redactor)).Contains('editado a mano para E-42'))
        Assert-Verdadero 'E-42 sin hu-redactor.md.nuevo' (-not (Test-Path -LiteralPath ($redactor + '.nuevo')))
        Assert-Verdadero 'E-42 fuera del lock' (-not ((Get-HuRutas $ad2) -contains '.claude\agents\hu-redactor.md'))
        Assert-Contiene  'E-42 la salida dice que ya no es parte del harness y que lo editaste' 'editaste a mano' $r.Salida
        Assert-Contiene  'E-42 y lo nombra' 'hu-redactor.md' $r.Salida
        foreach ($rel in @('.claude\skills\hu-escribir\SKILL.md', '.claude\agents\hu-refutador.md')) {
            Assert-Verdadero "E-42 $rel, sin editar, sale" (-not (Test-Path -LiteralPath (Join-Path $ad2 $rel)))
        }

        $ad3 = Copy-HuProyecto $huAD 'ad-e47'
        $rutasViejas = Get-HuRutas $ad3
        $r = Invoke-HuInstalador $huInstalador @('-Project', $ad3, '-Uninstall') -Registrar
        Assert-Igual 'E-47 -Uninstall sobre 0.28.0 con analisis y desarrollo sale con 0' 0 $r.Codigo
        $quedan = @($rutasViejas | Where-Object { $_ -match '^\.claude\\(harness|skills|agents)\\' -and (Test-Path -LiteralPath (Join-Path $ad3 $_)) })
        Assert-Vacio 'E-47 no queda ningun archivo que ese lock listara' ($quedan -join ', ')

        # -- E-43, E-44 y E-49: 0.28.0 con analisis solo -----------------------------------
        $an1 = Copy-HuProyecto $huAN 'an-e43'
        $rutaCfg = Join-Path $an1 '.claude\harness.config.json'
        $cfgAntes = [System.IO.File]::ReadAllBytes($rutaCfg)
        $r = Invoke-HuInstalador $huInstalador @('-Project', $an1, '-Update') -Registrar
        Assert-Igual 'E-43 -Update sobre 0.28.0 con analisis solo sale con 0' 0 $r.Codigo
        if ($huBInstalado) { Assert-Igual 'E-43 deja el inventario de E-15' ($huBRutas -join '|') ((Get-HuRutas $an1) -join '|') }
        foreach ($rel in @('.env', '.env.example', '.claude\harness.presupuesto.json')) {
            Assert-Verdadero "E-43 deja $rel" (Test-Path -LiteralPath (Join-Path $an1 $rel))
        }
        $sAn = Read-HuJson (Join-Path $an1 '.claude\settings.json')
        Assert-Verdadero 'E-43 registra el statusLine' ([bool]($sAn.PSObject.Properties['statusLine']))
        foreach ($rel in $huHu) { Assert-Verdadero "E-43 $rel sale" (-not (Test-Path -LiteralPath (Join-Path $an1 $rel))) }
        Assert-Igual 'E-43 harness.config.json queda byte a byte' ([System.BitConverter]::ToString($cfgAntes)) `
            ([System.BitConverter]::ToString([System.IO.File]::ReadAllBytes($rutaCfg)))
        $hLeg = Invoke-HuCli $an1 'harness'
        Assert-Igual 'E-43 dev-harness.py harness sale con 0' 0 $hLeg.Codigo
        $eLeg = Invoke-HuCli $an1 'estado'
        Assert-Igual 'E-43 dev-harness.py estado sale con 0' 0 $eLeg.Codigo

        # Los valores efectivos con el config legado, contra los defaults del manifiesto.
        $estadoLeg  = Normalize-HuFechas (Invoke-HuCli $an1 'estado --json').Salida
        $harnessLeg = Normalize-HuFechas (Invoke-HuCli $an1 'harness --json').Salida
        $timeoutLeg = Invoke-HuSonda $an1 'timeout'
        $manRepo = Join-Path $script:Raiz 'manifest.json'
        if (Test-Path -LiteralPath $manRepo) {
            $defaults = (Read-HuJson $manRepo).config
            $cfg = Read-HuJson $rutaCfg
            foreach ($p in $defaults.PSObject.Properties) {
                if (-not $cfg.PSObject.Properties[$p.Name]) { $cfg | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value }
            }
            try {
                [System.IO.File]::WriteAllText($rutaCfg, (ConvertTo-Json -InputObject $cfg -Depth 20), $huUtf8)
                $estadoCom  = Normalize-HuFechas (Invoke-HuCli $an1 'estado --json').Salida
                $harnessCom = Normalize-HuFechas (Invoke-HuCli $an1 'harness --json').Salida
            } finally {
                [System.IO.File]::WriteAllBytes($rutaCfg, $cfgAntes)
            }
            Assert-Igual 'E-43 estado --json con el config legado da lo mismo que con los defaults del manifiesto' $estadoCom $estadoLeg
            Assert-Igual 'E-43 harness --json con el config legado da lo mismo que con los defaults del manifiesto' $harnessCom $harnessLeg
            Assert-Igual 'E-43 timeout_de con el config legado es el timeoutIntegraciones del manifiesto' `
                ('{"timeout": ' + [string]$defaults.timeoutIntegraciones + '}') $timeoutLeg
        } else {
            Assert-Verdadero 'E-43 hay manifest.json para comparar los defaults' $false
        }

        $an2 = Copy-HuProyecto $huAN 'an-e44'
        $rutasViejas = Get-HuRutas $an2
        $r = Invoke-HuInstalador $huInstalador @('-Project', $an2, '-Usuario', $huUsuario) -Registrar
        Assert-Igual 'E-44 instalar sin -Update sobre 0.28.0 con analisis sale con 0' 0 $r.Codigo
        $rutasNuevas = Get-HuRutas $an2
        $sueltos = @($rutasViejas | Where-Object {
            ($rutasNuevas -notcontains $_) -and (Test-Path -LiteralPath (Join-Path $an2 $_)) -and (-not $r.Salida.Contains($_)) })
        Assert-Vacio 'E-44 ningun archivo del lock anterior queda fuera del nuevo sin nombrarse' ($sueltos -join ', ')
        foreach ($rel in $huHu) {
            Assert-Verdadero "E-44 $rel sale" (-not (Test-Path -LiteralPath (Join-Path $an2 $rel)))
            Assert-Contiene  "E-44 y se nombra $rel" $rel $r.Salida
        }

        $an3 = Copy-HuProyecto $huAN 'an-e49'
        $r = Invoke-HuInstalador $huInstalador @('-Doctor', '-Project', $an3) -Registrar
        Assert-Contiene 'E-49 -Doctor sobre 0.28.0 con analisis dice harness instalado y la version' 'harness instalado (v0.28.0)' $r.Salida
        Assert-Contiene 'E-49 y da la linea de la Context Bar' 'Context Bar:' $r.Salida
        $fallasLock = @(($r.Salida -split "`r?`n") | Where-Object { $_ -match '^\s*FALLA' -and $_ -match '(?i)harness|lock' })
        Assert-Vacio 'E-49 sin fallas por el contenido del lock' ($fallasLock -join ' / ')
    }

    # -- E-48: -Doctor sin proyecto -----------------------------------------------------
    $r = Invoke-HuInstalador $huInstalador @('-Doctor') -Registrar
    foreach ($a in @('PowerShell', 'Claude Code', 'Python', 'ExecutionPolicy', 'Mark-of-the-Web', 'latencia de hook', 'latencia de la Context Bar')) {
        Assert-Contiene "E-48 -Doctor verifica $a" $a $r.Salida
    }
    Assert-Verdadero 'E-48 y nada sobre harness disponibles' (-not $r.Salida.Contains('harness disponibles')) $r.Salida

    # -- E-11: nada de lo que dijo el instalador nuevo habla de varios harnesses --------
    $huTodo = ($huSalidas -join "`n")
    foreach ($prohibido in @('harness disponibles', 'se conserva lo ya instalado', 'prefijos', 'comun, desarrollo', 'analisis')) {
        Assert-Verdadero "E-11 ninguna salida del instalador dice: $prohibido" (-not $huTodo.Contains($prohibido)) `
            ((@(($huTodo -split "`r?`n") | Where-Object { $_.Contains($prohibido) }) | Select-Object -First 3) -join ' / ')
    }
    Assert-Verdadero 'E-11 se juntaron las salidas de los demas casos' ($huSalidas.Count -ge 10) "$($huSalidas.Count)"
}
finally {
    if (Test-Path -LiteralPath $huTmp) { Remove-Item -LiteralPath $huTmp -Recurse -Force -ErrorAction SilentlyContinue }
}
