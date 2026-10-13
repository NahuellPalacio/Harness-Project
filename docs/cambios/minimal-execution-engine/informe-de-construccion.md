# Informe de construcción — minimal-execution-engine

**Escrito por:** la sesión que construyó el cambio · **Fecha:** 08-10-2026 · **Spec:**
[spec.md](spec.md) · **Línea de base:** 0.31.0 (`fdca5ce`), con Task 3 integrada y sin commitear

📌 **Esto no es un veredicto.** Dice qué se construyó, cómo se probó y qué quedó abierto, para que
`harness-spec-refuter` lo contraste contra la spec. Quien construyó no verifica, y ME-E50 lo firma
una persona que no construyó.

## Baseline

| | |
|---|---|
| `HEAD` | `fdca5ce86e73ea2a47ad3745ff850310e88f80f5`, en `main`, tag `v0.31.0` |
| `VERSION` | `0.31.0`, sin tocar |
| `git status` al empezar | cinco modificados (`PENDIENTES-FH.md`, `PENDIENTES-I.md`, `modelo-canonico.md`, `63-harness-unico-instalador.ps1`, `64_modelo_de_dominio.py`) y los nuevos de Task 3, más `docs/cambios/minimal-execution-engine/` con la spec |
| Diff contra `fdca5ce` | el de Task 3, sin commitear |
| Stash | `stash@{0}: task3-execution-contract-sobre-0f8b725`, la copia de resguardo de Task 3. No se reaplicó ni se tocó |
| `.claude/ejecuciones/` en la fábrica | no existía, y no existe: los tests usan proyectos en `%TEMP%` |
| Task 3 | `contrato.py` `968c7831…`, `execution-request.schema.json` `df3a4bc1…`, `execution-result.schema.json` `266304c6…`, ADR-0014 `446b2e1d…` (sha256). Iguales al final |
| Hooks | `pre-tool-use.py` blob `b9cde9d`, `zonas.py` blob `e996067`. Iguales al final |

## Construido

| Artefacto | Qué hace |
|---|---|
| `bin/ejecucion/registro.py` (nuevo) | Rutas e ids con `fullmatch`; `nuevo_id` con `secrets.token_hex(16)`; `ruta_mala` y `repetidas` (MD-16); `escribir_una_vez` (temporal exclusivo, fsync, `os.link`, el temporal se borra siempre); el candado de vida (`Vida`, `candado_libre`, `Tomado`) con `msvcrt.locking`/`fcntl.flock`; turnos; `crear` en el orden de MD-04; el estado derivado con `ILEGIBLE`; el barrido de residuos y de temporales; `otras_entregadas` |
| `bin/ejecucion/proceso.py` (nuevo) | `git` con límite de 10 s y salida a un temporal; `lanzar`; `esperar` por tramos de 1 s mirando el pedido de cancelar, sin hilos; `matar_arbol` (`taskkill /F /T` y `killpg`); `pid_vivo`, solo para avisar |
| `bin/ejecucion/evidencia.py` (nuevo) | `instantanea` (`rev-parse` y `status --porcelain=v1 -z --untracked-files=all`, sin `.claude/ejecuciones/`); `armar` con la regla de atribución por ruta; `comparar` para las huérfanas |
| `bin/ejecucion/admision.py` (nuevo) | Las quince condiciones en el orden de `contrato.PRECEDENCIA`, al pedir y al entregar; la request en el orden de MD-23; `normas_de`; `ruta_del_plan` |
| `bin/ejecucion/host_claude_code.py` (nuevo) | El Host Adapter: `resolver_agente`, `provee`, `herramientas`, `modelo`, `argumentos`, `prompt`, `entregar`, `interpretar` |
| `bin/ejecucion/motor.py` (nuevo) | `configuracion` (MD-22), `ejecutar`, `cancelar`, `recuperar`, `estado`, `quien_pide` |
| `bin/ejecucion/__init__.py` | El docstring del paquete, que decía «no hay motor» |
| `bin/dev-harness.py` | El subcomando `ejecutar` con `--unidad`, `--cancelar`, `--estado`, `--recuperar`, `--pedido-por` y `--json`; `--unidad` ya existía para `contabilidad` |
| `tests/fixtures/host_falso.py` (nuevo) | El Host falso, externo, por `ejecucion.comandoHost` |
| `tests/casos/72_motor_de_ejecucion.py` (nuevo) | 53 escenarios de la suite, 464 aserciones |
| `tests/casos/72-motor-de-ejecucion-instalador.ps1` (nuevo) | ME-E26, 12 aserciones |
| `tests/casos/64_modelo_de_dominio.py`, `65_contrato_de_ejecucion.py`, `63-harness-unico-instalador.ps1` | Las adaptaciones, ver abajo |
| `docs/dominio/modelo-canonico.md` | §24 de la spec |
| `docs/adr/0015-el-motor-minimo-de-ejecucion.md` (nuevo) | Aceptada, las siete decisiones de §25 |
| `docs/cambios/minimal-execution-engine/lectura.md` (nuevo) | ME-E50, sin firmar |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Siete entradas de §30 que no estaban, y ME-E50 entre lo no verificado |
| `docs/cambios/minimal-execution-engine/spec.md` | El estado, ME-27, la fila 2 de §11, cuatro adaptaciones que §26.2 no listaba, la mutación de ME-E27 y el rojo visto (§29.1) |

