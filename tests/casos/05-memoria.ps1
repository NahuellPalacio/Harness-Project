# La capa de memoria: zonas del CLAUDE.md, sus techos, y lo que SessionStart recuerda.
#
# Lo que se verifica de fondo es la promesa que separa a este harness de una memoria que
# graba todo: SessionStart solo lee lo que alguien decidio dejar anotado. Nunca captura.
# Por eso no puede filtrar un token que el agente leyo hace un rato.

Set-Grupo 'Memoria — zonas del CLAUDE.md'

Import-Module (Join-Path $script:Raiz 'comun\hooks\lib\Zonas.psm1') -Force

$config = [pscustomobject]@{
    techoZonaFija   = 60
    techoZonaMapa   = 20
    techoZonaIndice = 25
    techoZonaCache  = 5      # bajo a proposito, para probar el exceso
}

$plantilla = [System.IO.File]::ReadAllText(
    (Join-Path $script:Raiz 'comun\claude-md\plantilla-proyecto.md'),
    (New-Object System.Text.UTF8Encoding $false))


# ── La plantilla trae las cuatro zonas ──────────────────────────────────────────

$m = Measure-Zonas -Texto $plantilla -Config $config
Assert-Igual 'la plantilla define cuatro zonas' 4 $m.Count
Assert-Verdadero 'las cuatro estan presentes en la plantilla' `
    (@($m | Where-Object { -not $_.Existe }).Count -eq 0)
Assert-Verdadero 'ninguna zona de la plantilla nace excedida' `
    (@($m | Where-Object { $_.Excedida }).Count -eq 0)


# ── Se reconoce el nombre con tilde y sin tilde ─────────────────────────────────
# La plantilla escribe ZONA ÍNDICE y ZONA CACHÉ con tilde; el codigo las nombra sin.

$indice = $m | Where-Object { $_.Nombre -eq 'ZONA INDICE' }
$cache  = $m | Where-Object { $_.Nombre -eq 'ZONA CACHE' }
Assert-Verdadero 'encuentra ZONA INDICE aunque este escrita con tilde' $indice.Existe
Assert-Verdadero 'encuentra ZONA CACHE aunque este escrita con tilde'  $cache.Existe


# ── Un archivo sin zonas ────────────────────────────────────────────────────────

$m2 = Measure-Zonas -Texto "# CLAUDE.md`r`n`r`nUn archivo cualquiera sin zonas." -Config $config
Assert-Verdadero 'un archivo sin zonas no reporta ninguna como presente' `
    (@($m2 | Where-Object { $_.Existe }).Count -eq 0)


# ── Se mide el exceso ───────────────────────────────────────────────────────────

$excedido = @'
<!-- ZONA CACHE — purgable -->
- linea uno
- linea dos
- linea tres
- linea cuatro
- linea cinco
- linea seis
- linea siete
<!-- /ZONA CACHE -->
'@
$m3 = Measure-Zonas -Texto $excedido -Config $config
$c3 = $m3 | Where-Object { $_.Nombre -eq 'ZONA CACHE' }
Assert-Igual 'cuenta solo las lineas con contenido' 7 $c3.Lineas
Assert-Verdadero 'detecta que paso su techo' $c3.Excedida

# Las lineas en blanco son formato, no informacion. Castigarlas empujaria a escribir
# CLAUDE.md ilegibles solo para pasar la medicion.
$conBlancos = "<!-- ZONA CACHE -->`r`n`r`n- una`r`n`r`n`r`n- dos`r`n`r`n<!-- /ZONA CACHE -->"
$m4 = Measure-Zonas -Texto $conBlancos -Config $config
$c4 = $m4 | Where-Object { $_.Nombre -eq 'ZONA CACHE' }
Assert-Igual 'las lineas en blanco no cuentan' 2 $c4.Lineas


# ── Zonas que el harness no reconoce ────────────────────────────────────────────
#
# El caso real: el CLAUDE.md del IGE traia las zonas del prototipo con otro nombre
# -'INDICE' y 'CACHE' sin el prefijo 'ZONA'- el instalador no las reconocio y agrego
# las canonicas al lado. Quedaron dos indices y dos caches, uno con el contenido y
# otro vacio, y el check medía el vacio. Fallo en silencio, que es lo unico que este
# harness no se permite.

Set-Grupo 'Memoria — zonas no reconocidas'

$conViejas = @'
# CLAUDE.md - proyecto

<!-- ZONA FIJA - reglas -->
- una regla
<!-- /ZONA FIJA -->

<!-- ÍNDICE - un puntero por nota del vault -->
- Dominio -> nota de dominio
<!-- /ÍNDICE -->

<!-- CACHÉ - zona purgable -->
- algo aprendido
<!-- /CACHÉ -->
'@

$raras = Find-ZonasNoReconocidas -Texto $conViejas
Assert-Igual 'encuentra los dos marcadores con nombre viejo' 2 $raras.Count
Assert-Verdadero 'no confunde ZONA FIJA, que si es canonica' `
    (@($raras | Where-Object { $_.Marcador -eq 'ZONA FIJA' }).Count -eq 0)

