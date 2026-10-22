<#
.SYNOPSIS
    Corre los tests del harness en paralelo: un proceso por archivo de tests\casos\.

.DESCRIPTION
    Es un acelerador, no la compuerta (ADR-0018): la compuerta sigue siendo
    .\tests\Invoke-Tests.ps1 sin parametros. Cada suite corre como
    Invoke-Tests.ps1 -SoloCaso <archivo> en su propio powershell.exe, con TEMP/TMP/TMPDIR
    propios; el runner junta los resultados y reproduce el reporte del oraculo en orden
    canonico.

    Sale 0 si pasa todo, 1 si algo fallo o hubo un error de infraestructura, y 2 si no corrio
    porque otro runner tiene el candado pesada.lock (o no se pudo leer).

    Los parametros son estos cinco y ninguno mas: no hay modo de prueba ni variables propias.

.PARAMETER Workers
    Suites vivas a la vez, de 1 a 4. Por defecto 2.

.PARAMETER Detallado
    Se lo pasa a cada worker, como al oraculo.

.PARAMETER TempBase
    Donde nace la raiz de la corrida (hpp-<id>). Por defecto $env:TEMP, tal cual.

.PARAMETER LockPath
    El candado que excluye a un runner de otro. Por defecto
    %LOCALAPPDATA%\gcba-harness\recursos\pesada.lock.

.PARAMETER CancelFile
    Si el archivo aparece, la corrida se cancela por el mismo camino que Ctrl-C.

.EXAMPLE
    .\tests\Invoke-Tests-Parallel.ps1
    .\tests\Invoke-Tests-Parallel.ps1 -Workers 3 -Detallado
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [int] $Workers = 2,

    [switch] $Detallado,

    [string] $TempBase = $env:TEMP,

    [string] $LockPath = "$env:LOCALAPPDATA\gcba-harness\recursos\pesada.lock",

    [string] $CancelFile
)

# Este archivo solo define funciones hasta la guarda del final: cargarlo con dot-source no corre
# nada (spec 16.7). La costura de testabilidad del agregador es Get-ReporteDeCorrida.

$script:SeparadorPy  = '── python tests/correr.py ──────────────────────────────────────────'
$script:SeparadorFin = '══════════════════════════════════════════════════════════════════'
$script:MarcaSinResumen = 'No se pudo leer el resumen de python tests/correr.py.'
$script:PuntoMedio = [string][char]0x00B7


# ── Registros por suite (spec 15.1) ─────────────────────────────────────────────

function New-RegistroDeSuite {
    param([string] $Suite, [string] $Engine, [int] $Index)
    return [pscustomobject]@{
        suite          = $Suite
        engine         = $Engine
        index          = $Index
        state          = 'PENDIENTE'
        exitCode       = $null
        reported       = $false
        forma          = $null        # 'verde' | 'roja': la forma de la linea final
        nFallaron      = $null        # el N de 'N fallaron.' cuando la forma es roja
        sinResumen     = $false       # la marca de resumen ausente (Invoke-Tests.ps1)
        ok             = 0
        total          = 0
        groups         = @()          # { name, n, malos, detalle[] }
        failedRows     = @()          # { grupo, nombre, detalle }
        failedLines    = @()          # las lineas de Fallos: tal cual (PS)
        pyRowLines     = @()          # las lineas de filas tal cual (Py)
        rows           = @()          # solo con -Detallado: { grupo, nombre, ok }
        infra          = $null        # { motivo, detalle } o el motivo solo
        timeoutSeconds = $null
        stdoutPath     = $null
        stderrPath     = $null
        stderrTexto    = ''
        seconds        = 0.0
        inicio         = $null
        fin            = $null
    }
}


function ConvertTo-InfraNormal {
    param($Infra)
    if ($null -eq $Infra) { return $null }
    if ($Infra -is [string]) { return [pscustomobject]@{ motivo = $Infra; detalle = '' } }
    return [pscustomobject]@{ motivo = [string]$Infra.motivo; detalle = [string]$Infra.detalle }
}


function Format-LineaInfra {
    <# INFRA <MOTIVO> <suite> [detalle]: si el detalle ya arranca con el nombre de la suite no se repite. #>
    param($Infra, [string] $Suite)
    $d = [string]$Infra.detalle
    if ($d.Length -eq 0) { $d = $Suite }
    elseif (-not $d.StartsWith($Suite)) { $d = $Suite + ' ' + $d }
    return ('INFRA ' + $Infra.motivo + ' ' + $d).TrimEnd()
}


function Test-EsEntero {
    param($Valor)
    return ($Valor -is [int] -or $Valor -is [long])
}


function Get-InfraDeSuite {
    <#
    .SYNOPSIS
        El motivo de infraestructura de un registro, derivado de sus campos (o $null).
    .DESCRIPTION
        Lo usan el parser, para el progreso, y el agregador, que no se fia de lo que el
        parser haya dejado: la regla vive en un solo lugar. Los motivos son los cerrados de
        la spec 17.
    #>
    param($R)

    $suite = [string]$R.suite
    switch ([string]$R.state) {
        'MATADA_TIMEOUT'     { return [pscustomobject]@{ motivo = 'TIMEOUT'; detalle = ("$suite $($R.timeoutSeconds) s") } }
        'MATADA_CANCELACION' { return [pscustomobject]@{ motivo = 'CANCELADA'; detalle = $suite } }
        'MUERTA'             { return [pscustomobject]@{ motivo = 'WORKER_MUERTO'; detalle = $suite } }
        'SIN_LANZAR'         { return [pscustomobject]@{ motivo = 'ERROR_INTERNO'; detalle = "$suite no se lanzo" } }
        'TERMINADA'          { }
        default              { return [pscustomobject]@{ motivo = 'ERROR_INTERNO'; detalle = "$suite estado desconocido <$($R.state)>" } }
    }

    if ($R.sinResumen -or -not $R.reported) {
        return [pscustomobject]@{ motivo = 'SIN_RESUMEN'; detalle = $suite }
    }

    $ok = $R.ok
    $total = $R.total
    if (-not (Test-EsEntero $ok) -or -not (Test-EsEntero $total)) {
        throw "el registro de $suite no tiene ok/total validos (ok=<$ok> total=<$total>)"
    }

    $grupos = @($R.groups | Where-Object { $null -ne $_ })

    if ([string]$R.engine -ceq 'py') {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($suite)
        $ajenos = @($grupos | Where-Object { [string]$_.name -cne $stem } | ForEach-Object { [string]$_.name })
        if ($ajenos.Count -gt 0) {
            return [pscustomobject]@{ motivo = 'GRUPO_AJENO'; detalle = ("$suite grupo=" + ($ajenos -join ',')) }
        }
    }

    $exit = $R.exitCode
    $forma = [string]$R.forma
    if (($exit -eq 0 -and $forma -ceq 'roja') -or ($exit -ne 0 -and $forma -ceq 'verde')) {
        return [pscustomobject]@{ motivo = 'EXIT_INCOHERENTE'; detalle = "$suite exit=$exit forma=$forma" }
    }

    $suma = 0
    foreach ($g in $grupos) { $suma += [long]$g.n }
    if ($suma -ne $total) {
        return [pscustomobject]@{ motivo = 'RESUMEN_INCOHERENTE'; detalle = "$suite grupos=$suma total=$total" }
    }
    if ($ok -gt $total) {
        return [pscustomobject]@{ motivo = 'RESUMEN_INCOHERENTE'; detalle = "$suite ok=$ok total=$total" }
    }
    if ($forma -ceq 'verde' -and $ok -ne $total) {
        return [pscustomobject]@{ motivo = 'RESUMEN_INCOHERENTE'; detalle = "$suite ok=$ok total=$total forma=verde" }
    }
    if ($forma -ceq 'roja' -and $null -ne $R.nFallaron -and ([long]$R.nFallaron -ne ($total - $ok))) {
        return [pscustomobject]@{ motivo = 'RESUMEN_INCOHERENTE'; detalle = "$suite fallaron=$($R.nFallaron) esperado=$($total - $ok)" }
    }
    return $null
}


# ── El parser de la salida de un worker (spec 15.2) ─────────────────────────────

