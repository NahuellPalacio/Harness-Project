<#
.SYNOPSIS
    El medidor de la Task 6.1: corre un par serial contra paralelo y dice si el par se acepta.
    Es el test de VP-E25 (benchmark acceptance de la spec), fuera de la suite.

.DESCRIPTION
    Protocolo de la spec 5.4, sobre el arbol donde vive este script (la raiz es la carpeta de
    arriba de tests\, como en Invoke-Tests.ps1):

      1. condiciones (spec 5.2) y huella (spec 5.1);
      2. .\tests\Invoke-Tests.ps1 (sin parametros: sin -Detallado, D-T5), capturado, con su wall
         (Stopwatch);
      3. huella; condiciones; .\tests\Invoke-Tests-Parallel.ps1 -Workers <n> -TempBase <carpeta>
         (sin -Detallado, D-T5), capturado, con su wall; huella;
      4. Compare-TestRuns.ps1 sobre las dos salidas;
      5. el registro: condiciones de cada pata, las tres huellas, walls, el veredicto del
         comparador con sus lineas, la duracion de cada suite (las lineas de progreso del
         runner, spec 16.6: son las que pueden alimentar maxSeconds por la regla B1), los
         residuos, los procesos vivos al terminar y la RAM libre minima.

    Cada pata corre con TEMP, TMP y TMPDIR nuevos, vacios y propios, en carpetas hermanas del
    mismo formato; la del runner usa esa carpeta como -TempBase. Las dos heredan el entorno del
    medidor: no se toca el PATH, y se registra el bash efectivo de cada una.

    Sale 0 solo si: las tres huellas son iguales, el comparador dice EQUIVALENTE, la corrida
    paralela no dejo residuos atribuibles (ninguna raiz hpp-*, ningun s<nnn>, ningun
    hpp-<id>.lock en su TempBase, y ninguna linea de su salida que EMPIECE con AVISO
    LIMPIEZA_INCOMPLETA), y, si se
    paso -Umbral, el wall paralelo es menor o igual que el umbral por el wall serial. Un par
    cuyo bash efectivo difiere entre patas tampoco se acepta (regla B2). Sale 1 si el par no se
    acepta y 2 si no se pudo medir (argumento invalido, un fallo del propio medidor).

    No escribe en el repo ni toma el candado pesada.lock (lo toma el runner en su pata; la pata
    serial no lo toma nadie). El registro se imprime y se guarda, con las capturas (serial.txt,
    paralelo.txt, registro.txt), en una carpeta nueva bajo el TEMP del medidor, cuya ruta se
    imprime al empezar y al terminar. El muestreador de RAM vive en el proceso del medidor y
    no lo sobrevive.

    Mientras corre no hay que lanzar otro trabajo pesado (regla operativa de la spec 28).

    Ademas de lo anterior, el modo normal guarda en la carpeta de capturas lo que el reuso de la
    pata serial necesita (spec 9.6): pata-serial.json (HEAD, status, wall y exit serial, bash
    efectivo, condiciones de la pata serial, las tres huellas, la huella de serial.txt) y
    lista-final.txt (la lista ruta, tamano, sha256 de la huella final).

    MODO DE REUSO (Enmienda 1, D-T2; spec 5.4 y 9.6): con -ReusarSerialDe <carpeta hpm-...> el
    medidor NO corre la pata serial: reutiliza la captura de la carpeta de un par anterior (el
    primer par N = 2) y aplica las condiciones (1) a (4) de la spec 5.4 sobre el arbol de cierre.
    La unica ruta que puede haber cambiado entre las dos huellas finales es
    tests/parallel-manifest.json. Si alguna condicion falla, sale 2 (no se pudo medir), nunca 0.

.PARAMETER Workers
    Workers de la pata paralela, de 1 a 4. Por defecto 2 (el que cierra; 3 es informativo).

.PARAMETER Umbral
    Fraccion maxima de wall paralelo sobre wall serial (por ejemplo 0.70). Sin el, no se
    exige relacion.

.PARAMETER ReusarSerialDe
    Carpeta hpm-... de un par anterior del medidor (la del primer par N = 2). Activa el modo de
    reuso de la pata serial. Es la unica forma de reuso: no hay parametro para excluir otra ruta
    ni para tolerar una diferencia (la unica ruta excluida es tests/parallel-manifest.json).

.EXAMPLE
    .\tests\Measure-TestRuns.ps1 -Workers 2 -Umbral 0.70

.EXAMPLE
    .\tests\Measure-TestRuns.ps1 -Workers 2 -Umbral 0.70 -ReusarSerialDe C:\t\hpm-261022-090000
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [int] $Workers = 2,

    [double] $Umbral,

    [string] $ReusarSerialDe
)

$script:Utf8     = New-Object System.Text.UTF8Encoding $false
$script:Inv      = [System.Globalization.CultureInfo]::InvariantCulture
$script:Registro = New-Object System.Collections.Generic.List[string]
$script:Powershell = [System.IO.Path]::Combine($env:SystemRoot, 'System32\WindowsPowerShell\v1.0\powershell.exe')

# Cada n segundos de reloj, una muestra de RAM libre; cada 5 minutos, un latido por pantalla.
$script:CadaRamSeg     = 5
$script:CadaLatidoSeg  = 300
$script:ReProgreso     = '^\[(\d+)/(\d+)\] (OK|FALLA|INFRA) (.+?) \((\d+)\) ([0-9]+\.[0-9]) s\s*$'

# Modo de reuso (spec 5.4, 9.6): la unica ruta que puede diferir entre las dos huellas finales, las dos
# suites cuyo resultado depende de su contenido (spec 1.3) y los nombres de lo que guarda el modo normal.
$script:RutaExcluida   = 'tests/parallel-manifest.json'
$script:SuitesDelReuso = @('75_manifest_paralelo.py', '63_harness_unico.py')
$script:EsquemaSerial  = 'pata-serial/1'
$script:ArchivoSerial  = 'pata-serial.json'
$script:ArchivoLista   = 'lista-final.txt'
$script:ReGrupoOraculo = '^  (?:OK    |FALLA )(.+)  \(([0-9]+)(?:/([0-9]+))?\)$'


# -- Salida: lo que se imprime es lo que se guarda ------------------------------------

function Write-Registro {
    param([string] $Linea = '', [string] $Color = '')
    $script:Registro.Add($Linea)
    if ($Color) { Write-Host $Linea -ForegroundColor $Color } else { Write-Host $Linea }
}


function Format-Seg {
    param([double] $S)
    return $S.ToString('0.0', $script:Inv)
}


function Format-Hms {
    param([double] $S)
    $t = [TimeSpan]::FromSeconds($S)
    return ('{0}:{1:00}' -f [int][math]::Floor($t.TotalMinutes), $t.Seconds)
}


# -- Procesos cortos (git, bash, python, el comparador) --------------------------------

function Invoke-Corto {
    <# Un proceso de vida corta con stdout y stderr capturados. No lanza si no arranca: Ok = $false. #>
    param(
        [string] $Exe,
        [string] $Argumentos = '',
        [string] $Cwd = '',
        [int] $TopeMs = 120000,
        [hashtable] $Entorno = @{}
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = $Argumentos
    if ($Cwd) { $psi.WorkingDirectory = $Cwd }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = $script:Utf8
    $psi.StandardErrorEncoding = $script:Utf8
    foreach ($k in $Entorno.Keys) { $psi.EnvironmentVariables[[string]$k] = [string]$Entorno[$k] }
    $p = $null
    try { $p = [System.Diagnostics.Process]::Start($psi) }
    catch { return [pscustomobject]@{ Ok = $false; Exit = -1; Out = ''; Err = $_.Exception.Message } }
    try {
        $p.StandardInput.Close()
        $errT = $p.StandardError.ReadToEndAsync()
        $outT = $p.StandardOutput.ReadToEndAsync()
        if (-not $p.WaitForExit($TopeMs)) {
            try { $p.Kill() } catch { }
            return [pscustomobject]@{ Ok = $false; Exit = -1; Out = ''; Err = "no termino en $TopeMs ms: $Exe $Argumentos" }
        }
        [void]$outT.Wait(10000)
        [void]$errT.Wait(10000)
        return [pscustomobject]@{ Ok = $true; Exit = $p.ExitCode; Out = [string]$outT.Result; Err = [string]$errT.Result }
    }
    finally { $p.Dispose() }
}


function Get-PrimeraLinea {
    param([string] $Texto)
    foreach ($l in ($Texto -split "`r?`n")) { if ($l.Trim().Length -gt 0) { return $l.Trim() } }
    return ''
}


function Resolve-Exe {
    <# La resolucion del PATH que ve el medidor. CreateProcess busca System32 antes que el PATH, y ahi vive
       el stub de WSL de bash: por eso a los procesos de condiciones se les da la ruta resuelta, no el nombre. #>
    param([string] $Nombre)
    $c = Get-Command $Nombre -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return [string]$c.Source }
    return ''
}


function Invoke-Git {
    param([string] $Raiz, [string[]] $Argumentos)
    $git = Resolve-Exe 'git'
    if (-not $git) { throw 'git no esta en el PATH' }
    $r = Invoke-Corto -Exe $git -Argumentos ('-C "' + $Raiz + '" ' + ($Argumentos -join ' ')) -Cwd $Raiz
    if (-not $r.Ok -or $r.Exit -ne 0) { throw "git $($Argumentos -join ' ') fallo (exit $($r.Exit)): $($r.Err.Trim())" }
    return $r.Out
}


# -- La huella del arbol (spec 5.1) ----------------------------------------------------
#
# Es la cuenta de la spec, hecha aca y no reusando la del runner: el medidor no le pide la
# huella al codigo que mide.

