# El escenario de docs/cambios/graph-execution/spec.md que instala de verdad: GE-E66. Cada asercion
# nombra su GE-Enn. Lo que no instala vive en tests/casos/73_ejecucion_de_grafo.py.
#
# ASCII puro a proposito: un .ps1 con caracteres no ASCII necesita BOM (00-encoding-fuentes.ps1).
#
# Task 5 no cambia install.ps1 ni manifest.json: Copy-Arbol ya copia bin/ y comun/schemas/ enteros, y
# el conductor y el schema de su resultado llegan solos. Aca se instala en %TEMP%, se arma un plan listo
# de dos unidades, y `dev-harness.py ejecutar --grafo` del arbol instalado lo lleva a SUCCEEDED con el
# Host falso (tests/fixtures/host_falso.py), configurado en `ejecucion.comandoHost` de
# harness.config.json. Nunca el Claude Code real. Todo se borra al final.

Set-Grupo 'graph-execution - el GraphRun en un proyecto instalado'

$geInstalador = Join-Path $script:Raiz 'install.ps1'
$geHostFalso  = Join-Path $script:Raiz 'tests\fixtures\host_falso.py'
$geUtf8       = New-Object System.Text.UTF8Encoding $false
$geTmp        = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-ge73-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $geTmp -Force | Out-Null


function Invoke-GeProceso {
    <# Un proceso con stdout y stderr en UTF-8, sin pasar por la tuberia de PowerShell. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Directorio = '', [string] $Guion = '')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardInput  = $true
    $psi.StandardOutputEncoding = $geUtf8
    $psi.StandardErrorEncoding  = $geUtf8
    $psi.EnvironmentVariables['PYTHONDONTWRITEBYTECODE'] = '1'
    $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    if ($Guion) { $psi.EnvironmentVariables['HOST_FALSO_GUION'] = $Guion }
    if ($psi.EnvironmentVariables.ContainsKey('CLAUDE_PROJECT_DIR')) { $psi.EnvironmentVariables.Remove('CLAUDE_PROJECT_DIR') }
    if ($Directorio) { $psi.WorkingDirectory = $Directorio }
    $p = [System.Diagnostics.Process]::Start($psi)
    $salida  = $p.StandardOutput.ReadToEndAsync()
    $errores = $p.StandardError.ReadToEndAsync()
    $p.StandardInput.Close()
    if (-not $p.WaitForExit(300000)) { try { $p.Kill() } catch { }; return [pscustomobject]@{ Codigo = -1; Salida = ''; Errores = 'no termino en 300 s' } }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Salida = $salida.Result; Errores = $errores.Result }
}


