# Verificación — Flow Governance, Wave 6 — limpieza de integridad y preparación para la calificación

**Estado:** cerrado, aceptado técnicamente · **Fecha:** 05-10-2026 · **Versión:** sin release todavía (base 0.26.0, sobre `556c7bd`)

Este documento registra lo que dijo quien verificó, que no es quien construyó, según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md). Verificaron tres:

- `harness-spec-refuter`, en dieciséis pasadas del 02-10-2026 al 05-10-2026;
- una revisión adversarial independiente, distinta del constructor y del refutador, que corrió después
  de la cuarta pasada y contradijo E-24;
- una **revisión humana independiente** de E-24 sobre el árbol final (INDEPENDENT HUMAN REVIEW), que lo
  sostuvo.

**Resultado final: 46 escenarios sostenidos (E-01 a E-46), los sub-escenarios E24-E1 a E24-E21
sostenidos, las 9 afirmaciones sostenidas; 0 contradichos, 0 leídos, 0 sin sustento.** E-24 tiene
además la revisión humana independiente: SUSTAINED. Las aceptaciones manuales A (en lo que la persona
observó), B y C son PASS.

Cómo se llegó, en una línea por tramo (el detalle está en «Las pasadas»):

- Pasadas primera a sexta: E-01, E-18 y E-24 contradichos y arreglados; la persona decidió que la
  afirmación 7 era un **SPEC_OVERSTATEMENT** y que toda escritura de `git config`, también la local, es
  autoridad (E24-E13).
- Pasadas séptima a decimotercera: cada forma de llegar a `git config` o a la autoridad que se
  arreglaba dejaba otra al lado (MCP, el matcher, comandos repartidos, comillas, scriptblocks,
  continuaciones de línea). La persona decidió el 04-10-2026 abandonar el parser forma por forma: si
  el texto deja ver git y `config` y el parser no prueba una lectura, es protegido (E24-E21,
  INTENTIONAL_CONSERVATIVE_OVERPROTECTION).
- Decimocuarta pasada: 35 sostenidos y las 9 afirmaciones, con E-24, E24-E21 y las afirmaciones 8 y 9
  solo con los tests de quien construyó: un control de seguridad cortó las sondas propias del
  refutador. Lo cubre la revisión humana independiente (abajo).
- La aceptación manual B falló en B4: `-Doctor` no llegaba a `ACTIVE` después de reiniciar. La persona
  decidió conservar la evidencia de la Context Bar (E-36 a E-46).
- Decimoquinta pasada: E-36 a E-43, E-45 y E-46 sostenidos con sondas propias; E-44 contradicho y
  arreglado. Decimosexta pasada, de otra sesión que la que construyó el arreglo: E-44, E-39 y E-45
  sostenidos, 0 contradichos, 0 sin sustento.

## La revisión humana independiente de E-24

**INDEPENDENT HUMAN REVIEW: SUSTAINED.** Es evidencia de la persona revisora, no de quien construyó
ni del refutador.

- El archivo de casos lo preparó la persona, sin veredictos esperados: 39 casos, 48 filas (caso por
  estado), 0 errores del runner, 0 discrepancias con el contrato.
- El instrumento lo preparó quien construyó y solo observa: un runner de solo clasificación, fuera
  del repo, que importa `lib.tool_policy.clasificar` y `lib.flow_gate.decidir` reales del árbol, no
  ejecuta los textos de los casos y no tiene casos ni resultados esperados.
- Lo observado:
  - todos los casos de autoridad protegida: `protected=true`, DENY, `FLOW_AUTHORITY_PROTECTED`;
  - las escrituras de `git config` directas, locales, con alcances abreviados, detrás de otro
    programa, en scriptblocks de PowerShell, con `Start-Process`, arreglos, `-FilePath` y
    continuación de línea, protegidas;
  - las lecturas de `git config` demostrables, `READ_ONLY` / ALLOW;
  - una MCP con destino protegido, DENY;
  - una MCP inocua: ALLOW con la tarea sana, DENY con la tarea bloqueada, con la decisión humana
    pendiente y con la autoridad ambigua;
  - `git status`, `git diff` y las lecturas genuinas no activaron el guard;
  - la sobreprotección conservadora documentada apareció como estaba prevista.

E-24 ya no queda pendiente de otra revisión independiente. El guard de autoridad no se modificó por
esta evidencia.

## Las pasadas

