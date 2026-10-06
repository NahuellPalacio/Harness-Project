# Flow Governance — Qualification Gate 1: tests del instalador que no rompen el árbol, y `-NonInteractive` en una consola de verdad

**Estado:** cerrado: construido, refutado (dos pasadas, sin contradichos) y aceptado por la persona. **Qualification Gate 1: CLOSED** (Q1 y Q2 CLOSED) · **Fecha:** 06-10-2026 ·
**Base:** `05fefcdf160c2149c4f6732f22aa0807c4bf3dd0`, `VERSION 0.28.0` · **Rama:**
`integration/flow-governance-0.28`

No es una Wave. No agrega funcionalidad ni cambia la semántica cerrada de Flow Governance, no
cambia `VERSION` y no califica nada. Cierra los dos impedimentos que `qualification-readiness.md`
nombra en «Lo que todavía impide calificar» y que `Pendientes/Fix-Harness/PENDIENTES-FH.md` pone
primero y segundo en «What to take first».

## Qué problema resuelve

### Q1 — Los tests del instalador rompen archivos versionados

`PENDIENTES-FH.md`, ítem 1 y la entrada *«Two installer tests break versioned files, and `finally`
does not survive a killed process»*:

> `tests/casos/03-instalador.ps1` covers E-20 and E-27 by appending a syntax error to a real,
> versioned file — `comun/hooks/lib/zonas.py` for one, `comun/hooks/pre-tool-use.py` for the other —
> running the installer against it, and restoring the file in a `finally`.

| | E-20 | E-27 |
|---|---|---|
| Archivo | `comun/hooks/lib/zonas.py` | `comun/hooks/pre-tool-use.py` |
| Rotura | se le agrega `\ndef (((\n` | igual |
| Restauración | `WriteAllBytes` de los bytes leídos antes, en un `finally` | igual |
| Ventana | desde el `AppendAllText` hasta el `finally`: lo que tarda una instalación que aborta | igual, más la compuerta de hooks |
| Si se mata el proceso | el `finally` no corre y el archivo queda roto **en el árbol** | igual: queda roto el hook de la única regla que bloquea |
| Si corren dos compuertas a la vez | una lee como «original» la copia rota de la otra y la restaura rota | igual |

Una corrida matada contamina las siguientes: E-20 lee el archivo ya roto como original y lo
«restaura» roto, y su aserción de bytes iguales pasa.

### Q2 — `-NonInteractive` en una consola

`PENDIENTES-FH.md`, ítem 2 y la entrada *«The installer misses `-NonInteractive` when stdin is a
console, and the gate goes red»*, especificada el 28-09-2026 en
`docs/cambios/instalador-sin-consola/spec.md` (E-01 a E-05) y no construida.

`Resolve-Usuario` (`install.ps1`; la entrada dice `Get-Usuario`, el nombre real es este) decidía que
no había a quién preguntar solo por `[Console]::IsInputRedirected`. Con `powershell.exe
-NonInteractive` y la consola como stdin, llegaba a `Read-Host`, PowerShell tiraba su propio
mensaje y el error no nombraba `-Usuario`. La compuerta corrida desde la terminal de la persona daba
rojo por eso.

## La reproducción, antes de tocar nada

Todo sobre un `git clone` descartable de `05fefcd`; el árbol fuente no se mató ni se escribió.

**Q1.** `.\tests\Invoke-Tests.ps1` del clon, como proceso hijo; un observador espera a que el
archivo tenga `def (((` y mata el árbol de procesos con `taskkill /T /F`.

```text
objetivo: comun\hooks\lib\zonas.py  sha256 antes: 9812CC62…D832F
ventana vista en: …\sandbox-20224da8\comun\hooks\lib\zonas.py  (t=61s)
proceso de la compuerta matado (taskkill /T /F), exit=1
sha256 despues: C40988DB…1879  igual=False
git status --porcelain (sandbox):
 M comun/hooks/lib/zonas.py
cola del objetivo:  | def (((
py_compile: SyntaxError: invalid syntax
restos nuevos en %TEMP%: …\harness-zonasrotas-d164b128
```

