<#
.SYNOPSIS
    Check: nomenclatura de rutas de API (ES0903).

.DESCRIPTION
    ES0903 fija como se nombra un endpoint. Dos reglas se pueden comprobar sin criterio
    humano y sin ambiguedad, y son las dos que mas caro salen de corregir despues:

      1. La ruta lleva la version. Sin version no hay forma de romper el contrato sin
         romperle la aplicacion a alguien.
      2. El recurso es un sustantivo, no un verbo. La accion la dice el metodo HTTP.
         `POST /usuarios` y `POST /crearUsuario` hacen lo mismo y solo el primero deja
         que `GET`, `PUT` y `DELETE` signifiquen algo sobre el mismo recurso.

    La tercera —plural— solo se reporta cuando es inequivoca: un segmento singular
    seguido de un identificador. `/usuario/{id}` es una coleccion mal nombrada; un
    `/salud` suelto puede ser cualquier cosa y no se toca.

.NOTES
    Avisa, no bloquea. Y se calla en cuanto la ruta no parece una ruta de API: un check
    de nomenclatura con falsos positivos se desactiva la primera semana.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [AllowNull()] $Evento,
    [Parameter(Mandatory)] [AllowEmptyString()] [string] $Proyecto,
    [Parameter(Mandatory)] [AllowNull()] $Config
)

Import-Module (Join-Path $PSScriptRoot 'lib\Dev.psm1') -Force

$archivo = Get-ArchivoEscrito -Evento $Evento
if ($null -eq $archivo) { return }
if (Test-RutaGenerada -Ruta $archivo.Ruta) { return }

$extensionesPosibles = @('.yaml', '.yml', '.json', '.raml', '.ts', '.js', '.php', '.java', '.cs', '.py')
if ($archivo.Extension -notin $extensionesPosibles) { return }

$prefijo = 'api'
if ($null -ne $Config -and $Config.PSObject.Properties['prefijoApi'] -and $Config.prefijoApi) {
    $prefijo = "$($Config.prefijoApi)"
}

# Solo rutas que arrancan con el prefijo de API del proyecto. Sin esto el check se
# pondria a opinar sobre rutas de front, imports y cualquier cadena con barras.
$patronRuta = '["''`](/' + [regex]::Escape($prefijo) + '/[^"''`\s]*)["''`]'
$encontradas = [regex]::Matches($archivo.Texto, $patronRuta)
if ($encontradas.Count -eq 0) { return }

$verbos = @(
    'get','post','put','patch','delete','create','update','remove','add','fetch','list','find','search','save','load',
    'crear','obtener','listar','buscar','guardar','eliminar','borrar','actualizar','modificar','consultar','traer','alta','baja'
)

$sinVersion = New-Object System.Collections.ArrayList
$conVerbo   = New-Object System.Collections.ArrayList
$singulares = New-Object System.Collections.ArrayList
$yaVistas   = New-Object System.Collections.ArrayList

foreach ($m in $encontradas) {
    $ruta = $m.Groups[1].Value
    if ($yaVistas -contains $ruta) { continue }
    [void] $yaVistas.Add($ruta)

    $linea = Get-LineaDe -Texto $archivo.Texto -Indice $m.Index
    $etiqueta = "$ruta (L$linea)"

    if ($ruta -notmatch '/v\d+(/|$)') { [void] $sinVersion.Add($etiqueta) }

    $segmentos = @($ruta.Split('/') | Where-Object { $_ })
    for ($i = 0; $i -lt $segmentos.Count; $i++) {
        $s = $segmentos[$i]
        if ($s -match '^\{.*\}$' -or $s -match '^:' -or $s -match '^v\d+$' -or $s -eq $prefijo) { continue }

        # El verbo se busca como palabra entera o como primer termino en camelCase.
        # Sin eso, "postulaciones" se reportaria por empezar con "post".
        #
        # El primer termino NO se saca con -split sobre un patron de ancho cero: en
        # PowerShell una alternativa que puede matchear vacio parte en cada caracter, y
        # 'crearUsuario' termina siendo doce pedazos de una letra. Se corta el separador
        # explicito primero y despues se toma la corrida inicial de minusculas.
        $base = ($s -split '[-_]')[0]
        $primerTermino = ([regex]::Match($base, '^[A-Za-z][a-z]*')).Value.ToLowerInvariant()
        if ($verbos -contains $s.ToLowerInvariant() -or ($primerTermino -and $verbos -contains $primerTermino)) {
            if ($conVerbo -notcontains $etiqueta) { [void] $conVerbo.Add($etiqueta) }
        }

        # Singular solo cuando es inequivoco: viene un identificador atras.
        $siguiente = if ($i + 1 -lt $segmentos.Count) { $segmentos[$i + 1] } else { '' }
        if ($siguiente -match '^\{.*\}$' -or $siguiente -match '^:') {
            if ($s -notmatch 's$' -and $s -notmatch '^v\d+$') {
                if ($singulares -notcontains $etiqueta) { [void] $singulares.Add($etiqueta) }
            }
        }
    }
}

$hallazgos = New-Object System.Collections.ArrayList

if ($sinVersion.Count -gt 0) {
    [void] $hallazgos.Add(
        "[ES0903] $($archivo.Nombre): ruta(s) de API sin version — " + (Format-Lista -Items $sinVersion) + ". " +
        "Deberia ser /$prefijo/v1/... : sin la version en la ruta no hay forma de cambiar el contrato sin romperle la aplicacion a quien ya la consume."
    )
}

if ($conVerbo.Count -gt 0) {
    [void] $hallazgos.Add(
        "[ES0903] $($archivo.Nombre): la accion va en el metodo HTTP, no en la ruta — " + (Format-Lista -Items $conVerbo) + ". " +
        "El recurso se nombra con un sustantivo; que sea alta, consulta o baja lo dice POST, GET o DELETE."
    )
}

if ($singulares.Count -gt 0) {
    [void] $hallazgos.Add(
        "[ES0903] $($archivo.Nombre): coleccion en singular — " + (Format-Lista -Items $singulares) + ". " +
        "El segmento que lleva un identificador atras es una coleccion y va en plural."
    )
}

return $hallazgos