| Pasada | Escenarios | Contradichos | Compuerta |
|---|---|---|---|
| Refutador, primera | 32 sostenidos | E-01, E-18, E-24 | no corrió entera |
| Refutador, segunda | 34 sostenidos | E-24 | no corrió entera |
| Refutador, tercera | 34 sostenidos | E-24 | 39055/39055 |
| Refutador, cuarta | 35 sostenidos, **sin sondas propias sobre E-24** | ninguno | 39080/39080 |
| Revisión independiente | — | **E-24**: 3 clases, 9 entradas | — |
| Refutador, quinta | 34 sostenidos | E-24: 3 formas más; afirmaciones 6, 7 y 8 | 39122/39122 |
| Refutador, sexta | 35 sostenidos | ninguno; afirmaciones 7 y 8 pendientes | 39154/39154 |
| Refutador, séptima | 34 sostenidos | E-24: `xargs git config <nombre>`; afirmaciones 7 (en la letra) y 9 | 39215/39215 |
| Refutador, octava | 34 sostenidos | E-24: las MCP no llegan al hook (E24-E14a a f); una ruta a más de 8 niveles o como clave; afirmación 7 a nivel sistema | 39245/39245 |
| Refutador, novena | 34 sostenidos | E-24 y E24-E14a a f: una MCP que corre comandos; un JSON de 3000 niveles que el hook no lee; afirmaciones 7, 8 y 9 a nivel sistema | 39266/39266 |
| Refutador, décima | 33 sostenidos | E-24: el comando como arreglo; E24-E14a a f por su cláusula de controles (un apóstrofo era protegido); afirmaciones 8 y 9 | 39290/39290 (la primera corrida se cortó por una suspensión; árbol intacto) |
| Refutador, undécima | 34 sostenidos | E-24: E24-E18 por el orden de los campos, E24-E19 por un apóstrofo escapado; afirmaciones 8 y 9 | 39310/39310 (la primera corrida la cortó el refutador; árbol intacto) |
| Refutador, duodécima | — | E-24: un scriptblock sin espacio después de `{`, `Start-Process` con `@(...)` o `-FilePath:`; afirmaciones 8 y 9 | 39333/39333 |
| Refutador, decimotercera | 34 sostenidos; E24-E1 a E24-E20 sostenidos | E-24 y E24-E21: una continuación de línea que parte `git` o `config`; afirmaciones 8 y 9 | 39409/39409 |
| Refutador, decimocuarta | 35 sostenidos; E24-E1 a E24-E21 sostenidos; 9 afirmaciones sostenidas. **E-24, E24-E21 y las afirmaciones 8 y 9, solo con los tests de quien construyó**: un control de seguridad cortó las sondas adversariales propias. Repitió con sus entradas la de la decimotercera pasada (también con `\r\n` y con backtick), protegida, y los controles | ninguno | 39425/39425 |
| Refutador, decimoquinta | E-36 a E-43, E-45 y E-46 sostenidos, con sondas propias (27 invalidaciones, todas sin `ACTIVE`); E-10 de `53_context_bar`, un cambio cerrado, sostenido y sin debilitar | E-44: un `bienvenida.py barra` que devuelve un JSON sin la forma de la barra (`{}`, un texto, `{"state": "ACTIVE"}` solo) cortaba `-Doctor` con Set-StrictMode 2.0 en vez de volver a lo guardado | 39495/39495 |
| Revisión humana independiente de E-24 | E-24 sostenido sobre el árbol final: 39 casos de la persona, 48 filas | ninguno | — (runner de solo clasificación) |
| Refutador, decimosexta (otra sesión que la que construyó el arreglo de E-44) | E-44, E-39 y E-45 sostenidos | ninguno; 0 sin sustento. Dos observaciones NON-BLOCKING, en «Lo que queda abierto» | — |

Cada arreglo se escribió primero como test y se vio en rojo:

