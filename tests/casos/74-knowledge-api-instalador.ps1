# El escenario de docs/cambios/knowledge-api/spec.md que instala de verdad: KA-E54. Cada asercion
# nombra su KA-E54. Lo que no instala vive en tests/casos/74_knowledge_api.py.
#
# ASCII puro a proposito: un .ps1 con caracteres no ASCII necesita BOM (00-encoding-fuentes.ps1).
#
# Task 6 no cambia install.ps1 ni manifest.json: Copy-Arbol ya copia bin/ entero, y el paquete
# bin/conocimiento/ llega solo. Aca se instala en %TEMP% con el instalador real, y se mira desde el
# ARBOL INSTALADO, no desde la fabrica (KA-I30):
#   - el lock (harness.lock.json) lista los cuatro archivos de .claude\harness\bin\desarrollo\conocimiento\;
#   - un proceso de Python, con el arbol instalado como unica ruta de busqueda, hace
#     `acceso.lookup` de codebase/project-context y da OK;
#   - y `acceso.lookup` de memoria/id_rsa da ACCESS_DENIED, con el deny LEIDO del .claude\settings.json
#     que escribio el instalador (KM-34): se comprueba que el archivo trae la entrada, y despues que
#     una entrada agregada ahi, que la fabrica no tiene, tambien se aplica.
# Los valores son sinteticos: ningun secreto real. Todo se borra al final, aunque falle.

Set-Grupo 'knowledge-api - Knowledge Access en un proyecto instalado'

$kaInstalador = Join-Path $script:Raiz 'install.ps1'
$kaUtf8       = New-Object System.Text.UTF8Encoding $false
$kaTmp        = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-ka74-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $kaTmp -Force | Out-Null


function Invoke-KaProceso {
    <# Un proceso con stdout y stderr en UTF-8, sin pasar por la tuberia de PowerShell. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Directorio = '')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardInput  = $true
    $psi.StandardOutputEncoding = $kaUtf8
    $psi.StandardErrorEncoding  = $kaUtf8
    $psi.EnvironmentVariables['PYTHONDONTWRITEBYTECODE'] = '1'
    $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    if ($psi.EnvironmentVariables.ContainsKey('PYTHONPATH')) { $psi.EnvironmentVariables.Remove('PYTHONPATH') }
    if ($psi.EnvironmentVariables.ContainsKey('CLAUDE_PROJECT_DIR')) { $psi.EnvironmentVariables.Remove('CLAUDE_PROJECT_DIR') }
    if ($Directorio) { $psi.WorkingDirectory = $Directorio }
    $p = [System.Diagnostics.Process]::Start($psi)
    $salida  = $p.StandardOutput.ReadToEndAsync()
    $errores = $p.StandardError.ReadToEndAsync()
    $p.StandardInput.Close()
    if (-not $p.WaitForExit(300000)) { try { $p.Kill() } catch { }; return [pscustomobject]@{ Codigo = -1; Salida = ''; Errores = 'no termino en 300 s' } }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Salida = $salida.Result; Errores = $errores.Result }
}


function Invoke-KaLookup {
    <# `acceso.lookup` desde el arbol instalado: devuelve el proceso y su salida ya leida como JSON (o $null). #>
    param([string] $Script, [string] $BinInstalado, [string] $Proyecto, [string] $Corpus, [string] $Documento, [string] $Directorio)
    $r = Invoke-KaProceso -Archivo 'python' -Argumentos ('-I -B "' + $Script + '" "' + $BinInstalado + '" "' + $Proyecto + '" ' + $Corpus + ' ' + $Documento) -Directorio $Directorio
    $json = $null
    try { $json = $r.Salida | ConvertFrom-Json } catch { $json = $null }
    return [pscustomobject]@{ Codigo = $r.Codigo; Salida = $r.Salida; Errores = $r.Errores; Json = $json }
}


# El proceso que consulta. `-I` lo aisla: ni el directorio del guion, ni PYTHONPATH, ni el directorio de
# trabajo entran a sys.path. La UNICA ruta de busqueda que se agrega es la del arbol instalado, y el
# resultado dice de donde salio `acceso` para que la prueba lo compruebe.
$kaConsultar = Join-Path $kaTmp 'consultar.py'
$kaCodigoConsultar = @'
import json, os, sys
sys.dont_write_bytecode = True
bin_instalado, proyecto, corpus, documento = sys.argv[1:5]
sys.path.insert(0, bin_instalado)
from conocimiento import acceso
resultado = acceso.lookup(proyecto, {"corpus": corpus, "document": documento})
sys.stdout.write(json.dumps({"modulo": os.path.abspath(acceso.__file__), "resultado": resultado}, sort_keys=True))
'@
[System.IO.File]::WriteAllText($kaConsultar, $kaCodigoConsultar, $kaUtf8)