No se tocaron `install.ps1`, `manifest.json`, `VERSION`, `CHANGELOG.md`, `UPGRADE.md`, ningún
schema, ni nada de lo protegido (ver *Archivos protegidos*). No hubo commit ni tag.

## Contradicción de la spec encontrada al construir: ME-27

**§11, fila 2, mandaba leer la ruta del plan con `refutacion.ruta_del_plan`.** MD-13 dice que
Execution no importa la refutación, y EX-E08 de Task 3, que no está en §26.2, lo prueba:
`bin/ejecucion/` no importa `refutacion`. Usar la función dejaba la suite en rojo (EX-E08, la primera
corrida de los casos `6*` dio 8557/8558).

**Se eligió la salida que no afloja un límite de dominio:** `admision.ruta_del_plan` arma
`.claude/planes/<KEY>.json`, y ME-E29 fija que es la misma ruta que la de la refutación. El costo es
que E-22 de Task 2 inventaría los módulos de `bin/` que arman una ruta bajo `.claude/planes/`: se le
sumó `ejecucion/admision.py`, con dos aserciones nuevas que cuidan lo que E-22 protege —la admisión
lee el plan por `aceptar_guardado` y no lo escribe—. **Queda para revisión:** la otra salida era
adaptar EX-E08, que relajaba la independencia de Execution respecto de Governance.

## Adaptaciones de tests anteriores

Las seis de §26.2, cada una con su comentario en el test:

| Test | Qué cambió |
|---|---|
| `64` E-41 | `taskkill` también desde `ejecucion/proceso.py`; el único lanzamiento de un parámetro permitido es `proceso.lanzar`, y una aserción nueva exige que solo lo llame `host_claude_code.py` |
| `64` E-09 | «motor», «admisión», «almacenamiento» y «Host Adapter» pasan de *Lo que todavía no existe* a *Lo que existe ahora* |
| `65` EX-E47 | Lo mismo; «sin productor» sigue, es lo que dejó ADR-0014 |
| `65` EX-E49 | Trece subcomandos, los de `fdca5ce` más `ejecutar`; sin `run` ni `execute`, y sin concurrencia |
| `65` EX-E51 | Corre el E-41 de ahora y exige que sea el de Task 4 |
| `65` EX-E52 | `contrato.py` no escribe, no lanza y no importa refutación ni contabilidad; el registro vive bajo `.claude/ejecuciones`; fuera de `bin/ejecucion/` nadie nombra esa ruta; de producción, solo `dev-harness.py` importa `ejecucion`, y es `ejecucion.motor` |

EX-E50 no cambió. Y cuatro que §26.2 no listaba, registradas en la spec como ajuste documental de la
construcción (§26.2, al final):

| Test | Qué cambió | Por qué |
|---|---|---|
| `64` E-22 | Seis módulos, con `ejecucion/admision.py`, y dos aserciones nuevas | ME-27 |
| `65` EX-G06 | Del flujo, solo `admision.py` importa `flujo.estado`; ningún hook, nada de `estado_de_tarea` | MD-12 |
| `65` EX-G11 | `dev-harness.py` sale de lo protegido de 0.31.0 | MD-01 |
| `63-harness-unico-instalador` E-15/E-16 | 292 rutas en vez de 286, y los seis módulos se saltean en E-16 | §31.1 |

Ninguna afloja una garantía distinta de la que su decisión cambia.

## Decisiones de construcción, por MD

Lo que la spec dejaba al código, y cómo quedó:

- **MD-04.** `admision.al_pedir` devuelve, además de la request, el número del último turno leído;
  `registro.crear` hace los pasos 2 a 6 con ese número. La perdedora borra su carpeta. Una falla antes
  de publicar también la borra; después de publicar, nunca (`crear` mira si el turno ya la nombra).
- **MD-05.** El temporal es `.<nombre>.<aleatorio>.tmp` de `mkstemp`, en la misma carpeta. Los JSON se
  escriben con `indent=2`, `sort_keys` y LF. Los temporales de los turnos se barren con la guarda de
  diez minutos, porque la carpeta de una clave no tiene candado.