| Arreglo | Aserciones en rojo |
|---|---|
| Lo de la revisión independiente | 24 |
| Lo de la quinta pasada | 28 |
| La forma de arreglo de PowerShell en E24-E10, una variante cercana que anotó la sexta pasada | 4 |
| `git config` local como autoridad, y las lecturas que el parser no conocía (E24-E13) | 32 |
| `xargs git config <nombre>`, la regresión de la séptima pasada (E24-E13j) | 8 |
| Una herramienta MCP que escribe la autoridad (E24-E14) | 12 |
| El matcher que no alcanzaba a `mcp__*`, y la profundidad y las claves (E24-E15) | 12 |
| Una MCP que corre comandos (E24-E16) y un evento que no se puede leer (E24-E17) | 12 |
| El comando repartido y los bordes (E24-E18), las comillas sueltas (E24-E19) | 14 |
| El orden de los campos y los apóstrofos escapados: la bolsa de palabras (E24-E20) | 16 |
| El fallback de `-Doctor` ante un JSON que no es la barra (E-44, decimoquinta pasada) | 18 |
| El guard de `git config`: scriptblock, `@(...)`, `-FilePath:`, escapes, MCP y ambiguos (E24-E21) | 34 |
| La palabra como la une el shell: continuaciones, `$''`, `$()` (E24-E21, decimotercera pasada) | 16 |

La cuarta pasada sostuvo E-24 solo con los tests de quien construyó; el refutador lo dijo así. La
revisión independiente lo contradijo después. Por eso un sostenido del refutador sobre E-24 no
reemplaza la repetición de esa revisión.

