# Verificación — Integración de Flow Governance con 0.30.0, y `orchestration-plan/2.1`

**Estado:** cerrado · **Fecha:** 07-10-2026 · **Versión:** 0.31.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` en dos
pasadas, el 07-10-2026, sobre el worktree de `integration/flow-governance-0.31`:

- **Primera pasada, sobre `7593b75`:** corrió la compuerta entera (42422/42423, `EXIT=1`) y
  `correr.py -k plan_2_1`. Dio 17 sostenidos, E-20 contradicho y E-09, E-12 y E-13 sin sustento.
  El cambio volvió a trabajo.
- **Segunda pasada, sobre `dde03fe`:** corrió la compuerta entera, 42484/42484, `EXIT=0`
  (PowerShell 889/889, Python 41595/41595). Probó además `flujo --approve` de punta a punta con los
  fixtures de `64_interaccion_humana`.

**Resultado: 22 escenarios sostenidos, 0 leídos, 0 contradichos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | El schema y `plan --propuesta` dicen `orchestration-plan/2.1` y solo 2.1 | sostenido | sí | `71_plan_2_1.py::test_e01`, más E-13 de `64_modelo_de_dominio.py` |
| E-02 | El status del plan es exactamente los cuatro, sin los retirados | sostenido | sí | `71::test_e02` |
| E-03 | El status de la unidad es exactamente los tres | sostenido | sí | `71::test_e03` |
| E-04 | `blockers` es opcional y con forma cerrada | sostenido | sí | `71::test_e04` |
| E-05 | Un 2.0 de 0.30.0 valida como 2.1 | sostenido | sí | `71::test_e05`. La sonda de la primera pasada lo confirmó con el productor real de `0f8b725` |
| E-06 | Toda unidad `BLOCKED` escrita lleva `blockers`; las demás no | sostenido | sí | `71::test_e06` |
| E-07 | Sin precondiciones, o con una bloqueante, el plan es `BLOCKED` | sostenido | sí | `71::test_e07` |
| E-08 | Lo escrito está en el contrato, y un plan `BLOCKED` tiene su causa | sostenido | sí | `71::test_e08` (24 combinaciones, llegan a los cuatro estados), más E-15/E-21 de `64` |
| E-09 | La precedencia de `estado_de` | sostenido | sí | `71::test_e09`. En la primera pasada no probaba la fuente que bloquea: **sin sustento** |
| E-10 | Una capacidad no es un agente sin ruteo | sostenido | sí | `71::test_e10`, hasta `task-flow-state` |
| E-11 | Un agente sin ruteo bloquea la tarea en `PLANNING` | sostenido | sí | `71::test_e11` |
| E-12 | Los dos comandos leen 2.1, 2.0 y 1.0 y rechazan otra versión con 2 | sostenido | sí | `71::test_e12_los_comandos_rechazan_otra_version`. En la primera pasada solo se probaba la función: **sin sustento** |
| E-13 | `BLOCKED` se lee; `DELEGATING` o `READY` se rechazan con 2 | sostenido | sí | `71::test_e13_los_comandos_rechazan_lo_retirado`. En la primera pasada solo se probaba la función: **sin sustento** |
| E-14 | Un 2.1 con una unidad `BLOCKED` sin `blockers` se rechaza | sostenido | sí | `71::test_e14`, por la CLI, con los bytes intactos |
| E-15 | `--replanificar` sobre un 2.0 escribe 2.1 | sostenido | sí | `71::test_e15` |
| E-16 | Nadie le pasa `-Harness` al instalador de la fábrica | sostenido | sí | `71::test_e16` |
| E-17 | `-Doctor` calcula la barra sin mirar el harness | sostenido | sí | `71::test_e17`, textual; el aviso `CONFIGURADA` también se ve corriendo en `66-integrity-instalador.ps1` |
| E-18 | Un ciclo sale con 2 | sostenido | sí | `71::test_e18` |
| E-19 | La documentación dice 2.1, `BLOCKED` y `blockers` | sostenido | sí | `71::test_e19` |
| E-20 | La compuerta sale con 0 | sostenido | no consta | `.\tests\Invoke-Tests.ps1`, 42484/42484. En la primera pasada: **contradicho** (ver abajo) |
| E-21 | Los seis schemas de Flow Governance tienen su concepto | sostenido | sí | `64_modelo_de_dominio.py::test_e05_*`, 1003/1003 |
| E-22 | Una decisión sobre un plan viejo lo escribe en 2.1 | sostenido | sí | `71::test_e22`, más la prueba de punta a punta del refutador |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá la lleva solo E-20, que
> es la suite entera.

## E-20, contradicho en la primera pasada

```
.\tests\Invoke-Tests.ps1 sobre 7593b75 -> 42422/42423, EXIT=1
[harness-unico - un solo producto, instalado] E-16 cada archivo tiene el contenido de 0.28.0,
salvo las cinco excepciones
    obtenido <.claude\harness\hooks\lib\tool_policy.py>
