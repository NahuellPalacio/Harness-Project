# Los checks del harness desarrollo.
#
# La mitad que importa de cada uno es la NEGATIVA: que se calle cuando no le toca. Un
# check de nomenclatura con falsos positivos se desactiva la primera semana, y entonces
# tampoco atrapa los verdaderos. Por eso hay tantos casos de "no dice nada" como de
# "encuentra el problema".

Set-Grupo 'Desarrollo — checks'

$dirChecks = Join-Path $script:Raiz 'harnesses\desarrollo\checks'
$u8 = New-Object System.Text.UTF8Encoding $false

# Los checks usan Get-HookField, que vive en Hook.psm1.
Import-Module (Join-Path $script:Raiz 'comun\hooks\lib\Hook.psm1') -Force

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-dev-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $temp -Force | Out-Null

function Invoke-Check {
    param([string] $Check, [string] $Nombre, [string] $Contenido, $Config = $null)

    $ruta = Join-Path $temp $Nombre
    $dir = Split-Path $ruta -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($ruta, $Contenido, (New-Object System.Text.UTF8Encoding $false))

    $evento = [pscustomobject]@{
        hook_event_name = 'PostToolUse'
        tool_name       = 'Write'
        tool_input      = [pscustomobject]@{ file_path = $ruta }
    }
    $salida = & (Join-Path $dirChecks $Check) -Evento $evento -Proyecto $temp -Config $Config
    # Con la coma adelante. Un arreglo de un elemento devuelto desde una funcion se
    # desenvuelve al elemento, y entonces $r[0] sobre un string devuelve su primer
    # CARACTER: el test compara '[' contra lo que espera y falla sin decir por que.
    return ,@($salida | Where-Object { $_ })
}

