# Verificación — Minimal Execution Engine: una WorkUnit, un intento, persistido y terminal

> 📌 **Esta verificación contradijo la primera construcción.** Las correcciones posteriores
> (spec §34, informe de construcción, «Corrección post-refutación») requieren reverificación
> independiente. Los veredictos de abajo son los del 09-10-2026 y no se reescriben.

**Estado:** cerrada el 13-10-2026 y publicada en 0.32.0 (ver «Cierre formal de Task 4», al final) · **Fecha:** 09-10-2026 (la primera verificación) · **Versión:** sobre 0.31.0 (`fdca5ce`), sin commitear

Este documento registra el veredicto por escenario de quien verificó, que no es quien construyó
([ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md)). Los veredictos los emitió
`harness-spec-refuter` el 09-10-2026, en seis contextos separados del de la construcción y sin sus
conclusiones:

- persistencia y recuperación;
- admisión;
- Host Adapter y lo demás;
- la corrida real de ME-E50;
- la auditoría del rojo visto;
- la suite completa con el árbol final.

Cada uno corrió los tests que nombran sus escenarios y los reprodujo con scripts propios en
`%TEMP%`. Lo registra la sesión que pidió la verificación, que es la misma que construyó: el
refutador no escribe su veredicto.

**Resultado: 54 escenarios por la suite: 51 sostenidos, 3 contradichos (ME-E24, ME-E28, ME-E39).
1 de lectura: ME-E50 contradicho, sin leer. 0 leídos, 0 sin sustento. Invariantes: 28 sostenidos, 3
contradichos (ME-I06, ME-I17, ME-I23). El cambio no cierra.**

## Baseline

| | |
|---|---|
| `HEAD` | `fdca5ce86e73ea2a47ad3745ff850310e88f80f5`, en `main`, tag `v0.31.0`. No hay commits después |
| `VERSION` | `0.31.0` |
| Task 3 | sin commit, integrada a 0.31.0 en el árbol de trabajo |
| Baseline efectiva de Task 4 | `fdca5ce` más Task 3 integrada, sin commitear |
| Diff contra `fdca5ce` | 6 modificados, +839/−97: `PENDIENTES-FH.md`, `PENDIENTES-I.md`, `modelo-canonico.md`, `dev-harness.py`, `63-harness-unico-instalador.ps1`, `64_modelo_de_dominio.py` |
| Archivos nuevos | 23: los de Task 3 y los de Task 4 (ADR-0015, `minimal-execution-engine/`, seis módulos de `bin/ejecucion/`, la suite 72, su instalador y `tests/fixtures/host_falso.py`) |
| Stash | `stash@{0}: task3-execution-contract-sobre-0f8b725` (`b85265a`). La copia de Task 3 anterior a la integración: 13 de sus 14 archivos difieren del árbol. Se listó y no se aplicó |
| `.claude/ejecuciones/` en el repo | no existe, ni antes ni después |

## Método

- **Independencia:** seis contextos de `harness-spec-refuter`, separados del constructor, con la spec
  como fuente. El informe de construcción se usó solo como índice.
- **Mutaciones:** siempre sobre copias de la fábrica en `%TEMP%`, con la restauración comprobada
  por hash.
- **Claude Code real:** solo lo lanzó la corrida de ME-E50. Las demás reproducciones usaron el Host
  falso por `ejecucion.comandoHost`, o un `claude.cmd` falso primero en el `PATH`.
- **Árbol real:** se tomó una foto antes de empezar, con el sha256 de 804 archivos (sin `.git` ni
  `__pycache__`). Al final dio `IGUAL`: sin nuevos, sin borrados y sin cambiados. `git status` dio las
  mismas 29 entradas. Ningún verificador escribió en el repositorio.

