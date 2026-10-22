<#
.SYNOPSIS
    Compara la salida del oraculo (Invoke-Tests.ps1) con la del runner (Invoke-Tests-Parallel.ps1)
    sobre la misma huella del arbol.

.DESCRIPTION
    Dice EQUIVALENTE (exit 0), NO_EQUIVALENTE (exit 1) o NO_COMPARABLE (exit 1). La primera linea
    de la salida es siempre una de esas tres palabras, sola.

    Equivalentes (spec 20.4, todo a la vez):
      1. mismo exit: se deduce de la forma de la linea final (verde si y solo si exit 0);
      2. misma secuencia de lineas de grupo PowerShell (nombre, n, malos) y Python (stem, n),
         en el mismo orden;
      3. mismos ok, total y fallidas, por motor y combinados;
      4. mismo multiconjunto de filas fallidas (grupo, nombre), en los dos motores;
      5. con -Detallado en los dos, mismo multiconjunto de filas (grupo, nombre, ok);
      6. el runner no tiene lineas INFRA.

    NO_EQUIVALENTE nombra cada campo que difiere, una linea por campo: "  campo <nombre>: ...".
    Los nombres: exit, grupos-ps, grupos-py, ok-ps, total-ps, fallidas-ps, ok-py, total-py,
    fallidas-py, ok, total, fallidas, filas-fallidas, filas, infra.

    NO_COMPARABLE: las huellas son distintas, una fila MAL de Python no tiene un prefijo de
    detalle conocido (no se puede separar su nombre), o una salida no tiene la forma del reporte.
    Con huellas distintas nunca hay EQUIVALENTE.

    Solo se compara la region comparable de cada archivo: desde la ULTIMA linea
    "gcba-harness - tests" hasta el final. Lo anterior (encabezado propio del runner, progreso,
    avisos con rutas) no cuenta. Las lineas INFRA del runner se buscan en todo el archivo.

    No hay tolerancia: ni lista de suites que derivan, ni margen, ni parametro para pedirla.

.PARAMETER Serial
    Archivo con la salida estandar del oraculo.

.PARAMETER Paralelo
    Archivo con la salida estandar del runner (con o sin progreso).

.PARAMETER HuellaSerial
    La huella del arbol de la corrida del oraculo.

.PARAMETER HuellaParalelo
    La huella del arbol de la corrida del runner.

.EXAMPLE
    .\tests\Compare-TestRuns.ps1 -Serial s.txt -Paralelo p.txt -HuellaSerial $h -HuellaParalelo $h
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory)]
    [string] $Serial,

    [Parameter(Mandatory)]
    [string] $Paralelo,

    [Parameter(Mandatory)]
    [string] $HuellaSerial,

    [Parameter(Mandatory)]
    [string] $HuellaParalelo
)

$ErrorActionPreference = 'Stop'

# UTF-8 en toda la cadena, como el oraculo: los nombres de grupo llevan tildes.
$utf8 = New-Object System.Text.UTF8Encoding $false
try { [Console]::OutputEncoding = $utf8 } catch { }
$OutputEncoding = $utf8

# Las formas del oraculo (Invoke-Tests.ps1:190-223, 284-291; correr.py:85-92). Todas sensibles a
# mayusculas: -cmatch, nunca -match.
$script:PuntoMedio   = [string][char]0x00B7
$script:ReCabecera   = 'gcba-harness - tests'
$script:ReCabeceraPy = 'gcba-harness - tests (python)'
$script:ReGrupo      = '^  (?:OK    |FALLA )(.+)  \(([0-9]+)(?:/([0-9]+))?\)$'
$script:ReFilaPs     = '^ {8}' + [regex]::Escape($script:PuntoMedio) + ' (.*)$'
$script:ReFalloPs    = '^  \[(.+?)\] (.*)$'
$script:ReResumenPs  = '^([0-9]+)/([0-9]+) pasaron \(PowerShell\)\.(?: ([0-9]+) fallaron\.)?$'
$script:ReResumenPy  = '^([0-9]+)/([0-9]+) pasaron\.$'
$script:ReFinalVerde = '^([0-9]+)/([0-9]+) pasaron\.$'
$script:ReFinalRojo  = '^([0-9]+)/([0-9]+) pasaron\. ([0-9]+) fallaron\.$'
$script:ReMal        = '^    MAL (.+?) / (.*)$'
$script:ReOk         = '^    ok  (.+?) / (.*)$'