```text
objetivo: comun\hooks\pre-tool-use.py  sha256 antes: DAB08EC4…40E1D
ventana vista en: …\sandbox-a01eaad1\comun\hooks\pre-tool-use.py  (t=71s)
sha256 despues: D9BBFF88…B66B  igual=False
git status --porcelain (sandbox):
 M comun/hooks/pre-tool-use.py
py_compile: SyntaxError: invalid syntax
```

**Q2.** Un envoltorio con consola propia, oculta (`Start-Process -WindowStyle Hidden`), corre
`powershell.exe -NoProfile -NonInteractive -File install.ps1 -Project <vacío> -Harness analisis`,
que hereda esa consola como stdin.

```text
StdinRedirigidoHijo : False
Codigo              : 1
.claude             : no se creó
Salida              : …El harness te va a tratar por tu nombre.
                      Windows PowerShell se encuentra en modo no interactivo. Las funciones de
                      lectura y confirmación no están disponibles.
```

No se colgaba: con `-NonInteractive`, `Read-Host` falla enseguida. El defecto era el mensaje.
Con `-Confirm` pasaba lo mismo por `ShouldProcess`: no instalaba, pero el error era
`Excepción al llamar a "ShouldProcess"…`.

## Qué queda afuera

- **E-06 y E-07 de `instalador-sin-consola`** (E-17 restringido a `git ls-files`). Es la otra mitad
  de aquella spec, de la familia «la compuerta depende de dónde corre», pero no es `-NonInteractive`
  ni un archivo versionado roto, y escribiría un archivo temporal dentro del árbol, que es la clase
  de riesgo que Q1 saca. Sigue en `PENDIENTES-FH.md`.
- **Los demos del temporal** (`harness-test-*`, `harness-zonasrotas-*`, …) que deja una corrida
  matada. Están fuera del árbol, con un nombre único por corrida: no invalidan la siguiente.
  NON_BLOCKING.
- **Una ejecución interactiva sin `-NonInteractive` y sin nadie delante** (una tarea programada que
  hereda una consola). Ahí `Read-Host` espera, que es el contrato interactivo; el instalador no
  puede distinguir eso de una persona que tarda en contestar.
- **Preguntar el nombre de otra forma**, por la misma razón que en `instalador-sin-consola`.

## El contrato

### Q1

| Caso | Qué pasa | Cubierto |
|---|---|---|
| A. Una aserción que falla, una excepción, un `exit` dentro del test | El `finally` borra la copia; la excepción y el código de salida salen tal cual | Sí |
| B. El proceso muere de golpe (`Stop-Process -Force`, `taskkill /F`, un watchdog, el timeout de un CI) | El árbol no se escribió nunca: queda igual byte a byte. La copia queda en `%TEMP%` y la próxima corrida la barre, porque su dueño ya no existe | Sí, para el árbol. La copia huérfana vive hasta la corrida siguiente |
| C. Se corta la luz o se cuelga la máquina | El árbol no se escribe, así que tampoco ahí lo rompe este test. Una copia a medio escribir en `%TEMP%` se barre igual que en B | Lo que no escribe no se puede romper; no hay más garantía que esa |
| Dos compuertas a la vez | Cada una rompe su propia copia, y el barrido de una no toca la copia de la otra mientras vive (E-05, E-05b) | Por construcción; ningún escenario corre dos compuertas a la vez |

El dueño de una copia es el par pid + arranque del proceso, escrito en `.fabrica-aislada.json` antes
de copiar nada. El barrido no toca una copia con el dueño vivo ni una carpeta sin esa marca. Un
proceso que existe y no deja leer su arranque (otro nivel de elevación) cuenta como vivo.

### Q2

