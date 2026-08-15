# Hooks, checks y tests en Python

**Estado:** especificado · **Fecha:** 2026-08-15

Primera vez que este repositorio usa el formato de spec para un cambio propio. ADR-0006 dejó
`gcba-harness` explícitamente afuera de SDD —*"se toma después de haberlo visto funcionar"*— y
esto es exactamente ese después: un cambio grande, que toca la única regla que bloquea, y que
tiene que salir con el comportamiento intacto.

## Qué problema resuelve

**El hook que corre en cada tool call tarda 981 ms.**

Medido el 15-08-2026 sobre `comun/hooks/pre-tool-use.ps1` con el payload real
`tests/payloads/pre-tool-use-write.json`, p50 de 14 corridas, cronometrado con `Stopwatch`
desde PowerShell para no contar el fork de Git Bash:

```
spawn puro (cmd /c exit)                    71 ms
powershell.exe arranque                    457 ms
+ los 2 Import-Module -Force               614 ms
HOOK REAL pre-tool-use, punta a punta      981 ms
```

El plan original —registrado en `docs/versiones/0.6.0.md`— decía evaluar la reescritura si el
p50 pasaba los ~400 ms, y nunca se midió. Está 2,5× por encima de ese umbral.

Un prototipo desechable en Python, haciendo el mismo trabajo real (leer stdin, cargar el
catálogo, compilar y correr las 12 regex de detección y las 15 de ignorar) da **335 ms**. Son
646 ms menos en cada llamada a herramienta de cada sesión.

📌 **El objetivo es paridad de comportamiento, con la latencia como premio.** No es una
oportunidad para rediseñar reglas. Si un check tiene un defecto, se porta con el defecto y se
arregla en un cambio aparte, donde se pueda ver el diff de la regla sin el ruido del port.

### El segundo problema, que se cierra de arrastre

Los hooks se lanzan desde `run-hook.cmd`, que resuelve `powershell.exe`. Por eso el harness es
de Windows y por eso falta el shim `.sh` que está anotado en `PENDIENTES-FH.md`. Con los hooks
en Python, `run-hook.sh` es de tres líneas y el mismo `.py` corre en WSL, macOS y Linux.

## Qué queda afuera

- **`install.ps1`.** Sigue en PowerShell y no se toca su rol. Es el bootstrap: corre sobre un
  Windows pelado, antes de que exista nada instalado. PowerShell 5.1 es lo único garantizado en
  ese momento, y un instalador que no puede arrancar tampoco puede explicar por qué.
- **El diseño de las reglas.** Es un port. El catálogo de patrones, los techos de zona, los
  umbrales y los mensajes salen idénticos.
- **Dependencias de `pip`.** Biblioteca estándar y nada más. La regla de ADR-0006 —*"no entra
  ninguna dependencia nueva"*— vale también acá: `json`, `re`, `importlib` y `pathlib` alcanzan.
- **Empaquetar un intérprete.** Se usa el Python de la máquina. Versionar 15 MB de runtime en un
  repo público es otra decisión y no es ésta.
- **PowerShell 7.** No se agrega `pwsh` como requisito, ni acá ni en el instalador.
- **El ruteo de `UserPromptSubmit`.** Sigue mudo. Está en pendientes y se resuelve por su cuenta:
  portarlo mudo es portarlo entero.

## Las decisiones, y por qué

### El shim fija el `python.exe`, no lo busca

```bat
run-hook.cmd    "<python.exe REAL, resuelto al instalar>" "%~dp0hooks\%1.py"
run-hook.sh     exec python3 "$(dirname "$0")/hooks/$1.py"
```

`install.ps1` corre `python -c "import sys; print(sys.executable)"` y escribe **esa** ruta. No
es cosmético: en esta máquina `python` es un shim de PyManager y cuesta 260 ms de más.

```
python via shim de PyManager    547 ms
python.exe directo              284 ms
```

