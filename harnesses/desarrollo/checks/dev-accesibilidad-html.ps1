<#
.SYNOPSIS
    Check: accesibilidad comprobable sobre el marcado (ley 26.653 · WCAG).

.DESCRIPTION
    La accesibilidad no es una mejora: es condicion de aprobacion, y en el GCBA es
    exigible por ley. La mayor parte no se puede verificar con una maquina —si el texto
    alternativo describe la imagen, si el orden de foco tiene sentido— pero un puñado sí,
    y son justamente las que se arreglan en diez segundos mientras el archivo esta
    abierto, y en dos horas cuando vuelve rebotado de una auditoria.

    Lo que mira, todo inequivoco:

      - `<html>` sin `lang`. Sin eso el lector de pantalla pronuncia el castellano con
        fonetica inglesa y la pagina es inescuchable.
      - `<img>` sin atributo `alt`. Ojo: `alt=""` es correcto y no se reporta — declara
        que la imagen es decorativa. Lo que falla es que el atributo no este.
      - Un control de formulario que no puede tener etiqueta asociada: sin `id`, sin
        `aria-label` y sin `aria-labelledby` no hay forma de nombrarlo.
      - Mas de un `<h1>`, o ninguno.

.NOTES
    Avisa, no bloquea. Y no intenta juzgar contraste ni orden de lectura: para eso hace
    falta renderizar, y un check que adivina es un check que se ignora.
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

$esHtml = ($archivo.Extension -eq '.html') -or
          ($archivo.Nombre -match '\.blade\.php$') -or
          ($archivo.Nombre -match '\.component\.html$')
if (-not $esHtml) { return }

$texto = $archivo.Texto
$hallazgos = New-Object System.Collections.ArrayList

# ── El idioma del documento ─────────────────────────────────────────────────────
# Solo si el archivo ES un documento. Un parcial o un componente no llevan <html>.
$html = [regex]::Match($texto, '(?is)<html\b[^>]*>')
if ($html.Success -and $html.Value -notmatch '(?i)\slang\s*=') {
    [void] $hallazgos.Add(
        "[a11y] $($archivo.Nombre): <html> sin atributo lang. " +
        "El lector de pantalla necesita saber el idioma para elegir la fonetica; sin eso lee el castellano como si fuera ingles."
    )
}

# ── Texto alternativo ───────────────────────────────────────────────────────────
$sinAlt = New-Object System.Collections.ArrayList
foreach ($m in [regex]::Matches($texto, '(?is)<img\b[^>]*>')) {
    if ($m.Value -match '(?i)\salt\s*=') { continue }
    [void] $sinAlt.Add("L" + (Get-LineaDe -Texto $texto -Indice $m.Index))
}
if ($sinAlt.Count -gt 0) {
    [void] $hallazgos.Add(
        "[a11y] $($archivo.Nombre): $($sinAlt.Count) <img> sin atributo alt — " + (Format-Lista -Items $sinAlt) + ". " +
        "Si la imagen es decorativa va alt=`"`" vacio, que es una afirmacion; que el atributo falte no dice nada."
    )
}

# ── Controles que no pueden ser etiquetados ─────────────────────────────────────
$sinNombre = New-Object System.Collections.ArrayList
foreach ($m in [regex]::Matches($texto, '(?is)<(input|select|textarea)\b[^>]*>')) {
    $tag = $m.Value
    if ($tag -match '(?i)type\s*=\s*["'']?(hidden|submit|button|reset|image)') { continue }
    if ($tag -match '(?i)\s(id|aria-label|aria-labelledby|title)\s*=') { continue }
    [void] $sinNombre.Add("L" + (Get-LineaDe -Texto $texto -Indice $m.Index))
}
if ($sinNombre.Count -gt 0) {
    [void] $hallazgos.Add(
        "[a11y] $($archivo.Nombre): $($sinNombre.Count) control(es) de formulario sin forma de nombrarlos — " +
        (Format-Lista -Items $sinNombre) + ". " +
        "Sin id que un <label for> pueda apuntar, ni aria-label, el control se anuncia como `"cuadro de edicion`" y nada mas."
    )
}

# ── Jerarquia de encabezados ────────────────────────────────────────────────────
# Solo sobre documentos completos: un parcial puede legitimamente no tener h1.
if ($html.Success) {
    $h1 = [regex]::Matches($texto, '(?is)<h1\b[^>]*>').Count
    if ($h1 -eq 0) {
        [void] $hallazgos.Add(
            "[a11y] $($archivo.Nombre): la pagina no tiene <h1>. Es el titulo con el que se navega el documento."
        )
    } elseif ($h1 -gt 1) {
        [void] $hallazgos.Add(
            "[a11y] $($archivo.Nombre): hay $h1 elementos <h1>. Va uno solo: los demas niveles son h2 en adelante, sin saltos."
        )
    }
}

return $hallazgos