| Modo | Comportamiento |
|---|---|
| Consola interactiva, sin `-NonInteractive` | Pregunta el nombre si falta, y confirma si se pidió `-Confirm`. Como siempre |
| `powershell.exe -NonInteractive`, con consola o sin ella | Nunca espera una respuesta. Si hace falta el nombre: sale 1 con `falta -Usuario …`. Si se pidió `-Confirm`: sale 1 con «`-Confirm` pide una confirmación y no hay consola para darla. No se hizo nada.» |
| stdin redirigido o cerrado | Igual que `-NonInteractive` |
| Con `-Usuario` (o el nombre ya configurado) y sin `-Confirm` | No pregunta nada: instala, actualiza o desinstala |

`install.ps1` no tiene un parámetro propio llamado `-NonInteractive`: el único es el de
`powershell.exe`. Los parámetros comunes que pueden preguntar son `-Confirm` (por `ShouldProcess`)
y `-WhatIf`, que no pregunta.

🔴 **NONINTERACTIVE != AUTO_APPROVE.** Una confirmación pedida y que nadie puede dar es un error que
no hace nada, nunca un sí. Lo afirma E-12 y lo rompen a propósito M03 y M03b.

📌 La protección tiene dos capas, y conviene saberlo para leer M03. `-Confirm` baja
`ConfirmPreference` para todo el script: cada cmdlet que escribe (`New-Item`, `Copy-Item`,
`Remove-Item`) también pregunta. Si `Confirm-Operacion` devolviera un sí (M03), el primer cmdlet
igual fallaría sin escribir nada: E-12 lo ve solo por el mensaje. Si además se aprobara todo
(M03b, `ConfirmPreference = None`), se instalaría: E-12 lo ve por el código, por el proyecto escrito
y por el mensaje. Las escrituras con .NET (`[IO.File]::WriteAllText`) no pasan por esa segunda capa;
en las tres operaciones van después de `Confirm-Operacion`.

Los demás puntos donde el instalador lanza un proceso hijo (`zonas.py`, la compuerta de hooks, la
barra, `bienvenida.py`, `medir_barra.py`) redirigen el stdin o corren programas que no lo leen: no
hay otra espera posible. Los `Remove-Item` sin `-Recurse`, que en una consola interactiva pueden
preguntar, solo corren sobre carpetas vacías.

## Las decisiones, y por qué

### Se rompe una copia, no se restaura mejor el árbol

Restaurar con un archivo de respaldo, un rename atómico o un lock seguiría escribiendo el árbol: un
proceso matado entre la rotura y la restauración lo deja roto igual, y dos corridas a la vez se
pisan igual. La única forma de que matar el proceso no pueda romper el árbol es que el test no lo
escriba. Es lo que pedía el arreglo de `PENDIENTES-FH.md`: *«Run those two cases against a copy of
the repo in a temporary directory»*.

### La copia es lo que el instalador lee, no el repo entero

`install.ps1`, `VERSION`, `comun`, `harnesses`, `normativa`, `tests\payloads` y
`tests\medir_barra.py`: lo que `install.ps1` lee de `$script:Repo`. Unos 380 archivos, 4 MB, menos
de un segundo. Si el instalador empieza a leer otra cosa, E-04 y E-08 lo dicen: la copia trae cada
archivo versionado de esas partes, y E-20/E-27 afirman que fallan por la rotura (`SyntaxError`,
`pre-tool-use`) y no por un archivo que falta.

### Se ataja la falla de `Read-Host` y la de `ShouldProcess`, no se adivina el modo

