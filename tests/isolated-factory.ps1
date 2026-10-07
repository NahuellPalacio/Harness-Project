# Una copia descartable de la fábrica, para los tests que tienen que romperla.
#
# E-20 y E-27 de 03-instalador.ps1 rompen zonas.py y pre-tool-use.py para ver que el
# instalador aborta. Hasta Qualification Gate 1 los rompían en el árbol versionado y los
# restauraban en un finally: si la compuerta moría a mitad (un watchdog, un Stop-Process, un
# timeout), el finally no corría y pre-tool-use.py, la única regla que bloquea, quedaba roto
# en el árbol. Dos compuertas a la vez también alcanzaban: una restauraba la rotura de la otra.
#
# Ahora se rompe una copia en el temporal. El árbol no se escribe nunca, así que matar el
# proceso no lo puede dejar roto: lo que queda es una carpeta en el temporal, que la próxima
# corrida barre cuando el proceso que la creó ya no existe.
#
# Se carga con dot-source: desde 03-instalador.ps1 y 68-isolated-factory.ps1, y desde el
# proceso hijo que 68 mata a propósito.

# Lo que install.ps1 lee de su propia carpeta ($script:Repo). Si el instalador empieza a leer
# otra cosa, la copia queda incompleta y E-20/E-27 lo dicen: cada uno afirma que su falla es
# la rotura que hizo y no un archivo que falta.
$script:PartesDeLaFabrica = @(
    'install.ps1', 'VERSION', 'manifest.json', 'comun', 'harnesses', 'normativa', 'tests\payloads',
    'tests\medir_barra.py'
)
$script:PrefijoFabrica = 'harness-fabrica-'
$script:MarcaFabrica   = '.fabrica-aislada.json'


function Get-DuenoDeProceso {
    <#
    .SYNOPSIS
        El pid y el arranque del proceso: el pid solo se reusa, el par no.
    .DESCRIPTION
        Un proceso de otro nivel (una compuerta elevada vista desde una que no lo está) existe
        pero no deja leer su arranque: es 'ilegible', y el barrido lo trata como vivo.
    #>
    param([int] $IdProceso = $PID)
    $p = Get-Process -Id $IdProceso -ErrorAction SilentlyContinue
    if (-not $p) { return $null }
    $arranque = 'ilegible'
    try { if ($null -ne $p.StartTime) { $arranque = $p.StartTime.ToFileTimeUtc() } } catch { }
    return [pscustomobject]@{ pid = $IdProceso; arranque = [string]$arranque }
}


function Clear-FabricasHuerfanas {
    <#
    .SYNOPSIS
        Borra las copias cuyo dueño ya no existe: las que dejó una corrida matada.
    .DESCRIPTION
        Solo toca carpetas del temporal con el prefijo y la marca. Una sin marca, o con una
        marca ilegible, no es una copia de esta suite y no se toca. Una cuyo dueño vive es de
        otra corrida en curso: tampoco.
    #>
    $tmp = [System.IO.Path]::GetTempPath()
    $borradas = @()
    foreach ($d in @(Get-ChildItem -LiteralPath $tmp -Directory -Filter ($script:PrefijoFabrica + '*') -ErrorAction SilentlyContinue)) {
        $marca = Join-Path $d.FullName $script:MarcaFabrica
        if (-not (Test-Path -LiteralPath $marca)) { continue }
        try { $m = [System.IO.File]::ReadAllText($marca) | ConvertFrom-Json } catch { continue }
        $vivo = Get-DuenoDeProceso -IdProceso ([int]$m.pid)
        if ($vivo -and ($vivo.arranque -eq 'ilegible' -or $vivo.arranque -eq [string]$m.arranque)) { continue }
        Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path -LiteralPath $d.FullName)) { $borradas += $d.FullName }
    }
    return $borradas
}


function New-FabricaAislada {
    <# Copia la fábrica a una carpeta nueva del temporal, con la marca de su dueño. Devuelve la ruta. #>
    param([string] $Origen = $script:Raiz)
    Clear-FabricasHuerfanas | Out-Null
    $dir = Join-Path ([System.IO.Path]::GetTempPath()) ($script:PrefijoFabrica + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    # La marca va primero: una corrida matada a mitad de la copia también deja una huérfana barrible.
    [System.IO.File]::WriteAllText((Join-Path $dir $script:MarcaFabrica),
        (ConvertTo-Json -InputObject (Get-DuenoDeProceso) -Compress))
    foreach ($parte in $script:PartesDeLaFabrica) {
        $desde = Join-Path $Origen $parte
        $hasta = Join-Path $dir $parte
        $padre = Split-Path -Parent $hasta
        if (-not (Test-Path -LiteralPath $padre)) { New-Item -ItemType Directory -Path $padre -Force | Out-Null }
        Copy-Item -LiteralPath $desde -Destination $hasta -Recurse -Force
    }
    return $dir
}


function Remove-FabricaAislada {
    <# Borra una copia. Se niega a borrar algo que no tenga el prefijo, la marca y esté en el temporal. #>
    param([Parameter(Mandatory)][string] $Dir)
    $tmp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    $full = [System.IO.Path]::GetFullPath($Dir)
    $esCopia = $full.StartsWith($tmp, [System.StringComparison]::OrdinalIgnoreCase) -and
               (Split-Path -Leaf $full).StartsWith($script:PrefijoFabrica) -and
               (Test-Path -LiteralPath (Join-Path $full $script:MarcaFabrica))
    if (-not $esCopia) { throw "no es una fábrica aislada, no se borra: $Dir" }
    Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction SilentlyContinue
}


function Invoke-EnFabricaAislada {
    <#
    .SYNOPSIS
        Corre el cuerpo con una copia propia de la fábrica, y la borra al salir.
    .DESCRIPTION
        El cuerpo recibe la ruta de la copia. Lo que devuelve, se devuelve; lo que tira, sale
        tal cual: el finally limpia y no se traga nada.
    #>
    param([Parameter(Mandatory)][scriptblock] $Cuerpo)
    $dir = New-FabricaAislada
    try { & $Cuerpo $dir }
    finally { Remove-FabricaAislada -Dir $dir }
}
