<#
.SYNOPSIS
    Instala, actualiza y desinstala el harness GCBA en un proyecto.

.DESCRIPTION
    Punto de entrada único del harness. La invariante que ordena todo lo demás:

        .claude\ es 100% regenerable y va gitignoreado.
        CLAUDE.md no lo es y se versiona.

    De ahí se deduce el resto: nada de lo que este script escribe en .claude\ necesita
    sobrevivir a un git clone, solo a un -Update.

.PARAMETER Doctor
    Revisa que la máquina esté en condiciones y reporta el estado de un proyecto.
    No escribe absolutamente nada.

.PARAMETER Project
    Ruta del proyecto sobre el que operar.

.PARAMETER Harness
    Uno o más harness a instalar. Se pueden combinar: -Harness analisis,desarrollo

.PARAMETER Update
    Trae los cambios del repo sin pisar lo que hayas editado a mano.

.PARAMETER Uninstall
    Saca el harness. Deja los backups y tu harness.config.json.

.EXAMPLE
    .\install.ps1 -Doctor
    .\install.ps1 -Project C:\Work\GCBA\IGE -Harness analisis -WhatIf
    .\install.ps1 -Project C:\Work\GCBA\IGE -Harness analisis
    .\install.ps1 -Project C:\Work\GCBA\IGE -Update
    .\install.ps1 -Project C:\Work\GCBA\IGE -Uninstall
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]   $Project,
    [string[]] $Harness = @(),
    [string]   $Usuario,
    [switch]   $Update,
    [switch]   $Uninstall,
    [switch]   $Doctor
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$utf8 = New-Object System.Text.UTF8Encoding $false
try { [Console]::OutputEncoding = $utf8 } catch { }

$script:Repo    = $PSScriptRoot
$script:Version = (Get-Content (Join-Path $script:Repo 'VERSION') -Raw).Trim()

# La definición de las zonas del CLAUDE.md vive en un solo lado. El instalador las crea y
# el check las mide, y los dos leen de acá.
Import-Module (Join-Path $script:Repo 'comun\hooks\lib\Zonas.psm1') -Force

# Marcadores de los bloques que el instalador administra dentro de archivos que también
# edita el humano. Todo lo que está entre ellos es del harness; el resto es intocable.
$script:MarcaClaudeIni = '<!-- HARNESS:COMUN — generado por install.ps1. No editar: -Update lo reemplaza. -->'
$script:MarcaClaudeFin = '<!-- /HARNESS:COMUN -->'
$script:MarcaGitIni    = '# >>> gcba-harness — no editar a mano'
$script:MarcaGitFin    = '# <<< gcba-harness'


# ── Utilidades ──────────────────────────────────────────────────────────────────

function Escribir     { param([string]$T) Write-Host $T }
function EscribirOk   { param([string]$T) Write-Host ('  OK    ' + $T) -ForegroundColor Green }
function EscribirAviso{ param([string]$T) Write-Host ('  AVISO ' + $T) -ForegroundColor Yellow }
function EscribirMal  { param([string]$T) Write-Host ('  FALLA ' + $T) -ForegroundColor Red }
function EscribirPaso { param([string]$T) Write-Host ('  ->    ' + $T) -ForegroundColor DarkGray }


function Write-TextoUtf8 {
    <# Escribe siempre UTF-8 sin BOM. Set-Content de PS 5.1 usa la codepage ANSI. #>
    param([string] $Ruta, [string] $Texto)

    $dir = Split-Path -Parent $Ruta
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Ruta, $Texto, (New-Object System.Text.UTF8Encoding $false))
}


function Read-TextoUtf8 {
    param([string] $Ruta)
    return [System.IO.File]::ReadAllText($Ruta, (New-Object System.Text.UTF8Encoding $false))
}


function ConvertTo-JsonTexto {
    <# ConvertTo-Json con -Depth explícito. El default de PS 5.1 es 2 y trunca en silencio. #>
    param($Objeto)
    return (ConvertTo-Json -InputObject $Objeto -Depth 20)
}


function Get-Sha256Archivo {
    param([string] $Ruta)
    if (-not (Test-Path $Ruta)) { return '' }
    return (Get-FileHash -Path $Ruta -Algorithm SHA256).Hash
}


function Read-Manifiesto {
    <# Lee y valida un manifest.json. Es el mismo contrato para comun y para cada harness. #>
    param([string] $Directorio)

    $ruta = Join-Path $Directorio 'manifest.json'
    if (-not (Test-Path $ruta)) { throw "falta manifest.json en $Directorio" }

    $m = Read-TextoUtf8 $ruta | ConvertFrom-Json

    foreach ($campo in @('id', 'descripcion', 'requiereClaudeCode')) {
        if (-not $m.PSObject.Properties[$campo]) {
            throw "manifest.json de $Directorio no declara '$campo'"
        }
    }
    return $m
}


function Get-HarnessDisponibles {
    <#
    .NOTES
        Devuelve con la coma adelante a propósito: sin eso, PowerShell desenvuelve un
        array vacío a $null y uno de un solo elemento a un escalar. Con Set-StrictMode
        2.0, pedirle .Count a cualquiera de los dos es un error terminante.
    #>
    $dir = Join-Path $script:Repo 'harnesses'
    if (-not (Test-Path $dir)) { return ,@() }

    $ids = @(Get-ChildItem $dir -Directory |
             Where-Object { Test-Path (Join-Path $_.FullName 'manifest.json') } |
             Select-Object -ExpandProperty Name)
    return ,$ids
}


function Set-BloqueMarcado {
    <#
    .SYNOPSIS
        Inserta o reemplaza un bloque delimitado dentro de un archivo, sin tocar el resto.
    .DESCRIPTION
        Idempotente: correrlo N veces deja el archivo igual que correrlo una.
        Es la razón por la que el bloque se inyecta en vez de importarse: un import roto
        pierde reglas en silencio, un bloque marcado se ve y se grepea.
    #>
    param(
        [string] $Ruta,
        [string] $MarcaIni,
        [string] $MarcaFin,
        [string] $Contenido,
        [string] $Encabezado = ''
    )

    $bloque = $MarcaIni + "`r`n" + $Contenido.TrimEnd() + "`r`n" + $MarcaFin

    if (-not (Test-Path $Ruta)) {
        $texto = ''
        if ($Encabezado) { $texto = $Encabezado + "`r`n`r`n" }
        Write-TextoUtf8 -Ruta $Ruta -Texto ($texto + $bloque + "`r`n")
        return 'creado'
    }

    $actual = Read-TextoUtf8 $Ruta
    $iIni = $actual.IndexOf($MarcaIni)
    $iFin = $actual.IndexOf($MarcaFin)

    if ($iIni -ge 0 -and $iFin -gt $iIni) {
        $antes   = $actual.Substring(0, $iIni)
        $despues = $actual.Substring($iFin + $MarcaFin.Length)
        Write-TextoUtf8 -Ruta $Ruta -Texto ($antes + $bloque + $despues)
        return 'reemplazado'
    }

    # No estaba: se agrega al final, para no desplazar lo que el humano puso arriba.
    $sep = "`r`n`r`n"
    if ($actual.EndsWith("`n")) { $sep = "`r`n" }
    Write-TextoUtf8 -Ruta $Ruta -Texto ($actual + $sep + $bloque + "`r`n")
    return 'agregado'
}