La decisión de `instalador-sin-consola`: buscar `-NonInteractive` en la línea de comandos cubre un
solo motivo. Atajar la falla cubre también los hosts sin UI. En `ShouldProcess` se ataja solo la
`PSInvalidOperationException` que da un host que no puede preguntar; cualquier otra sale tal cual.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `tests/isolated-factory.ps1` | `New-FabricaAislada`, `Remove-FabricaAislada`, `Invoke-EnFabricaAislada`, `Clear-FabricasHuerfanas` |
| `tests/casos/03-instalador.ps1` | E-20 y E-27 rompen una copia aislada; dos aserciones nuevas dicen que la falla es la rotura |
| `tests/casos/68-isolated-factory.ps1` | E-01 a E-07 y E-09 |
| `tests/casos/69-instalador-sin-consola.ps1` | E-10 a E-16, con una consola real |
| `install.ps1`, `Resolve-Usuario` | Si `Read-Host` no puede correr, o devuelve fin de entrada, `falta -Usuario …` |
| `install.ps1`, `Confirm-Operacion` | `ShouldProcess` en las tres operaciones; con `-Confirm` y sin consola, un error que dice que no se hizo nada |
| `install.ps1`, `Get-Sha256Archivo` | SHA-256 con .NET en vez de `Get-FileHash`, que pasa por `ShouldProcess` y no acepta `-Confirm:$false`. Mismo resultado, en mayúsculas y sin guiones |

## Escenarios verificables

### Q1 — la fábrica aislada

- **E-01** — (Q1-A) Un test que rompe su copia y termina con una aserción fallida: al salir, la copia
  no existe y el árbol (los bytes de `zonas.py` y `pre-tool-use.py`, y `git status --porcelain
  --untracked-files=all`) quedó igual. · rojo visto: si (M11, M12)
- **E-02** — (Q1-B, Q1-F) Un test que rompe su copia y tira una excepción: la misma excepción sale
  del mecanismo, la copia no existe y el árbol quedó igual. · rojo visto: si (M11, M12; M13 para la excepción)
- **E-03** — (Q1-C) Un proceso hijo con su copia rota, matado con `taskkill /T /F` en la ventana:
  el árbol queda igual byte a byte y con el mismo `git status`. · rojo visto: si (M11, y la reproducción sobre `05fefcd`)
- **E-04** — (Q1-D) La corrida siguiente borra la copia del hijo matado, y su copia nueva trae
  `zonas.py` y `pre-tool-use.py` iguales al árbol y cada archivo versionado de lo que el instalador
  lee. · rojo visto: si (M15, M17)
- **E-05** — El barrido no borra la copia de un dueño vivo ni una carpeta con el prefijo y sin
  marca. · rojo visto: si (M16, M16b)
- **E-05b** — Tampoco borra la copia de un dueño vivo cuyo arranque no se puede leer (una compuerta
  elevada vista desde una que no lo está). *Agregado el 06-10-2026 por la refutación (H1): antes ese
  dueño contaba como muerto.* · rojo visto: si (M19)
- **E-06** — (Q1-E) Al terminar no queda ninguna copia de la corrida en el temporal, y el árbol tiene
  los mismos bytes y el mismo `git status`, sin archivos nuevos. · rojo visto: si (M11, M12)
- **E-07** — (Q1-F) Un hijo que sale con `exit 7` dentro de su copia sale con 7, y su copia se
  borró. · rojo visto: si (M14b; M11 y M12 para la copia)
- **E-08** — E-20 y E-27 de `03-instalador.ps1` rompen una copia: el árbol queda byte a byte igual,
  y cada uno falla por su rotura (`SyntaxError` en E-20, `pre-tool-use` en E-27). · rojo visto:
  si (M21/M22, y la reproducción sobre `05fefcd`)
- **E-09** — `Remove-FabricaAislada` se niega a borrar algo que no es una copia marcada en el
  temporal, el árbol incluido. · rojo visto: si (M18)

### Q2 — sin nadie a quien preguntar

- **E-10** — (Q2-A; `instalador-sin-consola` E-05) Con consola real, `-NonInteractive` y `-Usuario`:
  termina, sale 0, deja el lockfile y no pregunta el nombre. · rojo visto: si (M06)
- **E-11** — (Q2-B; `instalador-sin-consola` E-01 a E-03) Con consola real, `-NonInteractive` y sin
  `-Usuario`: termina, sale 1, la salida pide `-Usuario`, no trae el mensaje de PowerShell sobre el
  modo no interactivo y no escribe nada en el proyecto. · rojo visto: si (M01 = `install.ps1` de `05fefcd`, M02, M07)
