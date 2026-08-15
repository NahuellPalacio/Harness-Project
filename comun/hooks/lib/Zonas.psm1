<#
.SYNOPSIS
    Lectura y medicion de las zonas del CLAUDE.md.

.DESCRIPTION
    El CLAUDE.md se carga entero al abrir la sesion y ocupa ventana de contexto mientras
    dure. Por eso esta partido en zonas con politica distinta, cada una con su techo.

    Sin una medicion automatica, "mantener chico el CLAUDE.md" es una intencion. Todo
    harness engorda, porque agregar una linea aca siempre va a ser mas facil que escribir
    una skill. El techo es la unica defensa que no depende de la disciplina de nadie.
#>

Set-StrictMode -Version 2.0


function Get-DefinicionZonas {
    <#
    .SYNOPSIS
        Las zonas conocidas, su marcador y la clave de su techo en harness.config.json.
    #>
    [CmdletBinding()]
    param()

    return @(
        [pscustomobject]@{ Nombre = 'ZONA FIJA';   Techo = 'techoZonaFija';   Que = 'reglas que se ejecutan cada turno' },
        [pscustomobject]@{ Nombre = 'ZONA MAPA';   Techo = 'techoZonaMapa';   Que = 'donde esta cada cosa' },
        [pscustomobject]@{ Nombre = 'ZONA INDICE'; Techo = 'techoZonaIndice'; Que = 'punteros al conocimiento'; Alias = @('ZONA ÍNDICE') },
        [pscustomobject]@{ Nombre = 'ZONA CACHE';  Techo = 'techoZonaCache';  Que = 'lo aprendido, todavia sin bajar'; Alias = @('ZONA CACHÉ') }
    )
}


function Get-ContenidoZona {
    <#
    .SYNOPSIS
        Devuelve el texto de una zona, o $null si el archivo no la tiene.
    .DESCRIPTION
        Los marcadores son comentarios HTML que ademas llevan la explicacion de la zona,
        asi que se busca por prefijo y no por igualdad. Se aceptan alias para tolerar la
        variante con tilde y la variante sin tilde del mismo nombre.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Texto,
        [Parameter(Mandatory)] $Zona
    )

    $nombres = @($Zona.Nombre)
    if ($Zona.PSObject.Properties['Alias'] -and $Zona.Alias) { $nombres += $Zona.Alias }

    foreach ($n in $nombres) {
        $iIni = $Texto.IndexOf('<!-- ' + $n)
        if ($iIni -lt 0) { continue }

        $cierreIni = $Texto.IndexOf('-->', $iIni)
        if ($cierreIni -lt 0) { continue }
        $cierreIni += 3

        $iFin = $Texto.IndexOf('<!-- /' + $n, $cierreIni)
        if ($iFin -lt 0) { continue }

        return $Texto.Substring($cierreIni, $iFin - $cierreIni)
    }
    return $null
}


function ConvertTo-NombrePlano {
    <#
    .SYNOPSIS
        Normaliza el nombre de un marcador para poder compararlo: sin tildes, en
        mayusculas y sin el prefijo 'ZONA '.
    .DESCRIPTION
        Sirve para reconocer que 'CACHÉ' y 'ZONA CACHE' son el mismo concepto escrito
        distinto. No se usa para decidir que es canonico -eso lo dice la definicion de
        zonas- sino para poder sugerir el nombre correcto cuando alguien uso otro.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Nombre)

    $descompuesto = $Nombre.Normalize([System.Text.NormalizationForm]::FormD)
    $sb = New-Object System.Text.StringBuilder
    foreach ($c in $descompuesto.ToCharArray()) {
        $cat = [System.Globalization.CharUnicodeInfo]::GetUnicodeCategory($c)
        if ($cat -ne [System.Globalization.UnicodeCategory]::NonSpacingMark) { [void] $sb.Append($c) }
    }
    $plano = $sb.ToString().ToUpperInvariant().Trim()
    return ($plano -replace '^ZONA\s+', '')
}


