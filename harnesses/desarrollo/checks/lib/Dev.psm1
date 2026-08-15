<#
.SYNOPSIS
    Ayudantes que comparten los checks de desarrollo.

.DESCRIPTION
    Todos los checks de este harness empiezan igual: averiguar que archivo se acaba de
    escribir, decidir si les incumbe, y leerlo. Repetir eso cuatro veces multiplica por
    cuatro las chances de que uno lo haga distinto.

    La regla que ordena a todos: SALIR TEMPRANO. PostToolUse corre despues de cada
    escritura de cada sesion. Un check que se pone a analizar archivos que no le tocan
    paga latencia en cada turno, y el presupuesto de avisos es de ocho en total: los que
    gasta un check con ruido no los tiene el que encontro algo de verdad.
#>

Set-StrictMode -Version 2.0


function Get-ArchivoEscrito {
    <#
    .SYNOPSIS
        Ruta y contenido del archivo que la herramienta acaba de escribir, o $null.
    .DESCRIPTION
        Se lee del disco y no del evento: MultiEdit manda las ediciones sueltas y Edit
        manda solo el fragmento, asi que el evento no tiene el archivo entero. Lo que
        importa es como quedo, que es lo que va a compilar y lo que va a leer el proximo.
    .OUTPUTS
        Ruta, Nombre, Extension y Texto. $null si no aplica.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowNull()] $Evento)

    $ruta = Get-HookField -Evento $Evento -Ruta 'tool_input.file_path' -Default ''
    if (-not $ruta) { return $null }
    if (-not (Test-Path $ruta)) { return $null }

    # Un archivo enorme no se analiza: el costo no lo justifica y suele ser generado.
    try {
        $info = Get-Item $ruta -ErrorAction Stop
        if ($info.Length -gt 512KB) { return $null }
    } catch { return $null }

    try {
        $texto = [System.IO.File]::ReadAllText($ruta, (New-Object System.Text.UTF8Encoding $false))
    } catch { return $null }

    return [pscustomobject]@{
        Ruta      = $ruta
        Nombre    = (Split-Path $ruta -Leaf)
        Extension = ([System.IO.Path]::GetExtension($ruta)).ToLowerInvariant()
        Texto     = $texto
    }
}


function Test-RutaGenerada {
    <#
    .SYNOPSIS
        Verdadero si la ruta cae en un directorio que nadie escribe a mano.
    .DESCRIPTION
        Avisar sobre node_modules o vendor es garantia de que el harness se apague: el
        hallazgo es correcto y no hay nada que la persona pueda hacer al respecto.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Ruta)

    return ($Ruta -match '[\\/](node_modules|vendor|dist|build|out|bin|obj|\.git|\.venv|__pycache__|coverage|target)[\\/]')
}


function Get-LineaDe {
    <#
    .SYNOPSIS
        Numero de linea (1-based) donde cae un indice de caracter.
    .DESCRIPTION
        Un aviso sin numero de linea obliga a buscar a mano lo que el check ya encontro.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Texto,
        [Parameter(Mandatory)] [int] $Indice
    )

    if ($Indice -le 0) { return 1 }
    if ($Indice -gt $Texto.Length) { $Indice = $Texto.Length }
    return ($Texto.Substring(0, $Indice).Split("`n").Count)
}


function Format-Lista {
    <#
    .SYNOPSIS
        Une hasta N ejemplos y dice cuantos quedaron afuera.
    .DESCRIPTION
        Un aviso que enumera cuarenta ocurrencias no se lee. Tres y el total sí.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowEmptyCollection()] [array] $Items,
        [int] $Maximo = 3
    )

    $muestra = @($Items | Select-Object -First $Maximo)
    $texto = $muestra -join ', '
    if ($Items.Count -gt $Maximo) { $texto += " (+$($Items.Count - $Maximo) mas)" }
    return $texto
}


Export-ModuleMember -Function @('Get-ArchivoEscrito', 'Test-RutaGenerada', 'Get-LineaDe', 'Format-Lista')
