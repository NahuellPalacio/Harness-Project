# Verificación — Contrato de ejecución: la frontera estable entre Planning y cualquier implementación que ejecute WorkUnits

**Estado:** cerrado en la reverificación sobre 0.31.0 (08-10-2026) · **Fecha:** 07-10-2026 y
08-10-2026 · **Versión:** publicado en 0.32.0 junto con Task 4; parte de 0.31.0

🔴 **Lo que cierra el cambio hoy es la sección `## Reverificación sobre HARNESS 0.31.0`, al final:
70 sostenidos sobre `fdca5ce`.** Lo que sigue hasta ahí es la primera verificación, sobre la
construcción en 0.30.0 (`f9393cf`), sin tocar. El 08-10-2026 el contrato se integró con 0.31.0 en
la sección 37 de la [spec](spec.md), y por eso ese primer veredicto ya no alcanza.

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 07-10-2026,
en un contexto propio, sin el de la construcción. Tomó la [spec](spec.md) como fuente y usó
[informe-de-construccion.md](informe-de-construccion.md) solo como índice de lo que el constructor
afirmaba.

| | |
|---|---|
| Verificó | `harness-spec-refuter`, en un contexto aparte. No escribió nada en el repo: el árbol quedó byte a byte como estaba, con 730 archivos comparados por sha256, y borró sus temporales |
| Árbol verificado | El árbol de trabajo sin commitear sobre `0f8b725` (`main`): cuatro archivos modificados y nueve nuevos |
| Líneas de base | `f9393cf` para la arquitectura de Task 2, y `0f8b725` para el relevamiento de la spec |
| Registró | La sesión que construyó, con `write-a-verdict`. No agregó veredictos propios |

**Resultado: 57 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes y 0 delegados) y
0 sin sustento. No hay hallazgos bloqueantes. El cambio cierra.**

## Baseline

| | |
|---|---|
| `HEAD` | `0f8b725`, en `main`. Desde `f9393cf` cambian solo `README.md`, `docs/instalacion.md` y `terceros/LEEME.md` |
| `VERSION` | `0.30.0`. No hay commit de release |
| Modificados | `Pendientes/Fix-Harness/PENDIENTES-FH.md`, `docs/dominio/modelo-canonico.md`, `tests/casos/63-harness-unico-instalador.ps1` y `tests/casos/64_modelo_de_dominio.py` |
| Nuevos | los dos schemas `execution-*`, `bin/ejecucion/__init__.py` y `contrato.py`, ADR-0014, `spec.md`, `informe-de-construccion.md` y los dos casos `65` |
| Sin cambios | `VERSION`, `CHANGELOG.md`, `UPGRADE.md` y `docs/adr/0013-modelo-de-dominio-canonico.md` |
| Archivos prohibidos | `git diff --name-only f9393cf` vacío, antes y después de cada compuerta, y ninguno tiene archivos sin seguimiento. Son: el schema del plan, todo `bin/orquestacion/`, `dev-harness.py`, `bin/contabilidad/`, los schemas de contabilidad, del ledger de seguridad y de la RefutationUnit, hooks, checks, agentes, skills, `dev-refutador.md`, `install.ps1` y `manifest.json` |

## Método

- La spec es la fuente. El informe de construcción se usó solo como índice.
- Antes de cualquier compuerta, el árbol se copió a `%TEMP%`. Las mutaciones y las sondas corrieron
  sobre copias de esa copia, nunca sobre el árbol real ni mientras corría una compuerta.
- Los requests salieron de planes reales: `dev-harness.py plan PRB-7 --propuesta … --proyecto …`, en
  un proyecto temporal.
- `validar_request`, `validar_resultado`, `validar_rechazo`, `validar_informe` y `huella` se
  sondearon con casos propios, sin los fixtures del test:
  - más de 90 casos solo para `validar_resultado`;
  - la tabla de 22 por 3 de §14, celda por celda;
  - los 36 pares de estados.
- Hubo una instalación propia en un proyecto temporal y un runner aislado de los casos `.ps1`.

## Verificación AS-IS

**Las contradicciones centrales, reproducidas con un `plan --propuesta` real:**

| # | Qué se reprodujo |
|---|---|
| EC-01 | Una unidad con `assignedAgent: dev-inexistente` sale `agentExists: false`, `AGENT_NOT_FOUND` y `PENDING`, y el plan queda `READY_FOR_EXECUTION` |
| EC-02 | Las unidades de `orchestration`, `refutation` y `tooling` salen con `assignedAgent: ''` y `PENDING`, y el plan queda `READY_FOR_EXECUTION` (`registro_agentes.py:342-348`) |
| EC-03 | `PENDING` lo deciden solo la aprobación y las capacidades que faltan (`plan.py:320-326`). La compuerta normativa corre al planificar y la unidad no la refleja |
| EC-04 | Dos `--propuesta` distintas dan las dos `pln_PRB-7` y `plan_version: 1`, con huellas distintas |
| EC-08 | `jira.issue.read` en `ENABLED` deja la unidad `PENDING`. Ningún `tools:` de los once agentes llega a Jira ni a GitLab. `plan.py:252-255` avisa que las capacidades locales no se verifican |
| EC-10 | En una copia con un `agents/dev-huerfano.md`: `validacion_de_agente` da `AGENT_NOT_FOUND`, y `resolver_ruteo` da `ORPHAN_AGENT` |
| EC-22 | Una unidad de backend asignada a `dev-frontend` sale `VALID` y `PENDING`, y el plan queda `READY_FOR_EXECUTION` |

**Las citas `file:line` de las secciones 4 a 6 controladas son ciertas.** Son unas 60, de:

- `plan.py`, `dev-harness.py`, `refutacion.py` y `contexto-armar.py`;
- `install.ps1`, `capacidades.py`, `roster.py`, `registro_agentes.py`, `consumo.py` y `modelo.py`;
- `jira.py`, `eventos.py`, `productores.py`, `statusline.py`, `agregacion.py` y `libro.py`;
- los schemas, los agentes, `docs/orquestacion.md`, el modelo canónico, `PENDIENTES-FH.md` y el
  caso `64`.

**Hay tres imprecisiones, y ninguna sostiene una decisión que cambie:**

- **EC-11, sobre los agentes.** La spec dice que ocho agentes declaran un `agentResult`: son siete,
  y `dev-tool-builder` declara un `toolBuilderResult`. Los ocho usan los mismos cuatro estados, así
  que D8 sigue en pie.
- **EC-11, sobre las skills.** La spec dice "siete conjuntos de 9 a 18 valores": el rango real es de
  9 a 20, por `dev-observability`.
- **EC-14.** `refutation-unit.schema.json:127`, que es `checks.json`, no dice "lo escribe quien
  ejecutó". Lo dice solo `:100`, sobre `scope.json`.