# Agrega una entrada al deny del .claude\settings.json que escribio el instalador. Es lo unico que toca.
$kaAgregarDeny = Join-Path $kaTmp 'agregar_deny.py'
$kaCodigoAgregar = @'
import io, json, sys
ruta, entrada = sys.argv[1:3]
with io.open(ruta, encoding="utf-8-sig") as f:
    doc = json.load(f)
doc["permissions"]["deny"].append(entrada)
with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
sys.stdout.write("ok")
'@
[System.IO.File]::WriteAllText($kaAgregarDeny, $kaCodigoAgregar, $kaUtf8)


try {
    $kaProy = Join-Path $kaTmp 'instalado'
    New-Item -ItemType Directory -Path $kaProy -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $kaProy 'CLAUDE.md'), "# Proyecto de prueba`r`n", $kaUtf8)

    $ErrorActionPreference = 'Continue'
    $kaSalida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                                 -File $kaInstalador -Project $kaProy -Usuario 'Ana Prueba' 2>&1 | Out-String
    $kaCodigo = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Assert-Igual 'KA-E54 el instalador, sin cambios, instala y sale con 0' 0 $kaCodigo

    # 1. El lock lista los cuatro archivos del paquete, y estan en disco.
    $kaBin = Join-Path $kaProy '.claude\harness\bin\desarrollo'
    $kaArchivos = @('__init__.py', 'acceso.py', 'corpus.py', 'recuperador_local.py')
    $kaLock = $null
    try { $kaLock = [System.IO.File]::ReadAllText((Join-Path $kaProy '.claude\harness.lock.json'), $kaUtf8) | ConvertFrom-Json } catch { $kaLock = $null }
    $kaRutas = @()
    if ($kaLock) { $kaRutas = @($kaLock.archivos | ForEach-Object { [string]$_.ruta }) }
    Assert-Verdadero 'KA-E54 se leyo el lockfile que escribio el instalador' ($kaRutas.Count -gt 0)
    foreach ($kaArchivo in $kaArchivos) {
        Assert-Verdadero "KA-E54 el lock lista .claude\harness\bin\desarrollo\conocimiento\$kaArchivo" ($kaRutas -contains ('.claude\harness\bin\desarrollo\conocimiento\' + $kaArchivo))
        Assert-Verdadero "KA-E54 y se instala bin\desarrollo\conocimiento\$kaArchivo" (Test-Path -LiteralPath (Join-Path $kaBin "conocimiento\$kaArchivo"))
    }
    $kaDelPaquete = @($kaRutas | Where-Object { $_ -like '.claude\harness\bin\desarrollo\conocimiento\*' } | Sort-Object)
    Assert-Igual 'KA-E54 el lock lista exactamente cuatro archivos de conocimiento\, ni uno mas' ($kaArchivos | Sort-Object | ForEach-Object { '.claude\harness\bin\desarrollo\conocimiento\' + $_ }) ($kaDelPaquete -join ' ')
    Assert-Igual 'KA-E54 son cuatro los archivos de conocimiento\ en el lock' 4 $kaDelPaquete.Count

    # El proyecto de prueba: un project-context.json en el corpus codebase y, en memoria, un archivo
    # que el deny nombra (id_rsa.md), uno que no (notas.md) y uno que solo el proyecto agregara.
    # Bytes explicitos, valores sinteticos.
    $kaCodebase = Join-Path $kaProy 'docs\codebase'
    $kaMemoria  = Join-Path $kaProy 'docs\conocimiento'
    New-Item -ItemType Directory -Path $kaCodebase -Force | Out-Null
    New-Item -ItemType Directory -Path $kaMemoria -Force | Out-Null
    $kaHash = 'sha256:' + ('a' * 64)
    [System.IO.File]::WriteAllText((Join-Path $kaCodebase 'project-context.json'), ("{`n  `"meta`": {`"context_hash`": `"$kaHash`"},`n  `"modulos`": []`n}`n"), $kaUtf8)
    [System.IO.File]::WriteAllText((Join-Path $kaMemoria 'id_rsa.md'), "MARCA-ID-RSA-KA54 contenido sintetico que no debe salir`n", $kaUtf8)
    [System.IO.File]::WriteAllText((Join-Path $kaMemoria 'notas.md'), "MARCA-NOTAS-KA54 una nota cualquiera`n", $kaUtf8)
    [System.IO.File]::WriteAllText((Join-Path $kaMemoria 'reservado.md'), "MARCA-RESERVADO-KA54 contenido sintetico que solo el proyecto reserva`n", $kaUtf8)

    $kaModuloInstalado = Join-Path $kaBin 'conocimiento\acceso.py'
    $kaModuloDeFabrica = Join-Path $script:Raiz 'harnesses\desarrollo\bin\conocimiento\acceso.py'

    # 2. lookup de codebase/project-context desde el arbol instalado da OK.
    $r = Invoke-KaLookup -Script $kaConsultar -BinInstalado $kaBin -Proyecto $kaProy -Corpus 'codebase' -Documento 'project-context' -Directorio $kaTmp
    Assert-Igual 'KA-E54 el proceso de lookup de codebase/project-context sale con 0' 0 $r.Codigo
    $kaModulo = ''
    $kaResultado = $null
    if ($r.Json) { $kaModulo = [string]$r.Json.modulo; $kaResultado = $r.Json.resultado }
    Assert-Verdadero 'KA-E54 acceso sale del arbol instalado, no de la fabrica' ($kaModulo -and $kaModulo.Equals($kaModuloInstalado, [System.StringComparison]::OrdinalIgnoreCase) -and -not $kaModulo.Equals($kaModuloDeFabrica, [System.StringComparison]::OrdinalIgnoreCase)) "modulo <$kaModulo>"
    $kaEstado = ''; $kaItems = @(); $kaTexto = ''; $kaCorpus = ''; $kaRuta = ''; $kaDerivacion = ''
    if ($kaResultado) {
        $kaEstado = [string]$kaResultado.status
        $kaItems = @($kaResultado.items)
        if ($kaItems.Count -gt 0) {
            $kaTexto = [string]$kaItems[0].excerpt.text
            $kaCorpus = [string]$kaItems[0].citation.corpus
            $kaRuta = [string]$kaItems[0].locator.path
            $kaDerivacion = [string]$kaItems[0].derivation
        }
    }
    Assert-Igual 'KA-E54 lookup de codebase/project-context da OK en el instalado' 'OK' $kaEstado
    Assert-Igual 'KA-E54 con un solo item' 1 $kaItems.Count
    Assert-Igual 'KA-E54 de la cita del corpus codebase' 'codebase' $kaCorpus
    Assert-Igual 'KA-E54 con el localizador relativo al proyecto' 'docs/codebase/project-context.json' $kaRuta
    Assert-Igual 'KA-E54 derivado GENERATED, como lo declara el corpus' 'GENERATED' $kaDerivacion
    Assert-Contiene 'KA-E54 y el tramo es el documento que se escribio' $kaHash $kaTexto

    # 3. lookup de memoria/id_rsa da ACCESS_DENIED, con el deny que escribio el instalador.
    $kaSettings = Join-Path $kaProy '.claude\settings.json'
    Assert-Verdadero 'KA-E54 el instalador escribio .claude\settings.json' (Test-Path -LiteralPath $kaSettings)
    $kaDeny = @()
    try { $kaDeny = @(([System.IO.File]::ReadAllText($kaSettings, $kaUtf8) | ConvertFrom-Json).permissions.deny) } catch { $kaDeny = @() }
    Assert-Verdadero 'KA-E54 el .claude\settings.json instalado trae la entrada del deny para id_rsa.*' ($kaDeny -contains 'Read(./**/id_rsa.*)')

    $r = Invoke-KaLookup -Script $kaConsultar -BinInstalado $kaBin -Proyecto $kaProy -Corpus 'memoria' -Documento 'id_rsa' -Directorio $kaTmp
    Assert-Igual 'KA-E54 el proceso de lookup de memoria/id_rsa sale con 0' 0 $r.Codigo
    $kaResultado = $null
    if ($r.Json) { $kaResultado = $r.Json.resultado }
    $kaEstado = ''; $kaCodigoError = ''; $kaMotivo = ''; $kaItems = @()
    if ($kaResultado) {
        $kaEstado = [string]$kaResultado.status
        $kaItems = @($kaResultado.items)
        if ($kaResultado.error) { $kaCodigoError = [string]$kaResultado.error.code; $kaMotivo = [string]$kaResultado.error.reason }
    }
    Assert-Igual 'KA-E54 lookup de memoria/id_rsa es ERROR en el instalado' 'ERROR' $kaEstado
    Assert-Igual 'KA-E54 con ACCESS_DENIED, por el deny del settings.json instalado' 'ACCESS_DENIED' $kaCodigoError
    Assert-Igual 'KA-E54 el motivo es DENIED, no POLICY_UNAVAILABLE ni otro' 'DENIED' $kaMotivo
    Assert-Igual 'KA-E54 y sin items: el documento denegado no se sirve' 0 $kaItems.Count
    Assert-Verdadero 'KA-E54 el contenido de id_rsa.md no sale' (-not $r.Salida.Contains('MARCA-ID-RSA-KA54'))

    # El deny no es un portazo: un documento de memoria que no nombra se sirve igual.
    $r = Invoke-KaLookup -Script $kaConsultar -BinInstalado $kaBin -Proyecto $kaProy -Corpus 'memoria' -Documento 'notas' -Directorio $kaTmp
    $kaEstado = ''
    $kaTexto = ''
    if ($r.Json) {
        $kaEstado = [string]$r.Json.resultado.status
        $kaItems = @($r.Json.resultado.items)
        if ($kaItems.Count -gt 0) { $kaTexto = [string]$kaItems[0].excerpt.text }
    }
    Assert-Igual 'KA-E54 lookup de memoria/notas, que el deny no nombra, da OK en el instalado' 'OK' $kaEstado
    Assert-Contiene 'KA-E54 y su contenido sale' 'MARCA-NOTAS-KA54' $kaTexto

    # El deny sale de ESE archivo, no de la fabrica: una entrada que solo el proyecto agrega se aplica.
    $kaEntradaDelProyecto = 'Read(./docs/conocimiento/reservado.md)'
    $r = Invoke-KaLookup -Script $kaConsultar -BinInstalado $kaBin -Proyecto $kaProy -Corpus 'memoria' -Documento 'reservado' -Directorio $kaTmp
    $kaEstado = ''
    if ($r.Json) { $kaEstado = [string]$r.Json.resultado.status }
    Assert-Igual 'KA-E54 antes de agregar la entrada, memoria/reservado se sirve: el deny de la fabrica no la nombra' 'OK' $kaEstado

    $r = Invoke-KaProceso -Archivo 'python' -Argumentos ('-I -B "' + $kaAgregarDeny + '" "' + $kaSettings + '" "' + $kaEntradaDelProyecto + '"') -Directorio $kaTmp
    Assert-Igual 'KA-E54 se agrego al .claude\settings.json instalado la entrada propia del proyecto' 'ok' $r.Salida
    $r = Invoke-KaLookup -Script $kaConsultar -BinInstalado $kaBin -Proyecto $kaProy -Corpus 'memoria' -Documento 'reservado' -Directorio $kaTmp
    $kaCodigoError = ''
    $kaMotivo = ''
    if ($r.Json -and $r.Json.resultado.error) { $kaCodigoError = [string]$r.Json.resultado.error.code; $kaMotivo = [string]$r.Json.resultado.error.reason }
    Assert-Igual 'KA-E54 con la entrada agregada, memoria/reservado da ACCESS_DENIED: el deny se lee del settings.json instalado' 'ACCESS_DENIED' $kaCodigoError
    Assert-Igual 'KA-E54 por DENIED' 'DENIED' $kaMotivo
    Assert-Verdadero 'KA-E54 y su contenido no sale' (-not $r.Salida.Contains('MARCA-RESERVADO-KA54'))
    $r = Invoke-KaLookup -Script $kaConsultar -BinInstalado $kaBin -Proyecto $kaProy -Corpus 'memoria' -Documento 'id_rsa' -Directorio $kaTmp
    $kaCodigoError = ''
    if ($r.Json -and $r.Json.resultado.error) { $kaCodigoError = [string]$r.Json.resultado.error.code }
    Assert-Igual 'KA-E54 y id_rsa sigue denegado: la entrada agregada no desplaza a las del instalador' 'ACCESS_DENIED' $kaCodigoError
}
finally {
    $ErrorActionPreference = 'Continue'
    Remove-Item -LiteralPath $kaTmp -Recurse -Force -ErrorAction SilentlyContinue
    $ErrorActionPreference = 'Stop'
}