## Escenarios

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| ME-E01 | Camino feliz: turno 1, request, entrega, output, `SUCCEEDED` válido, huellas y sesión | sostenido | sí, confirmado con tres mutaciones propias | `test_me_e01`, 14/14; repro por CLI con secretos y CRLF, 20/20 |
| ME-E02 | `PARTIAL`, `BLOCKED` y `FAILED` dan `AGENT_DECLARED_NOT_COMPLETE` con informe | sostenido | sí | `test_me_e02`, 15/15; repro 3/3 |
| ME-E03 | Sin `structured_output`, reintentos, clave de más o enum fuera: `OUTPUT_INVALID` | sostenido | sí | `test_me_e03`, 16/16; repro con 11 variantes |
| ME-E29 | Nadie lee `result` ni el artifact; las normas son las de la refutación sin importarla | sostenido | sí, confirmado con tres mutaciones propias | `test_me_e29`, 9/9; repro con 8 casos y 310 variantes de unidad |
| ME-E04 | Fallas del Host después de la entrega dan `HOST_FAILURE` con `startedAt` y evidencia | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e04`, 15/15; repro con 9 casos |
| ME-E32 | Proveedor identificado: `PROVIDER_FAILURE`; si no, `HOST_FAILURE` | sostenido | sí | `test_me_e32`, 2/2; repro con 8 formas. Contra el Host real, ver ME-E50 |
| ME-E05 | Señal externa o Ctrl-C sin pedido: `HOST_INTERRUPTED`, y el árbol muere | sostenido | sí | `test_me_e05`, 6/6; repro de los dos casos |
| ME-E06 | `--cancelar` con el motor vivo: RUNNING y REQUESTED a `CANCELLED`; terminal intacta | sostenido | sí | `test_me_e06`, 14/14; repro en otro proceso |
| ME-E31 | El límite da `TIMEOUT`, nombra el límite y mata el árbol | sostenido | sí | `test_me_e31`, 6/6; repro: 3 s cortan en 4,9 s, Host y nieto muertos |
| ME-E33 | Sin catálogo después del AgentReport: `ENGINE_FAILURE`, sin `output.md` | sostenido | sí | `test_me_e33`, 5/5; repro de tres variantes. Ver ME-I17 |
| ME-E34 | Una `REQUESTED` huérfana bloquea y se cancela; una `RUNNING` ya cortada da `HOST_INTERRUPTED` | sostenido | sí | `test_me_e34`, 11/11; repro con el motor matado de verdad |
| ME-E07 | El plan cambia entre la creación y la entrega: `PLAN_CHANGED` | sostenido | sí, confirmado con una mutación propia | `test_me_e07`, 3/3; repro con 4 campos y reformateo |
| ME-E08 | El flujo deja de permitir: `DELEGATION_NOT_ALLOWED` con el bloqueo en el detail | sostenido | sí | `test_me_e08`, 6/6; repro con 4 bloqueos distintos |
| ME-E09 | Fuente de la unidad en alerta: `NORMATIVE_GATE_BLOCKED`; la que no exige, admite | sostenido | sí, confirmado con tres mutaciones propias | `test_me_e09`, 5/5; repro con ES0902 y ES0903, y por CLI |
| ME-E10 | El agente deja de ser ruteable: `AGENT_UNAVAILABLE` | sostenido | sí | `test_me_e10`, 2/2; repro |
| ME-E11 | Una capability deja de estar: `CAPABILITY_UNAVAILABLE` | sostenido | sí | `test_me_e11`, 2/2; repro con el adaptador real |
| ME-E12 | Dependencias: solo `SUCCEEDED` en la misma huella; `admission.dependencies` la nombra | sostenido | sí | `test_me_e12`, 7/7; repro con siete estados y otra huella |
| ME-E27 | Al pedir gana la primera falla, y nada queda escrito | sostenido | sí | `test_me_e27`, 7/7; repro con 12 pares |
| ME-E28 | `request.json` editado a mano: `CONTRACT_INVALID` | **contradicho** | sí | `test_me_e28`, 4/4, pero prueba una proposición vecina. Ver su sección |
| ME-E30 | Plan 2.0, JSON cortado, otra TaskKey e ids repetidos | sostenido | sí | `test_me_e30`, 8/8; repro con 1.0, 2.0, 2.1 y once formas |
| ME-E41 | `jira.*` y `repository.write` sin `Write`: `CAPABILITY_UNAVAILABLE` al entregar | sostenido | sí | `test_me_e41`, 8/8; repro con `gitlab.*` y `tests.run` también |
| ME-E42 | Sin definición del agente: `REJECTED`; un Host que no lo carga: `HOST_FAILURE` | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e42`, 9/9; repro antes y después de la entrega |
| ME-E13 | Una `REQUESTED` o `RUNNING` bloquea sin escribir | sostenido | sí | `test_me_e13`, 5/5; repro |
| ME-E14 | Un `SUCCEEDED` bloquea pase lo que pase | sostenido | sí | `test_me_e14`, 4/4; repro |
| ME-E15 | Después de `FAILED`, turno 2, otro id, la misma clave | sostenido | sí | `test_me_e15`, 4/4; repro con tres turnos |
| ME-E16 | Lo mismo después de `CANCELLED` | sostenido | sí | `test_me_e16`, 4/4; repro |
| ME-E17 | Lo mismo después de `REJECTED` | sostenido | sí | `test_me_e17`, 4/4; repro |
| ME-E18 | EX-F01: dos procesos, una Execution, un duplicado, un turno, cero temporales | sostenido | sí, confirmado con una mutación propia | `test_me_e18`, 10/10; repro con 59 carreras de procesos reales |
| ME-E19 | EX-F02: la propia pasa la 15; si el último turno es de otra abierta o `SUCCEEDED`, `DUPLICATE_EXECUTION` | sostenido | sí, solo la primera mitad | `test_me_e19`, 6/6; la mitad «o SUCCEEDED» solo por reproducción. Ver hallazgos |
| ME-E37 | El barrido no toca una carpeta con el candado tomado, ni una joven | sostenido | sí | `test_me_e37`, 5/5; repro con un proceso vivo de verdad |
| ME-E52 | Un residuo sin turno no es una Execution y se barre | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e52`, 10/10; repro con un proceso matado antes del turno |
| ME-E20 | Una `RUNNING` huérfana: `HOST_INTERRUPTED`, sin reentregar ni matar | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e20`, 15/15; repro con espía: cero llamadas a matar |
| ME-E53 | Una cancelación persistida gana sobre la muerte del motor | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e53`, 12/12; repro con los motores suspendidos |
| ME-E21 | Escribir otra vez no cambia un byte; un corte no deja destino ni temporal | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e21`, 13/13; repro con muertes reales del proceso |
| ME-E22 | Un resultado tardío no pisa | sostenido | sí | `test_me_e22`, 4/4; repro |
| ME-E23 | Rutas no canónicas no se persisten; mayúsculas repetidas en Windows | sostenido | sí | `test_me_e23`, 6/6; repro con 26 formas y una junction |
| ME-E24 | Secretos en artifact, `requestedBy`, `detail` y WorkUnit | **contradicho** | sí, confirmado con dos mutaciones propias | `test_me_e24`, 10/10, pero el `detail` deja pasar un secreto. Ver su sección |
| ME-E35 | `--estado` no escribe, marca huérfanas e informa ilegibles | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e35`, 10/10; repro sobre el proyecto entero con espías |
| ME-E36 | Ids `fullmatch`, sin repetidos, y ningún `\n` final se usa como ruta | sostenido | sí | `test_me_e36`, 8/8; repro con 200 000 ids y 14 formas malas |
| ME-E25 | Repo sucio: lo limpio cambiado es de la Execution; lo sucio cambiado no se atribuye | sostenido | sí | `test_me_e25`, 5/5; repro con 13 chequeos |
| ME-E43 | Sin git: `CHANGES_UNRESOLVED`; con un commit del Host, sus archivos | sostenido | sí | `test_me_e43`, 4/4; repro, también con `.claude/` sin ignorar |
| ME-E44 | Otra Execution del proyecto RUNNING: `CHANGES_UNATTRIBUTABLE` | sostenido | sí, solo para la misma tarea | `test_me_e44`, 3/3; otra TaskKey del mismo proyecto, solo por reproducción |
| ME-E38 | `--model` solo con un perfil declarado; nunca `--max-budget-usd` | sostenido | sí | `test_me_e38`, 9/9; repro con 7 formas |
| ME-E39 | Nunca `--bare` ni saltear permisos; siempre las banderas de seguridad | **contradicho** | sí | `test_me_e39`, 11/11, solo con la configuración por defecto. Ver su sección |
| ME-E40 | `--allowedTools` mínimo; el schema intacto por un shim `.cmd`; el prompt por stdin | sostenido | sí | `test_me_e40`, 10/10; repro con el `claude.cmd` real de npm |
| ME-E45 | El motor no reconcilia; sin `state.json`, `DELEGATION_NOT_ALLOWED` | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e45`, 6/6; repro con corridas FAILED y REJECTED |
| ME-E54 | `comandoHost` inválido falla antes, sin residuo | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e54`, 22/22; repro con 11 formas |
| ME-E55 | `limiteSegundos` y un `harness.config.json` ilegible fallan antes | sostenido | sí, confirmado con dos mutaciones propias | `test_me_e55`, 30/30; repro con 17 formas |
| ME-E26 | En un proyecto instalado, `ejecutar` deja `SUCCEEDED` | sostenido | sí, confirmado con una mutación propia | `72-motor-de-ejecucion-instalador.ps1`, 12/12; instalación propia con lock de 292 rutas |
| ME-E46 | `contrato.py` puro; sin contabilidad; escritura solo bajo `.claude/ejecuciones` | sostenido | sí | `test_me_e46`, 9/9; repro con AST y una corrida entera |
| ME-E47 | Sin concurrencia ni SDK; trece subcomandos; el Host solo desde el adaptador | sostenido | sí | `test_me_e47`, 8/8; repro con AST propio |
| ME-E48 | Modelo canónico y ADR-0015; ADR-0013 y ADR-0014 intactos | sostenido | sí | `test_me_e48`, 16/16; conteo de conceptos 75 → 83 (los ocho de Task 3) |
| ME-E49 | Lo protegido es el de la base, sin archivos nuevos | sostenido | sí | `test_me_e49`, 20/20; `git diff --stat fdca5ce` vacío |
| ME-E50 | Una corrida real contra Claude Code: `structured_output`, `--agent`, stdin, vínculo, error del proveedor | **contradicho** | no consta | Tres corridas reales; `lectura.md` sin firmar. Ver su sección |
| ME-E51 | `Invoke-Tests.ps1` sale con 0 | sostenido | no consta | 43693/43693, exit 0, 2041 s |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. La auditoría del rojo visto
> reprodujo, con mutaciones propias distintas de las del constructor, las marcas de ME-E01, E04, E07,
> E09, E18, E20, E21, E24, E26, E29, E35, E42, E45, E52, E53, E54 y E55. Las 56 filas de §29.1 de la
> spec son coherentes con las marcas.

## ME-E24, el escenario contradicho por el `detail`

```
stderr del Host: 166 caracteres y después un token de GitHub de 40
result.json → error.detail lleva "ghp_" + 30 de los 36 caracteres siguientes, sin redactar
```

**Causa.** `host_claude_code.py:225` recorta stderr a 200 caracteres **antes** de redactar:

```python
stderr = error.read(4096).decode("utf-8", "replace").strip()[:TOPE_DE_STDERR] or None
```

El pedazo que queda ya no coincide con el patrón del catálogo. El test pone el secreto al principio
de stderr, y por eso pasa. MD-19 dice «redactado y recortado». Se sostiene lo demás del escenario:

- `requestedBy` sale redactado, y `requestFingerprint` es la huella del `request.json` redactado;
- `output.md` sale redactado, y su huella son sus bytes;
- un secreto en la WorkUnit da `CONTRACT_INVALID` sin crear la Execution.

**Decisión:** ninguna todavía. Vuelve a construcción.

## ME-E28, el escenario contradicho por la admission

| Edición de `request.json` entre la creación y la entrega | Resultado |
|---|---|
| Una clave de más en `workUnit`, otra `objective`, o un `admission.agent.domain` incoherente | `REJECTED` / `CONTRACT_INVALID`, sin Host |
| `admission.normativeGate`, `admission.agent.validation`, `admission.agent.type`, `requestedBy` o `createdAt` cambiados | **`SUCCEEDED`, con `entrega.json` y el Host lanzado** |
| Otra WorkUnit del plan, con las huellas rehechas | `REJECTED` / `DUPLICATE_EXECUTION`, no `CONTRACT_INVALID` |

**Causa.** `admision._regla` (`:261-269`) compara solo la huella del plan y la de la unidad.
`motor.py:223-226` no compara la request guardada con la que escribió, y le entrega al Host la que
tiene en memoria. El test elige como «otra admission» un dominio incoherente, que ya rechaza
`validar_request`: prueba una proposición vecina, no la del escenario. En todos los casos la
Execution queda ilegible en disco, porque `requestFingerprint` ya no es la huella del archivo
editado.

**Decisión:** ninguna todavía. Vuelve a construcción.

## ME-E39, el escenario contradicho por la configuración

```
ejecucion.comandoHost = [python, host, "--dangerously-skip-permissions", "--bare"]   (válido para MD-22)
→ el Host recibió ['--dangerously-skip-permissions', '--bare', '-p', ...] y la corrida dio SUCCEEDED
ejecucion.comandoHost = [..., "--permission-mode", "bypassPermissions"]
→ el Host recibió los dos modos: bypassPermissions y dontAsk
modelRouting.perfiles[tier] = "--dangerously-skip-permissions"
→ el Host recibió "--model --dangerously-skip-permissions"
```

**Causa.** `PROHIBIDOS` (`host_claude_code.py:42-43`) no lo usa nadie. No hay guarda al validar la
configuración ni al armar los argumentos. Con la configuración por defecto todo se cumple, y es lo
único que prueba el test. El escenario dice «nunca».

**Decisión:** ninguna todavía. Hay dos salidas, y elegir es de la persona: rechazarlo en el código
(`configuracion()` o `argumentos()`), o acotar el «nunca» de la spec a lo que agrega el adaptador.
Vuelve a construcción.

## ME-E50, la lectura contradicha por el Host real

**Corrida.** El verificador hizo tres corridas reales el 09-10-2026, con Claude Code 2.1.295 y USD
0,98 en total, en un proyecto instalado en `%TEMP%`:

1. `ejecutar` dentro del entorno de esta sesión;
2. la entrega a mano, con los argumentos del adaptador y un entorno de terminal;
3. un error provocado con un modelo inexistente.

| Lo que la spec supone del Host | Lo que se observó |
|---|---|
| El prompt por stdin | Sostenido: la primera línea es `Seguimos con GCBA-72.` y llega la WorkUnit entera |
| `--json-schema` devuelve `structured_output` con las dos claves | **Contradicho:** `subtype: success`, `is_error: false` y **sin `structured_output`**. El modelo escribió el JSON como texto en `result`. Con `--agent`, la sesión queda con las herramientas del `tools:` del agente, y `StructuredOutput` no está entre ellas, así que el Host tampoco la pide |
| `--agent` carga el agente | Sostenido: `agentSetting: dev-backend`, con su prompt |
| `--allowedTools` restringe junto con `tools:` | Parcial: `tools:` define el conjunto, pero `--allowedTools Read,Glob,Grep,Skill` no lo achica (se ofrecieron `Edit` y `Write`). No se vio ninguna negativa de `dontAsk` |
| La sesión queda vinculada a la TaskKey | Sostenido: `session-task-binding/1.0` con `GCBA-72`, en las tres sesiones |
| `session_id` es `host.sessionRef` | Sostenido |
| Un error del proveedor | Exit 1, `is_error: true`, **`subtype: "success"`**, `api_error_status: 404`, `terminal_reason: "api_error"`, **sin `error.type`**: el motor da `HOST_FAILURE`, y `PROVIDER_FAILURE` no se alcanza nunca |
| Termina terminal, y `result.json` pasa `validar_resultado` | Sostenido: dos Executions, `FAILED`/`OUTPUT_INVALID` y `FAILED`/`HOST_FAILURE`, que validan, con `requestFingerprint` igual a la huella de su `request.json` |

**Veredicto: contradicho.** Una premisa material del Host es falsa con los argumentos del adaptador:
`structured_output` no llega, así que ninguna Execution real puede terminar `SUCCEEDED` ni
`AGENT_DECLARED_NOT_COMPLETE`. Aunque no lo estuviera, no sería `leído`: `lectura.md` sigue sin
firmar, y el refutador no es una persona nombrada. ADR-0010 no aplica, porque es un solo escenario.

**Evidencia:**
- las transcripciones del Host, en
  `~\.claude\projects\C--Users-20435071482-AppData-Local-Temp-refuter-t4-me50-a97e74a0\`;
- las salidas crudas, en el scratchpad de la sesión.

**Decisión:** ninguna todavía. El Host Adapter vuelve a construcción, y `lectura.md` tiene que
firmarla una persona después.

## Invariantes

| Invariante | Evidencia | Veredicto |
|---|---|---|
| ME-I01 | Un turno, una request, una WorkUnit; `--unidad` con una coma da `CONTRACT_INVALID` | sostenido |
| ME-I02 | Una segunda escritura de `request.json` da `FileExistsError` con bytes y mtime iguales; las muertes alrededor de `os.link` no la dejan a medias | sostenido |
| ME-I03 | Los siete archivos y el turno son de una sola escritura; ningún otro escritor | sostenido |
| ME-I04 | 59 carreras: un ganador por clave | sostenido |
| ME-I05 | Turno exclusivo por `os.link`, con la request escrita antes | sostenido |
| ME-I06 | Al entregar se derivan las quince, pero una request con otra `admission`, otro `requestedBy` u otro `createdAt` llega al Host (ME-E28) | **contradicho** |
| ME-I07 | La propia pasa la 15; otra abierta o `SUCCEEDED` la rechaza | sostenido |
| ME-I08 | Resultado tardío, recuperación forzada y `--cancelar` sobre una terminal: no cambia | sostenido |
| ME-I09 | Turno N+1, otro id, la misma clave | sostenido |
| ME-I10 | `FAILED`, `CANCELLED` y `REJECTED` admiten reintento | sostenido |
| ME-I11 | `SUCCEEDED` cierra la clave | sostenido |
| ME-I12 | El adaptador devuelve un AgentReport de dos claves; el stdout crudo no sale de `entregar` | sostenido |
| ME-I13 | Nadie lee `result`; el artifact solo se redacta y se copia | sostenido |
| ME-I14 | No se vuelve a entregar; `recuperar` no llama al adaptador | sostenido |
| ME-I15 | El resultado solo lo escribe quien tiene el candado; con el motor vivo no se cierra | sostenido |
| ME-I16 | MD-16 en la evidencia y en el output; la junction da `CHANGES_UNRESOLVED` | sostenido |
| ME-I17 | Sin catálogo, el nombre de una clave de más del `structured_output` llega al `detail` de `OUTPUT_INVALID` (`host_claude_code.py:267-268`); y el pedazo de secreto de ME-E24 | **contradicho** |
| ME-I18 | Sin imports de contabilidad, sin `WORKUNIT_*`, sin tocar `accounting` | sostenido |
| ME-I19 | Cualquier campo cambiado da `PLAN_CHANGED`; reformatear no | sostenido |
| ME-I20 | La misma `idempotencyKey` aunque cambie el flujo; solo `leer`, `vigencia_local(10)` y `permisos` | sostenido |
| ME-I21 | Residuos, carpetas sin turno y turnos ilegibles no son Executions | sostenido |
| ME-I22 | E05, E06, E34 y E53 se cumplen. Con una reserva: si `--cancelar` ya vio el motor vivo y el motor muere antes de escribir el pedido, termina `CANCELLED` (hallazgo 9) | sostenido |
| ME-I23 | `comandoHost` y los perfiles meten `--bare`, `--dangerously-skip-permissions` y `bypassPermissions` (ME-E39) | **contradicho** |
| ME-I24 | `--allowedTools` mínimo en todo lo probado con el Host falso. Contra el Host real no achica `tools:` (ME-E50) | sostenido |
| ME-I25 | Todo id pasa por `fullmatch` antes de ser ruta | sostenido |
| ME-I26 | `contrato.py` con el hash de la base y AST limpio | sostenido |
| ME-I27 | Sin hilos, colas ni workers; nada elige ni recorre unidades | sostenido |
| ME-I28 | Un residuo no aparece, no bloquea, no satisface dependencias y se barre | sostenido |
| ME-I29 | `entrega.json` se crea en un solo lugar; ninguna corrida dio `FAILED` con esos dos códigos. Lo garantiza el adaptador, no el motor (hallazgo 12) | sostenido |
| ME-I30 | Derivar, redactar, comparar, validar, huella, persistir; la huella del `request.json` es `requestFingerprint` | sostenido |
| ME-I31 | 30 configuraciones inválidas: exit 2, sin residuo | sostenido |

## AS-IS confirmado

Antes de Task 4 estaban el contrato de Task 3, sin productor, y Flow Governance de 0.31.0. Task 4
agregó seis módulos en `bin/ejecucion/` y el subcomando `ejecutar`, con trece subcomandos en total.
La cadena que se lee en el código:

1. `motor.configuracion`;
2. la recuperación;
3. `admision.al_pedir`;
4. `registro.crear`, que publica con el turno;
5. `admision.al_entregar`;
6. la foto y `entrega.json`;
7. `Adaptador.entregar`;
8. `_output`;
9. `evidencia.armar`;
10. `result.json`.

No hay responsabilidades en la capa equivocada. La única guarda contra banderas prohibidas, en
cambio, no está en ninguna capa (ME-E39).

## Atomicidad

ME-E18 se reprodujo en 59 carreras de procesos reales, con estas variantes:

- 12 con punto de encuentro entre la lectura y la reserva;
- 40 de dos procesos sin punto de encuentro;
- 6 de cuatro procesos;
- 1 de tres procesos con punto de encuentro.

En cada una: un `SUCCEEDED`, n−1 `DUPLICATE_EXECUTION`, un turno y una carpeta, sin residuos ni
temporales. Además, 30 carreras sobre `escribir_una_vez` del mismo archivo: un solo ganador, intacto.
EX-F02 (ME-E19) quedó establecido por las dos mitades.

## Persistencia

- **Escritura de una sola vez.** Temporal exclusivo, fsync, `os.link`, y el temporal se borra
  siempre. En `bin/ejecucion/` no hay `os.replace`, `open(..., "w")`, `write_text` ni `write_bytes`.
  Muertes reales del proceso alrededor de cada `os.link`: nunca un destino a medias, y la
  recuperación limpia el temporal.
- **Punto de publicación.** Una Execution existe si y solo si un turno la nombra.
- **Candado de vida.** `msvcrt.locking` en Windows; ante la duda, vivo. Nadie mata por PID: un espía
  contó cero llamadas a matar durante la recuperación.
- **Recuperación.** Una `RUNNING` sin pedido da `HOST_INTERRUPTED`; con pedido, `CANCELLED`. Una
  `REQUESTED` huérfana queda abierta hasta `--cancelar`. El residuo previo a la publicación se barre
  con el candado libre y diez minutos.

## Admisión

- **Al pedir:** la precedencia del código es la de T3 §37.5, sin `PLAN_CHANGED`, y doce pares de
  fallas simultáneas dan siempre la primera.
- **Al entregar:** corren las quince, `PLAN_CHANGED` incluida, derivadas otra vez. Pero no se
  verifica que el `request.json` guardado sea el escrito (ME-E28).
- **Frontera de `entrega.json`:** antes, `REJECTED` con su código de admisión; después, solo
  códigos de corrida.
- **Compuerta normativa:** la llamada lleva las normas de la unidad, y `NORMATIVE_GATE_BLOCKED` es
  alcanzable.
- **Flujo:** se lee y no se escribe.

## Host Adapter

- **Contra el Host falso,** externo y sin monkeypatch, se sostienen:
  - los argumentos con la configuración por defecto;
  - el AgentReport solo desde `structured_output`;
  - el mapeo de errores;
  - el shim `.cmd` real de npm;
  - las herramientas mínimas y el modelo por perfil.
- **Contra el Host real,** `structured_output` no llega (ME-E50).
- **Con una configuración válida,** pasan banderas prohibidas (ME-E39).

## Evidencia

Se sostienen:

- un archivo limpio cambiado;
- un sucio no tocado;
- un sucio cambiado otra vez (`CHANGES_UNATTRIBUTABLE`);
- sin git (`CHANGES_UNRESOLVED`);
- otra Execution `RUNNING` de la misma tarea y de otra tarea del mismo proyecto;
- un commit del Host, con `ADDED`, `MODIFIED`, `DELETED` y un renombre.

El registro propio no contamina la evidencia, ni con `.claude/` fuera del `.gitignore`.

## Tests focalizados

Corridos en serie sobre el árbol real, el 09-10-2026:

| Caso | Aserciones | Exit | Segundos |
|---|---|---|---|
| 72_motor_de_ejecucion.py | 464/464 | 0 | 217,3 |
| 65_contrato_de_ejecucion.py | 673/673 | 0 | 71,5 |
| 64_modelo_de_dominio.py | 1038/1038 | 0 | 124,3 |
| 71_plan_2_1.py | 276/276 | 0 | 33,1 |
| 61_flujo_precondiciones.py | 184/184 | 0 | 22,1 |
| 61_conocimiento_auto_refresco.py | 292/292 | 0 | 10,0 |
| 62_estado_del_flujo.py | 177/177 | 0 | 61,0 |
| 63_compuerta_del_flujo.py | 487/487 | 0 | 100,9 |
| 64_interaccion_humana.py | 376/376 | 0 | 106,9 |
| 65_fail_closed.py | 284/284 | 0 | 15,6 |
| 67_integracion_frescura.py | 43/43 | 0 | 22,6 |
| 70_r11_glob_de_autoridad.py | 421/421 | 0 | 88,3 |
| 66_integrity_cleanup.py | 733/733 | 0 | 90,4 |
| 72-motor-de-ejecucion-instalador.ps1 | 12/12 | 0 | 13,6 |
| 63-harness-unico-instalador.ps1 | 188/188 | 0 | 202,9 |

## Suite completa

```
cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -File tests\Invoke-Tests.ps1 < NUL"
916/916 pasaron (PowerShell).
42777/42777 pasaron.
43693/43693 pasaron.
exit=0 · 2041 s
```

Sin deuda preexistente. Antes y después, `pre-tool-use.py` tiene el blob `b9cde9d`, `zonas.py`
`e996067`, y `contrato.py`, los dos schemas de Task 3 y ADR-0014 tienen su huella de la base.

## Alcance

- **Implementación:** no hay Graph Execution, DAG, scheduler, colas, workers, paralelismo, hilos,
  `asyncio`, `concurrent`, `sched`, reintento automático, backoff, checkpoint, reanudación,
  LangGraph, LangChain, eventos contables nuevos, Job Objects, una política nueva de hooks ni un
  framework multi-proveedor.
- **Menciones:** solo dos docstrings que dicen que no los hay.
- **Comportamiento de Task 5:** el motor no elige la siguiente unidad, no recorre dependencias para
  ejecutarlas y no corre varias.
- **Lo protegido:** idéntico a la base y sin archivos nuevos. `tool_policy.py` no menciona
  `ejecutar`.

## Riesgos aceptados

R1 a R4 siguen abiertos y declarados, y la construcción no los resolvió por su cuenta:

- **R1, el Host que sobrevive al motor.** La recuperación no mata por PID, `--estado` avisa y MP-01
  sigue abierto.
- **R2, la `REQUESTED` huérfana.** Queda abierta hasta `--cancelar`.
- **R3, lo no documentado del Host.** ME-E50 lo resolvió, en contra.
- **R4, `ejecutar` sin fila en la política de herramientas.** Sigue `UNRESOLVED_TOOL_CLASS`.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Claude Code real no devuelve `structured_output` con `--agent` y el `tools:` del agente**
   (ME-E50). La suite estaba verde porque el Host falso emite una forma que el Host real no emite.
2. **Un error real del proveedor llega con `subtype: "success"` y `api_error_status`, sin
   `error.type`.** `PROVIDER_FAILURE` no se alcanza, y la forma que prueba ME-E32 no es la del Host
   real.
3. **`--allowedTools` no achica las herramientas que ofrece `--agent`.** «El agente recibe solo lo
   que su unidad pide» descansa en una negativa de `dontAsk` que no se vio.
4. **Las banderas prohibidas entran por la configuración** (ME-E39). `PROHIBIDOS` es código muerto.
5. **Recortar stderr antes de redactar deja pasar un secreto** (ME-E24).
6. **Una request editada a mano en `admission`, `requestedBy` o `createdAt` llega al Host** (ME-E28).
7. **Sin catálogo, el nombre de una clave del `structured_output` llega al `detail`** (ME-I17).

## Lo que queda abierto, anotado y no escondido

La persona pidió no cambiar `Pendientes/Fix-Harness/PENDIENTES-FH.md` en esta verificación. Lo de
abajo queda escrito acá, para que la vuelta a construcción lo lleve a pendientes o lo resuelva.

**Bloqueantes:** los cuatro contradichos (ME-E24, ME-E28, ME-E39, ME-E50) y sus tres invariantes.

**No bloqueantes:**

8. **ME-E19 y ME-E44:** sus tests no cubren una de sus mitades («o SUCCEEDED» y «otra tarea del mismo
   proyecto»), que quedaron establecidas por reproducción. ME-E09 solo, sin ME-E29, no distingue las
   normas de la unidad de la norma por defecto.
9. **ME-I22:** si `--cancelar` vio el motor vivo y el motor muere antes de escribir el pedido, termina
   `CANCELLED` aunque el corte vino primero. Es inherente a la regla de MD-24, y el verificador lo
   clasificó como precisión documental; si se lee como contradicción del «nunca al revés», lo decide
   la persona.
10. **Un JSON `success` con un código de salida distinto de 0 da `SUCCEEDED`.** MD-10 dice «un código
    de salida raro» es `HOST_FAILURE`.
11. **En Windows, un Host terminado desde afuera** (`taskkill /F`, exit 1) da `HOST_FAILURE`, no
    `HOST_INTERRUPTED`. El Host falso simula 143.
12. **El motor no filtra ME-I29:** un adaptador que devuelva `AGENT_UNAVAILABLE` después de la entrega
    quedaría escrito como `FAILED`.
13. **Una request editada deja la Execution ilegible para siempre:** la clave queda bloqueada y solo
    se destraba replanificando.
14. **Errores con traceback en vez de error del comando:**
    - `--recuperar` con una clave con `\n`;
    - `--cancelar` y una recuperación concurrente que borra su temporal;
    - una `entrega.json` editada que deja a `recuperar` en `ErrorDelComando` para toda la tarea.
15. **E-22, EX-E51 y EX-G11 se aflojaron más de lo necesario:**
    - E-22 no limita qué funciones de la admisión usan la ruta del plan;
    - EX-E51 no fija la fuente de E-41;
    - EX-G11 dejó `dev-harness.py` cuidado solo en sus subcomandos.
16. **`resolver_agente` lee el frente del agente de forma literal:** un `name:` entre comillas o un
    `tools:` en lista YAML no se reconocen.
17. **Una ruta de la evidencia con un secreto en el nombre no se redacta.** MD-19 no lista las rutas.
18. **La suite 72 deja residuos en `%TEMP%`:** guiones, ecos, nietos, shims y `me72-hijo-*.py`.

**Precisión documental:**

19. **El modelo canónico:**
    - `### Claude Code ≠ HARNESS` y `### Plan ≠ Execution` siguen diciendo que HARNESS no lanza
      agentes y que no existe ninguna ejecución;
    - ExecutionId, ExecutionError, ExecutionEvidence y AgentReport siguen en condicional (ya
      anotado en PENDIENTES-FH).
