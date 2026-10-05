# E-17 y E-22 de docs/cambios/integrity-cleanup/spec.md (Wave 6), la mitad de PowerShell.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM (ver
# 00-encoding-fuentes.ps1).
#
# Las dos decisiones de -Doctor viven en funciones de install.ps1. Se las saca del script con el
# parser de PowerShell y se las corre sueltas: correr -Doctor entero pide un proyecto instalado,
# y lo que se prueba es la regla, no la instalacion.

Set-Grupo 'Instalador - lo que -Doctor afirma (Wave 6)'

$instalador66 = Join-Path $script:Raiz 'install.ps1'
$tokens66 = $null
$errores66 = $null
$ast66 = [System.Management.Automation.Language.Parser]::ParseFile($instalador66, [ref]$tokens66, [ref]$errores66)
$funciones66 = $ast66.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)

foreach ($nombre in @('Get-NivelDeLaBarra', 'Test-EsAliasDeLaStore')) {
    $f = $funciones66 | Where-Object { $_.Name -eq $nombre } | Select-Object -First 1
    Assert-Verdadero "E-17/E-22 install.ps1 define $nombre" ($null -ne $f)
    if ($f) { Invoke-Expression $f.Extent.Text }
}

# E-17 - la barra en OK solo si esta ACTIVE.
if (Get-Command Get-NivelDeLaBarra -ErrorAction SilentlyContinue) {
    Assert-Igual 'E-17 ACTIVE es ok' 'ok' (Get-NivelDeLaBarra 'ACTIVE')
    foreach ($estado in @('CONFIGURED', 'RELOAD_REQUIRED', 'INSTALLED', 'ERROR', 'UNRESOLVED', 'NOT_CONFIGURED')) {
        Assert-Igual "E-17 $estado no es ok" 'aviso' (Get-NivelDeLaBarra $estado)
    }
}
$texto66 = Get-Content -Raw -Encoding UTF8 $instalador66
Assert-Verdadero 'E-17 -Doctor decide con Get-NivelDeLaBarra' ($texto66.Contains('(Get-NivelDeLaBarra $estadoBarra) -eq ''ok'''))
Assert-Verdadero 'E-17 y CONFIGURED ya no va con ACTIVE al OK' (-not $texto66.Contains("-in @('ACTIVE', 'CONFIGURED')"))

# E-22 - el alias de la Store se reconoce, y -Doctor lo avisa.
if (Get-Command Test-EsAliasDeLaStore -ErrorAction SilentlyContinue) {
    Assert-Verdadero 'E-22 el alias de la Store se reconoce' (Test-EsAliasDeLaStore 'C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe')
    Assert-Verdadero 'E-22 un Python real no' (-not (Test-EsAliasDeLaStore 'C:\Users\x\AppData\Local\Programs\Python\Python312\python.exe'))
    Assert-Verdadero 'E-22 una ruta vacia no' (-not (Test-EsAliasDeLaStore ''))
}
Assert-Verdadero 'E-22 -Doctor mira el python del PATH' ($texto66.Contains('Test-EsAliasDeLaStore ([string]$enElPath.Source)'))

# E-39, E-44 y E-45 - -Doctor calcula la barra en vivo con bienvenida.py barra, el mismo resolvedor
# que `harness`, y sin Python vuelve al estado guardado sin inventar ACTIVE. La semantica de lo que
# calcula bienvenida.py barra esta en 66_integrity_cleanup.py; aca, lo que -Doctor hace con eso.
foreach ($nombre in @('Read-TextoUtf8', 'Get-EstadoDeLaBarra', 'Test-FormaDeLaBarra', 'Get-BarraEnVivo', 'Get-BarraDelDoctor', 'Resolve-Python')) {
    $f = $funciones66 | Where-Object { $_.Name -eq $nombre } | Select-Object -First 1
    Assert-Verdadero "E-45 install.ps1 define $nombre" ($null -ne $f)
    if ($f) { Invoke-Expression $f.Extent.Text }
}

