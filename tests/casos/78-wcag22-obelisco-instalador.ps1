# Los escenarios de docs/cambios/wcag22-obelisco/spec.md que instalan de verdad: E-62 a E-65. Lo que no
# instala vive en tests/casos/78_wcag22_obelisco.py. Cada asercion nombra su E-nn.
#
# ASCII puro a proposito: un .ps1 con caracteres no ASCII necesita BOM (00-encoding-fuentes.ps1).
#
# El cambio no toca install.ps1: Copy-Arbol copia las skills y los checks enteros, con sus subcarpetas.
# Lo que se prueba es que eso alcanza, con el instalador real, sobre una copia aislada de la fabrica
# (tests\isolated-factory.ps1) para poder retirar y agregar archivos sin tocar el arbol versionado:
#   E-62  el lock lista cada archivo de .claude\skills\dev-accessibility\ y el motor a11y.py, con su SHA256;
#   E-63  desde el arbol instalado, con `python -I -B`, corren wcag.py, contrast.py y review.py, review.py
#         encuentra el motor instalado, y el check instalado habla por el hook de PostToolUse;
#   E-64  -Update borra la referencia retirada sin editar, deja la editada fuera del inventario, e instala
#         una referencia nueva en una subcarpeta nueva;
#   E-65  -Uninstall no deja nada: ni archivos del lock, ni la carpeta de la skill, ni a11y.py, ni __pycache__.
# Los valores son sinteticos. Todo se borra al final, aunque falle.

. (Join-Path $script:Raiz 'tests\isolated-factory.ps1')

Set-Grupo 'wcag22-obelisco - referencias y scripts de accesibilidad en un proyecto instalado'

$waUtf8 = New-Object System.Text.UTF8Encoding $false
$waTmp  = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-wa78-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $waTmp -Force | Out-Null


function Invoke-WaProceso {
    <# Un proceso con stdout y stderr en UTF-8, sin pasar por la tuberia de PowerShell. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Directorio = '', [string] $Entrada = '', [hashtable] $Entorno = @{})
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardInput  = $true
    $psi.StandardOutputEncoding = $waUtf8
    $psi.StandardErrorEncoding  = $waUtf8
    $psi.EnvironmentVariables['PYTHONDONTWRITEBYTECODE'] = '1'
    $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    if ($psi.EnvironmentVariables.ContainsKey('PYTHONPATH')) { $psi.EnvironmentVariables.Remove('PYTHONPATH') }
    foreach ($k in $Entorno.Keys) { $psi.EnvironmentVariables[$k] = [string]$Entorno[$k] }
    if ($Directorio) { $psi.WorkingDirectory = $Directorio }
    $p = [System.Diagnostics.Process]::Start($psi)
    $salida  = $p.StandardOutput.ReadToEndAsync()
    $errores = $p.StandardError.ReadToEndAsync()
    if ($Entrada) { $p.StandardInput.Write($Entrada) }
    $p.StandardInput.Close()
    if (-not $p.WaitForExit(300000)) { try { $p.Kill() } catch { }; return [pscustomobject]@{ Codigo = -1; Salida = ''; Errores = 'no termino en 300 s' } }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Salida = $salida.Result; Errores = $errores.Result }
}


function Invoke-WaInstalador {
    <# El instalador real, desde la fabrica que se indique. #>
    param([string] $Desde, [string[]] $Argumentos)
    $ErrorActionPreference = 'Continue'
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $Desde @Argumentos 2>&1 | Out-String
    $codigo = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    return [pscustomobject]@{ Salida = $salida; Codigo = $codigo }
}


function Get-WaLock {
    param([string] $Proyecto)
    try { return ([System.IO.File]::ReadAllText((Join-Path $Proyecto '.claude\harness.lock.json'), $waUtf8) | ConvertFrom-Json) } catch { return $null }
}


function Get-WaRutasDelLock {
    param($Lock)
    if (-not $Lock) { return @() }
    return @($Lock.archivos | ForEach-Object { [string]$_.ruta })
}


function Get-WaSha {
    param([string] $Ruta)
    return (Get-FileHash -LiteralPath $Ruta -Algorithm SHA256).Hash.ToLowerInvariant()
}