20. **ADR-0015** dice 26 contradicciones, y son 27.
21. **La spec** todavía dice «No construye nada todavía» (línea 12).
22. **`lectura.md`** espera `error.type`, que el Host no emite.
23. **El `detail` de `DELEGATION_NOT_ALLOWED` recomienda `--status`,** que no reconcilia; el que
    reconcilia es `--resume`.
24. **MD-17** dice que PreToolUse alcanza a cada herramienta del agente, y `Read`, `Glob`, `Grep` y
    `Skill` no pasan por el hook.
25. **Nueve docstrings de la suite 72** traen mojibake.

**Riesgo Task 5+:**

26. **Las herramientas de la sesión real:** `Bash` no está en la sesión del Host Windows, y `Edit` y
    `Write` se ofrecen a una unidad de solo lectura.
27. **La sonda del candado puede caer entre `O_EXCL` y el bloqueo** de `Vida`: microsegundos, más
    probable con workers.
28. **Una junction interna duplica un archivo físico en la evidencia.**
29. **Ningún test fija que la exclusividad de la reserva venga del sistema de archivos.**

## Lo que ningún test cubre y se mira con los ojos

- **La corrida real contra Claude Code.** Después de corregir el adaptador, alguien que no construyó
  tiene que repetirla con `lectura.md` y firmarla `Leyó:`.
- **El costo de una corrida:** USD 0,43 a 0,55 por sesión, con el modelo que elige el Host para un
  tier `low_cost` sin perfil.

## Veredicto acumulado

| | Sostenidos | Leídos | Contradichos | Sin sustento |
|---|---|---|---|---|
| Por la suite (54) | 51 | — | 3 | 0 |
| De lectura (1) | — | 0 | 1 | 0 |
| **Total (55)** | **51** | **0** | **4** | **0** |
| Invariantes (31) | 28 | — | 3 | 0 |

```
verificacion.md con contradicho → EN CURSO
```

Task 4 no cierra, y Task 5 no queda habilitada.


---

## Reverificación post-corrección — 13-10-2026

