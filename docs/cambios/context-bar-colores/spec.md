# La Context Bar con colores

**Estado:** verificado y cerrado · **Fecha:** 29-09-2026 · **Bloque:** 1, capa de presentación

## Qué problema resuelve

La Context Bar (`harnesses/desarrollo/bin/contabilidad/statusline.py`) se dibuja como texto plano.
`WARNING` y `ERROR` se ven igual que el resto de la línea, y un `Ctx 92%` o un `Budget 95%` no
llaman la atención. El Bloque 4 ya calcula el nivel de cada uno (`NORMAL`, `WARNING`, `ERROR`,
`UNRESOLVED`, en `presupuesto.nivel`), pero la barra no lo muestra de ninguna manera visible.

La `statusLine` de Claude Code acepta secuencias ANSI. Este cambio las usa para mostrar ese nivel,
sin cambiar lo que dice la línea.

## Qué queda afuera

- **Cambiar el Bloque 4.** `barra.py`, los umbrales de `presupuesto.py`, la política, el cálculo del
  contexto, los tokens y el tiempo no se tocan: la barra usa el `level` que ya recibe. Volver a
  calcular umbrales en la barra sería una segunda fuente de los mismos números.
- **Verde para `NORMAL`.** Un color en cada campo, siempre, es ruido. El color se reserva para lo que
  pide atención.
- **Color para `UNRESOLVED`.** Sin umbrales no hay nivel. Pintarlo sería inventar una alerta.
- **Colorear `HARNESS | sin datos del Bloque 4`.** Es la línea de falla, y tiene que salir idéntica
  byte a byte: la comparan los tests y la mira quien diagnostica.
- **Detectar lo que soporta la terminal** (`tput`, `TERM`, `isatty`). La barra corre bajo Claude
  Code, que ya interpreta ANSI, y su stdout nunca es una terminal. Lo único que la apaga es
  `NO_COLOR`.
- **Glifos Unicode o colores de 256.** La salida sigue siendo ASCII, y los 8 colores básicos son los
  que se ven en cualquier consola.
- **Cambiar la forma del comando registrado.** Sigue siendo `python '<statusline.py>' '<huella>'`,
  sin envoltorios de shell.

## Las decisiones, y por qué

### El color sale de Python, no del shell

La barra corre en Git Bash o en PowerShell 5.1, según la máquina. Un `printf` o un `Write-Host`
serían dos implementaciones distintas. Python escribe la secuencia ANSI como bytes ASCII
(`ESC` es `0x1B`), y `linea.encode("ascii", "replace")` la deja pasar tal cual. PowerShell 5.1
vuelve a codificar la salida con la codepage de la consola, y un byte ASCII sobrevive a cualquier
codepage.

### `NO_COLOR` definida, aunque esté vacía, apaga todo

Es la convención de no-color.org: importa si la variable existe, no su valor. `NO_COLOR=` también
apaga los colores. Con `NO_COLOR`, la línea es la de hoy, byte a byte.

### Qué se pinta

| Fragmento | `NORMAL` | `WARNING` | `ERROR` | `UNRESOLVED` |
|---|---|---|---|---|
| `Ctx NN%` | sin color | amarillo | rojo | sin color |
| `Budget NN%` | sin color | amarillo | rojo | sin color |
| la etiqueta `WARNING` / `ERROR` | — | amarillo | rojo | — |

`HARNESS` va en negrita, sin color de severidad, cuando hay datos. Cada fragmento pintado se cierra
con su propio `ESC[0m`: un color no se derrama sobre el campo siguiente. Los separadores ` | ` nunca
llevan color.

Las secuencias son SGR estándar: `ESC[0m`, `ESC[1m`, `ESC[33m`, `ESC[31m`.

### `INTEGRATION_VERSION` pasa a `1.1.0`

