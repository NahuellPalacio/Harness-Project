# La unica regla del harness que impide algo.
#
# Los casos negativos —lo que NO tiene que bloquear— son tan importantes como los
# positivos, o mas. Un harness que traba trabajo legitimo se desinstala esa misma semana,
# y ahi se pierde tambien la proteccion que si servia.
#
# Los valores de prueba se arman por partes a proposito, para que el repositorio no
# contenga cadenas con forma de credencial real.

Set-Grupo 'Secretos — deteccion'

Import-Module (Join-Path $script:Raiz 'comun\hooks\lib\Hook.psm1')     -Force
Import-Module (Join-Path $script:Raiz 'comun\hooks\lib\Secretos.psm1') -Force

$catalogo = Import-PatronesSecretos -Ruta (Join-Path $script:Raiz 'comun\reglas\secretos.patrones.json')


function Assert-Detecta {
    param([string] $Nombre, [string] $Texto, [string] $ConfianzaEsperada)
    $h = Find-Secreto -Texto $Texto -Catalogo $catalogo
    if ($null -eq $h) {
        Add-Resultado -Nombre $Nombre -Ok $false -Detalle 'no detecto nada'
        return
    }
    $ok = ($h.Confianza -eq $ConfianzaEsperada)
    $detalle = ''
    if (-not $ok) { $detalle = "detecto '$($h.Id)' con confianza $($h.Confianza), se esperaba $ConfianzaEsperada" }
    Add-Resultado -Nombre $Nombre -Ok $ok -Detalle $detalle
}

function Assert-NoDetecta {
    param([string] $Nombre, [string] $Texto)
    $h = Find-Secreto -Texto $Texto -Catalogo $catalogo
    $ok = ($null -eq $h)
    $detalle = ''
    if (-not $ok) { $detalle = "falso positivo: '$($h.Id)'" }
    Add-Resultado -Nombre $Nombre -Ok $ok -Detalle $detalle
}


# ── Confianza alta: se bloquea ──────────────────────────────────────────────────

Assert-Detecta 'clave privada PEM' `
    ('-----BEGIN RSA ' + 'PRIVATE KEY-----' + "`nMIIEow==") 'alta'