## Escenarios

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Sin ningún número de uso: `USAGE_UNRESOLVED`, nunca `RESOLVED` | sostenido | sí | `66_integrity_cleanup.py`, `test_e01_…`, `test_e01b_…` |
| E-02 | Llega al libro por la barra y por `--ingerir`, una sola vez | sostenido | sí | `test_e02_…` |
| E-03 | La barra no lo muestra como tokens; el libro lo conserva | sostenido | sí | `test_e03_…` |
| E-04 | Un costo parcial da `COST_UNRESOLVED` | sostenido | sí | `test_e04_…` |
| E-05 | Un costo resuelto decide como siempre | sostenido | sí, por mutación | `test_e05_…` |
| E-06 | `compilar` con el plan sin estar listo: `PLAN_NOT_READY` | sostenido | sí | `test_e06_…` |
| E-07 | Con el TaskContext cambiado: `CONTEXT_STALE` | sostenido | sí | `test_e07_…` |
| E-08 | Con otro checkout: `REPOSITORY_MISMATCH` | sostenido | sí | `test_e08_…`, `test_e08b_…` |
| E-09 | `set`/`remove` no escriben el `.env` | sostenido | sí | `test_e09_…` |
| E-10 | Ninguna ruta del harness llama a `set` ni a `remove` | sostenido | sí, por mutación | `test_e10_…` |
| E-11 | Sesión bloqueada no corre `contabilidad` de otra tarea | sostenido | sí, por mutación | `test_e11_e12_…` |
| E-12 | El motivo nombra las dos tareas | sostenido | sí | `test_e11_e12_…` |
| E-13 | Tampoco con la otra tarea sana | sostenido | sí, por mutación | `test_e13_…` |
| E-14 | `context.repository` es el de la identidad del flujo | sostenido | sí | `test_e14_…` |
| E-15 | El aviso de ES0901 nombra lo que cuenta | sostenido | sí | `test_e15_…` |
| E-16 | Sin un libro con registros no hay `ACTIVE` | sostenido | sí | `test_e16_…`, `test_e16b_…`; texto ampliado en la quinta pasada |
| E-17 | `-Doctor` no muestra en OK una barra `CONFIGURED` | sostenido | sí, por mutación | `66-integrity-instalador.ps1`, 15 aserciones |
| E-18 | Una señal sin el registro del instalador no prueba | sostenido | sí | `test_e18_…`, `test_e18b_…`; contradicho en la primera pasada |
| E-19 | `plan` con una propuesta inválida sale con 2 | sostenido | sí | `test_e19_…` |
| E-20 | Un error inesperado no se disfraza de `PlanInvalido` | sostenido | sí, por mutación | `test_e20_…` |
| E-21 | `dev-iniciador-code` registrado y ruteable | sostenido | sí | `test_e21_…` |
| E-22 | El alias de la Store se avisa y no se toma por un Python | sostenido | sí | `test_e22_…` y el `.ps1` |
| E-23 | Lo desconocido sigue `UNRESOLVED`; `--out…` es escritura | sostenido | sí | `test_e23_…` |
| E-24 | Los puntos de persistencia que el texto nombra, protegidos | sostenido: decimocuarta pasada y **revisión humana independiente** | sí | `test_e24_…` a `test_e24n_…`; los casos de la persona revisora |
| E24-E1 a E24-E9 | Lo que encontró la revisión independiente | sostenidos | sí | `test_e24e_la_revision_independiente` |
| E24-E10 a E24-E12 | Lo que encontró la quinta pasada | sostenidos | sí | `test_e24f_la_quinta_pasada` |
| E24-E13a a E24-E13j | `git config` que escribe es autoridad, con cualquier alcance; sus lecturas pasan | sostenidos en la decimocuarta pasada | sí (E13i, no consta) | `test_e24g_git_config_que_escribe_es_autoridad` |
| E24-E14a a E24-E14f | Una herramienta desconocida que no es shell no escribe la autoridad | sostenidos en la decimocuarta pasada; la octava los contradijo (no llegaban al hook) y la novena con un JSON hondo | sí | `test_e24h_una_herramienta_desconocida_no_escribe_la_autoridad` |
| E24-E15 | El matcher alcanza a `mcp__*`; profundidad y claves | sostenido en la novena pasada, confirmado sobre una instalación real | sí | `test_e24i_las_herramientas_mcp_llegan_a_la_compuerta` |
| E24-E16 | Una MCP que corre comandos no escribe la autoridad | sostenido en la décima pasada | sí | `test_e24j_una_mcp_que_corre_comandos` |
| E24-E17 | Un evento que no se puede leer falla cerrado | sostenido en la décima pasada, de punta a punta | sí | `test_e24k_un_evento_que_no_se_puede_leer` |
| E24-E18 | El comando repartido en un arreglo o en campos, y los bordes | sostenido en la decimocuarta pasada; la undécima lo contradijo por el orden de los campos | sí | `test_e24l_una_mcp_con_el_comando_en_partes` |
| E24-E19 | Una comilla suelta en algo que no es un comando no es protegida | sostenido en la decimocuarta pasada; la undécima lo contradijo con un apóstrofo escapado | sí | `test_e24l_una_mcp_con_el_comando_en_partes` |
| E24-E20 | En cualquier orden y con cualquier comilla: la bolsa de palabras | sostenido en la decimotercera pasada | sí | `test_e24m_una_mcp_en_cualquier_orden` |
| E24-E21 | `git config` a la vista y sin prueba de lectura: protegido | sostenido en la decimocuarta pasada con los tests de quien construyó, y por la **revisión humana independiente**; la decimotercera lo contradijo con una continuación de línea | sí, 34 + 16 aserciones | `test_e24n_git_config_a_la_vista` |
| E-25 a E-34 | Las Waves 1–5 y los bloques cerrados siguen verdes | sostenidos | no consta | 65, 64, 63, 62, 61, 55, 60, 48, 30, 53 |
| E-35 | La compuerta entera | sostenido | no consta | corrida por cada pasada del refutador; la final, sobre el árbol del checkpoint, en «La compuerta final» |
| E-36 a E-43, E-45, E-46 | La evidencia de la Context Bar sobrevive al reinicio (aceptación manual B) | sostenidos en la decimoquinta pasada; E-39 y E-45, también en la decimosexta; la aceptación manual B, PASS | sí | `test_e36_…` a `test_e46_…`; E-45 también en `66-integrity-instalador.ps1` |
| E-44 | `-Doctor` sin una barra usable vuelve al estado guardado | sostenido en la decimosexta pasada, de otra sesión que la que construyó el arreglo; la decimoquinta lo contradijo | sí, 18 aserciones | `test_e44_…` y `66-integrity-instalador.ps1` (A a L con Set-StrictMode 2.0, y `-Doctor` entero con `{}`) |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## Las ocho afirmaciones

Con la letra del pedido de la Wave 6. La 7 tiene la redacción que ratificó la persona, y la 9 es
nueva, pedida por ella.

🔴 La tabla que tuvo este documento hasta la cuarta pasada usaba otra lista, una paráfrasis de
quien construyó. Desde la quinta pasada se verifica la letra original.

