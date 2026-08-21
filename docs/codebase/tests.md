# tests

## Qué es

La suite del repo: dos motores, un solo código de salida. Es la compuerta de todo — nada se da
por terminado sin la suite en verde, y el propio instalador la usa como compuerta suya.

No tiene dependencias: no hace falta Pester ni pytest ni nada instalado. Cada motor carga los
archivos de casos de su lenguaje y acumula resultados.

Acá vive también la evidencia: payloads reales de cada evento de hook, proyectos de fixture y
las capturas del testigo contra el que se comparó el porteo de PowerShell a Python.

## Qué expone

- **`Invoke-Tests.ps1`** — el corredor de PowerShell, con sus aserciones propias y la opción
  `-Detallado`. Sale 0 si pasa todo, 1 si falla algo.
- **`correr.py`** — el corredor de Python, mismo formato de resultados, con filtro por nombre
  de caso.
- **Casos de Python** — la librería de hooks, el contrato de `pre-tool-use` punta a punta como
  proceso hijo, el detector de secretos, la memoria de `SessionStart`, la carga de checks, los
  checks contra el testigo, los casos de borde de los checks de desarrollo, las zonas del
  `CLAUDE.md` y el aviso del índice del código.
- **Casos de PowerShell** — el encoding de los fuentes, el ciclo completo del instalador
  (`-WhatIf` → instalar → `-Doctor` → editar a mano → `-Update` → `-Uninstall`), la composición
  de dos harness en el mismo proyecto, la bitácora por versión y los escenarios del índice del
  código del lado del instalador.
- **`payloads/`** — un JSON por evento, con la forma real que manda Claude Code. Los usa la
  suite y también el instalador para verificar los hooks recién instalados.
- **`fixtures/`** — el corpus de secretos, un `CLAUDE.md` de prueba, hooks de mentira que
  responden cada una de las salidas posibles (eco, deny, preguntar, explotar, silencio, salir
  con código), un proyecto con archivos que disparan cada check, y un proyecto con índices de
  código sanos y rotos.
- **`Repair-EncodingFuentes.ps1`** — el arreglo del problema que detecta el caso de encoding.
  A un `.ps1` con caracteres no ASCII le agrega el BOM, porque PowerShell 5.1 sin BOM lee en la
  codepage ANSI; a un `.py` con BOM se lo saca, porque Python siempre lee UTF-8 y ahí el BOM
  sobra.

## De qué depende

- PowerShell 5.1 y Python 3.9+ en la máquina.
- El código que prueba: `comun/hooks/`, los checks, `install.ps1` y los manifiestos.
- Los casos del instalador escriben sobre un proyecto descartable, pero **dos de ellos rompen
  archivos versionados a propósito** y los restauran en un `finally` que no sobrevive a que
  maten el proceso. Si la suite se corta a la mitad, hay que revisar el árbol antes que nada:
  ya dejó el hook de bloqueo de secretos roto en el árbol durante una versión.
- **`generar-testigo.ps1`** importa cuatro módulos de PowerShell que ya no existen en el repo:
  la implementación que capturaba se portó a Python. Es un script de una sola corrida y su
  propia cabecera dice que volver a correrlo después de portar no tiene sentido. Se queda como
  registro de cómo se produjeron los tres archivos de paridad, pero hoy no se puede ejecutar.

## Dónde está

- `tests/Invoke-Tests.ps1`, `tests/correr.py` — los dos corredores.
- `tests/casos/` — quince archivos de casos, nueve en Python y seis en PowerShell.
- `tests/payloads/` — seis eventos reales.
- `tests/fixtures/` — corpus, hooks de mentira, proyectos de prueba y las tres capturas de
  paridad (`paridad-secretos.json`, `paridad-checks.json`, `paridad-zonas.json`).
- `tests/generar-testigo.ps1` — el generador del testigo, hoy inejecutable.
- `scripts/Repair-EncodingFuentes.ps1` — el arreglo de encoding, fuera de `tests/` pero
  emparejado con el caso que lo detecta.