> 📌 **Esta sección reverifica la corrección de §34 y no reescribe nada de lo de arriba.** Los
> veredictos del 09-10-2026 siguen como se escribieron. Lo que sigue es una segunda verificación, en
> otro contexto que el de la construcción y el de la primera verificación, contra el árbol de trabajo
> de hoy y contra el Claude Code real.

**Estado:** en curso, a la espera de la firma de ME-E50 · **Fecha:** 13-10-2026 (las corridas contra el Host real y casi todas las pruebas, del 10-10; la segunda compuerta, del 13-10) · **Versión:** sobre
0.31.0 (`fdca5ce`), sin commitear · **Claude Code:** 2.1.296 (comprobado de nuevo el 13-10)

**Resultado: 56 escenarios por la suite: 56 sostenidos y 0 contradichos, con una reserva en ME-E18 y
en ME-E51 (la misma causa, hallazgo N1). ME-E24, ME-E28 y ME-E39 se sostienen, y también los dos nuevos,
ME-E56 y ME-E57. 1 de lectura: ME-E50 anda contra el Claude Code real, pero ninguna persona que no
construyó lo leyó y firmó, así que se rinde `sin sustento`, y solo por eso. 0 leídos. Invariantes: 32
sostenidos, 0 contradichos: ME-I06, ME-I17 y ME-I23 vuelven a sostenerse. La compuerta completa salió con
1 en la primera corrida (una aserción de ME-E18 que no se repitió) y con 0 en la segunda. El cambio no
cierra hasta la firma de ME-E50.**

## Baseline

| | |
|---|---|
| `HEAD` | `fdca5ce86e73ea2a47ad3745ff850310e88f80f5`, en `main`, tag `v0.31.0`. Ningún commit ni tag nuevos |
| `VERSION` | `0.31.0`, sin tocar |
| `git status` | 6 modificados (+964/−100; la primera verificación vio +839/−97) y 24 nuevos (23 en la primera: el de más es `verificacion.md`, que se escribió después de su foto) |
| Archivos | 805 sin `.git` ni `__pycache__`; sha256 de cada uno antes y después de mis corridas: `IGUAL`, 805 archivos y 0 diferencias, también después de matar una corrida de la compuerta que quedó colgada (abajo) |
| Stash | `stash@{0}: task3-execution-contract-sobre-0f8b725`, sin aplicar |
| `.claude/ejecuciones/` en el repo | no existe, ni antes ni después |
| Claude Code | **2.1.296** en el `PATH`; la primera verificación y la enmienda usaron 2.1.295 (la sesión desde la que corrí es 2.1.295, el binario que lanza el motor es el 2.1.296) |
| Task 3 | `contrato.py` `968c7831…`, `execution-request.schema.json` `df3a4bc1…`, `execution-result.schema.json` `266304c6…` y ADR-0014 `446b2e1d…`: iguales a la base y a lo que dicen el informe y la primera verificación |
| Hooks | `pre-tool-use.py` blob `b9cde9d` y `zonas.py` blob `e996067`: iguales a `HEAD` |
| Task 5 | no empezó (ver *Alcance*) |

## Método

- **Independencia:** un contexto de `harness-spec-refuter`, separado del de la construcción y del de la
  primera verificación. La spec enmendada (§34) fue la fuente; el informe de construcción lo usé solo
  como índice, y nada de lo que dice ahí lo tomé por prueba.
- **Qué cambió se derivó del código**, no del informe. Como nada está commiteado, el «antes» sale de una
  copia instalada de la primera construcción que quedó en `%TEMP%` (`harness-cb-198d314c`, 08-10, 19:36):
  `contrato.py`, `evidencia.py`, `proceso.py` y `__init__.py` coinciden por hash con los de hoy, y las
  líneas que cita la primera verificación (`host_claude_code.py:225`, `motor.py:223-226`) están donde
  dice en esa copia.
- **Claude Code real:** lo corrí yo, con mi cuenta, los argumentos del adaptador y el entorno de una
  terminal (sin las variables `CLAUDE*` de esta sesión), sobre dos proyectos instalados con `install.ps1`.
  Detalle en *ME-E50*.
- **Mutaciones:** sobre una copia de la fábrica en `%TEMP%`, con la restauración comprobada por hash.
  El repositorio real no se tocó: foto de 805 archivos antes y después, `IGUAL`.
- **Mis scripts** (`repro_*.py`, `run_real.py`, `mutar.py` y los demás) y sus salidas están en
  `C:\Users\20435071482\AppData\Local\Temp\ref2-evidencia-t4`; reusan de la suite solo el armado de proyectos de prueba, y cada comprobación es
  propia.

## Lo que cambió con la corrección, derivado del código

| Archivo | Cambio observado en el diff |
|---|---|
| `bin/ejecucion/host_claude_code.py` | +164/−48. Sin `--agent`: el cuerpo del agente va a `prompt-de-sistema.md` (una sola escritura, en el registro) y se pasa con `--system-prompt-file`; `--tools` y `--allowedTools` con el mismo conjunto; `--strict-mcp-config`. `stderr` ya no se recorta (tope de 1 MiB). El texto del Host (stderr, `subtype` desconocido, `terminal_reason`, `api_error*`, mensajes de `validar_informe`) viaja aparte del texto del motor. `interpretar` mira primero el código de salida: distinto de 0 nunca es informe. El proveedor se reconoce por `terminal_reason == "api_error"` o un `api_error_status` numérico. Reglas nuevas para `comandoHost` y para los perfiles de modelo (`argumento_reservado`, `comando_invalido`, `perfiles_invalidos`), que el constructor del adaptador repite |
| `bin/ejecucion/motor.py` | +48/−11. `configuracion` usa las reglas del adaptador; el adaptador se construye antes de crear nada y un `ValueError` es error del comando; `_detalle_de_falla` redacta el texto del Host entero antes de que `admision.detalle` lo recorte; `_del_adaptador` filtra lo que devuelve el adaptador después de la entrega; `_correr` pasa la huella de lo escrito a la admisión y entrega la request del disco |
| `bin/ejecucion/admision.py` | +10/−2. `al_entregar(…, huella)`: la primera comprobación de la condición 1 es que `contrato.huella(request.json del disco)` sea la que el motor calculó al crear |
| `bin/ejecucion/registro.py` | +1, un docstring que nombra `prompt-de-sistema.md`. Ni una línea de código |
| `contrato.py`, `evidencia.py`, `proceso.py`, `__init__.py`, `dev-harness.py` | iguales (hash o fecha de archivo anterior a la corrección) |
| `tests/fixtures/host_falso.py` | el eco incluye el contenido de `--system-prompt-file`, y se escribe entero o nada |
| `tests/casos/72_motor_de_ejecucion.py` | 464 → 546 aserciones; no se aflojó ningún escenario de Task 3 (`65_*` y `64_*` tienen fecha anterior) |
| Documentos | `modelo-canonico.md` (tres frases), ADR-0015 (27 contradicciones y la «Enmienda post-refutación»), spec §34, `lectura.md`, `PENDIENTES-FH.md` |

## ME-E24 e ME-I17, la redacción antes del recorte

**Cadena en el código:** texto del Host → `limpieza.redactar` entero (`motor._detalle_de_falla`) →
`admision.detalle` redacta de nuevo y recorta a 300. El adaptador ya no recorta nada antes. Sin catálogo,
el `detail` es solo texto del motor.

**Mi reproducción** (`repro_e24.py`, 92 comprobaciones, 0 fallas): el recorte de stderr, con tres
formatos de secreto (token de GitHub, clave de AWS, token de Slack), y los demás campos del Host, con el de
GitHub; en todos, la búsqueda de cualquier fragmento de 13 caracteres en el `detail`, `result.json`,
`request.json`, `entrega.json`, `output.md`, todo `.claude/` del proyecto y la salida del CLI:

| Caso | Resultado |
|---|---|
| stderr con el secreto después de 0, 50, 100, 150, 160, 166, 170, 177, 185, 200, 250, 280, 290, 299, 300, 350, 4000 y 70000 caracteres | `HOST_FAILURE`; ningún fragmento de 13 caracteres del secreto en el `detail` ni en el árbol (54 casos) |
| stderr multilínea con CRLF | sin fragmentos |
| clave inesperada del `structured_output`, `declaredStatus` inválido, `artifact` que no es texto, `structured_output` que es una lista | `OUTPUT_INVALID`, con catálogo y sin él: sin fragmentos |
| `subtype` desconocido, `terminal_reason`, `api_error_status` de texto, `api_error_code`, `api_error` y `error.message`, con exit 0 y con exit 1 | sin fragmentos, con catálogo y sin él |
| `result` con el secreto | no se lee: `OUTPUT_INVALID` sin el secreto |
| `max_structured_output_retries`, 143 y salida 0 sin JSON, con el secreto en stderr | sin fragmentos |
| CLI, texto y `--json`, con el secreto después del corte | sale 2; ni stdout ni stderr lo llevan |

**Sin catálogo,** el `detail` es `el AgentReport no valida`, `el Host no logro una salida que valide
(subtype=…, codigo de salida N)` o `el Host termino con un codigo de salida distinto de 0 (subtype=otro…)`:
texto del motor.

**Rojo visto, con mutaciones mías** (`mutar.py`, sobre una copia):

| Mutación | Aserción que se puso en rojo |
|---|---|
| el motor recorta el texto del Host a 200 antes de redactar | `ni un pedazo del secreto despues del corte llega al detail` |
| el adaptador recorta stderr a 200 antes de devolverlo (el código de la primera construcción) | la misma |
| el mensaje de `validar_informe` vuelve al texto del motor | `un secreto como clave de mas, sin catalogo: el detail no lo lleva` (y una más) |

Mi primera mutación del adaptador recortaba a **100** y quedó en verde: con el corte antes del secreto no
hay fuga que medir, y estaba mal elegida; la rehice con el corte de 200 del código original y se puso en
rojo.

**Dos cosas que no son de Task 4 y las dejo dichas:** el marcador de la redacción
(`[secreto redactado: token-github ghp_Z9y8X7w6... (40 caracteres)]`) deja ver los 12 primeros caracteres
del valor (`secretos.muestra_segura`), y la regla de GitHub exige `\b` delante, así que `xxxghp_…` pegado
a otra palabra no es un secreto para el catálogo. Las dos cosas son del catálogo y de la SecretGate, y valen
igual para el hook y la refutación (hallazgo N9).

**Veredicto: ME-E24 sostenido; ME-I17 sostenido.**

## ME-E28 e ME-I06, la request adulterada

**Cadena en el código:** al entregar, `contrato.huella` del `request.json` del disco contra la huella que
el motor calculó al crearlo, antes que cualquier otra comprobación; si difiere, `REJECTED` con
`CONTRACT_INVALID`, sin `entrega.json` y sin Host; después se entrega la request del disco. La huella es
estructural: reformatear no la cambia.

**Mi reproducción** (`repro_e28.py`, 33 comprobaciones, 0 fallas): un `request.json` editado a mano
entre la creación y la entrega, con la Execution en `REQUESTED` y un Host con eco.

| Edición | Resultado |
|---|---|
| `requestedBy`, `createdAt`, `admission.normativeGate`, `admission.agent.validation`, `.type`, `.domain`, `admission.capabilities`, `admission.dependencies` | `REJECTED`/`CONTRACT_INVALID` en cada una |
| `workUnit.objective`, `workUnit` con una clave de más y la huella de la unidad rehecha, `plan.planVersion`, `plan.planFingerprint` | ídem |
| `executionId`, `taskKey`, `idempotencyKey`, `schema_version`, una clave de más en la raíz, una clave borrada, un tipo cambiado | ídem |
| archivo truncado, vacío, borrado, basura binaria; la request válida de otra Execution copiada encima | ídem |
| el mismo contenido con `indent=4`, compacto, o con escapes unicode | `SUCCEEDED`: se entrega |

En las 24 adulteraciones: sin `entrega.json`, **sin que el Host se lance** (eco ausente), sin
`prompt-de-sistema.md`, y el `result.json` lleva el `requestFingerprint` de lo que el motor escribió.

**Memoria contra disco:** la request correcta quedó en memoria y la del disco, adulterada: el Host no la
recibe; la comparación es contra el disco, no contra la memoria.

**Después del `CONTRACT_INVALID`:** la Execution queda **ilegible**
(`result.json no valida: $.requestFingerprint: no es la huella de su request`), cuenta como abierta, una
`ejecutar` nueva de la misma unidad da `DUPLICATE_EXECUTION`, `--cancelar` sobre ella da error del comando,
`--estado` la informa y sale 0, y otra unidad del mismo plan no queda bloqueada. El `result.json` que queda
es JSON válido y no pasa `validar_resultado` contra la request adulterada. Es lo que dice MD-11′ y el
riesgo R6: **no es una contradicción de la spec vigente**; se destraba replanificando.

