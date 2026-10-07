# Los escenarios de docs/cambios/canonical-domain-model/spec.md que instalan de verdad: E-44 y
# E-45. Cada asercion nombra su E-nn. Lo que no instala vive en tests/casos/64_modelo_de_dominio.py.
#
# ASCII puro a proposito: un .ps1 con caracteres no ASCII necesita BOM (00-encoding-fuentes.ps1).
#
# E-45 instala con el instalador de 4c6f0f3 (0.29.0), sacado con `git archive` a un temporal y
# nunca de una copia versionada. Sin esa historia -un clon superficial- falla en rojo con el
# motivo. Todo se instala en %TEMP%, y se borra al final.

Set-Grupo 'canonical-domain-model - el plan en un proyecto instalado'

$dmInstalador = Join-Path $script:Raiz 'install.ps1'
$dmBase       = '4c6f0f3'
$dmClave      = 'GCBA-64'
$dmUsuario    = 'Ana Prueba'
$dmUtf8       = New-Object System.Text.UTF8Encoding $false
$dmTmp        = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-dm64-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $dmTmp -Force | Out-Null


function Invoke-DmInstalador {
    <# Un install.ps1 por -File, como lo corre una persona. #>
    param([string] $Instalador, [string[]] $Argumentos)
    $ErrorActionPreference = 'Continue'
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $Instalador @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}


function Invoke-DmProceso {
    <# Un proceso con stdout y stderr en UTF-8, sin pasar por la tuberia de PowerShell. #>
    param([string] $Archivo, [string] $Argumentos, [string] $Directorio = '')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Archivo
    $psi.Arguments              = $Argumentos
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardInput  = $true
    $psi.StandardOutputEncoding = $dmUtf8
    $psi.StandardErrorEncoding  = $dmUtf8
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


function New-DmProyecto {
    param([string] $Nombre)
    $d = Join-Path $dmTmp $Nombre
    New-Item -ItemType Directory -Path $d -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $d 'CLAUDE.md'), "# Proyecto de prueba`r`n", $dmUtf8)
    return $d
}


function Write-DmTexto {
    param([string] $Ruta, [string] $Texto)
    $carpeta = Split-Path -Parent $Ruta
    if (-not (Test-Path -LiteralPath $carpeta)) { New-Item -ItemType Directory -Path $carpeta -Force | Out-Null }
    [System.IO.File]::WriteAllText($Ruta, $Texto, $dmUtf8)
}