## Escenarios

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| EX-E01 | Dos schemas con `$id`, `schema_version` de un valor, raíz cerrada y `controlar_soporte` | sostenido | si | `65_contrato_de_ejecucion.py`, `test_ex_e01` |
| EX-E02 | Un request armado desde un plan `READY_FOR_EXECUTION` real valida, y `validar_request` da `[]` | sostenido | si | `test_ex_e02`. Reproducido con un plan propio |
| EX-E03 | Si falta un obligatorio, sobra una clave o `workUnit` es una lista, falla nombrando el campo | sostenido | si | `test_ex_e03` |
| EX-E04 | Un resultado válido por terminal; `REQUESTED` y `RUNNING` no validan | sostenido | si | `test_ex_e04` |
| EX-E05 | `$defs.error` es {code, detail}, cerrado, con los 22 en orden y ninguno `TOOL_` | sostenido | si | `test_ex_e05`. La tabla de §14, comparada celda por celda |
| EX-E06 | `executionId` con patrón `exe_`; un UUID de sesión no valida | sostenido | si | `test_ex_e06` |
| EX-E07 | Un `planId` que no es de la `taskKey` falla, y una `taskKey` sin forma no valida | sostenido | si | `test_ex_e07` |
| EX-E08 | `huella` = `refutacion.huella`, sin importarla; dos `--propuesta` dan el mismo id, la v1 y huellas distintas | sostenido | si | `test_ex_e08`. La equivalencia se comprobó aparte sobre 18 valores límite (ver los no bloqueantes) |
| EX-E09 | Clave de idempotencia: una falsa falla; mismo plan, misma clave; otro plan, otra | sostenido | si | `test_ex_e09` |
| EX-E10 | Una `workUnit` tocada sin rehacer la huella falla | sostenido | si | `test_ex_e10` |
| EX-E11 | El resultado queda ligado por `executionId` y `requestFingerprint` | sostenido | si | `test_ex_e11` |
| EX-E12 | Un `planStatus` que no está listo no valida | sostenido | si | `test_ex_e12` |
| EX-E13 | Una `workUnit.status` `BLOCKED` o `WAITING` no valida | sostenido | si | `test_ex_e13` |
| EX-E14 | Los nueve `agentValidation` no ruteables, y un `assignedAgent` vacío o sin forma | sostenido | si | `test_ex_e14` |
| EX-E15 | `agentExists: false` en el plan con `VALID` al admitir pasa | sostenido | si | `test_ex_e15` |
| EX-E16 | `ORCHESTRATOR_AGENT` y `CRITIC_AGENT` no validan | sostenido | si | `test_ex_e16` |
| EX-E17 | Un agente de otro dominio falla | sostenido | si | `test_ex_e17` |
| EX-E18 | `capabilities` distinto de `ALL_AVAILABLE`, y `Read` o `Glob` como capacidad, no validan | sostenido | si | `test_ex_e18` |
| EX-E19 | Dependencias exactas, una vez cada una, y ninguna con el propio id | sostenido | si | `test_ex_e19` |
| EX-E20 | `PRECEDENCIA` es la de 9.2; `validar_rechazo` no acepta `PLAN_CHANGED`, ni códigos de corrida, ni `CANCELLED` | sostenido | si | `test_ex_e20`. `validar_rechazo` acepta exactamente 13 códigos |
| EX-E21 | `normativeGate: allowed` valida | sostenido | si | `test_ex_e21` |
| EX-E22 | `normativeGate: unresolved` valida | sostenido | si | `test_ex_e22` |
| EX-E23 | `blocked` no valida; `NORMATIVE_GATE_BLOCKED` va al pedir y en `REJECTED`; ningún código `GOVERNANCE` | sostenido | si | `test_ex_e23` |
| EX-E24 | Ningún campo de aprobación, presupuesto, timeout ni permiso | sostenido | si | `test_ex_e24` |
| EX-E25 | Seis transiciones verdaderas y treinta falsas | sostenido | si | `test_ex_e25`. Los 36 pares, sondeados aparte |
| EX-E26 | El camino feliz de `SUCCEEDED`, y sus roturas | sostenido | si | `test_ex_e26` |
| EX-E27 | `REJECTED` con los cuatro campos en null | sostenido | si | `test_ex_e27` |
| EX-E28 | `FAILED`: los códigos y el AgentReport | sostenido | si | `test_ex_e28`. Probado aparte con cada uno de los siete códigos de corrida |
| EX-E29 | `CANCELLED`: su código, el informe nulo y la evidencia según `startedAt` | sostenido | si | `test_ex_e29` |
| EX-E30 | Un terminal no cambia, y `TERMINALES` son cuatro | sostenido | si | `test_ex_e30` |
| EX-E31 | `SUCCEEDED` si y solo si el error es null | sostenido | si | `test_ex_e31` |
| EX-E32 | Execution no tiene `BLOCKED`, `PENDING` ni `WAITING` | sostenido | si | `test_ex_e32` |
| EX-E33 | La evidencia dice su estado, y lo que no es `RESOLVED` lleva `files: []` | sostenido | si | `test_ex_e33` |
| EX-E33b | El tiempo está solo en la raíz, y `evidence` es cerrada, con tres campos | sostenido | si | `test_ex_e33b` |
| EX-E34 | Un `SUCCEEDED` sin evidencia no pasa; un `REJECTED` sin evidencia sí | sostenido | si | `test_ex_e34` |
| EX-E35 | `output` es {path, fingerprint}, sin campos de texto; las rutas absolutas y con `..` no pasan | sostenido | si | `test_ex_e35`. Rutas de Windows, UNC, `c:x` y `\`, sondeadas aparte |
| EX-E36 | El contrato del AgentReport | sostenido | si | `test_ex_e36` |
| EX-E36b | Execution no interpreta el `artifact` | sostenido | si | `test_ex_e36b`. El código no lee el `artifact`: se verificó leyéndolo y sondeándolo. La tercera cláusula del test es débil (ver los no bloqueantes) |
| EX-E37 | Ningún campo de consumo ni de referencia contable | sostenido | si | `test_ex_e37` |
| EX-E38 | No importa contabilidad, y E-40 y E-42 siguen verdes e iguales a `f9393cf` | sostenido | si | `test_ex_e38` |
| EX-E39 | Nada del Host fuera de `workUnit` | sostenido | si | `test_ex_e39` |
| EX-E40 | `result.host` es opaco y puede ser null | sostenido | si | `test_ex_e40` |
| EX-E41 | El schema del plan 2.0 y `plan.py`, byte a byte; E-13 a E-17, verdes | sostenido | si | `test_ex_e41` |
| EX-E42 | Los tres schemas que la ejecución va a alimentar, byte a byte | sostenido | si | `test_ex_e42` |
| EX-E43 | `workUnit` se valida contra `workUnits.items` del plan, y el request restringe seis campos | sostenido | si | `test_ex_e43` |
| EX-E44 | Diez contextos, y ocho conceptos con sus diez campos | sostenido | si | `test_ex_e44` |
| EX-E45 | Los schemas nuevos están en su concepto, y son 48 | sostenido | si | `test_ex_e45` |
| EX-E46 | Las seis desigualdades nuevas y las catorce de antes | sostenido | si | `test_ex_e46` |
| EX-E47 | `## El límite de la ejecución` dice lo que existe, lo que no y lo que sigue | sostenido | si | `test_ex_e47` |
| EX-E48 | ADR-0014, aceptado, con siete decisiones | sostenido | si | `test_ex_e48` |
| EX-E49 | Once subcomandos y nada de concurrencia | sostenido | si | `test_ex_e49` |
| EX-E50 | No hay reintento | sostenido | si | `test_ex_e50` |
| EX-E51 | No hay SDK de modelos, y E-41 sigue verde | sostenido | si | `test_ex_e51` |
| EX-E52 | No escribe, no hay `.claude/ejecuciones` y nadie importa `ejecucion` | sostenido | si | `test_ex_e52` |
| EX-E53 | Se instala; `validar_request` corre desde el árbol instalado; no hay `ejecuciones` | sostenido | si | `65-contrato-de-ejecucion-instalador.ps1`, 15/15, y una instalación propia: 263 rutas en el lock, las cuatro nuevas iguales por hash al repo |
| EX-E54 | Los cinco títulos de §33, como `###` | sostenido | si | `test_ex_e54` |
| EX-E55 | `Invoke-Tests.ps1` sale con 0 | sostenido | no consta | La compuerta, con stdin desde NUL: 39899/39899, exit 0. Desde una consola da rojo por FH:1000, que ya existía antes del cambio |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá la lleva solo EX-E55,
> que es la compuerta misma.

**La auditoría del rojo visto.** El refutador reprodujo mutaciones sobre copias, con verde antes, el
rojo del propio escenario y la restauración comprobada:

- coinciden con el registro de §35 de la spec: EX-E36b (4 aserciones), EX-E28 (2), EX-E33b (3),
  EX-E53 (11 de 15, y 15 de 15 al restaurar), EX-E41 (1), EX-E25, EX-E26, EX-E11, EX-E35, EX-E44 y
  EX-E52;
- probó variantes propias de EX-E33b, EX-E41, EX-E08, EX-E15, EX-E17, EX-E19 y EX-E20, y dieron
  rojo;
- confirmó la nota de EX-E36b: una mutación que revienta con `KeyError` da una excepción y ninguna
  aserción del escenario, así que descartarla era lo correcto.

## Revisión de las adaptaciones a tests anteriores

**`64_modelo_de_dominio.py`:**