- **MD-06.** El candado es el byte 0 de `vivo.lock`, sin bloquear. Sin `vivo.lock` no hay a quién
  preguntarle: una Execution así no es huérfana, y un residuo así se barre por la edad de la carpeta.
  **En Windows el candado es obligatorio:** con el motor vivo, `vivo.lock` no se puede leer. La spec
  ya dice que nadie lo lee; un test que recorre el registro anota que existe sin abrirlo.
- **MD-07.** `ILEGIBLE` es un estado derivado más: una request que no valida o un resultado que no
  valida. Cuenta como abierta.
- **MD-08.** El prompt, stdout y stderr del Host van a **temporales anónimos del sistema**, no a la
  carpeta de la Execution: en Windows un temporal abierto por el Host no se puede leer, y adentro del
  registro trababa a quien lo recorre (lo encontró ME-E13). Se borran solos aunque el motor muera. El
  schema por argv es JSON compacto, sin espacios ni `& | < > ^ %`. `--allowedTools` va siempre.
- **MD-09 y MD-10.** `interpretar` toma el objeto `type: result` de stdout. `PROVIDER_FAILURE` solo
  con `is_error: true` y `error.type` de la API (`overloaded_error`, `rate_limit_error`, `api_error` y
  los demás de `DEL_PROVEEDOR`); la lectura ME-E50 dice si el Host real lo da. Sin JSON, 130, 143 o un
  código negativo es `HOST_INTERRUPTED`; lo demás, `HOST_FAILURE`. El `detail` es texto del motor,
  más el principio de stderr redactado solo si hay catálogo.
- **MD-11.** La condición 1 al entregar es `validar_request` sobre la request en disco y, si la huella
  del plan es la misma, la huella de su WorkUnit contra la del plan. La condición 10 al entregar
  suma `resolver_agente` antes de mirar el tipo y el dominio.
- **MD-12.** Cualquier excepción de `vigencia_local` —un `git remote -v` que no contesta incluido— es
  `DELEGATION_NOT_ALLOWED`.
- **MD-15 y MD-16.** Un id con `\n` final levanta `RegistroInvalido` antes de volverse ruta. Las rutas
  repetidas se comparan con `casefold` en Windows y macOS.
- **MD-19 y MD-23.** El catálogo se carga al principio de `ejecutar`: sin él, error del comando. La
  request entera pasa por `redactar_arbol`. **`requestFingerprint` es la huella que el motor calculó
  al crear la request, la de lo que persistió;** al entregar, la request en disco se valida, y si
  alguien la cambió después, el resultado conserva la huella de lo escrito y la diferencia queda a la
  vista (`validar_resultado` contra el archivo adulterado no pasa).
- **MD-20.** Las rutas salen de `status --porcelain=v1 -z --untracked-files=all -- .`, con el prefijo
  de `rev-parse --show-prefix`; lo commiteado, de `diff --name-only -z --no-renames`; lo que existía
  antes, de `ls-tree` en la revisión de antes. **El solape con otra Execution se mide con la hora de
  los archivos** (`entrega.json` propio y `result.json` ajeno), no con los tiempos del contrato, que
  van al segundo: dos corridas seguidas caben en el mismo segundo y se contaban como simultáneas (lo
  encontró el rojo visto de ME-E25; ME-E44 suma ese caso).
- **MD-22.** Un `comandoHost` que es un nombre se resuelve a la ruta que da `shutil.which`: en Windows,
  `CreateProcess` no encuentra un `.cmd` por su nombre.
- **MD-24.** El motor mira el pedido de cancelar antes de la admisión al entregar, otra vez justo
  antes de escribir `entrega.json`, y en cada tramo de la espera. Un Ctrl-C antes de la entrega no
  cierra nada: la Execution queda `REQUESTED` (R2). Después de la entrega, cualquier falla propia del
  motor, un resultado que no valida incluido, termina `FAILED` con `ENGINE_FAILURE`.
- **La API interna** sigue a §23 en lo que hace, con firmas más largas: `al_pedir` devuelve
  `(request, error, leido, huella)`; `al_entregar`, `(rechazo, derivado)`; `crear`, la `Vida` o
  `None`; `Adaptador(comando, limite, perfiles)`; y `motor.ejecutar` suma `catalogo`, `compuerta`,
  `cargar_registro`, `antes_de_reservar` y `antes_de_entregar`, que son los dueños inyectables y los
  puntos de encuentro de los tests.

## Tests

### Focalizados

Corridos el 08-10-2026 sobre el código final, cada archivo entero, en un proceso aparte.