# Una fila MAL de Python no separa nombre y detalle sin ambiguedad (correr.py:91): se corta en el
# primer prefijo de detalle conocido (correr.py:16-30, 68, 76).
$script:PrefijosDeDetalle = @('esperado <', 'no contiene <', 'contiene <', 'no esta vacio: <', 'es falso', 'Traceback')


function Split-NombreYDetalle {
    <# `resto` es "<nombre> <detalle>". Devuelve el nombre, o $null si ningun prefijo conocido aparece. #>
    param([string] $Resto)
    $mejor = -1
    foreach ($p in $script:PrefijosDeDetalle) {
        $i = $Resto.IndexOf(' ' + $p, [System.StringComparison]::Ordinal)
        if ($i -ge 0 -and ($mejor -lt 0 -or $i -lt $mejor)) { $mejor = $i }
    }
    if ($mejor -lt 0) { return $null }
    return $Resto.Substring(0, $mejor)
}


function Read-Salida {
    <# Lee un archivo como UTF-8 y extrae lo que 20.4 compara de su region comparable (A1). #>
    param([string] $Ruta)

    $texto = [System.IO.File]::ReadAllText($Ruta, $utf8)
    $todas = @($texto -split "\r?\n")
    $n = $todas.Count

    $o = [pscustomobject]@{
        Ruta      = $Ruta
        HayRegion = $false
        Infra     = @($todas | Where-Object { $_ -cmatch '^INFRA ' })
        Problemas = (New-Object 'System.Collections.Generic.List[string]')
        GruposPs  = (New-Object 'System.Collections.Generic.List[string]')
        GruposPy  = (New-Object 'System.Collections.Generic.List[string]')
        FilasPs   = (New-Object 'System.Collections.Generic.List[string]')
        FallosPs  = (New-Object 'System.Collections.Generic.List[string]')
        FilasPy   = (New-Object 'System.Collections.Generic.List[string]')
        FallosPy  = (New-Object 'System.Collections.Generic.List[string]')
        OkPy      = 0
        Ambiguas  = (New-Object 'System.Collections.Generic.List[string]')
        Ps        = $null
        Py        = $null
        Final     = $null
        Detallado = $false
    }

    # La region: desde la ULTIMA linea que, sin espacios, es exactamente la cabecera.
    $iCab = -1
    for ($i = $n - 1; $i -ge 0; $i--) {
        if ($todas[$i].Trim() -ceq $script:ReCabecera) { $iCab = $i; break }
    }
    if ($iCab -lt 0) {
        $o.Problemas.Add("no hay una linea '$($script:ReCabecera)'")
        return $o
    }
    $o.HayRegion = $true

    $estado = 'ps'; $enFallos = $false; $grupoActual = $null
    $iPySum = -1; $iUltima = -1
    for ($i = $iCab + 1; $i -lt $n; $i++) {
        $l = $todas[$i]
        if ($l.Trim().Length -gt 0) { $iUltima = $i }

        if ($estado -ceq 'ps') {
            if ($l -ceq $script:ReCabeceraPy) { $estado = 'py'; continue }
            if ($l -cmatch $script:ReResumenPs) {
                $f = if ($Matches[3]) { [int]$Matches[3] } else { 0 }
                $o.Ps = [pscustomobject]@{ Ok = [int]$Matches[1]; Total = [int]$Matches[2]; Fallidas = $f }
                $enFallos = $false; $grupoActual = $null
                continue
            }
            if ($enFallos) {
                if ($l -cmatch $script:ReFalloPs) { $o.FallosPs.Add('ps [' + $Matches[1] + '] ' + $Matches[2]) }
                continue
            }
            if ($l -ceq 'Fallos:') { $enFallos = $true; continue }
            if ($l -cmatch $script:ReGrupo) {
                $nombre = $Matches[1]
                if ($Matches[3]) { $malos = [int]$Matches[2]; $cuenta = [int]$Matches[3] }
                else { $malos = 0; $cuenta = [int]$Matches[2] }
                $grupoActual = $nombre
                if ($malos -gt 0) { $o.GruposPs.Add("$nombre ($malos/$cuenta)") } else { $o.GruposPs.Add("$nombre ($cuenta)") }
                continue
            }
            if ($null -ne $grupoActual -and $l -cmatch $script:ReFilaPs) {
                $o.FilasPs.Add('ps [' + $grupoActual + '] ' + $Matches[1])
                continue
            }
        }
        elseif ($estado -ceq 'py') {
            if ($l -cmatch $script:ReResumenPy) {
                $o.Py = [pscustomobject]@{ Ok = [int]$Matches[1]; Total = [int]$Matches[2]; Fallidas = ([int]$Matches[2] - [int]$Matches[1]) }
                $iPySum = $i; $estado = 'post'
                continue
            }
            if ($l -cmatch $script:ReGrupo) {
                if (-not $Matches[3]) { $o.GruposPy.Add($Matches[1] + ' (' + $Matches[2] + ')') }
                continue
            }
            if ($l -cmatch $script:ReMal) {
                $grupo = $Matches[1]; $resto = $Matches[2]
                $nombre = Split-NombreYDetalle $resto
                if ($null -eq $nombre) { $o.Ambiguas.Add($l); continue }
                $o.FallosPy.Add("py $grupo / $nombre")
                $o.FilasPy.Add("py $grupo / $nombre (MAL)")
                continue
            }
            if ($l -cmatch $script:ReOk) {
                $grupo = $Matches[1]; $nombre = $Matches[2]
                if ($nombre.EndsWith(' ')) { $nombre = $nombre.Substring(0, $nombre.Length - 1) }
                $o.FilasPy.Add("py $grupo / $nombre (ok)")
                $o.OkPy++
                continue
            }
        }
    }

    $o.Detallado = ($o.FilasPs.Count -gt 0 -or $o.OkPy -gt 0)

    # La linea final: la ultima no vacia, despues del resumen de Python. Su forma da el exit (16.4).
    if ($iUltima -ge 0 -and $iUltima -ne $iPySum) {
        $u = $todas[$iUltima]
        if ($u -cmatch $script:ReFinalVerde) {
            $o.Final = [pscustomobject]@{ Ok = [int]$Matches[1]; Total = [int]$Matches[2]; Fallidas = 0; Exit = 0 }
        }
        elseif ($u -cmatch $script:ReFinalRojo) {
            $o.Final = [pscustomobject]@{ Ok = [int]$Matches[1]; Total = [int]$Matches[2]; Fallidas = [int]$Matches[3]; Exit = 1 }
        }
    }

    if ($null -eq $o.Ps)    { $o.Problemas.Add('no tiene el resumen de PowerShell (N/M pasaron (PowerShell).)') }
    if ($null -eq $o.Py)    { $o.Problemas.Add('no tiene el resumen de Python (N/M pasaron.)') }
    if ($null -eq $o.Final) { $o.Problemas.Add('no tiene la linea final (N/M pasaron. [K fallaron.])') }
    return $o
}


