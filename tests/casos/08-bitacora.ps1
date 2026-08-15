# La bitacora por version.
#
# Sin este test, escribir la nota al cerrar una version es una intencion que dura hasta
# la primera semana ocupada. Es la misma logica de los techos del CLAUDE.md: lo que nadie
# mide, no se hace.

Set-Grupo 'Bitacora — una nota por version'

$u8       = New-Object System.Text.UTF8Encoding $false
$changelog = [System.IO.File]::ReadAllText((Join-Path $script:Raiz 'CHANGELOG.md'), $u8)
$dirNotas  = Join-Path $script:Raiz 'docs\versiones'

$versiones = @([regex]::Matches($changelog, '(?m)^##\s*\[(\d+\.\d+\.\d+)\]') |
               ForEach-Object { $_.Groups[1].Value })

Assert-Verdadero 'el CHANGELOG declara versiones' ($versiones.Count -gt 0)

# Cada version del CHANGELOG tiene su nota. Es el corazon del test.
$sinNota = @($versiones | Where-Object { -not (Test-Path (Join-Path $dirNotas "$_.md")) })
Assert-Verdadero 'toda version del CHANGELOG tiene su nota en docs/versiones' `
    ($sinNota.Count -eq 0) ("sin nota: " + ($sinNota -join ', '))

# Y al reves: una nota sin version en el CHANGELOG es una version fantasma.
$notas = @(Get-ChildItem $dirNotas -Filter '*.md' -File |
           Where-Object { $_.BaseName -match '^\d+\.\d+\.\d+$' } |
           Select-Object -ExpandProperty BaseName)
$huerfanas = @($notas | Where-Object { $versiones -notcontains $_ })
Assert-Verdadero 'ninguna nota sobra respecto del CHANGELOG' `
    ($huerfanas.Count -eq 0) ("sobran: " + ($huerfanas -join ', '))

# La version actual tiene la suya. Es el caso que mas se olvida: se cierra la version,
# se commitea, y la nota queda para despues.
$version = ([System.IO.File]::ReadAllText((Join-Path $script:Raiz 'VERSION'), $u8)).Trim()
Assert-Verdadero "la version actual ($version) tiene su nota" `
    (Test-Path (Join-Path $dirNotas "$version.md"))

# Las secciones son fijas: si algo no aplica se escribe que no aplica. Una seccion
# ausente se lee como olvido, no como vacio.
$obligatorias = @(
    '## Qué se hizo',
    '## Qué se decidió, y por qué',
    '## Lo que se rompió en el camino',
    '## Lo que quedó abierto',
    '## Dónde seguir'
)
$incompletas = New-Object System.Collections.ArrayList
foreach ($n in $notas) {
    $texto = [System.IO.File]::ReadAllText((Join-Path $dirNotas "$n.md"), $u8)
    foreach ($s in $obligatorias) {
        if ($texto -notmatch [regex]::Escape($s)) { [void] $incompletas.Add("$n → $s"); break }
    }
}
Assert-Verdadero 'toda nota tiene las cinco secciones' `
    ($incompletas.Count -eq 0) ("incompletas: " + ($incompletas -join '; '))

# El indice del README las lista a todas. Un indice desactualizado es peor que ninguno:
# hace creer que lo que no figura no existe.
$readme = [System.IO.File]::ReadAllText((Join-Path $dirNotas 'README.md'), $u8)
$sinIndexar = @($notas | Where-Object { $readme -notmatch [regex]::Escape("($_.md)") })
Assert-Verdadero 'el README de la bitacora indexa todas las notas' `
    ($sinIndexar.Count -eq 0) ("sin indexar: " + ($sinIndexar -join ', '))
