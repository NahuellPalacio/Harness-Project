# Verificación — hooks, checks y tests en Python

**Estado:** cerrado · **Fecha:** 17-08-2026 · **Versión:** 0.13.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los emitió
`harness-spec-refuter` a lo largo de las catorce tareas, corriendo los tests en cada caso —sin
ejecutarlos no emite veredicto— y `harness-hook-engineer` aportó las revisiones de calidad.

**Resultado: 30 escenarios sostenidos, 1 contradicho.** El contradicho es E-29 y está explicado
abajo, con su número.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Mismo veredicto que PowerShell, caso por caso | sostenido | sí, específico | `04_secretos.py`, 33 casos del testigo |
| E-02 | Las 27 regex del catálogo compilan bajo `re` | sostenido | no consta | `04_secretos.py`, sobre el catálogo real |
| E-03 | Confianza alta → `deny`; media → `ask` | sostenido | sí, las dos mitades | `02_hook_contrato.py` |
| E-04 | Un placeholder no dispara | sostenido | sí | `02_hook_contrato.py`, atado al código de salida |
| E-05 | Un secreto entre backticks no dispara | sostenido | no consta | `04_secretos.py` |
| E-06 | Los cuatro hooks salen 0 siempre | sostenido | sí, de módulo | `01_hook_lib.py` |
| E-07 | Un hook que explota avisa una vez y sale 0 | sostenido | sí | `01_hook_lib.py` |
| E-08 | No vuelve a avisar con el mismo `session_id` | sostenido | sí | `01_hook_lib.py`, probado con marca plantada |
| E-09 | `campo()` devuelve el default sin explotar | sostenido | sí, específico | `01_hook_lib.py` |
| E-10 | Un aviso con tildes llega íntegro | sostenido | sí, específico | `01_hook_lib.py`, con `PYTHONIOENCODING=cp1252` |
| E-11 | Un stdin con BOM se parsea igual | sostenido | sí, de módulo | `01_hook_lib.py` |
| E-12 | Silencio es silencio | sostenido | sí | `01_hook_lib.py` y `05_memoria.py`, los cuatro hooks |
| E-13 | Un `.py` nuevo en el directorio se descubre | sostenido | sí, de módulo | `06_reglas.py` |
| E-14 | Un check roto se saltea y los demás corren | sostenido | sí, de módulo | `06_reglas.py`, con el orden fijado |
| E-15 | El tope de 8 hallazgos se respeta | sostenido | sí, específico | `06_reglas.py` |
| E-16 | Los cinco checks producen los mismos hallazgos | sostenido | sí, específico | `07_checks.py`, 11 hallazgos texto a texto |
| E-17 | La definición de zonas vive en un solo lado | sostenido | sí | `03-instalador.ps1` |
| E-18 | `install.ps1` lee las zonas invocando `zonas.py` | sostenido | no consta | `09_zonas.py` + ciclo completo del instalador |
| E-19 | Mismas mediciones y mismos excesos de techo | sostenido | sí, específico | `09_zonas.py` (mediciones) + `07_checks.py` (excesos) |
| E-20 | Si `zonas.py` falla, no instala un `CLAUDE.md` a medias | sostenido | sí | `03-instalador.ps1` |
| E-21 | El shim fija el `python.exe` real | sostenido | no consta | `03-instalador.ps1`, verificado en instalación real |
| E-22 | `run-hook.sh` con LF, sin conversión | sostenido | no consta | `03-instalador.ps1`, 0 bytes `\r` |
| E-23 | `-Doctor` reporta aunque no haya Python | sostenido | no consta | `03-instalador.ps1`, con el PATH roto |
| E-23b | Nada de Python en el nivel superior | sostenido | sí, específico | `03-instalador.ps1` |
| E-24 | `-Doctor` falla si el Python es anterior al mínimo | sostenido | sí, específico | `03-instalador.ps1` |
| E-25 | Tras `-Update` no quedan `.ps1` huérfanos | sostenido | sí | `03-instalador.ps1` |
| E-25b | `-Doctor` mide el p50 y avisa, sin bloquear | sostenido | sí, específico | `03-instalador.ps1` |
| E-26 | `-Uninstall` saca lo suyo y deja config y backups | sostenido | sí | `03-instalador.ps1`, con y sin Python |
| E-27 | La compuerta: si los hooks fallan, revierte | sostenido | sí | `03-instalador.ps1` |
| E-28 | Ningún `.py` con BOM; los `.ps1` lo siguen exigiendo | sostenido | no consta | `00-encoding-fuentes.ps1` |
| E-29 | El p50 de `pre-tool-use` por debajo de 400 ms | **contradicho** | sí, medido | medición manual y `-Doctor` |

📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide ADR-0006:
un test que nunca se vio fallar no probó que puede fallar. Donde dice "de módulo", el rojo fue la
ausencia del archivo entero, no una rotura dirigida al escenario.

## E-29, el escenario contradicho

```
PowerShell, pre-tool-use punta a punta      981 ms   (medido el 15-08-2026)
Python,     pre-tool-use punta a punta      558 ms   (p50, 14 corridas, Stopwatch)
umbral que fijó el plan original            400 ms

descomposición:
    spawn puro (cmd /c exit)                 82 ms
    python -c "pass"                        387 ms   <- el piso del intérprete, solo
    python -c "import json,re"              503 ms
    el hook completo                        558 ms
```

Medido tres veces por tres partes distintas —el implementador, el controlador y el refutador— con
resultados entre 481 y 793 ms según la carga de la máquina. **La causa no es el port:** el arranque
desnudo del intérprete ya se come el umbral, así que ni llevando a cero el código del hook se
llegaría por debajo de 400 ms. La mejora real es 981 → 558 ms, un 43%.

**Decisión tomada:** el escenario queda contradicho y a la vista, no se baja el umbral para que dé
bien. Un umbral que se acomoda al resultado deja de medir. `-Doctor` pasa a reportar el p50 en cada
corrida y avisa si pasa los 400 ms, sin bloquear nunca (E-25b), que es lo que convierte esto en algo
vigilado en vez de una medición que nadie repite.

## Lo que la verificación encontró y no habría encontrado un test verde

Tres hallazgos que ninguna suite en verde mostraba, y que son la razón por la que quien verifica no
es quien construyó:

1. **Un falso positivo que bloqueaba código legítimo.** `-match` de PowerShell es case-insensitive
   siempre y `re.search` no. El patrón de ignorar `\$env:` era el único de los quince sin `(?i)`,
   así que `password = $Env:DB_PASSWORD` no disparaba en PowerShell y disparaba `deny` en Python.
   El caso entró al testigo y el arreglo es estructural, no un parche al patrón.
2. **Un `-Update` que podía dejar el proyecto sin harness.** El borrado de `.claude\harness\`
   quedaba antes de la reinstalación, y si esa reinstalación fallaba, el directorio y las ediciones
   humanas se perdían. Ahora se mueve a un temporal y se restaura si algo falla.
3. **33 aserciones de casos borde que un borrado se llevó sin reemplazo** — los falsos positivos que
   cada check tiene que evitar. Se repusieron desde la historia de git.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`: los cuatro arreglos de contrato que viajaron adentro
del port y deben su revisión propia; las cuatro divergencias menores; las 25 ramas de los checks que
ningún testigo ejercitó, listadas el día antes de borrar los originales; y los dos tests que rompen
archivos versionados y los restauran en un `finally` que no sobrevive a que maten el proceso.

## Lo que ningún test cubre y se mira con los ojos

Abrir una sesión de Claude Code real en un proyecto con el harness instalado y comprobar que el
saludo aparece, que un secreto se bloquea y que un aviso con tildes llega con las tildes puestas.
La suite verifica los hooks contra payloads; que Claude Code los invoque bien es otra cosa.