function ConvertFrom-SalidaDeWorker {
    <#
    .SYNOPSIS
        De la salida de un worker a los campos del registro. No decide nada: el oraculo ya decidio.
    .DESCRIPTION
        La linea final es la ultima no vacia y tiene que tener la forma exacta. Las lineas de
        grupo y de fallos se leen con el motor de la suite (ps o py). Un texto que no se puede
        leer deja los campos vacios, y el cruce con el total lo delata despues.
    #>
    param(
        [string] $Texto,
        [string] $Stderr,
        [string] $Engine,
        [bool] $Detallado
    )

    $r = [ordered]@{
        reported = $false; forma = $null; ok = 0; total = 0; nFallaron = $null
        sinResumen = $false; propio = $false
        groups = @(); failedRows = @(); failedLines = @(); pyRowLines = @(); rows = @()
    }

    $lineas = @($Texto -split "`r?`n")
    $ultima = $null
    for ($i = $lineas.Count - 1; $i -ge 0; $i--) {
        if ($lineas[$i].Trim().Length -gt 0) { $ultima = $lineas[$i]; break }
    }

    try {
        if ($null -ne $ultima -and $ultima -cmatch '^([0-9]+)/([0-9]+) pasaron\.$') {
            $r.reported = $true; $r.forma = 'verde'
            $r.ok = [long]$Matches[1]; $r.total = [long]$Matches[2]
        }
        elseif ($null -ne $ultima -and $ultima -cmatch '^([0-9]+)/([0-9]+) pasaron\. ([0-9]+) fallaron\.$') {
            $r.reported = $true; $r.forma = 'roja'
            $r.ok = [long]$Matches[1]; $r.total = [long]$Matches[2]; $r.nFallaron = [long]$Matches[3]
        }
    } catch { $r.reported = $false }

    $r.sinResumen = $Texto.Contains($script:MarcaSinResumen)
    $r.propio = ($Texto.Contains('No existe tests\casos\') -or $Texto.Contains('No hay casos en tests\casos\.') -or
                 $Texto.Contains('No se encontró un intérprete de Python'))

    $grupos = New-Object System.Collections.Generic.List[object]
    $reGrupoOk = '^  OK    (.+)  \(([0-9]+)\)$'

    try {
        if ($Engine -ceq 'ps') {
            $iCab = -1; $iSum = -1
            for ($i = 0; $i -lt $lineas.Count; $i++) {
                if ($iCab -lt 0 -and $lineas[$i] -ceq 'gcba-harness - tests') { $iCab = $i }
            }
            for ($i = $lineas.Count - 1; $i -gt $iCab -and $iCab -ge 0; $i--) {
                if ($lineas[$i] -cmatch '^[0-9]+/[0-9]+ pasaron \(PowerShell\)\.( [0-9]+ fallaron\.)?$') { $iSum = $i; break }
            }
            if ($iCab -ge 0 -and $iSum -gt $iCab) {
                $actual = $null
                $enFallos = $false
                $fallos = New-Object System.Collections.Generic.List[string]
                $reFila = '^ {8}' + [regex]::Escape($script:PuntoMedio) + ' (.*)$'
                for ($i = $iCab + 1; $i -lt $iSum; $i++) {
                    $l = $lineas[$i]
                    if ($enFallos) { $fallos.Add($l); continue }
                    if ($l -ceq 'Fallos:') { $enFallos = $true; continue }
                    if ($l -cmatch $reGrupoOk) {
                        $actual = [pscustomobject]@{ name = $Matches[1]; n = [long]$Matches[2]; malos = 0; detalle = @() }
                        $grupos.Add($actual); continue
                    }
                    if ($l -cmatch '^  FALLA (.+)  \(([0-9]+)/([0-9]+)\)$') {
                        $actual = [pscustomobject]@{ name = $Matches[1]; n = [long]$Matches[3]; malos = [long]$Matches[2]; detalle = @() }
                        $grupos.Add($actual); continue
                    }
                    if ($null -ne $actual -and $l -cmatch $reFila) { $actual.detalle += $l; continue }
                }
                if ($fallos.Count -gt 0 -and $fallos[$fallos.Count - 1].Trim().Length -eq 0) { $fallos.RemoveAt($fallos.Count - 1) }
                $r.failedLines = @($fallos)
                $filas = New-Object System.Collections.Generic.List[object]
                $cur = $null
                foreach ($l in $fallos) {
                    if ($l -cmatch '^  \[(.+?)\] (.*)$') {
                        $cur = [pscustomobject]@{ grupo = $Matches[1]; nombre = $Matches[2]; detalle = '' }
                        $filas.Add($cur)
                    }
                    elseif ($null -ne $cur) {
                        $d = $l
                        if ($l.StartsWith('      ')) { $d = $l.Substring(6) }
                        if ($cur.detalle.Length -gt 0) { $cur.detalle = $cur.detalle + "`n" + $d } else { $cur.detalle = $d }
                    }
                }
                $r.failedRows = $filas.ToArray()
            }
        }
        else {
            $iMarca = -1
            for ($i = 0; $i -lt $lineas.Count; $i++) {
                if ($lineas[$i].StartsWith('── python tests/correr.py')) { $iMarca = $i; break }
            }
            if ($iMarca -ge 0) {
                $iFin = $lineas.Count
                for ($i = $iMarca + 1; $i -lt $lineas.Count; $i++) {
                    if ($lineas[$i].StartsWith('═')) { $iFin = $i; break }
                }
                $iCab = -1; $iSum = -1
                for ($i = $iMarca + 1; $i -lt $iFin; $i++) {
                    if ($iCab -lt 0 -and $lineas[$i] -ceq 'gcba-harness - tests (python)') { $iCab = $i }
                }
                for ($i = $iFin - 1; $i -gt $iCab -and $iCab -ge 0; $i--) {
                    if ($lineas[$i] -cmatch '^[0-9]+/[0-9]+ pasaron\.$') { $iSum = $i; break }
                }
                if ($iCab -ge 0 -and $iSum -gt $iCab) {
                    $enFilas = $false
                    $filasCrudas = New-Object System.Collections.Generic.List[string]
                    for ($i = $iCab + 1; $i -lt $iSum; $i++) {
                        $l = $lineas[$i]
                        if (-not $enFilas) {
                            if ($l -cmatch $reGrupoOk) {
                                $grupos.Add([pscustomobject]@{ name = $Matches[1]; n = [long]$Matches[2]; malos = 0; detalle = @() }); continue
                            }
                            if ($l -cmatch '^  FALLA (.+)  \(([0-9]+)\)$') {
                                $grupos.Add([pscustomobject]@{ name = $Matches[1]; n = [long]$Matches[2]; malos = 0; detalle = @() }); continue
                            }
                            if ($l -cmatch '^    (ok |MAL) ') { $enFilas = $true; $filasCrudas.Add($l) }
                        }
                        else { $filasCrudas.Add($l) }
                    }
                    if ($filasCrudas.Count -gt 0 -and $filasCrudas[$filasCrudas.Count - 1].Trim().Length -eq 0) {
                        $filasCrudas.RemoveAt($filasCrudas.Count - 1)
                    }
                    $r.pyRowLines = @($filasCrudas)
                    $filas = New-Object System.Collections.Generic.List[object]
                    $todas = New-Object System.Collections.Generic.List[object]
                    $cur = $null
                    foreach ($l in $filasCrudas) {
                        if ($l -cmatch '^    (ok |MAL) (.+?) / (.*)$') {
                            $esOk = ($Matches[1] -ceq 'ok ')
                            $resto = $Matches[3]
                            if ($esOk -and $resto.EndsWith(' ')) { $resto = $resto.Substring(0, $resto.Length - 1) }
                            # Una fila MAL no separa nombre y detalle sin ambiguedad (correr.py:91): el
                            # texto entero queda en nombre y el comparador corta donde corresponde.
                            $cur = [pscustomobject]@{ grupo = $Matches[2]; nombre = $resto; detalle = ''; ok = $esOk }
                            $todas.Add($cur)
                            if (-not $esOk) { $filas.Add($cur) }
                        }
                    }
                    foreach ($g in $grupos) {
                        $g.malos = @($filas | Where-Object { $_.grupo -ceq $g.name }).Count
                    }
                    $r.failedRows = @($filas | ForEach-Object { [pscustomobject]@{ grupo = $_.grupo; nombre = $_.nombre; detalle = '' } })
                    if ($Detallado) {
                        $r.rows = @($todas | ForEach-Object { [pscustomobject]@{ grupo = $_.grupo; nombre = $_.nombre; ok = $_.ok } })
                    }
                }
            }
        }
    } catch {
        $grupos.Clear()
    }
    $r.groups = $grupos.ToArray()

    if ($Engine -ceq 'ps' -and $Detallado) {
        # NB-09: las filas PS de -Detallado no dicen ok o falla: lo que falto se deduce de Fallos:.
        $pendientes = New-Object System.Collections.Generic.List[object]
        foreach ($f in $r.failedRows) { $pendientes.Add($f) }
        $rows = New-Object System.Collections.Generic.List[object]
        foreach ($g in $grupos) {
            foreach ($l in $g.detalle) {
                $nombre = $l.Substring(10)
                $esOk = $true
                for ($k = 0; $k -lt $pendientes.Count; $k++) {
                    if ($pendientes[$k].grupo -ieq $g.name -and $pendientes[$k].nombre -ceq $nombre) {
                        $esOk = $false; $pendientes.RemoveAt($k); break
                    }
                }
                $rows.Add([pscustomobject]@{ grupo = $g.name; nombre = $nombre; ok = $esOk })
            }
        }
        $r.rows = $rows.ToArray()
    }
    return [pscustomobject]$r
}


# ── El manifest: validacion de forma (spec 10.3a) ───────────────────────────────

function Read-ManifestParalelo {
    <#
    .SYNOPSIS
        Lee el manifest y valida SOLO la forma que hace falta para correr con seguridad.
    .DESCRIPTION
        No mira la cobertura de tests\casos\, ni que los archivos existan, ni la formula de
        timeoutSeconds, ni el texto de reason: eso es politica del manifest real y lo valida la
        suite (spec 10.3b). Un manifest que no pasa esto no deja correr nada.
    #>
    param([string] $Ruta)

    $falla = { param($causa) return [pscustomobject]@{ Ok = $false; Causa = $causa; Entradas = @() } }

    if (-not [System.IO.File]::Exists($Ruta)) { return (& $falla "no existe $Ruta") }
    $obj = $null
    try {
        $texto = [System.IO.File]::ReadAllText($Ruta, (New-Object System.Text.UTF8Encoding $false))
        $obj = $texto | ConvertFrom-Json -ErrorAction Stop
    } catch {
        return (& $falla ("no es JSON legible: " + $_.Exception.Message))
    }
    if ($null -eq $obj -or $obj -isnot [System.Management.Automation.PSCustomObject]) { return (& $falla 'la raiz no es un objeto JSON') }
    $props = @($obj.PSObject.Properties.Name)
    if ($props -cnotcontains 'schema') { return (& $falla 'falta schema') }
    if ($obj.schema -isnot [string] -or $obj.schema -cne 'parallel-manifest/1') { return (& $falla ("schema distinto de parallel-manifest/1: <$($obj.schema)>")) }
    if ($props -cnotcontains 'suites') { return (& $falla 'falta suites') }
    if ($obj.suites -isnot [System.Array]) { return (& $falla 'suites no es una lista') }

    $vistos = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $entradas = New-Object System.Collections.Generic.List[object]
    $i = 0
    foreach ($e in $obj.suites) {
        $i++
        $donde = "entrada $i"
        if ($e -isnot [System.Management.Automation.PSCustomObject]) { return (& $falla "$donde no es un objeto") }
        $ep = @($e.PSObject.Properties.Name)
        foreach ($campo in 'suite', 'class', 'lane', 'maxSeconds', 'timeoutSeconds', 'reason') {
            if ($ep -cnotcontains $campo) { return (& $falla "$donde falta $campo") }
        }
        if ($e.suite -isnot [string] -or $e.suite.Trim().Length -eq 0) { return (& $falla "$donde suite no es un texto no vacio") }
        $donde = "entrada $i ($($e.suite))"
        if (-not $vistos.Add($e.suite)) { return (& $falla "$donde suite repetido") }
        if ($e.class -isnot [string] -or @('parallel', 'lane', 'serial') -cnotcontains $e.class) { return (& $falla "$donde class desconocida <$($e.class)>") }
        if ($e.class -ceq 'lane') {
            if ($e.lane -isnot [string] -or $e.lane.Trim().Length -eq 0) { return (& $falla "$donde lane tiene que ser un nombre cuando class es lane") }
        }
        elseif ($null -ne $e.lane) { return (& $falla "$donde lane tiene que ser null cuando class no es lane") }

        $max = $null
        if ($null -ne $e.maxSeconds) {
            if (-not ($e.maxSeconds -is [int] -or $e.maxSeconds -is [long] -or $e.maxSeconds -is [double] -or $e.maxSeconds -is [decimal])) {
                return (& $falla "$donde maxSeconds no es un numero")
            }
            $max = [double]$e.maxSeconds
            if ([double]::IsNaN($max) -or $max -le 0) { return (& $falla "$donde maxSeconds tiene que ser mayor que 0") }
        }
        $to = $null
        if ($null -ne $e.timeoutSeconds) {
            $v = $e.timeoutSeconds
            if (-not ($v -is [int] -or $v -is [long] -or $v -is [double] -or $v -is [decimal])) {
                return (& $falla "$donde timeoutSeconds no es un numero")
            }
            $d = [decimal]$v
            if ($d -ne [math]::Floor($d)) { return (& $falla "$donde timeoutSeconds tiene que ser entero (recibi $v)") }
            if ($d -le 0) { return (& $falla "$donde timeoutSeconds tiene que ser mayor que 0 (recibi $v)") }
            $to = [long]$d
        }
        if ($e.reason -isnot [string]) { return (& $falla "$donde reason no es un texto") }

        $entradas.Add([pscustomobject]@{
            suite = [string]$e.suite; clase = [string]$e.class; lane = $e.lane
            maxSeconds = $max; timeoutSeconds = $to; reason = [string]$e.reason
        })
    }
    return [pscustomobject]@{ Ok = $true; Causa = ''; Entradas = $entradas.ToArray() }
}


# ── Candados del SO (spec 19) ───────────────────────────────────────────────────

function Open-Candado {
    <#
    .SYNOPSIS
        Intenta tomar un candado sobre un archivo estable, sin esperar.
    .DESCRIPTION
        FileStream.Lock(0, 1) sobre el archivo: lo dice el sistema operativo y se libera solo
        si el proceso muere. Nunca un pid, una fecha ni que el archivo exista. Devuelve
        Estado = tomado | ocupado | ilegible.
    #>
    param([string] $Ruta, [switch] $CrearPadre, [switch] $SoloSiExiste)

    $fs = $null
    try {
        if ($CrearPadre) {
            $padre = [System.IO.Path]::GetDirectoryName($Ruta)
            if ($padre -and -not [System.IO.Directory]::Exists($padre)) { [void][System.IO.Directory]::CreateDirectory($padre) }
        }
        $modo = [System.IO.FileMode]::OpenOrCreate
        if ($SoloSiExiste) { $modo = [System.IO.FileMode]::Open }
        $fs = [System.IO.File]::Open($Ruta, $modo, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::ReadWrite)
    } catch {
        return [pscustomobject]@{ Estado = 'ilegible'; Stream = $null; Causa = $_.Exception.Message }
    }
    try {
        $fs.Lock(0, 1)
    }
    catch [System.IO.IOException] {
        $fs.Dispose()
        return [pscustomobject]@{ Estado = 'ocupado'; Stream = $null; Causa = '' }
    }
    catch {
        $fs.Dispose()
        return [pscustomobject]@{ Estado = 'ilegible'; Stream = $null; Causa = $_.Exception.Message }
    }
    return [pscustomobject]@{ Estado = 'tomado'; Stream = $fs; Causa = '' }
}


function Get-RutaDeInfoDelCandado {
    param([string] $LockPath)
    return [System.IO.Path]::ChangeExtension($LockPath, '.json')
}


function Read-InfoDelCandado {
    <# pesada.json es informativo: nunca decide quien es el dueno. #>
    param([string] $LockPath)
    $info = [pscustomobject]@{ Desde = '(desconocida)'; Pid = 0 }
    try {
        $j = [System.IO.File]::ReadAllText((Get-RutaDeInfoDelCandado $LockPath)) | ConvertFrom-Json
        if ($j.desde) { $info.Desde = [string]$j.desde }
        if ($j.pid -is [int] -or $j.pid -is [long]) { $info.Pid = [long]$j.pid }
    } catch { }
    return $info
}


function Write-InfoDelCandado {
    param([string] $LockPath, [string] $Raiz, [int] $Workers)
    try {
        $ruta = Get-RutaDeInfoDelCandado $LockPath
        $tmp = $ruta + '.' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.tmp'
        $json = ConvertTo-Json -Compress -InputObject ([ordered]@{
            pid = $PID; desde = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'); raiz = $Raiz; workers = $Workers })
        [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding $false))
        if ([System.IO.File]::Exists($ruta)) { [System.IO.File]::Replace($tmp, $ruta, [NullString]::Value) } else { [System.IO.File]::Move($tmp, $ruta) }
    } catch { }
}


# ── Borrado seguro (spec 19.4) ──────────────────────────────────────────────────

function Remove-ArbolRec {
    param([System.IO.DirectoryInfo] $Dir, $Fallos)
    $antes = $Fallos.Count
    $hijos = $null
    try { $hijos = $Dir.GetFileSystemInfos() } catch { $Fallos.Add($Dir.FullName); return }
    foreach ($h in $hijos) {
        $esEnlace = (($h.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
        if ($h -is [System.IO.DirectoryInfo]) {
            if ($esEnlace) {
                # Un junction o un symlink de carpeta se quita a si mismo: nunca se entra.
                try { [System.IO.Directory]::Delete($h.FullName) } catch { $Fallos.Add($h.FullName) }
            }
            else { Remove-ArbolRec -Dir $h -Fallos $Fallos }
        }
        else {
            try {
                if (($h.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0) { $h.Attributes = [System.IO.FileAttributes]::Normal }
                $h.Delete()
            } catch { $Fallos.Add($h.FullName) }
        }
    }
    try { $Dir.Delete() } catch { if ($Fallos.Count -eq $antes) { $Fallos.Add($Dir.FullName) } }
}


function Remove-ArbolSeguro {
    <# Borra un arbol sin seguir reparse points. Devuelve las rutas que no se pudieron borrar. #>
    param([string] $Ruta)
    $fallos = New-Object System.Collections.Generic.List[string]
    $d = New-Object System.IO.DirectoryInfo $Ruta
    if (-not $d.Exists) { return }
    Remove-ArbolRec -Dir $d -Fallos $fallos
    return @($fallos)
}


function Test-RaizBorrable {
    <# Solo se borra algo llamado hpp-<8 hex>, hijo directo del TempBase y que no sea un enlace. #>
    param([string] $TempBase, [string] $Ruta)
    $base = $TempBase.TrimEnd('\', '/')
    $padre = [System.IO.Path]::GetDirectoryName($Ruta.TrimEnd('\', '/'))
    $hoja = [System.IO.Path]::GetFileName($Ruta.TrimEnd('\', '/'))
    if ($hoja -cnotmatch '^hpp-[0-9a-f]{8}$') { return $false }
    if ($null -eq $padre -or -not $padre.Equals($base, [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
    $d = New-Object System.IO.DirectoryInfo $Ruta
    if ($d.Exists -and (($d.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) { return $false }
    return $true
}


function Remove-RaizDeCorrida {
    param([string] $TempBase, [string] $Ruta)
    if (-not (Test-RaizBorrable -TempBase $TempBase -Ruta $Ruta)) {
        return "$Ruta (no se borra: no es una raiz hpp-<id> del TempBase)"
    }
    return (Remove-ArbolSeguro -Ruta $Ruta)
}


function Invoke-BarridoDeRaices {
    <#
    .SYNOPSIS
        Barre las raices hpp-* de corridas muertas, con el mismo mecanismo del candado.
    .DESCRIPTION
        Un hpp-<id>.lock que se puede tomar es de un dueno muerto: se borra su carpeta y despues
        el .lock. Uno que no se puede tomar vive, y no se toca. Una carpeta sin su .lock no se
        toca y se avisa.
    #>
    param([string] $TempBase, $Avisos)

    $base = $TempBase.TrimEnd('\', '/')
    if (-not [System.IO.Directory]::Exists($base)) { return }

    foreach ($f in @(Get-ChildItem -LiteralPath $base -File -Filter 'hpp-*.lock' -ErrorAction SilentlyContinue)) {
        if ($f.Name -cnotmatch '^hpp-([0-9a-f]{8})\.lock$') { continue }
        $id = $Matches[1]
        $carpeta = $base + '\hpp-' + $id
        $c = Open-Candado -Ruta $f.FullName -SoloSiExiste
        if ($c.Estado -ne 'tomado') { continue }
        $quedaron = @()
        if ([System.IO.Directory]::Exists($carpeta)) { $quedaron = @(Remove-RaizDeCorrida -TempBase $base -Ruta $carpeta) }
        $c.Stream.Dispose()
        if ($quedaron.Count -eq 0) {
            try { [System.IO.File]::Delete($f.FullName) } catch { }
        }
        else {
            $Avisos.Add('AVISO LIMPIEZA_INCOMPLETA ' + $quedaron[0])
        }
    }

    foreach ($d in @(Get-ChildItem -LiteralPath $base -Directory -Filter 'hpp-*' -ErrorAction SilentlyContinue)) {
        if ($d.Name -cnotmatch '^hpp-[0-9a-f]{8}$') { continue }
        if (-not [System.IO.File]::Exists($base + '\' + $d.Name + '.lock')) {
            $Avisos.Add('AVISO LIMPIEZA_INCOMPLETA ' + $d.FullName + ' (raiz sin su .lock: no se toca)')
        }
    }
}


function New-RaizDeCorrida {
    <# Primero el hpp-<id>.lock, tomado; despues la carpeta hpp-<id>\ (spec 19.4). #>
    param([string] $TempBase)
    $base = $TempBase.TrimEnd('\', '/')
    if (-not [System.IO.Directory]::Exists($base)) { [void][System.IO.Directory]::CreateDirectory($base) }
    for ($intento = 0; $intento -lt 20; $intento++) {
        $id = [guid]::NewGuid().ToString('N').Substring(0, 8)
        $lock = $base + '\hpp-' + $id + '.lock'
        $dir = $base + '\hpp-' + $id
        if ([System.IO.File]::Exists($lock) -or [System.IO.Directory]::Exists($dir)) { continue }
        $fs = [System.IO.File]::Open($lock, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::ReadWrite)
        $fs.Lock(0, 1)
        [void][System.IO.Directory]::CreateDirectory($dir)
        [void][System.IO.Directory]::CreateDirectory($dir + '\logs')
        return [pscustomobject]@{ Id = $id; Dir = $dir; Lock = $lock; Stream = $fs; Logs = ($dir + '\logs'); Borrada = $false; TempBase = $base }
    }
    throw 'no se pudo elegir un id de corrida libre'
}


function Close-RaizDeCorrida {
    <# Libera el sidecar y, si la raiz quedo limpia (se borro), tambien lo borra (spec 19.5). #>
    param($Raiz)
    if ($null -eq $Raiz) { return }
    try { if ($null -ne $Raiz.Stream) { $Raiz.Stream.Dispose() } } catch { }
    if ($Raiz.Borrada) {
        try { [System.IO.File]::Delete($Raiz.Lock) } catch { }
    }
}


# ── La huella del arbol (spec 5.1) ──────────────────────────────────────────────

function Invoke-GitTexto {
    param([string] $Raiz, [string[]] $Argumentos)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'git'
    $psi.Arguments = '-C "' + $Raiz + '" ' + ($Argumentos -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding $false
    $psi.StandardErrorEncoding = New-Object System.Text.UTF8Encoding $false
    $p = [System.Diagnostics.Process]::Start($psi)
    try {
        $p.StandardInput.Close()
        $errAsync = $p.StandardError.ReadToEndAsync()
        $out = $p.StandardOutput.ReadToEnd()
        if (-not $p.WaitForExit(120000)) { try { $p.Kill() } catch { }; throw "git $($Argumentos -join ' ') no termino en 120 s" }
        $err = $errAsync.Result
        if ($p.ExitCode -ne 0) { throw "git $($Argumentos -join ' ') salio con $($p.ExitCode): $($err.Trim())" }
        return $out
    }
    finally { $p.Dispose() }
}


function Get-HashHex {
    param([System.Security.Cryptography.HashAlgorithm] $Alg, [byte[]] $Bytes)
    return ([System.BitConverter]::ToString($Alg.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant()
}


function Get-HuellaDelArbol {
    <#
    .SYNOPSIS
        La huella de la spec 5.1: HEAD + sha256 del status + sha256 de la lista (ruta, tamano, sha256).
    .DESCRIPTION
        Es la misma cuenta que hizo la herramienta de WU03-a (huella.py): lo ignorado no entra.
        Si no se puede calcular devuelve Ok = $false con la causa (HUELLA_NO_DISPONIBLE).
    #>
    param([string] $Raiz)
    try {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        $alg = [System.Security.Cryptography.SHA256]::Create()
        $head = (Invoke-GitTexto -Raiz $Raiz -Argumentos @('rev-parse', 'HEAD')).Trim()
        $status = Invoke-GitTexto -Raiz $Raiz -Argumentos @('status', '--porcelain', '--untracked-files=all')
        $lista = Invoke-GitTexto -Raiz $Raiz -Argumentos @('ls-files', '-c', '-o', '--exclude-standard', '-z')
        $rutas = @($lista.Split([char]0) | Where-Object { $_.Length -gt 0 })
        $rutas = [string[]]$rutas
        [System.Array]::Sort($rutas, [System.StringComparer]::Ordinal)
        $filas = New-Object System.Collections.Generic.List[string]
        $archivos = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
        foreach ($rel in $rutas) {
            $completa = $Raiz.TrimEnd('\', '/') + '\' + $rel.Replace('/', '\')
            if (-not [System.IO.File]::Exists($completa)) { continue }
            $bytes = [System.IO.File]::ReadAllBytes($completa)
            $valor = "$($bytes.Length)`t$(Get-HashHex -Alg $alg -Bytes $bytes)"
            $filas.Add("$rel`t$valor")
            $archivos[$rel] = $valor
        }
        $hStatus = Get-HashHex -Alg $alg -Bytes $utf8.GetBytes($status)
        $hFiles = Get-HashHex -Alg $alg -Bytes $utf8.GetBytes(($filas -join "`n"))
        $huella = (Get-HashHex -Alg $alg -Bytes $utf8.GetBytes($head + $hStatus + $hFiles)).ToUpperInvariant()
        $lineasStatus = @($status -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 })
        return [pscustomobject]@{
            Ok = $true; Causa = ''; Head = $head; Huella = $huella; StatusHash = $hStatus; FilesHash = $hFiles
            StatusLines = $lineasStatus; Files = $archivos
        }
    } catch {
        return [pscustomobject]@{ Ok = $false; Causa = $_.Exception.Message; Huella = $null; StatusLines = @(); Files = $null }
    }
}


function Get-ValorDeHuella {
    param($H)
    if ($null -eq $H) { return $null }
    if ($H -is [string]) { return $H }
    if ($H.PSObject.Properties['Ok'] -and $H.Ok -eq $false) { return $null }
    return [string]$H.Huella
}


function Get-DiferenciasDeHuella {
    <# Las lineas de git status que difieren y, de lo que no aparece ahi, los archivos que cambiaron. #>
    param($A, $B)
    $salida = New-Object System.Collections.Generic.List[string]
    $nombrados = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    if ($null -eq $A -or $A -is [string] -or $null -eq $B -or $B -is [string]) { return @($salida) }
    $sa = @($A.StatusLines); $sb = @($B.StatusLines)
    foreach ($l in $sa) { if ($sb -cnotcontains $l) { $salida.Add("  - $l"); [void]$nombrados.Add($l.Substring([math]::Min(3, $l.Length))) } }
    foreach ($l in $sb) { if ($sa -cnotcontains $l) { $salida.Add("  + $l"); [void]$nombrados.Add($l.Substring([math]::Min(3, $l.Length))) } }
    if ($null -ne $A.Files -and $null -ne $B.Files) {
        foreach ($k in $A.Files.Keys) {
            if ($nombrados.Contains($k)) { continue }
            if (-not $B.Files.ContainsKey($k)) { $salida.Add("  - $k") }
            elseif ($A.Files[$k] -cne $B.Files[$k]) { $salida.Add("  ~ $k") }
        }
        foreach ($k in $B.Files.Keys) {
            if (-not $nombrados.Contains($k) -and -not $A.Files.ContainsKey($k)) { $salida.Add("  + $k") }
        }
    }
    return @($salida)
}


# ── El agregador (spec 16): la costura de testabilidad (16.7) ───────────────────

function New-LineaDeReporte {
    <# B = 'py': parte del bloque de Python, que el oraculo imprime de una sola vez; 'fin': el salto que cierra ese bloque. #>
    param([string] $Texto, [string] $Color, [string] $Bloque)
    return [pscustomobject]@{ T = $Texto; C = $Color; B = $Bloque }
}


function Get-LineasDeFallosPs {
    param($R)
    $crudas = @($R.failedLines)
    if ($crudas.Count -gt 0) { return $crudas }
    $l = New-Object System.Collections.Generic.List[string]
    foreach ($f in @($R.failedRows)) {
        $l.Add('  [' + $f.grupo + '] ' + $f.nombre)
        if ($f.detalle) { $l.Add('      ' + $f.detalle) }
    }
    return @($l)
}


function Get-LineasDeFilasPy {
    param($R)
    $crudas = @($R.pyRowLines)
    if ($crudas.Count -gt 0) { return $crudas }
    $l = New-Object System.Collections.Generic.List[string]
    foreach ($f in @($R.failedRows)) { $l.Add('    MAL ' + $f.grupo + ' / ' + $f.nombre + ' ' + $f.detalle) }
    return @($l)
}


function Get-ReporteDeCorrida {
    <#
    .SYNOPSIS
        Los registros por suite, la enumeracion y las huellas, al reporte canonico y al exit.
    .DESCRIPTION
        Es la costura que prueba VP-E13 con registros armados a mano: no lanza procesos, no toca
        TempBase, ni el candado, ni el arbol, ni el manifest. Consume solo sus argumentos. Si algo
        adentro falla, el resultado es exit 1 con INFRA ERROR_INTERNO y la pila: no se la traga.
        Devuelve { Exit, Lineas[{T,C}], Texto, Infra[] }.
    #>
    [CmdletBinding()]
    param(
        [object[]] $Registros = @(),
        [string[]] $Enumeradas = @(),
        $HuellaInicial,
        $HuellaFinal,
        [bool] $ManifestOk = $true,
        [string[]] $Avisos = @(),
        [switch] $Detallado,
        [switch] $Cancelado
    )

    $Rep = New-Object System.Collections.Generic.List[object]
    $infra = New-Object System.Collections.Generic.List[string]
    try {
        $enum = @($Enumeradas)
        $regs = @($Registros | Where-Object { $null -ne $_ })
        $ordinal = [System.StringComparer]::Ordinal

        # 1. El conjunto con registro es exactamente el enumerado.
        $porNombre = New-Object 'System.Collections.Generic.Dictionary[string,object]' $ordinal
        $cuenta = New-Object 'System.Collections.Generic.Dictionary[string,int]' $ordinal
        foreach ($r in $regs) {
            $n = [string]$r.suite
            if ($n.Length -eq 0) { throw 'un registro no tiene suite' }
            if ($cuenta.ContainsKey($n)) { $cuenta[$n] = $cuenta[$n] + 1 } else { $cuenta[$n] = 1; $porNombre[$n] = $r }
        }
        $enEnum = New-Object 'System.Collections.Generic.HashSet[string]' $ordinal
        foreach ($n in $enum) { [void]$enEnum.Add($n) }

        $conjuntoOk = $true
        $infraPorSuite = New-Object 'System.Collections.Generic.Dictionary[string,object]' $ordinal
        $validas = New-Object System.Collections.Generic.List[object]
        foreach ($n in $enum) {
            if (-not $cuenta.ContainsKey($n)) { $infra.Add("INFRA SUITE_AUSENTE $n"); $conjuntoOk = $false; continue }
            if ($cuenta[$n] -gt 1) { $infra.Add("INFRA SUITE_DUPLICADA $n"); $conjuntoOk = $false; continue }
            $r = $porNombre[$n]
            $inf = ConvertTo-InfraNormal $r.infra
            if ($null -eq $inf) { $inf = Get-InfraDeSuite -R $r }
            if ($null -ne $inf) {
                $infraPorSuite[$n] = $inf
                if (-not $Cancelado) { $infra.Add((Format-LineaInfra -Infra $inf -Suite $n)) }
            }
            else { $validas.Add($r) }
        }
        $sobrantes = @($cuenta.Keys | Where-Object { -not $enEnum.Contains($_) })
        [System.Array]::Sort($sobrantes, $ordinal)
        foreach ($n in $sobrantes) {
            $infra.Add("INFRA ERROR_INTERNO $n suite sobrante: no figura en la enumeracion")
            $conjuntoOk = $false
        }

        # 2. Las huellas (spec 5.1, 16.1 condicion 4).
        $hi = Get-ValorDeHuella $HuellaInicial
        $hf = Get-ValorDeHuella $HuellaFinal
        $huellaOk = $false
        if ($null -eq $hi -or $null -eq $hf) {
            $causa = ''
            foreach ($h in @($HuellaInicial, $HuellaFinal)) {
                if ($null -ne $h -and $h -isnot [string] -and $h.PSObject.Properties['Causa'] -and $h.Causa) { $causa = [string]$h.Causa; break }
            }
            $infra.Add(('INFRA HUELLA_NO_DISPONIBLE ' + $causa).TrimEnd())
        }
        elseif ($hi -cne $hf) {
            $infra.Add('INFRA ARBOL_CAMBIADO')
            foreach ($d in (Get-DiferenciasDeHuella -A $HuellaInicial -B $HuellaFinal)) { $infra.Add($d) }
        }
        else { $huellaOk = $true }

        $avisosL = @($Avisos | Where-Object { $_ })
        $nInfra = @($infra | Where-Object { $_.StartsWith('INFRA ') }).Count

        if ($Cancelado) {
            # Cancelada: no es un resultado. Sin PS/Py ni la forma verde de la linea final.
            # En orden canonico, nunca de llegada.
            $enEstado = { param($n, $estados) $porNombre.ContainsKey($n) -and ($estados -ccontains [string]$porNombre[$n].state) }
            $terminadas = @($enum | Where-Object { & $enEstado $_ @('TERMINADA') })
            $abortadas = @($enum | Where-Object { & $enEstado $_ @('MATADA_CANCELACION', 'MATADA_TIMEOUT', 'MUERTA') })
            $sinLanzar = @($enum | Where-Object { & $enEstado $_ @('SIN_LANZAR') })
            $Rep.Add((New-LineaDeReporte '' $null))
            $Rep.Add((New-LineaDeReporte 'CANCELADO: la corrida se interrumpio y quedo INCOMPLETA; no es un resultado.' 'Red'))
            $Rep.Add((New-LineaDeReporte ("  Terminadas ($($terminadas.Count)): " + ($terminadas -join ', ')) $null))
            $Rep.Add((New-LineaDeReporte ("  Abortadas ($($abortadas.Count)): " + ($abortadas -join ', ')) $null))
            $Rep.Add((New-LineaDeReporte ("  Sin lanzar ($($sinLanzar.Count)): " + ($sinLanzar -join ', ')) $null))
            foreach ($n in $abortadas) {
                $inf = $infraPorSuite[$n]
                $linea = 'INFRA CANCELADA ' + $n
                if ($null -ne $inf -and $inf.motivo -cne 'CANCELADA') { $linea = Format-LineaInfra -Infra $inf -Suite $n }
                $infra.Add($linea)
                $nInfra++
            }
            foreach ($l in $infra) { $Rep.Add((New-LineaDeReporte $l 'Red')) }
            foreach ($a in $avisosL) { $Rep.Add((New-LineaDeReporte $a 'Yellow')) }
            $Rep.Add((New-LineaDeReporte '' $null))
            $Rep.Add((New-LineaDeReporte $script:SeparadorFin 'Cyan'))
            $Rep.Add((New-LineaDeReporte ("CANCELADO - INCOMPLETO: $($terminadas.Count) de $($enum.Count) suites terminadas, $($abortadas.Count) abortadas, $($sinLanzar.Count) sin lanzar.") 'Red'))
            return [pscustomobject]@{ Exit = 1; Lineas = $Rep.ToArray(); Texto = (@($Rep | ForEach-Object { $_.T }) -join "`n"); Infra = @($infra) }
        }

        # 3. Los conteos: solo suman suites sin infra (un error de infraestructura no es una fila).
        $okPs = 0L; $totalPs = 0L; $okPy = 0L; $totalPy = 0L
        $gruposPs = New-Object System.Collections.Generic.List[object]
        $fallosPs = New-Object System.Collections.Generic.List[string]
        $gruposPy = New-Object System.Collections.Generic.List[string]
        $filasPy = New-Object System.Collections.Generic.List[string]
        $todoVerde = $true
        foreach ($r in $validas) {
            $ok = [long]$r.ok; $total = [long]$r.total
            if ($ok -ne $total -or $r.exitCode -ne 0) { $todoVerde = $false }
            if ([string]$r.engine -ceq 'ps') {
                $okPs += $ok; $totalPs += $total
                foreach ($g in @($r.groups)) {
                    $gruposPs.Add([pscustomobject]@{ Grupo = [string]$g.name; n = [long]$g.n; malos = [long]$g.malos; detalle = @($g.detalle) })
                }
                foreach ($x in (Get-LineasDeFallosPs -R $r)) { $fallosPs.Add([string]$x) }
            }
            else {
                $okPy += $ok; $totalPy += $total
                foreach ($g in @($r.groups)) {
                    $estado = 'OK   '
                    if ([long]$g.malos -gt 0) { $estado = 'FALLA' }
                    $gruposPy.Add('  ' + $estado + ' ' + [string]$g.name + '  (' + [long]$g.n + ')')
                }
                foreach ($x in (Get-LineasDeFilasPy -R $r)) { $filasPy.Add([string]$x) }
            }
        }
        $okTotal = $okPs + $okPy
        $totalTotal = $totalPs + $totalPy
        $fallaronPs = $totalPs - $okPs

        # 4. El exit: las seis condiciones de 16.1 (la sexta, la excepcion, es el catch de abajo).
        $exit = 1
        if ($conjuntoOk -and $infraPorSuite.Count -eq 0 -and $todoVerde -and $okTotal -eq $totalTotal -and $huellaOk -and $ManifestOk) { $exit = 0 }

        # 5. El reporte, con las formas del oraculo.
        $Rep.Add((New-LineaDeReporte '' $null))
        $Rep.Add((New-LineaDeReporte 'gcba-harness - tests' 'Cyan'))
        $Rep.Add((New-LineaDeReporte '' $null))

        # Los grupos PS, reagrupados globalmente como lo hace Group-Object en el oraculo.
        $globales = @($gruposPs | Group-Object Grupo)
        foreach ($g in $globales) {
            $cg = 0L; $malos = 0L
            foreach ($x in $g.Group) { $cg += $x.n; $malos += $x.malos }
            if ($malos -eq 0) { $Rep.Add((New-LineaDeReporte ('  OK    ' + $g.Name + '  (' + $cg + ')') 'Green')) }
            else { $Rep.Add((New-LineaDeReporte ('  FALLA ' + $g.Name + '  (' + $malos + '/' + $cg + ')') 'Red')) }
            if ($Detallado) {
                foreach ($x in $g.Group) { foreach ($d in $x.detalle) { $Rep.Add((New-LineaDeReporte ([string]$d) 'DarkGray')) } }
            }
        }
        if ($fallaronPs -gt 0 -or $fallosPs.Count -gt 0) {
            $Rep.Add((New-LineaDeReporte '' $null))
            $Rep.Add((New-LineaDeReporte 'Fallos:' 'Red'))
            foreach ($x in $fallosPs) {
                if ($x.StartsWith('  [')) { $Rep.Add((New-LineaDeReporte $x 'Red')) } else { $Rep.Add((New-LineaDeReporte $x 'DarkYellow')) }
            }
        }
        $Rep.Add((New-LineaDeReporte '' $null))
        if ($fallaronPs -eq 0) { $Rep.Add((New-LineaDeReporte "$okPs/$totalPs pasaron (PowerShell)." 'Green')) }
        else { $Rep.Add((New-LineaDeReporte "$okPs/$totalPs pasaron (PowerShell). $fallaronPs fallaron." 'Red')) }

        # El bloque de Python, como lo imprime el oraculo (Invoke-Tests.ps1, Write-Host $salidaPython).
        $Rep.Add((New-LineaDeReporte '' $null))
        $Rep.Add((New-LineaDeReporte $script:SeparadorPy 'Cyan'))
        $Rep.Add((New-LineaDeReporte '' $null))
        $Rep.Add((New-LineaDeReporte '' $null 'py'))
        $Rep.Add((New-LineaDeReporte 'gcba-harness - tests (python)' $null 'py'))
        $Rep.Add((New-LineaDeReporte '' $null 'py'))
        foreach ($x in $gruposPy) { $Rep.Add((New-LineaDeReporte $x $null 'py')) }
        foreach ($x in $filasPy) { $Rep.Add((New-LineaDeReporte $x $null 'py')) }
        $Rep.Add((New-LineaDeReporte '' $null 'py'))
        $Rep.Add((New-LineaDeReporte "$okPy/$totalPy pasaron." $null 'py'))
        $Rep.Add((New-LineaDeReporte '' $null 'fin'))

        # El bloque de infraestructura y los avisos (spec 16.3).
        if ($infra.Count -gt 0 -or $avisosL.Count -gt 0) {
            foreach ($l in $infra) { $Rep.Add((New-LineaDeReporte $l 'Red')) }
            foreach ($a in $avisosL) { $Rep.Add((New-LineaDeReporte $a 'Yellow')) }
            if ($nInfra -gt 0) { $Rep.Add((New-LineaDeReporte "$nInfra suites con error de infraestructura." 'Red')) }
        }

        $Rep.Add((New-LineaDeReporte '' $null))
        $Rep.Add((New-LineaDeReporte $script:SeparadorFin 'Cyan'))
        if ($exit -eq 0) { $Rep.Add((New-LineaDeReporte "$okTotal/$totalTotal pasaron." 'Green')) }
        else { $Rep.Add((New-LineaDeReporte "$okTotal/$totalTotal pasaron. $($totalTotal - $okTotal) fallaron." 'Red')) }

        return [pscustomobject]@{ Exit = $exit; Lineas = $Rep.ToArray(); Texto = (@($Rep | ForEach-Object { $_.T }) -join "`n"); Infra = @($infra) }
    }
    catch {
        $m = $_.Exception.Message
        $pila = [string]$_.ScriptStackTrace
        $salida = New-Object System.Collections.Generic.List[object]
        $salida.Add((New-LineaDeReporte '' $null))
        $salida.Add((New-LineaDeReporte "INFRA ERROR_INTERNO $m" 'Red'))
        foreach ($p in ($pila -split "`r?`n")) { if ($p.Trim().Length -gt 0) { $salida.Add((New-LineaDeReporte "  $p" 'Red')) } }
        $salida.Add((New-LineaDeReporte '' $null))
        $salida.Add((New-LineaDeReporte $script:SeparadorFin 'Cyan'))
        $salida.Add((New-LineaDeReporte 'ERROR INTERNO del agregador: no hay resultado. 1 suites con error de infraestructura.' 'Red'))
        return [pscustomobject]@{ Exit = 1; Lineas = $salida.ToArray(); Texto = (@($salida | ForEach-Object { $_.T }) -join "`n"); Infra = @("INFRA ERROR_INTERNO $m") }
    }
}


function Write-LineasDeReporte {
    <#
    .SYNOPSIS
        Imprime el reporte. El bloque de Python sale de una sola vez, con los saltos CRLF que le da
        Out-String en el oraculo (Invoke-Tests.ps1: Write-Host $salidaPython): asi el texto es el mismo.
    #>
    param($Lineas)
    $bloque = $null
    foreach ($l in $Lineas) {
        if ($l.B -ceq 'py') {
            if ($null -eq $bloque) { $bloque = New-Object System.Collections.Generic.List[string] }
            $bloque.Add($l.T)
            continue
        }
        if ($null -ne $bloque) {
            Write-Host (($bloque -join "`r`n") + "`r`n")
            $bloque = $null
        }
        if ($l.B -ceq 'fin') { continue }
        if ($l.C) { Write-Host $l.T -ForegroundColor $l.C } else { Write-Host $l.T }
    }
}


# ── Workers (spec 9.2, 12, 14) ──────────────────────────────────────────────────

function New-CanalDeSalida {
    param($Stream, [string] $Ruta)
    $fs = New-Object System.IO.FileStream($Ruta, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
    $c = [pscustomobject]@{ Stream = $Stream; Fs = $fs; Buf = (New-Object byte[] 8192); Ar = $null; Done = $false }
    try { $c.Ar = $Stream.BeginRead($c.Buf, 0, $c.Buf.Length, $null, $null) } catch { $c.Done = $true }
    return $c
}


function Step-Canal {
    <# Un paso del bombeo, sin esperar: si hay bytes listos van al archivo tal cual (son los del worker). #>
    param($C)
    while (-not $C.Done -and $null -ne $C.Ar -and $C.Ar.IsCompleted) {
        $n = 0
        try { $n = $C.Stream.EndRead($C.Ar) } catch { $n = 0 }
        $C.Ar = $null
        if ($n -gt 0) {
            $C.Fs.Write($C.Buf, 0, $n)
            $C.Fs.Flush()
            try { $C.Ar = $C.Stream.BeginRead($C.Buf, 0, $C.Buf.Length, $null, $null) } catch { $C.Done = $true }
        }
        else { $C.Done = $true }
    }
}


function Start-WorkerDeSuite {
    <#
    .SYNOPSIS
        Lanza Invoke-Tests.ps1 -SoloCaso <archivo> en su propio powershell.exe, con TEMP propio.
    .DESCRIPTION
        stdin queda cerrado; stdout y stderr se bombean tal cual a <raiz>\logs\<nnn>.out/.err (los
        bytes UTF-8 del oraculo, sin recodificar); el resto del entorno es el del runner. El objeto
        Process queda abierto hasta recolectar al worker: su pid no se reusa mientras tanto.
    #>
    param($Ctx, $S)

    $nnn = '{0:D3}' -f $S.Index
    $sdir = $Ctx.RaizCorrida.Dir + '\s' + $nnn
    if ([System.IO.Directory]::Exists($sdir)) { throw "el temporal de la suite ya existe: $sdir" }
    [void][System.IO.Directory]::CreateDirectory($sdir)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = [System.IO.Path]::Combine($env:SystemRoot, 'System32\WindowsPowerShell\v1.0\powershell.exe')
    $linea = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $Ctx.Raiz + '\tests\Invoke-Tests.ps1" -SoloCaso "' + $S.Nombre + '"'
    if ($Ctx.Detallado) { $linea += ' -Detallado' }
    $psi.Arguments = $linea
    $psi.WorkingDirectory = $Ctx.Raiz
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $false
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding $false
    $psi.StandardErrorEncoding = New-Object System.Text.UTF8Encoding $false
    $psi.EnvironmentVariables['TEMP'] = $sdir
    $psi.EnvironmentVariables['TMP'] = $sdir
    $psi.EnvironmentVariables['TMPDIR'] = $sdir

    $outPath = $Ctx.RaizCorrida.Logs + '\' + $nnn + '.out'
    $errPath = $Ctx.RaizCorrida.Logs + '\' + $nnn + '.err'
    $reloj = [System.Diagnostics.Stopwatch]::StartNew()
    $inicio = [DateTime]::UtcNow
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.StandardInput.Close()
    $w = [pscustomobject]@{
        Suite = $S; Proc = $p; Reloj = $reloj; Inicio = $inicio; SDir = $sdir; OutPath = $outPath; ErrPath = $errPath
        Out = (New-CanalDeSalida -Stream $p.StandardOutput.BaseStream -Ruta $outPath)
        Err = (New-CanalDeSalida -Stream $p.StandardError.BaseStream -Ruta $errPath)
        Matado = ''; KillEnviado = $false; ProximaLenta = 1200.0
    }
    return $w
}


function Stop-ArbolDeWorker {
    <#
    .SYNOPSIS
        taskkill /PID <worker> /T /F con el handle del worker abierto (spec 14.3).
    .DESCRIPTION
        Mata al worker y a los descendientes cuya cadena de padres sigue viva. Nunca por nombre de
        imagen ni por un pid guardado: el pid es el de un Process que este runner tiene abierto.
    #>
    param($W)
    $W.KillEnviado = $true
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = [System.IO.Path]::Combine($env:SystemRoot, 'System32\taskkill.exe')
        $psi.Arguments = '/PID ' + $W.Proc.Id + ' /T /F'
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $t = [System.Diagnostics.Process]::Start($psi)
        try {
            $e = $t.StandardError.ReadToEndAsync()
            [void]$t.StandardOutput.ReadToEnd()
            [void]$t.WaitForExit(20000)
            [void]$e.Result
        } finally { $t.Dispose() }
    } catch { }
    # Respaldo: el proceso propio de este runner, si taskkill no pudo.
    try { if (-not $W.Proc.WaitForExit(3000)) { $W.Proc.Kill() } } catch { }
}


function Get-TextoDeLog {
    param([string] $Ruta)
    try { return [System.IO.File]::ReadAllText($Ruta, (New-Object System.Text.UTF8Encoding $false)) } catch { return '' }
}


function Format-Segundos {
    param([double] $S)
    return $S.ToString('0.0', [System.Globalization.CultureInfo]::InvariantCulture)
}


function Write-ProgresoDeSuite {
    <# Una linea por suite terminada; al fallar, sus lineas de fallo y la ruta de sus logs (spec 16.6). #>
    param($Ctx, $R)
    $k = $Ctx.Registros.Count
    $estado = 'OK'; $color = 'Green'
    if ($null -ne $R.infra) { $estado = 'INFRA'; $color = 'Red' }
    elseif ($R.exitCode -ne 0 -or $R.ok -ne $R.total) { $estado = 'FALLA'; $color = 'Red' }
    Write-Host ("[$k/$($Ctx.Total)] $estado $($R.suite) ($($R.total)) $(Format-Segundos $R.seconds) s") -ForegroundColor $color
    if ($estado -ne 'OK') {
        $inf = ConvertTo-InfraNormal $R.infra
        if ($null -ne $inf) { Write-Host ('    ' + (Format-LineaInfra -Infra $inf -Suite $R.suite)) -ForegroundColor Red }
        $mostradas = 0
        foreach ($l in @(Get-LineasDeFallosPs -R $R) + @(Get-LineasDeFilasPy -R $R)) {
            if ($mostradas -ge 30) { Write-Host '    ...' -ForegroundColor DarkYellow; break }
            Write-Host ('    ' + $l) -ForegroundColor DarkYellow
            $mostradas++
        }
        Write-Host ('    logs: ' + $R.stdoutPath) -ForegroundColor DarkGray
    }
    if ($R.stderrTexto -and $R.stderrTexto.Trim().Length -gt 0) {
        $e = @($R.stderrTexto -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 })
        Write-Host '    stderr del worker:' -ForegroundColor DarkYellow
        $n = 0
        foreach ($l in $e) {
            if ($n -ge 20) { Write-Host '      ...' -ForegroundColor DarkYellow; break }
            Write-Host ('      ' + $l) -ForegroundColor DarkYellow
            $n++
        }
    }
}


function Complete-Worker {
    <# Recolecta a un worker que ya salio: cierra la captura, parsea, borra su temporal, registra (spec 14.2). #>
    param($Ctx, $W)

    # Lo que quede en los pipes se junta con un plazo corto: un nieto que heredo el pipe y sigue
    # vivo no puede retener al runner.
    $limite = [System.Diagnostics.Stopwatch]::StartNew()
    while ((-not $W.Out.Done -or -not $W.Err.Done) -and $limite.Elapsed.TotalSeconds -lt 3) {
        Step-Canal $W.Out; Step-Canal $W.Err
        if (-not $W.Out.Done -or -not $W.Err.Done) { Start-Sleep -Milliseconds 20 }
    }
    foreach ($c in @($W.Out, $W.Err)) { try { $c.Fs.Dispose() } catch { } }

    $segundos = $W.Reloj.Elapsed.TotalSeconds
    $exit = $null
    try { $exit = [int]$W.Proc.ExitCode } catch { }
    $S = $W.Suite
    $R = New-RegistroDeSuite -Suite $S.Nombre -Engine $S.Engine -Index $S.Index
    $R.exitCode = $exit
    $R.stdoutPath = $W.OutPath
    $R.stderrPath = $W.ErrPath
    $R.seconds = $segundos
    $R.inicio = $W.Inicio.ToString('o')
    $R.fin = [DateTime]::UtcNow.ToString('o')
    $R.timeoutSeconds = $S.TimeoutSeconds
    $stdout = Get-TextoDeLog $W.OutPath
    $R.stderrTexto = Get-TextoDeLog $W.ErrPath

    if ($W.Matado -ceq 'TIMEOUT') { $R.state = 'MATADA_TIMEOUT' }
    elseif ($W.Matado -ceq 'CANCELACION') { $R.state = 'MATADA_CANCELACION' }
    else {
        $p = ConvertFrom-SalidaDeWorker -Texto $stdout -Stderr $R.stderrTexto -Engine $S.Engine -Detallado $Ctx.Detallado
        $R.reported = $p.reported; $R.forma = $p.forma; $R.ok = $p.ok; $R.total = $p.total; $R.nFallaron = $p.nFallaron
        $R.sinResumen = $p.sinResumen
        $R.groups = $p.groups; $R.failedRows = $p.failedRows; $R.failedLines = $p.failedLines
        $R.pyRowLines = $p.pyRowLines; $R.rows = $p.rows
        # Termino por su cuenta con la linea final, con la marca de resumen ausente o con un mensaje
        # propio del oraculo: TERMINADA. Si no dijo ninguna de las tres cosas, el contrato de exit del
        # oraculo separa la muerte del resumen ausente: el oraculo solo sale 0 o 1 (un `exit` o un
        # error de script), asi que otro codigo (el -1 de Stop-Process, un crash) es un proceso que
        # desaparecio: MUERTA, aunque haya escrito en stderr antes. Con 0 o 1 y algo en stderr, el
        # oraculo corto solo (el stderr de una suite Py lo corta: F6): TERMINADA, sin resumen. Con 0 o 1
        # y nada dicho, no hay con que distinguirla de una muerte: MUERTA.
        $salioComoElOraculo = ($null -ne $exit -and ($exit -eq 0 -or $exit -eq 1))
        if ($p.reported -or $p.sinResumen -or $p.propio) { $R.state = 'TERMINADA' }
        elseif (-not $salioComoElOraculo) { $R.state = 'MUERTA' }
        elseif ($R.stderrTexto.Trim().Length -gt 0) { $R.state = 'TERMINADA' }
        else { $R.state = 'MUERTA' }
    }
    $R.infra = Get-InfraDeSuite -R $R

    try { $W.Proc.Dispose() } catch { }

    $fallos = @(Remove-ArbolSeguro -Ruta $W.SDir)
    if ($fallos.Count -gt 0) { $Ctx.Pendientes.Add($W.SDir) }

    [void]$Ctx.Vivos.Remove($W)
    $Ctx.Registros.Add($R)
    if ($W.Matado -cne 'CANCELACION') { Write-ProgresoDeSuite -Ctx $Ctx -R $R }
}


function Stop-TodosLosWorkers {
    <# Pasos (2) a (4) de la cancelacion (spec 18): matar a cada worker vivo, esperarlo, recolectar. #>
    param($Ctx)
    foreach ($w in $Ctx.Vivos.ToArray()) {
        if ($w.Matado -cne 'TIMEOUT') { $w.Matado = 'CANCELACION' }
        Stop-ArbolDeWorker -W $w
    }
    $reloj = [System.Diagnostics.Stopwatch]::StartNew()
    while ($Ctx.Vivos.Count -gt 0 -and $reloj.Elapsed.TotalSeconds -lt 60) {
        foreach ($w in $Ctx.Vivos.ToArray()) {
            Step-Canal $w.Out; Step-Canal $w.Err
            if ($w.Proc.HasExited) { Complete-Worker -Ctx $Ctx -W $w }
        }
        if ($Ctx.Vivos.Count -gt 0) { Start-Sleep -Milliseconds 100 }
    }
}


function Invoke-Planificador {
    <#
    .SYNOPSIS
        El scheduler: un solo hilo, N lugares, carriles exclusivos, serial y desconocidas al final.
    .DESCRIPTION
        Lanza la primera de la lista cuyo carril no tenga otra viva; cuando la lista se vacia y no
        queda ninguna viva, corre las seriales y las desconocidas de a una. Espera con plazos
        cortos. Si aparece el CancelFile levanta una excepcion propia: va al mismo finally que
        Ctrl-C.
    #>
    param($Ctx)

    while ($true) {
        if ($Ctx.CancelFile -and [System.IO.File]::Exists($Ctx.CancelFile)) {
            throw (New-Object System.OperationCanceledException 'cancelacion solicitada por -CancelFile')
        }

        foreach ($w in $Ctx.Vivos.ToArray()) {
            Step-Canal $w.Out; Step-Canal $w.Err
            if ($w.Proc.HasExited) { Complete-Worker -Ctx $Ctx -W $w; continue }
            $t = $w.Reloj.Elapsed.TotalSeconds
            $limite = $w.Suite.TimeoutSeconds
            if ($null -ne $limite) {
                if ($t -ge $limite -and -not $w.KillEnviado) {
                    $w.Matado = 'TIMEOUT'
                    Stop-ArbolDeWorker -W $w
                }
            }
            elseif ($t -ge $w.ProximaLenta) {
                Write-Host ("LENTA $($w.Suite.Nombre) $([int]$t) s") -ForegroundColor Yellow
                $w.ProximaLenta += 600.0
            }
        }

        while ($Ctx.Vivos.Count -lt $Ctx.N) {
            $siguiente = $null
            if ($Ctx.Pool.Count -gt 0) {
                foreach ($s in $Ctx.Pool) {
                    $ocupado = $false
                    if ($s.Lane) {
                        foreach ($v in $Ctx.Vivos) { if ($v.Suite.Lane -and $v.Suite.Lane -ceq $s.Lane) { $ocupado = $true; break } }
                    }
                    if (-not $ocupado) { $siguiente = $s; break }
                }
                if ($null -eq $siguiente) { break }
                [void]$Ctx.Pool.Remove($siguiente)
            }
            elseif ($Ctx.Vivos.Count -eq 0 -and $Ctx.Seriales.Count -gt 0) {
                $siguiente = $Ctx.Seriales[0]
                $Ctx.Seriales.RemoveAt(0)
            }
            else { break }
            $Ctx.Vivos.Add((Start-WorkerDeSuite -Ctx $Ctx -S $siguiente))
        }

        if ($Ctx.Pool.Count -eq 0 -and $Ctx.Seriales.Count -eq 0 -and $Ctx.Vivos.Count -eq 0) { break }
        Start-Sleep -Milliseconds 50
    }
}


# ── La corrida ──────────────────────────────────────────────────────────────────

function Invoke-CuerpoDeLaCorrida {
    param($Cfg, $RaizCorrida, $Avisos)

    $raiz = $Cfg.Raiz
    $bash = ''
    try { $b = Get-Command bash -ErrorAction SilentlyContinue | Select-Object -First 1; if ($b) { $bash = $b.Source } } catch { }
    Write-Host ("Invoke-Tests-Parallel: workers=$($Cfg.Workers) TempBase=$($Cfg.TempBase) bash=$bash") -ForegroundColor DarkGray

    $hIni = Get-HuellaDelArbol -Raiz $raiz
    if (-not $hIni.Ok) {
        Write-Host ('INFRA HUELLA_NO_DISPONIBLE ' + $hIni.Causa) -ForegroundColor Red
        if (@(Remove-RaizDeCorrida -TempBase $RaizCorrida.TempBase -Ruta $RaizCorrida.Dir).Count -eq 0) { $RaizCorrida.Borrada = $true }
        return 1
    }

    # La enumeracion: una sola vez, con las mismas llamadas del oraculo (Invoke-Tests.ps1:166-167).
    $casosDir = Join-Path $Cfg.DirDelScript 'casos'
    $ps = @(Get-ChildItem $casosDir -Filter '*.ps1' -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($ps.Count -eq 0) {
        Write-Host ''
        Write-Host 'gcba-harness - tests' -ForegroundColor Cyan
        Write-Host ''
        Write-Host 'No hay casos en tests\casos\.' -ForegroundColor Yellow
        if (@(Remove-RaizDeCorrida -TempBase $RaizCorrida.TempBase -Ruta $RaizCorrida.Dir).Count -eq 0) { $RaizCorrida.Borrada = $true }
        return 1
    }
    # Python ordena con sorted() sobre Path (correr.py:57): en Windows compara los nombres en minusculas,
    # punto de codigo a punto de codigo. El runner REPRODUCE esa regla (ToLowerInvariant + comparacion
    # ordinal) en lugar de pedirsela a un interprete: no necesita Python, y VP-E14 la fija con a_b.py y ab.py.
    $pyArchivos = @(Get-ChildItem $casosDir -File -Filter '*.py' -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name.EndsWith('.py', [System.StringComparison]::OrdinalIgnoreCase) })
    if ($pyArchivos.Count -gt 1) {
        $ordenados = New-Object 'System.Collections.Generic.List[object]'
        foreach ($f in $pyArchivos) { $ordenados.Add($f) }
        $ordenados.Sort([System.Comparison[object]]{
            param($x, $y)
            [string]::CompareOrdinal($x.Name.ToLowerInvariant(), $y.Name.ToLowerInvariant())
        })
        $pyArchivos = $ordenados.ToArray()
    }
    $manif = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
    foreach ($e in $Cfg.Manifest.Entradas) { $manif[$e.suite] = $e }

    $todas = New-Object System.Collections.Generic.List[object]
    $indice = 0
    $nombresEnumerados = New-Object System.Collections.Generic.List[string]
    $conjunto = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($par in @(@('ps', $ps), @('py', $pyArchivos))) {
        foreach ($f in $par[1]) {
            $indice++
            $entrada = $null
            [void]$manif.TryGetValue($f.Name, [ref]$entrada)
            $s = [pscustomobject]@{
                Nombre = $f.Name; Engine = $par[0]; Index = $indice; Entrada = $entrada
                Clase = 'desconocida'; Lane = $null; MaxSeconds = $null; TimeoutSeconds = $null; Desconocida = $false
            }
            if ($null -eq $entrada) { $s.Desconocida = $true }
            else {
                $s.Clase = $entrada.clase
                if ($entrada.clase -ceq 'lane') { $s.Lane = $entrada.lane }
                $s.MaxSeconds = $entrada.maxSeconds
                $s.TimeoutSeconds = $entrada.timeoutSeconds
            }
            $todas.Add($s)
            $nombresEnumerados.Add($f.Name)
            [void]$conjunto.Add($f.Name)
        }
    }
    foreach ($e in $Cfg.Manifest.Entradas) {
        if (-not $conjunto.Contains($e.suite)) { $Avisos.Add('AVISO SUITE_INEXISTENTE ' + $e.suite) }
    }
    foreach ($s in $todas) {
        if ($s.Desconocida) { $Avisos.Add('AVISO SUITE_NO_CLASIFICADA ' + $s.Nombre) }
    }

    $pool = New-Object System.Collections.Generic.List[object]
    $seriales = New-Object System.Collections.Generic.List[object]
    $candidatas = @($todas | Where-Object { -not $_.Desconocida -and $_.Clase -cne 'serial' } |
        Sort-Object @{ Expression = { if ($null -eq $_.MaxSeconds) { -1.0 } else { [double]$_.MaxSeconds } }; Descending = $true }, @{ Expression = { $_.Index }; Descending = $false })
    foreach ($s in $candidatas) { $pool.Add($s) }
    foreach ($s in @($todas | Where-Object { $_.Desconocida -or $_.Clase -ceq 'serial' } | Sort-Object Index)) { $seriales.Add($s) }

    $ctx = [pscustomobject]@{
        N = $Cfg.Workers; Detallado = [bool]$Cfg.Detallado; Raiz = $raiz; RaizCorrida = $RaizCorrida; CancelFile = $Cfg.CancelFile
        Pool = $pool; Seriales = $seriales; Vivos = (New-Object System.Collections.Generic.List[object])
        Registros = (New-Object System.Collections.Generic.List[object]); Pendientes = (New-Object System.Collections.Generic.List[string])
        Total = $todas.Count
    }

    # Un solo try/finally: la cancelacion por -CancelFile y Ctrl-C llegan al mismo finally (spec 18).
    $cancelado = $false
    $completo = $false
    try {
        Invoke-Planificador -Ctx $ctx
        $completo = $true
    }
    catch [System.OperationCanceledException] { $cancelado = $true }
    finally {
        if (-not $completo) { Stop-TodosLosWorkers -Ctx $ctx }
    }
    if ($cancelado) {
        foreach ($s in ($ctx.Pool.ToArray() + $ctx.Seriales.ToArray())) {
            $r = New-RegistroDeSuite -Suite $s.Nombre -Engine $s.Engine -Index $s.Index
            $r.state = 'SIN_LANZAR'
            $ctx.Registros.Add($r)
        }
    }

    # Limpieza: reintento final de lo que no se pudo borrar al salir cada suite (spec 16.5).
    $residuos = New-Object System.Collections.Generic.List[string]
    foreach ($sd in $ctx.Pendientes) {
        $quedan = @(Remove-ArbolSeguro -Ruta $sd)
        if ($quedan.Count -gt 0) { $residuos.Add('AVISO LIMPIEZA_INCOMPLETA ' + $quedan[0]) }
    }
    $avisosFinales = New-Object System.Collections.Generic.List[string]
    foreach ($a in $Avisos) { $avisosFinales.Add($a) }
    foreach ($a in $residuos) { $avisosFinales.Add($a) }

    $hFin = Get-HuellaDelArbol -Raiz $raiz
    $detSw = [bool]$ctx.Detallado
    $canSw = [bool]$cancelado
    $reporte = Get-ReporteDeCorrida -Registros $ctx.Registros.ToArray() -Enumeradas @($nombresEnumerados) -HuellaInicial $hIni -HuellaFinal $hFin `
        -ManifestOk $true -Avisos @($avisosFinales) -Detallado:$detSw -Cancelado:$canSw

    # Todo verde y limpio: la raiz entera, y despues su sidecar. Si algo fue rojo, o quedo un
    # residuo declarado, se conservan los logs y el sidecar queda liberado al lado (spec 19.5).
    if ($reporte.Exit -eq 0 -and $residuos.Count -eq 0) {
        $quedan = @(Remove-RaizDeCorrida -TempBase $RaizCorrida.TempBase -Ruta $RaizCorrida.Dir)
        if ($quedan.Count -eq 0) { $RaizCorrida.Borrada = $true }
        else {
            $avisosFinales.Add('AVISO LIMPIEZA_INCOMPLETA ' + $quedan[0])
            $reporte = Get-ReporteDeCorrida -Registros $ctx.Registros.ToArray() -Enumeradas @($nombresEnumerados) -HuellaInicial $hIni -HuellaFinal $hFin `
                -ManifestOk $true -Avisos @($avisosFinales) -Detallado:$detSw -Cancelado:$canSw
        }
    }
    if (-not $RaizCorrida.Borrada) {
        Write-Host ''
        Write-Host ('Logs de la corrida (se conservan hasta la proxima): ' + $RaizCorrida.Logs) -ForegroundColor Yellow
    }

    Write-LineasDeReporte -Lineas $reporte.Lineas
    return $reporte.Exit
}


function Invoke-CorridaParalela {
    param(
        [int] $Workers,
        [bool] $Detallado,
        [string] $TempBase,
        [string] $LockPath,
        [string] $CancelFile,
        [string] $DirDelScript
    )

    $ErrorActionPreference = 'Stop'
    $utf8 = New-Object System.Text.UTF8Encoding $false
    try { [Console]::OutputEncoding = $utf8 } catch { }

    try {
        # 1. Argumentos y manifest: antes de crear nada y de tomar el candado.
        if ($Workers -lt 1 -or $Workers -gt 4) {
            Write-Host "ARGUMENTO_INVALIDO -Workers tiene que ser un entero de 1 a 4 (recibi $Workers)." -ForegroundColor Red
            return 1
        }
        if ([string]::IsNullOrWhiteSpace($TempBase)) {
            Write-Host 'ARGUMENTO_INVALIDO -TempBase esta vacio y $env:TEMP tampoco existe.' -ForegroundColor Red
            return 1
        }
        if ([string]::IsNullOrWhiteSpace($LockPath)) {
            Write-Host 'ARGUMENTO_INVALIDO -LockPath esta vacio y $env:LOCALAPPDATA tampoco existe.' -ForegroundColor Red
            return 1
        }
        try { $manifest = Read-ManifestParalelo -Ruta (Join-Path $DirDelScript 'parallel-manifest.json') }
        catch { $manifest = [pscustomobject]@{ Ok = $false; Causa = ('no se pudo validar la forma: ' + $_.Exception.Message); Entradas = @() } }
        if (-not $manifest.Ok) {
            Write-Host ('MANIFEST_INVALIDO ' + $manifest.Causa) -ForegroundColor Red
            return 1
        }

        $base = $TempBase.TrimEnd('\', '/')
        if (-not [System.IO.Path]::IsPathRooted($base)) { $base = (Join-Path $PWD.ProviderPath $base).TrimEnd('\', '/') }
        $cfg = [pscustomobject]@{
            Workers = $Workers; Detallado = $Detallado; TempBase = $base; CancelFile = $CancelFile
            DirDelScript = $DirDelScript; Raiz = (Split-Path -Parent $DirDelScript); Manifest = $manifest
        }

        # 2. El candado pesada.lock: sin esperar; ocupado o ilegible, no corre nada.
        $candado = Open-Candado -Ruta $LockPath -CrearPadre
        if ($candado.Estado -eq 'ocupado') {
            $info = Read-InfoDelCandado -LockPath $LockPath
            Write-Host ("LOCK_OCUPADO desde $($info.Desde) (pid $($info.Pid), informativo)") -ForegroundColor Red
            return 2
        }
        if ($candado.Estado -eq 'ilegible') {
            Write-Host ('LOCK_ILEGIBLE ' + $candado.Causa) -ForegroundColor Red
            return 2
        }

        $raizCorrida = $null
        try {
            Write-InfoDelCandado -LockPath $LockPath -Raiz $cfg.Raiz -Workers $Workers
            $avisos = New-Object System.Collections.Generic.List[string]
            # 3. El barrido de raices de corridas muertas, y la raiz de esta corrida.
            Invoke-BarridoDeRaices -TempBase $base -Avisos $avisos
            $raizCorrida = New-RaizDeCorrida -TempBase $base
            return (Invoke-CuerpoDeLaCorrida -Cfg $cfg -RaizCorrida $raizCorrida -Avisos $avisos)
        }
        finally {
            # 19.5: los hijos ya terminaron. Primero el sidecar de la corrida, despues pesada.lock.
            Close-RaizDeCorrida -Raiz $raizCorrida
            try { $candado.Stream.Dispose() } catch { }
        }
    }
    catch {
        Write-Host ('INFRA ERROR_INTERNO ' + $_.Exception.Message) -ForegroundColor Red
        foreach ($p in ([string]$_.ScriptStackTrace -split "`r?`n")) { if ($p.Trim().Length -gt 0) { Write-Host ('  ' + $p) -ForegroundColor Red } }
        return 1
    }
}


# La guarda de invocacion: cargar este archivo con dot-source (". .\Invoke-Tests-Parallel.ps1")
# solo define las funciones de arriba.
if ($MyInvocation.InvocationName -ne '.') {
    $salidaDeLaCorrida = @(Invoke-CorridaParalela -Workers $Workers -Detallado ([bool]$Detallado) -TempBase $TempBase `
        -LockPath $LockPath -CancelFile $CancelFile -DirDelScript $PSScriptRoot)
    exit ([int]$salidaDeLaCorrida[-1])
}