function Get-WaEsperados {
    <# Lo que la fabrica manda a .claude\: la skill entera y el motor, con la ruta relativa del proyecto. #>
    param([string] $Fabrica)
    $skill = Join-Path $Fabrica 'harnesses\desarrollo\skills\dev-accessibility'
    $esperados = @()
    foreach ($a in @(Get-ChildItem -LiteralPath $skill -Recurse -File | Where-Object { $_.Name -ne '.gitkeep' -and $_.Extension -ne '.pyc' -and $_.FullName -notlike '*__pycache__*' })) {
        $esperados += ('.claude\skills\dev-accessibility\' + $a.FullName.Substring($skill.Length).TrimStart('\'))
    }
    $esperados += '.claude\harness\checks\desarrollo\lib\a11y.py'
    return $esperados
}


try {
    Invoke-EnFabricaAislada {
        param($fabrica)
        $proy = Join-Path $waTmp 'instalado'
        New-Item -ItemType Directory -Path $proy -Force | Out-Null
        [System.IO.File]::WriteAllText((Join-Path $proy 'CLAUDE.md'), "# Proyecto de prueba`r`n", $waUtf8)
        $instalador = Join-Path $fabrica 'install.ps1'

        # -- E-62: instalar ----------------------------------------------------------------------
        $r = Invoke-WaInstalador -Desde $instalador -Argumentos @('-Project', $proy, '-Usuario', 'Ana Prueba')
        Assert-Verdadero 'E-62 el instalador, sin cambios, instala y sale con 0' ($r.Codigo -eq 0) ('codigo ' + $r.Codigo + ': ' + $r.Salida)

        $esperados = Get-WaEsperados -Fabrica $fabrica
        Assert-Verdadero ('E-62 la fabrica manda mas de 20 archivos de accesibilidad (' + $esperados.Count + ')') ($esperados.Count -gt 20)
        $lock = Get-WaLock -Proyecto $proy
        $rutas = Get-WaRutasDelLock -Lock $lock
        Assert-Verdadero 'E-62 se leyo el lockfile que escribio el instalador' ($rutas.Count -gt 0)
        $faltaEnLock = @($esperados | Where-Object { $rutas -notcontains $_ })
        Assert-Igual 'E-62 el lock lista cada archivo de la skill y el motor' 0 $faltaEnLock.Count
        $faltaEnDisco = @($esperados | Where-Object { -not (Test-Path -LiteralPath (Join-Path $proy $_)) })
        Assert-Igual 'E-62 y todos estan en disco' 0 $faltaEnDisco.Count
        $shaMalo = @()
        foreach ($a in @($lock.archivos | Where-Object { $esperados -contains [string]$_.ruta })) {
            $ruta = Join-Path $proy ([string]$a.ruta)
            if ((Test-Path -LiteralPath $ruta) -and ((Get-WaSha $ruta) -ne ([string]$a.sha256).ToLowerInvariant())) { $shaMalo += [string]$a.ruta }
        }
        Assert-Igual 'E-62 con el SHA256 que dice el lock' 0 $shaMalo.Count
        foreach ($sub in @('references\wcag22\operable.md', 'references\wcag22-criteria.json', 'references\obelisco-matrix.json', 'scripts\wcag.py', 'scripts\contrast.py', 'scripts\review.py', 'SKILL.md')) {
            Assert-Verdadero ('E-62 se instala dev-accessibility\' + $sub) ($rutas -contains ('.claude\skills\dev-accessibility\' + $sub))
        }
        Assert-Verdadero 'E-62 el motor queda en la carpeta de los checks de desarrollo' ($rutas -contains '.claude\harness\checks\desarrollo\lib\a11y.py')
        Assert-Verdadero 'E-62 y el check, a su lado' ($rutas -contains '.claude\harness\checks\desarrollo\dev-accesibilidad-html.py')

        # -- E-63: desde el arbol instalado ---------------------------------------------------------
        $scripts = Join-Path $proy '.claude\skills\dev-accessibility\scripts'
        $r = Invoke-WaProceso -Archivo 'python' -Argumentos ('-I -B "' + (Join-Path $scripts 'wcag.py') + '" count') -Directorio $waTmp
        Assert-Igual 'E-63 wcag.py count sale con 0 desde el arbol instalado' 0 $r.Codigo
        Assert-Contiene 'E-63 y cuenta 86 criterios' '86 criterios' $r.Salida
        $r = Invoke-WaProceso -Archivo 'python' -Argumentos ('-I -B "' + (Join-Path $scripts 'wcag.py') + '" criterion 2.4.11') -Directorio $waTmp
        Assert-Igual 'E-63 wcag.py criterion lee el texto normativo instalado' 0 $r.Codigo
        Assert-Contiene 'E-63 y trae el criterio' 'Focus Not Obscured (Minimum)' $r.Salida
        $r = Invoke-WaProceso -Archivo 'python' -Argumentos ('-I -B "' + (Join-Path $scripts 'contrast.py') + '" "#777" "#fff" --json') -Directorio $waTmp
        Assert-Igual 'E-63 contrast.py sale con 0' 0 $r.Codigo
        Assert-Contiene 'E-63 y da 4.48:1' '4.48:1' $r.Salida

        $pagina = Join-Path $proy 'web\index.html'
        New-Item -ItemType Directory -Path (Split-Path -Parent $pagina) -Force | Out-Null
        [System.IO.File]::WriteAllText($pagina, "<html><head><title>x</title></head><body><img src=`"a.png`"></body></html>`n", $waUtf8)
        $r = Invoke-WaProceso -Archivo 'python' -Argumentos ('-I -B "' + (Join-Path $scripts 'review.py') + '" "' + $pagina + '"') -Directorio $waTmp
        Assert-Igual 'E-63 review.py sale con 0 y encuentra el motor instalado' 0 $r.Codigo
        Assert-Contiene 'E-63 y revisa el archivo' 'sin atributo lang' $r.Salida
        Assert-Contiene 'E-63 y dice la cobertura' 'Cobertura: 1 archivo(s)' $r.Salida

        $hook = Join-Path $proy '.claude\harness\hooks\post-tool-use.py'
        $evento = ConvertTo-Json -Compress -Depth 5 -InputObject ([ordered]@{
            session_id = 'wa-e63'; cwd = $proy; hook_event_name = 'PostToolUse'; tool_name = 'Write'
            tool_input = [ordered]@{ file_path = $pagina; content = 'x' }; tool_response = [ordered]@{ success = $true } })
        $r = Invoke-WaProceso -Archivo 'python' -Argumentos ('-B "' + $hook + '"') -Directorio $proy -Entrada $evento -Entorno @{ CLAUDE_PROJECT_DIR = $proy }
        Assert-Igual 'E-63 el hook de PostToolUse sale con 0' 0 $r.Codigo
        Assert-Contiene 'E-63 el check instalado habla por el hook' 'sin atributo lang' $r.Salida
        Assert-Contiene 'E-63 y cita el criterio y su nivel' 'criterio 3.1.1, nivel A' $r.Salida

        # -- E-64: -Update con una referencia retirada, una editada y una nueva ----------------------
        $skillFabrica = Join-Path $fabrica 'harnesses\desarrollo\skills\dev-accessibility'
        $retiradaSinEditar = 'references\task-dynamic-media.md'
        $retiradaEditada   = 'references\task-color-contrast.md'
        $nuevaRelativa     = 'references\extra\nueva-referencia.md'
        $rutaEditada = Join-Path $proy ('.claude\skills\dev-accessibility\' + $retiradaEditada)
        [System.IO.File]::AppendAllText($rutaEditada, "`nUna nota que escribio una persona.`n", $waUtf8)
        Remove-Item -LiteralPath (Join-Path $skillFabrica $retiradaSinEditar) -Force
        Remove-Item -LiteralPath (Join-Path $skillFabrica $retiradaEditada) -Force
        New-Item -ItemType Directory -Path (Join-Path $skillFabrica 'references\extra') -Force | Out-Null
        [System.IO.File]::WriteAllText((Join-Path $skillFabrica $nuevaRelativa), "# Una referencia nueva, en una subcarpeta nueva`n", $waUtf8)

        $r = Invoke-WaInstalador -Desde $instalador -Argumentos @('-Project', $proy, '-Update')
        Assert-Igual 'E-64 -Update sale con 0' 0 $r.Codigo
        $rutas = Get-WaRutasDelLock -Lock (Get-WaLock -Proyecto $proy)
        $rel = '.claude\skills\dev-accessibility\'
        Assert-Verdadero 'E-64 la referencia retirada y sin editar se borra del disco' (-not (Test-Path -LiteralPath (Join-Path $proy ($rel + $retiradaSinEditar))))
        Assert-Verdadero 'E-64 y sale del lock' ($rutas -notcontains ($rel + $retiradaSinEditar))
        Assert-Verdadero 'E-64 la retirada y editada a mano se queda en el disco' (Test-Path -LiteralPath $rutaEditada)
        Assert-Verdadero 'E-64 con lo que escribio la persona' ([System.IO.File]::ReadAllText($rutaEditada, $waUtf8).Contains('Una nota que escribio una persona.'))
        Assert-Verdadero 'E-64 pero fuera del inventario' ($rutas -notcontains ($rel + $retiradaEditada))
        Assert-Contiene 'E-64 y el instalador avisa que quedo por editada' 'los editaste a mano' $r.Salida
        $rutaNueva = Join-Path $proy ($rel + $nuevaRelativa)
        Assert-Verdadero 'E-64 la referencia nueva, en una subcarpeta nueva, se instala' (Test-Path -LiteralPath $rutaNueva)
        Assert-Verdadero 'E-64 y entra al lock' ($rutas -contains ($rel + $nuevaRelativa))
        $lockNuevo = Get-WaLock -Proyecto $proy
        $entradaNueva = @($lockNuevo.archivos | Where-Object { [string]$_.ruta -eq ($rel + $nuevaRelativa) })
        Assert-Verdadero 'E-64 con su SHA256' ($entradaNueva.Count -eq 1 -and ([string]$entradaNueva[0].sha256).ToLowerInvariant() -eq (Get-WaSha $rutaNueva))
        Assert-Verdadero 'E-64 lo que sigue en la fabrica sigue instalado' ($rutas -contains ($rel + 'references\task-forms.md'))

        # -- E-65: -Uninstall --------------------------------------------------------------------------
        # La referencia editada es trabajo de una persona: el instalador no la borra, ni debe. Se la
        # retira como lo haria quien lee el aviso, y entonces -Uninstall no tiene que dejar nada.
        $listaAntes = @(Get-WaRutasDelLock -Lock (Get-WaLock -Proyecto $proy))
        Remove-Item -LiteralPath $rutaEditada -Force
        $r = Invoke-WaInstalador -Desde $instalador -Argumentos @('-Project', $proy, '-Uninstall')
        Assert-Igual 'E-65 -Uninstall sale con 0' 0 $r.Codigo
        $quedan = @($listaAntes | Where-Object { Test-Path -LiteralPath (Join-Path $proy $_) })
        Assert-Igual 'E-65 no queda ningun archivo del lock' 0 $quedan.Count
        Assert-Verdadero 'E-65 ni la carpeta de la skill' (-not (Test-Path -LiteralPath (Join-Path $proy '.claude\skills\dev-accessibility')))
        Assert-Verdadero 'E-65 ni el motor' (-not (Test-Path -LiteralPath (Join-Path $proy '.claude\harness\checks\desarrollo\lib\a11y.py')))
        Assert-Verdadero 'E-65 ni la carpeta de la lib de los checks' (-not (Test-Path -LiteralPath (Join-Path $proy '.claude\harness\checks\desarrollo\lib')))
        $pycache = @(Get-ChildItem -LiteralPath $proy -Recurse -Directory -Filter '__pycache__' -Force -ErrorAction SilentlyContinue)
        Assert-Igual 'E-65 los scripts corridos con -B no dejaron __pycache__' 0 $pycache.Count
        Assert-Verdadero 'E-65 el proyecto conserva su CLAUDE.md' (Test-Path -LiteralPath (Join-Path $proy 'CLAUDE.md'))
    }
}
finally {
    $ErrorActionPreference = 'Continue'
    Remove-Item -LiteralPath $waTmp -Recurse -Force -ErrorAction SilentlyContinue
    $ErrorActionPreference = 'Stop'
}