| Test | Qué cambió | Juicio |
|---|---|---|
| E-03 | Salen los tres asserts que ADR-0014 vuelve falsos: Execution aparte como límite reservado, Execution fuera de la tabla, ningún concepto de Execution. "Nueve" pasa a "diez" en el resto | No se perdió nada que siga siendo cierto |
| E-05 | De 46 a 48. S4 compara la unión de la tabla 3.2 y la de §22, y exige que la de §22 exista | Correcto |
| E-06 | De 14 a 20, con igualdad exacta de conjuntos. Las seis nuevas son exactamente las de §26.1, y se sigue exigiendo una ruta que exista | Correcto |
| E-09 | El conteo exacto pasa a ≥ en "existe" y sale en "no existe". Lo compensan 13 anclas en "existe" y 12 en "todavía no existe", que cubren cada ítem. Las cinco frases de invariantes y preguntas siguen | Correcto |

**`63-harness-unico-instalador.ps1`:**

- suma exactamente las cuatro rutas, y 263 = 259 + 4;
- `$esperadas` se ordena con el mismo `Sort-Object` que usa `Get-HuRutas`;
- E-16 saltea solo esas cuatro.

**No se debilitó ninguna otra garantía.**

## Hallazgos

**Bloqueantes:** ninguno.

**No bloqueantes, sobre la fuerza de los tests:**

1. **La tercera cláusula de EX-E36b no discrimina.** Un mutante que "rescata" un `declaredStatus`
   inválido leyendo `status: X` del `artifact` sobrevive: 537/537 sobre la copia mutada. Los dos
   artifacts del par contienen `status: COMPLETE`. El código real no lee el `artifact`.
2. **EX-E08 no cubre floats ni booleanos sueltos.** Un mutante de `huella` que altera los floats
   sobrevive. La equivalencia real se comprobó aparte, sobre 18 valores límite.

**Precisión documental:**

3. **"Tres asserts", y fueron cinco tests.** §27, §34.1 y §36 dicen que cambian tres asserts de
   Task 2; se adaptaron cinco tests. E-06 y `63` eran inevitables, y la construcción lo declaró.
4. **EC-11 y EC-14** (ver la verificación AS-IS). ADR-0014 repite "ocho agentes declaran un
   `agentResult`".
5. **La coherencia 10 de §11.3 es ambigua.** "No se repite" puede leerse sobre todas las rutas, y
   un `output.path` igual a un `files[].path` pasa. El código mira repetidos solo dentro de `files`,
   y no normaliza: `./src/a.py` y `src/a.py` pasan.
6. **Tres detalles del modelo canónico y de la spec:**
   - la fila de Execution en el mapa no lista "Host Adapter" en su lenguaje, como sí hace §25;
   - varios `Dónde vive` no siguen al pie la fórmula de §26.1;
   - §33 cita *The agent's invariants…*, y el título real es *…three invariants…*.
7. **El informe de construcción sobredice una cosa.** Afirma que EX-F01, EX-F02 y P13 están en el
   documento canónico. El documento tiene la atomicidad y "una abierta por clave", pero no nombra
   esos ids ni la exclusión de sí misma al entregar. La spec sí los tiene todos.

**Deuda preexistente:**

8. **La compuerta es roja desde una consola** (FH:1000, fila 2 de prioridades). Lo causa
   `install.ps1:788`. Se reprodujo en `0f8b725` sin el cambio: 204/204 con stdin desde NUL, 203/204
   desde una consola.
9. **El validador de subconjunto acepta un `\n` final.** Usa `re.search` con `$`, así que
   `"exe_<32hex>\n"` y un `createdAt` con `\n` validan.

**Riesgo futuro de Task 4:**

10. **`workUnits.items` del plan no está cerrado.** Un request con claves de más en `workUnit`
    pasa `validar_request`. Es por diseño (§10.3), y lo cubre EX-I21 solo si el motor vuelve a
    derivar la unidad del plan y compara su huella.
11. **El `\n` final del punto 9, en Task 4.** Un `executionId` con `\n` usado como nombre de carpeta
    en `.claude/ejecuciones/<KEY>/<executionId>/` es un riesgo. Task 4 tiene que validar con un
    patrón anclado de verdad.

## Tests focalizados

Corridos por el refutador sobre el árbol real:

| Corrida | Resultado | Exit | Duración |
|---|---|---|---|
| `python tests/correr.py -k 65_contrato` | 537/537 | 0 | 45 s |
| `python tests/correr.py -k _modelo_de_dominio` | 987/987 | 0 | 73 s |
| `python tests/correr.py -k 63_harness_unico` | 180/180 | 0 | 20 s |
| `65-contrato-de-ejecucion-instalador.ps1`, aislado | 15/15 | 0 | 9,6 s |
| `63-harness-unico-instalador.ps1`, aislado | 188/188 | 0 | 205 s |

## Suite completa

| Corrida | stdin | Duración | PowerShell | Python | Total | Exit |
|---|---|---|---|---|---|---|
| 1 | consola | 23 min 26 s | 789/790 | 39109/39109 | 39898/39899 | 1 |
| 2 | NUL | 23 min 05 s | 790/790 | 39109/39109 | 39899/39899 | 0 |

El único fallo de la corrida 1 es `[Instalador — ciclo completo] y el error dice como resolverlo`,
el hallazgo 8. `pre-tool-use.py` (`61567f3`) y `zonas.py` (`e996067`) dieron el mismo hash antes y
después de cada corrida, igual al de `HEAD`.

## Scope

La Task siguiente no empezó:

| | |
|---|---|
| Execution Engine | no |
| ExecutionAdmission implementada | no |
| Host Adapter | no |
| Persistencia de ejecuciones, `.claude/ejecuciones` | no, ni en el repo ni en una instalación |
| Subcomando de ejecución | no: los once de `f9393cf` |
| Scheduler, colas, workers, concurrencia | no |
| Reintento o timeout en runtime | no |
| SDK de modelos, subprocess nuevo | no |

`contrato.py` lee solo `contexto-armar.py` y tres schemas, por `rutas.localizar`. No escribe, no
lanza procesos y no importa `refutacion` ni `contabilidad`. Su único efecto global es insertar
`bin/` en `sys.path`.

## Veredicto acumulado

```
sostenidos      57
contradichos     0
leídos           0   (0 independientes, 0 delegados)
sin sustento     0
```

## Lo que la verificación encontró y no habría encontrado un test verde

1. Dos mutantes que sobreviven: la tercera cláusula de EX-E36b y los floats de EX-E08. El código
   cumple, pero esos tests no lo probarían si dejara de cumplir.
2. La ambigüedad de "no se repite" en la coherencia 10, y que las rutas no se normalizan.
3. Que la `workUnit` abierta deja pasar dentro de la unidad claves del Host o un `timeout`.
4. Que el validador de subconjunto acepta un `\n` final.
5. Las cifras de EC-11 y la cita de EC-14.
6. Que la compuerta da rojo desde una consola por FH:1000, y no por este cambio.

## Lo que queda abierto, anotado y no escondido

- **En `Pendientes/Fix-Harness/PENDIENTES-FH.md`, ya anotados por la construcción:**
  - los cinco ítems de *What the execution contract found and left open*;
  - la nota sobre el cuarto cabo suelto de *The canonical domain model closed with five loose ends*,
    que ADR-0014 decide.
- **Para la spec de Task 4:** EX-F01 y EX-F02, los invariantes marcados "Task 4" y las decisiones
  diferidas P1 a P13, como dice §34.3 de la spec.
- **Ya en `PENDIENTES-FH.md` de antes:** FH:1000, el instalador sin `-NonInteractive` cuando stdin es
  una consola.
- **Todavía sin anotar:** los hallazgos 1, 2, 4 a 7, 9, 10 y 11 de arriba. La consigna de esta
  verificación prohibía tocar pendientes, así que el siguiente paso es llevarlos a
  `PENDIENTES-FH.md`. El 3 ya está declarado en el informe de construcción.

## Lo que ningún test cubre y se mira con los ojos

- **La verdad de las secciones 4 a 6 de la spec.** El refutador la contrastó a mano, con las
  reproducciones de arriba.
- **La coherencia del modelo canónico con el resto del documento.** No quedaron frases viejas del
  "límite reservado", y `### Plan ≠ Execution` sigue siendo cierto.
- **Que la spec haya cambiado solo en estado, marcas y §35 durante la construcción.** No está en
  git, así que no hay una versión anterior con qué compararla, y no se pudo verificar.
- **Que el contrato alcance para Task 4.** Lo prueba Task 4.

---

## Reverificación sobre HARNESS 0.31.0