Lo que dibuja la barra cambia. Una instalación que actualiza tiene que ver que el renderizador es
otro. La huella del renderizador ya lo detecta sola; la versión lo dice en `harness --verbose` y en
la señal de vida.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/contabilidad/statusline.py` | Pinta los fragmentos según su `level`, apaga todo con `NO_COLOR` y deja `LINEA_SIN_DATOS` como está. `INTEGRATION_VERSION = "1.1.0"` |
| `tests/casos/53_context_bar.py` | Los escenarios E-01 a E-18, E-20 y E-21, contra `dibujar` y contra el renderizador instalado. Sus aserciones dicen `colores E-nn`, para no confundirse con los `E-nn` de `bloque-1-context-bar` del mismo archivo |
| `tests/casos/54-context-bar-instalador.ps1` | E-19: el comando instalado, con un estado en alerta, en los dos shells |
| `docs/contabilidad.md` | Los colores y `NO_COLOR`, en la sección de la Context Bar |

## Escenarios verificables

Los escenarios del pedido se llaman `CB-ANSI-nn`, y acá `E-nn` es `CB-ANSI-nn`. E-19 a E-21 los
agrega esta spec.

### El contexto

- **E-01** — Con el contexto en `NORMAL`, `Ctx NN%` no lleva ninguna secuencia ANSI de color.
  · rojo visto: si
- **E-02** — Con el contexto en `WARNING`, `Ctx NN%` sale como `ESC[33mCtx NN%ESC[0m`.
  · rojo visto: si
- **E-03** — Con el contexto en `ERROR`, `Ctx NN%` sale como `ESC[31mCtx NN%ESC[0m`.
  · rojo visto: si

### El presupuesto

- **E-04** — Con el presupuesto en `NORMAL`, `Budget NN%` no lleva ninguna secuencia ANSI de color.
  · rojo visto: si
- **E-05** — Con el presupuesto en `WARNING`, `Budget NN%` sale como `ESC[33mBudget NN%ESC[0m`.
  · rojo visto: si
- **E-06** — Con el presupuesto en `ERROR`, `Budget NN%` sale como `ESC[31mBudget NN%ESC[0m`.
  · rojo visto: si

### La etiqueta final

- **E-07** — La etiqueta `WARNING` del final sale como `ESC[33mWARNINGESC[0m`.
  · rojo visto: si
- **E-08** — La etiqueta `ERROR` del final sale como `ESC[31mERRORESC[0m`. · rojo visto: si

### `HARNESS`

- **E-09** — Con datos, la línea empieza con `ESC[1mHARNESSESC[0m | `. · rojo visto: si
- **E-10** — `HARNESS` nunca lleva `ESC[31m` ni `ESC[33m`, aunque el contexto y el presupuesto
  estén en `ERROR`. · rojo visto: si

### `NO_COLOR`

- **E-11** — Con `NO_COLOR=1`, la línea no tiene ningún byte `0x1B`, en un estado con los dos
  niveles en `ERROR`. · rojo visto: si
- **E-12** — Con `NO_COLOR=` (definida y vacía), tampoco. · rojo visto: si

### La línea sin datos

- **E-13** — La línea sin datos es exactamente `HARNESS | sin datos del Bloque 4`, con colores
  habilitados, y la del renderizador instalado sin stdin también. · rojo visto: si
- **E-14** — La línea sin datos no tiene ningún byte `0x1B`. · rojo visto: si

### `UNRESOLVED`

- **E-15** — Con el contexto en `UNRESOLVED`, su fragmento no lleva color, ni con porcentaje ni
  en tokens (`Ctx 10k`). · rojo visto: si
- **E-16** — Con el presupuesto en `UNRESOLVED`, `Budget NN%` no lleva color, y no aparece ninguna
  etiqueta `WARNING` ni `ERROR` que ningún nivel pidió. · rojo visto: si

### El contenido no cambia

- **E-17** — Para un estado con modelo, contexto, tokens, costo, tiempo, presupuesto, alerta, tarea
  y agente, sacar las secuencias ANSI (`\x1b\[[0-9;]*m`) de la línea con colores da exactamente la
  línea con `NO_COLOR`, y esa es exactamente la línea esperada escrita a mano en el test.
  · rojo visto: si
- **E-18** — El orden de los campos es `HARNESS`, modelo, `Ctx`, `Tok`, costo, tiempo, `Budget`,
  alerta, `Tarea`, `Agente`, con colores y sin ellos. · rojo visto: si

### El comando instalado

- **E-19** — El comando que registra `install.ps1`, corrido con `powershell.exe -NoProfile -Command`
  y con `bash -c` sobre una sesión con el presupuesto en `ERROR`, sale con 0, dibuja una sola línea no
  vacía que contiene los bytes `ESC[31m`, y deja la señal de vida con la huella del comando.
  · rojo visto: si
- **E-20** — La señal de vida que escribe la barra dice `integrationVersion: "1.1.0"`.
  · rojo visto: si
- **E-21** — `docs/contabilidad.md` dice qué se pinta de amarillo y de rojo, y que `NO_COLOR` apaga
  los colores. · rojo visto: si

## Cómo se verifica

Todos van por la suite:
- E-01 a E-18 y E-20 en `tests/casos/53_context_bar.py`, contra `dibujar` con estados armados a mano
  y contra el renderizador instalado;
- E-19 en `tests/casos/54-context-bar-instalador.ps1`, que instala de verdad;
- E-21 en `tests/casos/53_context_bar.py`, leyendo el archivo.

El `rojo visto` de E-01 a E-18, E-20 y E-21 salió de romper `statusline.py` y
`docs/contabilidad.md` una vez por comportamiento, el 29-09-2026: cada mutación hizo fallar su
escenario, y el archivo volvió a su versión byte a byte. El de E-19 se vio en la primera corrida
de la suite: el entorno traía `NO_COLOR=1`, el comando dibujó sin colores y E-19 falló en los dos
shells.

Los tests comparan bytes, no cómo se ve la terminal. Se mira con los ojos, y se anota en la
verificación, que en una sesión real de Claude Code los colores se ven.

## Riesgos conocidos

- **Una consola que no interpreta ANSI** muestra `[33m` en crudo. Claude Code interpreta ANSI en la
  `statusLine`. Para cualquier otro caso, la salida es `NO_COLOR`.
- **Los tests que ya existían comparan texto plano.** El ayudante `_dibujar` de
  `53_context_bar.py` corre con `NO_COLOR` salvo que un test pida colores. Si no, los escenarios de
  `bloque-1-context-bar` pasarían a probar los bytes de color, que no son lo suyo. E-17 es el que
  prueba que con y sin colores la línea dice lo mismo.
- **Claude Code le pone `NO_COLOR=1` a los comandos de sus herramientas** (visto el 29-09-2026: no
  viene del entorno del usuario ni del de la máquina). Si también se lo pone a la `statusLine`, la
  barra sale sin colores, que es lo que tiene que hacer con `NO_COLOR`. La suite no lo puede saber.
  Se mira con los ojos en una sesión real, y si pasa, queda anotado en la verificación.
- **Amarillo sobre fondo claro** se lee peor. Se aceptó: son los colores del pedido.