- **E-12** — (Q2-B, aprobación) Con consola real, `-NonInteractive`, `-Usuario` y `-Confirm`:
  termina, sale con error, no instala nada y la salida nombra `-Confirm`. · rojo visto: si (M01, M03, M03b)
- **E-12b** — Con stdin vacío y cerrado, `-Update -Confirm` sobre un proyecto instalado: sale con error, el
  lockfile no cambia, la salida nombra `-Confirm` y no trae una traza. *Agregado el 05-10-2026,
  después del smoke: `-Update` leía hashes con `Get-FileHash`, que con `-Confirm` también pregunta, y
  fallaba con el mensaje de PowerShell antes de la confirmación propia.* · rojo visto: si (M09)
- **E-12c** — En el mismo proyecto, `-Uninstall -Confirm`: sale con error, no desinstala (el lockfile
  sigue igual), nombra `-Confirm` y no trae una traza. *Agregado el 06-10-2026 por la refutación (H4).*
  · rojo visto: si (M10)
- **E-13** — (Q2-C; `instalador-sin-consola` E-04) Con stdin cerrado y sin `-Usuario`: termina, sale
  1, pide `-Usuario` y no escribe nada. · rojo visto: si (M07)
- **E-14** — (Q2-D) Las salidas de E-11, E-12 y E-13 no traen una traza de PowerShell (`En línea:`,
  `At line:`, `CategoryInfo`, `FullyQualifiedErrorId`) ni de Python. · rojo visto: si (M04)
- **E-15** — (Q2-E) E-11 corrido dos veces da el mismo código y la misma salida. · rojo visto:
  si (M05)
- **E-16** — La premisa: el instalador de E-10 a E-12 ve su stdin como una consola
  (`[Console]::IsInputRedirected` es `False`). Si no, Q2 no prueba nada y esto falla. · rojo visto:
  si (M08)

## Cómo se verifica

Todo por la suite: ningún escenario es sobre la corrida de un modelo. E-03 mata de verdad a un
proceso, pero es un hijo que trabaja sobre su propia copia; nunca se mata nada que escriba el árbol.
E-10 a E-16 abren una consola oculta por corrida.

Además, una aceptación humana de Q2 en la terminal de la persona (abajo): la consola oculta es una
consola real de Windows, pero no es la de quien usa el harness.

### La misma muerte, con el arreglo

El mismo observador y el mismo `taskkill /T /F`, sobre un clon con los tests nuevos. La ventana ahora
está en la copia del temporal:

```text
ventana vista en: …\Temp\harness-fabrica-023f4f5b\comun\hooks\lib\zonas.py  (t=58s)
sha256 despues: 9812CC62…D832F  igual=True
git status --porcelain (clon):            (vacío)
copias huerfanas tras el kill: harness-fabrica-023f4f5b
--- corrida siguiente (68-isolated-factory.ps1) sobre el mismo clon:
23/23 pasaron
copias huerfanas despues de la corrida siguiente: (ninguna)
```

Igual para `pre-tool-use.py` (t=72s, `DAB08EC4…40E1D` igual, `git status` vacío, la huérfana barrida).

### Las mutaciones

Cada una en su propio clon descartable bajo `%TEMP%`: `05fefcd` más los cambios de este gate y una
mutación de texto. El árbol fuente no se tocó.

