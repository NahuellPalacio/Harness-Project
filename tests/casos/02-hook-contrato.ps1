# Tests del contrato punta a punta: hook como proceso hijo, JSON por stdin, igual que
# lo invoca Claude Code. Es lo unico que prueba de verdad que el mecanismo funciona.

Set-Grupo 'Contrato de hooks — punta a punta'


# ── El camino normal: silencio ──────────────────────────────────────────────────
# Es el caso de la enorme mayoria de las llamadas. Cualquier byte de mas se paga en
# cada llamada a herramienta de cada sesion.

$r = Invoke-HookEnProceso -Script (Get-Fixture 'hook-silencio.ps1') `
                          -JsonEntrada (Get-Payload 'post-tool-use-write.json')

Assert-Igual 'sin hallazgos sale con codigo 0' 0 $r.Codigo
Assert-Vacio 'sin hallazgos no escribe absolutamente nada' $r.Salida


# ── Avisar ──────────────────────────────────────────────────────────────────────

$r = Invoke-HookEnProceso -Script (Get-Fixture 'hook-eco.ps1') `
                          -JsonEntrada (Get-Payload 'post-tool-use-write.json')

Assert-Igual 'el aviso sale con codigo 0' 0 $r.Codigo
Assert-Contiene 'el aviso llega como additionalContext' 'additionalContext' $r.Salida
Assert-Contiene 'el hook leyo la ruta del evento' 'ejemplo.md' $r.Salida


# ── Bloquear ────────────────────────────────────────────────────────────────────

$r = Invoke-HookEnProceso -Script (Get-Fixture 'hook-deny.ps1') `
                          -JsonEntrada (Get-Payload 'pre-tool-use-write.json')

Assert-Igual 'el bloqueo tambien sale con codigo 0' 0 $r.Codigo
Assert-Contiene 'el bloqueo declara deny' '"permissionDecision":"deny"' $r.Salida
Assert-Contiene 'el motivo dice que hacer, no solo que se impidio' 'variable de entorno' $r.Salida


# ── Encoding: el que mas silenciosamente rompe todo ─────────────────────────────
# Toda la normativa del GCBA esta en español. Si esto falla, cada aviso del harness
# llega ilegible al contexto y nadie entiende por que.

$r = Invoke-HookEnProceso -Script (Get-Fixture 'hook-eco.ps1') `
                          -JsonEntrada (Get-Payload 'encoding-acentos.json')

Assert-Igual 'el payload con acentos sale con codigo 0' 0 $r.Codigo
Assert-Contiene 'sobrevive la frase completa con tilde, guion largo y eñe' `
    'definición pendiente — ñandú' $r.Salida
Assert-Contiene 'sobreviven las vocales acentuadas en mayuscula' 'ÁÉÍÓÚ' $r.Salida
Assert-Contiene 'sobrevive la dieresis' 'üÜ' $r.Salida
Assert-Contiene 'sobreviven los signos de apertura' '¡señor!' $r.Salida
Assert-Contiene 'sobrevive el acento en la ruta del archivo' 'definición.md' $r.Salida


# ── La garantia central: un check roto no rompe la sesion ───────────────────────

# Se limpian las marcas porque lo que viene verifica el aviso de "una vez por sesion":
# si algo antes ya lo consumio, este bloque pasaria o fallaria por accidente.
Clear-MarcasHarness

$r = Invoke-HookEnProceso -Script (Get-Fixture 'hook-explota.ps1') `
                          -JsonEntrada (Get-Payload 'post-tool-use-write.json')

Assert-Igual 'un hook que explota igual sale con codigo 0' 0 $r.Codigo
Assert-Contiene 'reporta el problema como systemMessage' 'systemMessage' $r.Salida
Assert-Contiene 'el mensaje nombra el hook que fallo' 'PostToolUse' $r.Salida

$esJson = $true
try { $r.Salida | ConvertFrom-Json | Out-Null } catch { $esJson = $false }
Assert-Verdadero 'incluso al fallar, la salida sigue siendo JSON valido' $esJson `
    'un stack trace en stdout corrompe el contrato con Claude Code'

# Segunda invocacion con la misma sesion: el aviso NO se repite. Un hook roto que
# grita en cada llamada llena la sesion de ruido y termina desactivado.
$r2 = Invoke-HookEnProceso -Script (Get-Fixture 'hook-explota.ps1') `
                           -JsonEntrada (Get-Payload 'post-tool-use-write.json')

Assert-Igual 'la segunda falla en la misma sesion tambien sale 0' 0 $r2.Codigo
Assert-Vacio 'la segunda falla ya no vuelve a avisar' $r2.Salida


# ── stdin vacio ─────────────────────────────────────────────────────────────────
# Puede pasar por un problema de la tuberia. No es motivo para hacer ruido.

$r = Invoke-HookEnProceso -Script (Get-Fixture 'hook-eco.ps1') -JsonEntrada ''

Assert-Igual 'stdin vacio sale con codigo 0' 0 $r.Codigo
Assert-Vacio 'stdin vacio no emite nada' $r.Salida


# ── stdin con basura ────────────────────────────────────────────────────────────

$r = Invoke-HookEnProceso -Script (Get-Fixture 'hook-eco.ps1') -JsonEntrada 'esto no es json'

Assert-Igual 'stdin invalido no rompe la sesion' 0 $r.Codigo
