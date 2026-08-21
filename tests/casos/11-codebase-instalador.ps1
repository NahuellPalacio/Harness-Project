# E-18, E-19 y E-21 de docs/cambios/iniciador-code/spec.md.
#
# Va aparte de 03-instalador.ps1 a proposito. Ese caso instala 'analisis' -y estos tres
# escenarios son de 'desarrollo'- y ademas rompe archivos versionados para probar el
# -Update, con un finally que no sobrevive a que maten el proceso. Sumarle carga agranda
# esa superficie sin ninguna necesidad: aca no se rompe nada del repo.
#
# Sin acentos a proposito: un .ps1 con caracteres no ASCII necesita BOM, y el propio
# 00-encoding-fuentes.ps1 declara que no ponerlos es la otra mitad de esa regla.

Set-Grupo 'Instalador - el indice del codigo'

$instalador = Join-Path $script:Raiz 'install.ps1'
$demo = Join-Path ([System.IO.Path]::GetTempPath()) `
                  ('harness-cb-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
$usuarioPrueba = 'Ana Prueba'
$rutaAgente = Join-Path $demo '.claude\agents\dev-iniciador-code.md'
$rutaIndice = Join-Path $demo 'docs\codebase\indice.md'

function Invoke-InstaladorCb {
    param([string[]] $Argumentos)
    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                               -File $instalador @Argumentos 2>&1 | Out-String
    return [pscustomobject]@{ Salida = $salida; Codigo = $LASTEXITCODE }
}

try {
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'), "# Proyecto de prueba`r`n")
    [System.IO.File]::WriteAllText((Join-Path $demo '.gitignore'), "node_modules/`r`n")

    # -- Instalar desarrollo --------------------------------------------------------
    $r = Invoke-InstaladorCb @('-Project', $demo, '-Harness', 'desarrollo',
                               '-Usuario', $usuarioPrueba)
    Assert-Igual 'instalar desarrollo sale con codigo 0' 0 $r.Codigo

    # E-18: el agente aterriza donde Claude Code lo busca, sin subdirectorio por harness.
    Assert-Verdadero 'E-18 dev-iniciador-code.md queda en .claude\agents' `
        (Test-Path $rutaAgente) 'el agente no se instalo'

    # E-19: la clave llega desde el manifiesto de desarrollo. Solo pasa en una config
    # recien creada: harness.config.json no se reescribe nunca, y por eso el default
    # tambien vive en el hook y en el agente -eso lo cubre E-20, del lado de Python-.
    $rutaConfig = Join-Path $demo '.claude\harness.config.json'
    Assert-Verdadero 'E-19 existe harness.config.json' (Test-Path $rutaConfig)
    $config = [System.IO.File]::ReadAllText($rutaConfig) | ConvertFrom-Json
    Assert-Igual 'E-19 trae rutaCodebase' 'docs/codebase' $config.rutaCodebase

    # -- Un indice, como si el agente ya hubiera corrido ----------------------------
    New-Item -ItemType Directory -Path (Split-Path $rutaIndice) -Force | Out-Null
    $contenidoIndice = "# Indice del codigo`r`n`r`n- ``comun/hooks`` - los cuatro hooks`r`n"
    [System.IO.File]::WriteAllText($rutaIndice, $contenidoIndice)

    # -- -Uninstall no se lleva puesto el trabajo del proyecto ----------------------
    $r = Invoke-InstaladorCb @('-Project', $demo, '-Uninstall')
    Assert-Igual '-Uninstall sale con codigo 0' 0 $r.Codigo

    # E-21: docs/codebase/ es conocimiento del proyecto, no material del harness. El
    # inventario del lockfile no lo lista, asi que -Uninstall no tiene por que tocarlo;
    # esto es lo que lo deja escrito, para que un cambio futuro no lo barra de paso.
    Assert-Verdadero 'E-21 el indice sigue ahi despues de desinstalar' `
        (Test-Path $rutaIndice) '-Uninstall se llevo el indice del proyecto'
    Assert-Igual 'E-21 y sigue byte por byte igual' `
        $contenidoIndice ([System.IO.File]::ReadAllText($rutaIndice))

    # La contraparte: lo que si es del harness se va. Sin esto, el escenario de arriba
    # pasaria igual con un -Uninstall que no borra nada.
    Assert-Verdadero 'E-21 el agente si se lo lleva' `
        (-not (Test-Path $rutaAgente)) 'el agente sobrevivio a -Uninstall'
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}