try {

# ── dev-dependencias ────────────────────────────────────────────────────────────

$conRangos = '{ "dependencies": { "express": "^4.18.0", "lodash": "~4.17.21", "axios": "1.6.2" } }'
$r = Invoke-Check -Check 'dev-dependencias.ps1' -Nombre 'package.json' -Contenido $conRangos
Assert-Igual 'un package.json con rangos produce un aviso' 1 $r.Count
Assert-Verdadero 'nombra las dos dependencias con rango' `
    ($r[0] -match 'express' -and $r[0] -match 'lodash')
Assert-Verdadero 'no nombra la que si esta fijada' (-not ($r[0] -match 'axios'))
Assert-Verdadero 'cita el estandar' ($r[0] -match 'ES0901')

$exactas = '{ "dependencies": { "express": "4.18.0", "lodash": "4.17.21" } }'
Assert-Igual 'todas exactas: silencio' 0 `
    (Invoke-Check -Check 'dev-dependencias.ps1' -Nombre 'package.json' -Contenido $exactas).Count

# composer usa las mismas formas de rango
$composer = '{ "require": { "laravel/framework": "^10.0", "guzzlehttp/guzzle": "7.8.1" } }'
$rc = Invoke-Check -Check 'dev-dependencias.ps1' -Nombre 'composer.json' -Contenido $composer
Assert-Igual 'composer.json tambien se revisa' 1 $rc.Count

# La mitad negativa
Assert-Igual 'un json cualquiera no le incumbe' 0 `
    (Invoke-Check -Check 'dev-dependencias.ps1' -Nombre 'datos.json' -Contenido $conRangos).Count
Assert-Igual 'lo que esta en node_modules no se toca' 0 `
    (Invoke-Check -Check 'dev-dependencias.ps1' -Nombre 'node_modules\algo\package.json' -Contenido $conRangos).Count
Assert-Igual 'un package.json roto no explota, se saltea' 0 `
    (Invoke-Check -Check 'dev-dependencias.ps1' -Nombre 'package.json' -Contenido '{ esto no es json').Count


# ── dev-api-rutas ───────────────────────────────────────────────────────────────

$mal = @'
const rutas = {
  crear:  "/api/crearUsuario",
  ver:    "/api/usuario/{id}",
  listar: "/api/v1/usuarios"
};
'@
$ra = Invoke-Check -Check 'dev-api-rutas.ps1' -Nombre 'rutas.ts' -Contenido $mal
Assert-Verdadero 'detecta la ruta sin version' (($ra -join ' ') -match 'sin version')
Assert-Verdadero 'detecta el verbo en la ruta' (($ra -join ' ') -match 'metodo HTTP')
Assert-Verdadero 'detecta la coleccion en singular' (($ra -join ' ') -match 'singular')
Assert-Verdadero 'no reporta la ruta que esta bien' (-not (($ra -join ' ') -match '/api/v1/usuarios \(') )

$bien = 'const r = { listar: "/api/v1/usuarios", ver: "/api/v1/usuarios/{id}" };'
Assert-Igual 'rutas correctas: silencio' 0 `
    (Invoke-Check -Check 'dev-api-rutas.ps1' -Nombre 'rutas.ts' -Contenido $bien).Count

# El falso positivo que este check tiene que evitar si o si: una palabra que EMPIEZA
# como un verbo pero no lo es. "postulaciones" arranca con "post".
$postulaciones = 'const r = { listar: "/api/v1/postulaciones", ver: "/api/v1/postulaciones/{id}" };'
Assert-Igual 'postulaciones no se confunde con el verbo post' 0 `
    (Invoke-Check -Check 'dev-api-rutas.ps1' -Nombre 'rutas.ts' -Contenido $postulaciones).Count

# Una ruta que no es de API no le incumbe: si no, opinaria sobre todo el front.
$front = 'const r = { inicio: "/inicio/panel", detalle: "/noticia/{id}" };'
Assert-Igual 'las rutas que no son de API no se tocan' 0 `
    (Invoke-Check -Check 'dev-api-rutas.ps1' -Nombre 'rutas.ts' -Contenido $front).Count

Assert-Igual 'un archivo sin rutas de API: silencio' 0 `
    (Invoke-Check -Check 'dev-api-rutas.ps1' -Nombre 'util.ts' -Contenido 'export const sumar = (a, b) => a + b;').Count

# El prefijo sale de la configuracion del proyecto, no esta clavado
$otroPrefijo = 'const r = { x: "/servicios/crearUsuario" };'
$cfg = [pscustomobject]@{ prefijoApi = 'servicios' }
Assert-Verdadero 'respeta el prefijo de API que declara el proyecto' `
    ((Invoke-Check -Check 'dev-api-rutas.ps1' -Nombre 'rutas.ts' -Contenido $otroPrefijo -Config $cfg).Count -gt 0)


# ── dev-infra-en-codigo ─────────────────────────────────────────────────────────

$conIp = 'const cfg = { url: "http://10.51.2.30/api", puerto: 8080 };'
$ri = Invoke-Check -Check 'dev-infra-en-codigo.ps1' -Nombre 'config.ts' -Contenido $conIp
Assert-Igual 'una IP en posicion de host produce un aviso' 1 $ri.Count
Assert-Verdadero 'nombra la IP y su linea' ($ri[0] -match '10\.51\.2\.30')

Assert-Igual 'localhost no se reporta' 0 `
    (Invoke-Check -Check 'dev-infra-en-codigo.ps1' -Nombre 'config.ts' -Contenido 'const u = "http://127.0.0.1:3000";').Count
Assert-Igual 'un nombre DNS es justamente lo correcto' 0 `
    (Invoke-Check -Check 'dev-infra-en-codigo.ps1' -Nombre 'config.ts' -Contenido 'const u = "https://siccsir.buenosaires.gob.ar/api";').Count

# El falso positivo clasico: cuatro numeros con puntos que son una version.
Assert-Igual 'una version no se confunde con una IP' 0 `
    (Invoke-Check -Check 'dev-infra-en-codigo.ps1' -Nombre 'config.ts' -Contenido 'const version = "10.51.2.300";').Count
Assert-Igual 'un numero suelto con puntos tampoco' 0 `
    (Invoke-Check -Check 'dev-infra-en-codigo.ps1' -Nombre 'notas.ts' -Contenido 'const build = "8.4.1.2";').Count


# ── dev-accesibilidad-html ──────────────────────────────────────────────────────

$htmlMal = @'
<html>
<body>
  <h1>Uno</h1>
  <h1>Dos</h1>
  <img src="logo.png">
  <input type="text">
</body>
</html>
'@
$rh = Invoke-Check -Check 'dev-accesibilidad-html.ps1' -Nombre 'pagina.html' -Contenido $htmlMal
$todo = $rh -join ' '
Assert-Verdadero 'detecta html sin lang'          ($todo -match 'sin atributo lang')
Assert-Verdadero 'detecta img sin alt'            ($todo -match 'sin atributo alt')
Assert-Verdadero 'detecta el control sin nombre'  ($todo -match 'sin forma de nombrarlos')
Assert-Verdadero 'detecta los dos h1'             ($todo -match '2 elementos <h1>')

$htmlBien = @'
<html lang="es">
<body>
  <h1>Titulo</h1>
  <img src="logo.png" alt="Escudo del GCBA">
  <label for="nombre">Nombre</label>
  <input type="text" id="nombre">
</body>
</html>
'@
Assert-Igual 'un html correcto: silencio' 0 `
    (Invoke-Check -Check 'dev-accesibilidad-html.ps1' -Nombre 'pagina.html' -Contenido $htmlBien).Count

# alt vacio es una afirmacion -"esta imagen es decorativa"- y es correcta.
$decorativa = '<html lang="es"><h1>x</h1><img src="linea.png" alt=""></html>'
Assert-Igual 'alt vacio es correcto y no se reporta' 0 `
    (Invoke-Check -Check 'dev-accesibilidad-html.ps1' -Nombre 'pagina.html' -Contenido $decorativa).Count

# Un parcial no tiene <html> ni tiene por que tener h1.
$parcial = '<div class="tarjeta"><p>Un fragmento</p></div>'
Assert-Igual 'un parcial sin h1 no se reporta' 0 `
    (Invoke-Check -Check 'dev-accesibilidad-html.ps1' -Nombre 'tarjeta.component.html' -Contenido $parcial).Count

# Los campos ocultos y los botones no llevan etiqueta.
$ocultos = '<html lang="es"><h1>x</h1><input type="hidden" name="token"><input type="submit" value="Enviar"></html>'
Assert-Igual 'hidden y submit no piden etiqueta' 0 `
    (Invoke-Check -Check 'dev-accesibilidad-html.ps1' -Nombre 'pagina.html' -Contenido $ocultos).Count

Assert-Igual 'un .ts no le incumbe al check de html' 0 `
    (Invoke-Check -Check 'dev-accesibilidad-html.ps1' -Nombre 'algo.ts' -Contenido $htmlMal).Count

}
finally {
    Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
}
