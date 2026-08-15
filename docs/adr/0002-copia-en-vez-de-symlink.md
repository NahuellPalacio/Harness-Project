---
estado: aceptada
creado: 2026-08-05
---

# ADR-0002 — El instalador copia archivos, no los enlaza

## Contexto

`install.ps1` tiene que llevar el contenido del harness al directorio `.claude/` de cada
proyecto. Hay tres mecanismos posibles en Windows, y la elección determina cómo se propaga
una actualización y qué puede salir mal.

El contexto que condiciona todo: son **máquinas de un organismo público**, con políticas de
grupo que no controlamos y que varían entre equipos.

## Decisión

**Se copian los archivos.**

| Mecanismo | A favor | En contra |
|---|---|---|
| **Symlink** (`New-Item -ItemType SymbolicLink`) | Un `git pull` actualiza los 12 proyectos de una. Cero deriva | **Requiere privilegios de administrador o Modo Desarrollador activado.** En una máquina con GPO ninguno de los dos es apostable. Y falla en tiempo de instalación, que es el peor momento: le pasa al usuario que menos sabe diagnosticarlo |
| **Junction** (`-ItemType Junction`) | No requiere elevación ni Modo Desarrollador — el matiz que casi todos se pierden. Igual de instantáneo | **Git camina adentro del junction y versiona su contenido**, a diferencia del symlink. Un `git add .` en un repo con harness enlazado se traga el harness entero. OneDrive hace lo mismo con la sincronización |
| **Copia** | Funciona siempre: sin privilegios, sin GPO, sin sorpresas con git. Cada proyecto es autocontenido y auditable — se ve exactamente qué reglas rigen ahí | Deriva entre proyectos: uno puede quedar en una versión vieja del harness |

La contra de la copia es real, pero es **la única de las tres que se puede convertir en un
problema detectable**. `harness.lock.json` guarda el SHA256 de cada archivo instalado y la
versión del harness; `-Doctor` compara contra el repo y avisa *"este proyecto está en 1.1.0,
el repo está en 1.3.0"*.

Una deriva visible es un problema resuelto. Un junction versionado por accidente es un
incidente que alguien descubre tres commits después.

## Consecuencias

**A favor:**
- El instalador no puede fallar por permisos del sistema operativo.
- Cada proyecto es inspeccionable por sí solo: abrir `.claude/harness/` muestra las reglas
  que efectivamente rigen ahí, no un puntero a otro lado.
- Desinstalar es borrar archivos, sin dejar enlaces colgados.

**En contra:**
- Actualizar N proyectos son N invocaciones de `-Update`. No hay propagación automática.
- El harness ocupa espacio en disco una vez por proyecto. Es de kilobytes, pero es real — y
  por eso `normativa/` (los PDF, 11 MB) **nunca se copia**: se referencia desde el repo.

**Riesgo residual:** que alguien "optimice" reemplazando la copia por un junction y git se
coma el harness. `-Doctor` detecta reparse points bajo `.claude/` y lo avisa.

## Revisión

Se revisa si aparece un mecanismo de distribución nativo que evite el problema — por ejemplo
si el harness se empaqueta como plugin de Claude Code, que resuelve la propagación sin tocar
el filesystem del proyecto. Esa vía se evaluó y se descartó para la v1 por preferir control
explícito sobre qué se instala dónde, pero no está cerrada.