| # | Afirmación | Veredicto |
|---|---|---|
| 1 | Missing usage can never become RESOLVED accounting | sostenida |
| 2 | USAGE_UNRESOLVED reaches the ledger even if presentation hides it | sostenida |
| 3 | A partial budget cannot be reported WITHIN_BUDGET | sostenida |
| 4 | Direct library refutation cannot bypass flow preconditions | sostenida |
| 5 | Harness cannot write human-owned secret configuration through latent APIs | sostenida |
| 6 | Installation/runtime presentation never reports a stronger state than evidence supports | sostenida; contradicha en la quinta pasada (un libro con `"\n"` era `ACTIVE`) y arreglada (E-16b) |
| 7 | Unknown tool classes are never treated as READ_ONLY. They inherit the restrictions of MUTATING operations and are denied when the governed task is blocked, a human decision is pending on the governed task, or task authority is ambiguous | sostenida en la decimocuarta pasada, y por la revisión humana independiente (MCP inocua: ALLOW sana; DENY bloqueada, pendiente y ambigua). La letra original, «… remain fail-closed», fue un SPEC_OVERSTATEMENT ratificado por la persona |
| 8 | Qualification readiness does not claim protection beyond the declared threat model | sostenida en la decimocuarta pasada. Contradicha en las pasadas quinta, sexta y novena a decimotercera, y corregida cada vez |
| 9 | A mutating git config operation cannot write local .git/config through the governed tool path | sostenida en la decimocuarta pasada, y por la revisión humana independiente. Contradicha en las pasadas séptima a decimotercera, y corregida cada vez |

## Las afirmaciones 7 y 8: SPEC_OVERSTATEMENT, ratificado por la persona

**Decisión de la persona, 02-10-2026: B, SPEC_OVERSTATEMENT.** Se preserva el contrato cerrado de
las Waves 3 y 4. No hay deny global para `UNRESOLVED_TOOL_CLASS`, y no es un defecto de la
implementación. Lo que cambió es el texto, no el código:

- la afirmación 7;
- la frase de `qualification-readiness.md`;
- la sección «La clase desconocida» de la spec.

Lo que se observó:

```text
herramienta-desconocida --flag x, npm install, python script.py, curl ...
  tarea sana                    -> pasa
  tarea bloqueada               -> deny FLOW_TOOL_CLASS_UNRESOLVED
  decisión humana pendiente     -> deny HUMAN_DECISION_PENDING
  proyecto sin estado del flujo -> pasa
```

El contrato cerrado de la Wave 3 (`compuerta-del-flujo/spec.md`) clasifica `UNRESOLVED_TOOL_CLASS`
como «lo demás. Se trata como `MUTATING`», y `MUTATING` pasa con la tarea sana. E-25 de la Wave 3
pide deny solo con la tarea bloqueada. `64_interaccion_humana` E-53 afirma que, resuelta la decisión,
`npm test` vuelve a pasar.

La afirmación 7 decía «fail-closed» sin esa salvedad. La 8 caía por una frase de
`qualification-readiness.md`: «lo desconocido es `UNRESOLVED` y falla cerrado». Ahora esa frase dice:

- nunca `READ_ONLY`;
- las restricciones de `MUTATING`;
- no pasa con la tarea bloqueada, una decisión pendiente o la autoridad ambigua;
- puede pasar con la tarea sana.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Un `usage` con nulos o texto contaba como medido** (E-01, primera pasada).
2. **Un registro de instalación vacío probaba la señal** (E-18, primera pasada).
3. **`compilar` aceptaba un `gitlab` que salteaba su compuerta** (primera pasada).
4. **Las formas de nombrar un mismo archivo** (E-24, pasadas primera a tercera).
5. **Tres clases que solo vio la revisión independiente** (E24-E1 a E24-E9):
   - un `site-packages` como destino final;
   - las abreviaturas de alcance que acepta git y `-f<ruta>`;
   - `uniq -`, que la política leía como lectura y por eso salteaba el chequeo de persistencia.
6. **Tres formas de la quinta pasada** (E24-E10 a E24-E12):
   - `git config` lanzado por otro programa con sus argumentos en una palabra, o en un alias de `-c`;
   - un valor pegado con `=`;
   - un valor pegado a una opción corta.
7. **Un libro con un salto de línea era «con datos»** (afirmación 6, quinta pasada).
8. **La afirmación 7 decía más que el contrato de la Wave 3** (quinta pasada). Lo decidió la persona:
   SPEC_OVERSTATEMENT.
9. **`git config` sin alcance escribía `.git/config` sin protección** (encontrado al arreglar la
   revisión independiente). Un `core.fsmonitor` plantado con la tarea sana corría después en un
   `git status`, también con la tarea bloqueada. La persona lo clasificó MUST_FIX_BEFORE_QUALIFICATION,
   y se cerró dentro de la Wave (E24-E13).
   - Para que una lectura no se negara como escritura, el parser de `config` aprendió a reconocer:
     - un nombre solo;
     - `get` y `list`;
     - los modificadores de presentación.
