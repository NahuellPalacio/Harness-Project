<#
.SYNOPSIS
    Infraestructura de hooks del harness GCBA.

.DESCRIPTION
    Todo hook del harness se escribe sobre este modulo. Se encarga de las cuatro cosas
    que son identicas en los cuatro eventos y que, hechas mal, fallan en silencio:

      1. Encoding UTF-8 en entrada y salida. PowerShell 5.1 usa la codepage ANSI por
         defecto: sin esto, cualquier aviso con tilde llega corrupto al contexto.
      2. Lectura del evento JSON por stdin.
      3. Las tres unicas formas de salida validas (silencio / avisar / bloquear).
      4. Control de errores: un hook JAMAS rompe la sesion. Ante cualquier excepcion
         reporta una vez y sale con codigo 0.

    Compatible con Windows PowerShell 5.1. No usa operador ternario, ni ??, ni
    ConvertFrom-Json -AsHashtable, ni ninguna otra cosa que solo exista en PS 7.

.NOTES
    ConvertTo-Json lleva -Depth 10 SIEMPRE y de forma explicita. El default de PS 5.1
    es 2 y trunca objetos anidados sin avisar.
#>

Set-StrictMode -Version 2.0

# El nombre de evento que el harness ya emitio en esta sesion, para no repetir avisos
# de error. Se persiste en disco porque cada hook es un proceso nuevo.
$script:DirEstado = Join-Path $env:TEMP 'gcba-harness'


function Initialize-HookEncoding {
    <#
    .SYNOPSIS
        Fuerza UTF-8 sin BOM en la SALIDA. Se llama automaticamente.
    .NOTES
        Deliberadamente NO toca [Console]::InputEncoding.

        Asignar InputEncoding recrea el objeto Console.In, y cuando stdin ya viene
        redirigido desde una tuberia -que es siempre, en un hook- esa recreacion
        corrompe la lectura: ConvertFrom-Json termina fallando con "Primitivo JSON
        no valido". La entrada se lee con su propio StreamReader en Read-HookEvent,
        que es la forma correcta de fijar el encoding sin tocar el estado global.
    #>
    [CmdletBinding()]
    param()

    $utf8 = New-Object System.Text.UTF8Encoding $false
    try { [Console]::OutputEncoding = $utf8 } catch { }
    $OutputEncoding = $utf8
}


function Read-HookEvent {
    <#
    .SYNOPSIS
        Lee el evento JSON desde stdin y lo devuelve como objeto.
    .OUTPUTS
        PSCustomObject con el evento, o $null si stdin vino vacio.
    #>
    [CmdletBinding()]
    param()

    $entrada = [Console]::OpenStandardInput()
    $lector  = New-Object System.IO.StreamReader(
        $entrada,
        (New-Object System.Text.UTF8Encoding $false),
        $true)   # detectar BOM: si viene, se descarta en vez de romper el parseo

    try   { $crudo = $lector.ReadToEnd() }
    finally { $lector.Dispose() }

    if ([string]::IsNullOrWhiteSpace($crudo)) { return $null }

    return ($crudo.Trim() | ConvertFrom-Json)
}


function Get-HookField {
    <#
    .SYNOPSIS
        Lee una propiedad anidada de un evento sin explotar si no existe.
    .DESCRIPTION
        Con Set-StrictMode 2.0, tocar una propiedad ausente de un PSCustomObject es
        un error terminante. Los eventos de Claude Code varian de forma segun el
        tipo de herramienta, asi que el acceso directo no sirve.
    .EXAMPLE
        Get-HookField -Evento $e -Ruta 'tool_input.file_path' -Default ''
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [AllowNull()] $Evento,
        [Parameter(Mandatory)] [string] $Ruta,
        $Default = $null
    )

    $actual = $Evento
    foreach ($parte in $Ruta.Split('.')) {
        if ($null -eq $actual) { return $Default }
        if ($actual -isnot [psobject]) { return $Default }
        $prop = $actual.PSObject.Properties[$parte]
        if ($null -eq $prop) { return $Default }
        $actual = $prop.Value
    }

    if ($null -eq $actual) { return $Default }
    return $actual
}


function Write-HookJson {
    <#
    .SYNOPSIS
        Emite un objeto como JSON compacto por stdout. Uso interno.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] $Objeto)

    [Console]::Out.Write((ConvertTo-Json -InputObject $Objeto -Depth 10 -Compress))
}


function Write-HookContext {
    <#
    .SYNOPSIS
        AVISA: inyecta texto en el contexto de Claude sin interrumpir nada.
    .DESCRIPTION
        Es la forma normal de comunicar un incumplimiento. Claude lo lee y corrige en
        el turno siguiente. No traba a nadie.

        Solo tiene efecto real en PostToolUse, UserPromptSubmit y SessionStart: en
        PreToolUse la salida en exito va a la transcripcion y el modelo no la ve. Por
        eso todos los avisos del harness se entregan en PostToolUse.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string] $EventName,
        [Parameter(Mandatory)] [string] $Texto
    )

    if ([string]::IsNullOrWhiteSpace($Texto)) { return }

    Write-HookJson @{
        hookSpecificOutput = @{
            hookEventName     = $EventName
            additionalContext = $Texto
        }
    }
}


