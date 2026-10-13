# El escenario de docs/cambios/minimal-execution-engine/spec.md que instala de verdad: ME-E26. Cada
# asercion nombra su ME-Enn. Lo que no instala vive en tests/casos/72_motor_de_ejecucion.py.
#
# ASCII puro a proposito: un .ps1 con caracteres no ASCII necesita BOM (00-encoding-fuentes.ps1).
#
# Task 4 no cambia install.ps1 ni manifest.json: Copy-Arbol ya copia bin/ entero, y el motor llega
# solo. Aca se instala en %TEMP%, se arma un plan listo, y `dev-harness.py ejecutar` del arbol
# instalado corre una WorkUnit con el Host falso (tests/fixtures/host_falso.py), configurado en
# `ejecucion.comandoHost` de harness.config.json. Nunca el Claude Code real. Todo se borra al final.

Set-Grupo 'minimal-execution-engine - el motor en un proyecto instalado'

$meInstalador = Join-Path $script:Raiz 'install.ps1'
$meHostFalso  = Join-Path $script:Raiz 'tests\fixtures\host_falso.py'
$meUtf8       = New-Object System.Text.UTF8Encoding $false
$meTmp        = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-me72-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $meTmp -Force | Out-Null


function Invoke-MeProceso {
    <# Un proceso con stdout y stderr en UTF-8, sin pasar por la tuberia de PowerShell. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Directorio = '', [string] $Guion = '')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardInput  = $true
    $psi.StandardOutputEncoding = $meUtf8
    $psi.StandardErrorEncoding  = $meUtf8
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
# una unidad, y el Host falso en harness.config.json.
$mePreparar = Join-Path $meTmp 'preparar.py'
$meCodigoPreparar = @'
import importlib.util, io, json, os, subprocess, sys
from pathlib import Path
proy, raiz, host, guion = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("m64_me26", os.path.join(raiz, "tests", "casos", "64_modelo_de_dominio.py"))
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
m._json(Path(proy) / "prop-1.json", m._propuesta([m._unidad("analizar-api")]))
ruta = Path(proy) / ".claude" / "harness.config.json"
config = json.loads(ruta.read_text(encoding="utf-8-sig")) if ruta.is_file() else {}
config["ejecucion"] = {"comandoHost": [sys.executable, host], "limiteSegundos": 120}
ruta.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
Path(guion).write_text("{}", encoding="utf-8")
sys.stdout.write("ok")
'@
[System.IO.File]::WriteAllText($mePreparar, $meCodigoPreparar, $meUtf8)


try {
    $meProy = Join-Path $meTmp 'instalado'
    New-Item -ItemType Directory -Path $meProy -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $meProy 'CLAUDE.md'), "# Proyecto de prueba`r`n", $meUtf8)

    $ErrorActionPreference = 'Continue'
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $meInstalador -Project $meProy -Usuario 'Ana Prueba' 2>&1 | Out-String
    $codigo = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Assert-Igual 'ME-E26 el instalador, sin cambios, instala y sale con 0' 0 $codigo

    $meBin = Join-Path $meProy '.claude\harness\bin\desarrollo'
    foreach ($modulo in @('motor.py', 'admision.py', 'registro.py', 'evidencia.py', 'proceso.py', 'host_claude_code.py')) {
        Assert-Verdadero "ME-E26 se instala bin\desarrollo\ejecucion\$modulo" (Test-Path -LiteralPath (Join-Path $meBin "ejecucion\$modulo"))
    }

    $meGuion = Join-Path $meTmp 'guion.json'
    $r = Invoke-MeProceso -Archivo 'python' -Argumentos ('"' + $mePreparar + '" "' + $meProy + '" "' + $script:Raiz + '" "' + $meHostFalso + '" "' + $meGuion + '"') -Directorio $meTmp
    Assert-Igual 'ME-E26 el proyecto de prueba se armo' 'ok' $r.Salida

    $meCli = Join-Path $meBin 'dev-harness.py'
    $r = Invoke-MeProceso -Archivo 'python' -Argumentos ('"' + $meCli + '" plan GCBA-72 --propuesta prop-1.json --proyecto "' + $meProy + '"') -Directorio $meProy
    Assert-Igual 'ME-E26 plan --propuesta del arbol instalado sale con 0' 0 $r.Codigo

    $r = Invoke-MeProceso -Archivo 'python' -Argumentos ('"' + $meCli + '" ejecutar GCBA-72 --unidad analizar-api --json --proyecto "' + $meProy + '"') -Directorio $meProy -Guion $meGuion
    Assert-Igual 'ME-E26 ejecutar del arbol instalado sale con 0' 0 $r.Codigo
    $resultado = $null
    try { $resultado = $r.Salida | ConvertFrom-Json } catch { $resultado = $null }
    $estado = ''
    $exe = ''
    if ($resultado) { $estado = [string]$resultado.status; $exe = [string]$resultado.executionId }
    Assert-Igual 'ME-E26 la Execution queda SUCCEEDED en el instalado' 'SUCCEEDED' $estado
    $meResultado = Join-Path $meProy (".claude\ejecuciones\GCBA-72\" + $exe + "\result.json")
    Assert-Verdadero 'ME-E26 bajo .claude\ejecuciones\GCBA-72\<executionId>\result.json' ($exe -and (Test-Path -LiteralPath $meResultado))
}
finally {
    $ErrorActionPreference = 'Continue'
    Remove-Item -LiteralPath $meTmp -Recurse -Force -ErrorAction SilentlyContinue
    $ErrorActionPreference = 'Stop'
}
