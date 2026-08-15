<#
.SYNOPSIS
    Deteccion de secretos. La unica regla del harness que impide algo.

.DESCRIPTION
    Dos niveles de confianza, y la distincion es lo importante:

      alta  -> se bloquea. Formas inequivocas: una clave privada PEM no es otra cosa.
      media -> se pregunta. Formas plausibles pero ambiguas: decide la persona.

    El falso positivo es el riesgo existencial de este harness. Uno que traba trabajo
    legitimo se desinstala esa misma semana, y ahi se pierde tambien la proteccion que
    si servia. Por eso lo ambiguo pregunta en vez de bloquear.

    Este modulo es solo el detector. Quien decide que hacer con el hallazgo es el hook.
#>

Set-StrictMode -Version 2.0


function Import-PatronesSecretos {
    <#
    .SYNOPSIS
        Carga el catalogo de patrones desde reglas\secretos.patrones.json.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [string] $Ruta)

    if (-not (Test-Path $Ruta)) { throw "no se encontro el catalogo de patrones: $Ruta" }

    $texto = [System.IO.File]::ReadAllText($Ruta, (New-Object System.Text.UTF8Encoding $false))
    return ($texto | ConvertFrom-Json)
}


function Get-ValorDeAsignacion {
    <#
    .SYNOPSIS
        De "password = xxxxx" devuelve "xxxxx". Si no hay asignacion, devuelve todo.
    .DESCRIPTION
        Necesario para que los patrones de ignorar anclados con ^...$ funcionen. Un
        patron como "^x{3,}$" nunca puede matchear contra "password = xxxxx", que es el
        match completo de la regex de deteccion. Anclar sirve justamente para no
        confundir un placeholder con una palabra que lo contenga, asi que la salida no
        es aflojar el anclaje: es aislar el valor.

        Entre los delimitadores que se descartan esta la comilla invertida, y no es un
        detalle de estilo: es el delimitador de codigo de markdown. Sin eso, documentar
        el propio detector lo dispara. Paso al escribir docs/versiones/0.4.0.md, donde
        un relleno obvio entre comillas invertidas se bloqueo como credencial real.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Coincidencia)

    if ($Coincidencia -match '[:=]\s*["''`]?\s*(.+?)\s*["''`]?\s*$') { return $Matches[1] }
    return $Coincidencia
}


function Test-ValorIgnorable {
    <#
    .SYNOPSIS
        Decide si lo detectado es un placeholder y no un secreto.
    .DESCRIPTION
        Es la mitad del trabajo que evita que el harness se vuelva insoportable.
        "password = ${DB_PASSWORD}" y "token = your-token-here" matchean patrones de
        credencial y no son credenciales.

        Se prueba contra el valor aislado y tambien contra la coincidencia entera: hay
        patrones de ignorar que apuntan al valor (^x{3,}$) y otros que pueden aparecer
        en cualquier lado (process.env).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Valor,
        [Parameter(Mandatory)] $Catalogo
    )

    if ([string]::IsNullOrWhiteSpace($Valor)) { return $true }

    $aislado = Get-ValorDeAsignacion -Coincidencia $Valor
    if ([string]::IsNullOrWhiteSpace($aislado)) { return $true }

    foreach ($p in $Catalogo.ignorar.patrones) {
        if ($aislado -match $p) { return $true }
        if ($Valor   -match $p) { return $true }
    }
    return $false
}


function Find-Secreto {
    <#
    .SYNOPSIS
        Busca secretos en un texto. Devuelve el primer hallazgo, o $null.
    .OUTPUTS
        $null, o un objeto con Id, Confianza, Motivo y Muestra.
        Muestra NUNCA contiene el secreto: solo su forma, para que se entienda el aviso
        sin volver a exponer el valor.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Texto,
        [Parameter(Mandatory)] $Catalogo
    )

    if ([string]::IsNullOrWhiteSpace($Texto)) { return $null }

    # Los de confianza alta primero: si hay uno, gana sobre cualquier ambiguo.
    foreach ($nivel in @('alta', 'media')) {
        foreach ($patron in $Catalogo.patrones) {
            if ($patron.confianza -ne $nivel) { continue }

            $m = [regex]::Match($Texto, $patron.regex)
            if (-not $m.Success) { continue }
            if (Test-ValorIgnorable -Valor $m.Value -Catalogo $Catalogo) { continue }

            return [pscustomobject]@{
                Id        = $patron.id
                Confianza = $patron.confianza
                Motivo    = $patron.motivo
                Muestra   = (Get-MuestraSegura -Valor $m.Value)
            }
        }
    }
    return $null
}


function Get-MuestraSegura {
    <#
    .SYNOPSIS
        Describe un hallazgo sin repetir el secreto.
    .DESCRIPTION
        Importa mas de lo que parece: el motivo que devuelve el hook entra al contexto de
        Claude y queda en la transcripcion. Reproducir ahi el valor que se acaba de
        impedir escribir seria absurdo.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string] $Valor)

    $limpio = ($Valor -replace '\s+', ' ').Trim()
    if ($limpio.Length -le 12) { return ($limpio.Substring(0, [Math]::Min(4, $limpio.Length)) + '...') }
    return ($limpio.Substring(0, 12) + '... (' + $limpio.Length + ' caracteres)')
}


function Get-TextoDeHerramienta {
    <#
    .SYNOPSIS
        Extrae de un evento lo que la herramienta esta por escribir o ejecutar.
    .DESCRIPTION
        Cada herramienta trae su carga en un campo distinto. Se juntan todos los que
        pueden llevar contenido en vez de asumir la forma de uno.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowNull()] $Evento)

    if ($null -eq $Evento) { return '' }

    $partes = New-Object System.Collections.ArrayList
    foreach ($campo in @('content', 'new_string', 'command', 'new_source', 'prompt')) {
        $valor = Get-HookField -Evento $Evento -Ruta ('tool_input.' + $campo) -Default ''
        if ($valor) { [void] $partes.Add([string]$valor) }
    }

    # MultiEdit trae una lista de ediciones en vez de un solo new_string.
    $ediciones = Get-HookField -Evento $Evento -Ruta 'tool_input.edits' -Default $null
    if ($ediciones) {
        foreach ($e in $ediciones) {
            if ($e.PSObject.Properties['new_string']) { [void] $partes.Add([string]$e.new_string) }
        }
    }

    return ($partes -join "`n")
}


Export-ModuleMember -Function @(
    'Import-PatronesSecretos',
    'Get-ValorDeAsignacion',
    'Test-ValorIgnorable',
    'Find-Secreto',
    'Get-MuestraSegura',
    'Get-TextoDeHerramienta'
)
