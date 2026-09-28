# Instalador — sin consola para preguntar, aborta pidiendo `-Usuario`, también con `-NonInteractive`

**Estado:** especificado · **Fecha:** 28-09-2026

## Qué problema resuelve

El 28-09-2026, al cerrar 0.25.0, el usuario corrió `.\tests\Invoke-Tests.ps1` desde su propia
terminal de PowerShell. El motor PowerShell dio `465/467`. El mismo árbol, corrido con stdin
redirigido, dio `36881/36881`. Los dos fallos venían del lugar donde se corrió la compuerta:

1. **El instalador no reconoce `-NonInteractive`.** Para decidir si no hay a quién preguntarle el
   nombre, `Get-Usuario` (`install.ps1`, cerca de la línea 721) mira solo
   `[Console]::IsInputRedirected`. El caso de `03-instalador.ps1` lanza
   `powershell.exe -NoProfile -NonInteractive -File install.ps1` sin `-Usuario`. Desde una consola
   real, el hijo hereda la consola como stdin. Entonces `IsInputRedirected` da falso, el
   instalador llega a `Read-Host`, y `-NonInteractive` lo hace fallar con el mensaje propio de
   PowerShell:

   ```
   Windows PowerShell se encuentra en modo no interactivo. Las funciones de lectura y
   confirmación no están disponibles.
   ```

   La instalación aborta con código 1 y no deja nada a medias, pero el mensaje no dice que falta
   `-Usuario`. Le pasa igual a cualquiera que corra el instalador con `-NonInteractive` desde un
   script, no solo al test.

2. **E-17 revisa archivos que la fábrica no tiene.** El grupo
   `Composicion - la definicion de zonas vive en un solo lado (E-17)`, en `03-instalador.ps1`,
   recorre con `Get-ChildItem -Recurse` todo `*.py`, `*.ps1` y `*.psm1` bajo la raíz, esté
   trackeado o no. Esa vez encontró una copia de `comun\hooks\lib\zonas.py` en una carpeta
   `..Harness-release-024` dentro del árbol. Cuando se fue a mirar, la carpeta ya no estaba, así
   que no quedó registrado qué la creó.

🔴 El costo no es el rojo en sí. Una compuerta que da rojo por una razón que nadie arregla enseña a
dejar de leerla.

## Qué queda afuera

- **Preguntar el nombre de otra forma**, con una ventana o una variable de entorno. El contrato
  sigue igual: `-Usuario`, o el nombre ya configurado, o la pregunta en una consola de verdad.
- **Los tests del instalador que fallan al azar bajo carga** (*The installer tests fail at random
  under load*). Son otra causa, y ya tienen su propio pendiente.
- **Los dos tests del instalador que rompen archivos versionados** (ítem 1 de PENDIENTES-FH). Es
  otro cambio, y más grande.
- **Otros `Read-Host` o confirmaciones de `install.ps1`, si los hay.** Este cambio cubre solo la
  pregunta del nombre, que es la que rompió. Si aparece otro caso, se anota.

## Las decisiones, y por qué

### Se ataja la falla de `Read-Host`, no se adivina el modo

Otra opción era buscar `-NonInteractive` en `[Environment]::GetCommandLineArgs()`. Se descartó
porque cubre un solo motivo por el que `Read-Host` no puede correr, y hay otros: hosts sin UI o
consolas que no son de verdad. Atajar la falla cubre a todos con la misma regla: si no se pudo
preguntar, se aborta con el mismo mensaje que da la rama de stdin redirigido.

### E-17 mira lo que la fábrica versiona

La afirmación de E-17 es que la definición vive en un solo lugar de la fábrica. Lo que no está en
`git ls-files` no es la fábrica: una copia de release, un worktree o un resto de un ensayo no la
contradicen. Si el árbol no es un repo de git, el test lo dice y falla. No vuelve en silencio al
recorrido entero, porque así volvería a medir otra cosa.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `install.ps1`, `Get-Usuario` | Si `Read-Host` no puede correr, aborta con el mismo `falta -Usuario …` que la rama de stdin redirigido |
| `tests/casos/03-instalador.ps1` | Un caso nuevo que reproduce stdin de consola con `-NonInteractive`, y E-17 restringido a `git ls-files` |

## Escenarios verificables

### El nombre, sin nadie a quien preguntarle

- **E-01** — Con `-NonInteractive`, sin `-Usuario`, sin nombre configurado y con stdin que **no**
  está redirigido (una consola propia del proceso hijo), el instalador sale con código 1 y su
  salida contiene `-Usuario`. · rojo visto: no consta
- **E-02** — En el mismo caso, la salida no contiene el mensaje de PowerShell sobre el modo no
  interactivo: el error que ve la persona es el del harness. · rojo visto: no consta
- **E-03** — En el mismo caso, el proyecto no queda a medio instalar: no existe
  `.claude\harness.lock.json`. · rojo visto: no consta
- **E-04** — Con stdin redirigido y sin `-Usuario`, el comportamiento de hoy no cambia: sale con
  código 1 y la salida contiene `-Usuario`. · rojo visto: no consta
- **E-05** — Con `-Usuario`, o con el nombre ya configurado en `harness.config.json`, no se
  pregunta nada y la instalación sigue, con o sin `-NonInteractive`. · rojo visto: no consta

### La compuerta no depende de dónde se corre

- **E-06** — Un `.py` fuera de `git ls-files` que contiene la definición de una zona (una copia de
  `zonas.py` en una carpeta sin trackear) no hace fallar E-17. · rojo visto: no consta
- **E-07** — Un archivo trackeado fuera de `comun\hooks\lib\zonas.py` que contiene la definición sí
  hace fallar E-17, y la salida lo nombra. · rojo visto: no consta

## Cómo se verifica

Todo va por la suite, y ningún escenario es sobre la corrida de un modelo. E-01 a E-03 necesitan un
proceso hijo con una consola propia: un stdin heredado de la compuerta ya viene redirigido y no
reproduce el caso. El test tiene que asegurarse de que, en su entrada, `IsInputRedirected` del hijo
da falso. Si no, el test no prueba nada, y eso se afirma aparte. E-06 y E-07 se prueban con un
archivo temporal dentro del árbol, que se borra en un `finally`.

## Riesgos conocidos

- **Abrir una consola propia puede mostrar una ventana**, o comportarse distinto en un agente sin
  sesión de escritorio. Si no se puede ocultar, el caso tiene que decirlo en vez de saltearse en
  silencio.
- **E-06 y E-07 escriben dentro del árbol.** Si la compuerta muere a mitad de la corrida, el
  archivo temporal queda. Es el mismo riesgo que el ítem 1 de PENDIENTES-FH, y el nombre del
  archivo tiene que dejar claro que se puede borrar.