Assert-Detecta 'identificador de clave de AWS' `
    ('clave = "' + 'AKIA' + 'IOSFODNN7EXAMPLB"') 'alta'

Assert-Detecta 'token de GitHub' `
    ('$t = "' + 'ghp_' + 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"') 'alta'

Assert-Detecta 'token de Slack' `
    ('SLACK=' + 'xoxb-' + '2401009876-2401009876-AbCdEfGhIjKlMnOp') 'alta'

Assert-Detecta 'API key de Google' `
    ('key: ' + 'AIza' + 'SyD1e2F3g4H5i6J7k8L9m0N1o2P3q4R5s6T') 'alta'

Assert-Detecta 'JWT emitido' `
    ('Bear' + 'er ' + 'eyJhbGciOiJIUzI1NiJ9' + '.' + 'eyJzdWIiOiIxMjM0NTY3ODkwIn0' + '.dBjftJeZ4CVPmB92K27uhbUJU1p1r') 'alta'

Assert-Detecta 'credenciales embebidas en una URL' `
    'postgres://usuario:C4mbi4Est0@servidor:5432/base' 'alta'

Assert-Detecta 'password en una cadena de conexion' `
    'Server=srv01;Database=ige;User Id=app;Password=Tr4ns4cc10n;' 'alta'

Assert-Detecta 'client_secret de Keycloak' `
    ('client_' + 'secret: "8f4c2a1e9b7d3f60a5c8"') 'alta'

Assert-Detecta 'cabecera Authorization con token literal' `
    'Authorization: Bearer 8f4c2a1e9b7d3f60a5c8e2b1d7a930f4' 'alta'


# ── Confianza media: se pregunta, no se bloquea ─────────────────────────────────

Assert-Detecta 'asignacion con forma de credencial' `
    ('api_' + 'key = "9f8e7d6c5b4a39281706f5e4d3c2b1a0"') 'media'


# ── Lo que NO tiene que bloquear ────────────────────────────────────────────────
# Cada uno de estos es una forma legitima y frecuente de referirse a un secreto sin
# escribirlo. Trabar cualquiera de ellas hace inusable el harness.

Assert-NoDetecta 'referencia a variable de entorno con llaves' `
    'password = ${DB_PASSWORD}'

Assert-NoDetecta 'referencia a variable de entorno de PowerShell' `
    'password = $env:DB_PASSWORD'

Assert-NoDetecta 'referencia a variable de entorno de Node' `
    'const apiKey = process.env.API_KEY'

Assert-NoDetecta 'referencia a variable de entorno de Python' `
    'password = os.getenv("DB_PASSWORD")'

Assert-NoDetecta 'referencia a variable de entorno de Java' `
    'String secret = System.getenv("CLIENT_SECRET");'

Assert-NoDetecta 'placeholder explicito' `
    ('api_' + 'key = "your-api-key-here"')

Assert-NoDetecta 'placeholder de ejemplo' `
    ('client_' + 'secret = "example-value-para-la-doc"')

Assert-NoDetecta 'valor tachado' `
    'password = xxxxxxxxxxxx'

Assert-NoDetecta 'placeholder entre angulos' `
    ('access_' + 'token = <completar-en-el-deploy>')

Assert-NoDetecta 'variable de entorno estilo Windows' `
    'password = %DB_PASSWORD%'

Assert-NoDetecta 'campo vacio en un archivo de ejemplo' `
    'password='

# Documentar el detector no puede disparar el detector. La comilla invertida es el
# delimitador de codigo de markdown, y sin descartarla entraba al valor: el placeholder
# quedaba como "xxxx`" y ningun patron de ignorar anclado con ^...$ podia matchearlo.
# Paso escribiendo docs/versiones/0.4.0.md, que explica justamente este mecanismo.
Assert-NoDetecta 'relleno entre comillas invertidas de markdown' `
    ('`' + 'password = xxxxxxxxxxxx' + '`')

Assert-NoDetecta 'placeholder entre comillas invertidas, en medio de una oracion' `
    ('el ejemplo `' + 'api_key = your-key-here' + '` se bloqueaba de mas')

Assert-NoDetecta 'la palabra secreto en documentacion' `
    'El client_secret se pide por ticket a DGISIS y se guarda en una variable de entorno.'

Assert-NoDetecta 'una historia de usuario cualquiera' `
    'Como administrador quiero cambiar mi contrasena para mantener segura mi cuenta.'

Assert-NoDetecta 'un comando de git' `
    'git commit -m "arregla la validacion del formulario de acceso"'

Assert-NoDetecta 'un hash de commit' `
    'git checkout a851c90f4e2b8d3c7061f5a4e9b2c8d1f0a3e6b7'

Assert-NoDetecta 'una ruta de archivo larga' `
    'C:\Work\GCBA\IGE\docs\HistoriasUsuario\noticias-backoffice\administracion-noticias.md'


# ── La muestra no puede repetir el secreto ──────────────────────────────────────

$h = Find-Secreto -Texto ('ghp_' + 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8') -Catalogo $catalogo
Assert-Verdadero 'la muestra no reproduce el secreto completo' `
    ($h.Muestra -notmatch 'M3n4O5p6Q7r8') `
    'el motivo entra al contexto y queda en la transcripcion: no puede repetir lo que se acaba de impedir escribir'
Assert-Contiene 'la muestra dice cuanto medía' 'caracteres' $h.Muestra


# ── Punta a punta, por el hook real ─────────────────────────────────────────────

Set-Grupo 'Secretos — por el hook'

function New-PayloadHerramienta {
    param([string] $Herramienta, $Entrada)
    return (ConvertTo-Json -Depth 10 -InputObject @{
        session_id      = 'test-secretos'
        cwd             = 'C:\Work\GCBA\IGE'
        hook_event_name = 'PreToolUse'
        tool_name       = $Herramienta
        tool_input      = $Entrada
    })
}

$hookPre = Join-Path $script:Raiz 'comun\hooks\pre-tool-use.ps1'

# Escribir una clave privada: se bloquea.
$r = Invoke-HookEnProceso -Script $hookPre -JsonEntrada (New-PayloadHerramienta 'Write' @{
    file_path = 'C:\Work\GCBA\IGE\config\app.yml'
    content   = ('-----BEGIN ' + 'PRIVATE KEY-----' + "`nMIIEvQIBADAN")
})
Assert-Igual 'el hook sale con codigo 0 aun bloqueando' 0 $r.Codigo
Assert-Contiene 'bloquea la escritura de una clave privada' '"permissionDecision":"deny"' $r.Salida
Assert-Contiene 'el motivo dice que hacer' 'fuera del repositorio' $r.Salida

# Un comando con credenciales en la URL: se bloquea.
$r = Invoke-HookEnProceso -Script $hookPre -JsonEntrada (New-PayloadHerramienta 'Bash' @{
    command = 'psql postgres://app:C4mbi4Est0@srv01:5432/ige -c "select 1"'
})
Assert-Contiene 'bloquea un comando con credenciales en la URL' '"permissionDecision":"deny"' $r.Salida

# Algo ambiguo: se pregunta, no se bloquea.
$r = Invoke-HookEnProceso -Script $hookPre -JsonEntrada (New-PayloadHerramienta 'Write' @{
    file_path = 'C:\Work\GCBA\IGE\src\config.ts'
    content   = ('const api' + 'Key = "9f8e7d6c5b4a39281706f5e4d3c2b1a0";')
})
Assert-Contiene 'lo ambiguo pregunta en vez de bloquear' '"permissionDecision":"ask"' $r.Salida
Assert-Verdadero 'lo ambiguo NO bloquea' ($r.Salida -notmatch '"deny"') `
    'bloquear lo dudoso es como se pierde un harness'

# Contenido legitimo: silencio absoluto.
$r = Invoke-HookEnProceso -Script $hookPre -JsonEntrada (New-PayloadHerramienta 'Write' @{
    file_path = 'C:\Work\GCBA\IGE\docs\hu.md'
    content   = 'Como administrador quiero publicar una noticia. La clave se lee de $env:APP_SECRET.'
})
Assert-Igual 'contenido legitimo sale con codigo 0' 0 $r.Codigo
Assert-Vacio 'contenido legitimo no emite nada' $r.Salida

# Edit trae new_string en vez de content.
$r = Invoke-HookEnProceso -Script $hookPre -JsonEntrada (New-PayloadHerramienta 'Edit' @{
    file_path  = 'C:\Work\GCBA\IGE\src\config.ts'
    old_string = 'const token = ""'
    new_string = ('const token = "' + 'ghp_' + 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"')
})
Assert-Contiene 'tambien mira new_string, no solo content' '"permissionDecision":"deny"' $r.Salida