**Rojo visto:** al entregar no se compara la huella → 18 aserciones en rojo, la primera
`requestedBy cambiado: REJECTED con CONTRACT_INVALID`.

**Veredicto: ME-E28 sostenido; ME-I06 sostenido.**

## ME-E39 e ME-I23, la configuración hostil

**Cadena en el código:** `motor.configuracion` aplica `comando_invalido` y `perfiles_invalidos` antes de
crear nada; el constructor de `Adaptador` las repite; los argumentos los arma solo el adaptador.

**Mi reproducción** (`repro_e39.py` por el CLI real, un proceso aparte por caso, `repro_args.py`):
**121 configuraciones, 120 rechazadas con exit 2, sin Host, sin residuo bajo `.claude/ejecuciones/` y
sin ExecutionError.**

| Familia | Casos | Resultado |
|---|---|---|
| `comandoHost` con banderas del adaptador o de seguridad: `--bare`, `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions`, `--permission-mode bypassPermissions` y `=bypassPermissions`, `--allowedTools`/`--allowed-tools`, `--disallowedTools`/`--disallowed-tools`, `--agent`, `--agents`, `--json-schema`, `--session-id`, `--model`, `-p`, `--print`, `--output-format`, `--permission-prompts`, `--tools`, `--system-prompt*`, `--append-system-prompt*`, `--settings`, `--setting-sources`, `--mcp-config`, `--strict-mcp-config`; separadas y con `=valor`; en mayúsculas; en un solo argumento (`--permission-mode bypassPermissions`, ` --bare`, `x --bare`, `--`); opciones cortas (`-p`, `-P`, `-pn`, `-c`, `-r`, `-d`, `-vp`); `bypassPermissions` suelto | 75: 74 con exit 2 y una inerte (la envuelta en comillas dobles, abajo) |
| Forma: programa que empieza con `-`, programa con una bandera adentro, texto suelto, lista vacía, `null`, número, elemento vacío, lista anidada, objeto | 9, todas exit 2 |
| Perfil de modelo: `--dangerously-skip-permissions`, `--model`, `--bare`, `-p`, `--agent x`, ` --bare`, `opus --dangerously-skip-permissions`, `opus\n--bare`, `\u202e--bare`, `a b`, 129 caracteres, `$(id)`, `opus;--bare`, comillas, lista, objeto, número, booleano; de otro tier; `perfiles` que no es objeto | 37, todos exit 2 |

**Los argumentos reales** (Host falso con eco, y el cable al Claude Code real):

```
-p --output-format json --json-schema <schema> --session-id <uuid> --permission-mode dontAsk
--permission-prompts none --system-prompt-file <registro>/prompt-de-sistema.md
--tools Read,Glob,Grep,Skill --allowedTools Read,Glob,Grep,Skill --strict-mcp-config [--model haiku]
```

20 comprobaciones propias, 0 fallas: ninguna bandera repetida; ni `--agent`, ni `--bare`, ni
`dangerously`, ni `bypass`; `--tools` igual a `--allowedTools`; el archivo de `--system-prompt-file` es el
cuerpo del agente sin su frente y está en la carpeta de la Execution; `session-id` igual a
`host.sessionRef`; el schema es el del AgentReport, sin propiedades de más; el prompt, por stdin, con
`Seguimos con GCBA-72.` en la primera línea; `--model` solo con perfil y al final. Las herramientas
cambian con las capabilities: `repository.write` da `Edit,Write,Skill`, `tests.run` suma `Bash`.

**Lo que pasa y no está en lo que MD-22′ enumera** (no es una falla de la spec, y lo dejo anotado en N3 y
N4): una bandera envuelta entre comillas como un solo argumento (`"--bare"`, `'--bare'`) pasa la
validación, y el Host la recibe como un argumento literal con comillas, que no empieza con `-`: inerte.
Y 23 opciones de `claude --help` que la spec no enumera pasan: `--add-dir`, `--plugin-dir`,
`--plugin-url`, `--resume`, `--continue`, `--max-budget-usd`, `--fallback-model`,
`--permission-prompt-tool`, `--restricted`, `--safe-mode`, `--bg`, `--file`, `--worktree`,
`--no-session-persistence`, `--effort`, `--betas`, `--verbose`, `--include-hook-events`,
`--disable-slash-commands`, `--debug-file`, `--input-format`, `--ide` y `--chrome`.

**Rojo visto, con mutaciones mías:** la configuración acepta cualquier bandera → 20 aserciones en rojo
(`comandoHost con --bare: sale con 2`); un perfil puede ser cualquier texto → 4 (`perfil de modelo
--dangerously-skip-permissions: sale con 2`); el adaptador agrega `--dangerously-skip-permissions` → 1; el
adaptador vuelve a pasar `--agent` → 1 (`nunca --bare, saltear permisos ni --agent`).

**Veredicto: ME-E39 sostenido; ME-I23 sostenido** con la configuración por defecto y con la hostil.

## ME-E50 contra el Claude Code real

**Estrategia efectiva** (leída del código y comprobada en la corrida): **no usa `--agent`.** Materializa
el agente con su propio texto: el cuerpo de `.claude/agents/<agente>.md`, sin su frente, queda en
`prompt-de-sistema.md` dentro de la Execution y se pasa por `--system-prompt-file`. El AgentReport llega por
**`--json-schema`**: el Host suma su herramienta `StructuredOutput`, el modelo la llama con
`{declaredStatus, artifact}` y el Host valida contra el schema; el adaptador toma las dos claves de
`structured_output` y las pasa por `contrato.validar_informe`. No hay archivo estructurado ni otra
primitiva.

**El camino no interpreta texto.** En `bin/ejecucion/` ningún módulo lee el campo `result` del Host (los
únicos `.get("result")` son del registro de agentes); las únicas expresiones regulares de
`host_claude_code.py` son del schema y de los argumentos, ninguna sobre la salida del modelo; no hay parser
de Markdown ni búsqueda de `STATUS` o de `agentResult`. En la salida cruda del Host real el `result` trae el
mismo JSON como texto, y el adaptador no lo mira.

**Las corridas.** Dos proyectos instalados con `install.ps1` y el plan 2.1 listo (uno bajo una ruta con
nombre corto 8.3, y por eso con una salvedad en la tabla; el otro bajo la ruta larga), perfil
`modelRouting.perfiles.low_cost = haiku`, `ejecutar` por el CLI instalado, con el `claude` del `PATH`
(`claude.CMD` de npm) y, en las que lo dicen, a través de un cable que solo copia la salida cruda del Host.

| # | Unidad | Resultado de `ejecutar` | Lo que se vio |
|---|---|---|---|
| 1 | `leer-sumar` (quality) | `FAILED`/`AGENT_DECLARED_NOT_COMPLETE`, exit 2 | el agente declaró `PARTIAL` (los criterios de aceptación de la Ficha de prueba no coinciden con el objetivo) |
| 2 | `revisar-tests` (quality) | **`SUCCEEDED`, `COMPLETE`**, exit 0, 24,9 s | la huella de `output` es la de `output.md`; sin cambios en el árbol |
| 3 | `revisar-tests-2`, por el cable | **`SUCCEEDED`, `COMPLETE`**, exit 0 | salida cruda abajo |
| 4 | `bloqueada` (backend) | `FAILED`/`AGENT_DECLARED_NOT_COMPLETE` | el agente declaró `BLOCKED` |
| 5 | `intentar-escribir` (backend, solo `repository.read`) | `FAILED`/`AGENT_DECLARED_NOT_COMPLETE` | `BLOCKED`: dice que su sesión tiene `Glob, Grep, Read, Skill, StructuredOutput`, sin `Write`, `Edit` ni `Bash`; ningún archivo de más |
| 6 | `intentar-bash` (quality) | ídem | `BLOCKED`, la misma lista de herramientas |
| 7 | `escribir-nota` (con `repository.write`), **ruta corta 8.3** | `FAILED`/`AGENT_DECLARED_NOT_COMPLETE` | `BLOCKED`: el Host niega el `Write` por la ruta (N2) |
| 8 | `escribir-nota`, **ruta larga** | **`SUCCEEDED`, `COMPLETE`** | `NOTAS.md` aparece en la evidencia como `ADDED`, con su huella |
| 9 | `revisar-tests`, **desde dentro del entorno de esta sesión** | `SUCCEEDED` | `session_id` del Host igual a `--session-id` |
| 10 | `proveedor` con un modelo que no existe | `FAILED`/`PROVIDER_FAILURE`, exit 2 | ver abajo |
| 11 | `proveedor` con una `ANTHROPIC_API_KEY` inválida | `FAILED`/`PROVIDER_FAILURE` | ver abajo |

Recorrí las once Executions con un script (`verificar_todo.py`): en todas, `validar_resultado(result,
request)` vacío, `requestFingerprint` igual a la huella del `request.json`, la huella de `output` igual a la
de los bytes de `output.md` (las nueve que tienen), `prompt-de-sistema.md` en la carpeta, y el vínculo de
sesión de abajo. Cuatro `SUCCEEDED`/`COMPLETE`, cinco `FAILED`/`AGENT_DECLARED_NOT_COMPLETE` (`PARTIAL` y
`BLOCKED`) y dos `PROVIDER_FAILURE`.

**La salida cruda del Host real** (corrida 3, `claude.CMD`, `--output-format json`):

```
exit 0 · type: result · subtype: success · is_error: false · api_error_status: null · terminal_reason: completed
session_id: e646ba49-02eb-4510-81b4-eea043f15005   (== --session-id == host.sessionRef del result.json)
structured_output: {declaredStatus: "COMPLETE", artifact: "<1026 caracteres>"}   claves: artifact, declaredStatus
permission_denials: []
```

La herramienta que lo produjo es `StructuredOutput`: en el flujo `stream-json` de otra corrida aparece
como una llamada del modelo con esas dos claves. No es texto libre que HARNESS parsee.

**Las herramientas, de verdad** (mensaje `init` de `stream-json`, mismos argumentos del adaptador):

| Argumentos | Herramientas que la sesión tiene |
|---|---|
| adaptador, unidad de lectura (`--tools Read,Glob,Grep,Skill --strict-mcp-config`) | `Glob, Grep, Read, Skill, StructuredOutput` |
| lo mismo **sin** `--strict-mcp-config` | las cinco, **y las ocho `mcp__claude_ai_Claude_Docs__*`** de la cuenta |
| adaptador, unidad con `repository.write` | `Edit, Glob, Grep, Read, Skill, StructuredOutput, Write` |
| `--tools ""` | `StructuredOutput` |
| **la estrategia anterior**, `--agent dev-backend --allowedTools Read,Glob,Grep,Skill` | `Read, Glob, Grep, Edit, Write, Skill`, **sin `StructuredOutput`**, y `structured_output` ausente: el hallazgo original reaparece en 2.1.296 con la estrategia vieja |
| `--tools Read,Bash` | solo `Read`: en Windows el Host descarta `Bash` (R5, vigente) |

**Una herramienta fuera de lo que la unidad pide, rechazada** (ruta larga, `dontAsk`, `--permission-prompts
none`):

| Caso | Resultado |
|---|---|
| `Write` en `--tools` y en `--allowedTools` | se usa, el archivo se crea, `permission_denials` vacío |
| `Write` en `--tools` y **no** en `--allowedTools` | `permission_denials: [Write …]`, el archivo no se crea: `dontAsk` la niega |
| `Write` fuera de `--tools` | la sesión no la tiene, el modelo no la llama, el archivo no se crea |
| las unidades `intentar-escribir` e `intentar-bash` por `ejecutar` | `BLOCKED`: sin `Write`, `Edit` ni `Bash` en la sesión; ningún archivo de más |

La garantía «el agente recibe solo las herramientas de la unidad» (ME-I24) **está demostrada contra el
Host real**: por existencia (`--tools`), y, si una herramienta existiera sin estar permitida, por la
negativa de `dontAsk`.

**SessionTaskBinding.** En las once Executions, `.claude/runtime/sessions/<sessionRef>/task.json` es
`session-task-binding/1.0` con `taskKey: GCBA-72`, `source: user-prompt` y `sessionId` igual al
`host.sessionRef`: lo escribió el hook del propio Host. La primera línea del prompt es lo que lo logra: en
una prueba aparte, con una segunda tarea con estado en el proyecto, una sesión sin esa línea queda sin
vínculo y con ella queda vinculada a `GCBA-72`. La transcripción de las cuatro sesiones que abrí empieza con `Seguimos con
GCBA-72.` y la WorkUnit en JSON, así que el prompt llegó por stdin.

**El error del proveedor, real:**