# Arma el proyecto de prueba con los ayudantes de 64_modelo_de_dominio.py: un repositorio cuyo
# origin es el de la Ficha, el TaskContext con su hash de verdad, las capacidades, una propuesta de
# DOS unidades (la segunda depende de la primera), y el Host falso en harness.config.json.
$gePreparar = Join-Path $geTmp 'preparar.py'
$geCodigoPreparar = @'
import importlib.util, io, json, os, subprocess, sys
from pathlib import Path
proy, raiz, host, guion = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("m64_ge66", os.path.join(raiz, "tests", "casos", "64_modelo_de_dominio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
clave = "GCBA-72"
def git(*a):
    subprocess.run(["git", "-C", proy, "-c", "user.email=t@t", "-c", "user.name=t", "-c", "core.autocrlf=false"] + list(a),
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
m._escribir(Path(proy) / "src" / "app.py", "VALOR = 1\n")
git("init", "-q")
git("add", "-A")
git("commit", "-q", "-m", "inicial")
git("remote", "add", "origin", m.URL_DEL_REPO + ".git")
m._json(Path(proy) / ".claude" / "contextos" / (clave + ".json"), m._contexto(clave, True))
m._json(Path(proy) / ".claude" / "harness.capacidades.json", {"capacidades": m.REGISTRO})
m._json(Path(proy) / "prop-1.json", m._propuesta([m._unidad("analizar-api"),
                                                  m._unidad("implementar-endpoint", dependencias=("analizar-api",))]))
ruta = Path(proy) / ".claude" / "harness.config.json"
config = json.loads(ruta.read_text(encoding="utf-8-sig")) if ruta.is_file() else {}
config["ejecucion"] = {"comandoHost": [sys.executable, host], "limiteSegundos": 120}
ruta.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
Path(guion).write_text("{}", encoding="utf-8")
sys.stdout.write("ok")
'@
[System.IO.File]::WriteAllText($gePreparar, $geCodigoPreparar, $geUtf8)


try {
    $geProy = Join-Path $geTmp 'instalado'
    New-Item -ItemType Directory -Path $geProy -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $geProy 'CLAUDE.md'), "# Proyecto de prueba`r`n", $geUtf8)

    $ErrorActionPreference = 'Continue'
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $geInstalador -Project $geProy -Usuario 'Ana Prueba' 2>&1 | Out-String
    $codigo = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Assert-Igual 'GE-E66 el instalador, sin cambios, instala y sale con 0' 0 $codigo

    # grafo.py y el schema de su resultado estan instalados, y en el lockfile.
    $geBin = Join-Path $geProy '.claude\harness\bin\desarrollo'
    $geGrafo  = Join-Path $geBin 'ejecucion\grafo.py'
    $geSchema = Join-Path $geProy '.claude\harness\schemas\graph-run-result.schema.json'
    Assert-Verdadero 'GE-E66 se instala bin\desarrollo\ejecucion\grafo.py' (Test-Path -LiteralPath $geGrafo)
    Assert-Verdadero 'GE-E66 se instala schemas\graph-run-result.schema.json' (Test-Path -LiteralPath $geSchema)
    $geLock = $null
    try { $geLock = [System.IO.File]::ReadAllText((Join-Path $geProy '.claude\harness.lock.json'), $geUtf8) | ConvertFrom-Json } catch { $geLock = $null }
    $geRutas = @()
    if ($geLock) { $geRutas = @($geLock.archivos | ForEach-Object { [string]$_.ruta }) }
    Assert-Verdadero 'GE-E66 y el lockfile lista grafo.py' ($geRutas -contains '.claude\harness\bin\desarrollo\ejecucion\grafo.py')
    Assert-Verdadero 'GE-E66 y el schema del resultado' ($geRutas -contains '.claude\harness\schemas\graph-run-result.schema.json')
    $geDeclarado = ''
    if (Test-Path -LiteralPath $geSchema) { $geDeclarado = [System.IO.File]::ReadAllText($geSchema, $geUtf8) }
    Assert-Contiene 'GE-E66 el schema instalado es el de graph-run-result/1.0' 'graph-run-result/1.0' $geDeclarado

    $geGuion = Join-Path $geTmp 'guion.json'
    $r = Invoke-GeProceso -Archivo 'python' -Argumentos ('"' + $gePreparar + '" "' + $geProy + '" "' + $script:Raiz + '" "' + $geHostFalso + '" "' + $geGuion + '"') -Directorio $geTmp
    Assert-Igual 'GE-E66 el proyecto de prueba se armo' 'ok' $r.Salida

    $geCli = Join-Path $geBin 'dev-harness.py'
    $r = Invoke-GeProceso -Archivo 'python' -Argumentos ('"' + $geCli + '" plan GCBA-72 --propuesta prop-1.json --proyecto "' + $geProy + '"') -Directorio $geProy
    Assert-Igual 'GE-E66 plan --propuesta del arbol instalado sale con 0' 0 $r.Codigo

    # El GraphRun: `ejecutar --grafo` del arbol instalado lleva el plan de dos unidades a SUCCEEDED.
    $r = Invoke-GeProceso -Archivo 'python' -Argumentos ('"' + $geCli + '" ejecutar GCBA-72 --grafo --json --proyecto "' + $geProy + '"') -Directorio $geProy -Guion $geGuion
    Assert-Igual 'GE-E66 ejecutar --grafo del arbol instalado sale con 0' 0 $r.Codigo
    $geResultado = $null
    try { $geResultado = $r.Salida | ConvertFrom-Json } catch { $geResultado = $null }
    $geEstado = ''
    $geId = ''
    $geNodos = @()
    if ($geResultado) { $geEstado = [string]$geResultado.status; $geId = [string]$geResultado.graphRunId; $geNodos = @($geResultado.nodes) }
    Assert-Igual 'GE-E66 el GraphRun queda SUCCEEDED en el instalado' 'SUCCEEDED' $geEstado
    Assert-Igual 'GE-E66 con las dos unidades, SATISFIED y despachadas por el GraphRun' 'analizar-api:SATISFIED:True|implementar-endpoint:SATISFIED:True' (($geNodos | ForEach-Object { [string]$_.workUnitId + ':' + [string]$_.state + ':' + [string]$_.dispatched }) -join '|')
    $geCarpeta = Join-Path $geProy (".claude\ejecuciones\GCBA-72\grafos\" + $geId)
    Assert-Verdadero 'GE-E66 bajo .claude\ejecuciones\GCBA-72\grafos\<graphRunId>\result.json' ($geId -and (Test-Path -LiteralPath (Join-Path $geCarpeta 'result.json')))
    Assert-Verdadero 'GE-E66 con inicio.json y las marcas de despacho 001 y 002' ($geId -and (Test-Path -LiteralPath (Join-Path $geCarpeta 'inicio.json')) -and (Test-Path -LiteralPath (Join-Path $geCarpeta 'despachos\001.json')) -and (Test-Path -LiteralPath (Join-Path $geCarpeta 'despachos\002.json')))
    $geCarpetasDeExecution = @()
    $geBase = Join-Path $geProy '.claude\ejecuciones\GCBA-72'
    if (Test-Path -LiteralPath $geBase) { $geCarpetasDeExecution = @(Get-ChildItem -LiteralPath $geBase -Directory | Where-Object { $_.Name -like 'exe_*' }) }
    Assert-Igual 'GE-E66 y una Execution por unidad' 2 $geCarpetasDeExecution.Count

    # --grafo --estado, tambien desde el arbol instalado: solo lee, y muestra el GraphRun terminal.
    $r = Invoke-GeProceso -Archivo 'python' -Argumentos ('"' + $geCli + '" ejecutar GCBA-72 --grafo --estado --json --proyecto "' + $geProy + '"') -Directorio $geProy
    Assert-Igual 'GE-E66 ejecutar --grafo --estado del arbol instalado sale con 0' 0 $r.Codigo
    $geFilas = @()
    try { $geFilas = @($r.Salida | ConvertFrom-Json) } catch { $geFilas = @() }
    Assert-Igual 'GE-E66 y lista el GraphRun, SUCCEEDED' ($geId + ':SUCCEEDED') (($geFilas | ForEach-Object { [string]$_.graphRunId + ':' + [string]$_.estado }) -join '|')
}
finally {
    $ErrorActionPreference = 'Continue'
    Remove-Item -LiteralPath $geTmp -Recurse -Force -ErrorAction SilentlyContinue
    $ErrorActionPreference = 'Stop'
}