| | Mutación | Rojo |
|---|---|---|
| M01 | `install.ps1` de `05fefcd` | E-11 (pide `-Usuario`, sin el mensaje de PowerShell), E-12 (nombra `-Confirm`) |
| M02 | `Read-Host` que falla y reintenta | E-11 «no se cuelga» (timeout de 180 s) |
| M03 | `Confirm-Operacion` devuelve sí | E-12 (nombra `-Confirm`); ver la nota de las dos capas |
| M03b | sí y `ConfirmPreference = None` | E-12 entero: sale 0, instala, no nombra `-Confirm` |
| M04 | el despacho imprime el error entero | E-14, las tres salidas |
| M05 | un GUID en el mensaje | E-15 |
| M06 | ignora `-Usuario` | E-10 |
| M07 | sin la rama de stdin redirigido ni el `try` | E-11, E-13 |
| M08 | el envoltorio le redirige el stdin a la sonda | E-16 |
| M09 | `Get-FileHash` de vuelta | E-12b |
| M08b | lo mismo, con el prefijo compartido de la sonda y el instalador | E-16 |
| M10 | `-Uninstall` vuelve a `ShouldProcess` crudo | E-12c |
| M11 | la técnica vieja: romper el árbol y restaurarlo en un `finally` | E-03 (el árbol cambió al matar al hijo), E-01, E-02, E-04, E-06, E-07 |
| M12 | sin limpieza | E-01, E-02, E-06, E-07 |
| M13 | la limpieza se traga la excepción | E-02 |
| M14b | la limpieza tapa el `exit` | E-07 |
| M15 | sin barrido | E-04 |
| M16 | el barrido no mira si el dueño vive | E-05 |
| M16b | el barrido borra carpetas sin marca | E-05 |
| M17 | la copia sin `normativa` | E-04 (la ruta sale de `install.ps1`) |
| M18 | `Remove-FabricaAislada` sin guarda | E-09 |
| M19 | el barrido toma por muerto a un dueño con el arranque ilegible | E-05b |
| M21/M22 | E-20 borra `zonas.py` de la copia en vez de romperlo; E-27 borra un manifiesto | E-08: `SyntaxError`, `Revirtiendo`, `pre-tool-use` |

M17 primero dio verde: E-04 comparaba la copia contra la misma lista con la que se arma, así que no
podía fallar. Se cambió para leer de `install.ps1` las rutas que arma con `Join-Path $script:Repo`, y
recién ahí dio rojo. M14 (tirar en la limpieza) rompió la carga del archivo en vez de E-07, y se
reemplazó por M14b.

### Smoke real del instalador cambiado

Sobre un proyecto descartable, `powershell.exe -NoProfile -NonInteractive`, stdin cerrado:

```text
WhatIf sin -Usuario                exit=0
install desarrollo -Usuario        exit=0
Doctor -Project                    exit=0
Update -Confirm (sin consola)      exit=1  -Confirm pide una confirmación y no hay consola para darla. No se hizo nada. …   lock igual=True
Update                             exit=0
Uninstall -Confirm (sin consola)   exit=1  -Confirm pide una confirmación …   lock sigue=True
Uninstall                          exit=0  lock=False
```

### La compuerta

| | |
|---|---|
| Focales PowerShell (los 19 `.ps1` de `tests/casos`), antes de la refutación | 696/696 |
| `03-instalador.ps1` | 205/205 |
| `68-isolated-factory.ps1` | 25/25 (23/23 tres corridas seguidas antes de E-05b) |
| `69-instalador-sin-consola.ps1` | 31/31 |
| `.\tests\Invoke-Tests.ps1`, antes de la refutación | 40441/40441, exit 0, 1062 s |
| `.\tests\Invoke-Tests.ps1`, final | **40447/40447, exit 0** (PowerShell 702/702, Python 39745/39745), 1062 s |

La base era 40389/40389; los 58 nuevos son 2 en 03, 25 en 68 y 31 en 69.

### La refutación

`harness-spec-refuter`, que no construyó, el 05/06-10-2026. Corrió la compuerta completa (40441/40441,
exit 0), las focales, M03b y M09 por su cuenta y la muerte en la ventana de E-27 sobre un clon.

| Afirmación | Veredicto |
|---|---|
| R-Q1-01 Los tests afectados operan sobre estado aislado o garantizan la restauración dentro del alcance declarado | sostenido |
| R-Q1-02 Matar el proceso de prueba no modifica el árbol fuente | sostenido |
| R-Q1-03 Una corrida abortada no contamina la siguiente | sostenido |
| R-Q2-01 `-NonInteractive` nunca espera input humano | sostenido |
| R-Q2-02 `-NonInteractive` no es aprobación automática | sostenido |
| R-Q2-03 Los errores salen con código determinista y diagnóstico, sin traza | sostenido |
| R-Q2-04 No se debilitó Flow Authority, Secret Guard ni la aprobación; `Get-Sha256Archivo` da lo mismo que `Get-FileHash` (502 archivos, 0 diferencias) | sostenido |