| Disparo | Código de salida | `is_error` | `subtype` | `api_error_status` | `terminal_reason` | `error` | Resultado |
|---|---|---|---|---|---|---|---|
| modelo inexistente | 1 | true | `success` | 404 | `api_error` | ausente | `PROVIDER_FAILURE` |
| `ANTHROPIC_API_KEY` inválida | 1 | true | `success` | 401 | `api_error` | ausente | `PROVIDER_FAILURE` |

El `detail` lleva `subtype=success, codigo de salida 1 · terminal_reason=api_error · api_error_status=404`
y el principio de stderr redactado. No depende de `error.type`. Con un esquema imposible, el Host real
contesta en texto: `success` con exit 0 y sin `structured_output`; el motor, con esa forma en el Host falso,
da `OUTPUT_INVALID`.

**Lo que no pude mostrar:** un `error_max_structured_output_retries` real (el modelo desiste y contesta en
texto), así que no sé con qué código de salida lo emite el Host (hallazgo N8).

**Costo:** 9 llamadas pasaron por el cable (USD 0,038); con las demás, unos USD 0,15 (estimado).

**La lectura.** `lectura.md` está **sin firmar**: su banner dice «mientras esté así, el refutador lo
rinde `sin sustento`». Ya no espera `error.type`, y describe la forma implementada; tiene «Evidencia
preparada» (qué se ejecutó, qué se vio, la forma del Host, qué resultó) y `Observado:` vacío. Yo no soy
una persona que firma, y ADR-0010 no aplica a un solo escenario: **no firmé ni completé nada ahí**. Lo que
vi queda arriba, para quien firme.

**Veredicto: ME-E50 técnicamente sostenido por la corrida real; `sin sustento` por la firma.** No es
`leído`.

## La tabla que se pidió

| Hallazgo original | Primera verificación | Reverificación | Evidencia |
|---|---|---|---|
| ME-E24 | contradicho | **sostenido** | 92 comprobaciones propias, secreto después de 0 a 70 000 caracteres de stderr y en cada campo del Host, con y sin catálogo; 3 mutaciones propias en rojo; `test_me_e24` 18/18 |
| ME-E28 | contradicho | **sostenido** | 33 comprobaciones propias: 24 adulteraciones, todas `REJECTED`/`CONTRACT_INVALID` sin Host; 3 equivalentes se entregan; `test_me_e28` 31/31 |
| ME-E39 | contradicho | **sostenido** | 121 configuraciones por el CLI, 120 rechazadas con exit 2 y la 121.ª inerte; argv real sin duplicados; 4 mutaciones propias en rojo; `test_me_e39` 41/41 |
| ME-E50 | contradicho | **sin sustento, solo por la firma**; técnicamente sostenido | once corridas reales (2.1.296): cuatro `SUCCEEDED`/`COMPLETE`, cinco `AGENT_DECLARED_NOT_COMPLETE` (`PARTIAL` y `BLOCKED`), dos `PROVIDER_FAILURE`; `structured_output` real; herramientas por `init`; vínculo; `lectura.md` sin firmar |
| ME-I17 | contradicho | **sostenido** | ídem ME-E24, y `test_me_e33` 5/5 |
| ME-I06 | contradicho | **sostenido** | ídem ME-E28 |
| ME-I23 | contradicho | **sostenido** | ídem ME-E39 |

## Escenarios

57 escenarios: 56 por la suite y 1 de lectura (los que cuenta la spec enmendada, §34.4), y 32
invariantes. «N/N» son las aserciones del escenario en `72_motor_de_ejecucion.py`: el archivo pasó 546/546
en el focalizado, en cuatro corridas completas mías y en la segunda compuerta; en la primera compuerta
falló una aserción de ME-E18 (N1).

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| ME-E01 | Camino feliz: turno 1, request, entrega, output, `SUCCEEDED` válido, huellas y sesión | sostenido | sí | `test_me_e01` 14/14; y las corridas reales 2, 3, 8 y 9 |
| ME-E02 | `PARTIAL`, `BLOCKED` y `FAILED` dan `AGENT_DECLARED_NOT_COMPLETE` | sostenido | sí | `test_me_e02` 15/15; reales: `PARTIAL` y `BLOCKED` |
| ME-E03 | Sin `structured_output`, reintentos agotados, clave de más o enum fuera: `OUTPUT_INVALID` | sostenido | sí | `test_me_e03` 16/16; real: esquema imposible → `success` sin `structured_output` |
| ME-E29 | Nadie lee `result` ni el artifact | sostenido | sí | `test_me_e29` 9/9; búsqueda estática propia sin lecturas de `result` |
| ME-E04 | Fallas del Host después de la entrega: `HOST_FAILURE` | sostenido | sí | `test_me_e04` 15/15 |
| ME-E32 | Proveedor identificado: `PROVIDER_FAILURE` (forma real) | sostenido | sí | `test_me_e32` 6/6; 47 de mi `repro_e56`; real: 404 y 401. Mutación propia: solo `error.type` → rojo |
| ME-E05 | Señal externa o Ctrl-C sin pedido: `HOST_INTERRUPTED` | sostenido | sí | `test_me_e05` 6/6 |
| ME-E06 | `--cancelar` con el motor vivo | sostenido | sí | `test_me_e06` 14/14 |
| ME-E31 | El límite da `TIMEOUT` y mata el árbol | sostenido | sí | `test_me_e31` 6/6 |
| ME-E33 | Sin catálogo después del AgentReport: `ENGINE_FAILURE`, sin `output.md` | sostenido | sí | `test_me_e33` 5/5 |
| ME-E34 | `REQUESTED` huérfana bloquea y se cancela; `RUNNING` cortada da `HOST_INTERRUPTED` | sostenido | sí | `test_me_e34` 11/11 |
| ME-E07 | El plan cambia entre la creación y la entrega: `PLAN_CHANGED` | sostenido | sí | `test_me_e07` 3/3 |
| ME-E08 | El flujo deja de permitir: `DELEGATION_NOT_ALLOWED` | sostenido | sí | `test_me_e08` 6/6 |
| ME-E09 | Fuente en alerta: `NORMATIVE_GATE_BLOCKED` | sostenido | sí | `test_me_e09` 5/5 |
| ME-E10 | El agente deja de ser ruteable: `AGENT_UNAVAILABLE` | sostenido | sí | `test_me_e10` 2/2 |
| ME-E11 | Una capability deja de estar: `CAPABILITY_UNAVAILABLE` | sostenido | sí | `test_me_e11` 2/2 |
| ME-E12 | Dependencias: solo `SUCCEEDED` en la misma huella | sostenido | sí | `test_me_e12` 7/7 |
| ME-E27 | Al pedir gana la primera falla y no queda nada escrito | sostenido | sí | `test_me_e27` 7/7 |
| ME-E28 | `request.json` editado a mano: `CONTRACT_INVALID`, en cada campo | sostenido | sí | `test_me_e28` 31/31; `repro_e28` 33/33; mutación propia: 18 en rojo |
| ME-E30 | Plan 2.0, JSON cortado, otra TaskKey, ids repetidos | sostenido | sí | `test_me_e30` 8/8 |
| ME-E41 | `jira.*` y `repository.write` sin `Write`: `CAPABILITY_UNAVAILABLE` | sostenido | sí | `test_me_e41` 8/8 |
| ME-E42 | Sin definición del agente: `REJECTED`; un Host que no lo carga: `HOST_FAILURE` | sostenido | sí | `test_me_e42` 9/9 |
| ME-E13 | Una `REQUESTED` o `RUNNING` bloquea sin escribir | sostenido | sí | `test_me_e13` 5/5 |
| ME-E14 | Un `SUCCEEDED` bloquea | sostenido | sí | `test_me_e14` 4/4 |
| ME-E15 | Después de `FAILED`, turno 2 | sostenido | sí | `test_me_e15` 4/4; mi `repro_recuperacion` |
| ME-E16 | Lo mismo después de `CANCELLED` | sostenido | sí | `test_me_e16` 4/4 |
| ME-E17 | Lo mismo después de `REJECTED` | sostenido | sí | `test_me_e17` 4/4 |
| ME-E18 | EX-F01: dos procesos, una Execution, un duplicado, un turno | **sostenido, con una reserva** | sí | `test_me_e18` 10/10 en el focalizado, en cuatro corridas completas mías y en la segunda compuerta, y **9/10 en la primera compuerta (10-10, 21:10)**; 848 carreras propias sin una anomalía. Ver N1 |
| ME-E19 | EX-F02: la propia pasa la 15; otra abierta o `SUCCEEDED`, `DUPLICATE_EXECUTION` | sostenido | sí | `test_me_e19` 6/6 (la mitad «o SUCCEEDED» sigue sin test propio, como en la primera verificación) |
| ME-E37 | El barrido no toca una carpeta con el candado tomado, ni una joven | sostenido | sí | `test_me_e37` 5/5 |
| ME-E52 | Un residuo sin turno no es una Execution y se barre | sostenido | sí | `test_me_e52` 10/10; mi repro: no aparece en `--estado` y la recuperación lo borra |
| ME-E20 | Una `RUNNING` huérfana: `HOST_INTERRUPTED`, sin reentregar ni matar | sostenido | sí | `test_me_e20` 15/15; mi repro con procesos reales: 12/12 |
| ME-E53 | Una cancelación persistida gana sobre la muerte del motor | sostenido | sí | `test_me_e53` 12/12; mi repro: `CANCELLED`, y el Host sobrevive |
| ME-E21 | Escribir otra vez no cambia un byte; un corte no deja destino ni temporal | sostenido | sí | `test_me_e21` 15/15; mi repro: los cinco archivos, `prompt-de-sistema.md` incluido |
| ME-E22 | Un resultado tardío no pisa | sostenido | sí | `test_me_e22` 4/4 |
| ME-E23 | Rutas no canónicas no se persisten | sostenido | sí | `test_me_e23` 6/6 |
| ME-E24 | Secretos en artifact, `requestedBy`, `detail` y WorkUnit, y en cualquier texto del Host | sostenido | sí | `test_me_e24` 18/18; `repro_e24` 92/92; tres mutaciones propias en rojo |
| ME-E35 | `--estado` no escribe, marca huérfanas e informa ilegibles | sostenido | sí | `test_me_e35` 10/10; mi repro: sin cambios bajo `.claude/` |
| ME-E36 | Ids con `fullmatch` y sin repetidos | sostenido | sí | `test_me_e36` 8/8 |
| ME-E25 | Repo sucio: lo limpio cambiado es de la Execution, lo sucio no se atribuye | sostenido | sí | `test_me_e25` 5/5; mi repro: 3 chequeos; real: `NOTAS.md` `ADDED` |
| ME-E43 | Sin git: `CHANGES_UNRESOLVED`; con un commit del Host, sus archivos | sostenido | sí | `test_me_e43` 4/4 |
| ME-E44 | Otra Execution `RUNNING` del proyecto: `CHANGES_UNATTRIBUTABLE` | sostenido | sí | `test_me_e44` 3/3 (la mitad «otra tarea» sigue sin test propio) |
| ME-E38 | `--model` solo con un perfil declarado; nunca `--max-budget-usd` | sostenido | sí | `test_me_e38` 9/9; real: `--model haiku` |
| ME-E39 | Nunca `--bare`, saltear permisos ni `--agent`; siempre las banderas de seguridad; la configuración hostil falla antes | sostenido | sí | `test_me_e39` 41/41; `repro_e39` 121 y `repro_args` 20; cuatro mutaciones propias en rojo |
| ME-E40 | `--tools` y `--allowedTools` con el mismo conjunto mínimo; el schema intacto por el shim; el prompt por stdin | sostenido | sí | `test_me_e40` 11/11; real: a través de `claude.CMD`, el schema llega y el prompt entra por stdin |
| ME-E45 | El motor no reconcilia; sin `state.json`, `DELEGATION_NOT_ALLOWED` | sostenido | sí | `test_me_e45` 6/6; mi repro: `runtime/tasks` igual antes y después |
| ME-E54 | `comandoHost` inválido falla antes, sin residuo | sostenido | sí | `test_me_e54` 22/22; mi repro por el CLI: 5 formas, exit 2, sin residuo |
| ME-E55 | `limiteSegundos` y un `harness.config.json` ilegible fallan antes | sostenido | sí | `test_me_e55` 30/30; mi repro: 9 formas inválidas con exit 2, y 1800 por defecto |
| ME-E26 | En un proyecto instalado, `ejecutar` deja `SUCCEEDED` | sostenido | sí | `72-motor-de-ejecucion-instalador.ps1` 12/12; y mis dos instalaciones reales |
| ME-E46 | `contrato.py` puro; sin contabilidad; escritura solo bajo `.claude/ejecuciones` | sostenido | sí | `test_me_e46` 9/9 |
| ME-E47 | Sin concurrencia ni SDK; trece subcomandos; el Host solo desde el adaptador | sostenido | sí | `test_me_e47` 8/8; búsqueda estática propia en `bin/` y `comun/`: ningún import |
| ME-E48 | Modelo canónico y ADR-0015; ADR-0013 y ADR-0014 intactos | sostenido | sí | `test_me_e48` 16/16; ver *Documentos* |
| ME-E49 | Lo protegido es el de la base, sin archivos nuevos | sostenido | sí | `test_me_e49` 20/20; `git diff --stat HEAD` sobre lo protegido: vacío |
| ME-E50 | Una corrida real contra Claude Code: estrategia de §34.3 | **sin sustento** (firma) | no consta | técnicamente sostenido; `lectura.md` sin firmar. Ver su sección |
| ME-E51 | `Invoke-Tests.ps1` sale con 0 | sostenido, con una reserva | no consta | la primera compuerta (10-10, 21:10) salió **1** por una aserción de ME-E18 (N1); la segunda (13-10) salió **0**: 43775/43775, 1881,6 s |
| ME-E56 | Exit distinto de 0 nunca es `SUCCEEDED`: 1 `HOST_FAILURE`, 143 `HOST_INTERRUPTED`, 1 con `api_error_status` `PROVIDER_FAILURE` | sostenido | sí | `test_me_e56` 6/6; `repro_e56` 47/47; mutación propia: 6 en rojo |
| ME-E57 | Un código de admisión devuelto por el adaptador después de la entrega es `ENGINE_FAILURE` | sostenido | sí | `test_me_e57` 4/4; mis 19 códigos (los 16 del contrato que no son de corrida, uno inventado, `None` y vacío) dan `ENGINE_FAILURE`; mutación propia: 2 en rojo |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** De las mutaciones de la spec
> (§34.5) reproduje con otras mías las de ME-E24, ME-E28, ME-E32, ME-E39, ME-E56 y ME-E57 (once
> mutaciones, diez en rojo al primer intento y la undécima rehecha), y no las de ME-E40.