function Get-HashHex {
    param([System.Security.Cryptography.HashAlgorithm] $Alg, [byte[]] $Bytes)
    return ([System.BitConverter]::ToString($Alg.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant()
}


function Get-HuellaDeLista {
    <# La cuenta de la huella sobre un HEAD, un status y una lista de filas "ruta<TAB>tamano<TAB>sha256". Con
       -Excluir, la misma cuenta sin la fila de esa ruta (la huella "sin la ruta" del modo de reuso, spec 5.4 (3)). #>
    param([string] $Head, [string] $Status, [string[]] $Filas, [string] $Excluir = '')
    $alg = [System.Security.Cryptography.SHA256]::Create()
    $usadas = @($Filas | Where-Object { -not ($Excluir -and $_.StartsWith($Excluir + "`t", [System.StringComparison]::Ordinal)) })
    $hStatus = Get-HashHex -Alg $alg -Bytes $script:Utf8.GetBytes($Status)
    $hFiles = Get-HashHex -Alg $alg -Bytes $script:Utf8.GetBytes(($usadas -join "`n"))
    return (Get-HashHex -Alg $alg -Bytes $script:Utf8.GetBytes($Head + $hStatus + $hFiles)).ToUpperInvariant()
}


function Get-Huella {
    param([string] $Raiz)
    try {
        $alg = [System.Security.Cryptography.SHA256]::Create()
        $head = (Invoke-Git -Raiz $Raiz -Argumentos @('rev-parse', 'HEAD')).Trim()
        $status = Invoke-Git -Raiz $Raiz -Argumentos @('status', '--porcelain', '--untracked-files=all')
        $lista = Invoke-Git -Raiz $Raiz -Argumentos @('ls-files', '-c', '-o', '--exclude-standard', '-z')
        [string[]]$rutas = @($lista.Split([char]0) | Where-Object { $_.Length -gt 0 })
        [System.Array]::Sort($rutas, [System.StringComparer]::Ordinal)
        $filas = New-Object System.Collections.Generic.List[string]
        foreach ($rel in $rutas) {
            $completa = $Raiz.TrimEnd('\', '/') + '\' + $rel.Replace('/', '\')
            if (-not [System.IO.File]::Exists($completa)) { continue }
            $bytes = [System.IO.File]::ReadAllBytes($completa)
            $filas.Add("$rel`t$($bytes.Length)`t$(Get-HashHex -Alg $alg -Bytes $bytes)")
        }
        $huella = Get-HuellaDeLista -Head $head -Status $status -Filas @($filas)
        $nStatus = @($status -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }).Count
        return [pscustomobject]@{ Ok = $true; Huella = $huella; Head = $head; StatusLineas = $nStatus; Archivos = $filas.Count; Causa = ''
                                  Status = $status; Filas = @($filas) }
    }
    catch {
        return [pscustomobject]@{ Ok = $false; Huella = $null; Head = ''; StatusLineas = 0; Archivos = 0; Causa = $_.Exception.Message
                                  Status = ''; Filas = @() }
    }
}


function Format-Huella {
    param($H)
    if ($H.Ok) { return ($H.Huella + '  (' + $H.Archivos + ' archivos no ignorados, ' + $H.StatusLineas + ' lineas de status)') }
    return 'NO_DISPONIBLE: ' + $H.Causa
}


# -- Condiciones (spec 5.2) ------------------------------------------------------------

function Get-RamLibreGB {
    $os = Get-CimInstance Win32_OperatingSystem
    return [math]::Round($os.FreePhysicalMemory / 1MB, 2)
}


function Get-Procesos {
    $todos = @(Get-CimInstance Win32_Process)
    return @($todos | ForEach-Object {
        [pscustomobject]@{
            Pid = [int]$_.ProcessId; Ppid = [int]$_.ParentProcessId; Name = [string]$_.Name
            Cmd = [string]$_.CommandLine; Creacion = $_.CreationDate
        }
    })
}


function Get-Parentesco {
    <# Del medidor: el y sus descendientes vivos. Lanzadores: la cadena de padres hacia arriba. #>
    param($Todos)
    $hijos = @{}
    $porPid = @{}
    foreach ($p in $Todos) {
        $porPid[$p.Pid] = $p
        if (-not $hijos.ContainsKey($p.Ppid)) { $hijos[$p.Ppid] = New-Object System.Collections.Generic.List[int] }
        $hijos[$p.Ppid].Add($p.Pid)
    }
    $propios = New-Object 'System.Collections.Generic.HashSet[int]'
    $cola = New-Object 'System.Collections.Generic.Queue[int]'
    [void]$propios.Add($PID)
    $cola.Enqueue($PID)
    while ($cola.Count -gt 0) {
        $x = $cola.Dequeue()
        if ($hijos.ContainsKey($x)) {
            foreach ($h in $hijos[$x]) { if ($propios.Add($h)) { $cola.Enqueue($h) } }
        }
    }
    $lanz = New-Object 'System.Collections.Generic.HashSet[int]'
    $x = $PID
    for ($i = 0; $i -lt 12; $i++) {
        if (-not $porPid.ContainsKey($x)) { break }
        $pp = $porPid[$x].Ppid
        if ($pp -le 0 -or -not $porPid.ContainsKey($pp)) { break }
        if (-not $lanz.Add($pp)) { break }
        $x = $pp
    }
    return [pscustomobject]@{ Propios = $propios; Lanzadores = $lanz }
}


function Get-ClaseDeProceso {
    param($P, $Par)
    if ($Par.Propios.Contains($P.Pid)) { return 'medidor' }
    if ($Par.Lanzadores.Contains($P.Pid)) { return 'lanzador' }
    return 'otro'
}


function Get-ClaveDeProceso {
    param($P)
    $t = 0
    if ($null -ne $P.Creacion) { $t = ([datetime]$P.Creacion).Ticks }
    return ('' + $P.Pid + '|' + $t)
}


function Format-Cmd {
    param([string] $Cmd)
    if ([string]::IsNullOrEmpty($Cmd)) { return '(linea de comandos ilegible o vacia)' }
    if ($Cmd.Length -gt 220) { return $Cmd.Substring(0, 220) + '...' }
    return $Cmd
}


function Get-Condiciones {
    <#
    .SYNOPSIS
        Las condiciones de la spec 5.2 antes de una pata. Devuelve las lineas y lo que el medidor
        usa despues (bash efectivo, foto de procesos).
    #>
    param([string] $Etiqueta, [string] $Raiz, [string] $TempDeLaPata, [int] $Workers, $Huella)

    $L = New-Object System.Collections.Generic.List[string]
    $entorno = @{ TEMP = $TempDeLaPata; TMP = $TempDeLaPata; TMPDIR = $TempDeLaPata }
    $L.Add('[condiciones antes de la pata ' + $Etiqueta + ']')
    $L.Add('  fecha: ' + (Get-Date).ToString('o'))

    # RAM y CPUs
    $os = Get-CimInstance Win32_OperatingSystem
    $L.Add('  RAM total: ' + [math]::Round($os.TotalVisibleMemorySize / 1MB, 2).ToString($script:Inv) + ' GB; libre: ' +
           [math]::Round($os.FreePhysicalMemory / 1MB, 2).ToString($script:Inv) + ' GB; CPUs logicas: ' + [Environment]::ProcessorCount)

    # Procesos claude / python / powershell, con los del medidor separados
    $todos = Get-Procesos
    $par = Get-Parentesco -Todos $todos
    $nombres = @('claude.exe', 'python.exe', 'pythonw.exe', 'powershell.exe', 'pwsh.exe')
    $interes = @($todos | Where-Object { $nombres -contains $_.Name.ToLowerInvariant() } | Sort-Object Pid)
    $cuenta = @{ claude = 0; python = 0; powershell = 0 }
    foreach ($p in $interes) {
        $n = $p.Name.ToLowerInvariant()
        if ($n -eq 'claude.exe') { $cuenta.claude++ } elseif ($n -like 'python*') { $cuenta.python++ } else { $cuenta.powershell++ }
    }
    $propios = @($interes | Where-Object { $par.Propios.Contains($_.Pid) }).Count
    $lanzs = @($interes | Where-Object { $par.Lanzadores.Contains($_.Pid) }).Count
    $L.Add('  procesos: claude=' + $cuenta.claude + ', python=' + $cuenta.python + ', powershell=' + $cuenta.powershell +
           ' (del medidor: ' + $propios + '; de su cadena de lanzadores: ' + $lanzs + '; otros: ' + ($interes.Count - $propios - $lanzs) + ')')
    foreach ($p in $interes) {
        $L.Add('    pid=' + $p.Pid + ' ppid=' + $p.Ppid + ' ' + $p.Name + ' [' + (Get-ClaseDeProceso -P $p -Par $par) + '] ' + (Format-Cmd $p.Cmd))
    }
    $yo = $todos | Where-Object { $_.Pid -eq $PID } | Select-Object -First 1
    if ($yo) {
        $lanzador = $todos | Where-Object { $_.Pid -eq $yo.Ppid } | Select-Object -First 1
        if ($lanzador) { $L.Add('  proceso lanzador del medidor: pid=' + $lanzador.Pid + ' ' + $lanzador.Name + ' ' + (Format-Cmd $lanzador.Cmd)) }
        else { $L.Add('  proceso lanzador del medidor: pid=' + $yo.Ppid + ' (ya no existe)') }
    }

    # Otra corrida pesada: pesada.json (informativo; el candado no se prueba) y los procesos
    $sospechosos = @($interes | Where-Object {
        (Get-ClaseDeProceso -P $_ -Par $par) -eq 'otro' -and $_.Cmd -match '(?i)Invoke-Tests|correr\.py|Measure-TestRuns|Compare-TestRuns'
    })
    $infoRuta = ''
    if ($env:LOCALAPPDATA) { $infoRuta = Join-Path $env:LOCALAPPDATA 'gcba-harness\recursos\pesada.json' }
    $infoTexto = 'pesada.json: no existe'
    $dueno = $null
    if ($infoRuta -and [System.IO.File]::Exists($infoRuta)) {
        try {
            $j = [System.IO.File]::ReadAllText($infoRuta, $script:Utf8) | ConvertFrom-Json
            $vivo = $false
            if ($j.pid -is [int] -or $j.pid -is [long]) { $vivo = [bool]($todos | Where-Object { $_.Pid -eq [int]$j.pid }) }
            $infoTexto = 'pesada.json: pid=' + $j.pid + ' desde=' + $j.desde + ' raiz=' + $j.raiz + ' workers=' + $j.workers +
                         '; ese pid esta vivo: ' + $(if ($vivo) { 'SI' } else { 'NO' }) + ' (informativo; el candado no se prueba: el medidor no lo toma)'
            if ($vivo) { $dueno = $j.pid }
        } catch { $infoTexto = 'pesada.json: ilegible (' + $_.Exception.Message + ')' }
    }
    $L.Add('  ' + $infoTexto)
    $otra = ($sospechosos.Count -gt 0 -or $null -ne $dueno)
    $L.Add('  otra corrida pesada: ' + $(if ($otra) { 'SI (' + $sospechosos.Count + ' proceso(s) de prueba ajenos' + $(if ($null -ne $dueno) { '; pid del candado vivo' } else { '' }) + ')' } else { 'NO' }))
    foreach ($p in $sospechosos) { $L.Add('    ajeno: pid=' + $p.Pid + ' ' + $p.Name + ' ' + (Format-Cmd $p.Cmd)) }

    # bash: el del proceso lanzador (sin tocar el PATH) y el que ve cada herramienta
    $todosBash = @(Get-Command bash -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source })
    $bashEf = ''
    if ($todosBash.Count -gt 0) { $bashEf = [string]$todosBash[0] }
    $L.Add('  Get-Command bash -All (en el medidor): ' + $(if ($todosBash.Count) { $todosBash -join '  |  ' } else { '(ninguno)' }))
    $L.Add('  bash efectivo: ' + $(if ($bashEf) { $bashEf } else { '(ninguno)' }))
    if ($bashEf) {
        $bv = Invoke-Corto -Exe $bashEf -Argumentos '--version' -TopeMs 30000 -Entorno $entorno
        $L.Add('  bash --version (primera linea): ' + $(if ($bv.Ok) { Get-PrimeraLinea $bv.Out } else { 'no corrio: ' + $bv.Err }))
    }
    else { $L.Add('  bash --version (primera linea): (no hay bash en el PATH)') }
    $gitSrc = Resolve-Exe 'git'
    $gitRoot = ''
    if ($gitSrc) {
        $d = Split-Path $gitSrc -Parent
        for ($i = 0; $i -lt 4 -and $d; $i++) {
            if ([System.IO.File]::Exists($d + '\bin\bash.exe') -or [System.IO.File]::Exists($d + '\usr\bin\bash.exe')) { $gitRoot = $d; break }
            $d = Split-Path $d -Parent
        }
    }
    $frente = ($bashEf -and $gitRoot -and $bashEf.StartsWith($gitRoot + '\', [System.StringComparison]::OrdinalIgnoreCase))
    $L.Add('  Git Bash al frente del PATH: ' + $(if ($frente) { 'SI' } else { 'NO' }) + ' (git en ' + $(if ($gitSrc) { $gitSrc } else { '(no encontrado)' }) +
           '; instalacion de Git derivada de ahi: ' + $(if ($gitRoot) { $gitRoot } else { '(no se pudo derivar)' }) + ')')
    $pyExe = ''
    $pyVer = ''
    $pyWhich = ''
    foreach ($c in @('python', 'py', 'python3')) {
        $cExe = Resolve-Exe $c
        if (-not $cExe) { continue }
        $r = Invoke-Corto -Exe $cExe -Argumentos '-c "import sys, shutil; print(sys.executable); print(shutil.which(\"bash\") or \"\"); print(sys.version.split()[0])"' -TopeMs 30000 -Entorno $entorno
        if ($r.Ok -and $r.Exit -eq 0) {
            $ls = @($r.Out -split "`r?`n")
            if ($ls.Count -ge 3 -and $ls[0] -and [System.IO.File]::Exists($ls[0].Trim())) { $pyExe = $ls[0].Trim(); $pyWhich = $ls[1].Trim(); $pyVer = $ls[2].Trim(); break }
        }
    }
    $L.Add('  python: ' + $(if ($pyExe) { $pyExe + ' (' + $pyVer + ')' } else { '(no se encontro un interprete valido: python, py, python3)' }))
    $L.Add('  shutil.which("bash") con el entorno de la pata: ' + $(if ($pyWhich) { $pyWhich } else { '(ninguno)' }))
    $gv = $null
    if ($gitSrc) { $gv = Invoke-Corto -Exe $gitSrc -Argumentos '--version' -TopeMs 30000 }
    $L.Add('  git --version: ' + $(if ($gv -and $gv.Ok) { Get-PrimeraLinea $gv.Out } else { 'no corrio' }))
    $pathEntradas = @($env:PATH -split ';' | Where-Object { $_ })
    $L.Add('  PATH: no se toca (el medidor no antepone nada); primeras entradas: ' + (($pathEntradas | Select-Object -First 3) -join '  ;  '))

    # temporales y su formato
    foreach ($v in @('TEMP', 'TMP', 'TMPDIR')) {
        $val = [string]$entorno[$v]
        $fmt = if ($val -match '~\d') { '8.3' } else { 'largo' }
        $L.Add('  ' + $v + '=' + $val + '  (formato ' + $fmt + ', segun la presencia de ~n en la ruta)')
    }
    $elevado = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $L.Add('  elevado: ' + $elevado + $(if ($elevado) { '  (ADVERTENCIA: la spec pide no elevado)' } else { '' }))
    $L.Add('  workers: ' + $Workers)

    # el arbol
    $branch = ''; $ver = ''; $tag = ''
    try { $branch = (Invoke-Git -Raiz $Raiz -Argumentos @('branch', '--show-current')).Trim() } catch { }
    $verRuta = Join-Path $Raiz 'VERSION'
    if ([System.IO.File]::Exists($verRuta)) { $ver = ([System.IO.File]::ReadAllText($verRuta)).Trim() }
    if ($gitSrc) {
        $t = Invoke-Corto -Exe $gitSrc -Argumentos ('-C "' + $Raiz + '" describe --tags --exact-match') -Cwd $Raiz -TopeMs 30000
        if ($t.Ok -and $t.Exit -eq 0) { $tag = Get-PrimeraLinea $t.Out }
    }
    $L.Add('  raiz del arbol: ' + $Raiz)
    $L.Add('  HEAD: ' + $Huella.Head + '; rama: ' + $(if ($branch) { $branch } else { '(ninguna)' }) + '; VERSION: ' + $(if ($ver) { $ver } else { '(sin archivo)' }) +
           '; tag exacto: ' + $(if ($tag) { $tag } else { '(ninguno)' }) + '; lineas de status: ' + $Huella.StatusLineas)
    $base = New-Object System.Collections.Generic.List[string]
    foreach ($ref in @('v0.33.0', 'fdca5ce', 'ea2dff7', '4c6f0f3', 'f9393cf')) {
        $r = $null
        if ($gitSrc) { $r = Invoke-Corto -Exe $gitSrc -Argumentos ('-C "' + $Raiz + '" rev-parse --verify --quiet "' + $ref + '^{commit}"') -Cwd $Raiz -TopeMs 30000 }
        $base.Add($ref + '=' + $(if ($r -and $r.Ok -and $r.Exit -eq 0) { 'presente' } else { 'AUSENTE' }))
    }
    $L.Add('  tags y commits base que leen las suites: ' + ($base -join ', '))
    $L.Add('  huella: ' + (Format-Huella $Huella))

    return [pscustomobject]@{ Lineas = @($L); BashEfectivo = $bashEf; Procesos = @($todos); Elevado = $elevado; GitBashAlFrente = [bool]$frente }
}


# -- Una pata ---------------------------------------------------------------------------

function New-CarpetaVacia {
    param([string] $Ruta)
    if ([System.IO.Directory]::Exists($Ruta) -or [System.IO.File]::Exists($Ruta)) { throw "la carpeta de la pata ya existe: $Ruta" }
    [void][System.IO.Directory]::CreateDirectory($Ruta)
    if (@(Get-ChildItem -LiteralPath $Ruta -Force).Count -ne 0) { throw "la carpeta de la pata no esta vacia: $Ruta" }
}


function Stop-ArbolDe {
    <# taskkill /PID <pid> /T /F del proceso que lanzo este medidor. Nunca por nombre de imagen. #>
    param([int] $ProcId)
    try {
        $tk = [System.IO.Path]::Combine($env:SystemRoot, 'System32\taskkill.exe')
        [void](Invoke-Corto -Exe $tk -Argumentos ('/PID ' + $ProcId + ' /T /F') -TopeMs 30000)
    } catch { }
}


function Read-NuevasLineas {
    <# Lee lo que se agrego a la captura y devuelve las lineas completas; el resto queda en $Estado.Resto. #>
    param($Tail, $Estado)
    $nuevas = New-Object System.Collections.Generic.List[string]
    if ($Tail.Length -le $Tail.Position) { return @($nuevas) }
    $buf = New-Object byte[] 65536
    while ($Tail.Length -gt $Tail.Position) {
        $n = $Tail.Read($buf, 0, $buf.Length)
        if ($n -le 0) { break }
        $ch = New-Object char[] ($buf.Length + 4)
        $c = $Estado.Decoder.GetChars($buf, 0, $n, $ch, 0)
        $Estado.Resto += [string]::new($ch, 0, $c)
    }
    while (($i = $Estado.Resto.IndexOf("`n")) -ge 0) {
        $nuevas.Add($Estado.Resto.Substring(0, $i).TrimEnd("`r"))
        $Estado.Resto = $Estado.Resto.Substring($i + 1)
    }
    return @($nuevas)
}


function Invoke-Pata {
    <#
    .SYNOPSIS
        Corre un script de tests\ como proceso propio, con TEMP/TMP/TMPDIR de la pata, capturado a
        archivo, con su wall y el muestreo de RAM en este mismo proceso.
    .DESCRIPTION
        El muestreador es el propio bucle de espera: no hay proceso aparte, asi que no sobrevive al
        medidor. Si el medidor se corta, el finally mata el arbol de la pata (por pid, nunca por
        nombre de imagen).
    #>
    param(
        [string] $Nombre,
        [string] $Script,
        [string[]] $ArgsDelScript,
        [string] $Raiz,
        [string] $TempDir,
        [string] $SalidaPath,
        [string] $ErrPath,
        [bool] $ConProgreso
    )

    $linea = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $Script + '"'
    foreach ($a in $ArgsDelScript) { $linea += ' ' + $a }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $script:Powershell
    $psi.Arguments = $linea
    $psi.WorkingDirectory = $Raiz
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $false
    $psi.EnvironmentVariables['TEMP'] = $TempDir
    $psi.EnvironmentVariables['TMP'] = $TempDir
    $psi.EnvironmentVariables['TMPDIR'] = $TempDir

    $r = [ordered]@{
        Nombre = $Nombre; Comando = ($script:Powershell + ' ' + $linea); Exit = $null; WallSeg = 0.0
        Inicio = $null; Fin = $null; BytesOut = 0; BytesErr = 0; CapturaOutCerro = $false; CapturaErrCerro = $false
        RamMuestras = 0; RamPrimera = $null; RamMin = $null; RamMinHoraSeg = $null; RamMax = $null; RamUltima = $null
        Llegadas = (New-Object System.Collections.Generic.List[object]); PidRaiz = 0
    }

    $fsOut = [System.IO.FileStream]::new($SalidaPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite, 1)
    $fsErr = [System.IO.FileStream]::new($ErrPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite, 1)
    $tail = $null
    $estadoTail = $null
    if ($ConProgreso) {
        $tail = [System.IO.FileStream]::new($SalidaPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $estadoTail = [pscustomobject]@{ Resto = ''; Decoder = $script:Utf8.GetDecoder() }
    }
    $p = $null
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $r.Inicio = Get-Date
        $p = [System.Diagnostics.Process]::Start($psi)
        $r.PidRaiz = $p.Id
        $p.StandardInput.Close()
        $tOut = $p.StandardOutput.BaseStream.CopyToAsync($fsOut)
        $tErr = $p.StandardError.BaseStream.CopyToAsync($fsErr)

        $proximaRam = 0.0
        $proximoLatido = $script:CadaLatidoSeg
        while ($true) {
            if ($p.WaitForExit(100)) { $sw.Stop(); break }
            $t = $sw.Elapsed.TotalSeconds
            if ($t -ge $proximaRam) {
                $libre = Get-RamLibreGB
                $r.RamMuestras++
                if ($null -eq $r.RamPrimera) { $r.RamPrimera = $libre }
                if ($null -eq $r.RamMin -or $libre -lt $r.RamMin) { $r.RamMin = $libre; $r.RamMinHoraSeg = $t }
                if ($null -eq $r.RamMax -or $libre -gt $r.RamMax) { $r.RamMax = $libre }
                $r.RamUltima = $libre
                $proximaRam = $t + $script:CadaRamSeg
            }
            if ($null -ne $tail) {
                foreach ($l in (Read-NuevasLineas -Tail $tail -Estado $estadoTail)) {
                    $m = [regex]::Match($l, $script:ReProgreso)
                    if ($m.Success) {
                        $r.Llegadas.Add([pscustomobject]@{ Suite = $m.Groups[4].Value; Estado = $m.Groups[3].Value; Seg = [double]::Parse($m.Groups[6].Value, $script:Inv); Llegada = $sw.Elapsed.TotalSeconds })
                    }
                }
            }
            if ($t -ge $proximoLatido) {
                Write-Host ('  ... pata ' + $Nombre + ' en curso: ' + (Format-Hms $t) + ', RAM libre ' + $r.RamUltima + ' GB') -ForegroundColor DarkGray
                $proximoLatido = $t + $script:CadaLatidoSeg
            }
        }
        $r.WallSeg = $sw.Elapsed.TotalSeconds
        $r.Fin = Get-Date
        $r.Exit = $p.ExitCode

        # Una ultima muestra y lo que quedo por leer de la captura.
        $libre = Get-RamLibreGB
        $r.RamMuestras++
        if ($null -eq $r.RamPrimera) { $r.RamPrimera = $libre }
        if ($null -eq $r.RamMin -or $libre -lt $r.RamMin) { $r.RamMin = $libre; $r.RamMinHoraSeg = $r.WallSeg }
        if ($null -eq $r.RamMax -or $libre -gt $r.RamMax) { $r.RamMax = $libre }
        $r.RamUltima = $libre

        # Un nieto que heredo el pipe lo mantiene abierto: no se espera sin tope.
        $r.CapturaOutCerro = $tOut.Wait(20000)
        $r.CapturaErrCerro = $tErr.Wait(5000)
        $fsOut.Flush()
        $fsErr.Flush()
        if ($null -ne $tail) {
            foreach ($l in (Read-NuevasLineas -Tail $tail -Estado $estadoTail)) {
                $m = [regex]::Match($l, $script:ReProgreso)
                if ($m.Success) {
                    $r.Llegadas.Add([pscustomobject]@{ Suite = $m.Groups[4].Value; Estado = $m.Groups[3].Value; Seg = [double]::Parse($m.Groups[6].Value, $script:Inv); Llegada = $r.WallSeg })
                }
            }
        }
    }
    finally {
        # El medidor se corta (Ctrl-C, un error): la pata no queda corriendo sola.
        if ($null -ne $p) {
            try { if (-not $p.HasExited) { Stop-ArbolDe -ProcId $p.Id } } catch { }
            try { $p.Dispose() } catch { }
        }
        try { $fsOut.Dispose() } catch { }
        try { $fsErr.Dispose() } catch { }
        if ($null -ne $tail) { try { $tail.Dispose() } catch { } }
    }
    $r.BytesOut = ([System.IO.FileInfo]$SalidaPath).Length
    $r.BytesErr = ([System.IO.FileInfo]$ErrPath).Length
    return [pscustomobject]$r
}


function Write-Pata {
    param($R, [string] $Titulo)
    Write-Registro ('[' + $Titulo + ']')
    Write-Registro ('  comando: ' + $R.Comando)
    Write-Registro ('  inicio: ' + $R.Inicio.ToString('o') + '; fin: ' + $R.Fin.ToString('o') + '; pid de la raiz de la pata: ' + $R.PidRaiz)
    Write-Registro ('  wall (Stopwatch): ' + (Format-Seg $R.WallSeg) + ' s (' + (Format-Hms $R.WallSeg) + '); exit: ' + $R.Exit)
    Write-Registro ('  stdout: ' + $R.BytesOut + ' bytes (captura cerrada: ' + $(if ($R.CapturaOutCerro) { 'si' } else { 'NO: un proceso heredo el pipe' }) + '); stderr: ' + $R.BytesErr + ' bytes')
    Write-Registro ('  RAM libre durante la pata: primera ' + $R.RamPrimera + ' GB, minima ' + $R.RamMin + ' GB (a los ' + (Format-Seg $R.RamMinHoraSeg) + ' s), maxima ' + $R.RamMax + ' GB, ultima ' + $R.RamUltima +
                    ' GB; ' + $R.RamMuestras + ' muestras cada ' + $script:CadaRamSeg + ' s, del proceso del medidor')
}


# -- Residuos y procesos al terminar ----------------------------------------------------

function Get-Residuos {
    <# TempBase es nuevo y vacio al empezar: lo que haya de hpp-* y de s<nnn> es de la corrida. #>
    param([string] $TempBase)
    $items = New-Object System.Collections.Generic.List[string]
    $otros = New-Object System.Collections.Generic.List[string]
    foreach ($e in @(Get-ChildItem -LiteralPath $TempBase -Force -ErrorAction SilentlyContinue)) {
        if ($e.PSIsContainer -and $e.Name -match '^hpp-') {
            $items.Add('raiz ' + $e.FullName)
            foreach ($s in @(Get-ChildItem -LiteralPath $e.FullName -Force -Directory -ErrorAction SilentlyContinue)) {
                if ($s.Name -match '^s\d{3}$') { $items.Add('suite ' + $s.FullName) }
            }
        }
        elseif ((-not $e.PSIsContainer) -and $e.Name -match '^hpp-.*\.lock$') { $items.Add('sidecar ' + $e.FullName) }
        elseif ($e.PSIsContainer -and $e.Name -match '^s\d{3}$') { $items.Add('suite ' + $e.FullName) }
        elseif ((-not $e.PSIsContainer) -and ($e.Name -eq 'pesada.lock' -or $e.Name -eq 'pesada.json')) { $otros.Add($e.Name + ' (estable por diseno: no cuenta)') }
        else { $otros.Add($e.Name) }
    }
    return [pscustomobject]@{ Items = @($items); Otros = @($otros) }
}


function Get-ProcesosAtribuibles {
    <# python/powershell nuevos desde antes de la pata y todavia vivos, con la razon por la que se atribuyen. #>
    param($Antes, [string] $Raiz, [string] $TempDir)
    $conocidos = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($p in $Antes) { [void]$conocidos.Add((Get-ClaveDeProceso $p)) }
    $ahora = Get-Procesos
    $par = Get-Parentesco -Todos $ahora
    $nombres = @('python.exe', 'pythonw.exe', 'powershell.exe', 'pwsh.exe')
    $res = New-Object System.Collections.Generic.List[string]
    foreach ($p in ($ahora | Where-Object { $nombres -contains $_.Name.ToLowerInvariant() } | Sort-Object Pid)) {
        if ($p.Pid -eq $PID) { continue }
        if ($conocidos.Contains((Get-ClaveDeProceso $p))) { continue }
        $razon = ''
        if ($par.Propios.Contains($p.Pid)) { $razon = 'descendiente vivo del medidor' }
        elseif ($p.Cmd -and ($p.Cmd.IndexOf($TempDir, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -or $p.Cmd.IndexOf($Raiz, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)) { $razon = 'su linea de comandos nombra la raiz o el temporal de la pata' }
        else { $razon = 'nuevo desde la pata, sin atribuir' }
        $res.Add('pid=' + $p.Pid + ' ppid=' + $p.Ppid + ' ' + $p.Name + ' [' + $razon + '] ' + (Format-Cmd $p.Cmd))
    }
    return @($res)
}


function Get-DuracionesDeSuite {
    <# De las lineas de progreso del runner (spec 16.6), en el orden canonico del oraculo (PS y despues Py). #>
    param([string] $SalidaPath, [string] $Raiz)
    $texto = [System.IO.File]::ReadAllText($SalidaPath, $script:Utf8)
    $porSuite = @{}
    $orden = New-Object System.Collections.Generic.List[string]
    foreach ($l in ($texto -split "`r?`n")) {
        $m = [regex]::Match($l, $script:ReProgreso)
        if (-not $m.Success) { continue }
        $nombre = $m.Groups[4].Value
        if (-not $porSuite.ContainsKey($nombre)) { $orden.Add($nombre) }
        $porSuite[$nombre] = [pscustomobject]@{ Suite = $nombre; Estado = $m.Groups[3].Value; Seg = [double]::Parse($m.Groups[6].Value, $script:Inv); Filas = [int]$m.Groups[5].Value }
    }
    # El orden canonico es el de la enumeracion del oraculo (spec 20.1): los .ps1 por nombre y los .py
    # como correr.py los ordena (minusculas, punto de codigo).
    $casos = Join-Path $Raiz 'tests\casos'
    $canon = New-Object System.Collections.Generic.List[string]
    foreach ($f in @(Get-ChildItem $casos -Filter '*.ps1' -ErrorAction SilentlyContinue | Sort-Object Name)) { $canon.Add($f.Name) }
    $py = New-Object System.Collections.Generic.List[string]
    foreach ($f in @(Get-ChildItem $casos -File -Filter '*.py' -ErrorAction SilentlyContinue)) { $py.Add($f.Name) }
    $py.Sort([System.Comparison[string]]{ param($x, $y) [string]::CompareOrdinal($x.ToLowerInvariant(), $y.ToLowerInvariant()) })
    foreach ($n in $py) { $canon.Add($n) }
    $salida = @()
    foreach ($n in $canon) { if ($porSuite.ContainsKey($n)) { $salida += $porSuite[$n] } }
    foreach ($n in $orden) { if (-not $canon.Contains($n)) { $salida += $porSuite[$n] } }
    return $salida
}


# -- Lo que guarda el modo normal y lo que lee el modo de reuso (spec 5.4, 9.6) ---------

function Get-ShaDeArchivo {
    param([string] $Ruta)
    $alg = [System.Security.Cryptography.SHA256]::Create()
    return (Get-HashHex -Alg $alg -Bytes ([System.IO.File]::ReadAllBytes($Ruta))).ToUpperInvariant()
}


function Format-Doble {
    param($V)
    if ($null -eq $V) { return $null }
    return ([double]$V).ToString('R', $script:Inv)
}


function Save-PataSerial {
    <# Modo normal: deja en la carpeta de capturas lo que el reuso de la pata serial necesita, en archivos legibles
       por maquina: pata-serial.json y lista-final.txt (la lista de la huella FINAL del par). #>
    param([string] $Carpeta, [string] $Raiz, [int] $Workers, $H0, $H1, $H2, $Serial, $C1, [string] $OutSerial)
    $rutaLista = Join-Path $Carpeta $script:ArchivoLista
    [System.IO.File]::WriteAllText($rutaLista, (@($H2.Filas) -join "`n"), $script:Utf8)
    $datos = [ordered]@{
        schema = $script:EsquemaSerial
        completo = $true
        fecha = (Get-Date).ToString('o')
        raiz = $Raiz
        workers = $Workers
        head = $H2.Head
        status = $H2.Status
        huellaInicial = $H0.Huella
        huellaEntre = $H1.Huella
        huellaFinal = $H2.Huella
        huellasIguales = [bool]($H0.Huella -ceq $H1.Huella -and $H1.Huella -ceq $H2.Huella)
        archivosFinal = $H2.Archivos
        listaArchivo = $script:ArchivoLista
        listaSha256 = (Get-ShaDeArchivo -Ruta $rutaLista)
        serialArchivo = 'serial.txt'
        serialSha256 = (Get-ShaDeArchivo -Ruta $OutSerial)
        serialBytes = ([System.IO.FileInfo]$OutSerial).Length
        serialComando = $Serial.Comando
        serialWallSeg = (Format-Doble $Serial.WallSeg)
        serialExit = $Serial.Exit
        serialRamMinGB = (Format-Doble $Serial.RamMin)
        bashEfectivoSerial = $C1.BashEfectivo
        gitBashAlFrente = [bool]$C1.GitBashAlFrente
        elevado = [bool]$C1.Elevado
        condicionesSerial = @($C1.Lineas)
    }
    [System.IO.File]::WriteAllText((Join-Path $Carpeta $script:ArchivoSerial), (ConvertTo-Json -InputObject $datos -Depth 4), $script:Utf8)
}


function Read-PataSerial {
    <# Modo de reuso: lee lo guardado por Save-PataSerial y lo comprueba contra si mismo (los dos archivos y la
       captura por su sha256, la huella final recalculada de la lista). Ok = $false con la causa si algo falta o no cierra. #>
    param([string] $Carpeta)
    function Falla([string] $Causa) { return [pscustomobject]@{ Ok = $false; Causa = $Causa } }
    $rJson = Join-Path $Carpeta $script:ArchivoSerial
    $rLista = Join-Path $Carpeta $script:ArchivoLista
    $rSerial = Join-Path $Carpeta 'serial.txt'
    foreach ($r in @($rJson, $rLista, $rSerial)) {
        if (-not [System.IO.File]::Exists($r)) { return (Falla ('falta ' + $r + ' en la carpeta de reuso')) }
    }
    $j = $null
    try { $j = [System.IO.File]::ReadAllText($rJson, $script:Utf8) | ConvertFrom-Json }
    catch { return (Falla ($script:ArchivoSerial + ' ilegible: ' + $_.Exception.Message)) }
    if ($null -eq $j -or [string]$j.schema -cne $script:EsquemaSerial) { return (Falla ($script:ArchivoSerial + ' no es del esquema ' + $script:EsquemaSerial)) }
    foreach ($c in @('completo', 'head', 'status', 'huellaInicial', 'huellaEntre', 'huellaFinal', 'huellasIguales', 'listaSha256',
                     'serialSha256', 'serialWallSeg', 'serialExit', 'bashEfectivoSerial', 'condicionesSerial')) {
        if (-not ($j.PSObject.Properties.Name -contains $c)) { return (Falla ($script:ArchivoSerial + ' no tiene el campo ' + $c)) }
    }
    if ($j.completo -ne $true) { return (Falla 'el registro guardado no esta completo') }
    if ((Get-ShaDeArchivo -Ruta $rLista) -cne [string]$j.listaSha256) { return (Falla ($script:ArchivoLista + ' no coincide con el sha256 guardado')) }
    if ((Get-ShaDeArchivo -Ruta $rSerial) -cne [string]$j.serialSha256) { return (Falla 'serial.txt no coincide con el sha256 guardado') }
    $textoLista = [System.IO.File]::ReadAllText($rLista, $script:Utf8)
    [string[]]$filas = @($textoLista -split "`r?`n" | Where-Object { $_.Length -gt 0 })
    $recalculada = Get-HuellaDeLista -Head ([string]$j.head) -Status ([string]$j.status) -Filas $filas
    if ($recalculada -cne [string]$j.huellaFinal) { return (Falla 'la huella final guardada no sale de la lista, el HEAD y el status guardados') }
    $wall = 0.0
    if (-not [double]::TryParse([string]$j.serialWallSeg, [System.Globalization.NumberStyles]::Float, $script:Inv, [ref]$wall)) { return (Falla 'serialWallSeg no es un numero') }
    $ram = $null
    if ($j.PSObject.Properties.Name -contains 'serialRamMinGB' -and $null -ne $j.serialRamMinGB) {
        $rv = 0.0
        if ([double]::TryParse([string]$j.serialRamMinGB, [System.Globalization.NumberStyles]::Float, $script:Inv, [ref]$rv)) { $ram = $rv }
    }
    return [pscustomobject]@{
        Ok = $true; Causa = ''; Carpeta = $Carpeta; Json = $j; Filas = $filas; SerialPath = $rSerial
        Head = [string]$j.head; Status = [string]$j.status; HuellaFinal = [string]$j.huellaFinal
        HuellasIguales = ($j.huellasIguales -eq $true); WallSeg = $wall; Exit = [int]$j.serialExit; RamMin = $ram
        Bash = [string]$j.bashEfectivoSerial; Condiciones = @($j.condicionesSerial)
        GitBashAlFrente = ($j.gitBashAlFrente -eq $true); Elevado = ($j.elevado -eq $true)
    }
}


function Compare-Listas {
    <# La lista guardada contra la del arbol de cierre: que rutas difieren (cambiadas, agregadas, borradas), y si
       alguna es distinta de la unica excluida. #>
    param([string[]] $Guardada, [string[]] $Actual, [string] $Excluida)
    $g = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    $a = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    foreach ($par in @(@($Guardada, $g), @($Actual, $a))) {
        foreach ($f in $par[0]) {
            $i = $f.IndexOf("`t")
            if ($i -lt 0) { continue }
            $par[1][$f.Substring(0, $i)] = $f.Substring($i + 1)
        }
    }
    $cambios = New-Object System.Collections.Generic.List[string]
    $otros = New-Object System.Collections.Generic.List[string]
    $claves = New-Object 'System.Collections.Generic.SortedSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($k in $g.Keys) { [void]$claves.Add($k) }
    foreach ($k in $a.Keys) { [void]$claves.Add($k) }
    foreach ($k in $claves) {
        $enG = $g.ContainsKey($k)
        $enA = $a.ContainsKey($k)
        $txt = ''
        if ($enG -and $enA) { if ($g[$k] -ceq $a[$k]) { continue }; $txt = $k + ' (cambiada: ' + $g[$k].Replace("`t", ' / ') + ' -> ' + $a[$k].Replace("`t", ' / ') + ')' }
        elseif ($enG) { $txt = $k + ' (ya no esta en el arbol de cierre)' }
        else { $txt = $k + ' (nueva en el arbol de cierre)' }
        $cambios.Add($txt)
        if ($k -cne $Excluida) { $otros.Add($txt) }
    }
    return [pscustomobject]@{
        Cambios = @($cambios); Otros = @($otros)
        ExcluidaEnLasDos = ($g.ContainsKey($Excluida) -and $a.ContainsKey($Excluida))
        ExcluidaCambio = ($g.ContainsKey($Excluida) -and $a.ContainsKey($Excluida) -and $g[$Excluida] -cne $a[$Excluida])
    }
}


function Get-GrupoPy {
    <# De la salida del oraculo (completa o de -SoloCaso): la linea de grupo de una suite Python y sus ok y total. #>
    param([string] $Texto, [string] $Stem)
    $ls = @($Texto -split "`r?`n")
    $iPy = -1
    for ($i = $ls.Count - 1; $i -ge 0; $i--) { if ($ls[$i].Trim() -ceq 'gcba-harness - tests (python)') { $iPy = $i; break } }
    if ($iPy -lt 0) { return [pscustomobject]@{ Encontrada = $false; Causa = 'no hay seccion de python'; Linea = ''; Pasaron = 0; Total = 0 } }
    $hall = New-Object System.Collections.Generic.List[object]
    for ($i = $iPy + 1; $i -lt $ls.Count; $i++) {
        $l = $ls[$i].TrimEnd("`r")
        if ($l -cmatch $script:ReGrupoOraculo -and $Matches[1] -ceq $Stem) {
            $cuenta = 0; $malos = 0
            if ($Matches[3]) { $malos = [int]$Matches[2]; $cuenta = [int]$Matches[3] } else { $cuenta = [int]$Matches[2] }
            $hall.Add([pscustomobject]@{ Linea = $l; Pasaron = ($cuenta - $malos); Total = $cuenta })
        }
    }
    if ($hall.Count -ne 1) {
        return [pscustomobject]@{ Encontrada = $false; Causa = ('lineas de grupo de ' + $Stem + ': ' + $hall.Count + ' (se esperaba 1)'); Linea = ''; Pasaron = 0; Total = 0 }
    }
    return [pscustomobject]@{ Encontrada = $true; Causa = ''; Linea = $hall[0].Linea; Pasaron = $hall[0].Pasaron; Total = $hall[0].Total }
}


function Write-NoMedible {
    param([string] $Motivo)
    Write-Registro ('REUSO_NO_POSIBLE ' + $Motivo) 'Red'
    Write-Registro 'NO SE PUDO MEDIR (exit 2): la pata serial reutilizada no se acepta; no se mide ni se acepta ningun par' 'Red'
}


# -- La medicion ------------------------------------------------------------------------

function Invoke-Medicion {
    param([int] $Workers, [bool] $ConUmbral, [double] $Umbral, [bool] $ConReuso = $false, [string] $ReusarDe = '')

    $raiz = Split-Path -Parent $PSScriptRoot
    $motivos = New-Object System.Collections.Generic.List[string]
    $origen = ''

    if ($Workers -lt 1 -or $Workers -gt 4) {
        Write-Registro ('ARGUMENTO_INVALIDO -Workers tiene que ser un entero de 1 a 4 (recibi ' + $Workers + ').') 'Red'
        return 2
    }
    if ($ConUmbral -and $Umbral -le 0) {
        Write-Registro ('ARGUMENTO_INVALIDO -Umbral tiene que ser una fraccion mayor que 0 (recibi ' + $Umbral.ToString($script:Inv) + ').') 'Red'
        return 2
    }
    if ([string]::IsNullOrWhiteSpace($env:TEMP)) {
        Write-Registro 'ARGUMENTO_INVALIDO el medidor necesita un TEMP donde dejar sus carpetas y no hay ninguno.' 'Red'
        return 2
    }
    if ($ConReuso) {
        if ([string]::IsNullOrWhiteSpace($ReusarDe)) {
            Write-Registro 'ARGUMENTO_INVALIDO -ReusarSerialDe necesita la carpeta hpm-... de un par anterior y vino vacio.' 'Red'
            return 2
        }
        $origen = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ReusarDe)
        if (-not [System.IO.Directory]::Exists($origen)) {
            Write-Registro ('ARGUMENTO_INVALIDO -ReusarSerialDe: la carpeta no existe: ' + $origen) 'Red'
            Write-Registro 'NO SE PUDO MEDIR (exit 2): no hay pata serial que reutilizar' 'Red'
            return 2
        }
    }

    # Carpeta propia del medidor, y dentro, el temporal de cada pata: nuevos, vacios y hermanos
    # (el mismo formato de ruta).
    $marca = (Get-Date).ToString('yyMMdd-HHmmss')
    $work = Join-Path $env:TEMP ('hpm-' + $marca)
    if ([System.IO.Directory]::Exists($work)) { $work = $work + '-' + [guid]::NewGuid().ToString('N').Substring(0, 4) }
    New-CarpetaVacia -Ruta $work
    $script:CarpetaDeCapturas = $work
    $script:NombresDeCapturas = $(if ($ConReuso) { 'paralelo.txt, paralelo.err.txt, comparador.txt, reuso-<suite>.txt, registro.txt' } else { 'serial.txt, serial.err.txt, paralelo.txt, paralelo.err.txt, comparador.txt, registro.txt, ' + $script:ArchivoSerial + ', ' + $script:ArchivoLista })
    $tmpSerial = Join-Path $work 'tmp-serial'
    $tmpParalelo = Join-Path $work 'tmp-paralelo'
    if (-not $ConReuso) { New-CarpetaVacia -Ruta $tmpSerial }
    New-CarpetaVacia -Ruta $tmpParalelo
    $outSerial = Join-Path $work 'serial.txt'
    $errSerial = Join-Path $work 'serial.err.txt'
    $outParalelo = Join-Path $work 'paralelo.txt'
    $errParalelo = Join-Path $work 'paralelo.err.txt'

    Write-Registro $(if ($ConReuso) { '== Measure-TestRuns: VP-E25, el par que cierra, con la pata serial REUTILIZADA (D-T2) ==' } else { '== Measure-TestRuns: VP-E25, el par serial contra paralelo ==' })
    Write-Registro ('raiz del arbol medido: ' + $raiz)
    Write-Registro ('inicio: ' + (Get-Date).ToString('o'))
    Write-Registro ('workers de la pata paralela: ' + $Workers + '; umbral: ' + $(if ($ConUmbral) { $Umbral.ToString($script:Inv) } else { '(sin umbral)' }))
    if ($ConReuso) {
        Write-Registro ('orden de las patas: la serial NO corre (es la captura de ' + $origen + '); solo corre la paralela; no hay alternancia de orden (spec 5.4 (4))')
    }
    else { Write-Registro ('orden de las patas: serial primero, paralelo segundo (sesgo de orden, spec 5.4)') }
    Write-Registro ('carpeta de capturas (el medidor no escribe en el repo): ' + $work)
    if (-not $ConReuso) { Write-Registro ('temporal de la pata serial:   ' + $tmpSerial) }
    Write-Registro ('temporal de la pata paralela: ' + $tmpParalelo + '  (tambien su -TempBase)')
    Write-Registro ''

    $rec = $null
    $c1 = $null
    $serial = $null
    $h0 = $null
    $h1 = $null
    if ($ConReuso) {
        # -- Modo de reuso: la pata serial es la captura de un par anterior (spec 5.4 (1) a (4), 9.6) --
        Write-Registro '[REUSO DE LA PATA SERIAL (Enmienda 1, D-T2; spec 5.4 y 9.6)]'
        Write-Registro ('  la pata serial NO corrio en esta medicion: es REUTILIZADA de la carpeta ' + $origen)
        Write-Registro ('  unica ruta que puede diferir entre las dos huellas finales: ' + $script:RutaExcluida + ' (no hay otra ni tolerancia)')
        $rec = Read-PataSerial -Carpeta $origen
        if (-not $rec.Ok) { Write-NoMedible $rec.Causa; return 2 }
        $j = $rec.Json
        Write-Registro ('  captura reutilizada: ' + $rec.SerialPath + ' (' + $j.serialBytes + ' bytes, sha256 ' + $j.serialSha256 + ')')
        Write-Registro ('  registro guardado: fecha ' + $j.fecha + '; raiz ' + $j.raiz + '; workers ' + $j.workers)
        Write-Registro ('  comando de la pata serial: ' + $j.serialComando)
        Write-Registro ('  wall serial guardado: ' + (Format-Seg $rec.WallSeg) + ' s (' + (Format-Hms $rec.WallSeg) + '); exit serial guardado: ' + $rec.Exit)
        Write-Registro ('  bash efectivo guardado: ' + $rec.Bash)
        Write-Registro ('  HEAD guardado: ' + $rec.Head + '; archivos en la lista final: ' + $j.archivosFinal + '; lista: ' + (Join-Path $origen $script:ArchivoLista) + ' (sha256 ' + $j.listaSha256 + ')')
        Write-Registro ('  huellas guardadas del primer par: inicial ' + $j.huellaInicial + '; entre las patas ' + $j.huellaEntre + '; final ' + $j.huellaFinal)
        Write-Registro '  [condiciones de la pata serial reutilizada, tomadas al medir el primer par]'
        foreach ($l in $rec.Condiciones) { Write-Registro ('  | ' + $l) }
        if (-not $rec.HuellasIguales) { Write-NoMedible 'las tres huellas del primer par no eran iguales: la captura serial no corresponde a la lista final guardada'; return 2 }
        if ($rec.Exit -ne 0) { Write-Registro ('  AVISO: la captura serial reutilizada salio con exit ' + $rec.Exit + ': no vale como compuerta del paso 10 (D-T3)') 'Yellow' }
        Write-Registro ''

        # La huella del arbol de cierre, antes de verificar nada (la primera de las tres).
        $h0 = Get-Huella -Raiz $raiz
        Write-Registro ('huella del arbol de cierre antes de verificar el reuso: ' + (Format-Huella $h0))
        if (-not $h0.Ok) { Write-NoMedible ('no se pudo calcular la huella del arbol de cierre: ' + $h0.Causa); return 2 }

        # (1) la lista, el HEAD y el status
        Write-Registro ('[reuso (1): el unico cambio es ' + $script:RutaExcluida + ', con el mismo HEAD y el mismo status]')
        $cmpL = Compare-Listas -Guardada $rec.Filas -Actual $h0.Filas -Excluida $script:RutaExcluida
        Write-Registro ('  HEAD guardado ' + $rec.Head + '; HEAD del arbol de cierre ' + $h0.Head + ': ' + $(if ($rec.Head -ceq $h0.Head) { 'IGUAL' } else { 'DISTINTO' }))
        Write-Registro ('  git status --porcelain --untracked-files=all: ' + $(if ($rec.Status -ceq $h0.Status) { 'IGUAL' } else { 'DISTINTO' }) +
                        ' (' + $h0.StatusLineas + ' lineas de status en el arbol de cierre)')
        Write-Registro ('  rutas que difieren entre la lista guardada (' + $rec.Filas.Count + ') y la del arbol de cierre (' + $h0.Filas.Count + '): ' + $cmpL.Cambios.Count)
        foreach ($x in $cmpL.Cambios) { Write-Registro ('    ' + $x) }
        Write-Registro ('  ' + $script:RutaExcluida + ' esta en las dos listas: ' + $(if ($cmpL.ExcluidaEnLasDos) { 'SI' } else { 'NO' }) + '; su contenido cambio: ' + $(if ($cmpL.ExcluidaCambio) { 'SI' } else { 'NO' }))
        $falla1 = New-Object System.Collections.Generic.List[string]
        if ($rec.Head -cne $h0.Head) { $falla1.Add('HEAD distinto') }
        if ($rec.Status -cne $h0.Status) { $falla1.Add('git status distinto') }
        if ($cmpL.Otros.Count -gt 0) { $falla1.Add('cambio otra cosa ademas de ' + $script:RutaExcluida + ': ' + (($cmpL.Otros | Select-Object -First 3) -join ' ; ')) }
        if (-not $cmpL.ExcluidaEnLasDos) { $falla1.Add($script:RutaExcluida + ' no esta en las dos listas') }
        if ($falla1.Count -gt 0) { Write-NoMedible ('condicion (1): ' + ($falla1 -join '; ')); return 2 }
        Write-Registro '  condicion (1): CUMPLE'
        Write-Registro ''

        # (2) las suites que leen el manifest, en el arbol de cierre, contra la captura reutilizada
        Write-Registro '[reuso (2): las suites que leen el manifest, re-verificadas en el arbol de cierre con Invoke-Tests.ps1 -SoloCaso]'
        $textoSerial = [System.IO.File]::ReadAllText($rec.SerialPath, $script:Utf8)
        $k = 0
        foreach ($suite in $script:SuitesDelReuso) {
            $k++
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($suite)
            $gS = Get-GrupoPy -Texto $textoSerial -Stem $stem
            if (-not $gS.Encontrada) { Write-NoMedible ('condicion (2): en la captura serial reutilizada, ' + $gS.Causa); return 2 }
            $tmpC = Join-Path $work ('tmp-cierre-' + $k)
            New-CarpetaVacia -Ruta $tmpC
            $argc = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + (Join-Path $PSScriptRoot 'Invoke-Tests.ps1') + '" -SoloCaso ' + $suite
            Write-Host ('(reuso (2): ' + $suite + ' en curso)') -ForegroundColor DarkGray
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $rc = Invoke-Corto -Exe $script:Powershell -Argumentos $argc -Cwd $raiz -TopeMs 1800000 -Entorno @{ TEMP = $tmpC; TMP = $tmpC; TMPDIR = $tmpC }
            $sw.Stop()
            if (-not $rc.Ok) { Write-NoMedible ('condicion (2): ' + $suite + ' no corrio: ' + $rc.Err); return 2 }
            [System.IO.File]::WriteAllText((Join-Path $work ('reuso-' + $suite + '.txt')), $rc.Out + $(if ($rc.Err) { "`r`n[stderr]`r`n" + $rc.Err } else { '' }), $script:Utf8)
            $gC = Get-GrupoPy -Texto $rc.Out -Stem $stem
            Write-Registro ('  ' + $suite + ': .\tests\Invoke-Tests.ps1 -SoloCaso ' + $suite + ' en ' + $tmpC + '; exit ' + $rc.Exit + '; ' + (Format-Seg $sw.Elapsed.TotalSeconds) + ' s')
            Write-Registro ('    captura serial reutilizada: [' + $gS.Linea + '] ok ' + $gS.Pasaron + ' de ' + $gS.Total)
            if (-not $gC.Encontrada) { Write-NoMedible ('condicion (2): en la corrida de cierre de ' + $suite + ', ' + $gC.Causa); return 2 }
            Write-Registro ('    arbol de cierre:            [' + $gC.Linea + '] ok ' + $gC.Pasaron + ' de ' + $gC.Total)
            if ($gS.Linea -cne $gC.Linea -or $gS.Pasaron -ne $gC.Pasaron -or $gS.Total -ne $gC.Total) {
                Write-NoMedible ('condicion (2): ' + $suite + ' no da lo mismo en el arbol de cierre que en la captura reutilizada'); return 2
            }
        }
        $hC1 = Get-Huella -Raiz $raiz
        Write-Registro ('huella del arbol de cierre despues de verificar el reuso: ' + (Format-Huella $hC1))
        if (-not $hC1.Ok -or $hC1.Huella -cne $h0.Huella) { Write-NoMedible 'condicion (2): la huella del arbol de cierre cambio durante la re-verificacion'; return 2 }
        Write-Registro '  condicion (2): CUMPLE (misma linea de grupo, mismos ok/total en las dos suites; huella igual antes y despues)'
        Write-Registro ''

        # La pata paralela se mide como siempre; estas son las variables que el resto del protocolo usa.
        $h1 = $hC1
        $c1 = [pscustomobject]@{ BashEfectivo = $rec.Bash; GitBashAlFrente = $rec.GitBashAlFrente; Elevado = $rec.Elevado }
        $serial = [pscustomobject]@{ WallSeg = $rec.WallSeg; Exit = $rec.Exit; RamMin = $rec.RamMin }
        $outSerial = $rec.SerialPath
        Write-Registro ('huella entre las patas (la del arbol de cierre, antes de la pata paralela): ' + (Format-Huella $h1))
    }
    else {
    # 1. condiciones y huella
    $h0 = Get-Huella -Raiz $raiz
    $c1 = Get-Condiciones -Etiqueta 'serial' -Raiz $raiz -TempDeLaPata $tmpSerial -Workers $Workers -Huella $h0
    foreach ($l in $c1.Lineas) { Write-Registro $l }
    Write-Registro ''

    # 2. la pata serial
    Write-Host '(pata serial en curso)' -ForegroundColor DarkGray
    $serial = Invoke-Pata -Nombre 'serial' -Script (Join-Path $PSScriptRoot 'Invoke-Tests.ps1') -ArgsDelScript @() `
        -Raiz $raiz -TempDir $tmpSerial -SalidaPath $outSerial -ErrPath $errSerial -ConProgreso $false
    Write-Pata -R $serial -Titulo 'pata serial: .\tests\Invoke-Tests.ps1'
    $procSerial = @(Get-ProcesosAtribuibles -Antes $c1.Procesos -Raiz $raiz -TempDir $tmpSerial)
    Write-Registro ('  python/powershell nuevos y vivos al terminar la pata: ' + $procSerial.Count)
    foreach ($l in $procSerial) { Write-Registro ('    ' + $l) }
    $nSerialTmp = @(Get-ChildItem -LiteralPath $tmpSerial -Force -ErrorAction SilentlyContinue).Count
    Write-Registro ('  entradas en el temporal de la pata serial: ' + $nSerialTmp + ' (de las suites y del oraculo, no de un runner: se registran y no rechazan el par)')
    Write-Registro ''

    # 3. huella; condiciones; la pata paralela; huella
    $h1 = Get-Huella -Raiz $raiz
    Write-Registro ('huella entre las patas: ' + (Format-Huella $h1))
    }
    $c2 = Get-Condiciones -Etiqueta 'paralela' -Raiz $raiz -TempDeLaPata $tmpParalelo -Workers $Workers -Huella $h1
    foreach ($l in $c2.Lineas) { Write-Registro $l }
    Write-Registro ''
    Write-Host '(pata paralela en curso)' -ForegroundColor DarkGray
    $paralelo = Invoke-Pata -Nombre 'paralelo' -Script (Join-Path $PSScriptRoot 'Invoke-Tests-Parallel.ps1') `
        -ArgsDelScript @('-Workers', [string]$Workers, '-TempBase', ('"' + $tmpParalelo + '"')) `
        -Raiz $raiz -TempDir $tmpParalelo -SalidaPath $outParalelo -ErrPath $errParalelo -ConProgreso $true
    Write-Pata -R $paralelo -Titulo ('pata paralela: .\tests\Invoke-Tests-Parallel.ps1 -Workers ' + $Workers + ' -TempBase <temporal de la pata>')
    $procParalelo = @(Get-ProcesosAtribuibles -Antes $c2.Procesos -Raiz $raiz -TempDir $tmpParalelo)
    $h2 = Get-Huella -Raiz $raiz
    Write-Registro ('  python/powershell nuevos y vivos al terminar la pata (posiblemente atribuibles a la corrida): ' + $procParalelo.Count)
    foreach ($l in $procParalelo) { Write-Registro ('    ' + $l) }
    Write-Registro ''
    Write-Registro ('huella final: ' + (Format-Huella $h2))
    Write-Registro ''

    # Las tres huellas
    $huellasOk = ($h0.Ok -and $h1.Ok -and $h2.Ok)
    $huellasIguales = ($huellasOk -and $h0.Huella -ceq $h1.Huella -and $h1.Huella -ceq $h2.Huella)
    if ($ConReuso) {
        Write-Registro '[huellas del arbol de cierre: antes de verificar el reuso, antes de la pata paralela y final]'
        Write-Registro ('  antes de verificar el reuso: ' + $(if ($h0.Ok) { $h0.Huella } else { 'NO_DISPONIBLE' }))
        Write-Registro ('  antes de la pata paralela (despues de verificar): ' + $(if ($h1.Ok) { $h1.Huella } else { 'NO_DISPONIBLE' }))
        Write-Registro ('  final (despues de la pata paralela): ' + $(if ($h2.Ok) { $h2.Huella } else { 'NO_DISPONIBLE' }))
        Write-Registro ('  las tres iguales entre si (antes y despues de la pata paralela): ' + $(if ($huellasIguales) { 'SI' } else { 'NO' }))
    }
    else {
        Write-Registro '[huellas: inicial, entre las patas y final]'
        Write-Registro ('  inicial: ' + $(if ($h0.Ok) { $h0.Huella } else { 'NO_DISPONIBLE' }))
        Write-Registro ('  entre las patas: ' + $(if ($h1.Ok) { $h1.Huella } else { 'NO_DISPONIBLE' }))
        Write-Registro ('  final: ' + $(if ($h2.Ok) { $h2.Huella } else { 'NO_DISPONIBLE' }))
        Write-Registro ('  las tres iguales: ' + $(if ($huellasIguales) { 'SI' } else { 'NO' }))
    }
    if (-not $huellasIguales) {
        $motivos.Add('HUELLA_DISTINTA: ' + $(if (-not $huellasOk) { 'una huella no se pudo calcular' } else { 'el arbol cambio entre las corridas (inicial/entre/final no coinciden)' }))
    }
    Write-Registro ''

    # Las huellas que se le pasan al comparador. Modo normal: la inicial y la final. Modo de reuso (spec 5.4 (3)):
    # para las dos patas, la huella calculada sin la ruta excluida: la serial, de la lista final guardada; la
    # paralela, de la lista del arbol de cierre despues de su pata.
    $hSerialCmp = $(if ($h0.Ok) { $h0.Huella } else { $null })
    $hParaleloCmp = $(if ($h2.Ok) { $h2.Huella } else { $null })
    if ($ConReuso) {
        $hSerialCmp = $null
        $hParaleloCmp = $null
        Write-Registro '[reuso (3): la pata serial es REUTILIZADA, y las huellas que ve el comparador son las calculadas SIN la ruta excluida]'
        Write-Registro ('  la pata serial no corrio en esta medicion: es la captura de ' + $origen + ' (sha256 ' + $rec.Json.serialSha256 + ')')
        Write-Registro ('  ruta excluida: ' + $script:RutaExcluida)
        Write-Registro ('  huella final de la captura reutilizada (completa):  ' + $rec.HuellaFinal)
        Write-Registro ('  huella final del arbol de cierre (completa):        ' + $(if ($h2.Ok) { $h2.Huella } else { 'NO_DISPONIBLE' }))
        if ($h2.Ok) {
            $hSerialCmp = Get-HuellaDeLista -Head $rec.Head -Status $rec.Status -Filas $rec.Filas -Excluir $script:RutaExcluida
            $hParaleloCmp = Get-HuellaDeLista -Head $h2.Head -Status $h2.Status -Filas $h2.Filas -Excluir $script:RutaExcluida
            Write-Registro ('  huella de la captura reutilizada, sin la ruta:      ' + $hSerialCmp)
            Write-Registro ('  huella del arbol de cierre, sin la ruta:            ' + $hParaleloCmp)
            $sinRutaIguales = ($hSerialCmp -ceq $hParaleloCmp)
            Write-Registro ('  iguales sin la ruta: ' + $(if ($sinRutaIguales) { 'SI' } else { 'NO' }))
            if (-not $sinRutaIguales) { $motivos.Add('REUSO_HUELLA_SIN_RUTA: las huellas sin ' + $script:RutaExcluida + ' de la captura reutilizada y del arbol de cierre difieren') }
        }
        else { Write-Registro '  huellas sin la ruta: NO_DISPONIBLE (la huella final del arbol de cierre no se pudo calcular)' }
        Write-Registro ''
    }
    else {
        # Modo normal: lo que el reuso de la pata serial va a necesitar (spec 9.6), en la carpeta de capturas.
        if ($h0.Ok -and $h1.Ok -and $h2.Ok) {
            Save-PataSerial -Carpeta $work -Raiz $raiz -Workers $Workers -H0 $h0 -H1 $h1 -H2 $h2 -Serial $serial -C1 $c1 -OutSerial $outSerial
            Write-Registro ('[registro de la pata serial para un reuso posterior: ' + $script:ArchivoSerial + ' y ' + $script:ArchivoLista + ' en ' + $work + ']')
            Write-Registro ''
        }
        else { Write-Registro ('[registro de la pata serial para un reuso posterior: NO se guardo, una huella no se pudo calcular]'); Write-Registro '' }
    }

    # 4. el comparador, sobre las dos salidas con la huella de cada pata. La pata serial es
    # (inicial -> entre) y la paralela (entre -> final): al comparador se le pasan la inicial y la
    # final, asi que si el arbol se movio en cualquier punto las huellas difieren y dice NO_COMPARABLE.
    Write-Registro '[comparador: Compare-TestRuns.ps1]'
    $veredicto = ''
    $cmpExit = -1
    $cmpLineas = @()
    if ($hSerialCmp -and $hParaleloCmp) {
        $argc = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + (Join-Path $PSScriptRoot 'Compare-TestRuns.ps1') + '"' +
                ' -Serial "' + $outSerial + '" -Paralelo "' + $outParalelo + '" -HuellaSerial ' + $hSerialCmp + ' -HuellaParalelo ' + $hParaleloCmp
        $cmp = Invoke-Corto -Exe $script:Powershell -Argumentos $argc -Cwd $raiz -TopeMs 600000
        if ($cmp.Ok) {
            $cmpExit = $cmp.Exit
            $cmpLineas = @(($cmp.Out -split "`r?`n") | Where-Object { $_.Length -gt 0 })
            if ($cmpLineas.Count -gt 0) { $veredicto = $cmpLineas[0].Trim() }
            [System.IO.File]::WriteAllText((Join-Path $work 'comparador.txt'), $cmp.Out + $(if ($cmp.Err) { "`r`n[stderr]`r`n" + $cmp.Err } else { '' }), $script:Utf8)
        }
        else { $cmpLineas = @('el comparador no corrio: ' + $cmp.Err) }
    }
    else { $cmpLineas = @('el comparador no corrio: una huella no esta disponible') }
    Write-Registro ('  huellas que se le pasan' + $(if ($ConReuso) { ' (sin ' + $script:RutaExcluida + ', pata serial reutilizada)' } else { '' }) + ': serial=' + $(if ($hSerialCmp) { $hSerialCmp } else { 'NO_DISPONIBLE' }) + ' paralelo=' + $(if ($hParaleloCmp) { $hParaleloCmp } else { 'NO_DISPONIBLE' }))
    Write-Registro ('  veredicto: ' + $(if ($veredicto) { $veredicto } else { '(ninguno)' }) + '; exit del comparador: ' + $cmpExit)
    foreach ($l in $cmpLineas) { Write-Registro ('  | ' + $l) }
    if (-not ($veredicto -ceq 'EQUIVALENTE' -and $cmpExit -eq 0)) {
        $motivos.Add('COMPARADOR: ' + $(if ($veredicto) { $veredicto } else { 'sin veredicto' }) + ' (exit ' + $cmpExit + ')')
    }
    Write-Registro ''

    # Duraciones por suite (B1)
    $duraciones = @()
    if ([System.IO.File]::Exists($outParalelo)) { $duraciones = @(Get-DuracionesDeSuite -SalidaPath $outParalelo -Raiz $raiz) }
    $noOk = @($duraciones | Where-Object { $_.Estado -ne 'OK' })
    $elegible = ($huellasIguales -and $paralelo.Exit -eq 0 -and $duraciones.Count -gt 0 -and $noOk.Count -eq 0 -and $veredicto -ceq 'EQUIVALENTE')
    Write-Registro '[duracion de cada suite: lineas de progreso del runner, spec 16.6; en orden canonico]'
    Write-Registro ('  alimentan maxSeconds (regla B1) solo si la corrida salio 0, ok == total, con la misma huella y condiciones tomadas antes: ' +
                    $(if ($elegible) { 'esta corrida cumple (exit 0, todas OK, huellas iguales, EQUIVALENTE)' } else { 'esta corrida NO cumple: no las uses para maxSeconds' }))
    if ($ConReuso) { Write-Registro '  par que cierra con la pata serial reutilizada: estas duraciones se registran y NO realimentan el manifest (regla B4)' }
    Write-Registro ('  suites con linea de progreso: ' + $duraciones.Count + '; no OK: ' + $noOk.Count)
    Write-Registro 'suite,segundos'
    foreach ($d in $duraciones) { Write-Registro ($d.Suite + ',' + (Format-Seg $d.Seg)) }
    Write-Registro ''
    Write-Registro '[llegada de cada linea de progreso, en segundos desde el inicio de la pata paralela; diagnostico (+/- 0,2 s), no decide nada]'
    Write-Registro 'orden,suite,estado,llegada_s,inicio_aproximado_s'
    $k = 0
    foreach ($a in $paralelo.Llegadas) {
        $k++
        Write-Registro ('' + $k + ',' + $a.Suite + ',' + $a.Estado + ',' + (Format-Seg $a.Llegada) + ',' + (Format-Seg ([math]::Max(0.0, $a.Llegada - $a.Seg))))
    }
    Write-Registro ''

    # Residuos atribuibles a la corrida paralela
    $res = Get-Residuos -TempBase $tmpParalelo
    $avisos = @()
    foreach ($ruta in @($outParalelo, $errParalelo)) {
        if ([System.IO.File]::Exists($ruta)) {
            $avisos += @(([System.IO.File]::ReadAllText($ruta, $script:Utf8) -split "`r?`n") | Where-Object { $_ -cmatch '^AVISO LIMPIEZA_INCOMPLETA' })
        }
    }
    Write-Registro '[residuos atribuibles a la corrida paralela (spec 22.1)]'
    Write-Registro ('  en el TempBase ' + $tmpParalelo + ': ' + $res.Items.Count + ' (raices hpp-*, s<nnn>, hpp-<id>.lock)')
    foreach ($i in $res.Items) { Write-Registro ('    RESIDUO ' + $i) 'Red' }
    Write-Registro ('  lineas que empiezan con AVISO LIMPIEZA_INCOMPLETA en su salida: ' + $avisos.Count)
    foreach ($a in $avisos) { Write-Registro ('    ' + $a) 'Red' }
    Write-Registro ('  otras entradas del TempBase (no cuentan): ' + $res.Otros.Count + $(if ($res.Otros.Count -gt 0) { ' -> ' + ($res.Otros -join ', ') } else { '' }))
    $nRes = $res.Items.Count + $avisos.Count
    Write-Registro ('  residuos atribuibles: ' + $nRes)
    if ($nRes -gt 0) {
        $quien = @($res.Items | Select-Object -First 3) + @($avisos | Select-Object -First 2)
        $motivos.Add('RESIDUOS: ' + $nRes + ' (' + ($quien -join ' ; ') + ')')
    }
    Write-Registro ''

    # B2: el mismo bash efectivo en las dos patas
    $mismoBash = ($c1.BashEfectivo -ceq $c2.BashEfectivo)
    $bashRunner = ''
    if ([System.IO.File]::Exists($outParalelo)) {
        $mb = [regex]::Match(([System.IO.File]::ReadAllText($outParalelo, $script:Utf8)), '(?m)^Invoke-Tests-Parallel: workers=\d+ TempBase=.*? bash=(.*?)\s*$')
        if ($mb.Success) { $bashRunner = $mb.Groups[1].Value }
    }
    Write-Registro '[bash efectivo en cada pata (regla B2)]'
    Write-Registro ('  serial' + $(if ($ConReuso) { ' (el guardado en la captura reutilizada)' } else { '' }) + ': ' + $c1.BashEfectivo)
    Write-Registro ('  paralela: ' + $c2.BashEfectivo + '; el que dijo ver el runner en su encabezado: ' + $(if ($bashRunner) { $bashRunner } else { '(no lo dijo)' }))
    Write-Registro ('  el mismo en las dos patas: ' + $(if ($mismoBash) { 'SI' } else { 'NO' }))
    if (-not $mismoBash) { $motivos.Add('BASH_DISTINTO: el bash efectivo difiere entre las patas (regla B2)') }
    if (-not $c1.GitBashAlFrente -or -not $c2.GitBashAlFrente) { Write-Registro '  ADVERTENCIA: Git Bash no esta al frente del PATH (spec 5.2): el par puede dar rojos falsos (t63c E-38).' 'Yellow' }
    if ($c1.Elevado -or $c2.Elevado) { Write-Registro '  ADVERTENCIA: el medidor corre elevado (spec 5.2 pide no elevado).' 'Yellow' }
    Write-Registro ''

    # RAM y relacion
    $minimos = @($serial.RamMin, $paralelo.RamMin) | Where-Object { $null -ne $_ }
    $ramMin = ($minimos | Measure-Object -Minimum).Minimum
    Write-Registro '[RAM libre]'
    Write-Registro ('  minima de todo el protocolo: ' + $ramMin + ' GB (serial ' + $serial.RamMin + ', paralela ' + $paralelo.RamMin + '); muestreo en el proceso del medidor, sin proceso aparte')
    Write-Registro ''
    Write-Registro '[relacion]'
    $relacion = $null
    if ($serial.WallSeg -gt 0) { $relacion = $paralelo.WallSeg / $serial.WallSeg }
    Write-Registro ('  wall serial' + $(if ($ConReuso) { ' (el de la captura reutilizada)' } else { '' }) + ': ' + (Format-Seg $serial.WallSeg) + ' s (' + (Format-Hms $serial.WallSeg) + '); wall paralelo: ' + (Format-Seg $paralelo.WallSeg) + ' s (' + (Format-Hms $paralelo.WallSeg) + ')')
    if ($null -ne $relacion) {
        Write-Registro ('  wall paralelo / wall serial = ' + $relacion.ToString('0.0000', $script:Inv) + ' (' + (100 * $relacion).ToString('0.0', $script:Inv) + ' %)')
    }
    if ($ConUmbral) {
        $cumple = ($null -ne $relacion -and $paralelo.WallSeg -le ($Umbral * $serial.WallSeg))
        Write-Registro ('  umbral ' + $Umbral.ToString($script:Inv) + ': wall paralelo <= umbral * wall serial (' + (Format-Seg ($Umbral * $serial.WallSeg)) + ' s): ' + $(if ($cumple) { 'SI' } else { 'NO' }))
        if (-not $cumple) { $motivos.Add('UMBRAL: la relacion ' + $(if ($null -ne $relacion) { $relacion.ToString('0.0000', $script:Inv) } else { '?' }) + ' supera ' + $Umbral.ToString($script:Inv)) }
    }
    else { Write-Registro '  sin -Umbral: no se exige relacion' }
    Write-Registro ''

    # Veredicto
    Write-Registro '[veredicto]'
    if ($serial.Exit -ne 0 -or $paralelo.Exit -ne 0) {
        Write-Registro ('  AVISO: exit serial=' + $serial.Exit + ' exit paralelo=' + $paralelo.Exit + ': un par equivalente en rojo no alimenta maxSeconds (B1) ni cierra 6.1') 'Yellow'
    }
    $acepta = ($motivos.Count -eq 0)
    if ($acepta) {
        if ($ConReuso) { Write-Registro ('PAR ACEPTADO (exit 0), con la pata serial REUTILIZADA de ' + $origen + ': condiciones (1) y (2) cumplidas, huellas iguales, EQUIVALENTE sin ' + $script:RutaExcluida + ', residuos atribuibles = 0') 'Green' }
        else { Write-Registro 'PAR ACEPTADO (exit 0): huellas iguales, EQUIVALENTE, residuos atribuibles = 0' 'Green' }
        return 0
    }
    foreach ($m in $motivos) { Write-Registro ('  motivo: ' + $m) 'Red' }
    Write-Registro 'PAR NO ACEPTADO (exit 1)' 'Red'
    return 1
}


function Save-Registro {
    if ($script:CarpetaDeCapturas -and [System.IO.Directory]::Exists($script:CarpetaDeCapturas)) {
        try { [System.IO.File]::WriteAllText((Join-Path $script:CarpetaDeCapturas 'registro.txt'), (($script:Registro -join "`r`n") + "`r`n"), $script:Utf8) } catch { }
    }
}


if ($MyInvocation.InvocationName -ne '.') {
    $ErrorActionPreference = 'Stop'
    try { [Console]::OutputEncoding = $script:Utf8 } catch { }
    $OutputEncoding = $script:Utf8
    $script:CarpetaDeCapturas = ''
    $script:NombresDeCapturas = ''
    $codigo = 2
    try {
        $codigo = [int](@(Invoke-Medicion -Workers $Workers -ConUmbral ($PSBoundParameters.ContainsKey('Umbral')) -Umbral $Umbral `
                -ConReuso ($PSBoundParameters.ContainsKey('ReusarSerialDe')) -ReusarDe $ReusarSerialDe)[-1])
    }
    catch {
        Write-Registro ('MEDICION_ABORTADA ' + $_.Exception.Message) 'Red'
        foreach ($p in ([string]$_.ScriptStackTrace -split "`r?`n")) { if ($p.Trim().Length -gt 0) { Write-Registro ('  ' + $p) 'Red' } }
        $codigo = 2
    }
    finally {
        if ($script:CarpetaDeCapturas) {
            $nombres = $script:NombresDeCapturas
            if (-not $nombres) { $nombres = 'serial.txt, serial.err.txt, paralelo.txt, paralelo.err.txt, comparador.txt, registro.txt' }
            $script:Registro.Add('capturas: ' + $script:CarpetaDeCapturas + ' (' + $nombres + ')')
            Write-Host ('capturas: ' + $script:CarpetaDeCapturas + ' (' + $nombres + ')')
            Save-Registro
        }
    }
    exit $codigo
}
