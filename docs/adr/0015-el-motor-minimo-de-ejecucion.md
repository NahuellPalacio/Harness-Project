---
estado: aceptada
creado: 2026-10-08
---

# ADR-0015 — El motor mínimo de ejecución

## Contexto

ADR-0014 dejó un contrato de ejecución verificado y nada que lo produzca: `execution-request/1.0` y
`execution-result/1.0` existían y nadie escribía ninguno; la regla de admisión de quince condiciones
estaba escrita y ningún código la aplicaba; la reserva atómica de la `idempotencyKey` era obligatoria
y no tenía mecanismo; y el AgentReport era el único contrato de salida, sin un Host Adapter que lo
armara.

Mientras tanto, la única forma de que un especialista trabajara una WorkUnit era que el modelo de una
sesión de Claude Code lo delegara con la herramienta `Agent`: sin admisión, sin identidad, sin
evidencia y sin resultado registrado.

El relevamiento y el diseño están en `docs/cambios/minimal-execution-engine/spec.md` (Task 4), con 27
contradicciones numeradas `ME-nn`. Las que pesan en estas decisiones:

- **el modelo canónico decía que HARNESS no lanza agentes**, y un motor tiene que iniciar la corrida
  (ME-01);
- **la única primitiva de delegación, `Agent`, no la puede llamar Python y devuelve texto**: si el
  modelo de la sesión retransmitiera el resultado, podría escribir `COMPLETE` por el agente (ME-03);
- **no existía una escritura de una sola vez**: todas las atómicas del repo pisan el destino (ME-08);
- **no existía en Python una forma de saber si el motor de una Execution sigue vivo** (ME-09);
- **la compuerta normativa, llamada como en `plan`, nunca da `blocked`** (ME-05).

## Decisión

### 1. Una WorkUnit, un intento, sincrónico, por invocación de `ejecutar`

`dev-harness.py ejecutar <KEY> --unidad <id>` admite, crea la Execution, la entrega al Host, espera y
deja su resultado. El proceso que pide es el que entrega y el que espera. No hay cola, proceso de
fondo, segundo intento automático ni reanudación. Elegir la siguiente unidad, en qué orden y cuántas
a la vez, es scheduling: es de Task 5.

### 2. El registro es de archivos que se escriben una sola vez, y el estado se deriva

Cada Execution vive en `.claude/ejecuciones/<TaskKey>/<executionId>/`: `request.json`,
`entrega.json`, `cancelacion.json`, `proceso.json`, `output.md` y `result.json`. Cada uno se escribe
una sola vez, con un temporal exclusivo y `os.link`, que no reemplaza: nada se pisa nunca, ni un
resultado tardío. No hay un archivo de estado: el estado sale de cuáles existen —sin `entrega.json`
es `REQUESTED`, con ella `RUNNING`, y con `result.json` su terminal—. Un registro que no valida es
ilegible, y cuenta como abierto.

### 3. La reserva de la `idempotencyKey` son turnos de intento, creados de forma exclusiva

Cada clave tiene sus turnos, `claves/<hex>/<NNNNNN>.json`, y el turno N+1 se crea con la misma
escritura de una sola vez: dos admisiones que leyeron el mismo N compiten por el mismo archivo, y el
sistema de archivos deja ganar a una. **Una Execution existe si y solo si un turno la nombra.** La
request se escribe antes del turno, así que un turno nunca nombra una request a medio escribir. Las
dependencias y los duplicados se resuelven leyendo el último turno de una clave.

### 4. La vida del motor es un candado del sistema operativo, y nadie reanuda

El motor tiene tomado `vivo.lock` —`msvcrt.locking` en Windows, `fcntl.flock` en POSIX— desde que
crea la carpeta hasta que escribe el resultado. Si muere, el sistema suelta el candado, sin fechas
ni pids. Una `RUNNING` sin motor vivo la cierra la recuperación: `FAILED` con `HOST_INTERRUPTED`, o
`CANCELLED` si un pedido de cancelar ya estaba persistido. Una `REQUESTED` sin motor queda abierta
hasta una cancelación explícita. Nada se vuelve a entregar, y la recuperación no mata procesos por
pid. Una carpeta sin turno no es una Execution: es un residuo de la creación, y se recoge cuando su
candado está libre y pasaron diez minutos.

### 5. El Host Adapter de Claude Code lanza `claude -p` con `--agent` y salida estructurada

El adaptador lanza una sesión headless del Host con `--agent`, `--json-schema`, `--session-id`,
`--permission-mode dontAsk` y `--allowedTools` con las herramientas de las capabilities de la
unidad, nunca con `--bare` ni salteando permisos: los hooks del proyecto siguen activos. El prompt va
por stdin, y su primera línea vincula la sesión a la tarea por el hook que ya existe. **El AgentReport
sale de `structured_output`**, que valida el Host contra el schema; el `result` del Host no se lee, y
nadie interpreta texto. Lo que el adaptador no reconoce es `HOST_FAILURE`.

> 📌 **Enmendada el 09-10-2026.** Con `--agent`, el Host real no devuelve `structured_output`. El
> mecanismo de esta decisión lo reemplaza la sección «Enmienda post-refutación», abajo; el principio
> —el AgentReport sale solo de `structured_output`— queda.

