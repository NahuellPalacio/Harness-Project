# SessionStart — se dispara al abrir, retomar o limpiar una sesion.
#
# Contesta la pregunta que si no, hay que hacer a mano: en que quedamos.
#
# TODO lo que inyecta sale de fuentes que ya pasaron por el filtro humano de "esto vale
# la pena escribirlo": commits, la zona cache del CLAUDE.md, definiciones pendientes.
# No captura nada por su cuenta.
#
# Esa es la diferencia con una memoria que graba todo por las dudas: un capturador
# automatico persiste tambien la cadena de conexion que el agente leyo hace un rato, y
# entonces el secreto queda en dos lugares en vez de uno. Aca no puede pasar, porque lo
# unico que se lee es lo que alguien decidio dejar anotado.
#
# Presupuesto: 12 lineas. Se paga una vez por sesion, pero ocupa ventana todo el rato.

Import-Module (Join-Path $PSScriptRoot 'lib\Hook.psm1')   -Force
Import-Module (Join-Path $PSScriptRoot 'lib\Reglas.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'lib\Zonas.psm1')  -Force

Invoke-Hook -EventName 'SessionStart' -Cuerpo {
    param($e)

    $proyecto = Get-HookField -Evento $e -Ruta 'cwd' -Default ''
    if (-not $proyecto -or -not (Test-Path $proyecto)) { return }

    $config = Get-ConfigProyecto -Proyecto $proyecto
    $lineas = New-Object System.Collections.ArrayList

    # --- Quien sos y que harness rige aca ---------------------------------------
    $encabezado = ''
    if ($null -ne $config -and $config.PSObject.Properties['usuario'] -and $config.usuario) {
        $encabezado = [string]$config.usuario
    }

    $lock = Join-Path $proyecto '.claude\harness.lock.json'
    if (Test-Path $lock) {
        try {
            $datos = [System.IO.File]::ReadAllText($lock, (New-Object System.Text.UTF8Encoding $false)) | ConvertFrom-Json
            $ids = (@($datos.harness) -join ', ')
            $texto = "harness: $ids v$($datos.version)"
            if ($encabezado) { $encabezado = "$encabezado - $texto" } else { $encabezado = $texto }
        } catch { }
    }
    if ($encabezado) { [void] $lineas.Add($encabezado) }

    # --- Estado del control de versiones y ultimo trabajo ------------------------
    if (Test-Path (Join-Path $proyecto '.git')) {
        try {
            $rama  = (& git -C $proyecto rev-parse --abbrev-ref HEAD 2>$null)
            $sucio = @(& git -C $proyecto status --porcelain 2>$null)
            $estado = 'limpio'
            if ($sucio.Count -gt 0) { $estado = "$($sucio.Count) con cambios" }
            [void] $lineas.Add("git: $rama, $estado")

            $commits = @(& git -C $proyecto log --format='%s' -3 2>$null)
            if ($commits.Count -gt 0) {
                [void] $lineas.Add('Ultimo trabajo:')
                foreach ($c in $commits) { [void] $lineas.Add('  - ' + $c) }
            }
        } catch { }
    } else {
        [void] $lineas.Add('git: este proyecto no esta versionado. No hay diff ni vuelta atras.')
    }

    # --- Lo que quedo anotado en la cache ---------------------------------------
    # Es lo que alguien dejo escrito a proposito para el proximo que llegue.
    $claudeMd = Join-Path $proyecto 'CLAUDE.md'
    if (Test-Path $claudeMd) {
        try {
            $texto = [System.IO.File]::ReadAllText($claudeMd, (New-Object System.Text.UTF8Encoding $false))
            $zonaCache = (Get-DefinicionZonas) | Where-Object { $_.Nombre -eq 'ZONA CACHE' }
            $contenido = Get-ContenidoZona -Texto $texto -Zona $zonaCache

            if ($contenido) {
                $utiles = @($contenido -split "`n" |
                            Where-Object { $_.Trim() -and $_ -notmatch '^\s*#' -and $_ -notmatch '^\s*_\(' })
                if ($utiles.Count -gt 0) {
                    [void] $lineas.Add('En la cache quedo anotado:')
                    foreach ($u in ($utiles | Select-Object -First 4)) {
                        [void] $lineas.Add('  ' + $u.Trim())
                    }
                    if ($utiles.Count -gt 4) {
                        [void] $lineas.Add("  ... y $($utiles.Count - 4) mas en la zona cache del CLAUDE.md")
                    }
                }
            }
        } catch { }
    }

    # --- Definiciones pendientes abiertas ----------------------------------------
    if ($null -ne $config -and $config.PSObject.Properties['rutaDefinicionesPendientes'] -and $config.rutaDefinicionesPendientes) {
        $rutaDef = Join-Path $proyecto $config.rutaDefinicionesPendientes
        if (Test-Path $rutaDef) {
            try {
                $txt = [System.IO.File]::ReadAllText($rutaDef, (New-Object System.Text.UTF8Encoding $false))
                $abiertas = @([regex]::Matches($txt, '(?m)^\s*[-*]\s*\[ \]')).Count
                if ($abiertas -gt 0) { [void] $lineas.Add("$abiertas definiciones pendientes abiertas") }
            } catch { }
        }
    }

    if ($lineas.Count -eq 0) { return }

    Write-HookContext -EventName 'SessionStart' -Texto ($lineas -join "`n")
}
