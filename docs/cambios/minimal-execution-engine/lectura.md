# Lectura de ME-E50 — `minimal-execution-engine`

> ✅ **FIRMADA el 13-10-2026** por Nahuel Palacio, por firma dictada (ver abajo): ME-E50 queda
> `leído`, y `leído` vale menos que `sostenido`. Hasta esa firma estuvo `sin sustento`, y el cambio no
> cerraba. **Un papel vacío no es una lectura.**
>
> 📌 **Evidencia preparada para reverificación.** Quien construyó corrió el Claude Code real con la
> estrategia de la enmienda (spec §34) y dejó lo que vio abajo, en «Evidencia preparada». Eso **no**
> es una lectura: una corrida de quien construyó no firma ME-E50.

**Quién puede firmar:** cualquiera **menos quien construyó**. Es un solo escenario de lectura: la
firma delegada de [ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md) no
aplica, y se firma `Leyó:`, nunca `Firmó (delegado):`. Si se dicta, quien construyó solo transcribe.

**Qué es esto:** la vía que [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
define para un escenario cuyo sujeto es una corrida de un modelo: acá, una corrida real de
`ejecutar` contra Claude Code. La suite prueba el motor contra lo que la spec supone del Host, con un
Host falso; esta lectura mira al Host.

**Qué NO es:** una prueba. Un `leído` cierra un cambio y vale menos que un `sostenido`.

**Historia:** la primera versión de este archivo describía `--agent` y un `PROVIDER_FAILURE` por
`error.type`. La refutación del 09-10-2026 mostró que con `--agent` el Host no devuelve
`structured_output` y que un error del proveedor no trae `error.type` (spec §34.1). Este archivo
describe la forma implementada después de la enmienda.

## Cómo se llena

1. Armar el proyecto de prueba (abajo) en una carpeta temporal, fuera de este repositorio, o mirar
   los dos que quedaron de la evidencia preparada.
2. Correr `ejecutar` desde una terminal, no desde una sesión de Claude Code.
3. Contrastar lo que se ve contra cada punto de ME-E50, con la spec al lado (§34.2 a §34.4).
4. Escribir en `Observado` qué se vio, no si estaba bien.
5. Firmar abajo, con fecha y nombre.

### Cómo lanza el adaptador al Host

Los argumentos de MD-08′ (spec §34.3), sin `--agent`:

```
claude -p --output-format json --json-schema <AgentReport> --session-id <uuid>
  --permission-mode dontAsk --permission-prompts none
  --system-prompt-file .claude/ejecuciones/<KEY>/<executionId>/prompt-de-sistema.md
  --tools <conjunto de la unidad> --allowedTools <el mismo> --strict-mcp-config
  [--model <perfil del tier>]
stdin = el prompt, cwd = la raíz del proyecto
```

El AgentReport sale de `structured_output` y de ningún otro lado: `result` no se lee.

### El proyecto de prueba

Un proyecto instalado con `install.ps1`, **sin** `ejecucion.comandoHost` —así el motor usa `claude`
del `PATH`— y con `modelRouting.perfiles.low_cost` en `haiku` para que cueste poco. Encima, con los
ayudantes de `tests/casos/64_modelo_de_dominio.py`: un repositorio git con `origin` en la URL de la
Ficha, el TaskContext `GCBA-72`, las capacidades y una propuesta.

```powershell
$proy = Join-Path $env:TEMP ('me50-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory $proy | Out-Null
Set-Content (Join-Path $proy 'CLAUDE.md') '# Proyecto de prueba'
.\install.ps1 -Project $proy -Usuario '<quien lee>'
```

```python
import importlib.util, json, subprocess, sys
from pathlib import Path
proy = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("m64", "tests/casos/64_modelo_de_dominio.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
git = lambda *a: subprocess.run(["git", "-C", str(proy), "-c", "user.email=t@t", "-c", "user.name=t"] + list(a), check=True)
m._escribir(proy / "src" / "app.py", "def sumar(a, b):\n    return a + b\n")
git("init", "-q"); git("add", "-A"); git("commit", "-q", "-m", "inicial")
git("remote", "add", "origin", m.URL_DEL_REPO + ".git")
m._json(proy / ".claude" / "contextos" / "GCBA-72.json", m._contexto("GCBA-72", True))
m._json(proy / ".claude" / "harness.capacidades.json", {"capacidades": m.REGISTRO})
# backend: una unidad que se puede hacer, una que no, y una para el error del proveedor
m._json(proy / "prop-1.json", m._propuesta([
    m._unidad("analizar-api", objective="Leer src/app.py y describir en dos lineas que hace la funcion sumar. No cambiar ningun archivo."),
    m._unidad("unidad-bloqueada", objective="Esta unidad no se puede completar: falta la especificacion del endpoint. El agente tiene que declarar BLOCKED y decir que falta."),
    m._unidad("falla-proveedor", objective="Leer src/app.py y resumirlo en una linea.")]))
# calidad, en otro proyecto igual: el dominio quality no tiene requiredChecks
# m._json(proy / "prop-1.json", m._propuesta([m._unidad("revisar-calidad", dominio="quality",
#     objective="Revisar src/app.py y decir en una linea si la funcion sumar tiene tests. No cambiar ningun archivo.")],
#     dominios=("quality",)))
```

### El comando

```powershell
$cli = Join-Path $proy '.claude\harness\bin\desarrollo\dev-harness.py'
python $cli plan GCBA-72 --propuesta prop-1.json --proyecto $proy
python $cli ejecutar GCBA-72 --unidad analizar-api --json --proyecto $proy
```

Para el error del proveedor, antes de `ejecutar ... --unidad falla-proveedor`: poner en
`.claude\harness.config.json` `modelRouting.perfiles.low_cost` en un modelo que no existe.

El resultado queda en `.claude\ejecuciones\GCBA-72\<executionId>\`: `request.json`, `entrega.json`,
`prompt-de-sistema.md`, `output.md` si hubo un AgentReport válido, y `result.json`. `host.sessionRef`
del resultado es el `session_id` de la sesión del Host, y la transcripción queda en
`~\.claude\projects\<carpeta del proyecto>\<sessionRef>.jsonl`.

### Para ver qué herramientas ofrece la sesión, y la salida cruda

El motor no guarda el stdout del Host, y `--output-format json` no trae el conjunto de herramientas.
Las dos cosas se ven repitiendo a mano la entrega de una Execution, con los argumentos que arma el
adaptador sobre su `request.json`. Los dos scripts están en `%TEMP%\me50-lectura\scripts\`:

```powershell
# el mensaje init: cambia solo --output-format json por stream-json --verbose
python repeticion_init.py <proyecto> <executionId> <sufijo>
# la salida cruda, con los argumentos exactos y el perfil del harness.config.json
python repeticion_cruda.py <proyecto> <executionId> <archivo de salida>
```

Cada repetición es una sesión más del Host: no escribe en el registro de la Execution.

## Evidencia preparada

Del 09-10-2026, Claude Code `2.1.295`, Windows 11, el modelo `haiku` (que el Host resolvió a
`claude-haiku-5-5`), con el adaptador final. El motor no guarda el costo; cada repetición a mano
costó entre USD 0,0047 y 0,0059, y el error del proveedor, 0.

| Corrida | Unidad | Agente | Exit | `status` | `error.code` | `agentDeclaredStatus` | `validar_resultado` | `requestFingerprint` = huella de `request.json` | Herramientas usadas |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `analizar-api` | `dev-backend` | 2 | `FAILED` | `AGENT_DECLARED_NOT_COMPLETE` | `PARTIAL` | `[]` | sí | `Read`, `StructuredOutput` |
| 1 | `unidad-bloqueada` | `dev-backend` | 2 | `FAILED` | `AGENT_DECLARED_NOT_COMPLETE` | `BLOCKED` | `[]` | sí | `Glob`, `Grep`, `StructuredOutput` |
| 1 | `falla-proveedor` | `dev-backend` | 2 | `FAILED` | `PROVIDER_FAILURE` | — | `[]` | sí | ninguna |
| 2 | `revisar-calidad` | `dev-quality` | 0 | `SUCCEEDED` | — | `COMPLETE` | `[]` | sí | `Glob`, `Grep`, `Read`, `StructuredOutput` |

- **El `PARTIAL` de `analizar-api`** es del agente: `dev-backend` declara `PARTIAL` cuando no corrió
  los `requiredChecks` de su unidad. Por eso el `SUCCEEDED` está en una unidad de calidad, cuyo
  dominio no tiene `requiredChecks`.
- **El vínculo:** en las cuatro, `.claude\runtime\sessions\<sessionRef>\task.json` existe con
  `taskKey: GCBA-72`, `source: user-prompt`, y su `sessionId` es el `host.sessionRef` del resultado.
- **El prompt de sistema:** `prompt-de-sistema.md` empieza con `# Agent: dev-backend` (corrida 1) y
  `# Agent: dev-quality` (corrida 2).
- **El prompt:** el primer mensaje de usuario de cada transcripción es `Seguimos con GCBA-72.`,
  seguido de la WorkUnit en JSON.
- **Las herramientas que ofrece la sesión** (repetición de `analizar-api` con `repeticion_init.py`):
  `init.tools` = `Glob, Grep, Read, Skill, StructuredOutput`; `--tools` y `--allowedTools` =
  `Read,Glob,Grep,Skill`; `permission_denials: []`; `structured_output` con `artifact` y
  `declaredStatus`, y `validar_informe` = `[]`. Sin `--strict-mcp-config` la misma sesión ofrecía
  además las ocho `mcp__claude_ai_Claude_Docs__*` de la cuenta (spec §34.2, E9): es lo que hizo
  sumar esa bandera.
- **El error del proveedor, crudo** (repetición con `repeticion_cruda.py`): exit `1`,
  `type: result`, `subtype: success`, `is_error: true`, `api_error_status: 404`,
  `terminal_reason: api_error`, sin `error`; stderr
  `[claude-code:unrecognized_model] {"model":"claude-modelo-inexistente-me50","query_source":"sdk"}`.
  El `detail` del `result.json`:
  `el proveedor fallo (subtype=success, codigo de salida 1) · terminal_reason=api_error · api_error_status=404 · stderr: [claude-code:unrecognized_model] {...}`.

**Dónde está** (se puede borrar después de firmar):

| Qué | Ruta |
|---|---|
| Proyecto de la corrida 1 | `%TEMP%\me50-real-4qshkfzd` |
| Proyecto de la corrida 2 | `%TEMP%\me50-real-s6qnzf2h` |
| Resúmenes, stdout y stderr de cada `ejecutar`, salida cruda del proveedor | `%TEMP%\me50-lectura\corrida-1\`, `corrida-2\` |
| `init` de la sesión con el adaptador final | `%TEMP%\me50-lectura\repeticion-init-adaptador-final.json` |
| Discovery E1 a E10 de §34.2 | `%TEMP%\me50-lectura\discovery\` |
| Scripts que lo produjeron | `%TEMP%\me50-lectura\scripts\` |
| Transcripciones | `~\.claude\projects\C--Users-204350-1-AppData-Local-Temp-me50-real-4qshkfzd\` y `...-me50-real-s6qnzf2h\` |

---

**Leyó:** Nahuel Palacio · **Fecha:** 13-10-2026 · **Corrida sobre:** la evidencia de la
reverificación del 13-10-2026 (`verificacion.md`, «Reverificación post-corrección»): once corridas
reales de `ejecutar` con Claude Code `2.1.296`, sobre dos proyectos de prueba en `%TEMP%`
(`ref2-me50-dca12ce4` y `ref2-long-01a6f898`); la firma es de quien leyó esa evidencia

---

## ME-E50 — Una corrida real de `ejecutar` contra Claude Code, con la estrategia de §34.3, sobre un proyecto de prueba con unidades de backend y de calidad, termina terminal y cada `result.json` pasa `validar_resultado`

Qué mirar, tomado de la spec (§34.4):

1. **Que el prompt llega por stdin.** El primer mensaje de usuario de la transcripción empieza con
   `Seguimos con GCBA-72.` y trae la WorkUnit de la Execution.
2. **Que el agente se materializa.** `prompt-de-sistema.md` del registro es el cuerpo de
   `.claude\agents\<assignedAgent>.md` sin su frente, y el `artifact` responde como ese agente.
3. **Que llega un AgentReport estructurado.** En la salida cruda, `structured_output` con
   `declaredStatus` y `artifact`, y nada más; en el registro, `output.md` presente.
4. **Que `declaredStatus` y el artifact están.** `agentDeclaredStatus` y `output` en `result.json`, y
   la huella de `output` es la de `output.md`.
5. **Que las herramientas quedan restringidas.** El `init.tools` de la sesión es el conjunto de la
   unidad más `StructuredOutput`, sin herramientas MCP; las usadas en la transcripción están dentro
   de ese conjunto, y `permission_denials` está vacío.
6. **SessionTaskBinding.** `.claude\runtime\sessions\<sessionRef>\task.json` con `GCBA-72`, escrito
   por el hook UserPromptSubmit del propio Host, y la compuerta del flujo sin
   `SESSION_TASK_AMBIGUOUS`.
7. **`sessionRef`.** El `session_id` de la sesión es el `host.sessionRef` del resultado.
8. **Un error del proveedor.** Qué `subtype`, código de salida, `terminal_reason` y
   `api_error_status` da, y que el `result.json` dice `PROVIDER_FAILURE`.
9. **`SUCCEEDED` con `COMPLETE`.** Una Execution que termina así.
10. **`FAILED` con `AGENT_DECLARED_NOT_COMPLETE`.** Una unidad que el agente declara `PARTIAL` o
    `BLOCKED`.
11. **`result.json` válido.** `validar_resultado(result, request)` vacío en cada una, y su
    `requestFingerprint` igual a la huella de su `request.json`.

**Observado:**

> Firma dictada. Nahuel Palacio dictó lo que sigue el 13-10-2026; quien construyó solo lo
> transcribió, textual y sin editar el sentido.

```
Se revisó la evidencia de ME-E50 y se confirmó que la estrategia vigente del Host Adapter,
sin --agent y con --system-prompt-file + --json-schema, produce structured_output real con
declaredStatus y artifact; que las tools de la sesión quedan restringidas según la WorkUnit;
que SessionTaskBinding y host.sessionRef coinciden; y que los errores reales de proveedor
se clasifican como PROVIDER_FAILURE. Los result.json observados validan contra el contrato.
```