function Remove-BloqueMarcado {
    param([string] $Ruta, [string] $MarcaIni, [string] $MarcaFin)

    if (-not (Test-Path $Ruta)) { return $false }

    $actual = Read-TextoUtf8 $Ruta
    $iIni = $actual.IndexOf($MarcaIni)
    $iFin = $actual.IndexOf($MarcaFin)
    if ($iIni -lt 0 -or $iFin -le $iIni) { return $false }

    $nuevo = $actual.Substring(0, $iIni) + $actual.Substring($iFin + $MarcaFin.Length)
    Write-TextoUtf8 -Ruta $Ruta -Texto $nuevo.TrimEnd() + "`r`n"
    return $true
}


function Get-BloqueZonaCompleto {
    <# Extrae una zona entera, marcadores incluidos, de un texto. #>
    param([string] $Texto, $Zona)

    $nombres = @($Zona.Nombre)
    if ($Zona.PSObject.Properties['Alias'] -and $Zona.Alias) { $nombres += $Zona.Alias }

    foreach ($n in $nombres) {
        $iIni = $Texto.IndexOf('<!-- ' + $n)
        if ($iIni -lt 0) { continue }
        $marcaFin = '<!-- /' + $n + ' -->'
        $iFin = $Texto.IndexOf($marcaFin, $iIni)
        if ($iFin -lt 0) { continue }
        return $Texto.Substring($iIni, $iFin + $marcaFin.Length - $iIni)
    }
    return $null
}


function Add-ZonasSiFaltan {
    <#
    .SYNOPSIS
        Agrega al CLAUDE.md las zonas que no tenga, vacías, desde la plantilla.
    .DESCRIPTION
        Solo agrega lo que falta. Una zona que ya existe NO se toca nunca, ni en
        -Update: adentro está el trabajo de alguien.

        Si el archivo trae una zona escrita con otro nombre —un `<!-- CACHÉ -->` en vez
        del `<!-- ZONA CACHÉ -->` canónico— la zona canónica NO se agrega: hacerlo
        dejaría el archivo con dos, una con el contenido real y otra vacía, y el check
        mediría la vacía. Se avisa y se deja el archivo como está, para que la persona
        renombre el marcador.

        Ya pasó, y pasó en silencio, al instalar sobre el CLAUDE.md del IGE.
    .OUTPUTS
        Agregadas (nombres) y NoReconocidas (marcador y la zona a la que se parece).
    #>
    param([string] $RutaClaudeMd, [string] $RutaPlantilla)

    $vacio = [pscustomobject]@{ Agregadas = @(); NoReconocidas = @() }
    if (-not (Test-Path $RutaPlantilla)) { return $vacio }

    $plantilla = Read-TextoUtf8 $RutaPlantilla
    $actual    = Read-TextoUtf8 $RutaClaudeMd
    $agregadas = @()

    # Sin @() a proposito. Estas funciones devuelven la coleccion como UN objeto -es lo
    # que hace `return ,$x`, y es lo que evita que un resultado vacio se desenvuelva a
    # $null- asi que envolverla otra vez da un arreglo de un elemento que es la
    # coleccion entera. Se asigna derecho y se recorre con foreach o con la tuberia.
    $raras   = Find-ZonasNoReconocidas -Texto $actual
    $tomadas = @($raras | Where-Object { $_.Parecida } | Select-Object -ExpandProperty Parecida)

    foreach ($zona in (Get-DefinicionZonas)) {
        if ($null -ne (Get-ContenidoZona -Texto $actual -Zona $zona)) { continue }
        if ($tomadas -contains $zona.Nombre) { continue }

        $bloque = Get-BloqueZonaCompleto -Texto $plantilla -Zona $zona
        if (-not $bloque) { continue }

        $actual = $actual.TrimEnd() + "`r`n`r`n" + $bloque + "`r`n"
        $agregadas += $zona.Nombre
    }

    if ($agregadas.Count -gt 0) { Write-TextoUtf8 -Ruta $RutaClaudeMd -Texto $actual }
    return [pscustomobject]@{ Agregadas = @($agregadas); NoReconocidas = $raras }
}


function Remove-ZonasVacias {
    <#
    .SYNOPSIS
        Al desinstalar, saca las zonas que quedaron vacías y deja las que tienen algo.
    .DESCRIPTION
        Una zona vacía es andamiaje que el instalador puso y nadie usó: dejarla es basura.
        Una zona con contenido es trabajo de alguien: borrarla sería destruirlo.

        La diferencia la marca el contenido real, ignorando los marcadores de posición de
        la plantilla — los encabezados vacíos y las líneas entre paréntesis bajos.
    #>
    param([string] $RutaClaudeMd)

    if (-not (Test-Path $RutaClaudeMd)) { return ,@() }

    $texto   = Read-TextoUtf8 $RutaClaudeMd
    $sacadas = @()

    foreach ($zona in (Get-DefinicionZonas)) {
        $contenido = Get-ContenidoZona -Texto $texto -Zona $zona
        if ($null -eq $contenido) { continue }

        $utiles = @($contenido -split "`n" | Where-Object {
            $l = $_.Trim()
            $l -and $l -notmatch '^#' -and $l -notmatch '^_\(' -and $l -notmatch '^\|'
        })
        if ($utiles.Count -gt 0) { continue }

        $bloque = Get-BloqueZonaCompleto -Texto $texto -Zona $zona
        if ($bloque) {
            $texto = $texto.Replace($bloque, '')
            $sacadas += $zona.Nombre
        }
    }

    if ($sacadas.Count -gt 0) {
        $texto = [regex]::Replace($texto, "(\r?\n){3,}", "`r`n`r`n")
        Write-TextoUtf8 -Ruta $RutaClaudeMd -Texto ($texto.TrimEnd() + "`r`n")
    }
    return ,$sacadas
}