function Invoke-DmCli {
    <# Un dev-harness.py -el de la fabrica o el instalado- contra un proyecto. #>
    param([string] $Cli, [string] $Proyecto, [string] $Argumentos)
    return (Invoke-DmProceso -Archivo 'python' -Argumentos ('"' + $Cli + '" ' + $Argumentos + ' --proyecto "' + $Proyecto + '"') `
                             -Directorio $Proyecto)
}


function Get-DmCliInstalado {
    param([string] $Proyecto)
    return (Join-Path $Proyecto '.claude\harness\bin\desarrollo\dev-harness.py')
}


# La sonda: las comparaciones de JSON, en Python, en un proceso aparte.
$dmSonda = Join-Path $dmTmp 'sonda.py'
$dmCodigoSonda = @'
import glob, json, os, re, sys
accion = sys.argv[1]


def leer(ruta):
    with open(ruta, encoding="utf-8-sig") as f:
        return json.load(f)


def normal(doc):
    """E-44: lo que puede cambiar entre la fabrica y un proyecto instalado."""
    doc = json.loads(json.dumps(doc))
    doc["meta"].pop("generated_at", None)
    doc["meta"].pop("harness_version", None)
    for h in doc.get("planHistory") or []:
        h.pop("timestamp", None)
    return doc


def dif(x, y, ruta, salida):
    """[(ruta, fabrica, instalado)] de cada hoja que difiere."""
    if type(x) is not type(y):
        salida.append((ruta, x, y))
    elif isinstance(x, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x or k not in y:
                salida.append((ruta + "." + k, x.get(k), y.get(k)))
            else:
                dif(x[k], y[k], ruta + "." + k, salida)
    elif isinstance(x, list):
        if len(x) != len(y):
            salida.append((ruta + "[]", len(x), len(y)))
        else:
            for i, (a, b) in enumerate(zip(x, y)):
                dif(a, b, "%s[%d]" % (ruta, i), salida)
    elif x != y:
        salida.append((ruta, x, y))


# E-44, la segunda excepcion: lo normativo que depende de controles/, que no se instala. Hoy es
# exactamente el developmentStandardBaseline de C3 de ES0902, en cada unidad.
DE_CONTROLES = re.compile(r"^\$\.workUnits\[\d+\]\.normative\.standards\.ES0902\.rules\.C3"
                          r"\.developmentStandardBaseline(\.|\[|$)")


def c3(doc):
    return [((((u.get("normative") or {}).get("standards") or {}).get("ES0902") or {})
             .get("rules") or {}).get("C3", {}).get("developmentStandardBaseline", {}).get("status")
            for u in doc.get("workUnits") or []]


if accion == "e44-otras":
    salida = []
    dif(normal(leer(sys.argv[2])), normal(leer(sys.argv[3])), "$", salida)
    otras = ["%s: %r / %r" % d for d in salida if not DE_CONTROLES.match(d[0])]
    extra = ["... y %d mas" % (len(otras) - 12)] if len(otras) > 12 else []
    sys.stdout.write("\n".join(otras[:12] + extra))
elif accion == "e44-c3":
    fabrica, instalado = c3(leer(sys.argv[2])), c3(leer(sys.argv[3]))
    ok = (len(fabrica) > 0 and len(fabrica) == len(instalado)
          and all(f == "RESOLVED" for f in fabrica) and all(i == "UNRESOLVED" for i in instalado))
    sys.stdout.write("conocida" if ok else "fabrica %r / instalado %r" % (fabrica, instalado))
elif accion == "version":
    doc = leer(sys.argv[2])
    sys.stdout.write("%s|%s" % (doc["meta"]["schema_version"], doc["meta"]["plan_version"]))
elif accion == "historia":
    antes, despues = leer(sys.argv[2]), leer(sys.argv[3])
    n = len(antes["planHistory"])
    ok = despues["planHistory"][:n] == antes["planHistory"] and len(despues["planHistory"]) == n + 1
    sys.stdout.write("conservada" if ok else "perdida: %d entradas antes, %d despues"
                     % (n, len(despues["planHistory"])))
elif accion == "contexto-de-la-tarea":
    # Pisado por docs/cambios/integracion-flow-governance-0-31/spec.md: la Ficha nombra el
    # repositorio de la tarea y el TaskContext lleva su hash de verdad, con el hash_de de la
    # fabrica. Es lo que la compuerta de REFUTATION exige (flujo-precondiciones).
    import importlib.util
    ruta, url, armador = sys.argv[2:5]
    spec = importlib.util.spec_from_file_location("armador_dm64", armador)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    doc = leer(ruta)
    doc["project"]["ficha"]["summary"] = "El repositorio es " + url
    doc["meta"]["context_hash"] = m.hash_de(doc)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, ensure_ascii=False))
    sys.stdout.write("listo")
elif accion == "listo-para-la-compuerta":
    # Pisado por docs/cambios/integracion-flow-governance-0-31/spec.md: un 1.0 de 4c6f0f3 no trae
    # flowPreconditions y la compuerta no lo deja compilar nunca. Se le pone la evaluacion real de
    # PLANNING del proyecto, con el codigo instalado, como la traia un 1.0 de las Waves (D5).
    # Nada mas del plan cambia.
    proyecto, plan_ruta, contexto_ruta, bin_dir = sys.argv[2:6]
    sys.path.insert(0, bin_dir)
    from flujo import precondiciones as flujo_pre
    from orquestacion import plan as orq_plan
    plan, contexto = leer(plan_ruta), leer(contexto_ruta)
    plan["flowPreconditions"] = orq_plan._precondiciones(
        flujo_pre.de_planificacion(contexto, None, proyecto, {}), plan["workUnits"])
    with open(plan_ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write("%s|%s" % (plan["flowPreconditions"]["status"],
                                (plan["flowPreconditions"].get("repository") or {}).get("status")))
elif accion == "unidades":
    us = [leer(p) for p in sorted(glob.glob(os.path.join(sys.argv[2], "*.json")))]
    sys.stdout.write("\n".join("%s|%s|%s|%s" % (u["refutationUnitId"], u["workUnitId"],
                                                u["standard"]["ruleKey"], u["taskKey"]) for u in us))
'@
[System.IO.File]::WriteAllText($dmSonda, $dmCodigoSonda, $dmUtf8)


function Invoke-DmSonda {
    param([string] $Argumentos)
    $r = Invoke-DmProceso -Archivo 'python' -Argumentos ('"' + $dmSonda + '" ' + $Argumentos)
    if ($r.Codigo -ne 0) { return "la sonda fallo: $($r.Errores)" }
    return $r.Salida.Trim()
}


# El mismo TaskContext y la misma propuesta para los dos lados. Sin normativeEvidence (E-44): la
# evidencia de Vu3 a Vu10 apunta a controles/, que no se instala, y eso ya esta documentado. Lo
# que igual depende de controles/ -el C3 de ES0902- es la segunda excepcion del escenario.
$dmContexto = @'
{"meta": {"task_key": "GCBA-64", "context_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
 "task": {"key": "GCBA-64", "type": "Historia de Usuario", "title": "Filtro por fecha en el listado",
          "acceptance_criteria": ["Filtra por rango", "Muestra vacio"]},
 "project": {"ficha": {"key": "GCBA-7", "rules": ["Un tramite no se borra, se anula"]}},
 "documentation": {"items": [{"doc_id": "10"}, {"doc_id": "11"}]},
 "repository": {"project": {"name": "tramites/backoffice"}}}
'@
$dmPropuesta = @'
{"objective": "Implementar el filtro por fecha", "domains": ["backend", "security", "frontend"],
 "policies": ["una politica"],
 "workUnits": [
  {"id": "leer", "objective": "leer el listado", "domain": "backend",
   "requiredCapabilities": ["repository.read"], "dependencies": [], "signals": ["novelty"]},
  {"id": "asegurar", "objective": "revisar la sesion", "domain": "security",
   "requiredCapabilities": ["no.existe"], "dependencies": ["leer"],
   "signals": ["ambiguity", "security_impact", "architectural_impact"]},
  {"id": "pantalla", "objective": "armar el filtro", "domain": "frontend",
   "requiredCapabilities": [], "dependencies": [], "signals": [],
   "normativeSignals": {"citizenFacing": true}}]}
'@
$dmPropuestaNueva = @'
{"objective": "Implementar el filtro por fecha", "domains": ["backend"], "policies": [],
 "workUnits": [
  {"id": "wu-1", "objective": "leer el listado", "domain": "backend",
   "requiredCapabilities": ["repository.read"], "dependencies": [], "signals": []},
  {"id": "wu-2", "objective": "agregar el filtro", "domain": "backend",
   "requiredCapabilities": ["repository.read"], "dependencies": ["wu-1"], "signals": []}]}
'@
$dmPropuestaVieja = @'
{"objective": "Implementar el filtro por fecha", "domains": ["backend"], "policies": [],
 "workUnits": [
  {"id": "wu-1", "objective": "leer el listado", "domain": "backend",
   "requiredCapabilities": ["repository.read"], "dependencies": [], "signals": []}]}
'@
$dmScope = '{"schema_version": "refutation-scope/1.0", "workUnits": {"wu-1": [{"scopeId": "s", "source": "workUnitFiles", "paths": ["src/sesion.py"]}], "wu-2": [{"scopeId": "s", "source": "workUnitFiles", "paths": ["src/sesion.py"]}]}}'


function Set-DmTarea {
    <# El TaskContext puesto a mano y las propuestas, como prop-1.json y prop-2.json. #>
    param([string] $Proyecto, [string] $Propuesta, [string] $Otra = '')
    Write-DmTexto (Join-Path $Proyecto ".claude\contextos\$dmClave.json") $dmContexto
    Write-DmTexto (Join-Path $Proyecto 'prop-1.json') $Propuesta
    if ($Otra) { Write-DmTexto (Join-Path $Proyecto 'prop-2.json') $Otra }
}


try {
    # -- E-44: el mismo plan desde la fabrica y desde un proyecto instalado --------------------
    $dmInst = New-DmProyecto 'instalado'
    $r = Invoke-DmInstalador $dmInstalador @('-Project', $dmInst, '-Usuario', $dmUsuario)
    Assert-Igual 'E-44 el instalador de ahora instala y sale con 0' 0 $r.Codigo
    $dmFab = New-DmProyecto 'fabrica'
    Set-DmTarea $dmInst $dmPropuesta
    Set-DmTarea $dmFab $dmPropuesta
    # La fabrica lee el mismo registro de capacidades y la misma configuracion que el instalado.
    foreach ($rel in @('.claude\harness.capacidades.json', '.claude\harness.config.json')) {
        $origen = Join-Path $dmInst $rel
        Assert-Verdadero "E-44 el proyecto instalado tiene $rel" (Test-Path -LiteralPath $origen)
        if (Test-Path -LiteralPath $origen) { Copy-Item -LiteralPath $origen -Destination (Join-Path $dmFab $rel) -Force }
    }
    $cliFab = Join-Path $script:Raiz 'harnesses\desarrollo\bin\dev-harness.py'
    $rFab  = Invoke-DmCli $cliFab $dmFab "plan $dmClave --propuesta `"$(Join-Path $dmFab 'prop-1.json')`""
    $rInst = Invoke-DmCli (Get-DmCliInstalado $dmInst) $dmInst "plan $dmClave --propuesta `"$(Join-Path $dmInst 'prop-1.json')`""
    Assert-Igual 'E-44 el plan se arma desde la fabrica' 0 $rFab.Codigo
    Assert-Igual 'E-44 el plan se arma en el proyecto instalado' 0 $rInst.Codigo
    $planFab  = Join-Path $dmFab ".claude\planes\$dmClave.json"
    $planInst = Join-Path $dmInst ".claude\planes\$dmClave.json"
    if ((Test-Path -LiteralPath $planFab) -and (Test-Path -LiteralPath $planInst)) {
        # Las dos excepciones de E-44 (corregido durante la construccion): generated_at,
        # harness_version y planHistory[].timestamp, y lo que depende de controles/, que hoy es
        # el developmentStandardBaseline de C3. La segunda no se esconde: tiene que ser la conocida.
        Assert-Vacio 'E-44 fuera de las dos excepciones, los dos planes son iguales' `
            (Invoke-DmSonda "e44-otras `"$planFab`" `"$planInst`"")
        Assert-Igual 'E-44 la diferencia de C3 es la conocida: RESOLVED en la fabrica, UNRESOLVED en el instalado' `
            'conocida' (Invoke-DmSonda "e44-c3 `"$planFab`" `"$planInst`"")
    } else {
        Assert-Verdadero 'E-44 hay dos planes que comparar' $false ($rFab.Errores + $rInst.Errores)
    }

    # -- E-45: un proyecto de 4c6f0f3, actualizado con el instalador de ahora --------------------
    $dmBaseOk = $false
    $dmMotivo = ''
    $g = Invoke-DmProceso -Archivo 'git' -Argumentos ('-C "' + $script:Raiz + '" cat-file -e ' + $dmBase + '^{commit}')
    if ($g.Codigo -ne 0) {
        $dmMotivo = "no esta el commit $dmBase en este clon (un clon superficial?): no hay con que instalar"
    } else {
        $zip = Join-Path $dmTmp 'base.zip'
        $g = Invoke-DmProceso -Archivo 'git' -Argumentos ('-C "' + $script:Raiz + '" archive --format=zip -o "' + $zip + '" ' + $dmBase +
                                                         ' install.ps1 VERSION manifest.json comun harnesses normativa/extractos tests/payloads tests/medir_barra.py')
        if ($g.Codigo -ne 0) {
            $dmMotivo = "git archive $dmBase fallo: $($g.Errores)"
        } else {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $dmRepoViejo = Join-Path $dmTmp 'repo-0.29.0'
            [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $dmRepoViejo)
            $dmInstaladorViejo = Join-Path $dmRepoViejo 'install.ps1'
            $dmBaseOk = $true
        }
    }
    if (-not $dmBaseOk) { Assert-Verdadero "E-45 la linea de base $dmBase esta disponible" $false $dmMotivo }

    if ($dmBaseOk) {
        $dmViejo = New-DmProyecto 'de-0.29.0'
        $r = Invoke-DmInstalador $dmInstaladorViejo @('-Project', $dmViejo, '-Usuario', $dmUsuario)
        Assert-Igual 'E-45 el instalador de 4c6f0f3 instala y sale con 0' 0 $r.Codigo
        Set-DmTarea $dmViejo $dmPropuestaVieja $dmPropuestaNueva
        # Pisado por docs/cambios/integracion-flow-governance-0-31/spec.md: el proyecto es un
        # checkout cuyo origin es el repositorio que nombra la Ficha, y el TaskContext esta
        # vigente. Sin eso la compuerta de REFUTATION frena el refute --compile de despues.
        $dmUrlRepo = 'https://gitlab.example/tramites/backoffice'
        $g1 = Invoke-DmProceso -Archivo 'git' -Argumentos ('-C "' + $dmViejo + '" init -q')
        $g2 = Invoke-DmProceso -Archivo 'git' -Argumentos ('-C "' + $dmViejo + '" remote add origin ' + $dmUrlRepo + '.git')
        Assert-Igual 'E-45 el proyecto es un checkout con el origin de la tarea' '0|0' "$($g1.Codigo)|$($g2.Codigo)"
        $dmRutaContexto = Join-Path $dmViejo ".claude\contextos\$dmClave.json"
        Assert-Igual 'E-45 el TaskContext nombra el repositorio y lleva su hash' 'listo' `
            (Invoke-DmSonda "contexto-de-la-tarea `"$dmRutaContexto`" $dmUrlRepo `"$(Join-Path $script:Raiz 'comun\bin\contexto-armar.py')`"")
        Write-DmTexto (Join-Path $dmViejo 'src\sesion.py') "TIMEOUT = 900`n"
        Write-DmTexto (Join-Path $dmViejo ".claude\refutaciones\$dmClave\scope.json") $dmScope
        $cliViejo = Get-DmCliInstalado $dmViejo
        $r = Invoke-DmCli $cliViejo $dmViejo "plan $dmClave --propuesta `"$(Join-Path $dmViejo 'prop-1.json')`""
        Assert-Igual 'E-45 el CLI de 4c6f0f3 escribe el plan' 0 $r.Codigo
        $dmPlan = Join-Path $dmViejo ".claude\planes\$dmClave.json"
        Assert-Igual 'E-45 es un plan orchestration-plan/1.0' 'orchestration-plan/1.0|1' (Invoke-DmSonda "version `"$dmPlan`"")
        $r = Invoke-DmCli $cliViejo $dmViejo "refute $dmClave --compile"
        Assert-Igual 'E-45 el CLI de 4c6f0f3 compila la refutacion' 0 $r.Codigo
        $dmUnidades = Join-Path $dmViejo ".claude\refutaciones\$dmClave\units"
        $dmUnidadesViejas = Invoke-DmSonda "unidades `"$dmUnidades`""
        Assert-Verdadero 'E-45 la refutacion compilada tiene unidades' ([bool]$dmUnidadesViejas) $r.Errores
        $dmCopiaPlan = Join-Path $dmTmp 'plan-1.0.json'
        Copy-Item -LiteralPath $dmPlan -Destination $dmCopiaPlan -Force
        $dmHashPlan = (Get-FileHash -LiteralPath $dmPlan -Algorithm SHA256).Hash

        $r = Invoke-DmInstalador $dmInstalador @('-Project', $dmViejo, '-Update')
        Assert-Igual 'E-45 -Update con el instalador de ahora sale con 0' 0 $r.Codigo
        $schemaInstalado = Join-Path $dmViejo '.claude\harness\schemas\orchestration-plan.schema.json'
        # Pisado por docs/cambios/integracion-flow-governance-0-31/spec.md (E-01, E-15): el contrato es 2.1.
        Assert-Contiene 'E-45 E-01 (integracion) despues del -Update el schema instalado es orchestration-plan/2.1' `
            '"$id": "orchestration-plan/2.1"' ([System.IO.File]::ReadAllText($schemaInstalado, $dmUtf8))
        Assert-Igual 'E-45 el -Update no toca el plan' $dmHashPlan (Get-FileHash -LiteralPath $dmPlan -Algorithm SHA256).Hash

        $cliNuevo = Get-DmCliInstalado $dmViejo
        # Pisado por docs/cambios/integracion-flow-governance-0-31/spec.md: el 1.0 con la
        # evaluacion de PLANNING (ver la sonda listo-para-la-compuerta). Lo que se afirma sigue
        # siendo que refute --compile lo lee sin reescribirlo.
        Assert-Igual 'E-45 el 1.0 lleva flowPreconditions READY con el repositorio MATCHED' 'READY|MATCHED' `
            (Invoke-DmSonda "listo-para-la-compuerta `"$dmViejo`" `"$dmPlan`" `"$dmRutaContexto`" `"$(Split-Path -Parent $cliNuevo)`"")
        Assert-Igual 'E-45 sigue siendo un plan orchestration-plan/1.0' 'orchestration-plan/1.0|1' (Invoke-DmSonda "version `"$dmPlan`"")
        $dmHashListo = (Get-FileHash -LiteralPath $dmPlan -Algorithm SHA256).Hash
        $r = Invoke-DmCli $cliNuevo $dmViejo "refute $dmClave --compile"
        Assert-Igual 'E-45 refute --compile funciona sobre el plan 1.0' 0 $r.Codigo
        Assert-Igual 'E-45 y no lo regenera: el plan queda igual, byte a byte' $dmHashListo `
            (Get-FileHash -LiteralPath $dmPlan -Algorithm SHA256).Hash
        Assert-Igual 'E-45 y compila las mismas unidades que antes del -Update' $dmUnidadesViejas `
            (Invoke-DmSonda "unidades `"$dmUnidades`"")

        $r = Invoke-DmCli $cliNuevo $dmViejo "plan $dmClave --replanificar `"$(Join-Path $dmViejo 'prop-2.json')`" --motivo `"suma una unidad`""
        Assert-Igual 'E-45 --replanificar lee el plan 1.0 y sale con 0' 0 $r.Codigo
        Assert-Igual 'E-45 E-15 (integracion) --replanificar lo reescribe como orchestration-plan/2.1, version 2' `
            'orchestration-plan/2.1|2' (Invoke-DmSonda "version `"$dmPlan`"")
        Assert-Igual 'E-45 sin perder la historia' 'conservada' (Invoke-DmSonda "historia `"$dmCopiaPlan`" `"$dmPlan`"")
    }
}
finally {
    if (Test-Path -LiteralPath $dmTmp) { Remove-Item -LiteralPath $dmTmp -Recurse -Force -ErrorAction SilentlyContinue }
}