| Caso | Aserciones | Segundos |
|---|---|---|
| `72_motor_de_ejecucion.py` (Task 4) | 464/464 | 136,5 |
| `65_contrato_de_ejecucion.py` (Task 3) | 673/673 | 49,0 |
| `64_modelo_de_dominio.py` | 1038/1038 | 84,9 |
| `71_plan_2_1.py` (Plan 2.1) | 276/276 | 27,1 |
| `61_flujo_precondiciones.py` | 184/184 | 22,2 |
| `61_conocimiento_auto_refresco.py` | 292/292 | 9,1 |
| `62_estado_del_flujo.py` (estado de tarea) | 177/177 | 47,6 |
| `63_compuerta_del_flujo.py` | 487/487 | 85,2 |
| `63_harness_unico.py` | 180/180 | 17,4 |
| `64_interaccion_humana.py` | 376/376 | 106,0 |
| `65_fail_closed.py` | 284/284 | 13,0 |
| `66_integrity_cleanup.py` | 733/733 | 81,1 |
| `67_integracion_frescura.py` | 43/43 | 20,9 |
| `70_r11_glob_de_autoridad.py` | 421/421 | 74,0 |
| **Python, total** | **5628/5628, exit 0** | **789** |
| `72-motor-de-ejecucion-instalador.ps1` (ME-E26) | 12/12 | |
| `63-harness-unico-instalador.ps1` | 188/188 | |
| `65-contrato-de-ejecucion-instalador.ps1` | 15/15 | |
| **Instaladores, total** | **215/215, exit 0** | **244** |

### La compuerta

```
cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -File tests\Invoke-Tests.ps1 < NUL"
42777/42777 pasaron.            (Python)
43693/43693 pasaron.            (total; PowerShell, 916)
exit=0 · 1638 s
```

Corrida el 08-10-2026 sobre el árbol de trabajo final, sin commitear, como un proceso aparte y con
stdin desde el dispositivo nulo, después del rojo visto y de los focalizados. No hubo deuda previa
que separar: todo pasó. Antes y después, `pre-tool-use.py` tiene el blob `b9cde9d` y `zonas.py`
`e996067`, y `.claude/ejecuciones/` no existe en la fábrica. Contra la reverificación de Task 3
(43201) son 492 aserciones más: las 464 de la suite 72, las 12 de su instalador, y lo que suman las
adaptaciones.

## Rojo visto (54)

Registrado en la spec, §29.1, y en la marca de cada escenario.

- **53 escenarios con mutación, 56 mutaciones** (ME-E01, ME-E24 y ME-E42 llevan dos): las 56 verdes
  antes, en rojo después con al menos una aserción propia y ninguna excepción, restauradas por huella
  contra el árbol de trabajo, y verdes otra vez. 895 s.
- **ME-E51:** `no consta`, como fija §29: es la compuerta.
- **ME-E50:** lectura.
- Sobre una copia de la fábrica en `%TEMP%`, con el código final. La primera pasada, sobre el código
  de antes, dio cuatro sin rojo, y cada uno tuvo su causa: ME-E25 encontró el solape por segundos
  (corregido en el motor); ME-E38, una guarda doble del perfil vacío (una sola ahora); ME-E46 y ME-E49
  no se aplicaron porque esos archivos tienen CRLF; ME-E48 sacaba el motor de un lado y no del otro.
  Las cuatro se rehicieron, y la pasada final, entera, es la que se registra.
- **ME-E27, ajuste documental:** la mutación de la spec invertía las condiciones 7 y 8, que no pueden
  fallar a la vez —una unidad que no está no tiene estado—; se invirtieron la 9 y la 13.

## Atomicidad: ME-E18 y EX-F01

Dos `python` hijos, con la API del motor, sobre la misma clave. El punto de encuentro
(`antes_de_reservar`) está entre la lectura del último turno y la reserva: cada uno deja una marca y
espera la del otro. Resultado: una Execution, un `DUPLICATE_EXECUTION`, un turno, una carpeta y
ningún temporal. Después, veinte carreras sin punto de encuentro, en tandas de cinco claves con dos
procesos cada una: veinte veces lo mismo. Con la reserva escrita por `open("w")`, la mutación de
§29, quedan dos Executions.

EX-F02 es ME-E19: la propia pasa la condición 15 al entregar y llega a `RUNNING`; con un turno
posterior armado a mano que nombra a otra abierta, `REJECTED` con `DUPLICATE_EXECUTION`.

## Recuperación

