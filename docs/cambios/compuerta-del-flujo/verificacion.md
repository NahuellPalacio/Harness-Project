# Verificación — Flow Governance, Wave 3 — la sesión, su tarea y la compuerta del flujo en los hooks

**Estado:** cerrado · **Fecha:** 30-09-2026 · **Versión:** sin release todavía (base 0.26.0, sobre `32febd7`)

Este documento cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el
veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los dio
`harness-spec-refuter` el 30-09-2026, en nueve pasadas. La quinta llegó después de la
pre-aceptación, que encontró dos caminos reales sin cubrir (E-63 y E-64). De la sexta a la novena
fueron sobre el límite de `git remote -v` (E-65). En cada una corrió `63_compuerta`,
`62_estado`, `61_flujo`, `55_refutacion`, `53_context_bar`, `60_entorno`, `30_b4_contabilidad`,
`48_reporte_de_seguridad`, `02_hook` y `04_secretos`, más sondas propias contra proyectos temporales.
La compuerta entera la tomó de quien construyó: `.\tests\Invoke-Tests.ps1` sobre el árbol final,
lanzada después del último arreglo (ver «La compuerta entera», abajo).

**Resultado: 65 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.** E-48 es el único
sostenido sobre evidencia prestada. La quinta pasada dejó una decisión a la persona: E-28 y E-31
admiten ahora un proceso, `git -C <raíz> remote -v`, que es lo que exige E-63, y con el límite
vencido el `taskkill /F /T` de ese árbol.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | SessionStart lee el `session_id` | sostenido | sí | `63_compuerta_del_flujo.py`, `test_e01_…` |
| E-02 | UserPromptSubmit lee el `session_id` | sostenido | sí | `test_e02_…` |
| E-03 | PreToolUse lee el `session_id` | sostenido | sí | `test_e03_…` |
| E-04 | Un binding es estable | sostenido | sí | `test_e04_…` |
| E-05 | Dos sesiones, dos tareas | sostenido | sí | `test_e05_…` |
| E-06 | `active-task.json` no pisa otro binding | sostenido | sí | `test_e06_…` |
| E-07 | `active-task.json` no autoriza | sostenido | sí | `test_e07_…`; el refutador además auditó que PreToolUse nunca lo abre |
| E-08 | Una clave declarada crea el binding | sostenido | sí | `test_e08_…` |
| E-09 | Un prompt ambiguo no inventa tarea | sostenido | sí | `test_e09_…`; ver abajo |
| E-10 | Varias tareas sin binding: deny `SESSION_TASK_AMBIGUOUS` | sostenido | sí | `test_e10_…` |
| E-11 | Binding `STALE`: deny a mutar, la lectura pasa | sostenido | sí | `test_e11_…` |
| E-12 | El binding no guarda el prompt ni secretos | sostenido | sí | `test_e12_…`, valida contra su schema |
| E-13 | SessionStart con binding: una línea | sostenido | sí | `test_e13_…` |
| E-14 | SessionStart sin binding no inventa | sostenido | sí | `test_e14_…` |
| E-15 | UserPromptSubmit inyecta el bloqueo | sostenido | sí | `test_e15_…` |
| E-16 | Un secreto pendiente sin valor | sostenido | sí | `test_e16_…` |
| E-17 | El mismo bloqueo no se repite | sostenido | sí | `test_e17_…` |
| E-18 | Un bloqueo distinto se informa entero | sostenido | sí | `test_e18_…` |
| E-19 | Secreto alto gana sobre el flujo | sostenido | sí, por mutación | `test_e19_…` |
| E-20 | Secreto ambiguo: ask; con bloqueo, deny | sostenido | sí | `test_e20_…` |
| E-21 | `BLOCKED` + mutación: deny | sostenido | sí | `test_e21_…` |
| E-22 | `BLOCKED` + avance: deny | sostenido | sí | `test_e22_…` |
| E-23 | `BLOCKED` + lectura: pasa | sostenido | sí, por mutación | `test_e23_…` |
| E-24 | `BLOCKED` + recuperación: pasa | sostenido | sí | `test_e24_…` |
| E-25 | Lo que no se clasifica falla cerrado | sostenido | sí | `test_e25_…` |
| E-26 | El `.env` nunca es recuperación | sostenido | sí | `test_e26_…` |
| E-27 | PreToolUse no consulta Jira | sostenido | sí | `test_e27_a_e30_…`, con espía |
| E-28 | PreToolUse no lee la URL de GitLab por ninguna vía; su único proceso, `git remote -v` | sostenido | sí, por mutación | `test_e27_a_e30_…`; ver abajo |
| E-29 | PreToolUse no abre sockets | sostenido | sí, por mutación | `test_e27_a_e30_…` |
| E-30 | PreToolUse no carga un cliente de modelo | sostenido | sí | `test_e27_a_e30_…` y barrido de imports |
| E-31 | UserPromptSubmit local; su único proceso, `git remote -v` | sostenido | sí; el camino colgado, por mutación | `test_e31_…` y `test_e65_…` |
| E-32 | SessionStart local | sostenido | sí | `test_e32_…` |
| E-33 | Consume `vigencia` y `permisos` | sostenido | sí | `test_e33_…`; ver abajo |
| E-34 | Un estado viejo no deja mutar | sostenido | sí | `test_e34_…` |
| E-35 | Dos sesiones concurrentes | sostenido | sí | `test_e35_…` |
| E-36 | Una sola emisión | sostenido | sí, por mutación | `test_e36_…` |
| E-37 | Por PowerShell | sostenido | sí | `test_e37_e38_e39_e57_…`: `powershell.exe` llama a Python; el camino por `run-hook.cmd` lo cubre `03-instalador.ps1` |
| E-38 | Por Git Bash | sostenido | sí | ídem, con `run-hook.sh` |
| E-39 | Ruta con espacios | sostenido | sí | ídem |
| E-40 | La Context Bar sigue siendo la `statusLine` | sostenido | sí | `test_e40_…` |
| E-41 | E-25 de la Context Bar, acotado | sostenido | sí | `test_e41_…`; `53_context_bar` 463/463 |
| E-42 | Wave 2 sigue verde | sostenido | no consta | `62_estado_del_flujo` 173/173 |
| E-43 | Wave 1 sigue verde | sostenido | no consta | `61_flujo_precondiciones` 183/183 |
| E-44 | Refutación atómica sigue verde | sostenido | no consta | `55_refutacion_atomica` 305/305 |
| E-45 | Entorno primero sigue verde | sostenido | no consta | `60_entorno_primero` 307/307 |
| E-46 | Bloque 4 sigue verde | sostenido | no consta | `30_b4_contabilidad` 863/863 |
| E-47 | Reporte de seguridad sigue verde | sostenido | no consta | `48_reporte_de_seguridad` 566/566 |
| E-48 | La compuerta entera | sostenido | no consta | 38001/38001, salida 0; corrida de quien construyó |
| E-49 | Sin `session_id` | sostenido | sí | `test_e49_…` |
| E-50 | Un `session_id` inseguro | sostenido | sí | `test_e50_…` |
| E-51 | Revalidar la etapa bloqueada | sostenido | sí | `test_e51_…` |
| E-52 | Esperando una aprobación no revalida | sostenido | sí | `test_e52_…` |
| E-53 | Un comando con clave evalúa su clave | sostenido | sí | `test_e53_…` |
| E-54 | Un fallo de la compuerta falla cerrado | sostenido | sí | `test_e54_…` |
| E-55 | Sin flujo, nada cambia | sostenido | sí, por mutación | `test_e55_…` |
| E-56 | Tarea vinculada sin estado | sostenido | sí | `test_e56_…` |
| E-57 | Instalado | sostenido | sí | `test_e37_e38_e39_e57_…` |
| E-58 | `cwd` en una subcarpeta | sostenido | sí | `test_e58_…` |
| E-59 | Un binding sin estado del flujo no gobierna | sostenido | sí | `test_e59_…`; ver abajo |
| E-60 | `refute --record` no revalida | sostenido | sí | `test_e60_…` |
| E-61 | El Secret Guard no depende del flujo | sostenido | sí | `test_e61_…` |
| E-62 | Lo que parece lectura y no es | sostenido | sí | `test_e62_…`; ver abajo |
| E-63 | Un remoto cambiado sin reconciliar no deja mutar | sostenido | sí | `test_e63_…`; ver abajo |
| E-64 | La delegación (`Agent`, `Task`) pasa por la compuerta | sostenido | sí | `test_e64_…`; ver abajo |
| E-65 | `git remote -v` colgado falla cerrado y en el límite del hook | sostenido | sí | `test_e65_…`; el refutador colgó además el `git` real del lanzador: deny en unos 2 s |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

