<#
.SYNOPSIS
    Check: la infraestructura no se escribe en el codigo (ES0901).

.DESCRIPTION
    Dos reglas del bloque comun de desarrollo, comprobables sin criterio humano:

      - **Los servidores se referencian por nombre DNS, jamas por IP.** Una IP en el
        fuente ata el codigo a una maquina puntual; el dia que cambia hay que recompilar
        para arreglar algo que era configuracion.
      - **La configuracion va afuera del codigo.** Bases, servicios externos y URLs se
        leen del entorno o de un archivo externo, ni siquiera para probar.

    No pisa al hook de secretos, que es otra cosa y sí bloquea: una IP no es un secreto.
    Lo que se reporta acá es acoplamiento, no filtracion.

.NOTES
    Una IP solo se reporta cuando esta en posicion de host —en una URL, un `host:`, una
    cadena de conexion—. Suelta puede ser una version, una mascara o un dato de prueba, y
    reportarla seria ruido. Las de loopback y las de documentacion no se tocan nunca.
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

$extensiones = @('.ts', '.js', '.java', '.cs', '.php', '.py', '.yml', '.yaml', '.json', '.xml', '.properties', '.conf', '.ini')
if ($archivo.Extension -notin $extensiones) { return }

# Loopback, "cualquier interfaz" y los rangos que la RFC 5737 reserva justamente para
# documentacion y ejemplos. Ninguno ata el codigo a una maquina real.
$ipsInocentes = @('127.0.0.1', '0.0.0.0', '255.255.255.255', '1.2.3.4')
$rangosDeEjemplo = '^(192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)'

# La IP tiene que estar donde va un host. Suelta en el texto es cualquier otra cosa.
$posiciones = @(
    'https?://(\d{1,3}(?:\.\d{1,3}){3})',
    '(?i)\b(?:host|server|hostname|servidor|addr|address|ip)\s*[:=]\s*["'']?(\d{1,3}(?:\.\d{1,3}){3})',
    '(?i)(?:Data\s+Source|Server|Host)\s*=\s*(\d{1,3}(?:\.\d{1,3}){3})',
    '(?i)\b(?:jdbc|mongodb|redis|amqp|mysql|postgres(?:ql)?):[^\s"'']*?@?(\d{1,3}(?:\.\d{1,3}){3})'
)

$ips = New-Object System.Collections.ArrayList
$yaVistas = New-Object System.Collections.ArrayList

foreach ($p in $posiciones) {
    foreach ($m in [regex]::Matches($archivo.Texto, $p)) {
        $ip = $m.Groups[1].Value
        if (-not $ip) { continue }
        if ($ipsInocentes -contains $ip) { continue }
        if ($ip -match $rangosDeEjemplo) { continue }

        # Un octeto fuera de rango significa que no era una IP: una version, una fecha.
        $fuera = $false
        foreach ($o in $ip.Split('.')) { if ([int]$o -gt 255) { $fuera = $true } }
        if ($fuera) { continue }

        $linea = Get-LineaDe -Texto $archivo.Texto -Indice $m.Index
        $etiqueta = "$ip (L$linea)"
        if ($yaVistas -contains $etiqueta) { continue }
        [void] $yaVistas.Add($etiqueta)
        [void] $ips.Add($etiqueta)
    }
}

if ($ips.Count -eq 0) { return }

return @(
    "[ES0901] $($archivo.Nombre): servidor referenciado por IP — " + (Format-Lista -Items $ips) + ". " +
    "Los servidores se nombran por DNS. Una IP en el fuente ata el codigo a una maquina: el dia que cambia " +
    "hay que tocar y desplegar el aplicativo para arreglar algo que era configuracion."
)