- **ME-E20.** El motor corre en otro proceso; con él vivo, la recuperación no toca la `RUNNING`.
  Muerto a la fuerza (`taskkill /F` sin `/T`, así el Host sobrevive), la cierra `FAILED` con
  `HOST_INTERRUPTED`, `startedAt` de `entrega.json` y evidencia `RESOLVED` vacía, o
  `CHANGES_UNATTRIBUTABLE` si el Host cambió un archivo. No se vuelve a entregar, y el Host que
  sobrevivió sigue vivo después de la recuperación: nadie lo mató.
- **ME-E34.** Un motor colgado entre la creación y la entrega, muerto a la fuerza, deja una
  `REQUESTED` real: la recuperación no la toca, bloquea la clave con un `detail` que dice cómo
  cancelarla, y `--cancelar` la deja `CANCELLED` sin `startedAt` ni evidencia. Una `RUNNING` cuyo motor
  ya murió, con `--cancelar`, queda `FAILED` con `HOST_INTERRUPTED`, sin `cancelacion.json`.
- **ME-E52.** Un residuo sin turno, con `request.json` válido y un temporal: no aparece en `--estado`,
  no bloquea, y la recuperación lo borra entero pasados diez minutos. Con turno, es una `REQUESTED`
  real: bloquea y no se borra.
- **ME-E53.** Dos huérfanas armadas a la vez —cada `ejecutar` recupera primero, y una segunda corrida
  cerraría la primera—, iguales salvo `cancelacion.json`: `CANCELLED` y `FAILED`/`HOST_INTERRUPTED`,
  sin AgentReport aunque haya quedado un `output.md`. El pedido se escribe después de matar los
  motores: para la recuperación, el orden entre el pedido y la muerte no es observable.

## Host Adapter

Probado contra el Host falso, un proceso externo configurado por `ejecucion.comandoHost`, sin
monkeypatch del motor: éxito con `structured_output`, cada `subtype` de error, JSON roto, sin
`structured_output`, `result` que dice COMPLETE, error del proveedor, un agente que no carga, sueño
para el límite y la cancelación, muerte por señal, cambios y commit en el repositorio, un nieto para
ver morir el árbol, y el eco de argv y stdin. ME-E40 lo llama a través de un shim `.cmd` como el de
npm: el schema llega intacto y el prompt por stdin. Ningún test lanza el Claude Code real: los que
miran el default de `comandoHost` ponen un `claude` falso primero en el `PATH`.

## ME-E50

> 📌 Superado el 09-10-2026: ver «Corrección post-refutación», abajo. Lo que sigue es la primera
> construcción.

**Pendiente de lectura independiente.** `lectura.md` tiene el proyecto, el comando, cómo ver la
salida cruda del Host y los cinco puntos a mirar, sin firmar. Quien construyó no corrió el Claude Code
real: cada corrida cuesta y sale de la máquina, y no sería una lectura. Es un solo escenario: ADR-0010
no aplica. Hasta la firma de una persona que no construyó, Task 4 no cierra (§32, R3).

## Alcance

Sin Task 5: no hay Graph Execution, DAG, scheduler, colas, workers ni paralelismo; no hay reintento
automático, backoff, checkpoint ni reanudación; no hay LangGraph, LangChain ni SDK de modelos; no hay
eventos contables, cambios de hooks ni de la política de herramientas, ni Job Objects. Una búsqueda
de `threading`, `multiprocessing`, `asyncio`, `concurrent`, `sched`, `queue`, `langgraph`,
`langchain`, `retry`, `backoff`, `checkpoint` y `resume` en `bin/ejecucion/` encuentra solo dos
docstrings que dicen que no los hay; en lo agregado a `dev-harness.py`, nada. ME-E47 lo cuida en
`bin/` y `comun/`. Los riesgos R1 a R4 quedaron como estaban, y lo que §30 deja pendiente está en
`PENDIENTES-FH.md`.

## Archivos protegidos

`git diff --stat fdca5ce` sobre `bin/flujo/`, `bin/estado_de_tarea/`, `bin/orquestacion/`,
`bin/contabilidad/`, `comun/hooks/` (con `tool_policy.py`, `task_binding.py` y `human_intent.py`),
`agents/` y `skills/` de los dos harnesses, `reglas/`, `install.ps1`, `manifest.json`, ADR-0013,
`VERSION`, `CHANGELOG.md`, `UPGRADE.md` y `comun/schemas/` versionados: **vacío**. Sin archivos nuevos
en ninguno. `contrato.py`, los dos schemas de Task 3 y ADR-0014 tienen la misma huella que al
empezar. ME-E49 lo cuida en la suite.

## Lo que queda abierto

- ME-E50, sin firmar.
- ME-27, para que una persona decida si la salida elegida es la que quiere.
- Cuatro conceptos de Execution del modelo canónico siguen hablando del motor en condicional, porque
  §24 no los nombraba: anotado en `PENDIENTES-FH.md`.