**Fecha:** 08-10-2026 · **Baseline:** 0.31.0 (`fdca5ce`) · **Fuente:** la [spec](spec.md), con su
sección 37

Los veredictos los emitió `harness-spec-refuter` el 08-10-2026, en un contexto propio, sin el de la
construcción ni el de la integración. Usó el informe de construcción solo como mapa de lo que el
constructor afirmaba. Los registra la sesión que construyó, con `write-a-verdict`, sin agregar
veredictos propios.

**Resultado sobre `fdca5ce`: 70 escenarios sostenidos (57 históricos y 13 nuevos), 0 contradichos, 0
leídos (0 independientes y 0 delegados) y 0 sin sustento. No hay hallazgos bloqueantes. El cambio
cierra sobre 0.31.0.**

📌 **El 57/57 de arriba es sobre `f9393cf` y no se suma a este.** Es la misma lista de escenarios
históricos, vuelta a dictaminar sobre otra base.

### Baseline

| | |
|---|---|
| `HEAD` | `fdca5ce86e73ea2a47ad3745ff850310e88f80f5`, en `main`, tag `v0.31.0`. `git log fdca5ce..HEAD` vacío: no hay commit de Task 3 ni de release |
| `VERSION` | `0.31.0` |
| Árbol verificado | El de trabajo sin commitear: cinco modificados y diez nuevos |
| Modificados | `Pendientes/Fix-Harness/PENDIENTES-FH.md`, `Pendientes/Ideas-Harness/PENDIENTES-I.md`, `docs/dominio/modelo-canonico.md`, `tests/casos/63-harness-unico-instalador.ps1` y `tests/casos/64_modelo_de_dominio.py` |
| Nuevos | los dos schemas `execution-*`, `bin/ejecucion/__init__.py` y `contrato.py`, ADR-0014, `spec.md`, `informe-de-construccion.md`, este archivo y los dos casos `65` |
| Sin cambios contra `fdca5ce` | `VERSION`, `CHANGELOG.md`, `UPGRADE.md` y ADR-0013 |
| Código de 0.31.0 | Intacto. `git diff --name-only fdca5ce` vacío, y sin archivos nuevos sin seguimiento, sobre los hooks, `bin/flujo/`, `bin/estado_de_tarea/`, `bin/orquestacion/` (`plan.py` y el registro de agentes incluidos), `bin/contabilidad/`, `dev-harness.py`, `reglas/`, los schemas versionados, `install.ps1`, `manifest.json`, agentes, skills y checks |
| Cambio ajeno | Ninguno |

El refutador no escribió nada en el repo. El árbol terminó byte a byte como lo encontró, y el stash
de resguardo del constructor quedó intacto: lo leyó y no lo aplicó.

### Por qué se reverifica

0.31.0 pasó el plan de `orchestration-plan/2.0` a `2.1`, con `BLOCKED` público y `blockers` por
unidad, y trajo Flow Governance: el TaskFlowState, la compuerta del flujo en PreToolUse, la
HumanIntent, el HumanDecisionRecord y el SessionTaskBinding. El contrato se integró en la sección 37
de la spec, y cambió después de la primera verificación.

### Integración revisada

Lo que cambió en Execution Contract, comparado contra el stash del constructor:

- `contrato.py` suma `DELEGATION_NOT_ALLOWED` a `CODIGOS` y a `PRECEDENCIA`, y la coherencia 8: una
  WorkUnit sin `blockers`;
- el request admite solo `orchestration-plan/2.1` en `plan.schemaVersion`, y suma `admission.flow`;
- el resultado suma un código;
- ADR-0014 suma solo su sección de integración, y conserva sus siete decisiones;
- la spec cambia, en las secciones 1 a 36, solo el encabezado y la tabla de estado; lo nuevo está en
  la 37;
- este archivo y el informe de construcción suman solo una nota.

La historia sobre 0.30.0 no se reescribió.

### Escenarios históricos

