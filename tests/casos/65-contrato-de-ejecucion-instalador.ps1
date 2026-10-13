# El escenario de docs/cambios/execution-contract/spec.md que instala de verdad: EX-E53. Cada
# asercion nombra su EX-Enn. Lo que no instala vive en tests/casos/65_contrato_de_ejecucion.py.
#
# ASCII puro a proposito: un .ps1 con caracteres no ASCII necesita BOM (00-encoding-fuentes.ps1).
#
# Task 3 instala el contrato y nada mas: los dos schemas y bin/ejecucion/. No instala almacenamiento
# de ejecuciones, y install.ps1 no cambia: ya copia bin/ y comun/schemas/ enteros. Todo se instala
# en %TEMP%, y se borra al final.

Set-Grupo 'execution-contract - el contrato en un proyecto instalado'

$ecInstalador = Join-Path $script:Raiz 'install.ps1'
$ecUtf8       = New-Object System.Text.UTF8Encoding $false
$ecTmp        = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-ec65-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $ecTmp -Force | Out-Null


function Invoke-EcProceso {
    <# Un proceso con stdout y stderr en UTF-8, sin pasar por la tuberia de PowerShell. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Directorio = '')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardInput  = $true
    $psi.StandardOutputEncoding = $ecUtf8
    $psi.StandardErrorEncoding  = $ecUtf8
    $psi.EnvironmentVariables['PYTHONDONTWRITEBYTECODE'] = '1'
    $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    if ($psi.EnvironmentVariables.ContainsKey('CLAUDE_PROJECT_DIR')) { $psi.EnvironmentVariables.Remove('CLAUDE_PROJECT_DIR') }
    if ($Directorio) { $psi.WorkingDirectory = $Directorio }
    $p = [System.Diagnostics.Process]::Start($psi)
    $salida  = $p.StandardOutput.ReadToEndAsync()
    $errores = $p.StandardError.ReadToEndAsync()
    $p.StandardInput.Close()
    if (-not $p.WaitForExit(300000)) { try { $p.Kill() } catch { }; return [pscustomobject]@{ Codigo = -1; Salida = ''; Errores = 'no termino en 300 s' } }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Salida = $salida.Result; Errores = $errores.Result }
}


# La sonda corre desde el arbol instalado: importa ejecucion.contrato de ahi, y dice donde encontro
# cada schema y si validar_request y validar_resultado llegan a validar.
$ecSonda = Join-Path $ecTmp 'sonda.py'
$ecCodigoSonda = @'
import os, sys
bin_dir = sys.argv[1]
sys.path.insert(0, bin_dir)
from ejecucion import contrato as C
import rutas
lineas = ["modulo|" + os.path.normcase(os.path.abspath(C.__file__))]
for nombre in (C.SCHEMA_REQUEST, C.SCHEMA_RESULT, C.SCHEMA_PLAN):
    ruta = rutas.localizar(("schemas", nombre), C.__file__)
    esquema, motivo = C._schema(nombre)
    lineas.append("%s|%s|%s" % (nombre, os.path.normcase(os.path.abspath(ruta)) if ruta else "-",
                                "ok" if esquema is not None else motivo))
faltan = [e for e in C.validar_request({}) + C.validar_resultado({}, {}) if "no esta" in e]
lineas.append("faltan|" + ";".join(faltan))
sys.stdout.write("\n".join(lineas))
'@
[System.IO.File]::WriteAllText($ecSonda, $ecCodigoSonda, $ecUtf8)


try {
    $ecProy = Join-Path $ecTmp 'instalado'
    New-Item -ItemType Directory -Path $ecProy -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $ecProy 'CLAUDE.md'), "# Proyecto de prueba`r`n", $ecUtf8)

    $ErrorActionPreference = 'Continue'
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $ecInstalador -Project $ecProy -Usuario 'Ana Prueba' 2>&1 | Out-String
    $codigo = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Assert-Igual 'EX-E53 el instalador instala y sale con 0' 0 $codigo

    $ecHarness = Join-Path $ecProy '.claude\harness'
    foreach ($rel in @('schemas\execution-request.schema.json',
                       'schemas\execution-result.schema.json',
                       'bin\desarrollo\ejecucion\contrato.py',
                       'bin\desarrollo\ejecucion\__init__.py')) {
        Assert-Verdadero "EX-E53 se instala .claude\harness\$rel" (Test-Path -LiteralPath (Join-Path $ecHarness $rel))
    }

    $ecBin = Join-Path $ecHarness 'bin\desarrollo'
    $r = Invoke-EcProceso -Archivo 'python' -Argumentos ('"' + $ecSonda + '" "' + $ecBin + '"') -Directorio $ecProy
    Assert-Igual 'EX-E53 la sonda corre desde el arbol instalado' 0 $r.Codigo
    $lineas = @{}
    foreach ($l in ($r.Salida -split "`n")) {
        $partes = $l.Trim() -split '\|'
        if ($partes.Count -ge 2) { $lineas[$partes[0]] = $partes[1..($partes.Count - 1)] }
    }
    $ecDentro = [System.IO.Path]::GetFullPath($ecHarness).ToLowerInvariant()
    $modulo = ''
    if ($lineas.ContainsKey('modulo')) { $modulo = [string]$lineas['modulo'][0] }
    Assert-Verdadero 'EX-E53 contrato.py se importa del arbol instalado' ($modulo.ToLowerInvariant().StartsWith($ecDentro)) $modulo
    foreach ($nombre in @('execution-request.schema.json', 'execution-result.schema.json', 'orchestration-plan.schema.json')) {
        $fila = $lineas[$nombre]
        $ruta = ''
        $estado = ''
        if ($fila) { $ruta = [string]$fila[0]; $estado = [string]$fila[1] }
        Assert-Verdadero "EX-E53 el contrato instalado encuentra $nombre en el arbol instalado" ($ruta.ToLowerInvariant().StartsWith($ecDentro)) $ruta
        Assert-Igual "EX-E53 y lo carga: $nombre" 'ok' $estado
    }
    $faltan = ''
    if ($lineas.ContainsKey('faltan')) { $faltan = [string]($lineas['faltan'] -join '|') }
    Assert-Vacio 'EX-E53 validar_request y validar_resultado encuentran sus schemas' $faltan

    Assert-Verdadero 'EX-E53 no hay .claude\ejecuciones: Task 3 instala el contrato, no un almacenamiento' `
        (-not (Test-Path -LiteralPath (Join-Path $ecProy '.claude\ejecuciones')))
}
finally {
    $ErrorActionPreference = 'Continue'
    Remove-Item -LiteralPath $ecTmp -Recurse -Force -ErrorAction SilentlyContinue
    $ErrorActionPreference = 'Stop'
}
