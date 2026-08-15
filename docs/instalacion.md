# Instalación

Paso a paso para dejar el harness andando en un proyecto, por PowerShell y por bash.

Las dos vías corren **el mismo** `install.ps1`. No hay dos instaladores: hay un instalador y
dos formas de invocarlo. Lo que cambia es la sintaxis de la línea de comandos, nada más.

## Antes de empezar

| | Mínimo | Cómo lo verificás |
|---|---|---|
| Windows | 10 u 11 | — |
| PowerShell | 5.1 (el que ya trae Windows) | `$PSVersionTable.PSVersion` |
| Claude Code | 2.1.0 | `claude --version` |
| Git | cualquiera | `git --version` |

> 🔴 **Hoy el harness es de Windows.** Los hooks se lanzan desde un `run-hook.cmd` que apunta
> a `powershell.exe`. Eso significa que **el harness se instala y corre en Windows**, y que
> desde WSL, macOS o Linux los hooks no arrancan. Falta el shim `.sh` — está anotado en
> `Pendientes/Fix-Harness/PENDIENTES-FH.md`. Cuando este documento dice "bash" quiere decir
> **Git Bash sobre Windows**, que es lo que hoy funciona de verdad.

No hace falta instalar PowerShell 7. No hace falta ser administrador.

## 1. Traer el harness

```bash
git clone https://github.com/NahuellPalacio/Harness-Project.git C:/Work/gcba-harness
```

La ruta destino es tuya: el harness no depende de dónde esté. Poné la que quieras.

> ⚠️ **Cloná, no bajes el ZIP.** Windows le pone *Mark-of-the-Web* a todo archivo bajado de
> internet, y la política de ejecución por defecto (`RemoteSigned`) bloquea los `.ps1`
> marcados. El síntoma es un error de permisos que no menciona en ningún momento la causa
> real, y se pierde media tarde. `-Doctor` lo detecta y te lo dice; si igual bajaste el ZIP,
> se arregla con `Get-ChildItem -Recurse | Unblock-File`.

## 2. Instalar — vía PowerShell

Tres pasos. Los dos primeros no escriben nada.

```powershell
cd C:\Work\gcba-harness

# 1. ¿Está la máquina en condiciones? No escribe nada.
.\install.ps1 -Doctor

# 2. ¿Qué va a escribir, exactamente? Tampoco escribe nada.
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis -WhatIf

# 3. Instalar.
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis -Usuario "Tu Nombre"
```

Si te salta `no se puede cargar el archivo ... install.ps1`, es la política de ejecución de
tu sesión. Se levanta para esa consola sola, sin tocar nada de la máquina:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Instalar — vía bash

Los mismos tres pasos, invocando el instalador a través de `powershell.exe`. Andá al directorio
del harness y corré:

```bash
cd /c/Work/gcba-harness

# 1. Revisar la máquina.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install.ps1 -Doctor

# 2. Ver qué va a escribir.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install.ps1 \
  -Project 'C:/Work/GCBA/MiProyecto' -Harness analisis -WhatIf

# 3. Instalar.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install.ps1 \
  -Project 'C:/Work/GCBA/MiProyecto' -Harness analisis -Usuario 'Tu Nombre'
```

Cuatro detalles que sí importan en esta vía:

**La ruta del proyecto va en formato Windows.** `-Project /c/Work/GCBA/MiProyecto` no sirve:
quien lee ese argumento es PowerShell, no bash. Usá `C:/Work/GCBA/MiProyecto` — PowerShell
acepta la barra normal, así que no hace falta pelearse con las contrabarras y el escapado.

**`-Usuario` es obligatorio acá.** Cuando el instalador no tiene consola para preguntar tu
nombre, aborta explicando en vez de inventar un default. Por parámetro, no hay problema.

**`-NoProfile` no es un lujo.** Si tu perfil de PowerShell imprime algo, ese texto se mezcla
con la salida y ensucia el diagnóstico.