La clasificación de 37.8 se confirma: 49 sin cambio, 1 con el fixture actualizado, 6 con la
expectativa actualizada y 1 reemplazado. Ninguno quedó "ya no aplica", y no hay pérdida de
cobertura. 29 escenarios arman su request con `_request()` y heredan el fixture nuevo. De ellos, los
28 sin cambio tienen las mismas aserciones que se verificaron sobre 0.30.0; el otro es EX-E12, con la
expectativa actualizada.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| EX-E01 | Dos schemas con `$id`, `schema_version` de un valor, raíz cerrada y `controlar_soporte` | sostenido | si | `65_contrato_de_ejecucion.py`, `test_ex_e01` |
| EX-E02 | Un request armado desde un plan 2.1 `READY_FOR_EXECUTION` real valida | sostenido | si | `test_ex_e02`, fixture actualizado. Reproducido con un plan propio. Rojo rehecho: 3 de 5 |
| EX-E03 | Si falta un obligatorio, sobra una clave o `workUnit` es una lista, falla nombrando el campo | sostenido | si | `test_ex_e03`. Rojo rehecho con el fixture heredado: 3 de 31 |
| EX-E04 | Un resultado válido por terminal; `REQUESTED` y `RUNNING` no validan | sostenido | si | `test_ex_e04` |
| EX-E05 | `$defs.error` es {code, detail}, cerrado, con los 23 en orden y ninguno `TOOL_` | sostenido | si | `test_ex_e05`, expectativa actualizada. La tabla de 23 por 4, celda por celda. Rojo rehecho: 1 de 10 |
| EX-E06 | `executionId` con patrón `exe_`; un UUID de sesión no valida | sostenido | si | `test_ex_e06` |
| EX-E07 | Un `planId` que no es de la `taskKey` falla, y una `taskKey` sin forma no valida | sostenido | si | `test_ex_e07` |
| EX-E08 | `huella` = `refutacion.huella`, sin importarla; dos `--propuesta` dan el mismo id, la v1 y huellas distintas | sostenido | si | `test_ex_e08`. Equivalencia propia sobre 25 valores |
| EX-E09 | Clave de idempotencia: una falsa falla; mismo plan, misma clave; otro plan, otra | sostenido | si | `test_ex_e09` |
| EX-E10 | Una `workUnit` tocada sin rehacer la huella falla | sostenido | si | `test_ex_e10`. Rojo rehecho: 2 de 2 |
| EX-E11 | El resultado queda ligado por `executionId` y `requestFingerprint` | sostenido | si | `test_ex_e11` |
| EX-E12 | Un `planStatus` que no está listo no valida, `BLOCKED` incluido | sostenido | si | `test_ex_e12`, expectativa actualizada. Rojo rehecho: 2 de 6 |
| EX-E13 | Una `workUnit.status` `BLOCKED` o `WAITING` no valida | sostenido | si | `test_ex_e13` |
| EX-E14 | Los nueve `agentValidation` no ruteables, y un `assignedAgent` vacío o sin forma | sostenido | si | `test_ex_e14` |
| EX-E15 | `agentExists: false` en el plan con `VALID` al admitir pasa | sostenido | si | `test_ex_e15`. La premisa cambió con 2.1 (R-05), y el escenario sigue valiendo |
| EX-E16 | `ORCHESTRATOR_AGENT` y `CRITIC_AGENT` no validan | sostenido | si | `test_ex_e16` |
| EX-E17 | Un agente de otro dominio falla | sostenido | si | `test_ex_e17`. EC-22 reproducido sobre 0.31.0. Rojo rehecho: 2 de 2 |
| EX-E18 | `capabilities` distinto de `ALL_AVAILABLE`, y `Read` o `Glob` como capacidad, no validan | sostenido | si | `test_ex_e18` |
| EX-E19 | Dependencias exactas, una vez cada una, y ninguna con el propio id | sostenido | si | `test_ex_e19`. Rojo rehecho: 2 de 10 |
| EX-E20 | `PRECEDENCIA` es la de 37.5, de quince; `validar_rechazo` no acepta `PLAN_CHANGED`, ni códigos de corrida, ni `CANCELLED` | sostenido | si | `test_ex_e20`, expectativa actualizada. `validar_rechazo` acepta exactamente 14. Rojo rehecho: 1 de 35 |
| EX-E21 | `normativeGate: allowed` valida | sostenido | si | `test_ex_e21` |
| EX-E22 | `normativeGate: unresolved` valida | sostenido | si | `test_ex_e22` |
| EX-E23 | `blocked` no valida; `NORMATIVE_GATE_BLOCKED` va al pedir y en `REJECTED`; ningún código `GOVERNANCE` | sostenido | si | `test_ex_e23` |
| EX-E24 | Ningún campo de aprobación, presupuesto, timeout ni permiso | sostenido | si | `test_ex_e24` |
| EX-E25 | Seis transiciones verdaderas y treinta falsas | sostenido | si | `test_ex_e25`. Los 36 pares, sondeados aparte |
| EX-E26 | El camino feliz de `SUCCEEDED`, y sus roturas | sostenido | si | `test_ex_e26` |
| EX-E27 | `REJECTED` con los cuatro campos en null | sostenido | si | `test_ex_e27` |
| EX-E28 | `FAILED`: los códigos y el AgentReport | sostenido | si | `test_ex_e28` |
| EX-E29 | `CANCELLED`: su código, el informe nulo y la evidencia según `startedAt` | sostenido | si | `test_ex_e29` |
| EX-E30 | Un terminal no cambia, y `TERMINALES` son cuatro | sostenido | si | `test_ex_e30` |
| EX-E31 | `SUCCEEDED` si y solo si el error es null | sostenido | si | `test_ex_e31` |
| EX-E32 | Execution no tiene `BLOCKED`, `PENDING` ni `WAITING` | sostenido | si | `test_ex_e32` |
| EX-E33 | La evidencia dice su estado, y lo que no es `RESOLVED` lleva `files: []` | sostenido | si | `test_ex_e33` |
| EX-E33b | El tiempo está solo en la raíz, y `evidence` es cerrada, con tres campos | sostenido | si | `test_ex_e33b` |
| EX-E34 | Un `SUCCEEDED` sin evidencia no pasa; un `REJECTED` sin evidencia sí | sostenido | si | `test_ex_e34` |
| EX-E35 | `output` es {path, fingerprint}, sin campos de texto; las rutas absolutas y con `..` no pasan | sostenido | si | `test_ex_e35`. Rutas sondeadas aparte (hallazgo 7) |
| EX-E36 | El contrato del AgentReport | sostenido | si | `test_ex_e36` |
| EX-E36b | Execution no interpreta el `artifact` | sostenido | si | `test_ex_e36b`. La tercera cláusula sigue débil (hallazgo 5) |
| EX-E37 | Ningún campo de consumo ni de referencia contable | sostenido | si | `test_ex_e37` |
| EX-E38 | No importa contabilidad, y E-40 y E-42 siguen verdes e iguales a `f9393cf` | sostenido | si | `test_ex_e38`. La base `f9393cf` vale: E-40 y E-42 son iguales en `f9393cf`, en `fdca5ce` y en el árbol |
| EX-E39 | Nada del Host fuera de `workUnit` | sostenido | si | `test_ex_e39` |
| EX-E40 | `result.host` es opaco y puede ser null | sostenido | si | `test_ex_e40` |
| EX-E41 | El schema del plan 2.1 y `plan.py`, iguales a `fdca5ce`; E-13 a E-17, verdes y sin cambios | sostenido | si | `test_ex_e41_el_plan_2_1_no_cambia`, reemplazado. La intención la cubren el propio EX-E41 y EX-G11. Rojo rehecho: 1 de 30 |
| EX-E42 | Los tres schemas que la ejecución va a alimentar, byte a byte | sostenido | si | `test_ex_e42`. Iguales en `f9393cf`, en `fdca5ce` y en el árbol |
| EX-E43 | `workUnit` se valida contra `workUnits.items` del plan 2.1, y el request restringe seis campos | sostenido | si | `test_ex_e43`. Rojo rehecho: 2 de 6 |
| EX-E44 | Diez contextos, y ocho conceptos con sus diez campos | sostenido | si | `test_ex_e44`. Conteo propio del mapa |
| EX-E45 | Los schemas nuevos están en su concepto, y son 54 | sostenido | si | `test_ex_e45`, expectativa actualizada. Rojo rehecho: 1 de 4 |
| EX-E46 | Las seis desigualdades nuevas y las catorce de antes | sostenido | si | `test_ex_e46` |
| EX-E47 | `## El límite de la ejecución` dice lo que existe, lo que no y lo que sigue | sostenido | si | `test_ex_e47` |
| EX-E48 | ADR-0014, aceptado, con siete decisiones | sostenido | si | `test_ex_e48` |
| EX-E49 | Doce subcomandos, los de `fdca5ce`, y nada de concurrencia | sostenido | si | `test_ex_e49`, expectativa actualizada. Rojo rehecho: 3 de 4 |
| EX-E50 | No hay reintento | sostenido | si | `test_ex_e50` |
| EX-E51 | No hay SDK de modelos, y E-41 sigue verde e igual a `fdca5ce` | sostenido | si | `test_ex_e51`, expectativa actualizada. Rojo rehecho: 1 de 5 |
| EX-E52 | No escribe, no hay `.claude/ejecuciones` y nadie importa `ejecucion` | sostenido | si | `test_ex_e52`. Pureza comprobada por AST |
| EX-E53 | Se instala; `validar_request` corre desde el árbol instalado; no hay `ejecuciones` | sostenido | si | `65-contrato-de-ejecucion-instalador.ps1`, 15/15, aislado y en la suite. El caso es idéntico al del stash |
| EX-E54 | Los cinco títulos de §33, como `###` | sostenido | si | `test_ex_e54` |
| EX-E55 | `Invoke-Tests.ps1` sale con 0 | sostenido | no consta | La compuerta, con stdin desde NUL: 43201/43201, exit 0 |

**Históricos sobre `fdca5ce`:** 57 sostenidos, 0 contradichos, 0 leídos (0 independientes y 0
delegados), 0 sin sustento.

### Escenarios nuevos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| EX-G01 | Un plan 2.1 `READY` con su WorkUnit `PENDING` da un request válido; 2.0 y 1.0 no validan | sostenido | sí | `test_ex_g01`. Rojo propio: `schemaVersion` acepta 2.0, 3 de 9 |
| EX-G02 | Un agente que el registro no rutea deja el plan y la unidad `BLOCKED`, y ninguno de los dos se admite | sostenido | sí | `test_ex_g02`. Rojo propio: `workUnit.status` acepta `BLOCKED`, 1 de 8 |
| EX-G03 | `blockers` solo dentro del snapshot; una `PENDING` con `blockers` no pasa | sostenido | sí | `test_ex_g03`. Rojo propio: la coherencia 8 apagada, 4 de 7 |
| EX-G04 | `admission.flow` es obligatorio y solo vale `DELEGATION_ALLOWED` | sostenido | sí | `test_ex_g04`. Rojo propio: `flow` deja de ser obligatorio, 3 de 16 |
| EX-G05 | Con el plan listo por los dos lados, el flujo frena la tarea por `CONTEXT_STALE` | sostenido | sí | `test_ex_g05`. Rojo propio, solo en la copia: `derivar` deja de ver `CONTEXT_STALE`, 3 de 7 |
| EX-G06 | La compuerta del flujo deja pasar o niega `Agent`, y no es la admisión: códigos disjuntos, ninguna importación | sostenido | sí | `test_ex_g06`. Rojo propio: `contrato.py` importa `lib.flow_gate` en una función sin uso, 1 de 8 |
| EX-G07 | `DELEGATION_NOT_ALLOWED` es el sexto de 23, va al pedir y en `REJECTED`, nunca en `FAILED` ni en `CANCELLED` | sostenido | sí | `test_ex_g07`. Rojo propio: puede ir en `FAILED`, 3 de 11 |
| EX-G08 | `planFingerprint` es la del TaskFlowState y cambia con un dato de 2.1 | sostenido | sí | `test_ex_g08`. Rojo propio: `huella` ignora `capabilityStatus`, 2 de 9 |
| EX-G09 | La clave sale de `taskKey`, `planFingerprint` y `workUnit.id`; la sesión no es identidad | sostenido | sí | `test_ex_g09`. Rojo propio: el request suma `sessionBinding`, 1 de 4 |
| EX-G10 | Ni la intención humana ni el estado del flujo viajan; del flujo, solo `admission.flow` | sostenido | sí | `test_ex_g10`. Rojo propio: `admission` suma `humanIntentId`, 1 de 3 |
| EX-G11 | Lo de 0.31.0 no se toca, y no hay archivos nuevos entre ello | sostenido | sí | `test_ex_g11`. Rojo propio: un archivo nuevo sin seguimiento en `bin/flujo/`, 1 de 20 |
| EX-G12 | El modelo canónico integrado: diez contextos, el flujo no es uno, y los bloques de Execution | sostenido | sí | `test_ex_g12`. Rojo propio: ExecutionError vuelve a decir "veintidós", 1 de 11 |
| EX-G13 | ADR-0014 con su sección de integración; la spec con 37.2 y 37.8 completas | sostenido | sí | `test_ex_g13`. Rojo propio: 37.8 con un impacto "ya no aplica", 1 de 13. Recuento propio de 37.2: 1 A, 8 B, 10 C, 4 D y 2 E |