Escenarios: E-01 a E-16 y E-12b, **17 sostenidos**, ninguno contradicho ni sin sustento.

Hallazgos NON_BLOCKING, y qué se hizo:

| | Hallazgo | Qué se hizo |
|---|---|---|
| H1 | El barrido tomaba por muerto a un dueño vivo cuyo arranque no se puede leer (una compuerta elevada vista desde una que no lo está): contradecía «nunca se borra de más» | Arreglado: un arranque ilegible es un dueño vivo. E-05b, rojo con M19 |
| H2 | E-16 mide un proceso hermano del instalador | La sonda y el instalador se lanzan con el mismo prefijo; M08b sigue dando rojo |
| H3 | E-12b decía «stdin cerrado» y heredaba el de la compuerta | El hijo recibe un pipe vacío que se cierra |
| H4 | `-Uninstall -Confirm` sin test; «dos compuertas a la vez» sin escenario; `instalador-sin-consola` E-05 cubierta a medias | E-12c (rojo con M10); la fila de la tabla Q1 y los riesgos lo dicen |
| H5 | M03b y M09 sin evidencia registrada | El refutador las corrió; están en la tabla de mutaciones |

**Segunda pasada**, sobre lo cambiado después de la primera: E-05b, E-12b (con el stdin cerrado de
verdad), E-12c, E-16 con el prefijo compartido, el arreglo de H1 y la regresión de los 17 de la
primera. **6 sostenidos**, ninguno contradicho ni sin sustento. Corrió 68 y 69 (56/56), 03 (205/205)
y M08b, M10 y M19 (un rojo cada una). Recorrió los 301 procesos vivos con `Get-DuenoDeProceso`: 138
dan `ilegible`, ninguno tira. Tres NON_BLOCKING: N1, números viejos en esta sección (leyó antes de
que se actualizaran); N2, lo que queda de H2 (abajo, en los riesgos); N3, el script de mutaciones
del scratchpad ignora `-Solo` con varios valores si se lo llama con `-File` (no es del repo).

### La aceptación humana de Q2

**PASS**, de la persona, en su propia terminal de PowerShell, con los pasos de abajo. La pedía el
gate porque la consola oculta de la suite es una consola real de Windows, pero no la terminal de la
persona, que es donde se vio el defecto.

| | Qué | Lo que observó la persona | Veredicto |
|---|---|---|---|
| A | `-NonInteractive`, sin `-Usuario` | «falta -Usuario. Este harness te trata por tu nombre, y no hay consola para preguntarlo. Agregá: -Usuario 'Tu Nombre'»; `exit=1`, `.claude=False` | PASS |
| B | `-NonInteractive` con `-Confirm` | «-Confirm pide una confirmación y no hay consola para darla. No se hizo nada. Corré sin -Confirm, o desde una consola interactiva.»; `exit=1`, `.claude=False`. Sostiene que `-NonInteractive` no es aprobación automática | PASS |
| C | `-NonInteractive` con `-Usuario` | instalación completa, estado READY, `exit=0`, `lock=True`, sin pedir nada | PASS |
| D | interactivo, sin `-Usuario` | preguntó «¿Cómo te llamás?:», la persona contestó, terminó READY, `exit=0`. El arreglo no sacó la interacción normal | PASS |
| E | la compuerta desde su terminal | PowerShell 702/702 (Q1 «la fábrica aislada» 25/25, Q2 «el instalador sin nadie a quien preguntar» 31/31), Python 39745/39745: **40447/40447, exit 0** | PASS |

Un comando escrito por error después de que la suite terminó y volvió el prompt no es parte de la
compuerta y no cambia esta evidencia.