El shim sigue siendo el único artefacto del harness con una ruta absoluta de la máquina, y sigue
estando gitignoreado. La invariante de portabilidad no cambia: `settings.json` nunca ve una ruta
absoluta.

### El mínimo es Python 3.9

`comun/manifest.json` declara `requierePython: "3.9"`, al lado de `requiereClaudeCode`. Es el
piso que hace falta para escribir el port sin contorsiones y está en cualquier máquina que tenga
Python de esta década. Esta máquina tiene 3.13.14.

Se declara en el manifiesto y no en el código por la misma razón que la versión de Claude Code:
subir el piso tiene que ser un cambio de un número, no una búsqueda por el repo.

### Sin `-I` ni `-S`

Recortan el arranque 6 ms —ruido— y a cambio `-I` implica `-P`, que deja de poner el directorio
del script en `sys.path`. Eso rompe `import lib.hook` de una forma que se descubre recién cuando
un hook no arranca en la máquina de otro. Comprobado el 15-08-2026 sobre 3.13.14:

```
sin flags   -> import OK
-I          -> import FALLA: No module named 'm'
-I -S       -> import FALLA
-P          -> import FALLA
```

No se paga una trampa por 6 ms.

### Los checks se cargan por ruta, no por nombre de módulo

El contrato de hoy es *"un `.ps1` en el directorio de checks, y con eso alcanza"*: agregar una
regla no exige registrarla en ningún lado. Se preserva tal cual, con una vuelta: los checks se
llaman `claude-md-zonas.py`, `dev-api-rutas.py`, con guiones, y un guion no es un nombre de
módulo importable.

Se cargan con `importlib.util.spec_from_file_location`, que acepta cualquier nombre de archivo.
El descubrimiento sigue siendo *estar en el directorio*, y el nombre del check sigue siendo el
que se lee en un aviso.

Contrato del check, antes y después:

```powershell
param($Evento, $Proyecto, $Config)   ->   devuelve cero o mas strings
```
```python
def verificar(evento, proyecto, config) -> list[str]
```

### Las zonas se implementan una vez, en Python

`install.ps1` usa `Get-DefinicionZonas`, `Get-ContenidoZona` y `Find-ZonasNoReconocidas`; el
check usa `Find-ZonasNoReconocidas`, `Measure-FueraDeZonas` y `Measure-Zonas`. Si el check se va
a Python y el instalador se queda, esa lib queda escrita dos veces — y el repo tiene anotado que
*"la definición de las zonas del CLAUDE.md vive en un solo lado"*.

`lib/zonas.py` es el dueño y expone verbos por línea de comandos que devuelven JSON por stdout.
`install.ps1` lo invoca y parsea. Es el patrón que `comun/bin/docimg.py` ya usa en este repo, así
que no se inventa nada:

```
python lib/zonas.py definicion
python lib/zonas.py contenido <archivo> <zona>
python lib/zonas.py no-reconocidas <archivo>
```

El costo: Python pasa a ser requisito de **instalación**, no solo de ejecución. `-Doctor` lo
verifica y falla con instrucciones.

🔴 **`-Doctor` tiene que correr sin Python, y eso obliga a mover la invocación.** Es la
herramienta que diagnostica la máquina; si dependiera de lo que diagnostica, en la máquina rota
no arrancaría, que es justo donde hace falta.

No alcanza con que `Invoke-Doctor` no llame a `zonas.py`. Hoy la dependencia se carga en el
nivel superior del script, mucho antes de que se despache el verbo:

```powershell
install.ps1:47     $ErrorActionPreference = 'Stop'
install.ps1:58     Import-Module ...\Zonas.psm1 -Force      # corre siempre, para todos los verbos
install.ps1:1117   if ($Doctor) { exit (Invoke-Doctor) }    # recién acá se decide qué se hace
```

Con `Zonas.psm1` eso es inocuo: es PowerShell y está siempre. Convertida en una invocación a
`zonas.py`, la línea 58 mata a `-Doctor` en la máquina sin Python **antes de imprimir nada**.