function Write-HookDeny {
    <#
    .SYNOPSIS
        BLOQUEA: impide que la herramienta se ejecute.
    .DESCRIPTION
        Reservado para la regla de secretos. Es la unica cosa que el harness bloquea.

        El motivo se le muestra a Claude, asi que tiene que decir que hacer en vez de
        lo que se impidio: "usa una variable de entorno" sirve, "operacion denegada"
        no sirve.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string] $EventName,
        [Parameter(Mandatory)] [string] $Motivo
    )

    Write-HookJson @{
        hookSpecificOutput = @{
            hookEventName            = $EventName
            permissionDecision       = 'deny'
            permissionDecisionReason = $Motivo
        }
    }
}


function Write-HookAsk {
    <#
    .SYNOPSIS
        PREGUNTA: deja que decida la persona en vez de decidir el harness.
    .DESCRIPTION
        Para lo ambiguo. Un patron de credencial que puede ser un identificador comun no
        justifica bloquear —el falso positivo es lo que hace que desinstalen un harness—
        pero tampoco pasar de largo.

        Si una version de Claude Code no reconociera esta forma, el peor caso es que la
        salida se ignore y la herramienta siga. Es el lado seguro de equivocarse: nadie
        queda trabado por un patron dudoso.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string] $EventName,
        [Parameter(Mandatory)] [string] $Motivo
    )

    Write-HookJson @{
        hookSpecificOutput = @{
            hookEventName            = $EventName
            permissionDecision       = 'ask'
            permissionDecisionReason = $Motivo
        }
    }
}


function Write-HookSystemMessage {
    <#
    .SYNOPSIS
        Avisa de un problema del propio harness, una sola vez por sesion.
    .DESCRIPTION
        Un hook que falla en cada llamada llena la sesion de ruido y termina
        desactivado. Este mensaje se emite una vez y despues se calla, dejando marca
        en disco por sesion y evento.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string] $Texto,
        [string] $SessionId = 'sin-sesion',
        [string] $Clave     = 'general'
    )

    try {
        if (-not (Test-Path $script:DirEstado)) {
            New-Item -ItemType Directory -Path $script:DirEstado -Force | Out-Null
        }
        $seguro = ($SessionId + '.' + $Clave) -replace '[^A-Za-z0-9._-]', '_'
        $marca  = Join-Path $script:DirEstado ($seguro + '.avisado')

        if (Test-Path $marca) { return }
        New-Item -ItemType File -Path $marca -Force | Out-Null
    }
    catch {
        # Si no se puede escribir la marca, se avisa igual: perder el aviso es peor
        # que repetirlo.
    }

    Write-HookJson @{ systemMessage = $Texto }
}


function Invoke-Hook {
    <#
    .SYNOPSIS
        Envoltorio de todo hook. Lee el evento, corre el cuerpo y garantiza salida 0.
    .DESCRIPTION
        El contrato con el cuerpo:
          - recibe el evento parseado como unico argumento
          - emite su salida con Write-HookContext / Write-HookDeny, o no emite nada
          - si tira una excepcion, el harness reporta una vez y sigue

        La garantia que da: un check mal escrito nunca rompe la sesion de nadie.
    .EXAMPLE
        Invoke-Hook -EventName 'PostToolUse' -Cuerpo {
            param($e)
            $ruta = Get-HookField -Evento $e -Ruta 'tool_input.file_path' -Default ''
            if ($ruta -like '*.md') { Write-HookContext -EventName 'PostToolUse' -Texto 'ojo' }
        }
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string] $EventName,
        [Parameter(Mandatory)] [scriptblock] $Cuerpo
    )

    Initialize-HookEncoding

    $evento    = $null
    $sessionId = 'sin-sesion'

    try {
        $evento = Read-HookEvent
        if ($null -eq $evento) { exit 0 }

        $sessionId = Get-HookField -Evento $evento -Ruta 'session_id' -Default 'sin-sesion'

        & $Cuerpo $evento
    }
    catch {
        $detalle = $_.Exception.Message
        Write-HookSystemMessage `
            -Texto "harness: fallo el hook $EventName ($detalle). Se omite hasta el proximo reinicio." `
            -SessionId $sessionId `
            -Clave $EventName
    }

    exit 0
}


Export-ModuleMember -Function @(
    'Initialize-HookEncoding',
    'Read-HookEvent',
    'Get-HookField',
    'Write-HookContext',
    'Write-HookDeny',
    'Write-HookAsk',
    'Write-HookSystemMessage',
    'Invoke-Hook'
)