## Invariantes

| Invariante | Evidencia | Veredicto |
|---|---|---|
| ME-I01 a ME-I05 | sin cambios; ME-E01, E13, E14, E18, E21 y mi carrera de procesos (ver N1 sobre una anomalía) | sostenido |
| ME-I06 | al entregar se compara la huella del `request.json` del disco y se derivan las quince; 24 adulteraciones y 3 equivalentes (ME-E28) | **sostenido** |
| ME-I07 a ME-I11 | sin cambios; ME-E15 a ME-E19 | sostenido |
| ME-I12, ME-I13 | el adaptador devuelve un AgentReport de dos claves, de `structured_output`; ninguna lectura de `result` en `bin/ejecucion/`; el `result` del Host real no se mira | sostenido |
| ME-I14, ME-I15 | no se vuelve a entregar; solo escribe quien tiene el candado; mi repro con procesos reales | sostenido |
| ME-I16 | sin cambios; ME-E23 | sostenido |
| ME-I17 | redacción antes del recorte en todo texto del Host; sin catálogo, texto del motor | **sostenido** |
| ME-I18 | `contrato.py`, `evidencia.py` y `proceso.py` iguales por hash; sin imports de contabilidad | sostenido |
| ME-I19, ME-I20 | sin cambios; ME-E07, E08, E45 | sostenido |
| ME-I21 | residuos y carpetas sin turno no son Executions; mi repro de ME-E52 | sostenido |
| ME-I22 | ME-E05, E06, E34 y E53; sigue la reserva de MD-24 (hallazgo 9 de la primera verificación) | sostenido |
| ME-I23 | ni la configuración ni los perfiles meten `--bare` ni salteos de permisos; el argv real no los lleva | **sostenido** |
| ME-I24 | `init.tools` del Host real = el conjunto de la unidad + `StructuredOutput`, sin MCP; una herramienta no permitida, negada | **sostenido contra el Host real** |
| ME-I25, ME-I26, ME-I27, ME-I28 | sin cambios; ME-E36, E46, E47, E52 | sostenido |
| ME-I29 | el motor filtra: 19 códigos que no son de corrida, devueltos por un adaptador, dan `ENGINE_FAILURE` | **sostenido en el motor** (ya no depende del adaptador) |
| ME-I30 | `requestFingerprint` es la huella del `request.json` persistido, también en las corridas reales | sostenido |
| ME-I31 | 121 configuraciones de `comandoHost` y de perfiles, y 14 más de `comandoHost`, `limiteSegundos`, config ilegible y sin `claude` en el `PATH`: exit 2, sin residuo | sostenido |
| ME-I32 | un exit distinto de 0 nunca produce `SUCCEEDED`: 8 códigos y 3 formas | sostenido |

## Regresión: lo que ya estaba sostenido y sigue

Corrí cada uno de los diez prioritarios con script propio, sobre el código corregido:

| Escenario | Qué reproduje | Resultado |
|---|---|---|
| ME-E18 | 8 rondas con barrera de salida (2 a 4 procesos), más 240 carreras con la mecánica de la suite y 480 con tres grupos en paralelo, más 120 con barrera | 1 `SUCCEEDED`, n−1 `DUPLICATE_EXECUTION`, un turno, sin temporales, **en las 848**; la anomalía de la compuerta no se reprodujo (N1) |
| ME-E20 | un motor real, matado a la fuerza sin su árbol, con el Host vivo | `--estado` la marca huérfana; la recuperación la cierra `FAILED`/`HOST_INTERRUPTED` con `startedAt` de la entrega; no mata al Host ni reentrega |
| ME-E21 | reescribir los cinco archivos de una Execution | `FileExistsError` en cada uno, sin un byte ni un `mtime` cambiado, sin temporales |
| ME-E25 | repo sucio, el Host cambia lo limpio y crea un archivo; después cambia lo sucio | `RESOLVED` con los dos archivos y sin el sucio; `CHANGES_UNATTRIBUTABLE` con `files: []` |
| ME-E35 | `--estado` con una huérfana | sale 0, JSON, sin cambios bajo `.claude/` |
| ME-E45 | una corrida entera; después sin `state.json` | `runtime/tasks` igual; `DELEGATION_NOT_ALLOWED` y dice cómo reconciliar |
| ME-E52 | un residuo con request válida y un temporal, sin turno | no aparece, no bloquea, y la recuperación lo borra pasados diez minutos |
| ME-E53 | una cancelación persistida y el motor muerto | `CANCELLED`, sin AgentReport, y el Host sigue vivo |
| ME-E54 | cuatro `comandoHost` inválidos, y la clave ausente sin `claude` en el `PATH` | exit 2, sin residuo, sin ExecutionError |
| ME-E55 | cinco `limiteSegundos` inválidos, `ejecucion` que no es objeto y tres configs ilegibles (no objeto, cortada, vacía); 1800 por defecto | exit 2, sin residuo |

**0 regresiones sobre lo que sostuvo la primera verificación.** El `registro.py` cambió en un docstring y
nada más; `evidencia.py` y `proceso.py` son idénticos por hash.

## Tests focalizados

Corridos en serie sobre el árbol real, el 10-10-2026:

| Caso | Aserciones | Exit | Segundos |
|---|---|---|---|
| 72_motor_de_ejecucion.py | 546/546 | 0 | 132,3 |
| 65_contrato_de_ejecucion.py | 673/673 | 0 | 44,6 |
| 64_modelo_de_dominio.py | 1038/1038 | 0 | 79,6 |
| 71_plan_2_1.py | 276/276 | 0 | 17,5 |
| 61_flujo_precondiciones.py | 184/184 | 0 | 15,3 |
| 62_estado_del_flujo.py | 177/177 | 0 | 42,3 |
| 63_compuerta_del_flujo.py | 487/487 | 0 | 76,6 |
| 65_fail_closed.py | 284/284 | 0 | 11,9 |
| 67_integracion_frescura.py | 43/43 | 0 | 18,8 |
| 72-motor-de-ejecucion-instalador.ps1 | 12/12 | 0 | 13,5 |
| 63-harness-unico-instalador.ps1 | 188/188 | 0 | 178,4 |

Además, `72_motor_de_ejecucion.py` entero cuatro veces seguidas con una instrumentación mía que guarda lo
que devuelve cada proceso hijo de las carreras: 546/546 las cuatro, 0 hijos con excepción (208 a 272 s
cada una).

## Suite completa

```
cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -File tests\Invoke-Tests.ps1 < NUL"
```

| Corrida | PowerShell | Python | Total | Exit | Duración |
|---|---|---|---|---|---|
| 1 (21:10) | 916/916 | 42858/42859 | 43774/43775, 1 falló | **1** | 1701 s |
| 2 (13-10, 09:08) | 916/916 | 42859/42859 | 43775/43775 | **0** | 1882 s |

La que falló en la primera:

```
MAL 72_motor_de_ejecucion / ME-E18 veinte carreras sin punto de encuentro: una Execution, un duplicado y un
turno cada vez no esta vacio: <['carrera-11: 1 Execution(s), [], 1 turno(s)']>
```

La segunda salió con 0, sobre el mismo árbol (la foto por hash es la misma). **Una corrida que no cuenta:**
la primera vez que lancé la segunda (10-10, 21:56) la máquina se suspendió unos dos días y medio con la
corrida en curso; con el reloj saltado no sirve de compuerta, la maté y el árbol quedó igual, por hash.
La que cuenta es la del 13-10, con la suspensión impedida mientras corre.

Antes y después de las corridas: `pre-tool-use.py` `b9cde9d`, `zonas.py` `e996067`, `contrato.py`, los dos
schemas de Task 3 y ADR-0014 con su huella de la base; `.claude/ejecuciones/` no existe en el repo.

## La falla intermitente de ME-E18 (hallazgo N1)

- **Qué se vio:** una aserción de ME-E18, en la primera compuerta (10-10, 21:10). En la carrera 11 de las veinte sin
  punto de encuentro, un proceso terminó con una Execution, el otro **no** devolvió
  `DUPLICATE_EXECUTION` (devolvió una excepción o nada), y quedó un solo turno. El test no guarda el texto
  de la excepción, así que no sé cuál fue.
- **Lo que quedó cumplido igual:** una Execution, un turno. Lo que no se cumplió es «un
  `DUPLICATE_EXECUTION`».
- **No se repitió:** `72_motor_de_ejecucion.py` pasó 546/546 en el focalizado de las 20:33, en las cuatro
  corridas instrumentadas y en la segunda compuerta; mis 848 carreras propias, entre ellas 120 con barrera de salida y 480 con tres
  grupos en paralelo, no dieron ninguna anomalía.
- **Mecanismo compatible, forzado, no observado en esa corrida:** cada `ejecutar` empieza con
  `recuperar`, que sondea el candado de toda carpeta de la tarea (`candado_libre`, `limpiar_temporales`). Si
  la sonda de un proceso toma el candado en el instante en que otro lo pide, `Vida` falla con
  `PermissionError`, `registro.crear` borra su carpeta y `ejecutar` levanta
  `ErrorDelComando: no se pudo crear la Execution (PermissionError)`. Lo forcé de forma determinista
  (`repro_ventana.py`): sin residuo y sin turno, y la misma unidad corre bien después. Es la ventana que la
  primera verificación ya anotó como hallazgo 27 (microsegundos, «más probable con workers»).
- **No es una regresión de la corrección:** `registro.py` y el prólogo de `ejecutar` son idénticos a los
  de la primera construcción (un docstring de diferencia); la primera verificación corrió 59 carreras sin
  ver nada.
- **Cómo lo rindo:** `sostenido, con una reserva`, como la primera verificación rindió ME-I22. La seguridad
  (una Execution por clave, un turno, sin residuo) se sostuvo en todo lo corrido, y la compuerta no es
  determinista por una ventana ya anotada. Si se lee como contradicción de «siempre lo mismo» de ME-E18,
  lo decide la persona.

## Alcance

- **Implementación:** sin Graph Execution, DAG, scheduler, colas, workers, paralelismo, hilos, `asyncio`,
  `concurrent`, `sched`, LangGraph, LangChain, reintento automático, backoff, checkpoint ni reanudación.
  Una búsqueda de `threading`, `multiprocessing`, `asyncio`, `concurrent`, `sched`, `queue`, `langgraph`,
  `langchain`, `retry`, `backoff`, `checkpoint`, `resume`, `scheduler`, `DAG` y `worker` en
  `bin/ejecucion/` encuentra solo dos docstrings que dicen que no los hay; ningún import de esos módulos
  en `harnesses/` ni `comun/`; lo agregado a `dev-harness.py` no los nombra.