function Copy-Arbol {
    <#
    .SYNOPSIS
        Copia un directorio y devuelve las rutas de destino, para el lockfile.
    .NOTES
        Las variables locales llevan prefijo a propósito. PowerShell NO distingue
        mayúsculas en nombres de variables: un `$destino = ...` adentro del bucle pisa
        el parámetro `$Destino`, y a partir de la segunda vuelta las rutas se anidan
        una adentro de otra. Costó encontrarlo.
    #>
    param([string] $Origen, [string] $Destino)

    $copiados = New-Object System.Collections.ArrayList
    if (-not (Test-Path $Origen)) { return ,$copiados }

    $archivos = @(Get-ChildItem $Origen -Recurse -File |
                  Where-Object { $_.Name -ne '.gitkeep' })

    foreach ($a in $archivos) {
        $relArchivo = $a.FullName.Substring($Origen.Length).TrimStart('\')
        $rutaFinal  = Join-Path $Destino $relArchivo
        $dirPadre   = Split-Path -Parent $rutaFinal
        if (-not (Test-Path $dirPadre)) {
            New-Item -ItemType Directory -Path $dirPadre -Force | Out-Null
        }
        Copy-Item -Path $a.FullName -Destination $rutaFinal -Force
        [void] $copiados.Add($rutaFinal)
    }
    return ,$copiados
}


# ── Entorno ─────────────────────────────────────────────────────────────────────

function Get-VersionClaudeCode {
    try {
        $salida = (& claude --version 2>$null | Out-String).Trim()
        if ($salida -match '(\d+)\.(\d+)\.(\d+)') { return $Matches[0] }
    } catch { }
    return ''
}


function Test-VersionMinima {
    param([string] $Actual, [string] $Minima)
    if (-not $Actual) { return $false }
    try {
        return ([version]$Actual -ge [version]$Minima)
    } catch { return $false }
}


function Test-Entorno {
    <# Devuelve una lista de hallazgos: Nivel = ok | aviso | falla #>
    $h = New-Object System.Collections.ArrayList

    $psv = $PSVersionTable.PSVersion.ToString()
    if ($PSVersionTable.PSVersion.Major -ge 5) {
        [void] $h.Add(@{ Nivel='ok'; Texto="PowerShell $psv" })
    } else {
        [void] $h.Add(@{ Nivel='falla'; Texto="PowerShell $psv — hace falta 5.1 o superior" })
    }

    $manifiestoComun = Read-Manifiesto (Join-Path $script:Repo 'comun')
    $vcc = Get-VersionClaudeCode
    if (-not $vcc) {
        [void] $h.Add(@{ Nivel='aviso'; Texto="no se pudo determinar la versión de Claude Code (¿está en el PATH?)" })
    } elseif (Test-VersionMinima -Actual $vcc -Minima $manifiestoComun.requiereClaudeCode) {
        [void] $h.Add(@{ Nivel='ok'; Texto="Claude Code $vcc (mínimo $($manifiestoComun.requiereClaudeCode))" })
    } else {
        [void] $h.Add(@{ Nivel='falla'; Texto="Claude Code $vcc es anterior al mínimo $($manifiestoComun.requiereClaudeCode)" })
    }

    # ExecutionPolicy: el riesgo número uno de este harness en máquinas con GPO.
    try {
        $politicas = Get-ExecutionPolicy -List
        $maquina = ($politicas | Where-Object { $_.Scope -eq 'MachinePolicy' }).ExecutionPolicy
        if ($maquina -eq 'AllSigned') {
            [void] $h.Add(@{ Nivel='falla'; Texto="ExecutionPolicy de máquina = AllSigned. Los hooks no van a poder ejecutarse." })
        } else {
            [void] $h.Add(@{ Nivel='ok'; Texto="ExecutionPolicy de máquina = $maquina" })
        }
    } catch {
        [void] $h.Add(@{ Nivel='aviso'; Texto='no se pudo leer ExecutionPolicy' })
    }

    # Mark-of-the-Web: pasa cuando el repo se bajó como ZIP en vez de clonarse.
    $bloqueados = @(Get-ChildItem $script:Repo -Recurse -Include '*.ps1','*.psm1' -ErrorAction SilentlyContinue |
                    Where-Object { Get-Item $_.FullName -Stream 'Zone.Identifier' -ErrorAction SilentlyContinue })
    if ($bloqueados.Count -gt 0) {
        [void] $h.Add(@{ Nivel='falla'; Texto="$($bloqueados.Count) script(s) con Mark-of-the-Web. Cloná el repo en vez de bajarlo como ZIP, o corré Unblock-File." })
    } else {
        [void] $h.Add(@{ Nivel='ok'; Texto='ningún script bloqueado por Mark-of-the-Web' })
    }

    # Sin @() a propósito: la función ya devuelve con la coma adelante, y envolver de
    # nuevo produce un array adentro de un array.
    $disponibles = Get-HarnessDisponibles
    if ($disponibles.Count -gt 0) {
        [void] $h.Add(@{ Nivel='ok'; Texto="harness disponibles: $($disponibles -join ', ')" })
    } else {
        [void] $h.Add(@{ Nivel='aviso'; Texto='todavía no hay ningún harness en harnesses/' })
    }

    return ,$h
}


# ── Generación de artefactos ────────────────────────────────────────────────────

function Resolve-Python {
    <#
    .SYNOPSIS
        Devuelve la ruta del python.exe REAL, o $null.
    .DESCRIPTION
        Se pide sys.executable y no se usa lo que haya en el PATH: en una máquina con
        PyManager, `python` es un shim que cuesta 260 ms de más en CADA hook.

        NOTA: versión mínima trasplantada por la Task 8/9/12 para que el instalador
        siga funcionando apenas los hooks pasan a Python — el borrado de los .ps1 no
        puede dejar el shim apuntando a un archivo que ya no existe. La Task 10 es la
        dueña del diseño completo: resolución cacheada, versión mínima de Python
        (Test-Entorno), shim POSIX y la migración de Zonas.psm1 a JSON. Esta función
        se limita a lo mínimo indispensable para no romper -Project/-Update, y se
        espera que la Task 10 la reemplace o la reconcilie.
    #>
    foreach ($c in @('python', 'py', 'python3')) {
        try {
            $ruta = (& $c -c "import sys; print(sys.executable)" 2>$null)
            if ($ruta -and (Test-Path $ruta)) { return $ruta.Trim() }
        } catch { }
    }
    return $null
}


function New-Shim {
    <#
    .SYNOPSIS
        Escribe el lanzador de hooks. Único artefacto que depende de esta máquina.
    .DESCRIPTION
        -NoProfile no es opcional: si el $PROFILE de quien instala imprime algo, ese
        texto se mezcla con el JSON de stdout y el hook falla de una forma que nadie
        asocia a su perfil de PowerShell.

        Los hooks son Python desde la Task 8: el shim invoca el intérprete real, no
        "python" a secas (ver Resolve-Python). El resto del diseño -shim POSIX,
        versión mínima- es de la Task 10.
    #>
    param([string] $Ruta, [string] $Python)

    $cmd = @"
@echo off
rem Generado por install.ps1 del harness GCBA. Se regenera en cada -Update.
rem Es el unico archivo del harness que contiene una ruta absoluta de esta maquina.
"$Python" "%~dp0hooks\%1.py"
"@

    # Los .cmd necesitan CRLF.
    $cmd = ($cmd -replace "`r?`n", "`r`n")
    [System.IO.File]::WriteAllText($Ruta, $cmd, (New-Object System.Text.UTF8Encoding $false))
}


function New-SettingsProyecto {
    <# Combina permisos + registro de hooks en el settings.json del proyecto. #>
    param([string] $RutaSettings)

    $deny = (Read-TextoUtf8 (Join-Path $script:Repo 'comun\settings\permissions.deny.json')) | ConvertFrom-Json

    # El comando nunca lleva una ruta absoluta: se resuelve contra el proyecto. Va entre
    # comillas porque $CLAUDE_PROJECT_DIR puede expandirse a una ruta con espacios.
    #
    # El reemplazo se hace sobre el TEXTO de la plantilla, con las comillas escapadas
    # como JSON. Hacerlo después de serializar mete comillas crudas adentro de un string
    # y rompe el archivo.
    $shimEscapado = '\"$CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd\"'
    $textoPlantilla = Read-TextoUtf8 (Join-Path $script:Repo 'comun\settings\hooks.plantilla.json')
    $hooks = ($textoPlantilla.Replace('{{SHIM}}', $shimEscapado) | ConvertFrom-Json)

    $settings = [ordered]@{
        '$comentario' = "Generado por gcba-harness v$($script:Version). Se regenera en cada -Update."
        permissions   = $deny.permissions
        hooks         = $hooks.hooks
    }

    Write-TextoUtf8 -Ruta $RutaSettings -Texto (ConvertTo-JsonTexto $settings)
}


function Get-UsuarioDeConfig {
    <# Lee el nombre ya configurado, si lo hay. #>
    param([string] $Ruta)

    if (-not (Test-Path $Ruta)) { return '' }
    try {
        $c = Read-TextoUtf8 $Ruta | ConvertFrom-Json
        if ($c.PSObject.Properties['usuario']) { return [string]$c.usuario }
    } catch { }
    return ''
}


function Resolve-Usuario {
    <#
    .SYNOPSIS
        Determina con qué nombre tratar a quien usa el harness.
    .DESCRIPTION
        Orden: lo que ya está configurado, después -Usuario, después preguntar.

        Si no hay consola interactiva y no vino por parámetro, falla con instrucciones
        en vez de inventar un default. Un instalador que se cuelga esperando una
        respuesta que nadie puede dar es peor que uno que aborta explicando.
    #>
    param([string] $RutaConfig, [string] $Provisto)

    $yaConfigurado = Get-UsuarioDeConfig -Ruta $RutaConfig
    if ($yaConfigurado) { return $yaConfigurado }

    if ($Provisto) { return $Provisto.Trim() }

    if ([Console]::IsInputRedirected) {
        throw "falta -Usuario. Este harness te trata por tu nombre, y no hay consola para preguntarlo. Agregá: -Usuario 'Tu Nombre'"
    }

    Escribir ''
    Write-Host '  El harness te va a tratar por tu nombre.' -ForegroundColor Cyan
    $respuesta = ''
    while (-not $respuesta) {
        $respuesta = (Read-Host '  ¿Cómo te llamás?').Trim()
        if (-not $respuesta) { Write-Host '  Hace falta un nombre.' -ForegroundColor Yellow }
    }
    return $respuesta
}


function New-ConfigProyecto {
    <#
    .SYNOPSIS
        Crea harness.config.json SOLO si no existe. Si existe, no se toca jamás.
    .DESCRIPTION
        Es el archivo del humano. Es donde se disiente de un default del harness —
        por ejemplo el nombre de la rama, que tiene tres variantes en la norma.
    #>
    param([string] $Ruta, $Manifiestos, [string] $Usuario)

    if (Test-Path $Ruta) { return $false }

    $config = [ordered]@{
        '$comentario' = 'Tus ajustes. El harness no pisa este archivo nunca, ni en -Update.'
        usuario       = $Usuario
    }
    foreach ($m in $Manifiestos) {
        if ($m.PSObject.Properties['config']) {
            foreach ($p in $m.config.PSObject.Properties) {
                if (-not $config.Contains($p.Name)) { $config[$p.Name] = $p.Value }
            }
        }
    }

    Write-TextoUtf8 -Ruta $Ruta -Texto (ConvertTo-JsonTexto $config)
    return $true
}


function Test-HooksInstalados {
    <#
    .SYNOPSIS
        Dispara los cuatro hooks instalados con payloads reales y verifica su respuesta.
    .DESCRIPTION
        Un hook roto es PEOR que ningún hook, porque falla en silencio. Por eso esto no
        es opcional: si algún hook no responde bien, la instalación falla y revierte.
    #>
    param([string] $DirHarness)

    $shim = Join-Path $DirHarness 'run-hook.cmd'
    $casos = @(
        @{ Hook='session-start';      Payload='session-start.json' },
        @{ Hook='user-prompt-submit'; Payload='user-prompt-submit.json' },
        @{ Hook='pre-tool-use';       Payload='pre-tool-use-write.json' },
        @{ Hook='post-tool-use';      Payload='post-tool-use-write.json' }
    )

    $problemas = New-Object System.Collections.ArrayList

    foreach ($c in $casos) {
        $rutaPayload = Join-Path $script:Repo ('tests\payloads\' + $c.Payload)
        if (-not (Test-Path $rutaPayload)) { continue }
        $json = Read-TextoUtf8 $rutaPayload

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName               = $shim
        $psi.Arguments              = $c.Hook
        $psi.UseShellExecute        = $false
        $psi.RedirectStandardInput  = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding $false
        $psi.StandardErrorEncoding  = New-Object System.Text.UTF8Encoding $false

        try {
            $p = [System.Diagnostics.Process]::Start($psi)
            $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream,
                                                   (New-Object System.Text.UTF8Encoding $false))
            $w.Write($json); $w.Flush(); $w.Close()
            $salida = $p.StandardOutput.ReadToEnd()
            $p.StandardError.ReadToEnd() | Out-Null
            $p.WaitForExit()

            if ($p.ExitCode -ne 0) {
                [void] $problemas.Add("$($c.Hook): salió con código $($p.ExitCode)")
                continue
            }
            if ($salida.Trim()) {
                try { $salida | ConvertFrom-Json | Out-Null }
                catch { [void] $problemas.Add("$($c.Hook): la salida no es JSON válido") }
            }
        }
        catch {
            [void] $problemas.Add("$($c.Hook): no se pudo ejecutar — $($_.Exception.Message)")
        }
    }

    return ,$problemas
}


# ── Operaciones ─────────────────────────────────────────────────────────────────

function Invoke-Doctor {
    Escribir ''
    Escribir "gcba-harness v$($script:Version) — doctor"
    Escribir ''

    $fallas = 0
    foreach ($x in (Test-Entorno)) {
        switch ($x.Nivel) {
            'ok'    { EscribirOk    $x.Texto }
            'aviso' { EscribirAviso $x.Texto }
            'falla' { EscribirMal   $x.Texto; $fallas++ }
        }
    }

    if ($Project) {
        Escribir ''
        Escribir "Proyecto: $Project"
        if (-not (Test-Path $Project)) {
            EscribirMal 'no existe'
            $fallas++
        } else {
            $lock = Join-Path $Project '.claude\harness.lock.json'
            if (Test-Path $lock) {
                $d = Read-TextoUtf8 $lock | ConvertFrom-Json
                EscribirOk "harness instalado: $($d.harness -join ', ') (v$($d.version))"

                if ($d.version -ne $script:Version) {
                    EscribirAviso "el proyecto está en v$($d.version) y el repo en v$($script:Version). Corré -Update."
                }

                # Deriva: archivos editados a mano después de instalar.
                $derivados = @()
                foreach ($a in $d.archivos) {
                    $ruta = Join-Path $Project $a.ruta
                    if (-not (Test-Path $ruta)) { $derivados += ($a.ruta + ' (borrado)'); continue }
                    if ((Get-Sha256Archivo $ruta) -ne $a.sha256) { $derivados += $a.ruta }
                }
                if ($derivados.Count -gt 0) {
                    EscribirAviso "$($derivados.Count) archivo(s) editados a mano; -Update no los va a pisar:"
                    foreach ($x in $derivados) { EscribirPaso $x }
                } else {
                    EscribirOk 'ningún archivo del harness fue editado a mano'
                }
            } else {
                EscribirAviso 'no tiene el harness instalado'
            }

            if (Test-Path (Join-Path $Project '.git')) {
                EscribirOk 'está bajo control de versiones'
            } else {
                EscribirAviso 'no está bajo control de versiones: no hay diff ni vuelta atrás'
            }

            # Reparse points: alguien reemplazó la copia por un junction y git se lo va a tragar.
            $dirClaude = Join-Path $Project '.claude'
            if (Test-Path $dirClaude) {
                $enlaces = @(Get-ChildItem $dirClaude -Recurse -Force -ErrorAction SilentlyContinue |
                             Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
                if ($enlaces.Count -gt 0) {
                    EscribirMal "hay $($enlaces.Count) enlace(s) bajo .claude\. Git los recorre y versiona su contenido — ver ADR-0002."
                    $fallas++
                }
            }
        }
    }

    # Los subagentes globales sin tools declaradas. Fuera del alcance del harness, pero
    # se listan porque nadie más los mira.
    $dirAgentes = Join-Path $env:USERPROFILE '.claude\agents'
    if (Test-Path $dirAgentes) {
        $sueltos = @(Get-ChildItem $dirAgentes -Filter '*.md' -File | Where-Object {
            $t = Read-TextoUtf8 $_.FullName
            -not ($t -match '(?m)^tools:')
        })
        if ($sueltos.Count -gt 0) {
            Escribir ''
            EscribirAviso "$($sueltos.Count) subagente(s) globales sin 'tools:' declaradas — heredan escritura y ejecución total:"
            EscribirPaso (($sueltos | Select-Object -ExpandProperty BaseName) -join ', ')
            EscribirPaso 'Ver UPGRADE.md. El harness no los toca.'
        }
    }

    Escribir ''
    if ($fallas -eq 0) {
        Write-Host '  Todo en orden.' -ForegroundColor Green
        return 0
    }
    Write-Host "  $fallas problema(s) que hay que resolver antes de instalar." -ForegroundColor Red
    return 1
}


function Invoke-Instalar {
    param([string[]] $Ids)

    Escribir ''
    Escribir "gcba-harness v$($script:Version) — instalar"
    Escribir ''

    # 1. Precondiciones. Se aborta, no se repara.
    $fallas = @(Test-Entorno | Where-Object { $_.Nivel -eq 'falla' })
    if ($fallas.Count -gt 0) {
        foreach ($f in $fallas) { EscribirMal $f.Texto }
        throw 'la máquina no está en condiciones. Corré -Doctor.'
    }
    if (-not (Test-Path $Project)) { throw "el proyecto no existe: $Project" }

    # -Harness analisis,desarrollo se parte solo en una sesión interactiva: ahí el parser
    # de PowerShell arma el array. Invocado con -File —desde un .cmd, desde CI, desde otro
    # script— el mismo texto llega como UNA cadena literal y el harness "analisis,desarrollo"
    # no existe. Se normaliza acá para que las dos vías se comporten igual.
    $Ids = @($Ids | ForEach-Object { $_ -split ',' } |
                    ForEach-Object { $_.Trim() } |
                    Where-Object { $_ })

    # Instalar es ADITIVO: lo que el proyecto ya tenía se conserva. Sin esto, agregar el
    # segundo harness reemplaza el bloque del CLAUDE.md y el lockfile con el conjunto nuevo,
    # y los archivos del primero quedan en disco fuera del inventario — invisibles para
    # -Doctor y para -Uninstall. Y falla en silencio, que es la peor forma de fallar.
    #
    # Es el caso que el README anticipa: un repo de relevamiento que recibe su primer código
    # meses después. Ese camino es incremental por naturaleza.
    #
    # Para quedarse con un conjunto exacto, el camino es -Uninstall y volver a instalar.
    $heredados = @()
    $rutaLockPrevio = Join-Path $Project '.claude\harness.lock.json'
    if (Test-Path $rutaLockPrevio) {
        $lockPrevio = Read-TextoUtf8 $rutaLockPrevio | ConvertFrom-Json
        if ($lockPrevio.PSObject.Properties['harness']) {
            $heredados = @($lockPrevio.harness |
                           Where-Object { $_ -and $_ -ne 'comun' -and $Ids -notcontains $_ })
        }
    }
    if ($heredados.Count -gt 0) {
        $Ids = @($Ids) + $heredados
        EscribirOk ("se conserva lo ya instalado: " + ($heredados -join ', '))
    }

    # Orden canónico, no orden de instalación. Llegar al mismo conjunto instalando los dos
    # juntos o agregando uno después tiene que producir el mismo archivo: si el orden
    # dependiera del camino, el bloque del CLAUDE.md cambiaría de orden solo, y un -Update
    # generaría un diff que no corresponde a ningún cambio real.
    $Ids = @($Ids | Sort-Object)

    # Sin @() a propósito: la función ya devuelve con la coma adelante, y envolver de
    # nuevo produce un array adentro de un array.
    $disponibles = Get-HarnessDisponibles
    foreach ($id in $Ids) {
        if ($disponibles -notcontains $id) {
            throw "no existe el harness '$id'. Disponibles: $($disponibles -join ', ')"
        }
    }

    $manifiestos = @(Read-Manifiesto (Join-Path $script:Repo 'comun'))
    foreach ($id in $Ids) {
        $manifiestos += Read-Manifiesto (Join-Path $script:Repo "harnesses\$id")
    }

    # Prefijos disjuntos: es lo que hace imposible que dos harness colisionen.
    $prefijos = @($manifiestos | Where-Object { $_.PSObject.Properties['prefijo'] -and $_.prefijo } |
                  Select-Object -ExpandProperty prefijo)
    $repetidos = @($prefijos | Group-Object | Where-Object { $_.Count -gt 1 })
    if ($repetidos.Count -gt 0) {
        throw "hay prefijos repetidos entre los harness pedidos: $(($repetidos | Select-Object -ExpandProperty Name) -join ', ')"
    }

    EscribirOk ("se va a instalar: " + (@('comun') + $Ids -join ', '))

    $dirClaude  = Join-Path $Project '.claude'
    $dirHarness = Join-Path $dirClaude 'harness'
    $sello      = Get-Date -Format 'yyyyMMdd-HHmmss'
    $dirBackup  = Join-Path $dirClaude ('.harness-backup\' + $sello)
    $rutaConfigExistente = Join-Path $dirClaude 'harness.config.json'

    if (-not $PSCmdlet.ShouldProcess($Project, "instalar gcba-harness v$($script:Version)")) {
        Escribir ''
        Escribir '  Se escribiría:'
        EscribirPaso ".claude\settings.json"
        EscribirPaso ".claude\harness\  (hooks, reglas, checks, manifiestos)"
        EscribirPaso ".claude\skills\ y .claude\agents\"
        EscribirPaso ".claude\harness.lock.json"
        EscribirPaso ".claude\harness.config.json  (solo si no existe)"
        EscribirPaso "CLAUDE.md  (solo el bloque marcado)"
        EscribirPaso ".gitignore (solo el bloque marcado)"
        EscribirPaso "backup de lo que se pise en $dirBackup"
        Escribir ''
        return 0
    }

    # 2. El nombre, antes de tocar un solo archivo. Va después del corte de -WhatIf a
    # propósito: -WhatIf no escribe nada, así que no puede exigir nada.
    $nombreUsuario = Resolve-Usuario -RutaConfig $rutaConfigExistente -Provisto $Usuario

    # 3. Backup de todo lo que se pueda pisar. Nunca se borra, ni al desinstalar.
    $aRespaldar = @('.claude\settings.json', 'CLAUDE.md', '.gitignore')
    $huboBackup = $false
    foreach ($rel in $aRespaldar) {
        $origen = Join-Path $Project $rel
        if (Test-Path $origen) {
            $destino = Join-Path $dirBackup $rel
            $dir = Split-Path -Parent $destino
            if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            Copy-Item $origen $destino -Force
            $huboBackup = $true
        }
    }
    if ($huboBackup) { EscribirOk "backup en .claude\.harness-backup\$sello" }

    # 3. Copiar los assets.
    $instalados = New-Object System.Collections.ArrayList

    foreach ($destino in @($dirHarness, (Join-Path $dirClaude 'skills'), (Join-Path $dirClaude 'agents'))) {
        if (-not (Test-Path $destino)) { New-Item -ItemType Directory -Path $destino -Force | Out-Null }
    }

    # comun
    $origenComun = Join-Path $script:Repo 'comun'
    foreach ($x in (Copy-Arbol (Join-Path $origenComun 'hooks')  (Join-Path $dirHarness 'hooks')))  { [void]$instalados.Add($x) }
    foreach ($x in (Copy-Arbol (Join-Path $origenComun 'reglas') (Join-Path $dirHarness 'reglas'))) { [void]$instalados.Add($x) }
    foreach ($x in (Copy-Arbol (Join-Path $origenComun 'checks') (Join-Path $dirHarness 'checks'))) { [void]$instalados.Add($x) }
    foreach ($x in (Copy-Arbol (Join-Path $origenComun 'bin')    (Join-Path $dirHarness 'bin')))    { [void]$instalados.Add($x) }
    foreach ($x in (Copy-Arbol (Join-Path $origenComun 'skills') (Join-Path $dirClaude 'skills')))  { [void]$instalados.Add($x) }
    foreach ($x in (Copy-Arbol (Join-Path $origenComun 'agents') (Join-Path $dirClaude 'agents')))  { [void]$instalados.Add($x) }

    # cada harness
    foreach ($id in $Ids) {
        $origen = Join-Path $script:Repo "harnesses\$id"
        foreach ($x in (Copy-Arbol (Join-Path $origen 'checks') (Join-Path $dirHarness "checks\$id"))) { [void]$instalados.Add($x) }
        foreach ($x in (Copy-Arbol (Join-Path $origen 'skills') (Join-Path $dirClaude 'skills')))      { [void]$instalados.Add($x) }
        foreach ($x in (Copy-Arbol (Join-Path $origen 'agents') (Join-Path $dirClaude 'agents')))      { [void]$instalados.Add($x) }
    }

    # manifiestos, para que -Doctor sepa qué rige acá
    $dirManif = Join-Path $dirHarness 'manifiestos'
    if (-not (Test-Path $dirManif)) { New-Item -ItemType Directory -Path $dirManif -Force | Out-Null }
    foreach ($m in $manifiestos) {
        $destino = Join-Path $dirManif ($m.id + '.json')
        Write-TextoUtf8 -Ruta $destino -Texto (ConvertTo-JsonTexto $m)
        [void] $instalados.Add($destino)
    }
    EscribirOk "$($instalados.Count) archivo(s) copiados"

    # 4. Shim y settings.
    $rutaShim = Join-Path $dirHarness 'run-hook.cmd'
    $python = Resolve-Python
    if (-not $python) {
        throw 'no se encontró un intérprete de Python instalado (se probó python, py y python3). Los hooks del harness lo necesitan desde esta versión: instalalo y volvé a correr.'
    }
    New-Shim -Ruta $rutaShim -Python $python
    [void] $instalados.Add($rutaShim)

    $rutaSettings = Join-Path $dirClaude 'settings.json'
    New-SettingsProyecto -RutaSettings $rutaSettings
    [void] $instalados.Add($rutaSettings)
    EscribirOk 'settings.json y lanzador de hooks generados'

    # 5. Config del humano.
    $rutaConfig = Join-Path $dirClaude 'harness.config.json'
    if (New-ConfigProyecto -Ruta $rutaConfig -Manifiestos $manifiestos -Usuario $nombreUsuario) {
        EscribirOk "harness.config.json creado para $nombreUsuario (no se vuelve a tocar nunca)"
    } else {
        EscribirOk "harness.config.json ya existía: no se toca (usuario: $nombreUsuario)"
    }

    # 6. Bloques en archivos del humano.
    $bloqueClaude = Read-TextoUtf8 (Join-Path $origenComun 'claude-md\bloque-comun.md')
    foreach ($id in $Ids) {
        $extra = Join-Path $script:Repo "harnesses\$id\claude-md\bloque.md"
        if (Test-Path $extra) { $bloqueClaude += "`r`n`r`n" + (Read-TextoUtf8 $extra) }
    }
    $nombreProyecto = Split-Path -Leaf $Project
    $rutaClaudeMd = Join-Path $Project 'CLAUDE.md'
    $accion = Set-BloqueMarcado -Ruta $rutaClaudeMd `
                                -MarcaIni $script:MarcaClaudeIni -MarcaFin $script:MarcaClaudeFin `
                                -Contenido $bloqueClaude -Encabezado "# CLAUDE.md — $nombreProyecto"
    EscribirOk "CLAUDE.md: bloque $accion (el resto del archivo no se tocó)"

    $zonas = Add-ZonasSiFaltan -RutaClaudeMd $rutaClaudeMd `
                               -RutaPlantilla (Join-Path $origenComun 'claude-md\plantilla-proyecto.md')
    if ($zonas.Agregadas.Count -gt 0) {
        EscribirOk ("CLAUDE.md: zonas agregadas vacías — " + ($zonas.Agregadas -join ', '))
    } else {
        EscribirOk 'CLAUDE.md: las zonas ya estaban, no se tocaron'
    }
    foreach ($r in $zonas.NoReconocidas) {
        if ($r.Parecida) {
            EscribirAviso ("CLAUDE.md: `<!-- $($r.Marcador) -->` parece ser tu $($r.Parecida) con otro nombre.")
            EscribirPaso  ("no se agregó $($r.Parecida) para no dejarte dos. Renombrá el marcador —el de apertura y el de cierre— y corré -Update.")
        } else {
            EscribirAviso ("CLAUDE.md: `<!-- $($r.Marcador) -->` es un bloque marcado que el harness no conoce. No lo toca nadie.")
        }
    }

    $bloqueGit = @'
.claude/
!.claude/settings.json.ejemplo

# Secretos
secrets/
!secrets/*.example
.env
.env.*
!.env.example
*.secret
*.pem
*.key
*.pfx
*.p12
*.keystore
'@
    $accion = Set-BloqueMarcado -Ruta (Join-Path $Project '.gitignore') `
                                -MarcaIni $script:MarcaGitIni -MarcaFin $script:MarcaGitFin `
                                -Contenido $bloqueGit
    EscribirOk ".gitignore: bloque $accion"

    # 7. Lockfile.
    $inventario = @()
    foreach ($ruta in ($instalados | Sort-Object -Unique)) {
        $inventario += [ordered]@{
            ruta   = $ruta.Substring($Project.Length).TrimStart('\')
            sha256 = (Get-Sha256Archivo $ruta)
        }
    }
    $lock = [ordered]@{
        version   = $script:Version
        harness   = @('comun') + $Ids
        instalado = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        backup    = ".claude\.harness-backup\$sello"
        archivos  = $inventario
    }
    Write-TextoUtf8 -Ruta (Join-Path $dirClaude 'harness.lock.json') -Texto (ConvertTo-JsonTexto $lock)
    EscribirOk "lockfile con $($inventario.Count) archivo(s) y su SHA256"

    # 8. Verificación. Si los hooks no responden, se revierte.
    $problemas = Test-HooksInstalados -DirHarness $dirHarness
    if ($problemas.Count -gt 0) {
        Escribir ''
        foreach ($p in $problemas) { EscribirMal $p }
        Escribir ''
        EscribirAviso 'los hooks no respondieron bien. Revirtiendo — un hook roto es peor que ninguno.'
        Invoke-Desinstalar -Silencioso
        throw 'instalación revertida'
    }
    EscribirOk 'los cuatro hooks responden correctamente'

    Escribir ''
    Write-Host '  Listo.' -ForegroundColor Green
    Escribir ''
    return 0
}


function Invoke-Actualizar {
    Escribir ''
    Escribir "gcba-harness v$($script:Version) — actualizar"
    Escribir ''

    $lock = Join-Path $Project '.claude\harness.lock.json'
    if (-not (Test-Path $lock)) { throw "el proyecto no tiene el harness instalado: $Project" }

    $d = Read-TextoUtf8 $lock | ConvertFrom-Json
    $ids = @($d.harness | Where-Object { $_ -ne 'comun' })

    # Lo que el humano editó a mano NO se pisa. Se escribe al lado con .nuevo y se avisa.
    $editados = @()
    foreach ($a in $d.archivos) {
        $ruta = Join-Path $Project $a.ruta
        if (-not (Test-Path $ruta)) { continue }
        if ((Get-Sha256Archivo $ruta) -ne $a.sha256) { $editados += $a.ruta }
    }

    if ($editados.Count -gt 0) {
        EscribirAviso "$($editados.Count) archivo(s) editados a mano. No se van a pisar:"
        foreach ($e in $editados) { EscribirPaso $e }
        Escribir ''
    }

    if (-not $PSCmdlet.ShouldProcess($Project, "actualizar de v$($d.version) a v$($script:Version)")) {
        return 0
    }

    # Se preservan los editados, se reinstala, y se les devuelve su contenido dejando
    # la versión nueva al lado.
    $guardados = @{}
    foreach ($e in $editados) {
        $ruta = Join-Path $Project $e
        $guardados[$e] = [System.IO.File]::ReadAllBytes($ruta)
    }

    $codigo = Invoke-Instalar -Ids $ids
    if ($codigo -ne 0) { return $codigo }

    foreach ($e in $editados) {
        $ruta = Join-Path $Project $e
        if (Test-Path $ruta) { Copy-Item $ruta ($ruta + '.nuevo') -Force }
        [System.IO.File]::WriteAllBytes($ruta, $guardados[$e])
    }
    if ($editados.Count -gt 0) {
        EscribirAviso 'tus versiones se conservaron. Las nuevas quedaron como .nuevo al lado.'
    }

    Escribir ''
    Write-Host "  Actualizado de v$($d.version) a v$($script:Version)." -ForegroundColor Green
    Escribir ''
    return 0
}


function Invoke-Desinstalar {
    param([switch] $Silencioso)

    if (-not $Silencioso) {
        Escribir ''
        Escribir 'gcba-harness — desinstalar'
        Escribir ''
    }

    $dirClaude = Join-Path $Project '.claude'
    $lock = Join-Path $dirClaude 'harness.lock.json'
    if (-not (Test-Path $lock)) {
        if (-not $Silencioso) { EscribirAviso 'el proyecto no tiene el harness instalado' }
        return 0
    }

    if (-not $Silencioso -and -not $PSCmdlet.ShouldProcess($Project, 'desinstalar gcba-harness')) {
        return 0
    }

    $d = Read-TextoUtf8 $lock | ConvertFrom-Json

    $borrados = 0
    foreach ($a in $d.archivos) {
        $ruta = Join-Path $Project $a.ruta
        if (Test-Path $ruta) { Remove-Item $ruta -Force -ErrorAction SilentlyContinue; $borrados++ }
    }
    Remove-Item $lock -Force -ErrorAction SilentlyContinue

    # Los .nuevo que dejó algún -Update. Existen para que el humano compare contra su
    # versión; sin harness instalado no comparan contra nada.
    $sobrantes = @(Get-ChildItem (Join-Path $dirClaude 'harness') -Recurse -File -Filter '*.nuevo' `
                                 -ErrorAction SilentlyContinue)
    foreach ($s in $sobrantes) { Remove-Item $s.FullName -Force -ErrorAction SilentlyContinue }

    # Directorios que quedaron vacíos.
    foreach ($sub in @('harness', 'skills', 'agents')) {
        $dir = Join-Path $dirClaude $sub
        if (Test-Path $dir) {
            $quedan = @(Get-ChildItem $dir -Recurse -File -Force -ErrorAction SilentlyContinue)
            if ($quedan.Count -eq 0) { Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue }
        }
    }

    $rutaClaudeMd = Join-Path $Project 'CLAUDE.md'
    Remove-BloqueMarcado -Ruta $rutaClaudeMd                      -MarcaIni $script:MarcaClaudeIni -MarcaFin $script:MarcaClaudeFin | Out-Null
    Remove-BloqueMarcado -Ruta (Join-Path $Project '.gitignore') -MarcaIni $script:MarcaGitIni    -MarcaFin $script:MarcaGitFin    | Out-Null

    # Las zonas vacías son andamiaje que nadie usó. Las que tienen contenido se quedan:
    # adentro está el trabajo de alguien.
    $zonasSacadas = Remove-ZonasVacias -RutaClaudeMd $rutaClaudeMd
    $zonasQueQuedan = @()
    foreach ($z in (Get-DefinicionZonas)) {
        if ($zonasSacadas -notcontains $z.Nombre) {
            $texto = ''
            if (Test-Path $rutaClaudeMd) { $texto = Read-TextoUtf8 $rutaClaudeMd }
            if ($null -ne (Get-ContenidoZona -Texto $texto -Zona $z)) { $zonasQueQuedan += $z.Nombre }
        }
    }

    if ($Silencioso) { return 0 }

    EscribirOk "$borrados archivo(s) borrados"
    if ($sobrantes.Count -gt 0) {
        EscribirOk "$($sobrantes.Count) archivo(s) .nuevo de un -Update previo, borrados"
    }
    EscribirOk 'bloques sacados de CLAUDE.md y .gitignore'
    if ($zonasSacadas.Count -gt 0) {
        EscribirOk ('zonas vacías sacadas del CLAUDE.md — ' + ($zonasSacadas -join ', '))
    }
    if ($zonasQueQuedan.Count -gt 0) {
        EscribirAviso ('quedan zonas con contenido, no se tocaron — ' + ($zonasQueQuedan -join ', '))
    }
    EscribirOk 'se conservan: los backups y tu harness.config.json'
    Escribir ''
    Write-Host '  Desinstalado.' -ForegroundColor Green
    Escribir ''
    return 0
}


# ── Despacho ────────────────────────────────────────────────────────────────────

try {
    # Resolve-Path devuelve $null si la ruta no existe: pedirle .Path a eso, bajo StrictMode,
    # muere con "No se encuentra la propiedad 'Path'", que no nombra ni el parámetro ni la ruta.
    # Errar la ruta del proyecto es el primer error que va a cometer cualquiera —desde Git Bash
    # alcanza con olvidar las comillas simples y las barras invertidas se las come el shell—,
    # así que el error tiene que decir cuál es la ruta que no existe.
    if ($Project) {
        $rutaResuelta = Resolve-Path -LiteralPath $Project -ErrorAction SilentlyContinue
        if (-not $rutaResuelta) { throw "el proyecto no existe: $Project" }
        $Project = $rutaResuelta.Path
    }

    if ($Doctor)         { exit (Invoke-Doctor) }
    if (-not $Project)   { throw 'falta -Project. Probá: .\install.ps1 -Doctor' }
    if ($Uninstall)      { exit (Invoke-Desinstalar) }
    if ($Update)         { exit (Invoke-Actualizar) }
    if ($Harness.Count -eq 0) {
        throw "falta -Harness. Disponibles: $((Get-HarnessDisponibles) -join ', ')"
    }
    exit (Invoke-Instalar -Ids $Harness)
}
catch {
    Escribir ''
    Write-Host ('  ' + $_.Exception.Message) -ForegroundColor Red
    Escribir ''
    exit 1
}