Los tests de E-01 a E-58 se escribieron antes que los cuatro módulos y se corrieron en rojo: 185 de
327 aserciones, en 45 escenarios. Los seis que afirmaban lo que el hook de antes ya cumplía (E-19,
E-23, E-29, E-36, E-55, y E-28 cuando se amplió) se vieron fallar por mutación: 19 mutaciones de la
lógica, todas en rojo en el escenario que tocaban, entre ellas decidir por `active-task.json`, un ask
en lugar de un deny, ignorar la vigencia y fallar abierto.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-09, contradicho en la primera pasada.** Una línea que empezaba con la clave y seguía con texto
   declaraba la tarea: «ABC-123 failed at line 3» vinculaba la sesión. Ahora, sin un verbo de
   continuidad, la línea tiene que ser solo la clave (o `tarea`/`task` y la clave).
2. **E-28, sin sustento en la primera y la segunda pasada.** Primero faltaba la aserción de «no lee
   la URL». Después, el texto se angostó a «no abre el `.env`», cuando la URL también sale del entorno
   del proceso y de `harness.integraciones.json`. El escenario volvió a decir «por ninguna vía» y el
   espía ahora audita los dos archivos y cuenta las llamadas a `entorno.resolver`.
3. **Un binding trababa un proyecto sin estado del flujo** (E-59). En un harness sin `desarrollo`
   no había salida: todo `Write` era deny. Ahora, sin ningún `state.json`, no hay nada que gobernar,
   haya o no binding.