- Las dos preguntas anteriores a esta Task siguen sin respuesta y no se tocaron: anotar los hallazgos
  no bloqueantes de la verificación y la reverificación de Task 3, y corregir el docstring de
  `test_e05` y la contradicción de la ModelTierApproval.

## Corrección post-refutación

**Fecha:** 09-10-2026 · **Escrito por:** la sesión que construyó y corrigió. Tampoco es un veredicto:
la corrección necesita reverificación independiente, y ME-E50 la firma de una persona que no
construyó.

La refutación ([`verificacion.md`](verificacion.md)) contradijo ME-E24, ME-E28, ME-E39 y ME-E50, y los
invariantes ME-I17, ME-I06 y ME-I23. La spec se enmendó primero (§34) y después se tocó el código. Lo
que ya estaba sostenido no se rehízo.

### Los cuatro contradichos

| Escenario | Causa | Decisión (spec §34.3) |
|---|---|---|
| ME-E24, ME-I17 | El adaptador recortaba stderr a 200 caracteres antes de redactar, y un secreto partido ya no coincidía con su patrón. Sin catálogo, el mensaje de `validar_informe` —con el nombre de una clave del agente— iba en el texto del motor | MD-19′: texto del Host → redactar → recortar. El adaptador devuelve el texto del Host entero (hasta 1 MiB de stderr), separado del texto del motor; el motor lo redacta entero y `admision.detalle` recorta a 300. Sin catálogo, solo texto del motor |
| ME-E28, ME-I06 | Al entregar solo se comparaban la huella del plan y la de la unidad, y el motor entregaba la request que tenía en memoria | MD-11′: la primera comprobación al entregar es la huella (`contrato.huella`, estructural) del `request.json` del disco contra la que el motor escribió; si difiere, `REJECTED`/`CONTRACT_INVALID` sin Host. Después se entrega la request del disco. El resultado guarda la huella original; la Execution queda ilegible (R6), sin reescribir ni borrar nada |
| ME-E39, ME-I23 | `ejecucion.comandoHost` aceptaba cualquier argumento, y `PROHIBIDOS` no lo usaba nadie; un perfil de modelo podía ser una bandera | MD-22′: `comandoHost` no puede traer banderas del adaptador ni de seguridad (también `--x=valor` y con otras mayúsculas), nada con `dangerously` o `bypasspermissions`, ni opciones cortas, ni un programa que empiece con `-`. Un perfil declarado tiene que ser un nombre de modelo conservador. Exit 2 antes de crear la Execution; el adaptador repite la regla al construirse |
| ME-E50 | Con `--agent`, Claude Code 2.1.295 toma las herramientas del `tools:` del agente y no suma `StructuredOutput`: ninguna corrida real llegaba a `SUCCEEDED`. El error del proveedor no trae `error.type` | MD-08′, MD-09′, MD-10′, MD-18′: estrategia A del discovery (§34.2), abajo |

### La estrategia nueva del Host

Sin `--agent`. El cuerpo de `.claude/agents/<agente>.md` va a `prompt-de-sistema.md`, un archivo más
del registro de la Execution escrito una sola vez, y se pasa con `--system-prompt-file`. `--tools` y
`--allowedTools` llevan el mismo conjunto mínimo de la unidad, y `--strict-mcp-config` saca las
herramientas MCP que el Host suma por su cuenta. El AgentReport sale solo de `structured_output`;
`result` no se lee. El proveedor se reconoce por `terminal_reason: "api_error"` o `api_error_status`.
Un código de salida distinto de 0 nunca es `SUCCEEDED`. Windows, un Host matado desde afuera: exit 1,
indistinguible, `HOST_FAILURE` (R7).

Se probaron A (sin `--agent`), B (`--agents` con `StructuredOutput` en el `tools:`) y C (un archivo,
que no hizo falta). Se eligió A: B escribe una definición de agente por corrida y depende de una
precedencia no documentada. El contrato de Task 3 no cambió.

`--strict-mcp-config` salió de la corrida exploratoria, no del discovery: repitiendo la entrega de una
Execution real con `stream-json`, la sesión ofrecía, además de `Glob, Grep, Read, Skill,
StructuredOutput`, las ocho herramientas del conector Claude Docs de la cuenta (§34.2, E9). Con la
bandera, solo las cinco (E10), y los hooks siguen corriendo. Se agregó al adaptador, a la lista de
banderas reservadas (con `--mcp-config`) y a ME-E39, con su rojo visto.

### Además, del mismo código

- **ME-E56, ME-I32:** un JSON `success` con código de salida distinto de 0 terminaba `SUCCEEDED`.
- **ME-E57, ME-I29:** el motor ahora solo acepta códigos de corrida después de la entrega; otro
  código de un adaptador es `ENGINE_FAILURE`.