function Get-MarcadoresHtml {
    <#
    .SYNOPSIS
        Todos los comentarios HTML del texto, con su nombre, si son apertura o cierre,
        y que lineas ocupan.
    .DESCRIPTION
        Un marcador puede ocupar varias lineas -ya paso: la CACHE del prototipo del IGE
        tenia tres- asi que no alcanza con mirar linea por linea. Se ubican los
        comentarios sobre el texto completo y recien despues se traducen a lineas.

        El nombre es la primera corrida de palabras del comentario. Lo que sigue es la
        explicacion de la zona, que cambia sin que cambie la zona, y va separada por
        alguna clase de guion: no se puede confiar en cual. Los archivos generados usan
        raya larga y una persona escribiendo a mano pone un guion comun, asi que el
        nombre se toma por lo que ES -letras, numeros, dos puntos y espacios- y no por
        el separador que venga despues.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Texto)

    $marcadores = New-Object System.Collections.ArrayList
    if (-not $Texto) { return ,$marcadores }

    $lineas = $Texto -split "`n"
    $inicioDeLinea = New-Object int[] ($lineas.Count)
    $acum = 0
    for ($i = 0; $i -lt $lineas.Count; $i++) { $inicioDeLinea[$i] = $acum; $acum += $lineas[$i].Length + 1 }

    $indiceDeLinea = {
        param($offset)
        for ($k = $lineas.Count - 1; $k -ge 0; $k--) { if ($offset -ge $inicioDeLinea[$k]) { return $k } }
        return 0
    }

    foreach ($m in [regex]::Matches($Texto, '(?s)<!--.*?-->')) {
        $interior = $m.Value.Substring(4, $m.Value.Length - 7)
        $primera  = ($interior -split "`n")[0]

        $nom = [regex]::Match($primera, '^\s*(/?)\s*([\p{L}\p{N}:_]+(?:\s+[\p{L}\p{N}:_]+)*)')
        if (-not $nom.Success) { continue }

        $esCierre = ($nom.Groups[1].Value -eq '/')
        $nombre   = $nom.Groups[2].Value.Trim()
        if (-not $nombre) { continue }

        [void] $marcadores.Add([pscustomobject]@{
            Nombre     = $nombre
            EsCierre   = $esCierre
            LineaIni   = (& $indiceDeLinea $m.Index)
            LineaFin   = (& $indiceDeLinea ($m.Index + $m.Length - 1))
        })
    }

    return ,$marcadores
}


function Find-ZonasNoReconocidas {
    <#
    .SYNOPSIS
        Marcadores con forma de zona que el harness no reconoce.
    .DESCRIPTION
        Un par de comentarios HTML de apertura y cierre con el mismo nombre ES una zona,
        la haya escrito el harness o una persona. Si el nombre no coincide con ninguna
        zona canonica, agregar la zona canonica al lado deja el archivo con dos: una con
        el contenido real y otra vacia, y el check mide la vacia.

        Ya paso, y paso en silencio: el CLAUDE.md del IGE traia 'INDICE' y 'CACHE' sin
        el prefijo 'ZONA', el instalador no los reconocio y agrego duplicados sin decir
        nada. Callarse fue peor que equivocarse.
    .OUTPUTS
        Una fila por marcador desconocido: Marcador y Parecida (la zona canonica a la
        que se parece, o cadena vacia si no se parece a ninguna).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Texto)

    $hallazgos = New-Object System.Collections.ArrayList

    $canonicos = New-Object System.Collections.ArrayList
    foreach ($z in (Get-DefinicionZonas)) {
        [void] $canonicos.Add($z.Nombre)
        if ($z.PSObject.Properties['Alias'] -and $z.Alias) { foreach ($a in $z.Alias) { [void] $canonicos.Add($a) } }
    }
    # El bloque comun lo genera el instalador y tambien es un par apertura/cierre.
    [void] $canonicos.Add('HARNESS:COMUN')

    $marcadores = Get-MarcadoresHtml -Texto $Texto
    $aperturas  = @($marcadores | Where-Object { -not $_.EsCierre })
    $cierres    = @($marcadores | Where-Object { $_.EsCierre } | Select-Object -ExpandProperty Nombre)

    $yaVistos = New-Object System.Collections.ArrayList
    foreach ($a in $aperturas) {
        if ($canonicos -contains $a.Nombre) { continue }
        if ($cierres -notcontains $a.Nombre) { continue }   # sin cierre no es una zona
        if ($yaVistos -contains $a.Nombre)  { continue }
        [void] $yaVistos.Add($a.Nombre)

        $plano = ConvertTo-NombrePlano -Nombre $a.Nombre
        $parecida = ''
        foreach ($z in (Get-DefinicionZonas)) {
            if ((ConvertTo-NombrePlano -Nombre $z.Nombre) -eq $plano) { $parecida = $z.Nombre; break }
        }

        [void] $hallazgos.Add([pscustomobject]@{ Marcador = $a.Nombre; Parecida = $parecida })
    }

    return ,$hallazgos
}


