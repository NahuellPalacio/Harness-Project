# Contrato de hooks

Todo lo que hay que saber para escribir un hook del harness. Verificado punta a punta
por `tests\casos\02_hook_contrato.py`.

Desde 0.13.0 los hooks corren en **Python 3.9+**. El contrato de fondo —tres salidas,
salida 0 siempre, silencio cuando no hay nada que decir— no cambió: cambió el lenguaje
y, con él, las trampas.

## Entrada

Claude Code invoca el hook como un proceso del sistema y le pasa **un objeto JSON por
stdin**. Campos comunes a todos los eventos:

```jsonc
{
  "session_id": "...",
  "transcript_path": "C:\\...\\transcript.jsonl",
  "cwd": "C:\\Work\\GCBA\\IGE",
  "hook_event_name": "PostToolUse"
}
```

Y según el evento:

| Evento | Campos propios |
|---|---|
| `SessionStart` | `source` — `startup` / `resume` / `clear` / `compact` |
| `UserPromptSubmit` | `prompt` |
| `PreToolUse` | `tool_name`, `tool_input` |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_response` |

**La forma de `tool_input` cambia según la herramienta.** `Write` trae `file_path` y
`content`; `Edit` trae `old_string` y `new_string`; `Bash` trae `command`. Por eso nunca
se accede a una propiedad directamente: se usa `campo(evento, ruta, default)`, en
`comun/hooks/lib/hook.py`, que devuelve un default en vez de explotar.

Hay payloads reales de cada evento en `tests\payloads\`.

## Salida — tres formas, y solo tres

### 1. Silencio

El caso normal, y el que hay que optimizar. Sin hallazgos, el hook no escribe nada y
sale con código 0. Costo en contexto: cero.

Esto importa más de lo que parece: `PostToolUse` corre después de **cada** escritura de
**cada** sesión. Un hook que siempre dice algo se vuelve ruido de fondo que nadie lee.

### 2. Avisar

```python
avisar("PostToolUse", "[ES0903] `/api/usuario` usa singular y no versiona. Debe ser `/api/v1/users`.")
```

Inyecta el texto en el contexto de Claude sin interrumpir nada. Claude lo lee y corrige
en el turno siguiente. **Es la forma normal de comunicar un incumplimiento.**

> ⚠️ **Solo funciona en `PostToolUse`, `UserPromptSubmit` y `SessionStart`.** En
> `PreToolUse`, la salida en caso de éxito va a la transcripción y el modelo no la ve.
> Por eso **todos los avisos del harness se entregan en `PostToolUse`**, aunque el
> problema se pudiera detectar antes: `pre-tool-use.py` solo importa `bloquear` y
> `preguntar` de `lib.hook`, nunca `avisar`.
>
> 📌 **Esto es una convención del código de los hooks, no algo que la biblioteca
> impida.** `avisar()` no valida el evento que recibe: si un hook nuevo la llama desde
> `PreToolUse`, corre sin error y el texto se pierde en la transcripción sin que nadie
> lo note. Quedó anotado como algo a decidir —si vale la pena que `lib.hook` lo
> rechace en vez de solo documentarlo— y este es el lugar donde se deja dicho.

### 3. Bloquear

```python
bloquear("PreToolUse", "Literal con forma de client_secret. Usá una variable de entorno.")
```

Impide que la herramienta se ejecute. **Reservado exclusivamente a la regla de
secretos.** Ninguna otra regla del harness bloquea.

El motivo se le muestra a Claude, así que tiene que decir **qué hacer**, no qué se
impidió. `usá una variable de entorno` sirve; `operación denegada` no.

Existe una cuarta función, `preguntar`, para la confianza media del detector de
secretos: emite `permissionDecision: ask` y deja la decisión en manos de la persona.

## Cómo se escribe un hook

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, avisar, campo

def cuerpo(e):
    ruta = campo(e, "tool_input.file_path", "")
    if not ruta.endswith(".md"):
        return                      # salir temprano es gratis

    # ... verificar algo ...

    if hay_hallazgo:
        avisar("PostToolUse", mensaje)

invoke_hook("PostToolUse", cuerpo)
```

`invoke_hook` se encarga de leer stdin, forzar el encoding, atrapar cualquier excepción
y garantizar salida con código 0. **Un hook roto nunca rompe la sesión de nadie**: se
reporta una vez con `mensaje_de_sistema` y se calla hasta el próximo reinicio (una
marca en `%TEMP%/gcba-harness/`, por `session_id` y evento).

Un check —una regla, no infraestructura— se escribe distinto: un `.py` en el
directorio de checks con una sola función.

```python
def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada uno es un hallazgo."""
    return []
```

Se descubre por estar en el directorio, igual que antes: no hace falta registrarlo en
ningún lado. `lib/reglas.py` los carga todos, en orden alfabético, corta en 8 hallazgos
y saltea en silencio el que tire una excepción.

## Portabilidad — tres capas, con dos lanzadores

```
.claude\settings.json          → "$CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd" post-tool-use
                                  (o run-hook.sh en Linux/macOS/WSL)
                                  nunca contiene una ruta absoluta
.claude\harness\run-hook.cmd   → fija el python.exe REAL de ESTA máquina
.claude\harness\run-hook.sh    → invoca "python3" del sistema, genérico
                                  único par de artefactos dependiente del equipo
                                  (el .cmd). Los dos gitignoreados
.claude\harness\hooks\*.py     → la lógica, Python 3.9+
```