**Nuevos:** 13 sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá la lleva solo EX-E55,
> que es la compuerta misma.

**La auditoría del rojo visto.** El refutador hizo 26 mutaciones propias sobre una copia completa
del repo, con `.git`:

- los 13 EX-G, con nueve mutaciones distintas de las de la construcción;
- los ocho históricos que cambiaron en 37.8: EX-E02, E05, E12, E20, E41, E45, E49 y E51;
- cinco de muestra con el fixture heredado: EX-E03, E10, E17, E19 y E43, para ver que el fixture
  nuevo no los neutralizó.

En cada una vio el escenario en verde antes, corrió un proceso nuevo, contó solo las aserciones del
escenario y comprobó la restauración por sha256. Las 26 dieron rojo y quedaron restauradas. La
copia terminó idéntica al árbol real, 791 archivos y ninguno distinto, y la borró. Los 43 históricos
que no cambiaron en texto ni en aserciones se apoyan en el registro de §35, en la auditoría de la
primera verificación y en la suite verde.

### Semántica

**Quién es dueño de cada condición:**

| Condición | Contexto dueño | ¿Execution la consume? | ¿Execution la recalcula? |
|---|---|---|---|
| Forma de la TaskKey, del id de la WorkUnit y de `requestedBy` | Execution | es suya, por el schema | — |
| El plan existe y se lee, por `plan.aceptar_guardado` | Planning | sí, regla 2; la implementa Task 4 | no: `contrato.py` no lee planes ni migra |
| `meta.task_key` del plan | Planning | sí | no |
| La huella del documento, para `PLAN_CHANGED` | Execution, con el algoritmo de `refutacion.huella` | sí | calcula su huella; no recalcula una decisión |
| Plan 2.1 listo por los dos lados: lo escrito y `estado_de` | Planning | sí: `admission.planStatus` admite solo `READY_FOR_EXECUTION` | no |
| `delegationAllowed` | Planning, por el TaskFlowState (`flujo/estado.permisos`) | sí: `admission.flow` | no |
| La WorkUnit está en el plan y `PENDING` | Planning | sí: el snapshot, con el enum `PENDING` | no |
| `blockers` | Planning | no como fuente; solo la coherencia "una `PENDING` sin `blockers`" | no |
| La compuerta normativa | Normative Sources (`auto_refresh`) | sí: `admission.normativeGate`, `allowed` o `unresolved` | no (hallazgo 1) |
| El agente: ruteable, tipo y dominio | Catalog, por el AgentRegistry | sí: `admission.agent` | compara el dominio del registro con el de la unidad (D6); no decide si existe |
| Las capacidades disponibles y provistas | Catalog y el Host Adapter | sí: `ALL_AVAILABLE`; lo provisto es de Task 4 | no |
| Dependencias satisfechas y duplicados | Execution | son suyas | — |
| La compuerta del flujo de PreToolUse | Guardrails, que lee el TaskFlowState | no | no |
| SessionTaskBinding | Work Intake | no: la `taskKey` viaja explícita | no |
| HumanIntent y HumanDecisionRecord | Planning | no: se llega por `planFingerprint` al plan | no |
| HostSession | External, el Host | solo `result.host.sessionRef`, como observabilidad | no |
| SecretGate y GuardrailChecks | Guardrails | no | no |

**La frontera.** La evidencia no sostiene una cadena lineal, sino entradas en paralelo a una
admisión escrita y sin implementar:

```
HumanIntent ─(flujo --approve / --alternative)─> replanifica el Plan 2.1       (Planning)
TaskFlowState (Planning) ─ permisos().delegationAllowed ───────────────────────┐
Plan 2.1 (Planning) ─ aceptar_guardado; READY escrito y por estado_de;         │
                      WorkUnit PENDING ─────────────────────────────────────────┤
NormativeFreshnessGate (Normative Sources) ─ allowed / unresolved ──────────────┤
AgentRegistry y capacidades (Catalog) ─ ruteable, tipo, dominio, disponible ────┤
Execution ─ dependencias y duplicados ──────────────────────────────────────────┤
                                                                                ▼
                     ExecutionAdmission (regla escrita en 37.5) ─> ExecutionRequest ─> [Task 4]

Aparte, sin dependencia contractual: la compuerta del flujo (Guardrails, PreToolUse), que lee el
state.json guardado y vigencia_local, y responde FLOW_* o SESSION_TASK_*.
```

**Lo que el refutador comprobó, con evidencia propia:**

- **El plan es `orchestration-plan/2.1`** (`plan.py:35`). Los estados del plan son `BLOCKED`,
  `CAPABILITY_RESOLUTION`, `WAITING_FOR_HUMAN_APPROVAL` y `READY_FOR_EXECUTION` (`plan.py:41`). Los de
  la unidad son `PENDING`, `BLOCKED` y `WAITING_FOR_HUMAN_APPROVAL` (`plan.py:43`). `blockers` va solo
  en una unidad `BLOCKED`.
- **La regla de lectura es la oficial.** Execution no tiene parser ni migración propios: valida el
  snapshot contra `workUnits.items`. Reproducido con `aceptar_guardado`:
  - un 2.0 y un 1.0 se aceptan tal cual, y `estado_de` los da `BLOCKED` porque no traen
    `flowPreconditions`;
  - un 3.0, y un 2.1 con una unidad `BLOCKED` sin `blockers`, dan `PlanRechazado`;
  - el request rechaza 2.0, 1.0 y 3.0 en `plan.schemaVersion`. Un 2.0 editado a mano con
    `flowPreconditions` da `READY` por `estado_de`, y el enum del request lo cierra igual.
- **Solo `READY_FOR_EXECUTION` cruza, y solo `PENDING`.** `BLOCKED`, `CAPABILITY_RESOLUTION` y
  `WAITING_FOR_HUMAN_APPROVAL` no validan, ni en el plan ni en la unidad. Execution no tiene
  `BLOCKED`: aparece solo en `agentDeclaredStatus`.
- **`blockers`.** Una `PENDING` sin `blockers` pasa. Una `BLOCKED` con `blockers` falla por el estado
  y por los `blockers`. Una `PENDING` con `[]`, con uno o con una clave de más falla: la forma la
  pone `workUnits.items`, y Execution suma solo la coherencia 8. En la raíz o en `admission` no
  entran: están cerradas.
- **El TaskFlowState.** La admisión lo consulta por la regla 6, con `permisos()["delegationAllowed"]`,
  que es `puede_avanzar` (`flujo/estado.py:556`) en las etapas que permiten delegar. El request guarda
  solo `admission.flow`, sin huella ni referencia del estado. `planFingerprint` coincide con
  `planRef.planFingerprint`. Cómo se obtiene el estado vigente es P14, de Task 4.
- **La compuerta del flujo no es la admisión.** `flow_gate.decidir` decide por llamada, de la sesión
  a la tarea, y `Agent` y `Task` son `WORKFLOW_ADVANCING` (`tool_policy.py:1504-1505`). Reproducido:
  `allow` por el camino gobernado, `deny` con `FLOW_STATE_STALE` sin reconciliar y con
  `FLOW_HARD_BLOCKER` reconciliado. `bin/ejecucion/` no la importa.
- **HumanIntent y SessionTaskBinding quedan afuera.** El request no tiene ninguna propiedad de los
  dos: solo `requestedBy`. Una cancelación deja la misma huella y la misma clave, y saca
  `delegationAllowed`. Siguen las tres desigualdades: ExecutionId ≠ HostSession, HostSession ≠ Task
  y SessionTaskBinding ≠ identidad.