function New-Contador {
    return New-Object 'System.Collections.Generic.Dictionary[string,int]' ([System.StringComparer]::Ordinal)
}

function Get-Exceso {
    <# Lo que `A` tiene de mas respecto de `B`, como multiconjunto, en el orden de `A`. #>
    param($A, $B)
    $c = New-Contador
    foreach ($x in $B) { if ($c.ContainsKey($x)) { $c[$x] = $c[$x] + 1 } else { $c[$x] = 1 } }
    $res = New-Object 'System.Collections.Generic.List[string]'
    foreach ($x in $A) {
        if ($c.ContainsKey($x) -and $c[$x] -gt 0) { $c[$x] = $c[$x] - 1 } else { $res.Add($x) }
    }
    return ,$res
}

function Format-Lista {
    param($Items, [int] $Max = 8)
    $arr = @($Items)
    $txt = (@($arr | Select-Object -First $Max) -join ', ')
    if ($arr.Count -gt $Max) { $txt += ' (+' + ($arr.Count - $Max) + ' mas)' }
    return $txt
}

function Compare-Conjunto {
    <# Multiconjunto. Devuelve el texto de la diferencia, o $null si no hay. #>
    param($A, $B)
    $soloA = Get-Exceso $A $B
    $soloB = Get-Exceso $B $A
    if ($soloA.Count -eq 0 -and $soloB.Count -eq 0) { return $null }
    return ('solo en serial: ' + $(if ($soloA.Count) { Format-Lista $soloA } else { '(nada)' }) +
            ' | solo en paralelo: ' + $(if ($soloB.Count) { Format-Lista $soloB } else { '(nada)' }))
}