**Q1: CLOSED. Q2: CLOSED. Qualification Gate 1: CLOSED.** No es la calificación: los bloqueantes
que quedan están en `qualification-readiness.md`.

Los pasos que corrió la persona:

Desde la terminal propia de PowerShell, en la raíz del repo. Nada de esto toca el árbol: los
proyectos son carpetas nuevas del temporal.

```powershell
$p = Join-Path $env:TEMP ('qg1-manual-' + (Get-Random)); New-Item -ItemType Directory $p | Out-Null

# A. -NonInteractive, sin -Usuario: no pregunta, sale 1, pide -Usuario, no escribe nada
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\install.ps1 -Project $p -Harness analisis
"exit=$LASTEXITCODE  .claude=$(Test-Path "$p\.claude")"          # esperado: exit=1  .claude=False

# B. -NonInteractive con -Confirm: no confirma solo, sale 1, nombra -Confirm, no instala
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\install.ps1 -Project $p -Harness analisis -Usuario 'Prueba Manual' -Confirm
"exit=$LASTEXITCODE  .claude=$(Test-Path "$p\.claude")"          # esperado: exit=1  .claude=False

# C. -NonInteractive con -Usuario: instala sin preguntar
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\install.ps1 -Project $p -Harness analisis -Usuario 'Prueba Manual'
"exit=$LASTEXITCODE  lock=$(Test-Path "$p\.claude\harness.lock.json")"   # esperado: exit=0  lock=True

# D. Interactivo, sin -NonInteractive y sin -Usuario: TIENE que preguntar el nombre. Contestar.
$q = Join-Path $env:TEMP ('qg1-manual-i-' + (Get-Random)); New-Item -ItemType Directory $q | Out-Null
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Project $q -Harness analisis
"exit=$LASTEXITCODE"                                               # esperado: preguntó, exit=0

# E. La compuerta desde la terminal propia: el rojo del 28-09-2026 era acá
.\tests\Invoke-Tests.ps1; "exit=$LASTEXITCODE"                     # esperado: 40447/40447, exit=0

# Limpieza
Remove-Item -LiteralPath $p, $q -Recurse -Force
```

Lo que hay que devolver: la salida de A a D tal cual, y las dos últimas líneas de E.

## Riesgos conocidos

- **Una consola oculta necesita una sesión de escritorio.** En un agente o un CI sin escritorio,
  `Start-Process -WindowStyle Hidden` puede no darle consola al hijo. E-16 falla en ese caso, en vez
  de dejar pasar en silencio a E-10 a E-15.
- **La copia huérfana de una corrida matada** queda en `%TEMP%` hasta la corrida siguiente. Si el
  pid se reusó con el mismo instante de arranque —que no pasa—, o lo tomó un proceso que no deja
  leer su arranque, no se barre: la duda queda del lado de no borrar.
- **E-16 mide un proceso hermano del instalador** (refutación, H2 y N2): la sonda y el instalador
  salen del mismo prefijo, así que no pueden recibir el stdin distinto sin que se note en el código,
  pero eso se sostiene por lectura, no por un test. El refutador confirmó aparte, en el proceso mismo
  del instalador, que ve la consola.
- **E-05b usa a System (pid 4)** como dueño vivo con el arranque ilegible. Si en otra máquina se
  pudiera leer, la premisa de E-05b falla y lo dice, en vez de pasar en silencio.
- **`instalador-sin-consola` E-05 queda cubierta a medias:** E-10 prueba `-Usuario` con
  `-NonInteractive` en consola real; el nombre ya configurado lo recorren `-Update` (E-12b y los
  casos de `03-instalador.ps1`), no una instalación nueva con `harness.config.json` previo.
- **Una corrida matada mientras copia** deja una copia parcial con la marca: se barre igual.
- **E-12 se apoya en el tipo de la excepción** (`PSInvalidOperationException`) que da
  `ShouldProcess` en un host que no puede preguntar. Si una versión de PowerShell cambia el tipo, el
  error sale crudo, pero sigue sin instalar nada: E-12 lo vería por el mensaje.