```

**Causa:** `7593b75` trajo R11, que cambia `tool_policy.py`, y la lista de excepciones de E-16 en
`63-harness-unico-instalador.ps1` no lo nombraba. La última corrida del constructor sobre ese
commit había sido solo del motor Python.

**Decisión:** el archivo entra a la lista, con su motivo, igual que `flujo/estado.py` y
`estado_de_tarea/decisiones.py`, que cambian por D4 y D8. La aserción sigue cuidando que nada más
se aparte de la base. Lo registra la tabla de D9.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Una decisión humana sobre un plan 2.0 o 1.0 guardado caía al escribirlo.** `replanificar`
   dejaba la versión vieja, y `escribir` valida contra 2.1. Ningún test lo tocaba. Se arregló en
   `dde03fe` (D8) y lo fija E-22.
2. **E-12 y E-13 solo probaban la función,** no los dos comandos ni el código 2. Ahora los prueban
   por la CLI.
3. **E-09 no probaba la rama de la fuente que bloquea.**
4. **La spec no registraba lo que la integración pisa** de 0.30.0 y de harness-unico. Ahora lo
   registra la tabla de D9. También faltaba que un plan de 0.30.0 se lee pero no compila: está en
   el párrafo «Leer no es compilar» de D5.
5. **Tres textos viejos:**
   - el docstring de `PlanRechazado`;
   - la lista del validador en la descripción del schema;
   - `docs/orquestacion.md`, que prometía que un plan viejo «se usa tal cual».
6. **En la segunda pasada:**
   - el helper `_como_0_30_0` de `71` prometía más de lo que armaba, y se renombró `_sin_blockers`;
   - el título de E-16 de harness-unico seguía diciendo «cinco excepciones», y se corrigió.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- **Una decisión rechazada igual consume la intención de la persona.** `decisiones.aplicar` consume
  el `human-intent` antes de aplicar el efecto en el plan. Si el plan se rechaza (por ejemplo, una
  unidad `BLOCKED` sin causa derivable), el plan queda intacto pero la intención queda gastada.
  Contradice el docstring de `aplicar` («no toca nada si falla»). No se tocó acá porque cambiar ese
  orden toca el candado de un solo uso de la Wave 4.
- **E-22 nunca se da sobre un 2.0 real de 0.30.0.** Esos planes no traen `flowPreconditions`, así que
  la compuerta no ofrece una decisión sobre ellos (D5). E-22 prueba la migración sobre un plan con
  precondiciones.

## Lo que ningún test cubre y se mira con los ojos

- Un `-Update` real de 0.30.0 a 0.31.0 sobre un proyecto con un plan 2.0 guardado: que `refute
  --compile` diga `PLAN_NOT_READY` y que `--replanificar` lo deje en 2.1.
- Una sesión real de Claude Code con estado del flujo, con el matcher nuevo de `PreToolUse`
  sobre `Agent`, `Task` y una herramienta `mcp__*`.