function Compare-Secuencia {
    <# Secuencia ordenada. Si el conjunto difiere dice cuales; si es el mismo con otro orden, donde. #>
    param($A, $B)
    $dif = Compare-Conjunto $A $B
    if ($null -ne $dif) { return $dif }
    $a = @($A); $b = @($B)
    for ($i = 0; $i -lt $a.Count; $i++) {
        if ($a[$i] -cne $b[$i]) {
            return ('mismo conjunto, otro orden; primera diferencia en la posicion ' + ($i + 1) +
                    ': serial ' + $a[$i] + ', paralelo ' + $b[$i])
        }
    }
    return $null
}


function Write-Resultado {
    param([string] $Veredicto, $Lineas, [int] $Exit)
    Write-Host $Veredicto
    foreach ($l in $Lineas) { Write-Host $l }
    exit $Exit
}


try {
    # Las huellas primero: con huellas distintas no hay nada que comparar (VP-I12).
    if ($HuellaSerial -cne $HuellaParalelo) {
        Write-Resultado 'NO_COMPARABLE' @("  motivo: huellas distintas: serial=$HuellaSerial paralelo=$HuellaParalelo") 1
    }

    $rutas = @{}
    foreach ($par in @(@('Serial', $Serial), @('Paralelo', $Paralelo))) {
        if (-not (Test-Path -LiteralPath $par[1] -PathType Leaf)) {
            Write-Resultado 'NO_COMPARABLE' @("  motivo: no se pudo leer -$($par[0]): $($par[1])") 1
        }
        $rutas[$par[0]] = (Resolve-Path -LiteralPath $par[1]).ProviderPath
    }

    $s = Read-Salida $rutas['Serial']
    $p = Read-Salida $rutas['Paralelo']

    $difs    = New-Object 'System.Collections.Generic.List[string]'
    $motivos = New-Object 'System.Collections.Generic.List[string]'

    # NO_COMPARABLE: filas que no se pueden separar, y salidas que no tienen la forma del reporte.
    foreach ($par in @(@('serial', $s), @('paralelo', $p))) {
        foreach ($l in $par[1].Ambiguas) {
            $motivos.Add("fila MAL sin prefijo de detalle conocido (" + $par[0] + "): " + $l.Substring(0, [Math]::Min(160, $l.Length)))
        }
        if ($par[1].Problemas.Count -gt 0) {
            # Un runner con INFRA no necesita tener la forma completa: su INFRA ya lo dice (punto 6).
            if (-not ($par[0] -ceq 'paralelo' -and $par[1].Infra.Count -gt 0)) {
                $motivos.Add("region ilegible (" + $par[0] + "): " + ($par[1].Problemas -join '; '))
            }
        }
    }

    # 1. El exit, de la forma de la linea final.
    if ($null -ne $s.Final -and $null -ne $p.Final -and $s.Final.Exit -ne $p.Final.Exit) {
        $difs.Add('  campo exit: serial=' + $s.Final.Exit + ' paralelo=' + $p.Final.Exit)
    }

    # 2. La secuencia de lineas de grupo, PS y Py.
    if ($s.HayRegion -and $p.HayRegion) {
        $d = Compare-Secuencia $s.GruposPs $p.GruposPs
        if ($null -ne $d) { $difs.Add('  campo grupos-ps: ' + $d) }
        $d = Compare-Secuencia $s.GruposPy $p.GruposPy
        if ($null -ne $d) { $difs.Add('  campo grupos-py: ' + $d) }
    }

    # 3. ok, total y fallidas, por motor y combinados.
    foreach ($c in @(
            @('ps', 'Ps', $s.Ps, $p.Ps), @('py', 'Py', $s.Py, $p.Py), @('', 'Final', $s.Final, $p.Final))) {
        $sufijo = if ($c[0]) { '-' + $c[0] } else { '' }
        if ($null -eq $c[2] -or $null -eq $c[3]) { continue }
        foreach ($campo in @('Ok', 'Total', 'Fallidas')) {
            if ($c[2].$campo -ne $c[3].$campo) {
                $difs.Add('  campo ' + $campo.ToLowerInvariant() + $sufijo + ': serial=' + $c[2].$campo + ' paralelo=' + $c[3].$campo)
            }
        }
    }

    # 4. El multiconjunto de filas fallidas (grupo, nombre), en los dos motores.
    if ($s.HayRegion -and $p.HayRegion) {
        $d = Compare-Conjunto (@($s.FallosPs) + @($s.FallosPy)) (@($p.FallosPs) + @($p.FallosPy))
        if ($null -ne $d) { $difs.Add('  campo filas-fallidas: ' + $d) }
    }

    # 5. Con -Detallado en los dos, el multiconjunto de filas (grupo, nombre, ok).
    $nota = $null
    if ($s.Detallado -and $p.Detallado) {
        $d = Compare-Conjunto (@($s.FilasPs) + @($s.FilasPy)) (@($p.FilasPs) + @($p.FilasPy))
        if ($null -ne $d) { $difs.Add('  campo filas: ' + $d) }
    }
    elseif ($s.Detallado -ne $p.Detallado) {
        $nota = '  nota: solo ' + $(if ($s.Detallado) { 'el oraculo' } else { 'el runner' }) + ' corrio con -Detallado: las filas no se comparan'
    }

    # 6. El runner no tiene INFRA.
    if ($p.Infra.Count -gt 0) {
        $difs.Add('  campo infra: el runner tiene ' + $p.Infra.Count + ' linea(s) INFRA: ' + (Format-Lista $p.Infra 5))
    }

    if ($motivos.Count -gt 0) {
        $lineas = @($motivos | ForEach-Object { '  motivo: ' + $_ })
        $lineas += @($difs | ForEach-Object { '  ademas' + $_.Substring(1) })
        Write-Resultado 'NO_COMPARABLE' $lineas 1
    }
    if ($difs.Count -gt 0) { Write-Resultado 'NO_EQUIVALENTE' $difs 1 }

    $ok = @("  comparado: " + $s.GruposPs.Count + ' grupos PS, ' + $s.GruposPy.Count + ' grupos Py, ' +
            $s.Final.Ok + '/' + $s.Final.Total + ' pasaron, exit ' + $s.Final.Exit)
    if ($null -ne $nota) { $ok += $nota }
    Write-Resultado 'EQUIVALENTE' $ok 0
}
catch {
    # Una excepcion nunca es EQUIVALENTE.
    Write-Host 'NO_COMPARABLE'
    Write-Host ('  motivo: error interno del comparador: ' + $_.Exception.Message)
    exit 1
}
