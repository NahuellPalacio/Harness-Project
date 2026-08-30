# Proyecto

_(Lo escribe `dev-iniciador-code`. Lo lee `contexto-armar.py` para armar
`project-context.json`. No es una ficha de módulo: no va en el índice.)_

## Qué es el proyecto

La fábrica del harness del GCBA. Produce, versiona y reparte el harness de Claude Code que después
se instala sobre los proyectos: los cuatro hooks, los checks, las skills y los agentes de cada
harness. Cada versión que sale de acá hay que volver a instalarla donde el harness ya está en uso.

- Tipo: cli
- Etapa: production

## Stack

- Lenguajes: Python, PowerShell
- Frameworks: —
- Runtimes: Python 3.9 o mayor, Windows PowerShell 5.1
- Gestores de paquetes: —

## Cómo se levanta

- `.\install.ps1 -Project <ruta> -Harness desarrollo`
- `.\install.ps1 -Project <ruta> -Update`
- `.\install.ps1 -Project <ruta> -Doctor`
- Entrypoints: `install.ps1`, `comun/hooks/session-start.py`, `comun/hooks/pre-tool-use.py`, `comun/hooks/post-tool-use.py`, `comun/hooks/user-prompt-submit.py`
- Integraciones: —

## Cómo se testea

- `.\tests\Invoke-Tests.ps1`
- `python tests/correr.py`

## Interfaces

Este repositorio no expone ninguna interfaz remota: no hay servidor HTTP, ni GraphQL, ni
eventos, ni webhooks. `install.ps1` se invoca desde la línea de comandos y los hooks se
disparan como procesos que Claude Code lanza localmente; nada de esto se consulta por red.

## Identidad y acceso

Este repositorio no tiene login, sesiones ni roles de aplicación: es una herramienta de línea
de comandos que corre con los permisos del usuario que la invoca. No hay usuarios de prueba ni
modelo de autenticación que declarar.

## Ambientes

| id | tipo | urls | mutaciones | datos |
|---|---|---|---|---|
| fabrica | local | - | read-write | código, tests y documentación de este repositorio: donde se construye y se versiona el harness |
| proyecto-instalado | other | - | read-write | el repositorio ajeno que recibe `-Project`; fuera de este repositorio, no observable desde acá |

## Qué falta saber

- Si `docs/codebase/` sigue cubriendo todos los módulos: el índice se regenera entero y este archivo no lo verifica.
- El costo en milisegundos de los checks sobre un repositorio grande no está medido.