### 6. La admisión lee el TaskFlowState guardado y llama a la compuerta normativa con las normas de la unidad

La admisión corre la regla de quince condiciones dos veces, al pedir y al entregar, leyendo a cada
dueño. Del flujo lee el estado guardado y su vigencia local, con el límite de diez segundos de la CLI,
y el permiso `delegationAllowed`: no reconcilia, no deriva y no escribe estado del flujo. Llama a la
compuerta normativa con las normas de la WorkUnit, así `NORMATIVE_GATE_BLOCKED` es alcanzable. Antes de
`entrega.json`, lo que falla es un rechazo con su código de admisión; después, solo un código de
corrida o `CANCELLED`.

### 7. HARNESS lanza el Host, nunca un modelo

El invariante del Host del modelo canónico pasa a decir: HARNESS no llama a ningún modelo; desde Task
4, el motor de Execution puede lanzar el Host para que corra un agente, y el agente y el modelo los
corre el Host. No hay un SDK de modelos, ni LangGraph, ni un segundo runtime de agentes.

## Consecuencias

A favor:

- El contrato de Task 3 tiene productor sin cambiar: los dos schemas y `contrato.py` son los mismos.
- La idempotencia, la atomicidad y la recuperación no dependen de fechas ni de pids, y se prueban
  con dos procesos del sistema operativo.
- El AgentReport lo valida el Host contra un schema: nadie busca un estado en Markdown.
- `install.ps1` y `manifest.json` no cambian: `bin/` se copia entero, y la configuración del motor
  son dos claves opcionales de `harness.config.json` con el default en el código.

En contra, y dicho:

- **El Host puede sobrevivir al motor.** En Windows un hijo no muere con su padre, y la recuperación
  no mata por pid. La evidencia de esa Execution queda `CHANGES_UNATTRIBUTABLE` si hubo cambios.
- **Una `REQUESTED` huérfana bloquea su clave** hasta que una persona la cancele.
- **Lo no documentado del Host** —los `subtype` de error, cómo se combinan `--agent` y
  `--allowedTools`, el prompt por stdin— lo confirma una lectura de una corrida real, ME-E50.
- **`ejecutar` no tiene clasificación propia en la política de herramientas**: desde una sesión
  interactiva pasa solo si la tarea puede avanzar.
- **`os.link` no anda en FAT ni en exFAT**: el motor no corre ahí.

## Enmienda post-refutación

**Fecha:** 09-10-2026. La refutación independiente de Task 4
(`docs/cambios/minimal-execution-engine/verificacion.md`) corrió el Claude Code real, `2.1.295`, y
contradijo el mecanismo de la decisión 5. El detalle, el discovery y las alternativas están en la
spec, §34. Lo que cambia en este ADR:

- **El agente se materializa sin `--agent`.** Con `--agent`, el Host toma las herramientas del
  `tools:` del agente y no suma `StructuredOutput`: la sesión termina `success` sin
  `structured_output`, y ninguna Execution real llega a `SUCCEEDED`. El adaptador pasa el cuerpo de
  `.claude/agents/<agente>.md` como `--system-prompt-file`, desde `prompt-de-sistema.md`, un archivo
  más del registro de la Execution escrito una sola vez.
- **Las herramientas son exactamente las de la unidad.** `--tools` y `--allowedTools` llevan el mismo
  conjunto mínimo, y `--strict-mcp-config` saca las herramientas MCP que el Host suma por su cuenta.
  El Host agrega `StructuredOutput` por `--json-schema`.
- **El proveedor se reconoce por la forma real:** `terminal_reason: "api_error"` o un
  `api_error_status`, con `subtype: "success"` y código de salida 1. No por `error.type`, que el Host
  no emite.
- **Un código de salida distinto de 0 nunca es `SUCCEEDED`**, y después de la entrega el motor solo
  escribe códigos de corrida: otro código de un adaptador es `ENGINE_FAILURE`.
- **La configuración no toca lo que arma el adaptador:** `ejecucion.comandoHost` y los perfiles de
  modelo no pueden traer banderas del adaptador ni de seguridad.
- **El texto del Host se redacta antes de recortarse**, y al entregar la huella del `request.json`
  tiene que ser la que el motor escribió.

Lo que no cambia: las decisiones 1 a 4, 6 y 7, el principio de la 5, el contrato de Task 3 y
ADR-0014. En contra, y dicho además de lo de arriba: en Windows, `Bash` no existe en la sesión del
Host; un Host terminado desde afuera es `HOST_FAILURE`, porque no hay una señal que lo distinga; y una
request adulterada deja su Execution ilegible hasta replanificar.

## Revisión

**Revisa ADR-0014 en lo que dejaba para la Task siguiente** —el mecanismo de la reserva, el
almacenamiento, la admisión implementada y el Host Adapter—, sin cambiar sus siete decisiones.
ADR-0013 y ADR-0014 no se editan, porque son historia, y los dos invariantes del punto 4 de ADR-0013
siguen: la contabilidad no es estado de ejecución, y el estado del Plan se deriva del contenido del
Plan. Este ADR se revisa cuando Task 5 agregue scheduling, colas, reintento automático o un segundo
Host.