4. **`refute --record` saltaba un HARD_BLOCKER** (E-60). Pasaba como revalidación, pero no tiene
   compuerta propia. Solo `contexto`, `plan` y `refute --compile` revalidan.
5. **Una instalación a medias apagaba el Secret Guard** (E-61). El import de la compuerta estaba al
   tope de `pre-tool-use.py`: sin `lib/tool_policy.py`, un secreto de confianza alta salía sin deny.
   En la segunda pasada, además, la rama de fallo no subía hasta la raíz desde una subcarpeta.
6. **Comandos que escriben, ejecutan o leen el `.env` pasaban por lectura** (E-62, en tres
   pasadas): un scriptblock de PowerShell, `sed`, `git --output`, `git -c`, `-C`, `--git-dir`,
   `--ext-diff`, `grep -O`, `rg --pre`, globs y variables hacia el `.env`, y un `dev-harness.py` que
   no es el del proyecto: en otra carpeta, o el relativo corrido desde una subcarpeta.
7. **E-33 tenía una aserción que no probaba nada.** Ahora forzar `puede_avanzar` cambia `permisos()`.
8. **La delegación esquivaba la compuerta** (E-64, pre-aceptación). `Agent` —y `Task`, su nombre
   anterior— estaba clasificada como avance pero el matcher registrado no la alcanzaba: con la tarea
   bloqueada, un subagente arrancaba igual. El matcher de PreToolUse suma `^Agent$|^Task$`, anclados;
   `03-instalador.ps1` fija el matcher nuevo por evento. En una corrida real de Claude Code 2.1.283,
   la herramienta llega como `Agent` y el deny impide que el subagente arranque (0 lanzados).
9. **Un remoto cambiado sin reconciliar dejaba mutar** (E-63, pre-aceptación). `repositoryRef` se
   tomaba del estado guardado, que seguía diciendo MATCHED. Ahora `vigencia_local` recalcula los
   remotos del checkout con `repositorio.remotos`: `git remote -v`, local, sin red ni `.env`.
10. **`BashOutput` y `KillBash` quedaban en deny con la tarea bloqueada** (quinta pasada). El matcher
    sin anclar los alcanza por `Bash`; leen o paran un shell de fondo y ahora son de lectura.
11. **Un `git` colgado esperaba 10 s y, con la lista guardada vacía, dejaba pasar** (E-65, cierre de
    la aceptación). `remotos` devolvía lo mismo para "no contestó" que para "no hay remotos". Ahora
    el hook pasa 1,5 s y, vencido, la compuerta da `FLOW_GATE_UNRESOLVED`.
12. **El límite no cortaba con el `git` de verdad** (sexta pasada, E-65 contradicho). El test colgaba
    un hijo directo; el `git` del `PATH` en Windows es un lanzador, y `subprocess.run` esperaba al
    nieto: 12 y 20 s en las sondas del refutador. El camino estricto ahora no usa pipes y mata el
    árbol; el test cuelga un lanzador con un nieto, que antes daba 30 s y ahora corta en el límite.
13. **E-28 y E-31 no nombraban el `taskkill`** (séptima y octava pasada). Con el límite vencido, la
    compuerta lanza también el `taskkill /F /T` del árbol. El texto lo dice, y test_e65 lo afirma para
    los dos hooks.

## La latencia

Sobre eventos sintéticos, N=40 por caso, en esta máquina, después de la pre-aceptación (con
`git remote -v` en la compuerta), en dos corridas seguidas:

