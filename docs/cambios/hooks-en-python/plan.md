# Plan de implementación — hooks, checks y tests en Python

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portar los cuatro hooks, los cinco checks y la suite de tests de PowerShell a Python conservando el comportamiento exacto, y bajar el hook que corre en cada tool call de 981 ms a menos de 400 ms.

**Architecture:** El shim `run-hook.cmd` deja de invocar `powershell.exe` y pasa a invocar el `python.exe` real que `install.ps1` resuelve y fija al instalar. La lógica vive en `comun/hooks/lib/*.py` como biblioteca estándar pura. `install.ps1` se queda en PowerShell —es el bootstrap— y consume la lógica de zonas invocando `zonas.py` y leyendo JSON por stdout, el mismo patrón que ya usa `comun/bin/docimg.py`.

**Tech Stack:** Python 3.9+ (solo `json`, `re`, `importlib`, `pathlib`, `sys`, `os`, `unicodedata`). Windows PowerShell 5.1 para `install.ps1` y un único caso de test. Sin `pip`, sin `pwsh`, sin Pester.

**Spec:** [`docs/cambios/hooks-en-python/spec.md`](spec.md)

## Global Constraints

Copiadas literalmente de la spec. Los requisitos de cada tarea las incluyen implícitamente.

- **Python mínimo 3.9**, declarado en `comun/manifest.json` como `requierePython: "3.9"`.
- **Biblioteca estándar y nada más.** Ninguna dependencia de `pip`. `json`, `re`, `importlib`, `pathlib` alcanzan.
- **Paridad de comportamiento, no rediseño.** El catálogo de patrones, los techos de zona, los umbrales y los mensajes salen idénticos. Si un check tiene hoy un defecto, se porta con el defecto.
- **`install.ps1` se queda en PowerShell.** No se toca su rol de bootstrap.
- **El shim se invoca sin `-I` ni `-S`.** Recortan 6 ms y rompen `import lib.hook`.
- **La resolución del intérprete y toda llamada a `zonas.py` viven adentro de las rutas de `-Instalar` y `-Update`, nunca en el nivel superior de `install.ps1`.**
- **Ningún `.py` del harness lleva BOM.** Los `.ps1` que quedan siguen exigiendo BOM si tienen acentos.
- **Un hook jamás rompe la sesión.** Ante cualquier excepción, `systemMessage` una vez por sesión y salida con código 0.
- **Silencio es silencio.** Sin hallazgos, stdout queda vacío.
- **Todo el texto que ve una persona va en español**, igual que hoy.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `comun/hooks/lib/hook.py` | El contrato: leer stdin, las tres salidas, salir 0 siempre, `systemMessage` una vez por sesión |
| `comun/hooks/lib/secretos.py` | Detector de secretos. Puerto exacto de `Secretos.psm1` |
| `comun/hooks/lib/reglas.py` | Descubrir y correr checks, con el tope de 8 hallazgos |
| `comun/hooks/lib/zonas.py` | Zonas del `CLAUDE.md`: lectura, medición, y los verbos de línea de comandos |
| `comun/hooks/pre-tool-use.py` | Bloqueo de secretos, y nada más |
| `comun/hooks/post-tool-use.py` | Corre los checks y entrega los hallazgos |
| `comun/hooks/session-start.py` | El saludo: quién sos, git, caché, definiciones pendientes |
| `comun/hooks/user-prompt-submit.py` | Mudo, igual que hoy |
| `comun/checks/claude-md-zonas.py` | Puerto del check de zonas |
| `harnesses/desarrollo/checks/lib/dev.py` | Puerto de `Dev.psm1` |
| `harnesses/desarrollo/checks/dev-*.py` | Puerto de los cuatro checks de desarrollo |
| `comun/settings/run-hook.sh.plantilla` | Shim POSIX |
| `tests/correr.py` | Runner de la suite Python |
| `tests/casos/*.py` | Los casos portados |
| `tests/fixtures/paridad-secretos.json` | **El testigo.** Veredictos de la implementación PowerShell |
| `tests/fixtures/paridad-checks.json` | **El testigo.** Hallazgos de los cinco checks PowerShell |

---

## Task 1: El testigo — capturar los veredictos de la implementación actual

Es la tarea que hace segura toda la migración, y sólo se puede hacer ahora: captura lo que la
implementación PowerShell responde, mientras todavía existe. Portar antes que esto es quedarse
sin nada contra qué comparar.

**Files:**
- Create: `tests/generar-testigo.ps1`
- Create: `tests/fixtures/corpus-secretos.txt`
- Create: `tests/fixtures/claude-md-de-prueba.md`
- Create: `tests/fixtures/paridad-secretos.json`
- Create: `tests/fixtures/paridad-checks.json`
- Create: `tests/fixtures/paridad-zonas.json`

**Interfaces:**
- Consumes: nada.
- Produces: tres JSON con esta forma exacta, que consumen las tareas 3, 6 y 7.

```jsonc
// paridad-secretos.json
{ "generado": "0.12.0",
  "casos": [ { "texto": "Server=srv01;...;Password=Tr4ns4cc10n;",
               "hallazgo": true, "id": "password-en-cadena-de-conexion",
               "confianza": "alta", "muestra": "Password=Tr4... (20 caracteres)" },
             { "texto": "password = ${DB_PASSWORD}", "hallazgo": false } ] }

// paridad-checks.json
{ "generado": "0.12.0",
  "casos": [ { "check": "claude-md-zonas",
               "ruta": "comun/checks/claude-md-zonas.ps1",
               "payload": "post-tool-use-write.json",
               "proyecto": "<ruta del proyecto de fixture>",
               "config": { "techoZonaFija": 60 },
               "hallazgos": ["texto exacto del hallazgo"] } ] }

// paridad-zonas.json
{ "generado": "0.12.0",
  "archivo": "tests/fixtures/claude-md-de-prueba.md",
  "zonas": { "ZONA FIJA": 12, "ZONA MAPA": 3, "ZONA INDICE": 0, "ZONA CACHE": 7 },
  "fueraDeZonas": 4 }
```

📌 **`ruta` y `config` en `paridad-checks.json` no son decorativos:** el test de la tarea 7 carga
el módulo por esa ruta y le pasa esa config. Sin los dos campos, el caso no se puede reproducir.

- [ ] **Step 1: Escribir el corpus a un archivo**

Todas las cadenas que hoy prueba `tests/casos/04-secretos.ps1` — las de `Assert-Detecta` y las
de `Assert-NoDetecta`— más las de `tests/payloads/`. Son 31 y están todas en literales.

Van a `tests/fixtures/corpus-secretos.txt`, **una cadena por línea, en UTF-8 sin BOM**. Es el
archivo que lee el generador del paso 2, y además deja a la vista qué se probó.

Armar también `tests/fixtures/claude-md-de-prueba.md`: un `CLAUDE.md` con las cuatro zonas, algo
de contenido en cada una y algunas líneas fuera de toda zona, para que las mediciones del testigo
de zonas no sean todas cero.

- [ ] **Step 2: Escribir el generador**

```powershell
# tests/generar-testigo.ps1 — corre la implementacion PowerShell y guarda sus veredictos.
# Se corre UNA vez, antes de portar nada. Su salida es el testigo contra el que se compara
# la implementacion Python.
param([string] $Salida = (Join-Path $PSScriptRoot 'fixtures\paridad-secretos.json'))

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..\comun\hooks\lib\Hook.psm1')     -Force
Import-Module (Join-Path $PSScriptRoot '..\comun\hooks\lib\Secretos.psm1') -Force

$catalogo = Import-PatronesSecretos -Ruta (Join-Path $PSScriptRoot '..\comun\reglas\secretos.patrones.json')
$corpus   = Get-Content (Join-Path $PSScriptRoot 'fixtures\corpus-secretos.txt') -Encoding UTF8

$casos = foreach ($t in $corpus) {
    if (-not $t) { continue }
    $h = Find-Secreto -Texto $t -Catalogo $catalogo
    if ($null -eq $h) {
        [ordered]@{ texto = $t; hallazgo = $false }
    } else {
        [ordered]@{ texto = $t; hallazgo = $true; id = $h.Id; confianza = $h.Confianza; muestra = $h.Muestra }
    }
}

$doc = [ordered]@{ generado = (Get-Content (Join-Path $PSScriptRoot '..\VERSION') -Raw).Trim(); casos = @($casos) }
[System.IO.File]::WriteAllText($Salida, (ConvertTo-Json $doc -Depth 10), (New-Object System.Text.UTF8Encoding $false))
Write-Host "testigo escrito: $Salida ($($casos.Count) casos)"
```