- **Comportamiento de Task 5:** el motor no elige la siguiente unidad, no recorre dependencias para
  ejecutarlas y no corre varias. Mis carreras de procesos son varios `ejecutar`, cada uno de una unidad.
- **Task 5 no empezó.**

## Archivos protegidos

`git diff --stat HEAD` sobre `comun/hooks/` (con `tool_policy.py`), `install.ps1`, `manifest.json`,
`VERSION`, `CHANGELOG.md`, `UPGRADE.md`, `bin/flujo/`, `bin/estado_de_tarea/`, `bin/orquestacion/`,
`bin/contabilidad/` y ADR-0013: **vacío**. `contrato.py`, los dos schemas de Task 3 y ADR-0014: misma
huella que la base. ADR-0016 no existe, y no hace falta: ADR-0015 se enmendó dentro de sí mismo, sin tocar
sus siete decisiones. Mi foto del árbol: 805 archivos, sin nuevos, sin borrados y sin cambiados, y `git status` con las mismas 18 entradas que al empezar.

## Documentos

- **Modelo canónico:** `### Claude Code ≠ HARNESS` dice que desde Task 4 el motor lanza el Host y que el
  agente y el modelo los corre Claude Code; `### Plan ≠ Execution` dice que una Execution la crea el
  motor; el Host Adapter está en *Lo que existe ahora*. Ya no dice «no existe ninguna ejecución», y no hay
  Task 5 como implementada. **Siguen en condicional** ExecutionId (`lo generaría la ExecutionAdmission`),
  ExecutionError (`lo escribirían la admisión y el motor`) y ExecutionEvidence (`la observaría el motor`);
  AgentReport dice `es de la Task siguiente`, y esa Task es esta. Está anotado en `PENDIENTES-FH.md` y no
  era una de las tres correcciones prometidas (hallazgo N6).
- **ADR-0015:** dice 27 contradicciones; la decisión 5 lleva una nota que remite a la «Enmienda
  post-refutación», que documenta la estrategia sin `--agent`, las herramientas exactas, la forma real del
  proveedor, el exit distinto de 0, la configuración sin banderas, y el orden redactar-antes-de-recortar.
  La decisión 2 sigue listando seis archivos del registro, sin `prompt-de-sistema.md` (N7). ADR-0014 no
  cambió.
- **`lectura.md`:** refleja la estrategia vigente y no espera `error.type`. Sin firmar.

## Riesgos aceptados

| | Estado después de reverificar |
|---|---|
| R1, el Host que sobrevive al motor | sigue abierto; lo vi: el Host siguió vivo y `--estado` lo avisó |
| R2, la `REQUESTED` huérfana | sigue abierto, declarado; ME-E34 sostenido |
| R3, lo no documentado del Host | se achicó: observado en 2.1.296; se cierra con la firma de ME-E50 |
| R4, `ejecutar` sin fila en la política de herramientas | sigue; `tool_policy.py` igual a `HEAD` |
| R5, `Bash` no existe en la sesión del Host en Windows | confirmado en 2.1.296 (`--tools Read,Bash` da solo `Read`) |
| R6, una request adulterada deja la Execution ilegible | confirmado: ilegible, abierta, y solo se destraba replanificando |
| R7, un Host matado desde afuera es `HOST_FAILURE` en Windows | no lo reprobé |

## Hallazgos nuevos

Ninguno bloquea por sí solo, y ninguno amplía la Task. Quedan escritos acá, porque la persona pidió no
tocar `PENDIENTES-FH.md` en la verificación.

- **N1. ME-E18, una aserción en rojo en la compuerta (arriba).** Deuda preexistente, ventana ya anotada
  (hallazgo 27 de la primera verificación); decisión de la persona sobre cómo se lee «siempre».
- **N2. El Host rechaza escribir en una ruta con un nombre 8.3.** Con el proyecto en
  `C:\Users\204350~1\…`, `Write` da `permission_denials` también con `acceptEdits` («la ruta contiene
  `204350~1`… requiere aprobación manual»). No es de la estrategia: con la ruta larga, una unidad con
  `repository.write` termina `SUCCEEDED` y `NOTAS.md` sale en la evidencia. Observación del Host; un
  proyecto bajo `%TEMP%` de este usuario cae en esto.
- **N3. Opciones del Host que MD-22′ no enumera y pasan por `comandoHost`:** `--add-dir`, `--plugin-dir`,
  `--plugin-url`, `--resume`, `--continue`, `--max-budget-usd`, `--fallback-model`,
  `--permission-prompt-tool`, `--restricted`, `--safe-mode`, `--bg`, `--file`, `--worktree` y otras. La spec
  enumera una lista y se cumple; el que escribe `comandoHost` es el dueño del proyecto.
- **N4. Una bandera entera entre comillas pasa la validación** (`"--bare"`, `'--bare'`): llega al Host como
  un argumento literal que no empieza con `-`. Inerte; lo vi con el Host falso, no con el real.
- **N5. `admision.al_entregar(…, huella=None)` se salta la comprobación.** Su único llamador la pasa; un
  llamador futuro que no la pase la desactivaría sin avisar.
- **N6. Modelo canónico:** ExecutionId, ExecutionError, ExecutionEvidence y AgentReport siguen hablando del
  motor en condicional, y AgentReport dice «es de la Task siguiente». Precisión documental, ya en
  `PENDIENTES-FH.md` (19 de la primera verificación).
- **N7. ADR-0015, decisión 2:** lista seis archivos del registro y no `prompt-de-sistema.md`; la
  «Enmienda» sí lo nombra. Precisión documental.
- **N8. `error_max_structured_output_retries` con exit distinto de 0.** §21 lo manda a `OUTPUT_INVALID` y
  MD-10′ manda a `HOST_FAILURE` todo exit distinto de 0 que no sea proveedor ni señal; con un exit 1 el
  motor da `HOST_FAILURE`. El Host real no me dejó emitir ese `subtype`, así que no sé qué código de salida
  trae. Ambigüedad de spec, a decidir cuando se sepa.
- **N9. El marcador de la redacción muestra 12 caracteres del secreto,** y las reglas de la SecretGate
  piden un límite de palabra delante. Del catálogo, no de Task 4.
- **N10. Residuos en `%TEMP%`:** la suite sigue dejando `me72-*.guion.json`, `.eco.json`, `.marca-*` y
  `me72-hijo-*.py` (705 archivos y 7 carpetas `me72*` al terminar mis corridas, y centenares de `harness-*`:
  6204 carpetas en `%TEMP%` al final, 5181 al empezar; mis dos suites completas y el resto de mis
  corridas suman a eso). La corrección no los elimina ni los empeora; ya está en la lista de la primera
  verificación (18).

## Lo que ningún test cubre y se mira con los ojos

- **La firma de ME-E50.** Una persona que no construyó abre `lectura.md`, mira lo de arriba (o lo corre de
  nuevo: dos proyectos de prueba quedaron en `%TEMP%\ref2-long-01a6f898` y
  `%TEMP%\ref2-me50-dca12ce4`, con sus transcripciones bajo `~\.claude\projects\`), escribe en
  `Observado` lo que vio y firma `Leyó: <nombre>`, con fecha. ADR-0010 no la puede delegar: es un solo
  escenario.
- **El costo de una corrida con el modelo que elige el Host:** los USD 0,43 a 0,55 de la primera
  verificación se midieron sin perfil; con `haiku` son centavos.

## Veredicto acumulado de la reverificación

| | Sostenidos | Leídos | Contradichos | Sin sustento |
|---|---|---|---|---|
| Por la suite (56) | 56 (con reserva: ME-E18 y ME-E51) | — | 0 | 0 |
| De lectura (1) | — | 0 | 0 | 1 (ME-E50, solo por la firma) |
| **Total (57)** | **56** | **0** | **0** | **1** |
| Invariantes (32) | 32 | — | 0 | 0 |

```
verificacion.md con un sin sustento (la firma de ME-E50) → EN CURSO
```

Task 4 no cierra hasta que una persona que no construyó firme `lectura.md`; con esa firma y la compuerta
en verde, no queda nada abierto del lado del código. Task 5 no queda habilitada.

---

## Cierre formal de Task 4 — 13-10-2026

> 📌 **Esta sección cierra la Task y no reescribe nada de lo de arriba.** La primera verificación y la
> reverificación post-corrección quedan como se escribieron; el único cambio fuera de esta sección es
> la línea de **Estado** del encabezado. El cierre es el de la Task arquitectónica, no el de una
> versión: no hay commit, tag, `VERSION`, `CHANGELOG` ni `UPGRADE`.

### ME-E50, leído

| | |
|---|---|
| Quién leyó | Nahuel Palacio |
| Fecha | 13-10-2026 |
| Camino | firma dictada ([ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)); [ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md) no aplica, es un solo escenario, y se firma `Leyó:` |
| Qué leyó | la evidencia de la reverificación (once corridas reales con Claude Code 2.1.296); lo dictó con sus palabras y quien construyó lo transcribió textual a `lectura.md`, en `Observado` |
| Veredicto | **`leído`** (antes `sin sustento`, solo por la falta de firma) |

`leído` vale menos que `sostenido` y se cuenta aparte. R3 (lo no documentado del Host) queda cerrado para
Task 4 mediante este `leído`.

### Conteo final

```
57 escenarios
  56 sostenidos   (por la suite; con reserva ME-E18 y ME-E51, hallazgo N1)
   1 leído        (ME-E50)
   0 contradichos
   0 sin sustento
32 invariantes: 32 sostenidos, 0 contradichos
```

| | Sostenidos | Leídos | Contradichos | Sin sustento |
|---|---|---|---|---|
| Por la suite (56) | 56 | — | 0 | 0 |
| De lectura (1) | — | 1 | 0 | 0 |
| **Total (57)** | **56** | **1** | **0** | **0** |
| Invariantes (32) | 32 | — | 0 | 0 |

Los 56 escenarios de la suite y los 32 invariantes son los de la reverificación, sin cambios. ME-E18
sigue `sostenido, con una reserva` (la ventana de la sonda del candado, N1), y no se reabrió.

### La compuerta

La última compuerta válida es la del 13-10-2026, 09:08, sobre el árbol final:

```
916/916 pasaron (PowerShell).
42859/42859 pasaron (Python).
43775/43775 pasaron.
exit=0 · 1882 s
```

No se volvió a correr. Desde esa corrida solo cambiaron documentos de este cambio
(`lectura.md`, `spec.md`, `informe-de-construccion.md` y este archivo), y ningún test los lee. Por hash,
sobre 805 archivos: ninguno nuevo, ninguno borrado y cuatro cambiados, esos cuatro. `git status`, las
mismas 18 entradas que antes.

### Lo protegido

Sin cambios, por hash y por `git diff --stat HEAD`: `bin/ejecucion/`, `contrato.py`, los dos schemas de
Task 3 y ADR-0014, Flow Governance (`bin/flujo/`, `bin/estado_de_tarea/`, `bin/orquestacion/`), los hooks
y `tool_policy.py`, `install.ps1`, `manifest.json`, `VERSION`, `CHANGELOG.md` y `UPGRADE.md`.

### Riesgos que siguen abiertos

| | Estado |
|---|---|
| R1, el Host que sobrevive al motor | abierto |
| R2, la `REQUESTED` huérfana | abierto |
| R3, lo no documentado del Host | **cerrado para Task 4**, por ME-E50 `leído` |
| R4, `ejecutar` sin clasificación propia en la política de herramientas | abierto |
| R5, `Bash` ausente en la sesión del Host en Windows | abierto |
| R6, una request adulterada deja la Execution ilegible | abierto |
| R7, un Host matado desde afuera es `HOST_FAILURE` en Windows | abierto, sin cambios |

### Hallazgos N1 a N10

No se resolvieron en este cierre. Siguen donde los dejó la reverificación («Hallazgos nuevos», arriba) y
no se movieron a `PENDIENTES-FH.md`; los no bloqueantes de la primera verificación ya están ahí, en «What
the refutation of the minimal execution engine left open». Para Task 5:

- **N1, la ventana del candado bajo concurrencia:** la sonda de `recuperar` puede caer entre `O_EXCL` y el
  bloqueo de `Vida`. Microsegundos hoy, y más probable con workers o paralelismo.
- **R5, `Bash` ausente en la sesión del Host en Windows:** una unidad con `tests.run` no puede correr
  `Bash` en esa sesión.

### Decisión

Task 4 cierra. No queda `contradicho` ni `sin sustento`, y el `leído` de ME-E50 es de una persona con
nombre y fecha.

```
TASK 5 — GRAPH EXECUTION
LISTA PARA DISCOVERY / SPEC
```

Task 5 no empezó, y esta sección no la construye.