function Measure-FueraDeZonas {
    <#
    .SYNOPSIS
        Cuenta las lineas con contenido que no estan dentro de ningun bloque marcado.
    .DESCRIPTION
        Measure-Zonas mide lo que esta ADENTRO de las zonas. Lo que queda afuera no lo
        mide nadie: no se puede purgar, no se puede bajar al conocimiento del proyecto
        y no cuenta contra ningun techo. Un CLAUDE.md de trescientas lineas sin un solo
        marcador pasa la medicion entera sin que el harness diga una palabra.

        No es un pecado tener algo afuera: el titulo del archivo y dos lineas de
        presentacion van afuera y esta bien. Es un problema cuando es mucho, porque
        entonces el mecanismo entero es decorativo.
    .OUTPUTS
        Lineas (cuantas con contenido) y Muestra (las primeras, para poder nombrarlas).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Texto)

    if (-not $Texto) { return [pscustomobject]@{ Lineas = 0; Muestra = @() } }

    $lineas  = $Texto -split "`n"
    $tapada  = New-Object bool[] ($lineas.Count)

    $marcadores = Get-MarcadoresHtml -Texto $Texto

    # El marcador en si no es contenido.
    foreach ($m in $marcadores) {
        for ($i = $m.LineaIni; $i -le $m.LineaFin -and $i -lt $lineas.Count; $i++) { $tapada[$i] = $true }
    }

    # Todo lo que va entre una apertura y su cierre esta adentro de un bloque.
    for ($k = 0; $k -lt $marcadores.Count; $k++) {
        $a = $marcadores[$k]
        if ($a.EsCierre) { continue }
        for ($j = $k + 1; $j -lt $marcadores.Count; $j++) {
            $c = $marcadores[$j]
            if ($c.EsCierre -and $c.Nombre -eq $a.Nombre) {
                for ($i = $a.LineaFin; $i -le $c.LineaIni -and $i -lt $lineas.Count; $i++) { $tapada[$i] = $true }
                break
            }
        }
    }

    $afuera = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt $lineas.Count; $i++) {
        if ($tapada[$i]) { continue }
        $l = $lineas[$i].Trim()
        if ($l) { [void] $afuera.Add($l) }
    }

    return [pscustomobject]@{
        Lineas  = $afuera.Count
        Muestra = @($afuera | Select-Object -First 3)
    }
}


function Measure-Zonas {
    <#
    .SYNOPSIS
        Mide cada zona de un CLAUDE.md contra su techo.
    .OUTPUTS
        Una fila por zona: Nombre, Existe, Lineas, Techo, Excedida.
    .NOTES
        Se cuentan lineas con contenido. Las vacias son formato, no informacion, y
        castigarlas empujaria a escribir CLAUDE.md ilegibles para pasar la medicion.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Texto,
        [Parameter(Mandatory)] [AllowNull()] $Config
    )

    $resultado = New-Object System.Collections.ArrayList

    foreach ($zona in (Get-DefinicionZonas)) {
        $contenido = Get-ContenidoZona -Texto $Texto -Zona $zona

        $techo = 0
        if ($null -ne $Config -and $Config.PSObject.Properties[$zona.Techo]) {
            $techo = [int]$Config.($zona.Techo)
        }

        $lineas = 0
        if ($null -ne $contenido) {
            $lineas = @($contenido -split "`n" | Where-Object { $_.Trim() }).Count
        }

        [void] $resultado.Add([pscustomobject]@{
            Nombre   = $zona.Nombre
            Que      = $zona.Que
            Existe   = ($null -ne $contenido)
            Lineas   = $lineas
            Techo    = $techo
            Excedida = ($techo -gt 0 -and $lineas -gt $techo)
        })
    }

    return ,$resultado
}


Export-ModuleMember -Function @(
    'Get-DefinicionZonas',
    'Get-ContenidoZona',
    'Measure-Zonas',
    'Find-ZonasNoReconocidas',
    'Measure-FueraDeZonas'
)