10. **Esa lectura de «un nombre solo» soltó `xargs git config core.fsmonitor`** (séptima pasada).
    El valor lo agrega `xargs` al correr, y el refutador lo comprobó con git de verdad en un repo
    descartable. Era una regresión de quien construyó: detrás de otro programa, un nombre solo es
    escritura (E24-E13j).
11. **Una herramienta MCP de escritura podía escribir `.claude/`, `.git/` o un `~/.gitconfig`** con
    la tarea sana: nada miraba su `tool_input`. Lo vio quien construyó al analizar la afirmación 7, y
    ninguna pasada lo había encontrado. La persona lo clasificó MUST_FIX_BEFORE_QUALIFICATION
    (E24-E14).
12. **E24-E14 solo protegía al hook invocado a mano** (octava pasada). El matcher de la Wave 3 no
    alcanzaba a `mcp__*`, así que en una sesión real la herramienta no llegaba. Quien construyó
    probó la decisión del hook y no que la escritura se impidiera. El test probaba algo vecino.
    También faltaban las claves de un objeto y las rutas a más de 8 niveles. La persona decidió
    sumar `^mcp__` al matcher (E24-E15).
13. **Una MCP que corre comandos escribía lo que a Bash se le niega** (novena pasada). La política
    miraba sus valores solo como rutas (E24-E16).
14. **Un evento que el hook no podía leer pasaba** (novena pasada). Un `tool_input` de 3000 niveles
    hacía fallar `json.loads`, y el contrato de «salir 0 siempre» lo dejaba pasar, también con la
    tarea bloqueada (E24-E17).
15. **Una MCP de shell con el comando como arreglo** (décima pasada): cada palabra era un valor suelto
    (E24-E18).
16. **Un apóstrofo en un comentario de Jira se negaba como protegido** (décima pasada): las comillas
    sin cerrar eran «ante la duda, sí» también fuera del shell. Lo mismo le pasaba a Write con una
    ruta como `O'Brien.py` desde la Wave 4 (E24-E19).
17. **El límite «script de varias líneas» se alcanzaba con un solo `\n` al final** (décima pasada):
    ahora se miran los valores sin sus bordes.
18. **Cada arreglo por forma dejaba otra forma al lado** (pasadas octava a undécima): el orden de los
    campos, un apóstrofo escapado. Quien construyó cambió de mecanismo: una bolsa de palabras sin
    orden (E24-E20), que no depende de cómo una herramienta desconocida arma su comando. Va hacia
    el lado seguro, y la sobreprotección queda declarada.
