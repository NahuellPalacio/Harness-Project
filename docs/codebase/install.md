# install

## Qué es

El instalador: el único punto de entrada del repo. Copia el harness dentro de otro proyecto,
lo actualiza, lo saca y diagnostica la máquina. Es un solo script de PowerShell, largo y con
comentarios que explican cada decisión.

La invariante que ordena todo lo que escribe: `.claude/` es 100% regenerable y va
gitignoreado; el `CLAUDE.md` del proyecto no lo es y se versiona. De ahí se deduce el resto —
nada de lo que escribe en `.claude/` tiene que sobrevivir a un clone, solo a un `-Update`.

Acá también viven las plantillas de lo que instala: el registro de hooks, la lista de rutas
denegadas, los dos lanzadores y los bloques de `CLAUDE.md` que se inyectan en el proyecto.

## Qué expone

- Cinco verbos por parámetro: `-Doctor` (no escribe nada), `-Project` + `-Harness` para
  instalar, `-Update`, `-Uninstall`, y `-WhatIf` heredado de `SupportsShouldProcess`.
- Instalar es **aditivo**: lo que el proyecto ya tenía se conserva y se anuncia. Los ids se
  ordenan de forma canónica para que llegar al mismo conjunto por dos caminos produzca el
  mismo archivo.
- `harness.lock.json` en el proyecto: qué versión, qué archivos y el SHA256 de cada uno. Es
  el inventario que después usan `-Doctor` y `-Uninstall`.
- `harness.config.json`: se crea **solo si no existe** y no se pisa jamás, ni en `-Update`.
  Sus valores por defecto salen del bloque `config` de cada manifiesto.
- Dos lanzadores de hooks: `run-hook.cmd`, el único artefacto instalado que contiene una ruta
  absoluta de la máquina (el `python.exe` que se resolvió), y `run-hook.sh`, genérico, para
  el caso POSIX.
- Bloques marcados dentro de archivos que también edita una persona: uno en `CLAUDE.md` y otro
  en `.gitignore`. Todo lo que está entre las marcas es del harness; el resto es intocable.
- Se puede cargar con dot-source sin ejecutar ningún verbo: es la costura que usa la suite
  para probar funciones internas sin levantar un proceso por caso.

## De qué depende

- **PowerShell 5.1** y Windows para correr. Claude Code ≥ 2.1.0 y Python ≥ 3.9 en la máquina
  de destino, verificados antes de escribir nada; si faltan, aborta en vez de reparar.
- Los **manifiestos** de `comun/` y de cada harness: de ahí saca qué copiar, el prefijo de
  namespace y los defaults de configuración. Los harness se descubren recorriendo el
  directorio, no hay ningún id registrado en el script.
- El módulo `lib/zonas.py` de `comun/hooks`, invocado como proceso: la definición de las zonas
  del `CLAUDE.md` vive en un solo lado y el instalador la lee en vez de reimplementarla. La
  llamada está adentro de las rutas de instalar y actualizar, no arriba, porque `-Doctor`
  tiene que poder diagnosticar una máquina que todavía no tiene Python.
- Los **payloads** de `tests/payloads/`: al terminar dispara los cuatro hooks instalados con
  eventos reales y, si alguno no responde bien, la instalación falla y revierte.
- La suite de `tests/` como compuerta propia.
- El `.gitattributes` del repo, que fija LF en la plantilla del shim `.sh`: un `.sh` con CRLF
  falla con un error que no menciona los saltos de línea.

## Dónde está

- `install.ps1` — todo el instalador.
- `VERSION` — la versión que sella el lockfile y los archivos generados.
- `comun/manifest.json` — el manifiesto del esqueleto que se instala siempre.
- `comun/settings/hooks.plantilla.json` — el registro de los cuatro hooks, con matchers
  estrictos a propósito.
- `comun/settings/permissions.deny.json` — las rutas sensibles que no se pueden leer.
- `comun/settings/run-hook.sh.plantilla` — el lanzador POSIX, versionado con LF fijo.
- `comun/claude-md/bloque-comun.md` — el bloque que se inyecta en el `CLAUDE.md` del proyecto.
- `comun/claude-md/plantilla-proyecto.md` — las cuatro zonas con sus marcadores y techos.