- **Documental:** el modelo canónico (`### Plan ≠ Execution`, `### Claude Code ≠ HARNESS` y el Host
  Adapter de «Lo que existe ahora»), ADR-0015 (26 → 27 contradicciones, y la sección «Enmienda
  post-refutación», sin tocar sus siete decisiones), la línea 12 de la spec, `lectura.md` sin
  `error.type`, y el mojibake de los docstrings de la suite 72.

### Archivos modificados en esta pasada

| Archivo | Qué |
|---|---|
| `bin/ejecucion/host_claude_code.py` | Reescrito el adaptador: argumentos de MD-08′, `prompt-de-sistema.md`, texto del Host separado, forma real del proveedor, código distinto de 0, validación de `comandoHost` y de perfiles |
| `bin/ejecucion/motor.py` | La configuración usa las reglas del adaptador; `_detalle_de_falla` redacta antes de recortar; `_del_adaptador` (ME-I29); se entrega la request guardada |
| `bin/ejecucion/admision.py` | `al_entregar` compara la huella del `request.json` primero |
| `bin/ejecucion/registro.py` | Solo el docstring: nombra `prompt-de-sistema.md` |
| `tests/fixtures/host_falso.py` | El eco incluye el contenido de `--system-prompt-file`, y se escribe entero o nada (temporal y `os.replace`) |
| `tests/casos/72_motor_de_ejecucion.py` | ME-E24, E28, E32, E39 y E40 reescritos; ME-E56 y ME-E57 nuevos; ME-E21 mira `prompt-de-sistema.md`; mojibake |
| `docs/cambios/minimal-execution-engine/spec.md` | §34, notas en §27 y §28, línea 12 |
| `docs/adr/0015-el-motor-minimo-de-ejecucion.md` | 27, nota en la decisión 5, «Enmienda post-refutación» |
| `docs/dominio/modelo-canonico.md` | Las tres frases de arriba |
| `docs/cambios/minimal-execution-engine/lectura.md` | Rehecho para la estrategia A, con la evidencia preparada, sin firmar |
| `docs/cambios/minimal-execution-engine/verificacion.md` | Solo la nota de estado arriba; sus veredictos no se tocaron |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Los no bloqueantes de la refutación, y ME-E50 al día |

### Tests nuevos o fortalecidos

- **ME-E24:** un secreto que empieza después del carácter 170 de stderr; un secreto como clave de
  más de un `structured_output`, con catálogo y sin él; un secreto como `declaredStatus`, sin
  catálogo. La aserción busca 13 caracteres del secreto, porque el marcador de la redacción deja ver
  12.
- **ME-E28:** diez adulteraciones del `request.json` —`requestedBy`, `createdAt`,
  `admission.normativeGate`, `admission.agent.validation`, `.type`, `.domain`,
  `admission.capabilities`, `admission.dependencies`, `workUnit`, `plan`—, cada una `REJECTED` sin
  `entrega.json` ni Host, con el `requestFingerprint` original; reescrita con el mismo contenido, se
  entrega.
- **ME-E32:** la forma real del proveedor, con `subtype: success` y código 1.
- **ME-E39:** los argumentos de MD-08′, y doce configuraciones adversariales, cada una exit 2 sin
  Execution. Diez de `comandoHost`: `--bare`, `--dangerously-skip-permissions`, `--permission-mode
  bypassPermissions`, `--permission-mode=bypassPermissions`, `--allowedTools`, `--agent`,
  `--model=opus`, `-p`, `--BARE` y `--mcp-config`. Dos de perfil de modelo:
  `--dangerously-skip-permissions` y `--model`.
- **ME-E40:** `--tools` y `--allowedTools` con el mismo conjunto mínimo.
- **ME-E56** y **ME-E57**, nuevos.

### Rojo visto

Once mutaciones sobre siete escenarios, todas en rojo con aserciones propias y sin excepción, y verdes
al restaurar: spec §34.7.

### Evidencia real preparada

Dos corridas exploratorias con el adaptador final contra Claude Code 2.1.295, `haiku`: `PARTIAL` y
`BLOCKED` → `FAILED`/`AGENT_DECLARED_NOT_COMPLETE`; un modelo inexistente → `PROVIDER_FAILURE`; una
unidad de calidad → `SUCCEEDED`/`COMPLETE`. Las cuatro con `validar_resultado` vacío, la huella de la
request igual, el vínculo de sesión con `GCBA-72` y herramientas dentro del conjunto. El detalle está
en `lectura.md`, que queda **sin firmar**: quien construyó preparó evidencia y no lee ME-E50.