```
                                          corrida 1              corrida 2
HEAD, Write, sin flujo                    82.4 / p95  85.7 ms    84.7 / p95  92.8 ms
ahora, Write, sin flujo                  102.0 / p95 151.7 ms   129.7 / p95 171.3 ms
HEAD, Write, con flujo                    99.5 / p95 117.2 ms   103.9 / p95 202.3 ms
ahora, Write, tarea bloqueada (deny)     183.1 / p95 295.3 ms   219.4 / p95 294.3 ms
ahora, Write, tarea sana (allow)         206.7 / p95 294.1 ms   212.5 / p95 226.5 ms
ahora, Bash git status, bloqueada        117.4 / p95 128.4 ms   119.9 / p95 127.8 ms
ahora, Write, ambigua (deny)             124.0 / p95 130.1 ms   122.3 / p95 147.2 ms
ahora, Agent, tarea bloqueada (deny)     241.2 / p95 348.1 ms   212.8 / p95 236.6 ms
```

Sin estado del flujo, la compuerta suma entre 20 y 45 ms de mediana. Con una tarea que evaluar y una
herramienta que no es de lectura, unos 110 ms más que HEAD: cargar `flujo/estado.py`, validar el
estado contra su schema (unos 55 ms, medido antes de la pre-aceptación) y `git remote -v` (otros
50 a 60 ms). La lectura no paga ninguna de las dos cosas. El repositorio no fija un presupuesto para
esta Wave: el número queda escrito para comparar, y es el primer candidato si hace falta bajarlo.

## Lo que queda abierto, anotado y no escondido

- **`Read`, `Glob` y `Grep` no llegan al hook.** Son de lectura, y el `.env` lo sigue cerrando
  `permissions.deny`.
- **La identidad del repositorio de la TAREA no la recalcula el hook**: pide la URL de GitLab del
  `.env`. Los remotos del checkout sí, con `git remote -v`; si `git` se cuelga, el hook espera hasta
  `TIMEOUT_REMOTOS`, 1,5 s, y falla cerrado. El `taskkill` tiene su propio límite, 5 s: el peor caso
  es 6,5 s; medido, unos 0,5 s. La rama POSIX del corte (`os.killpg`) no se ejerció en esta máquina.
- **SessionStart no corre `git remote -v`.** Después de un cambio de remoto puede mostrar la tarea en
  curso mientras PreToolUse la niega por `REPOSITORY_STATE_STALE`.
- **El matcher sin anclar alcanza herramientas por subcadena** (`Write` a `TodoWrite`, `Bash` a
  `BashOutput`, y un `mcp__*` que las contenga). Las conocidas son de lectura; una desconocida queda
  `UNRESOLVED` y, con la tarea bloqueada, en deny.
- **Una sesión sin tarea en un proyecto con dos o más tareas no escribe** hasta nombrar una. Es
  justamente el falso positivo que el contrato de hooks llamaba el riesgo existencial.
- **Un binding escrito en un proyecto sin estado sigue ahí** cuando aparece el `state.json` de otra
  tarea, y entonces gobierna la sesión con `TASK_FLOW_STATE_MISSING`. Es por diseño.
- **Sin `cwd` en el evento, la CLI relativa se acepta.** Claude Code siempre lo manda.
- **Siguen diferidos:**
  - `AlmacenSecretos.set/remove`;
  - `PlanInvalido` en `main`;
  - el stub de Python;
  - el conteo de `CLAUDE.md`, que dice 24875 tests con 38001 en la compuerta;
  - `refutacion.compilar` como biblioteca;
  - las Waves 4, 5 y 6.

## La compuerta entera

`.\tests\Invoke-Tests.ps1` sobre el árbol final, después del último cambio de código: ver el reporte
de aceptación de la Wave 3.

## La corrida real de Claude Code

Claude Code 2.1.283 (`claude.exe -p`, el binario de la extensión), sobre un proyecto temporal
instalado con `install.ps1`, con un registrador de eventos que vivió solo en ese proyecto:

- el mismo `session_id` en SessionStart, UserPromptSubmit, PreToolUse y PostToolUse, y el mismo
  después de `--resume`;
- el `systemMessage` y el contexto de UserPromptSubmit llegan (`hook_system_message` y
  `hook_additional_context` en la transcripción), y el segundo prompt recibe la línea compacta;
- `Write` con la tarea bloqueada: deny `FLOW_HARD_BLOCKER`, el archivo no se creó;
- `flujo ABC-123 --status` por Bash: corrió;
- `Agent`: llega con ese nombre, deny, 0 subagentes lanzados.

## Lo que ningún test cubre y se mira con los ojos

- Que la persona vea el bloque de `UserPromptSubmit` en el panel de Claude Code.
- Que el enlace `vscode://file/…` abra el `.env` en la línea que dice; no es una integración nativa
  con el editor, es un enlace.