`install.ps1` resuelve el intérprete con `sys.executable`, no con lo primero que
encuentre en el `PATH`: en una máquina con un shim de PyManager delante, invocar
`python` a secas cuesta **260 ms** de más en cada hook (547 ms el shim, 284 ms el
`.exe` directo). `run-hook.cmd` fija esa ruta absoluta; es, igual que antes, el único
artefacto de todo el harness instalado que depende de la máquina.

`run-hook.sh` es genérico a propósito —"exec python3 ..."— y sale de una plantilla
versionada, `comun/settings/run-hook.sh.plantilla`, en vez de un heredoc en
`install.ps1`: así nace con LF fijo por `.gitattributes` (`*.sh text eol=lf`) y no
depende de que nadie recuerde no tocarle los saltos de línea. Un `.sh` con CRLF falla
con *"bad interpreter"*, un error que no menciona en ningún momento su causa real.

```bat
@echo off
"C:\...\python.exe" "%~dp0hooks\%1.py"
```
```sh
#!/bin/sh
exec python3 "$(dirname "$0")/hooks/$1.py"
```

## Las trampas de Python

Cinco, todas verificadas en el cambio `hooks-en-python` y ninguna teórica: cada una
rompió algo durante el port antes de quedar escrita acá.

### 1. `-I` (aislado) rompe el import ✅ *verificado*

Recorta el arranque del intérprete apenas **6 ms** —ruido, frente a los ~400 ms que ya
cuesta arrancar Python en esta clase de máquina— y a cambio implica `-P`, que saca el
directorio del script de `sys.path`. Eso rompe cualquier `sys.path.insert(...)` seguido
de `from lib.hook import ...` de una forma que se descubre recién cuando un hook no
arranca en la máquina de otro. Comprobado sobre 3.13.14:

```
sin flags   -> import OK
-I          -> import FALLA: No module named 'lib'
-I -S       -> import FALLA
-P          -> import FALLA
```

No se paga una trampa por 6 ms. Los shims no llevan `-I` ni `-S`.

### 2. `ensure_ascii=False`, o los acentos llegan escapados ✅ *verificado*

El default de `json.dumps` escapa todo lo que no sea ASCII: un aviso con `versión`
sale como `"versi\u00f3n"`. Es JSON válido y Claude Code lo puede leer, pero es el
tipo de detalle que nadie nota hasta que alguien lee el aviso crudo en la
transcripción y no entiende el escape. `_emitir`, en `lib/hook.py`, pasa
`ensure_ascii=False` siempre.

### 3. La salida se escribe como bytes UTF-8 al buffer, no con `print` ✅ *verificado, nos mordió en la Task 2*

`sys.stdout.write(texto)` en Windows sale codificado en la codepage de la consola
—cp1252 casi siempre—, y un texto con tildes se corrompe o directamente tira una
excepción de encoding, según el carácter. `_emitir` esquiva la consola por completo:
codifica a UTF-8 a mano y escribe al **buffer binario**, `sys.stdout.buffer.write(...)`.

```python
crudo = json.dumps(objeto, ensure_ascii=False, separators=(",", ":"))
sys.stdout.buffer.write(crudo.encode("utf-8"))
```

El test que cubre esto corre a propósito con `PYTHONIOENCODING=cp1252`: es la única
forma de reproducir el bug sin depender de la codepage de quien corre la suite ese
día.

### 4. `utf-8-sig` al leer stdin ✅ *verificado*

Un BOM al inicio del JSON que llega por stdin, sin descartar, hace que
`json.loads` falle con un "JSON no válido" que no menciona el BOM en ningún lado —el
síntoma no delata la causa. `leer_evento()` decodifica con `"utf-8-sig"`, que descarta
el BOM si está y no hace nada si no está.

### 5. Los checks se cargan por ruta, no por nombre de módulo ✅ *verificado*

El contrato es *"un `.py` en el directorio de checks, y con eso alcanza"*: agregar una
regla no exige registrarla en ningún lado. Pero los checks se llaman
`claude-md-zonas.py`, `dev-api-rutas.py`, con guiones — y un guion no es un nombre de
módulo importable por `import`.

`lib/reglas.py` los carga con `importlib.util.spec_from_file_location`, que acepta
cualquier nombre de archivo. El descubrimiento sigue siendo *estar en el directorio*,
y el nombre del check sigue siendo el que se lee en un aviso.

Contrato del check, antes y después:

```powershell
param($Evento, $Proyecto, $Config)   ->   devuelve cero o mas strings
```
```python
def verificar(evento, proyecto, config) -> list[str]
```

## Correr los tests

```powershell
.\tests\Invoke-Tests.ps1
.\tests\Invoke-Tests.ps1 -Detallado
```

Un solo comando, dos motores adentro: `03-instalador.ps1` y el resto de lo que sigue
en PowerShell corren primero, después se delega a `python tests/correr.py`, y los dos
conteos se suman en un único código de salida — 0 si pasa todo, 1 si falla algo en
cualquiera de los dos.

Para iterar sobre los hooks sin esperar la parte de `install.ps1` —que tarda decenas de
minutos—, `python tests/correr.py` solo corre en segundos.

`install.ps1` usa `Invoke-Tests.ps1` como compuerta: **si los hooks no responden bien,
la instalación falla y revierte.** Un hook roto es peor que ningún hook, porque falla
en silencio.