### Tests

**Focalizados**, el 09-10-2026, cada archivo entero en un proceso aparte:

| Caso | Aserciones | Segundos |
|---|---|---|
| `72_motor_de_ejecucion.py` | 546/546 | 206,4 |
| `65_contrato_de_ejecucion.py` | 673/673 | 70,7 |
| `64_modelo_de_dominio.py` | 1038/1038 | 117,7 |
| `71_plan_2_1.py` | 276/276 | 30,2 |
| `61_flujo_precondiciones.py` | 184/184 | 18,0 |
| `61_conocimiento_auto_refresco.py` | 292/292 | 7,6 |
| `62_estado_del_flujo.py` | 177/177 | 47,2 |
| `63_compuerta_del_flujo.py` | 487/487 | 92,2 |
| `63_harness_unico.py` | 180/180 | 25,9 |
| `64_interaccion_humana.py` | 376/376 | 99,8 |
| `65_fail_closed.py` | 284/284 | 15,2 |
| `66_integrity_cleanup.py` | 733/733 | 87,8 |
| `67_integracion_frescura.py` | 43/43 | 21,0 |
| `70_r11_glob_de_autoridad.py` | 421/421 | 69,5 |
| **Python, total** | **5710/5710** | |
| `72-`, `63-` y `65-…-instalador.ps1` | 12/12, 188/188, 15/15 | 238 |

**La compuerta**, primera corrida:

```
42856/42857 pasaron.            (Python)
43772/43773 pasaron. 1 fallaron.
exit=1 · 2472 s
```

La que falló fue ME-E34, con un `JSONDecodeError` en el ayudante `_huerfanas`: el Host falso abría
el eco con `"w"` y lo escribía después, y el test lo leyó vacío. La carrera ya existía; al sumar el
prompt de sistema al eco, el archivo creció y la ventana también. Se arregló el fixture —temporal y
`os.replace`, con reintento si Windows tiene el eco viejo abierto—, sin tocar el motor ni el test, y
ME-E34, E39, E20, E53 y E21 pasaron aparte (94/94). Segunda corrida, sobre el árbol final:

```
cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -File tests\Invoke-Tests.ps1 < NUL"
916/916 pasaron.                (PowerShell)
42859/42859 pasaron.            (Python)
43775/43775 pasaron.            (total)
exit=0 · 2755 s
```

Antes y después, `pre-tool-use.py` blob `b9cde9d` y `zonas.py` `e996067`, y `.claude/ejecuciones/` no
existe en la fábrica. Contra la compuerta de la primera construcción (43693) son 82 aserciones más,
todas de la suite 72.

**Regresión:** ME-E18, E20, E21, E25, E35, E45, E52, E53, E54 y E55 siguen en verde, en la suite 72
de la compuerta.

### Archivos protegidos

`contrato.py` `968c7831…`, `execution-request.schema.json` `df3a4bc1…`,
`execution-result.schema.json` `266304c6…` y ADR-0014 `446b2e1d…`, iguales. `pre-tool-use.py` blob
`b9cde9d` y `zonas.py` `e996067`, iguales. `git diff --stat fdca5ce` sobre `comun/hooks/` (con
`tool_policy.py`), `install.ps1`, `manifest.json`, `VERSION`, `CHANGELOG.md`, `UPGRADE.md`, `bin/flujo/`,
`bin/estado_de_tarea/` y `bin/orquestacion/`: vacío. Ningún cambio de Host Adapter pidió tocarlos.

### Deuda que queda

- **ME-E50** sin firmar, y con él R3.
- **R5:** `Bash` no existe en la sesión del Host en Windows. **R6:** una request adulterada deja su
  Execution ilegible hasta replanificar. **R7:** un Host matado desde afuera en Windows es
  `HOST_FAILURE`.
- Los no bloqueantes de la refutación, en `PENDIENTES-FH.md` («What the refutation of the minimal
  execution engine left open»): ME-E19 y ME-E44 a medias, la precisión de MD-24, tracebacks, tests
  históricos aflojados, el frente YAML literal, rutas de la evidencia con secretos, residuos en
  `%TEMP%`, el `detail` de `DELEGATION_NOT_ALLOWED`, MD-17, la ventana de la sonda del candado, la
  junction duplicada y la exclusividad de la reserva sin test. El costo por corrida ya estaba (MP-03).
- **Task 4 no está cerrada:** necesita reverificación independiente y la lectura firmada de ME-E50.

> 📌 **13-10-2026:** Task 4 cerrada después de la reverificación y la firma independiente de ME-E50
> (`verificacion.md`, «Cierre formal de Task 4»). Lo de arriba es lo que decía este informe al
> escribirse y no se reescribe.