- **La compuerta normativa y la del flujo son distintas.** La normativa es de Normative Sources, corre
  en `plan` (`dev-harness.py:1086`) y, por regla, en la admisión, y su código es
  `NORMATIVE_GATE_BLOCKED`. La del flujo es de Guardrails, corre en cada PreToolUse y sus códigos son
  `FLOW_*`. `NORMATIVE_GATE_BLOCKED` nunca se usa para un bloqueo del flujo. Lo inverso sí pasa: ver
  el hallazgo 1.
- **Errores y precedencia.** Son 23 códigos, los 22 más `DELEGATION_NOT_ALLOWED`, y no se retiró
  ninguno. `DELEGATION_NOT_ALLOWED`:
  - condición: el TaskFlowState vigente no da `delegationAllowed`;
  - dueño: Planning, por el TaskFlowState;
  - momento: al pedir y al entregar;
  - terminal posible: `REJECTED`; al pedir, vuelve como error sin crear una Execution.

  `PRECEDENCIA` coincide con 37.5: quince, con el nuevo en sexto lugar. `validar_rechazo` acepta 14 y
  rechaza un detalle de 301 caracteres, un código ajeno como `FLOW_HARD_BLOCKER`, una clave de más y
  null.
- **La huella y `PLAN_CHANGED`.** `flowPreconditions`, `capabilityStatus`, `knowledgeSources`,
  `humanApprovals`, `planHistory` y los `blockers` de una unidad entran en la huella y cambian la
  clave. Con el mismo `plan_id` y `plan_version`, otro documento da otra huella. `PLAN_CHANGED` va solo
  en `REJECTED`.
- **La idempotencia.** La clave es `huella([taskKey, planFingerprint, workUnit.id])`. El mismo plan y
  la misma unidad dan la misma clave, y otra huella da otra. Un cambio solo del TaskFlowState, o una
  cancelación, deja la misma: el flujo afecta la admisibilidad, no la identidad.
- **El request** sigue en 1.0, con raíz cerrada y once obligatorios. `plan.schemaVersion` admite solo
  2.1, y no queda ningún enum de 2.0. El cambio sería mayor, porque achica un enum y suma un
  obligatorio, pero 1.0 nunca se publicó: ninguna ref ni tag lo contiene, tampoco `v0.31.0`, y ni
  `CHANGELOG.md`, ni `UPGRADE.md`, ni `README.md`, ni el manifiesto, ni `docs/versiones/` lo nombran.
- **El resultado** cambió solo en un código del enum. No tiene flujo, intención, compuerta ni
  `blockers`. La única propiedad de sesión es `host.sessionRef`.
- **El AgentReport** se probó con `COMPLETE`, `PARTIAL`, `BLOCKED`, `FAILED`, texto contradictorio,
  Markdown con `agentResult`, `artifact` vacío, una clave de más, null, `"COMPLETE "` y bytes.
  Execution no interpreta el `artifact`.
- **El ciclo de vida** tiene seis estados y cuatro terminales: 6 de los 36 pares valen, y no hay
  `BLOCKED`, `PAUSED` ni `WAITING`. La evidencia sigue siendo `{repoRevisionBefore,
  repoRevisionAfter, changes}`, cerrada y sin tiempos.
- **El modelo canónico** tiene diez contextos en el mapa: los nueve de ADR-0013 y Execution. El flujo
  no es un contexto, y sus seis conceptos siguen en Work Intake, Planning y Guardrails. Los ocho
  conceptos de Execution están en Execution, el Host Adapter figura como infraestructura, y no
  quedaron frases de "límite reservado", de "nueve contextos" ni de Plan 2.0. Hay dos detalles: los
  hallazgos 3 y 8.
- **ADR-0014** sigue aceptado, con sus siete decisiones intactas y la sección de integración que
  precisa la 3 y la 7. **ADR-0013** es igual al de `fdca5ce`.

**La verificación AS-IS, sobre 0.31.0:**

| # | Qué se reprodujo | ¿Cambió con Flow Governance? |
|---|---|---|
| EC-01, EC-02 | Un agente inexistente deja la unidad `BLOCKED` con `agents.routing AGENT_NOT_FOUND`, y el plan `BLOCKED`. Lo mismo `assignedAgent: ""` en `orchestration` | Sí. `AGENT_UNAVAILABLE` queda para un registro que cambia después de planificar |
| EC-04 | Dos `--propuesta` distintas dan el mismo id y la v1, con huellas distintas | No |
| EC-05 | Las aprobaciones se resuelven con `flujo --approve` y `--alternative` | Sí (R-08) |
| EC-08 | `jira.issue.read` en `ENABLED` deja el plan `READY` y la unidad `PENDING` | No |
| EC-11 | Siete agentes tienen `agentResult` con los cuatro valores | No |
| EC-22 | Una unidad de backend con `dev-frontend` sale `PENDING`, y el plan `READY` | No: hace falta `AGENT_DOMAIN_MISMATCH` |
| Capacidades | `gitlab` en `DISABLED` deja la unidad `BLOCKED` con `plan.capabilityStatus CAPABILITY_UNAVAILABLE`, y el plan `BLOCKED`. Una capacidad desconocida da `CAPABILITY_RESOLUTION` con `CAPABILITY_GAP` | Es nuevo en 0.31.0 |

**Los tres puntos que dejó la primera verificación:**

| Punto | Estado |
|---|---|
| `huella` sobre todos los tipos | Resuelto en lo semántico: `contrato.huella` y `refutacion.huella` dan lo mismo en 25 valores (str, vacío, Unicode, escapes, U+2028, int negativo y 2^70, float −0.0, 1e300, 5e-324 y 0.1+0.2, bool, null, listas, anidados, claves no ASCII, tupla, NaN e inf). El test EX-E08 sigue cubriendo 4: deuda de fuerza del test (hallazgo 5) |
| Un `\n` final que pasa por `$` | Sin corregir, y no era exigible en esta integración. Pasa en `executionId`, `createdAt`, `taskKey`, `idempotencyKey`, `planId`, `assignedAgent` y las capacidades del request, y en `executionId`, `endedAt` y `requestFingerprint` del resultado; también en `contrato.UTC.match`. La causa es `re.search` en `contexto-armar.py:932`. Un CRLF y un espacio sí se rechazan. Deuda y riesgo de Task 4 (hallazgo 6) |
| Las rutas | La ambigüedad sigue, y es más amplia: se rechazan las absolutas POSIX, Windows y UNC, las de `..` y las de `\`, pero pasan `./a`, `a/./b`, `a//b`, `a/`, `.`, `~/x`, `file:///x`, `src/a.py` junto a `./src/a.py` o `SRC/A.py`, y un `output.path` igual a un `files[].path`. Deuda y riesgo de Task 4 (hallazgo 7) |

### Tests focalizados

Corridos por el refutador sobre el árbol real, en serie, después de la suite:

| Corrida | Resultado | Exit | Duración |
|---|---|---|---|
| `python tests/correr.py -k 65_contrato` | 666/666 | 0 | 76,4 s |
| `python tests/correr.py -k 64_modelo` | 1035/1035 | 0 | 134,5 s |
| `python tests/correr.py -k 71_plan` | 276/276 | 0 | 38,9 s |
| `python tests/correr.py -k 61_flujo` | 184/184 | 0 | 23,8 s |
| `python tests/correr.py -k 62_estado` | 177/177 | 0 | 65,0 s |
| `python tests/correr.py -k 63_compuerta` | 487/487 | 0 | 119,7 s |
| `python tests/correr.py -k 64_interaccion` | 376/376 | 0 | 141,1 s |
| `python tests/correr.py -k 65_fail` | 284/284 | 0 | 17,5 s |
| `python tests/correr.py -k 66_integrity` | 727/727 | 0 | 113,1 s |
| `python tests/correr.py -k 67_integracion` | 43/43 | 0 | 34,4 s |
| `python tests/correr.py -k 70_r11` | 421/421 | 0 | 110,5 s |
| `python tests/correr.py -k 63_harness_unico` | 180/180 | 0 | 32,5 s |
| `65-contrato-de-ejecucion-instalador.ps1`, aislado, stdin desde NUL | 15/15 | 0 | 13,4 s |
| `63-harness-unico-instalador.ps1`, aislado, stdin desde NUL | 188/188 | 0 | 277,4 s |