- [ ] **Step 3: Correr el generador y revisar el resultado a ojo**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\generar-testigo.ps1`
Expected: escribe el JSON e informa 31 casos. Abrirlo y confirmar que los `hallazgo: true` son
los que hoy bloquean y los `false` los placeholders. **Un testigo mal capturado convierte toda
la migración en una mentira verificada**, así que este paso se mira, no se saltea.

- [ ] **Step 4: Capturar el testigo de los checks**

Mismo procedimiento con `Invoke-Checks`, corriendo los cinco checks contra un proyecto de
fixture y los payloads de `tests/payloads/`, y guardando el texto exacto de cada hallazgo, con
la `ruta` del check y la `config` que se le pasó.

- [ ] **Step 5: Capturar el testigo de zonas**

Sobre `tests/fixtures/claude-md-de-prueba.md`, con `Measure-Zonas` y `Measure-FueraDeZonas` de
`Zonas.psm1`. Es el mismo motivo que los otros dos: se toma ahora, con la implementación
PowerShell viva.

- [ ] **Step 6: Verificar que los tres testigos tienen contenido**

```powershell
Get-ChildItem tests\fixtures\paridad-*.json | ForEach-Object {
    $d = Get-Content $_.FullName -Raw | ConvertFrom-Json
    "{0}: {1}" -f $_.Name, (@($d.casos).Count)
}
```
Expected: `paridad-secretos.json` con 31 casos, `paridad-checks.json` con al menos uno por
check, y `paridad-zonas.json` con las cuatro zonas y un `fueraDeZonas` distinto de cero.
**Un testigo vacío pasa todos los tests que lo consumen y no prueba nada.**

- [ ] **Step 7: Commit**

```bash
git add tests/generar-testigo.ps1 tests/fixtures/
git commit -m "El testigo: los veredictos de la implementacion PowerShell, capturados antes de portarla"
```

---

## Task 2: `lib/hook.py` — el contrato

**Files:**
- Create: `tests/correr.py` (versión mínima — ver Step 0)
- Create: `comun/hooks/lib/__init__.py` (vacío)
- Create: `comun/hooks/lib/hook.py`
- Test: `tests/casos/01_hook_lib.py`

**Interfaces:**
- Consumes: nada.
- Produces, y todo lo demás se apoya en esto:

```python
def leer_evento() -> dict | None
def campo(evento, ruta: str, default=None)
def avisar(evento_nombre: str, texto: str) -> None
def bloquear(evento_nombre: str, motivo: str) -> None
def preguntar(evento_nombre: str, motivo: str) -> None
def mensaje_de_sistema(texto: str, session_id: str = "sin-sesion", clave: str = "general") -> None
def invoke_hook(evento_nombre: str, cuerpo) -> None   # no retorna: termina con sys.exit(0)
```

- [ ] **Step 0: El runner mínimo, porque todo lo que sigue lo invoca**

Todas las tareas de acá en adelante verifican con `python tests/correr.py`, así que existe desde
ahora. Mínimo y sin dependencias: descubre `tests/casos/*.py`, importa cada uno por ruta,
corre las funciones que empiezan con `test_` pasándoles el objeto `t`, y sale 0 si pasa todo.

```python
# tests/correr.py — sin dependencias: no hace falta pytest ni nada instalado.
import argparse, importlib.util, sys, traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class Resultados:
    def __init__(self):
        self.filas = []          # (grupo, nombre, ok, detalle)
        self.grupo = "(sin grupo)"

    def _add(self, nombre, ok, detalle=""):
        self.filas.append((self.grupo, nombre, ok, detalle))

    def igual(self, nombre, esperado, obtenido):
        self._add(nombre, esperado == obtenido,
                  "" if esperado == obtenido else "esperado <%r> / obtenido <%r>" % (esperado, obtenido))

    def contiene(self, nombre, aguja, pajar):
        self._add(nombre, aguja in (pajar or ""), "" if aguja in (pajar or "") else "no contiene <%s>" % aguja)

    def no_contiene(self, nombre, aguja, pajar):
        self._add(nombre, aguja not in (pajar or ""), "" if aguja not in (pajar or "") else "contiene <%s>" % aguja)

    def vacio(self, nombre, valor):
        self._add(nombre, not valor, "" if not valor else "no esta vacio: <%r>" % (valor,))

    def verdadero(self, nombre, condicion):
        self._add(nombre, bool(condicion), "" if condicion else "es falso")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", default="")
    ap.add_argument("--detallado", action="store_true")
    args = ap.parse_args()

    t = Resultados()
    casos = sorted((RAIZ / "tests" / "casos").glob("*.py"))
    if args.k:
        casos = [c for c in casos if args.k in c.name]

    for caso in casos:
        t.grupo = caso.stem
        spec = importlib.util.spec_from_file_location("caso_" + caso.stem, caso)
        modulo = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(modulo)
        except Exception:
            t._add("el archivo de casos se pudo cargar", False, traceback.format_exc(limit=3))
            continue
        for nombre in sorted(dir(modulo)):
            if not nombre.startswith("test_"):
                continue
            try:
                getattr(modulo, nombre)(t)
            except Exception:
                t._add(nombre, False, traceback.format_exc(limit=3))

    fallaron = [f for f in t.filas if not f[2]]
    grupos = {}
    for grupo, nombre, ok, detalle in t.filas:
        g = grupos.setdefault(grupo, [0, 0])
        g[0] += 1
        if ok:
            g[1] += 1
    print("\ngcba-harness - tests (python)\n")
    for grupo, (total, ok) in grupos.items():
        estado = "OK   " if total == ok else "FALLA"
        print("  %s %s  (%d)" % (estado, grupo, total))
    for grupo, nombre, ok, detalle in t.filas:
        if not ok or args.detallado:
            print("    %s %s / %s %s" % ("ok " if ok else "MAL", grupo, nombre, detalle))
    print("\n%d/%d pasaron." % (len(t.filas) - len(fallaron), len(t.filas)))
    sys.exit(1 if fallaron else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 1: Escribir los tests que fallan**

```python
# tests/casos/01_hook_lib.py
import json, subprocess, sys, os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import hook   # noqa: E402


def test_campo_devuelve_default_si_falta(t):
    e = {"tool_input": {"file_path": "a.md"}}
    t.igual("E-09 ruta presente", "a.md", hook.campo(e, "tool_input.file_path", ""))
    t.igual("E-09 ruta ausente", "", hook.campo(e, "tool_input.content", ""))
    t.igual("E-09 rama inexistente", "", hook.campo(e, "no.existe.nada", ""))
    t.igual("E-09 evento None", "", hook.campo(None, "tool_input.file_path", ""))


def test_avisar_no_escapa_no_ascii(t):
    salida = _correr("hook-eco.py", {"session_id": "s", "prompt": "definición"})
    t.contiene("E-10 tilde intacta", "definición", salida)
    t.no_contiene("E-10 sin \\u", "\\u00f3", salida)


def test_silencio_es_silencio(t):
    salida = _correr("hook-silencio.py", {"session_id": "s"})
    t.igual("E-12 stdout vacio", "", salida)
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python tests/correr.py -k hook_lib`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.hook'`

- [ ] **Step 3: Escribir `lib/hook.py`**

```python
"""Infraestructura de hooks del harness GCBA.

Las cuatro cosas que son identicas en los cuatro eventos y que, hechas mal, fallan
en silencio: encoding, lectura del evento por stdin, las tres unicas salidas validas,
y el control de errores. Un hook JAMAS rompe la sesion.
"""
import json
import os
import re
import sys
import tempfile

DIR_ESTADO = os.path.join(tempfile.gettempdir(), "gcba-harness")


def leer_evento():
    """Lee el JSON de stdin. Devuelve None si vino vacio.

    Se lee del buffer binario y se decodifica con utf-8-sig: si el BOM viene, se
    descarta en vez de romper el parseo.
    """
    crudo = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
    if not crudo.strip():
        return None
    return json.loads(crudo)


def campo(evento, ruta, default=None):
    """Lee una propiedad anidada sin explotar si no existe.

    La forma de tool_input cambia segun la herramienta, asi que el acceso directo
    no sirve: Write trae file_path y content, Edit trae old_string y new_string.
    """
    actual = evento
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return default
        actual = actual[parte]
    return default if actual is None else actual


def _emitir(objeto):
    # ensure_ascii=False: sin esto un aviso con tilde llega escapado al contexto.
    sys.stdout.write(json.dumps(objeto, ensure_ascii=False, separators=(",", ":")))


def avisar(evento_nombre, texto):
    """AVISA: inyecta texto en el contexto sin interrumpir nada."""
    if not texto or not texto.strip():
        return
    _emitir({"hookSpecificOutput": {
        "hookEventName": evento_nombre, "additionalContext": texto}})


def bloquear(evento_nombre, motivo):
    """BLOQUEA. Reservado a la regla de secretos: es lo unico que el harness impide."""
    _emitir({"hookSpecificOutput": {
        "hookEventName": evento_nombre,
        "permissionDecision": "deny", "permissionDecisionReason": motivo}})


def preguntar(evento_nombre, motivo):
    """PREGUNTA: lo ambiguo lo decide la persona, no el harness."""
    _emitir({"hookSpecificOutput": {
        "hookEventName": evento_nombre,
        "permissionDecision": "ask", "permissionDecisionReason": motivo}})


def mensaje_de_sistema(texto, session_id="sin-sesion", clave="general"):
    """Avisa de un problema del propio harness, una sola vez por sesion y evento."""
    try:
        os.makedirs(DIR_ESTADO, exist_ok=True)
        seguro = re.sub(r"[^A-Za-z0-9._-]", "_", "%s.%s" % (session_id, clave))
        marca = os.path.join(DIR_ESTADO, seguro + ".avisado")
        if os.path.exists(marca):
            return
        open(marca, "w").close()
    except OSError:
        # Si no se puede escribir la marca se avisa igual: perder el aviso es peor
        # que repetirlo.
        pass
    _emitir({"systemMessage": texto})


def invoke_hook(evento_nombre, cuerpo):
    """Envoltorio de todo hook. Garantiza salida 0 pase lo que pase."""
    evento = None
    session_id = "sin-sesion"
    try:
        evento = leer_evento()
        if evento is None:
            sys.exit(0)
        session_id = campo(evento, "session_id", "sin-sesion")
        cuerpo(evento)
    except SystemExit:
        raise
    except BaseException as e:            # noqa: BLE001 - a proposito: nada escapa
        mensaje_de_sistema(
            "harness: fallo el hook %s (%s). Se omite hasta el proximo reinicio."
            % (evento_nombre, e),
            session_id=session_id, clave=evento_nombre)
    sys.exit(0)
```

- [ ] **Step 4: Portar los fixtures de hook**

`tests/fixtures/hook-eco.ps1`, `hook-silencio.ps1`, `hook-deny.ps1` y `hook-explota.ps1` pasan a
`.py` sobre `invoke_hook`. Son de 4 a 6 líneas cada uno.

- [ ] **Step 5: Correr y verificar que pasa**

Run: `python tests/correr.py -k hook_lib`
Expected: PASS, incluidos E-06, E-07, E-08, E-09, E-10, E-11 y E-12.

- [ ] **Step 6: Commit**

```bash
git add comun/hooks/lib/hook.py comun/hooks/lib/__init__.py tests/casos/01_hook_lib.py tests/fixtures/
git commit -m "El contrato de hooks en Python: tres salidas, salida 0 siempre"
```

---

## Task 3: `lib/secretos.py` contra el testigo

**Files:**
- Create: `comun/hooks/lib/secretos.py`
- Test: `tests/casos/04_secretos.py`

**Interfaces:**
- Consumes: `lib.hook.campo`.
- Produces:

```python
def importar_patrones(ruta: str) -> dict
def valor_de_asignacion(coincidencia: str) -> str
def es_valor_ignorable(valor: str, catalogo: dict) -> bool
def muestra_segura(valor: str) -> str
def texto_de_herramienta(evento) -> str
def buscar_secreto(texto: str, catalogo: dict) -> dict | None
    # -> {"id":..., "confianza": "alta"|"media", "motivo":..., "muestra":...} o None
```

- [ ] **Step 1: Escribir el test de paridad, que es el que importa**

```python
# tests/casos/04_secretos.py
def test_paridad_con_powershell(t):
    """E-01 — mismo veredicto que la implementacion PowerShell, caso por caso."""
    testigo = json.loads((RAIZ / "tests/fixtures/paridad-secretos.json").read_text("utf-8"))
    catalogo = secretos.importar_patrones(str(RAIZ / "comun/reglas/secretos.patrones.json"))

    for caso in testigo["casos"]:
        h = secretos.buscar_secreto(caso["texto"], catalogo)
        etiqueta = "E-01 " + caso["texto"][:40]
        if not caso["hallazgo"]:
            t.igual(etiqueta + " (no debe disparar)", None, h)
            continue
        t.verdadero(etiqueta + " (debe disparar)", h is not None)
        t.igual(etiqueta + " id", caso["id"], h["id"])
        t.igual(etiqueta + " confianza", caso["confianza"], h["confianza"])
        t.igual(etiqueta + " muestra", caso["muestra"], h["muestra"])


def test_secreto_entre_comillas_invertidas(t):
    """E-05 — el caso que rompio la escritura de docs/versiones/0.4.0.md: un relleno
    obvio entre delimitadores de codigo markdown se bloqueaba como credencial real."""
    catalogo = secretos.importar_patrones(str(RAIZ / "comun/reglas/secretos.patrones.json"))
    t.igual("E-05 relleno entre backticks",
            None, secretos.buscar_secreto("`password = xxxxxxxx`", catalogo))


def test_catalogo_compila(t):
    """E-02 — sobre el catalogo real, no sobre una copia."""
    cat = json.loads((RAIZ / "comun/reglas/secretos.patrones.json").read_text("utf-8"))
    for p in cat["patrones"]:
        try:
            re.compile(p["regex"])
            t.verdadero("E-02 compila " + p["id"], True)
        except re.error as e:
            t.verdadero("E-02 compila %s -> %s" % (p["id"], e), False)
    for i, r in enumerate(cat["ignorar"]["patrones"]):
        try:
            re.compile(r)
            t.verdadero("E-02 compila ignorar[%d]" % i, True)
        except re.error as e:
            t.verdadero("E-02 compila ignorar[%d] -> %s" % (i, e), False)
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python tests/correr.py -k secretos`
Expected: FAIL — `No module named 'lib.secretos'`

- [ ] **Step 3: Escribir `lib/secretos.py`**

Puerto literal de `Secretos.psm1`. Los cuatro puntos donde un port descuidado cambia el
comportamiento:

```python
def valor_de_asignacion(coincidencia):
    """De "password = xxxxx" devuelve "xxxxx". Si no hay asignacion, devuelve todo.

    Entre los delimitadores que se descartan esta la comilla invertida, y no es
    estilo: es el delimitador de codigo de markdown. Sin eso, documentar el propio
    detector lo dispara. Paso al escribir docs/versiones/0.4.0.md.
    """
    m = re.search(r"[:=]\s*[\"'`]?\s*(.+?)\s*[\"'`]?\s*$", coincidencia)
    return m.group(1) if m else coincidencia


def es_valor_ignorable(valor, catalogo):
    """Se prueba contra el valor aislado Y contra la coincidencia entera: hay
    patrones de ignorar anclados al valor (^x{3,}$) y otros que aparecen en
    cualquier lado (process.env)."""
    if not valor or not valor.strip():
        return True
    aislado = valor_de_asignacion(valor)
    if not aislado or not aislado.strip():
        return True
    for p in catalogo["ignorar"]["patrones"]:
        if re.search(p, aislado) or re.search(p, valor):
            return True
    return False


def muestra_segura(valor):
    """Describe el hallazgo sin repetir el secreto: entra al contexto de Claude y
    queda en la transcripcion."""
    limpio = re.sub(r"\s+", " ", valor).strip()
    if len(limpio) <= 12:
        return limpio[:4] + "..."
    return "%s... (%d caracteres)" % (limpio[:12], len(limpio))


def buscar_secreto(texto, catalogo):
    """Los de confianza alta primero: si hay uno, gana sobre cualquier ambiguo."""
    if not texto or not texto.strip():
        return None
    for nivel in ("alta", "media"):
        for patron in catalogo["patrones"]:
            if patron.get("confianza") != nivel:
                continue
            m = re.search(patron["regex"], texto)
            if not m:
                continue
            if es_valor_ignorable(m.group(0), catalogo):
                continue
            return {"id": patron["id"], "confianza": patron["confianza"],
                    "motivo": patron["motivo"], "muestra": muestra_segura(m.group(0))}
    return None
```

`texto_de_herramienta` junta `content`, `new_string`, `command`, `new_source` y `prompt`, y
además recorre `tool_input.edits` para MultiEdit, igual que la versión PowerShell.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python tests/correr.py -k secretos`
Expected: PASS en los 31 casos del testigo y en las 27 regex.
**Si un caso no coincide, se arregla el port, nunca el testigo.**

- [ ] **Step 5: Commit**

```bash
git add comun/hooks/lib/secretos.py tests/casos/04_secretos.py
git commit -m "Detector de secretos en Python, con paridad verificada caso por caso"
```

---

## Task 4: `pre-tool-use.py`

**Files:**
- Create: `comun/hooks/pre-tool-use.py`
- Test: `tests/casos/02_hook_contrato.py`

**Interfaces:**
- Consumes: `lib.hook.invoke_hook`, `lib.secretos.buscar_secreto`.
- Produces: el primer hook completo, invocable como `python comun/hooks/pre-tool-use.py < payload.json`.

- [ ] **Step 1: Escribir el test punta a punta**

```python
def test_deny_con_secreto_alto(t):
    """E-03 — confianza alta -> deny."""
    payload = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": "a.cs",
                              "content": 'var cs = "Server=s;Password=Tr4ns4cc10n;";'}}
    salida = json.loads(_correr("pre-tool-use.py", payload))
    hs = salida["hookSpecificOutput"]
    t.igual("E-03 deny", "deny", hs["permissionDecision"])
    t.contiene("E-03 dice que hacer", "archivo externo al codigo", hs["permissionDecisionReason"])


def test_placeholder_no_dispara(t):
    """E-04 — ${DB_PASSWORD} no es un secreto."""
    payload = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": "a.cs", "content": "password = ${DB_PASSWORD}"}}
    t.igual("E-04 silencio", "", _correr("pre-tool-use.py", payload))
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python tests/correr.py -k hook_contrato`
Expected: FAIL — el archivo no existe.

- [ ] **Step 3: Escribir el hook**

```python
# PreToolUse — EXCLUSIVAMENTE el bloqueo de secretos. Nada mas entra aca.
#   1. Es la puerta: una sola cosa la cruza.
#   2. Avisar desde aca no sirve: en exito la salida va a la transcripcion.
#   3. Latencia: dispara antes de cada llamada. Cada regla de mas se paga siempre.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, bloquear, preguntar          # noqa: E402
from lib.secretos import importar_patrones, buscar_secreto, texto_de_herramienta  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))


def cuerpo(e):
    texto = texto_de_herramienta(e)
    if not texto.strip():
        return
    catalogo = importar_patrones(os.path.join(AQUI, "..", "reglas", "secretos.patrones.json"))
    h = buscar_secreto(texto, catalogo)
    if h is None:
        return
    mensaje = "%s [%s: %s]" % (h["motivo"], h["id"], h["muestra"])
    if h["confianza"] == "alta":
        bloquear("PreToolUse", mensaje)
    else:
        # Ambiguo: decide la persona. Bloquear de mas es como se pierde un harness.
        preguntar("PreToolUse", mensaje)


invoke_hook("PreToolUse", cuerpo)
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python tests/correr.py -k hook_contrato`
Expected: PASS.

- [ ] **Step 5: Medir, y anotar el número**

```powershell
$py = (python -c "import sys; print(sys.executable)")
$p  = Get-Content .\tests\payloads\pre-tool-use-write.json -Raw
$ms=@(); 1..14 | % { $w=[Diagnostics.Stopwatch]::StartNew(); $p | & $py .\comun\hooks\pre-tool-use.py | Out-Null; $w.Stop(); $ms+=$w.Elapsed.TotalMilliseconds }
"p50 = {0:N0} ms" -f ($ms|Sort-Object)[7]
```
Expected: por debajo de 400 ms (E-29). El PowerShell equivalente daba 981 ms.

- [ ] **Step 6: Commit**

```bash
git add comun/hooks/pre-tool-use.py tests/casos/02_hook_contrato.py
git commit -m "pre-tool-use en Python: de 981 ms a <400, con el mismo veredicto"
```

---

## Task 5: `lib/reglas.py` — descubrir y correr checks

**Files:**
- Create: `comun/hooks/lib/reglas.py`
- Test: `tests/casos/06_reglas.py`

**Interfaces:**
- Consumes: nada de tareas previas.
- Produces:

```python
MAX_HALLAZGOS = 8
def config_proyecto(proyecto: str) -> dict | None
def correr_checks(evento, dir_checks: str, proyecto: str, config) -> list[str]
```

- [ ] **Step 1: Escribir los tests**

```python
def test_descubre_por_estar_en_el_directorio(t):
    """E-13 — un .py nuevo en el directorio corre, sin registrarlo en ningun lado."""
    d = _dir_temporal_con_check("mi-check.py", 'def verificar(e, p, c): return ["hola"]')
    t.igual("E-13", ["hola"], reglas.correr_checks({}, d, "", None))


def test_un_check_roto_no_tumba_a_los_demas(t):
    """E-14 — se saltea en silencio y los otros corren igual."""
    d = _dir_temporal_con_checks({
        "a-explota.py": 'def verificar(e, p, c): raise RuntimeError("boom")',
        "b-anda.py":    'def verificar(e, p, c): return ["sigo vivo"]'})
    t.igual("E-14", ["sigo vivo"], reglas.correr_checks({}, d, "", None))


def test_tope_de_ocho(t):
    """E-15 — con mas de 8 hallazgos, se recorta."""
    d = _dir_temporal_con_check("mucho.py",
        'def verificar(e, p, c): return ["h%d" % i for i in range(20)]')
    t.igual("E-15", 8, len(reglas.correr_checks({}, d, "", None)))
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python tests/correr.py -k reglas`
Expected: FAIL — `No module named 'lib.reglas'`

- [ ] **Step 3: Escribir `lib/reglas.py`**

```python
"""Carga y ejecucion de los checks que aportan comun y los harness instalados.

Los hooks son cuatro y son infraestructura. Los checks son N y son reglas. La
separacion existe para que agregar una regla no pueda romper el manejo de stdin,
el encoding ni el control de errores.

Contrato de un check: un .py con verificar(evento, proyecto, config) que devuelve
cero o mas strings. Cada string es un hallazgo.
"""
import importlib.util
import json
import os

# Presupuesto de salida. PostToolUse corre despues de cada escritura de cada sesion:
# una tanda larga de avisos deja de leerse y el harness se vuelve ruido de fondo.
MAX_HALLAZGOS = 8


def config_proyecto(proyecto):
    if not proyecto:
        return None
    ruta = os.path.join(proyecto, ".claude", "harness.config.json")
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _cargar(ruta):
    """Por ruta y no por nombre de modulo: los checks se llaman dev-api-rutas.py y
    un guion no es un nombre importable. El descubrimiento sigue siendo estar en
    el directorio."""
    nombre = "check_" + os.path.basename(ruta).replace("-", "_")[:-3]
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def correr_checks(evento, dir_checks, proyecto, config):
    hallazgos = []
    if not dir_checks or not os.path.isdir(dir_checks):
        return hallazgos

    rutas = []
    for raiz, _dirs, archivos in os.walk(dir_checks):
        for a in archivos:
            if a.endswith(".py") and not a.startswith("__"):
                rutas.append(os.path.join(raiz, a))
    rutas.sort()

    for ruta in rutas:
        try:
            modulo = _cargar(ruta)
            salida = modulo.verificar(evento, proyecto, config)
            for s in (salida or []):
                if s and str(s).strip():
                    hallazgos.append(str(s).strip())
        except BaseException:      # noqa: BLE001
            # Un check roto se saltea en silencio. Reportarlo en cada escritura
            # seria peor que el problema que quiso evitar.
            pass
        if len(hallazgos) >= MAX_HALLAZGOS:
            break

    return hallazgos[:MAX_HALLAZGOS]
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python tests/correr.py -k reglas`
Expected: PASS en E-13, E-14 y E-15.

- [ ] **Step 5: Commit**

```bash
git add comun/hooks/lib/reglas.py tests/casos/06_reglas.py
git commit -m "Descubrimiento y corrida de checks en Python, con el tope de 8 intacto"
```

---

## Task 6: `lib/zonas.py` y sus verbos de línea de comandos

**Files:**
- Create: `comun/hooks/lib/zonas.py`
- Test: `tests/casos/09_zonas.py`

🔴 **`Zonas.psm1` NO se borra en esta tarea.** `install.ps1:58` lo importa en el nivel superior
y `03-instalador.ps1` corre en cada `Invoke-Tests`: borrarlo ahora deja la suite en rojo hasta
la Task 10, y una suite roja durante cuatro tareas deja de ser señal. Convive con `zonas.py`
hasta que el instalador deje de importarlo, y se borra en la Task 10.

**Interfaces:**
- Consumes: nada.
- Produces, para Python y para `install.ps1`:

```python
def definicion_zonas() -> list[dict]   # {"nombre","techo","que","alias":[...]}
def contenido_zona(texto: str, zona: dict) -> str | None
def a_nombre_plano(nombre: str) -> str
def marcadores_html(texto: str) -> list[dict]
def zonas_no_reconocidas(texto: str) -> list[dict]
def medir_fuera_de_zonas(texto: str) -> int
def medir_zonas(texto: str) -> list[dict]
```
```
python lib/zonas.py definicion
python lib/zonas.py contenido <archivo> <zona>
python lib/zonas.py no-reconocidas <archivo>
```

- [ ] **Step 1: Escribir el test de paridad de medición**

```python
def test_mide_igual_que_powershell(t):
    """E-19 — mismas mediciones y mismos excesos sobre el mismo CLAUDE.md."""
    testigo = json.loads((RAIZ / "tests/fixtures/paridad-zonas.json").read_text("utf-8"))
    texto = (RAIZ / "tests/fixtures/claude-md-de-prueba.md").read_text("utf-8")
    medido = {z["nombre"]: z["lineas"] for z in zonas.medir_zonas(texto)}
    for nombre, esperado in testigo["zonas"].items():
        t.igual("E-19 " + nombre, esperado, medido[nombre])
    t.igual("E-19 fuera de zonas", testigo["fueraDeZonas"], zonas.medir_fuera_de_zonas(texto))


def test_la_definicion_sale_por_json(t):
    """E-18 — el verbo que consume install.ps1."""
    salida = subprocess.run([sys.executable, str(LIB / "zonas.py"), "definicion"],
                            capture_output=True, text=True, encoding="utf-8")
    zs = json.loads(salida.stdout)
    t.igual("E-18 cuatro zonas", 4, len(zs))
    t.igual("E-18 primera", "ZONA FIJA", zs[0]["nombre"])
    t.igual("E-18 techo", "techoZonaFija", zs[0]["techo"])
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python tests/correr.py -k zonas`
Expected: FAIL — el módulo no existe. (El testigo `paridad-zonas.json` se captura como en la
tarea 1, corriendo `Measure-Zonas` de `Zonas.psm1` sobre el mismo archivo de prueba.)

- [ ] **Step 3: Portar `Zonas.psm1`**

Puerto función por función. Las dos que tienen trampa:

```python
def a_nombre_plano(nombre):
    """Normaliza para comparar: sin tildes, en mayusculas y sin el prefijo ZONA.
    Sirve para reconocer que CACHÉ y ZONA CACHE son el mismo concepto escrito
    distinto, no para decidir que es canonico."""
    descompuesto = unicodedata.normalize("NFD", nombre)
    plano = "".join(c for c in descompuesto
                    if unicodedata.category(c) != "Mn").upper().strip()
    return re.sub(r"^ZONA\s+", "", plano)


def marcadores_html(texto):
    """Un marcador puede ocupar varias lineas -ya paso- asi que no alcanza con mirar
    linea por linea: se ubican los comentarios sobre el texto completo y recien
    despues se traducen a lineas.

    El nombre se toma por lo que ES -letras, numeros, dos puntos y espacios- y no
    por el separador que venga despues: los archivos generados usan raya larga y
    una persona escribiendo a mano pone un guion comun.
    """
    marcadores = []
    if not texto:
        return marcadores
    lineas = texto.split("\n")
    inicio = []
    acum = 0
    for l in lineas:
        inicio.append(acum)
        acum += len(l) + 1

    def indice_de_linea(offset):
        for k in range(len(lineas) - 1, -1, -1):
            if offset >= inicio[k]:
                return k
        return 0

    for m in re.finditer(r"(?s)<!--.*?-->", texto):
        interior = m.group(0)[4:-3]
        primera = interior.split("\n")[0]
        nom = re.match(r"^\s*(/?)\s*([^\W_]+(?:[:\w]*)(?:\s+[^\W_][:\w]*)*)", primera, re.UNICODE)
        if not nom:
            continue
        nombre = nom.group(2).strip()
        if not nombre:
            continue
        marcadores.append({"nombre": nombre, "es_cierre": nom.group(1) == "/",
                           "linea_ini": indice_de_linea(m.start()),
                           "linea_fin": indice_de_linea(m.end() - 1)})
    return marcadores
```

Al final del archivo, los verbos:

```python
if __name__ == "__main__":
    import sys
    verbo = sys.argv[1] if len(sys.argv) > 1 else ""
    if verbo == "definicion":
        print(json.dumps(definicion_zonas(), ensure_ascii=False))
    elif verbo == "contenido":
        texto = open(sys.argv[2], encoding="utf-8-sig").read()
        zona = next(z for z in definicion_zonas() if z["nombre"] == sys.argv[3])
        print(json.dumps({"contenido": contenido_zona(texto, zona)}, ensure_ascii=False))
    elif verbo == "no-reconocidas":
        texto = open(sys.argv[2], encoding="utf-8-sig").read()
        print(json.dumps(zonas_no_reconocidas(texto), ensure_ascii=False))
    else:
        sys.stderr.write("verbo desconocido: %s\n" % verbo)
        sys.exit(2)
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python tests/correr.py -k zonas`
Expected: PASS en E-18 y E-19.

- [ ] **Step 5: Verificar E-17 — la definición vive en un solo lado**

Run: `git grep -n "techoZonaFija" -- ':!docs' ':!comun/manifest.json'`
Expected: una sola línea, en `comun/hooks/lib/zonas.py`.

- [ ] **Step 6: Commit**

```bash
git add comun/hooks/lib/zonas.py tests/casos/09_zonas.py tests/fixtures/paridad-zonas.json
git commit -m "Zonas en Python, con los verbos JSON que va a consumir el instalador"
```

---

## Task 7: Los cinco checks, contra el testigo

**Files:**
- Create: `comun/checks/claude-md-zonas.py`
- Create: `harnesses/desarrollo/checks/lib/dev.py`
- Create: `harnesses/desarrollo/checks/dev-accesibilidad-html.py`, `dev-api-rutas.py`, `dev-dependencias.py`, `dev-infra-en-codigo.py`
- Test: `tests/casos/07_checks.py`
- Delete al final: los `.ps1` equivalentes y `Dev.psm1`

**Interfaces:**
- Consumes: `lib.zonas`, `lib.reglas.correr_checks`.
- Produces: cada check expone `def verificar(evento, proyecto, config) -> list[str]`.
  `dev.py` expone `archivo_escrito(evento)`, `es_ruta_generada(ruta)`, `linea_de(texto, aguja)`
  y `formatear_lista(items)`.

- [ ] **Step 1: Escribir el test de paridad**

```python
def test_paridad_de_hallazgos(t):
    """E-16 — mismos hallazgos, texto incluido, que la version PowerShell."""
    testigo = json.loads((RAIZ / "tests/fixtures/paridad-checks.json").read_text("utf-8"))
    for caso in testigo["casos"]:
        evento = json.loads((RAIZ / "tests/payloads" / caso["payload"]).read_text("utf-8"))
        modulo = reglas._cargar(str(RAIZ / caso["ruta"]))
        obtenidos = modulo.verificar(evento, caso["proyecto"], caso.get("config"))
        t.igual("E-16 " + caso["check"], caso["hallazgos"], list(obtenidos or []))
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python tests/correr.py -k checks`
Expected: FAIL — ninguno de los `.py` existe.

- [ ] **Step 3: Portar los cinco checks, uno por uno**

Orden: `claude-md-zonas` (usa `lib.zonas`, ya portada), después `dev.py`, después los cuatro de
desarrollo. Cada uno se porta línea por línea desde su `.ps1`, **sin corregir nada**: los
umbrales, los mensajes y hasta las rarezas salen idénticos. El testigo es el juez.

Firma de cada uno:

```python
def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    return []
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python tests/correr.py -k checks`
Expected: PASS. **Si un hallazgo difiere en una coma, se arregla el port.**

- [ ] **Step 5: Commit**

```bash
git add comun/checks/ harnesses/desarrollo/checks/ tests/casos/07_checks.py
git commit -m "Los cinco checks en Python, con los hallazgos verificados contra el testigo"
```

---

## Task 8: Los tres hooks restantes

**Files:**
- Create: `comun/hooks/post-tool-use.py`, `session-start.py`, `user-prompt-submit.py`
- Test: `tests/casos/05_memoria.py`
- Delete al final: los cuatro `.ps1` de `comun/hooks/` y las cuatro `.psm1` de `lib/`

**Interfaces:**
- Consumes: `lib.hook`, `lib.reglas`, `lib.zonas`.
- Produces: los cuatro hooks completos, invocables por el shim.

- [ ] **Step 1: Escribir los tests del saludo**

```python
def test_saludo_trae_nombre_y_harness(t):
    proy = _proyecto_de_prueba(usuario="Nahue", harness=["comun", "analisis"], version="0.13.0")
    salida = json.loads(_correr("session-start.py", {"session_id": "s", "cwd": proy,
                                                     "hook_event_name": "SessionStart"}))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("saludo: nombre", "Nahue", ctx)
    t.contiene("saludo: harness", "comun, analisis v0.13.0", ctx)


def test_sin_nada_que_decir_no_dice_nada(t):
    """E-12 tambien vale para SessionStart."""
    t.igual("silencio", "", _correr("session-start.py",
            {"session_id": "s", "cwd": str(_dir_vacio()), "hook_event_name": "SessionStart"}))
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python tests/correr.py -k memoria`
Expected: FAIL — los tres archivos no existen.

- [ ] **Step 3: Portar los tres hooks**

`user-prompt-submit.py` sale mudo, igual que hoy: lee el prompt, y si no hay nada que rutear,
calla. El ruteo por disparadores de skill sigue siendo otro pendiente.

`post-tool-use.py` es el caballo de batalla:

```python
def cuerpo(e):
    proyecto = campo(e, "cwd", "")
    if not proyecto:
        return
    dir_checks = os.path.join(AQUI, "..", "checks")
    if not os.path.isdir(dir_checks):
        return
    config = config_proyecto(proyecto)
    hallazgos = correr_checks(e, dir_checks, proyecto, config)
    if not hallazgos:
        return
    avisar("PostToolUse", "\n".join(hallazgos))
```

`session-start.py` porta las cuatro secciones del saludo en el mismo orden: encabezado con
usuario y harness, estado de git y últimos tres commits, hasta cuatro líneas de la zona caché, y
la cuenta de definiciones pendientes. Presupuesto: 12 líneas.

- [ ] **Step 4: Correr la suite entera**

Run: `python tests/correr.py`
Expected: PASS.

- [ ] **Step 5: Borrar la implementación PowerShell**

```bash
git rm comun/hooks/*.ps1 comun/checks/*.ps1 \
       comun/hooks/lib/Hook.psm1 comun/hooks/lib/Secretos.psm1 comun/hooks/lib/Reglas.psm1 \
       harnesses/desarrollo/checks/*.ps1 harnesses/desarrollo/checks/lib/Dev.psm1
```

🔴 **`Zonas.psm1` queda.** Se borra en la Task 10, después de que `install.ps1` deje de
importarlo. Borrarlo acá rompe el instalador y la suite entra en rojo por cuatro tareas.

- [ ] **Step 6: Commit**

```bash
git add -A comun/hooks comun/checks harnesses tests
git commit -m "Los cuatro hooks en Python; sale la implementacion PowerShell"
```

---

## Task 9: El runner de tests

**Files:**
- Modify: `tests/correr.py` (creado mínimo en la Task 2; acá se completa)
- Modify: `tests/Invoke-Tests.ps1`
- Delete: `tests/casos/*.ps1` salvo `03-instalador.ps1` y `00-encoding-fuentes.ps1`

**Interfaces:**
- Consumes: `tests/correr.py` de la Task 2.
- Produces: `python tests/correr.py [-k <filtro>] [--detallado]`, código 0 si pasa todo.
  El objeto `t` que reciben los tests expone `igual(nombre, esperado, obtenido)`,
  `contiene(nombre, aguja, pajar)`, `no_contiene(...)`, `vacio(nombre, valor)` y
  `verdadero(nombre, condicion)` — los mismos cinco de `Invoke-Tests.ps1`.

- [ ] **Step 1: Completar `tests/correr.py`**

Ya existe desde la Task 2 con lo mínimo. Acá se le agrega lo que faltaba: `--detallado` que
imprima también los que pasaron, el corte con código 1 ante cualquier falla, y el mismo formato
de salida que la suite PowerShell —grupo, nombre, `N/M pasaron`— para que nadie tenga que
aprender a leer otra cosa.

- [ ] **Step 2: Correr y comparar contra la suite vieja**

Run: `python tests/correr.py`
Expected: la misma cantidad de aserciones que reportaba la suite PowerShell para los casos
portados. Si son menos, falta un caso.

- [ ] **Step 3: Hacer que `Invoke-Tests.ps1` delegue**

`Invoke-Tests.ps1` sigue siendo el comando y la compuerta de `install.ps1`. Adentro corre
`03-instalador.ps1` y `00-encoding-fuentes.ps1` en PowerShell, invoca `python tests/correr.py`,
suma las dos cuentas y devuelve 0 sólo si las dos pasaron.

- [ ] **Step 4: Verificar**

Run: `.\tests\Invoke-Tests.ps1`
Expected: PASS, con el total sumado de los dos motores.

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "Un solo comando de tests, dos motores adentro"
```

---

## Task 10: `install.ps1` — intérprete, shims y zonas por JSON

Es la tarea con más riesgo de romper el diagnóstico, así que E-23 y E-23b se escriben primero.

**Files:**
- Modify: `install.ps1:47-58` (sacar el import del nivel superior), `New-Shim`, `Test-Entorno`, y los puntos donde se usaban `Get-DefinicionZonas` y `Get-ContenidoZona`
- Create: `comun/settings/run-hook.sh.plantilla`
- Modify: `comun/manifest.json` (campo `requierePython`)
- Test: `tests/casos/03-instalador.ps1`

**Interfaces:**
- Consumes: `python lib/zonas.py definicion|contenido|no-reconocidas`.
- Produces: `Resolve-Python` devuelve la ruta del `python.exe` real o `$null`;
  `Get-ZonasPorJson` devuelve la definición parseada.

- [ ] **Step 1: Escribir los tests de `-Doctor`, que son los que protegen el diagnóstico**

```powershell
Set-Grupo 'Instalador - Doctor sin Python'

# E-23: -Doctor imprime su diagnostico completo aunque el interprete no este.
$salida = & powershell -NoProfile -ExecutionPolicy Bypass -Command {
    $env:PATH = 'C:\no-existe'          # ningun python alcanzable
    & "$using:raiz\install.ps1" -Doctor 2>&1 | Out-String
}
Assert-Contiene 'E-23 imprime el diagnostico' 'PowerShell'      $salida
Assert-Contiene 'E-23 reporta la falta'       'Python'          $salida
Assert-Contiene 'E-23 dice que hacer'         'instala'         $salida

# E-23b: ninguna invocacion en el nivel superior del script.
$hasta = (Select-String -Path "$raiz\install.ps1" -Pattern '^function ' | Select-Object -First 1).LineNumber
$cabecera = (Get-Content "$raiz\install.ps1" -TotalCount $hasta) -join "`n"
Assert-Vacio 'E-23b sin zonas.py en el nivel superior' `
    (($cabecera | Select-String -Pattern 'zonas\.py|Resolve-Python') -join '')
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `.\tests\Invoke-Tests.ps1`
Expected: FAIL en E-23 (todavía no hay chequeo de Python) y en E-23b (la línea 58 sigue arriba).

- [ ] **Step 3: Sacar la dependencia del nivel superior**

Borrar `install.ps1:56-58`. Agregar, dentro de las rutas de instalar y actualizar:

```powershell
function Resolve-Python {
    <#
    .SYNOPSIS
        Devuelve la ruta del python.exe REAL, o $null.
    .DESCRIPTION
        Se pide sys.executable y no se usa lo que haya en el PATH: en una maquina con
        PyManager, `python` es un shim que cuesta 260 ms de mas en CADA hook (547 ms
        contra 284 del .exe directo).
    #>
    foreach ($c in @('python', 'py', 'python3')) {
        try {
            $ruta = (& $c -c "import sys; print(sys.executable)" 2>$null)
            if ($ruta -and (Test-Path $ruta)) { return $ruta.Trim() }
        } catch { }
    }
    return $null
}
```

- [ ] **Step 4: Agregar el chequeo a `Test-Entorno`, con su test**

Reporta `ok` con la versión, o `falla` con instrucciones. `Test-Entorno` **no** ejecuta código
Python del harness: sólo `-c "import sys; print(sys.version_info[:2])"`.

```powershell
# E-24: un Python anterior al minimo del manifiesto es una falla, no un aviso.
$hallazgos = Test-Entorno -PythonSimulado '3.6'
$falla = @($hallazgos | Where-Object { $_.Nivel -eq 'falla' -and $_.Texto -match 'Python' })
Assert-Igual    'E-24 falla con 3.6'      1       $falla.Count
Assert-Contiene 'E-24 dice cual es el minimo' '3.9' $falla[0].Texto
```

- [ ] **Step 5: Reescribir `New-Shim` y agregar el shim POSIX**

```powershell
$cmd = @"
@echo off
rem Generado por install.ps1 del harness GCBA. Se regenera en cada -Update.
rem Es el unico archivo del harness que contiene una ruta absoluta de esta maquina.
"$python" "%~dp0hooks\%1.py"
"@
```

El `.sh` va con LF y bit de ejecución donde el sistema lo soporte:

```sh
#!/bin/sh
# Generado por install.ps1 del harness GCBA. Se regenera en cada -Update.
exec python3 "$(dirname "$0")/hooks/$1.py"
```

Y su test, porque un `.sh` con CRLF falla con `bad interpreter` y el mensaje no menciona en
ningún momento los finales de línea:

```powershell
# E-22: el shim POSIX se genera, va con LF y .gitattributes no lo convierte.
$sh = "$proy\.claude\harness\run-hook.sh"
Assert-Verdadero 'E-22 existe'        (Test-Path $sh)
$bytes = [System.IO.File]::ReadAllBytes($sh)
Assert-Igual     'E-22 ningun CR'     0 (@($bytes | Where-Object { $_ -eq 13 }).Count)
Assert-Contiene  'E-22 invoca python3' 'python3' ([System.IO.File]::ReadAllText($sh))
```

- [ ] **Step 6: Reemplazar los usos de `Zonas.psm1`**

Los tres puntos que usaban `Get-DefinicionZonas`, `Get-ContenidoZona` y
`Find-ZonasNoReconocidas` pasan a invocar `zonas.py` y parsear su JSON. Si la invocación falla,
se aborta con el mensaje del error: no se instala un `CLAUDE.md` a medias (E-20).

Recién ahora, con el último consumidor migrado, se borra el módulo que las tareas 6 y 8 dejaron
a propósito:

```bash
git rm comun/hooks/lib/Zonas.psm1
```

- [ ] **Step 7: Correr los tests**

Run: `.\tests\Invoke-Tests.ps1`
Expected: PASS, incluidos E-20 a E-24, E-26 y E-27.

- [ ] **Step 8: Instalar de verdad en un proyecto de prueba**

```powershell
.\install.ps1 -Project $env:TEMP\proy-prueba -Harness analisis,desarrollo -Usuario 'Prueba'
Get-Content $env:TEMP\proy-prueba\.claude\harness\run-hook.cmd
```
Expected: el shim tiene una ruta a un `python.exe` que existe, y no dice `powershell.exe`.

Y su aserción, que es E-21 — el shim tiene que llevar el `.exe` resuelto y **no** la palabra
`python` suelta, que sería el shim de PyManager y volvería a costar los 260 ms:

```powershell
# E-21: el shim fija el interprete real, no lo busca en el PATH.
$txt = [System.IO.File]::ReadAllText("$proy\.claude\harness\run-hook.cmd")
Assert-Vacio     'E-21 sin powershell' (($txt | Select-String 'powershell\.exe') -join '')
Assert-Contiene  'E-21 con .exe'       '.exe' $txt
$exe = ([regex]::Match($txt, '"([^"]+\.exe)"')).Groups[1].Value
Assert-Verdadero 'E-21 el .exe existe'      (Test-Path $exe)
Assert-Verdadero 'E-21 no es el shim suelto' ($exe -notmatch '\\PyManager\\')
```

- [ ] **Step 9: Commit**

```bash
git add install.ps1 comun/settings/ comun/manifest.json tests/casos/03-instalador.ps1
git commit -m "El instalador fija el python.exe real y deja de depender de Python para diagnosticar"
```

---

## Task 11: `-Update` sin huérfanos

**Files:**
- Modify: `install.ps1`, función `Invoke-Actualizar`
- Test: `tests/casos/03-instalador.ps1`

**Interfaces:**
- Consumes: `Resolve-Python` de la tarea 10.
- Produces: nada nuevo hacia afuera.

- [ ] **Step 1: Escribir el test**

```powershell
# E-25: tras actualizar desde una version con hooks .ps1, no queda ninguno.
$proy = New-ProyectoDePrueba
& "$raiz\install.ps1" -Project $proy -Harness analisis -Usuario 'Prueba' | Out-Null
New-Item -ItemType File -Path "$proy\.claude\harness\hooks\pre-tool-use.ps1" -Force | Out-Null
& "$raiz\install.ps1" -Project $proy -Update | Out-Null

$huerfanos = @(Get-ChildItem "$proy\.claude\harness" -Recurse -Filter '*.ps1' -ErrorAction SilentlyContinue)
Assert-Igual 'E-25 sin .ps1 huerfanos' 0 $huerfanos.Count
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `.\tests\Invoke-Tests.ps1`
Expected: FAIL — el `.ps1` plantado sigue ahí después del `-Update`.

- [ ] **Step 3: Implementar la limpieza**

Antes de copiar, `-Update` borra de `.claude\harness\` lo que figuraba en el lockfile anterior y
ya no está en el manifiesto nuevo. No borra `harness.config.json` ni `.harness-backup\`.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `.\tests\Invoke-Tests.ps1`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add install.ps1 tests/casos/03-instalador.ps1
git commit -m "-Update limpia lo que la version anterior dejo y el manifiesto nuevo ya no tiene"
```

---

## Task 12: El test de encoding, dado vuelta

**Files:**
- Modify: `tests/casos/00-encoding-fuentes.ps1`
- Modify: `scripts/Repair-EncodingFuentes.ps1`

**Interfaces:**
- Consumes: nada.
- Produces: nada nuevo.

- [ ] **Step 1: Escribir el test**

```powershell
# E-28: los .py del harness NO llevan BOM. Los .ps1 que quedan si, cuando tienen acentos.
$conBom = @(Get-ChildItem $raiz -Recurse -Filter '*.py' -File |
            Where-Object { $_.FullName -notmatch '\\tests\\out\\' } |
            Where-Object {
                $b = [System.IO.File]::ReadAllBytes($_.FullName)
                $b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF })
Assert-Igual 'E-28 ningun .py con BOM' 0 $conBom.Count
```

- [ ] **Step 2: Correr y verificar que pasa o falla según corresponda**

Run: `.\tests\Invoke-Tests.ps1`
Expected: PASS si el port se escribió bien; si falla, hay un `.py` guardado con BOM y se
corrige con `Repair-EncodingFuentes.ps1`, que se extiende para quitarlo en `.py`.

- [ ] **Step 3: Commit**

```bash
git add tests/casos/00-encoding-fuentes.ps1 scripts/Repair-EncodingFuentes.ps1
git commit -m "El test de encoding, dado vuelta: los .py no llevan BOM"
```

---

## Task 13: `-Doctor` mide la latencia

**Files:**
- Modify: `install.ps1`, función `Invoke-Doctor`
- Test: `tests/casos/03-instalador.ps1`

**Interfaces:**
- Consumes: `Resolve-Python`.
- Produces: `Measure-LatenciaHook` devuelve el p50 en milisegundos.

- [ ] **Step 1: Escribir el test**

```powershell
# E-25b: -Doctor reporta el p50 de un hook y avisa si pasa los 400 ms. Nunca bloquea.
$salida = & "$raiz\install.ps1" -Doctor 2>&1 | Out-String
Assert-Contiene 'E-25b reporta latencia' 'latencia de hook' $salida
Assert-Igual    'E-25b no bloquea'       0                  $LASTEXITCODE
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `.\tests\Invoke-Tests.ps1`
Expected: FAIL — `-Doctor` no dice nada de latencia.

- [ ] **Step 3: Implementar la medición**

Cinco corridas de `pre-tool-use.py` sobre `tests/payloads/pre-tool-use-write.json`, se reporta
el p50. Si no hay Python, no mide y no falla por eso: ya lo reportó el chequeo del intérprete.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `.\tests\Invoke-Tests.ps1`
Expected: PASS, y el `-Doctor` real imprime un p50 por debajo de 400 ms.

- [ ] **Step 5: Commit**

```bash
git add install.ps1 tests/casos/03-instalador.ps1
git commit -m "-Doctor mide la latencia del hook: el numero que justifica el cambio queda vigilado"
```

---

## Task 14: Documentación y versión 0.13.0

**Files:**
- Modify: `docs/contrato-hooks.md`, `docs/instalacion.md`, `README.md`, `UPGRADE.md`, `VERSION`
- Create: `docs/versiones/0.13.0.md`
- Modify: `docs/versiones/README.md`, `CHANGELOG.md`
- Modify: `Pendientes/Fix-Harness/PENDIENTES-FH.md`

**Interfaces:**
- Consumes: los números medidos en las tareas 4 y 13.
- Produces: nada de código.

- [ ] **Step 1: Reescribir `docs/contrato-hooks.md`**

Sobre el contrato nuevo. Las cinco trampas cambian: se van las tres de PowerShell 5.1 —BOM,
`InputEncoding`, `-NoProfile`— y entran las de Python: `-I` rompe el import, `ensure_ascii=False`
o los acentos llegan escapados, `utf-8-sig` al leer stdin, y los checks se cargan por ruta
porque su nombre lleva guiones.

- [ ] **Step 2: Actualizar requisitos en `README.md` y `docs/instalacion.md`**

Python 3.9 entra en las dos tablas de requisitos. La fila de "Los hooks se lanzan con
`powershell.exe`: todavía no hay shim `.sh`" se va: ahora lo hay.

- [ ] **Step 3: Escribir `docs/versiones/0.13.0.md`**

Con el p50 medido antes y después, y los pendientes que cierran: la latencia sin medir, el shim
`.sh` que faltaba, y `-Doctor` que no medía latencia.

- [ ] **Step 4: Nota de migración en `UPGRADE.md`**

Rompe el contrato de checks y suma un requisito. Quien tenga el harness instalado corre
`-Update`; quien haya escrito un check propio en `.ps1` tiene que portarlo.

- [ ] **Step 5: Sacar de `PENDIENTES-FH.md` lo que cerró**

Se van "`-Doctor` does not measure hook latency" y "There is no `.sh` shim". El de la nota de
versión de la distribución también, si ya se escribió la 0.13.0.

- [ ] **Step 6: Subir `VERSION` a `0.13.0` y correr todo**

Run: `.\tests\Invoke-Tests.ps1`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "0.13.0: los hooks corren en Python, y el .sh que faltaba"
```

---

## Verificación final

Antes de dar el cambio por cerrado:

```powershell
.\tests\Invoke-Tests.ps1                                    # todo verde, dos motores
.\install.ps1 -Doctor                                       # p50 por debajo de 400 ms
.\install.ps1 -Project C:\Work\GCBA\IGE -Update             # el proyecto real
```

Y el escenario que ningún test cubre: **abrir una sesión de Claude Code en un proyecto con el
harness instalado y comprobar que el saludo aparece, que un secreto se bloquea y que un aviso
con tildes llega con las tildes puestas.** La suite verifica los hooks contra payloads; que
Claude Code los invoque bien es otra cosa, y se mira con los ojos.

El veredicto del refutador va en `docs/cambios/hooks-en-python/verificacion.md`, que es lo que
cierra el cambio según ADR-0006.