Por eso la regla es de ubicación, no de intención: **la resolución del intérprete y toda llamada
a `zonas.py` viven adentro de las rutas de `-Instalar` y `-Update`, nunca en el nivel superior.**
`-Doctor` solo comprueba que el intérprete esté y qué versión tiene, con su propia lógica, sin
ejecutar código Python del harness. E-23 lo verifica corriendo `-Doctor` con el Python escondido.

### Un solo comando para los tests, con dos motores adentro

`tests/Invoke-Tests.ps1` sigue siendo el comando y sigue siendo la compuerta que `install.ps1`
usa antes de dar una instalación por buena. Adentro corre `03-instalador` en PowerShell —testea
un script que sigue siendo PowerShell— y delega el resto a `tests/correr.py`, y suma los dos
resultados en un único código de salida.

No se cambia la costumbre ni la compuerta. Cambia lo que hay abajo.

### La trampa del BOM se da vuelta

En PowerShell 5.1 un `.ps1` con acentos **necesita** BOM, y `tests/casos/00-encoding-fuentes.ps1`
lo verifica. En Python el fuente es UTF-8 por definición (PEP 3120) y un BOM es basura tolerada.
El test de encoding se invierte para los `.py`: se exige que **no** lo lleven.

Es la misma clase de bug que ya mordió una vez —un test comparando una cadena corrupta contra
otra corrupta de la misma forma, y pasando—, así que el test se porta antes que los hooks.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/hooks/lib/hook.py` | El contrato: lee stdin, las tres salidas, salir 0 siempre, `systemMessage` una vez por sesión |
| `comun/hooks/lib/secretos.py` | El detector. Puerto exacto de `Secretos.psm1` |
| `comun/hooks/lib/reglas.py` | Descubre y corre los checks, con el tope de 8 hallazgos |
| `comun/hooks/lib/zonas.py` | Zonas: lectura, medición, y los verbos de línea de comandos que consume `install.ps1` |
| `comun/hooks/{session-start,user-prompt-submit,pre-tool-use,post-tool-use}.py` | Los cuatro hooks |
| `comun/checks/claude-md-zonas.py` | Puerto del check de zonas |
| `harnesses/desarrollo/checks/*.py` + `lib/dev.py` | Puerto de los cuatro checks de desarrollo y su lib |
| `comun/settings/run-hook.sh.plantilla` | El shim POSIX. Cierra el pendiente del `.sh` |
| `install.ps1` | Resuelve `python.exe`, escribe los dos shims, consume `zonas.py`, verifica Python en `Test-Entorno` |
| `comun/manifest.json` | Campo `requierePython`, al lado de `requiereClaudeCode` |
| `tests/correr.py` + `tests/casos/*.py` | La suite portada |
| `tests/casos/09-paridad.py` | **El test que hace que esto sea seguro.** Ver E-01 |
| `docs/contrato-hooks.md` | Reescrito sobre el contrato nuevo |
| `docs/instalacion.md`, `README.md`, `UPGRADE.md` | Python como requisito; migración desde 0.12.0 |

📌 **`-Doctor` que mide la latencia (E-25b) entra acá aunque sea otro pendiente.** Es el único
lugar donde el número que justifica todo este cambio queda vigilado; si se deja afuera, dentro
de tres versiones nadie sabe si el hook volvió a los 900 ms. Si se prefiere aparte, se saca este
renglón y el escenario E-25b con él.

## Escenarios verificables

### Paridad del detector de secretos

- **E-01** — Los 31 casos de `tests/casos/04-secretos.ps1` producen en Python **el mismo
  veredicto que en PowerShell**: mismo `permissionDecision` y mismo id de patrón. El caso se
  escribe como tabla de entrada → veredicto esperado, tomada de la implementación actual.
  · rojo visto: no consta
- **E-02** — Las 12 regex de detección y las 15 de ignorar del catálogo compilan bajo `re`. El
  test corre sobre el catálogo, no sobre una copia: si mañana alguien agrega un patrón con
  sintaxis solo de .NET, falla acá y no en la sesión de alguien. · rojo visto: no consta
- **E-03** — Confianza `alta` produce `permissionDecision: deny`; confianza `media` produce
  `ask`. Ninguna otra regla del harness emite `deny`. · rojo visto: no consta
- **E-04** — Un placeholder (`${DB_PASSWORD}`, `your-token-here`, `xxxx`) no dispara: el valor se
  aísla de la asignación antes de probar los patrones de ignorar. · rojo visto: no consta
- **E-05** — Un secreto entre comillas invertidas de markdown no dispara. Es el caso que rompió
  la escritura de `docs/versiones/0.4.0.md`. · rojo visto: no consta

### Contrato de los hooks

- **E-06** — Los cuatro hooks salen con código 0 siempre: con evento válido, con stdin vacío y
  con JSON roto. · rojo visto: no consta
- **E-07** — Un hook cuyo cuerpo tira una excepción emite `systemMessage` y sale 0. La sesión no
  se rompe. · rojo visto: no consta
- **E-08** — Ese mismo hook roto, invocado de nuevo con el mismo `session_id`, **no** vuelve a
  emitir. Una vez por sesión y por evento. · rojo visto: no consta
- **E-09** — `campo(evento, "tool_input.file_path", "")` devuelve el default cuando la ruta no
  existe, en vez de explotar. Es lo que hace que un hook tolere las formas distintas de
  `tool_input` según la herramienta. · rojo visto: no consta
- **E-10** — Un aviso con tildes llega íntegro: la salida JSON no escapa los no-ASCII y se emite
  en UTF-8 aunque la consola esté en CP1252. · rojo visto: no consta
- **E-11** — Un stdin que viene con BOM se parsea igual, sin fallar con "JSON no válido".
  · rojo visto: no consta
- **E-12** — Silencio es silencio: sin hallazgos el hook no escribe **nada** en stdout. Costo en
  contexto cero. · rojo visto: no consta

### Checks

- **E-13** — Un `.py` nuevo dejado en el directorio de checks se descubre y corre, sin
  registrarlo en ningún archivo. · rojo visto: no consta
- **E-14** — Un check que tira una excepción se saltea en silencio y los demás corren igual.
  · rojo visto: no consta
- **E-15** — El tope de 8 hallazgos se respeta: con más, se recorta. · rojo visto: no consta
- **E-16** — Los cinco checks portados producen, sobre los mismos payloads, **los mismos
  hallazgos** que su versión PowerShell, texto incluido. · rojo visto: no consta

### Zonas

- **E-17** — La lista de zonas y sus techos aparece **una sola vez en todo el repo**. Un `grep`
  de `ZONA MAPA` fuera de `zonas.py`, la plantilla del `CLAUDE.md` y la documentación no
  encuentra ninguna definición. · rojo visto: no consta
- **E-18** — `install.ps1` obtiene la definición invocando `zonas.py` y parseando su JSON, y
  crea las cuatro zonas del `CLAUDE.md` igual que antes. · rojo visto: no consta
- **E-19** — El check de zonas, sobre el mismo `CLAUDE.md`, reporta las mismas mediciones y los
  mismos excesos de techo que la versión PowerShell. · rojo visto: no consta
- **E-20** — Si `zonas.py` falla o no está, `install.ps1` aborta con un mensaje que dice qué
  pasó. No instala un `CLAUDE.md` a medias. · rojo visto: no consta

### Arranque, instalación y desinstalación

- **E-21** — `install.ps1` resuelve el `python.exe` real vía `sys.executable` y lo escribe en
  `run-hook.cmd`. El shim generado **no** invoca `python` del PATH. · rojo visto: no consta
- **E-22** — Se genera además `run-hook.sh`, con finales de línea LF, y `.gitattributes` no se
  los convierte. · rojo visto: no consta
- **E-23** — `-Doctor` corre y reporta **aunque no haya Python instalado**: se invoca con el
  `python.exe` inaccesible y tiene que imprimir su diagnóstico completo y fallar con
  instrucciones, no morir antes de la primera línea. · rojo visto: no consta
- **E-23b** — Ninguna invocación a `zonas.py` ni resolución del intérprete ocurre en el nivel
  superior de `install.ps1`: todas viven adentro de las rutas de instalar y actualizar. Es lo
  que hace que E-23 no dependa de la buena voluntad de quien edite el script mañana.
  · rojo visto: no consta
- **E-24** — `-Doctor` falla si el Python encontrado es anterior a `requierePython` del
  manifiesto. · rojo visto: no consta
- **E-25** — Tras `-Update` desde 0.12.0 no queda ningún `.ps1` huérfano en
  `.claude/harness/hooks/` ni en `.claude/harness/checks/`. · rojo visto: no consta
- **E-25b** — `-Doctor` mide el p50 de un hook sobre un payload real y lo reporta. Avisa si pasa
  los 400 ms; nunca bloquea. · rojo visto: no consta
- **E-26** — `-Uninstall` saca los `.py` y los dos shims, y deja `harness.config.json` y los
  backups. · rojo visto: no consta
- **E-27** — La compuerta se mantiene: si los hooks no responden bien, `install.ps1` falla y
  revierte. · rojo visto: no consta

### Fuentes y encoding

- **E-28** — Ningún `.py` del harness lleva BOM, y el test de encoding lo verifica. Los `.ps1`
  que quedan siguen exigiendo BOM si tienen acentos: la regla se aplica por extensión.
  · rojo visto: no consta

### Latencia

- **E-29** — El p50 de `pre-tool-use` sobre `tests/payloads/pre-tool-use-write.json` queda por
  debajo de **400 ms**, el umbral que fijó el plan original. Se mide con el mismo método que dio
  981 ms en PowerShell, y el número medido se anota en la nota de versión.
  · rojo visto: no consta

## Cómo se verifica

E-01 a E-19, E-28 y E-29 son Python y van en `tests/casos/*.py`, con los payloads reales que ya
están en `tests/payloads/`.

E-20 a E-27 tocan `install.ps1`, que sigue en PowerShell: van en `tests/casos/03-instalador.ps1`,
que se queda donde está.

**E-01 y E-16 son la red de seguridad y se escriben primero.** Son los dos que comparan contra la
implementación actual, así que se construyen mientras la versión PowerShell todavía existe y
puede producir la tabla esperada. Portar los hooks antes que ellos es quedarse sin testigo.

## Riesgos conocidos

- **Que compilen no es que se comporten igual.** Las 27 regex compilan bajo `re` —verificado el
  15-08-2026— pero .NET y Python difieren en detalles: cuantificadores perezosos anidados,
  `\b` con no-ASCII, el significado de `$` frente a un salto de línea final. E-01 es la defensa,
  y por eso enumera casos en vez de comparar motores en abstracto.
- **Python no está en la máquina de alguien del equipo.** Deja el harness sin guardas, que es el
  peor modo de falla porque es silencioso. Mitigación: `-Doctor` falla claro, `install.ps1` no
  instala, y el shim —si el `python.exe` fijado desapareció— tiene que fallar ruidosamente en
  vez de salir 0 en silencio.
- **El port arrastra un defecto sin que nadie lo vea.** Es el precio de exigir paridad: si el
  check de accesibilidad tiene hoy un falso negativo, mañana lo tiene igual. Aceptado a
  propósito; se separa el port del arreglo para que cada diff diga una sola cosa.
- **La suite queda en dos lenguajes.** Dos formas de escribir un test conviviendo invitan a que
  la de PowerShell se pudra. Mitigación: lo único que queda en PowerShell es
  `03-instalador.ps1`, y queda porque testea un script que también se queda.
- **Ganancia menor a la medida.** Los 335 ms salen de un prototipo, no del port completo:
  `post-tool-use` carga además todos los checks. El número de E-29 es sobre `pre-tool-use`, que
  es el que corre en cada tool call; si `post-tool-use` no baja parecido, se anota y se decide
  aparte.