19. **El shell también tenía su forma de al lado** (duodécima pasada): `& {git config ...}` sin
    espacio y `Start-Process` con `@(...)` o `-FilePath:git`. La persona decidió dejar de parsear
    forma por forma: el parser solo sirve para probar una lectura, y lo que deja ver git y `config`
    sin esa prueba es protegido, en el shell y en una MCP (E24-E21). Al probarlo aparecieron dos
    más del mismo tipo, cerradas por la misma regla y no una por una: un escape (`g\it`, ``g`it``,
    `g^it`) y un splat de PowerShell (`git config @a`), que el parser leía como lectura.
20. **La regla de la evidencia todavía se podía partir** (decimotercera pasada): una continuación de
    línea (`\` o `` ` `` y un salto) une `g`, `i` y `t` en el shell, y la evidencia borraba el
    escape pero dejaba el salto como separador. Se corrigió la regla y no el caso: la evidencia lee
    cada palabra como la une el shell —sin continuaciones de `\`, `` ` `` o `^`, y sin lo que vale
    vacío (`$''`, `$()`)—. Las formas vecinas (`g$'i't`, `"g$()it"`, `-FilePath:` con continuación)
    entraron por la misma regla.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`, «Wave 6 leftovers»:

- **INTENTIONAL_CONSERVATIVE_OVERPROTECTION**, decisión de la persona: un comando que deja ver git y
  `config` sin correr `git config` (`git commit -m "update config"`), o una MCP cuyo texto solo los
  menciona, se niega como protegido;
- **dos observaciones NON-BLOCKING de la decimosexta pasada**, las dos hacia el lado seguro:
  - `Test-FormaDeLaBarra` compara los nombres de las propiedades sin distinguir mayúsculas
    (HARDENING / LOW). No abre un hueco nuevo: un `bienvenida.py` adulterado puede mentir igual con
    los nombres correctos.
  - Un `bienvenida.py barra` válido que escribe algo en stderr hace que `-Doctor` vuelva al estado
    guardado (CONSERVATIVE_FALLBACK). Puede esconder un `ACTIVE` vivo detrás de lo guardado; nunca
    inventa uno.
- lo demás de esa entrada.

Los límites de E-24 siguen fuera, porque su destino o su intención solo se ven al correr:

- un glob;
- `Get-Variable PROFILE`;
- una ruta después de un `cd`;
- `pip install --user`;
- una concatenación que arma el nombre al correr;
- un paquete `sitecustomize/` o un `.pyw`;
- una MCP que recibe un script de varias líneas;
- una herramienta que no es `mcp__*` ni está en el matcher.

## La aceptación manual

Sobre `Desktop\harness-w6-aceptacion`:

- **A, la ingesta sin `usage`: PASS, de la persona**, en lo que observó:
  - dos eventos ingeridos y `USAGE_UNRESOLVED` presente;
  - los tokens presentados `N/D`, y el costo y el tiempo sin resolver;
  - ningún `0` como total resuelto;
  - el resumen con 12/34 conocidos y `resolved.tokens = false`, valores parciales y no totales.

  **Todavía no observado por la persona:** el libro evento por evento (`msg-sin-usage` →
  `USAGE_UNRESOLVED`, `msg-con-usage` → `RESOLVED`). No se declara como evidencia manual hasta que
  ella lea `ledger.jsonl`. Lo prueban por separado E-01, E-02 y el ensayo sobre una copia, que es
  evidencia automática y de quien construyó, no de la persona.
- **B, `-Doctor` y runtime: PASS, de la persona**, con Claude Code CLI real, repetida entera sobre
  el fixture actualizado con `-Update` (salida 0, 276 archivos, 4 hooks OK). La primera vez falló en
  B4 —el primer dibujo vacío de la sesión nueva pisaba la evidencia, y `-Doctor` leía el estado de
  SessionStart— y la persona decidió conservar la evidencia (E-36 a E-46). Lo observado en la
  repetición:
  - **B1:** `-Doctor` después del `-Update`: AVISO «Context Bar configurada. Reiniciá la sesión de
    Claude Code para activarla.»; guardado `RELOAD_REQUIRED`, `reloadRequired = true`,
    `activeInCurrentSession = false`, `lastSessionWithData = null`.
  - **B2:** en una sesión nueva, `dev-harness.py harness`: «Context Bar CONFIGURADA», «Reinicio de
    Claude Code: no hace falta».
  - **B3:** después de reiniciar, sin datos: `-Doctor` AVISO «Context Bar: CONFIGURADA, todavía sin
    una sesión que la haya dibujado con datos.»; `bienvenida.py barra`: `CONFIGURED`,
    `lastSessionWithData = null`.
  - **B4:** con un mensaje, la barra dibujó con datos reales (`HARNESS | claude-opus-5-5 | Ctx 51k |
    Tok 51k in / 4 out`) y `bienvenida.py barra` dio `ACTIVE` con `lastSessionWithData` de esa sesión.
    Después de un reinicio real: `-Doctor` OK «Context Bar: ACTIVA (última sesión con datos:
    b7128da7-…)»; `bienvenida.py barra`: `ACTIVE`, `activeInCurrentSession = false`, `lastSessionId`
    de la sesión nueva y `lastSessionWithData` de la anterior.

  Sostiene que la evidencia histórica no es actividad de la sesión actual, y que una sesión nueva o
  vacía no borra la evidencia compatible de la anterior.
- **C, `PlanInvalido`: PASS, de la persona.**
  - Lo observado: salida 2, «harness: la propuesta no trae ninguna unidad de trabajo.», sin
    traceback y sin plan escrito.

## La compuerta final

Sobre el árbol exacto del checkpoint, después de esta documentación: ver el informe de aceptación
final de la Wave 6. Si falla, no hay commit.

## Lo que esto no es

La Wave 6 está **aceptada técnicamente**: no está calificada. La calificación es otra fase, con sus
propios bloqueantes en `flow-governance/qualification-readiness.md`. VERSION sigue en 0.26.0.