El refutador leyó el runner aislado antes de usarlo: sus diez helpers son idénticos a los de
`Invoke-Tests.ps1`.

### Suite

| stdin | Desde | Hasta | Duración | PowerShell | Python | Total | Exit |
|---|---|---|---|---|---|---|---|
| NUL | 13:24:27 | 14:02:43 | 38 min 16 s (2296 s) | 904/904 | 42297/42297 | 43201/43201 | 0 |

No se corrió desde una consola, así que la deuda conocida de stdin queda separada de este cambio.
`pre-tool-use.py` (`b9cde9d9a2ad16f6a01c9f6189164ad4a21a901e`) y `zonas.py`
(`e996067644151ea113b83c90c382d52e328c1c17`) dieron el mismo hash que en `HEAD` antes de la suite,
después de ella y al final.

### Scope

La Task siguiente no empezó:

| | |
|---|---|
| Execution Engine | no |
| ExecutionAdmission implementada | no: es la regla escrita y `PRECEDENCIA` |
| Host Adapter | no |
| Persistencia, `.claude/ejecuciones` | no, ni en el repo ni en la instalación de EX-E53 |
| CLI de ejecución | no: los doce subcomandos de `fdca5ce` |
| Scheduler, colas, workers | no; nada importa concurrencia |
| Reintento o timeout en runtime | no |
| SDK de modelos, subprocess nuevo | no; E-41 contra `fdca5ce` en verde |

`contrato.py` es puro, comprobado por AST:

- importa solo `hashlib`, `importlib.util`, `io`, `json`, `os`, `re`, `sys` y `rutas`;
- su única E/S es leer los schemas y `contexto-armar.py`, que no tiene efectos al importarse;
- no consulta el flujo, el registro, las capacidades, el TaskFlowState, la contabilidad ni la
  refutación.

Flow Governance existente no es un motor de ejecución.

### Hallazgos

**Bloqueantes:** ninguno.

**No bloqueantes:**

1. **La compuerta normativa de 0.31.0 casi nunca da `blocked` por el camino de `plan`.** 0.31.0
   cambió `ensure_normative_knowledge_fresh` (`auto_refresh.py:474-523`, `05fefcd`): sin
   `requeridas`, nunca da `blocked`, y `plan` la llama sin ellas (`dev-harness.py:1086`). La 37.2 no
   registra ese cambio, y GD8 confirma D4 solo porque la función existe. Reproducido con una fuente
   exigida (ES0901/ES0902) que entra en `SOURCE_INTEGRITY_ALERT` después de planificar:
   - el plan sigue `READY` por los dos lados;
   - el flujo queda `BLOCKED` con `plan.knowledgeSources SOURCE_INTEGRITY_ALERT`, sin
     `delegationAllowed`;
   - la compuerta "como en `plan`" da `unresolved`, y con `requeridas` daría `blocked`;
   - por la precedencia sale `DELEGATION_NOT_ALLOWED` (sexto) antes que `NORMATIVE_GATE_BLOCKED`
     (noveno).

   Un bloqueo que nace en Normative Sources se informa con el código del TaskFlowState. No contradice
   ningún escenario, y el contrato no mezcla códigos: cambió por dónde llega el bloqueo, y es diseño
   de 0.31.0. Riesgo de Task 4: decidir si la admisión pasa `requeridas`, y qué dice el `detail`.
2. **Precisión documental.** Un mojibake, `â€”` en lugar de `—`, en el docstring de `test_e05` de
   `tests/casos/64_modelo_de_dominio.py:668`. Lo introdujo la integración: no está en `fdca5ce` ni
   en el stash. No cambia ninguna aserción.
3. **Precisión documental.** El modelo canónico pasó "la ModelTierApproval en `PENDING`" a *Lo que ya
   estaba, sin cambios*, en presente. Contradice el bloque `### ModelTierApproval` del mismo
   documento: en 0.31.0 se resuelve con `flujo --approve` o `--alternative`.
4. **Precisión documental.** Las "49 sin cambio" de 37.8 incluyen 28 que heredan el fixture nuevo.
   Está declarado en la introducción de 37.8, y la muestra de cinco confirma que el fixture no los
   neutralizó.
5. **Fuerza de los tests, preexistente.** La tercera cláusula de EX-E36b no discrimina: el mutante que
   "rescata" el estado del texto sobrevive, y se reprodujo. EX-E08 prueba cuatro valores; el código
   cumple, comprobado leyéndolo y sobre 25.

**Deuda preexistente:**

6. **El validador de subconjunto acepta un `\n` final** por `$` (ver los tres puntos de arriba).
7. **La ambigüedad de las rutas sigue, y es más amplia** (ver los tres puntos de arriba).
8. **El bloque `### Agent` del modelo canónico** dice "El plan no rechaza uno desconocido: lo marca con
   `agentExists: false`". La frase viene de `fdca5ce` y queda incompleta en 2.1: la unidad, además,
   queda `BLOCKED`. Task 3 solo agregó una oración después.
9. **Nota, no hallazgo.** `docs/versiones/0.31.0.md:128,148` todavía llama "décimo contexto" al
   flujo. Es historia de 0.31.0 y no se edita.

**Riesgo de Task 4:**

10. **`workUnits.items` está abierto:** una clave de más en `workUnit` pasa.
11. **La sesión ambigua, ya declarada en 37.11, se reprodujo:** con dos tareas con estado y una sesión
    sin vínculo, la compuerta da `SESSION_TASK_AMBIGUOUS`. Siguen P14 y la deuda de `git remote -v`
    bajo carga.

Ningún código de los 23 coincide con los literales de los cuatro módulos de `comun/hooks/lib/`. Las
coincidencias con `flujo/estado.py` (`PLAN_NOT_READY`, `CAPABILITY_UNAVAILABLE` y `CANCELLED`) están
declaradas en GD3 y en R-13.

### Resultado acumulado actual

Sobre `fdca5ce`:

```
históricos (57)    sostenidos 57 · contradichos 0 · leídos 0 (0 independientes, 0 delegados) · sin sustento 0
nuevos (13)        sostenidos 13 · contradichos 0 · leídos 0 (0 independientes, 0 delegados) · sin sustento 0
total actual (70)  sostenidos 70 · contradichos 0 · leídos 0 · sin sustento 0
```

El 57/57 de la primera verificación es sobre `f9393cf`, y no se suma a este. Registrar el veredicto
no cierra la versión.

### Lo que la verificación encontró y no habría encontrado un test verde

1. Que un bloqueo de Normative Sources llega como `DELEGATION_NOT_ALLOWED`, porque 0.31.0 cambió la
   compuerta normativa y la 37.2 no lo registra (hallazgo 1).
2. Que el modelo canónico se contradice sobre la ModelTierApproval (hallazgo 3).
3. Un mojibake que dejó la integración en un docstring (hallazgo 2).
4. Que un 2.0 editado a mano con `flowPreconditions` puede dar `READY` por `estado_de`, y que lo
   cierra el enum del request.
5. Que la ambigüedad de las rutas es más amplia de lo que vio la primera verificación.

### Lo que queda abierto, anotado y no escondido

- **En la spec, para Task 4:** la deuda de 37.11 (P14, la sesión del Host Adapter, el flujo que no
  conoce las Executions, la etapa `EXECUTION` sin inputs y `git remote -v` bajo carga), y lo de §34.3.
- **Todavía sin anotar en `PENDIENTES-FH.md`:**
  - los hallazgos 1, 2, 3, 5, 6, 7, 8, 10 y 11 de esta reverificación;
  - los hallazgos 1, 2, 4 a 7, 9, 10 y 11 de la primera verificación, que siguen sin llevarse.

  Los dos grupos esperan la decisión de la persona. Los que se repiten en las dos listas (la fuerza
  de EX-E36b y EX-E08, el `\n` final, las rutas y `workUnits.items` abierto) se anotan una sola vez.

### Lo que ningún test cubre y se mira con los ojos

- **Que la tabla de 37.2 sea completa.** El refutador la contrastó contra el código de 0.31.0, y le
  encontró el faltante del hallazgo 1.
- **Una sesión real del Host con la compuerta del flujo y una Execution.** No existe hasta Task 4.
- **Que el contrato alcance para Task 4.** Lo prueba Task 4.