**Los dos harness juntos se pasan igual:** `-Harness analisis,desarrollo`. Invocado con
`-File` eso llega como una sola cadena literal, y el instalador la parte él mismo. Las dos
vías se comportan igual.

## 4. Comprobar que quedó

```powershell
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Doctor
```

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install.ps1 \
  -Project 'C:/Work/GCBA/MiProyecto' -Doctor
```

Te dice qué harness rige, en qué versión está, si el proyecto está bajo control de versiones y
qué archivos del harness fueron editados a mano. Abrí Claude Code en el proyecto: si en el
saludo aparece tu nombre y el estado del repo, está andando.

## 5. Qué escribió en tu proyecto

```
MiProyecto/
├── CLAUDE.md              # se le inyecta un bloque marcado; el resto no se toca
├── .gitignore             # se le agrega un bloque de secretos
└── .claude/
    ├── settings.json      # permisos + registro de hooks     ─┐
    ├── harness/           # los hooks, skills, agentes         │ todo esto es
    ├── harness.lock.json  # qué versión, qué archivos, SHA256  │ regenerable
    ├── harness.config.json# tus ajustes — nunca se pisan       │ y va gitignoreado
    └── .harness-backup/   # copia de todo lo que se pisó      ─┘
```

La regla que ordena todo: **`.claude/` es 100% regenerable y va gitignoreado; `CLAUDE.md` no
lo es y se versiona.** Si algo se rompe, borrás `.claude/` y reinstalás.

`normativa/` **no** se copia nunca a un proyecto: es insumo de autoría del harness, se
referencia desde el repo.

## 6. Actualizar y desinstalar

```powershell
cd C:\Work\gcba-harness
git pull

.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Update      # traer cambios del harness
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Uninstall   # sacarlo, sin dejar rastro
```

Por bash, lo mismo con el prefijo `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
./install.ps1`.

`-Update` **nunca pisa un archivo que hayas editado a mano**: escribe la versión nueva al lado,
con extensión `.nuevo`, y te avisa al final. `harness.config.json` no se toca jamás.

Para migrar entre versiones con cambios que rompen, mirá [UPGRADE.md](../UPGRADE.md).

## 7. Sumar el segundo harness

Instalar es **aditivo**: lo que el proyecto ya tenía se conserva, y el instalador lo anuncia.

```powershell
.\install.ps1 -Project ... -Harness analisis,desarrollo   # los dos de una
.\install.ps1 -Project ... -Harness desarrollo            # sumar el segundo más tarde
```

Para quedarte con un conjunto exacto, el camino es `-Uninstall` y volver a instalar.

## Cuando algo falla

| Síntoma | Causa | Salida |
|---|---|---|
| `no se puede cargar el archivo install.ps1` | ExecutionPolicy de la sesión | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, o invocar con `-ExecutionPolicy Bypass` |
| `-Doctor` avisa de Mark-of-the-Web | Bajaste el ZIP en vez de clonar | `Get-ChildItem -Recurse \| Unblock-File`, o clonar de nuevo |
| `-Doctor` falla con `ExecutionPolicy de máquina = AllSigned` | GPO del organismo | No hay vuelta por tu cuenta: los hooks no van a poder ejecutarse. Va por Sistemas |
| `no se pudo determinar la versión de Claude Code` | `claude` no está en el PATH | Abrí una consola nueva después de instalarlo |
| `falta -Usuario` | Invocado sin consola interactiva | Pasá `-Usuario 'Tu Nombre'` |
| `el proyecto no existe` | Ruta en formato bash (`/c/...`) | Pasala en formato Windows: `C:/Work/...` |
| Los hooks no hacen nada | Estás en WSL, macOS o Linux | Todavía no está soportado: falta el shim `.sh` |
| Acentos rotos en la salida | Consola en codepage vieja | `chcp 65001` antes de correr |

Si `-Doctor` cierra con `Todo en orden.` y aun así algo no anda, eso es un bug del harness:
va a `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