$indice = $raras | Where-Object { $_.Marcador -eq 'ÍNDICE' }
Assert-Igual 'sugiere la zona canonica a la que se parece' 'ZONA INDICE' $indice.Parecida
$cache = $raras | Where-Object { $_.Marcador -eq 'CACHÉ' }
Assert-Igual 'reconoce la equivalencia aunque cambie la tilde' 'ZONA CACHE' $cache.Parecida

# Un CLAUDE.md ya canonico no tiene nada raro. Es la mitad que importa: un aviso que
# salta siempre es un aviso que se ignora siempre.
Assert-Igual 'la plantilla canonica no dispara ningun aviso' 0 `
    (Find-ZonasNoReconocidas -Texto $plantilla).Count

# El bloque que genera el instalador tambien es un par apertura/cierre, y no es una zona.
$conBloqueComun = "<!-- HARNESS:COMUN - generado -->`r`ntexto`r`n<!-- /HARNESS:COMUN -->"
Assert-Igual 'el bloque HARNESS:COMUN no se reporta como zona rara' 0 `
    (Find-ZonasNoReconocidas -Texto $conBloqueComun).Count

# Un comentario suelto no es una zona: sin cierre no hay bloque que duplicar.
$comentarioSuelto = "# CLAUDE.md`r`n`r`n<!-- ojo con esto -->`r`n`r`ntexto"
Assert-Igual 'un comentario sin cierre no se confunde con una zona' 0 `
    (Find-ZonasNoReconocidas -Texto $comentarioSuelto).Count

# El contrato de devolucion, fijado a proposito. `return ,$coleccion` la emite como UN
# objeto: eso es lo que evita que un resultado vacio se desenvuelva a $null, pero
# tambien significa que envolverla en @() da un arreglo de un elemento que es la
# coleccion entera. Se asigna derecho, se recorre con foreach o con la tuberia.
# Es la cuarta vez que esta familia de bugs muerde este repositorio; queda fijada.
$vacio = Find-ZonasNoReconocidas -Texto "# nada"
Assert-Igual 'un resultado vacio tiene Count 0, no es $null' 0 $vacio.Count
$recorridas = 0
foreach ($r in $vacio) { $recorridas++ }
Assert-Igual 'un resultado vacio no entra al foreach' 0 $recorridas
foreach ($r in (Find-ZonasNoReconocidas -Texto $conViejas)) { $recorridas++ }
Assert-Igual 'un resultado con items se recorre elemento por elemento' 2 $recorridas


# ── Lo que queda fuera de toda zona ─────────────────────────────────────────────
#
# Measure-Zonas mide lo que esta ADENTRO. Lo de afuera no lo mide nadie: no se purga,
# no se baja al conocimiento del proyecto y no cuenta contra ningun techo. Un
# CLAUDE.md de trescientas lineas sin un solo marcador pasa la medicion entera.

Set-Grupo 'Memoria — contenido fuera de zonas'

$f1 = Measure-FueraDeZonas -Texto $conBlancos
Assert-Igual 'un archivo que es todo zona no tiene nada afuera' 0 $f1.Lineas

$conAfuera = @'
# CLAUDE.md - proyecto

Una linea de presentacion.

<!-- ZONA FIJA - reglas -->
- una regla
- otra regla
<!-- /ZONA FIJA -->

Esto quedo suelto abajo.
'@
$f2 = Measure-FueraDeZonas -Texto $conAfuera
Assert-Igual 'cuenta el titulo y las dos lineas sueltas' 3 $f2.Lineas
Assert-Verdadero 'devuelve una muestra para poder nombrarlas' ($f2.Muestra.Count -gt 0)

# El caso que motiva el check: un CLAUDE.md sin ningun marcador.
$sinMarcadores = "# CLAUDE.md`r`n`r`nLinea una.`r`nLinea dos.`r`nLinea tres."
$f3 = Measure-FueraDeZonas -Texto $sinMarcadores
Assert-Igual 'un archivo sin zonas esta entero afuera' 4 $f3.Lineas

# Un marcador de varias lineas no se cuenta como contenido. Ya paso: la CACHE del
# prototipo tenia el comentario partido en tres.
$marcadorLargo = "<!-- ZONA CACHE - purgable.`r`n     Sigue en otra linea.`r`n     Y termina aca. -->`r`n- una`r`n<!-- /ZONA CACHE -->"
$f4 = Measure-FueraDeZonas -Texto $marcadorLargo
Assert-Igual 'un marcador partido en varias lineas no cuenta como contenido' 0 $f4.Lineas

$f5 = Measure-FueraDeZonas -Texto $plantilla
Assert-Verdadero 'la plantilla deja poco afuera' ($f5.Lineas -le 12)


# ── Punta a punta: instalar y ver que recuerda ──────────────────────────────────

Set-Grupo 'Memoria — SessionStart recuerda'

$instalador = Join-Path $script:Raiz 'install.ps1'
$demo = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-mem-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))

try {
    New-Item -ItemType Directory -Path $demo -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $demo 'CLAUDE.md'), "# CLAUDE.md - demo`r`n")

    $salida = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                  -File $instalador -Project $demo -Harness 'analisis' -Usuario 'Ana Prueba' 2>&1 | Out-String

    Assert-Contiene 'el instalador crea las zonas que faltan' 'zonas agregadas' $salida

    $claudeMd = Join-Path $demo 'CLAUDE.md'
    $texto = [System.IO.File]::ReadAllText($claudeMd, (New-Object System.Text.UTF8Encoding $false))
    $conf  = [System.IO.File]::ReadAllText((Join-Path $demo '.claude\harness.config.json')) | ConvertFrom-Json

    $medido = Measure-Zonas -Texto $texto -Config $conf
    Assert-Verdadero 'el CLAUDE.md instalado tiene las cuatro zonas' `
        (@($medido | Where-Object { $_.Existe }).Count -eq 4)

    Assert-Verdadero 'y ninguna nace excedida' `
        (@($medido | Where-Object { $_.Excedida }).Count -eq 0)

    # Alguien deja una nota en la cache, como al cerrar una sesion.
    $texto = $texto.Replace('_(vacía)_', '- falta validar ES0903 contra un proyecto con codigo')
    [System.IO.File]::WriteAllText($claudeMd, $texto, (New-Object System.Text.UTF8Encoding $false))

    $payload = ConvertTo-Json -Depth 10 -InputObject @{
        session_id      = 'test-memoria'
        cwd             = $demo
        hook_event_name = 'SessionStart'
        source          = 'startup'
    }
    $r = Invoke-HookEnProceso -Script (Join-Path $demo '.claude\harness\hooks\session-start.ps1') `
                              -JsonEntrada $payload

    Assert-Igual 'SessionStart sale con codigo 0' 0 $r.Codigo
    Assert-Contiene 'saluda por el nombre de quien lo usa'    'Ana Prueba'   $r.Salida
    Assert-Contiene 'dice que harness rige y en que version'  'analisis'     $r.Salida
    Assert-Contiene 'devuelve lo que quedo anotado en la cache' 'ES0903'     $r.Salida
    Assert-Contiene 'avisa que el proyecto no esta versionado' 'no esta versionado' $r.Salida

    # Lo que NO tiene que hacer: inventar contexto que nadie escribio.
    $demo2 = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-mem2-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
    try {
        New-Item -ItemType Directory -Path $demo2 -Force | Out-Null
        $payload2 = ConvertTo-Json -Depth 10 -InputObject @{
            session_id      = 'test-memoria-2'
            cwd             = $demo2
            hook_event_name = 'SessionStart'
            source          = 'startup'
        }
        $r2 = Invoke-HookEnProceso -Script (Join-Path $demo '.claude\harness\hooks\session-start.ps1') `
                                   -JsonEntrada $payload2
        Assert-Igual 'en un proyecto sin harness sale con codigo 0' 0 $r2.Codigo
        Assert-Verdadero 'y no menciona a nadie que no este configurado ahi' `
            ($r2.Salida -notmatch 'Ana Prueba') `
            'SessionStart solo puede leer lo que hay en ESE proyecto'
    }
    finally { Remove-Item $demo2 -Recurse -Force -ErrorAction SilentlyContinue }
}
finally {
    if (Test-Path $demo) { Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue }
}