$proy66 = Join-Path ([System.IO.Path]::GetTempPath()) ('w6-doctor-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$lib66 = Join-Path $proy66 '.claude\harness\hooks\lib'
New-Item -ItemType Directory -Force $lib66 | Out-Null
[System.IO.File]::WriteAllText((Join-Path $proy66 '.claude\harness.installation.json'),
    '{"runtimeComponents": {"contextBar": {"state": "CONFIGURED", "activeInCurrentSession": false}}}')
$py66 = $null
if (Get-Command Resolve-Python -ErrorAction SilentlyContinue) { $py66 = Resolve-Python }
try {
    if (Get-Command Get-BarraDelDoctor -ErrorAction SilentlyContinue) {
        # E-44 - sin Python: el estado guardado, tal cual. Nunca un ACTIVE que no esta escrito.
        $r = Get-BarraDelDoctor -Project $proy66 -Python $null
        Assert-Igual 'E-44 sin Python: el estado guardado' 'CONFIGURED' $r.Estado
        Assert-Igual 'E-44 sin Python: dice de donde sale' 'guardado' $r.Fuente
        Assert-Igual 'E-44 sin Python: sin sesion con datos' '' $r.ConDatos

        # E-44 - con Python y un bienvenida.py que se cae: el estado guardado, sin traceback.
        [System.IO.File]::WriteAllText((Join-Path $lib66 'bienvenida.py'), "raise RuntimeError('roto')`n")
        $r = Get-BarraDelDoctor -Project $proy66 -Python $py66
        Assert-Igual 'E-44 bienvenida.py roto: el estado guardado' 'CONFIGURED' $r.Estado
        Assert-Igual 'E-44 bienvenida.py roto: dice de donde sale' 'guardado' $r.Fuente

        # E-44 - una salida que no es la barra tampoco es ACTIVE.
        [System.IO.File]::WriteAllText((Join-Path $lib66 'bienvenida.py'), "print('ACTIVE')`n")
        $r = Get-BarraDelDoctor -Project $proy66 -Python $py66
        Assert-Igual 'E-44 salida que no es JSON: el estado guardado' 'CONFIGURED' $r.Estado

        # E-45 - con Python, lo que calcula bienvenida.py barra manda sobre lo guardado.
        # La salida tiene la forma de runtimeComponents.contextBar, como la escribe bienvenida.py.
        [System.IO.File]::WriteAllText((Join-Path $lib66 'bienvenida.py'),
            "import json, sys`nassert sys.argv[1:] == ['barra', sys.argv[2]]`nprint(json.dumps({'state': 'ACTIVE', 'installed': True, 'configured': True, 'reloadRequired': False, 'activeInCurrentSession': False, 'lastSessionWithData': 's-w6-uno', 'lastSessionId': 's-w6-dos'}))`n")
        $r = Get-BarraDelDoctor -Project $proy66 -Python $py66
        Assert-Igual 'E-45 en vivo: ACTIVE' 'ACTIVE' $r.Estado
        Assert-Igual 'E-45 en vivo: dice de donde sale' 'vivo' $r.Fuente
        Assert-Igual 'E-45 en vivo: la ultima sesion con datos' 's-w6-uno' $r.ConDatos
    }

    # E-44 (pasada 15 del refutador) - un JSON que no es la barra tampoco reemplaza lo guardado.
    # install.ps1 corre con Set-StrictMode 2.0: leer una propiedad que no esta tira, y antes eso
    # subia hasta el catch del script y cortaba -Doctor. Por eso se corre con el mismo StrictMode.
    if ($py66 -and (Get-Command Get-BarraDelDoctor -ErrorAction SilentlyContinue)) {
        function Invoke-DoctorEstricto66 {
            param([string] $Json, [int] $Codigo = 0)
            [System.IO.File]::WriteAllText((Join-Path $lib66 'bienvenida.py'),
                "import sys`nsys.stdout.write(r'''$Json''' + '\n')`nsys.exit($Codigo)`n")
            try {
                return & { Set-StrictMode -Version 2.0; Get-BarraDelDoctor -Project $proy66 -Python $py66 }
            } catch {
                return [pscustomobject]@{ Estado = 'EXCEPCION'; ConDatos = ''; Fuente = $_.Exception.Message }
            }
        }
        $forma66 = '"installed": true, "configured": true, "reloadRequired": false, "activeInCurrentSession": false'
        $malas66 = [ordered]@{
            'A un objeto vacio'                         = '{}'
            'B un JSON string'                          = '"ACTIVE"'
            'C un array vacio'                          = '[]'
            'C un array con una barra adentro'          = "[{`"state`": `"ACTIVE`", $forma66, `"lastSessionWithData`": `"s-w6-uno`"}]"
            'D ACTIVE sin nada mas'                     = '{"state": "ACTIVE"}'
            'D ACTIVE sin los campos requeridos'        = '{"state": "ACTIVE", "lastSessionWithData": "s-w6-uno"}'
            'E sin state'                               = "{$forma66, `"lastSessionWithData`": null}"
            'F state que no es texto'                   = "{`"state`": 123, $forma66, `"lastSessionWithData`": null}"
            'G state desconocido'                       = "{`"state`": `"WHATEVER`", $forma66, `"lastSessionWithData`": null}"
            'H lastSessionWithData numero'              = "{`"state`": `"ACTIVE`", $forma66, `"lastSessionWithData`": 123}"
            'H lastSessionWithData objeto'              = "{`"state`": `"ACTIVE`", $forma66, `"lastSessionWithData`": {`"sessionId`": `"s-w6-uno`"}}"
            'H ACTIVE sin lastSessionWithData'          = "{`"state`": `"ACTIVE`", $forma66}"
            'L JSON cortado'                            = '{"state": "ACTIVE",'
        }
        foreach ($caso66 in $malas66.Keys) {
            $r = Invoke-DoctorEstricto66 $malas66[$caso66]
            Assert-Igual "E-44 $caso66 : el estado guardado, sin excepcion" 'CONFIGURED|guardado' "$($r.Estado)|$($r.Fuente)"
        }
        $r = Invoke-DoctorEstricto66 "{`"state`": `"ACTIVE`", $forma66, `"lastSessionWithData`": `"s-w6-uno`"}" 1
        Assert-Igual 'E-44 K ACTIVE con salida distinta de 0: el estado guardado' 'CONFIGURED|guardado' "$($r.Estado)|$($r.Fuente)"

        # Los controles: una barra con su forma manda, con StrictMode.
        $r = Invoke-DoctorEstricto66 "{`"state`": `"CONFIGURED`", $forma66, `"lastSessionWithData`": null}"
        Assert-Igual 'E-44 I CONFIGURED en vivo: se usa' 'CONFIGURED|vivo|' "$($r.Estado)|$($r.Fuente)|$($r.ConDatos)"
        $r = Invoke-DoctorEstricto66 "{`"state`": `"ACTIVE`", $forma66, `"lastSessionWithData`": `"s-w6-uno`", `"lastSessionId`": `"s-w6-dos`"}"
        Assert-Igual 'E-44 J ACTIVE en vivo con la evidencia: se usa' 'ACTIVE|vivo|s-w6-uno' "$($r.Estado)|$($r.Fuente)|$($r.ConDatos)"

        # Y la barra de verdad, la que calcula bienvenida.py del repositorio, tiene esa forma.
        $vacio66 = Join-Path ([System.IO.Path]::GetTempPath()) ('w6-vacio-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
        New-Item -ItemType Directory -Force $vacio66 | Out-Null
        try {
            $real66 = (& $py66 (Join-Path $script:Raiz 'comun\hooks\lib\bienvenida.py') barra $vacio66 2>$null | Out-String).Trim()
            $formaReal66 = $false
            if (Get-Command Test-FormaDeLaBarra -ErrorAction SilentlyContinue) {
                $formaReal66 = & { Set-StrictMode -Version 2.0; Test-FormaDeLaBarra ($real66 | ConvertFrom-Json) }
            }
            Assert-Verdadero 'E-44 la barra que calcula bienvenida.py tiene la forma que -Doctor acepta' $formaReal66 $real66
        } finally {
            Remove-Item -LiteralPath $vacio66 -Recurse -Force -ErrorAction SilentlyContinue
        }

        # -Doctor entero, con el {} que cortaba el diagnostico: vuelve a lo guardado y sigue.
        [System.IO.File]::WriteAllText((Join-Path $proy66 '.claude\harness.lock.json'),
            '{"version": "0.26.0", "harness": ["comun", "desarrollo"], "instalado": "2026-10-01 10:00:00", "archivos": []}')
        [System.IO.File]::WriteAllText((Join-Path $lib66 'bienvenida.py'), "print('{}')`n")
        $doctor66 = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $instalador66 -Doctor -Project $proy66 2>&1 | Out-String
        Assert-Verdadero 'E-44 A -Doctor no se corta en la Context Bar' (-not ($doctor66 -match "'state'")) $doctor66
        Assert-Contiene 'E-44 A -Doctor informa el estado guardado' 'Context Bar: CONFIGURADA' $doctor66
        Assert-Contiene 'E-44 A -Doctor sigue con lo que viene despues' 'control de versiones' $doctor66
    }
} finally {
    Remove-Item -LiteralPath $proy66 -Recurse -Force -ErrorAction SilentlyContinue
}
Assert-Verdadero 'E-45 -Doctor decide con Get-BarraDelDoctor' ($texto66.Contains('Get-BarraDelDoctor -Project $Project -Python'))
Assert-Verdadero 'E-45 -Doctor nombra la ultima sesion con datos' ($texto66.Contains('$barraDoctor.ConDatos'))
