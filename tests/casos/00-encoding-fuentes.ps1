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


# ── Los .py del harness: la regla dada vuelta ────────────────────────────────────
#
# Python siempre lee un .py en UTF-8 -no depende de la codepage del sistema, a
# diferencia de PowerShell 5.1-, asi que el problema que motiva la regla de arriba no
# existe del lado de Python. Ahi el BOM es el problema: un BOM al principio de un .py
# se cuela como caracter dentro del primer token si algo lo concatena sin filtrarlo -y
# es exactamente lo que hace lib.hook.leer_evento con el stdin de un hook, aunque ahi
# se descarta a proposito con utf-8-sig-. Se guarda siempre sin BOM.
#
# E-28: los .py del harness NO llevan BOM. Los .ps1 que quedan SI, cuando tienen
# acentos -es la seccion de arriba, sin tocar-.

$fuentesPy = Get-ChildItem $script:Raiz -Recurse -Filter '*.py' -File -ErrorAction SilentlyContinue |
             Where-Object { $_.FullName -notmatch '\\\.git\\' -and $_.FullName -notmatch '\\tests\\out\\' -and $_.FullName -notmatch '\\__pycache__\\' }

Assert-Verdadero 'hay fuentes .py para revisar' ($fuentesPy.Count -gt 0) `
    'no se encontro ningun .py'

$conBom = @($fuentesPy | Where-Object {
    $b = [System.IO.File]::ReadAllBytes($_.FullName)
    $b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF
})

Assert-Igual 'E-28 ningun .py con BOM' 0 $conBom.Count
