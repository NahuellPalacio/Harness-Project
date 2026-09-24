# Verificación — Los hooks se registran para PowerShell, y el instalador prueba el comando que registró

**Estado:** cerrado · **Fecha:** 24-09-2026 · **Versión:** 0.21.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 24-09-2026
en **un pase**. Corrió la compuerta completa `.\tests\Invoke-Tests.ps1` con el árbol quieto:
`32755/32755`, EXIT=0, con 388 tests de PowerShell. De esos, 115 aserciones son del grupo "Instalador -
hooks registrados para PowerShell".

Además hizo una instalación real de `analisis,desarrollo` en un directorio temporal y revisó el
`settings.json` que quedó:
- el `&` es literal, con 0 apariciones de `\u0026`;
- no hay ninguna ruta con unidad;
- no hay ningún `${`;
- `-Doctor` dio `los cuatro hooks registrados en settings.json responden`.

**Resultado: 11 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

## Los veredictos

Todos los tests están en `tests/casos/03-instalador.ps1`, grupo "Instalador - hooks registrados para
PowerShell".

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Los cuatro hooks con `"shell": "powershell"`, `& "$env:CLAUDE_PROJECT_DIR/…"` y `; exit $LASTEXITCODE` | sostenido | sí | `E-01 <evento> fija shell…`, `…empieza con &…`, `…termina con ; exit…`, `…no usa $CLAUDE_PROJECT_DIR sin env:`, `…no usa ${` |
| E-02 | Los dos filtros nombran `PowerShell` | sostenido | sí | `E-02 el filtro de PreToolUse/PostToolUse nombra PowerShell, exacto` |
| E-03 | Cada comando registrado sale con 0 y JSON válido o vacío | sostenido | sí | `E-03 <evento> sale con 0`, `…JSON valido o nada`, `…PowerShell no reporta ningun error` |
| E-04 | Lo mismo con una ruta con espacios, apóstrofo y `$` | sostenido | sí | `E-04 …ruta rara` |
| E-05 | El comando viejo, corrido igual, falla | sostenido | sí | `E-05 el comando viejo de <evento> falla` |
| E-06 | Un comando registrado que no corre revierte la instalación | sostenido | sí | `E-06 la instalacion sale con codigo de fallo` … `no deja hooks` |
| E-07 | La verificación corre lo registrado y no lanza `run-hook.cmd` por su cuenta | sostenido | sí | `E-07 … la compuerta falla en los cuatro`, `E-07 … corre solo lo registrado` |
| E-08 | `-Doctor` informa el `settings.json` viejo y no el nuevo | sostenido | sí | `E-08 -Doctor con el settings.json viejo…`, `…con el nuevo no informa nada…`, `E-08 y dice que responden` |
| E-09 | `-Update` deja el `settings.json` nuevo y su hash al día | sostenido | sí | `E-09 -Update deja los comandos nuevos`, `…el hash … coincide` |
| E-10 | `PowerShell` con un secreto de confianza alta sale denegado | sostenido | sí | `E-10 PowerShell con un secreto de confianza alta sale denegado` |
| E-11 | La salida UTF-8 con tildes sale igual byte a byte | sostenido | sí | `E-11 byte a byte igual que por el lanzador directo` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los once la declaran `sí`.
> El rojo de E-05 salió de una mutación en el ejecutor del test, que corría el comando viejo en Git
> Bash, donde anda. El refutador la aceptó como el rojo legítimo de "la prueba distingue".

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El comando que fija la spec sale con 0 si no encuentra `run-hook.cmd`.** Lo encontró el
   builder, midiendo con `CLAUDE_PROJECT_DIR=C:\no\existe`: `$LASTEXITCODE` queda en `$null` y la
   salida vacía, que la letra de E-03 daba por buena.
   - La compuerta ahora cuenta como falla un registro de error de PowerShell (`<S S="Error">`) en
     stderr, aunque el código sea 0.
   - El refutador lo juzgó más estricto que la letra, sin contradecirla: un `.cmd` sano que escribe a
     stderr no dispara la condición, y sin ella E-03 daba verde con el lanzador ausente.

## Lo que queda abierto, anotado y no escondido

Los dos quedan en `Pendientes/Fix-Harness/PENDIENTES-FH.md`:
- **En una sesión real, el hook sigue fallando en silencio si falta `run-hook.cmd`**, porque el comando
  sale con 0. Arreglarlo cambia el comando que fija la spec.
- **No se sabe desde qué versión de Claude Code existe el campo `shell` de los hooks.**
  `requiereClaudeCode` sigue en `2.1.0`.

Además, WSL, macOS y Linux siguen sin hooks, como declara la spec en "Qué queda afuera".

## Lo que ningún test cubre y se mira con los ojos

Que Claude Code 2.1.281 respete `"shell": "powershell"`. Está documentado y no se probó en una sesión
real. Se comprueba en el Portal IGE después del `-Update`, con el procedimiento del reporte original:
1. aparece el contexto del `SessionStart`;
2. una llamada a `PowerShell` genera `PreToolUse:PowerShell` y `PostToolUse:PowerShell`;
3. un `Write` con un secreto de prueba queda denegado;
4. en la transcripción hay `hook_success` y ningún `hook_non_blocking_error`.
