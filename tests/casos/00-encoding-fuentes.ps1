# Verifica una regla del repo que, violada, produce el peor tipo de falla: silenciosa
# y con falsos positivos.
#
# Windows PowerShell 5.1 lee un .ps1 SIN BOM usando la codepage ANSI del sistema, no
# UTF-8. Un archivo guardado en UTF-8 sin BOM que contenga "definición" se carga como
# "definiciÃ³n", y todo mensaje del harness llega ilegible al contexto de Claude.
#
# Peor todavia: un test escrito en ese archivo compara una cadena corrupta contra otra
# cadena corrupta del mismo modo, y PASA. Asi que el problema no solo no se detecta:
# queda tapado por un test en verde. Paso exactamente eso durante la construccion.
#
# La regla, entonces:
#
#   Todo .ps1 o .psm1 que contenga un caracter no ASCII se guarda en UTF-8 CON BOM.
#
# Y su alternativa igual de valida: no poner caracteres no ASCII en el codigo. Los
# archivos de este repo que no llevan texto en español no necesitan BOM.

Set-Grupo 'Encoding de los fuentes'

$fuentes = Get-ChildItem $script:Raiz -Recurse -Include '*.ps1', '*.psm1' -ErrorAction SilentlyContinue |
           Where-Object { $_.FullName -notlike '*\.git\*' }

Assert-Verdadero 'hay fuentes para revisar' ($fuentes.Count -gt 0) `
    'no se encontro ningun .ps1 ni .psm1'

$culpables = @()

foreach ($f in $fuentes) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)

    $tieneBom = ($bytes.Length -ge 3 -and
                 $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)

    $tieneNoAscii = $false
    foreach ($b in $bytes) {
        if ($b -gt 127) { $tieneNoAscii = $true; break }
    }

    if ($tieneNoAscii -and -not $tieneBom) {
        $culpables += $f.FullName.Replace($script:Raiz + '\', '')
    }
}

Assert-Verdadero 'ningun fuente con acentos quedo sin BOM' ($culpables.Count -eq 0) `
    ("se corrompen al cargar: " + ($culpables -join ', '))
