# Informe de cierre — canonical-domain-model

**Escrito por:** la sesión que construyó y cierra · **Fecha:** 05-10-2026 · **Versión:** 0.30.0 ·
**Commit:** `0f4e96f` · **Estado:** cerrado

📌 Esto no es un veredicto: el veredicto está en [verificacion.md](verificacion.md). Este informe
dice en qué quedó el pedido de cierre, paso por paso.

## En qué quedamos

**0.30.0 está cerrada en `0f4e96fb2db8daec155336dc0f8fe3a52c1a26ef`**, con la suite final en verde
sobre el árbol de ese commit: `39316/39316`, exit 0. La versión de partida era 0.29.0, en
`4c6f0f3`. Se trabajó en `main` y no se hizo push.

Este informe no entra en ese commit, porque un archivo no puede llevar el hash del commit que lo
contiene. Va en el siguiente, que es solo documental.

## Los pasos del pedido

| Paso | Qué | Estado |
|---|---|---|
| 1 | Revisar el estado antes de tocar nada | Hecho, ver `## El árbol antes de empezar` |
| 2 | Decidir la versión | Hecho: 0.30.0 |
| 3 | `VERSION` | Hecho: `0.30.0`, sin BOM, igual que antes |
| 4 | `CHANGELOG.md` | Hecho: `## [0.30.0] — 2026-10-05` |
| 5 | `UPGRADE.md` | Hecho: `## 0.29.0 → 0.30.0`, con los tres casos de un plan guardado |
| 6 | La documentación del cambio | Hecho: se actualizaron solo las cabeceras, y la historia de las tres verificaciones queda entera |
| 7 | Los hallazgos no bloqueantes | Hecho: un ítem nuevo en `PENDIENTES-FH.md`, sin arreglar ninguno |
| 8 | La suite final, sobre el árbol del commit | Hecho: `39316/39316`, exit 0 |
| 9 | Revisar el diff del release | Hecho, ver `## El árbol antes del commit` |
| 10 | El commit del release | Hecho: `0f4e96f` |
| 11 | El hash real | Hecho: está en este informe, que va en un commit aparte |
| 12 | Este informe | Hecho |
| 13 | El commit documental | Va con este archivo, y nada más |
| 14 | El árbol limpio | Después del commit documental |

## El árbol antes de empezar

- **El estado de partida:** branch `main`; `HEAD` en `4c6f0f3`, que es 0.29.0; `VERSION` decía
  `0.29.0`.
- **Lo que no había:** ni `CHANGELOG.md` ni `UPGRADE.md` tenían una entrada 0.30.0.
- **El veredicto:** `verificacion.md` terminaba en `SPEC VERIFIED`, con el acumulado en 52
  sostenidos, 0 contradichos, 0 leídos y 0 sin sustento.
- **`git status` tenía 32 entradas: 27 modificados y 5 nuevos.** Se atribuyeron con la tabla
  `Archivos` del informe de construcción y la spec, no por fecha:
  - los 27 modificados son los de esa tabla, sumando las pasadas de corrección;
  - los 5 nuevos son el ADR, la carpeta del cambio, `docs/dominio/` y los dos casos `64_*`.

  No apareció ningún cambio ajeno.

## La versión

**0.30.0, un bump menor.** La política del repo es SemVer, y el precedente está escrito en la nota de
0.29.0: *"un bump menor aunque el cambio rompe, como las versiones anteriores antes de 1.0"*.

`orchestration-plan/2.0` es la versión del contrato del plan, no la de HARNESS. Sigue siendo
`orchestration-plan/2.0`, y ningún otro `$id` cambió en el cierre.

`VERSION` llega solo al instalador, a `settings.json`, al lock y al `-Doctor`. Ningún otro archivo
del producto ni de los tests tiene escrita la versión actual.

## Lo que se escribió para la versión

| Archivo | Qué |
|---|---|
| `VERSION` | 0.30.0 |
| `CHANGELOG.md` | La entrada de 0.30.0. Marca con 🔴 el contrato 2.0, los rechazos nuevos de `plan`, la TaskKey de `seguridad` y la clave de libro. Tiene una sección de lo que no cambia: no hay ejecución, `controles/` no se instala y G2 sigue igual |
| `UPGRADE.md` | `## 0.29.0 → 0.30.0`, ver `## El contrato` |
| `docs/versiones/0.30.0.md` | Las cinco secciones |
| `docs/versiones/README.md` | La fila de 0.30.0 |
| `CLAUDE.md` | El conteo de la compuerta, de 38337 a 39316 |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Un ítem nuevo con los cinco hallazgos de la tercera verificación |
| `spec.md` | La cabecera pasa a "verificado y cerrado (0.30.0)" |
| `verificacion.md` | La cabecera dice la versión, 0.30.0. Los tres veredictos no se tocaron |

**Los mapas no se tocaron.** Este cambio no movió nada del recorrido entre el mensaje y la
respuesta, ni de la instalación. El mapa del recorrido sigue diciendo `v0.29.0`, y quedó anotado
en la nota de versión.

## La verificación

**`SPEC VERIFIED`: 52 escenarios sostenidos, 0 contradichos, 0 leídos y 0 sin sustento**, en tres
pasadas que se conservan enteras en `verificacion.md`:

```
primera verificación    48 sostenidos, 3 contradichos (E-02, E-05, E-06)  -> corrección
segunda verificación    E-05, E-06 y E-18b sostenidos, E-02 contradicho   -> corrección final
tercera verificación    E-02 sostenido                                    -> SPEC VERIFIED
```

## La suite

| Corrida | PowerShell | Python | Total | Exit | Duración |
|---|---|---|---|---|---|
| Final, sobre el árbol exacto del commit `0f4e96f`, con stdin vacío | 775/775 | 38541/38541 | **39316/39316** | **0** | 1533 s |
| Documental, sobre `0f4e96f` más este informe, con stdin vacío | 775/775 | 38541/38541 | **39316/39316** | **0** | 1580 s |

- La corrida documental no la pide el precedente de 0.29.0, porque ningún test lee este informe. Se
  hizo igual. Lo único que cambió en el árbol después es esta fila.
- En las dos corridas, `pre-tool-use.py` (`61567f3`) y `zonas.py` (`e996067`) tuvieron el mismo
  hash antes y después.
- `git status` quedó igual que antes de la corrida.
- El número que dicen `CLAUDE.md` y la nota es el de esta corrida, así que no hubo que corregirlo
  después.

## El árbol antes del commit

- **`git diff --check` da limpio.** La única excepción es la evidencia cruda de la primera
  verificación: son salidas copiadas tal cual, con espacios al final, y no se tocan.
- **La evidencia cruda** (`evidencia-verificacion/`) entra a pedido tuyo de la primera verificación,
  y la enlaza `verificacion.md`. No tiene credenciales ni rutas de `%TEMP%` o del usuario.
- **No entró nada temporal, de caché ni credenciales.** Los 57 archivos del commit son:
  - los 27 modificados y los 24 nuevos del cambio;
  - `VERSION`, `CHANGELOG.md`, `UPGRADE.md` y `CLAUDE.md`;
  - el índice de versiones y la nota nueva.
- **Sin cambios contra `4c6f0f3`:** `dev-refutador.md`, `install.ps1`, `manifest.json`,
  `comun/hooks/`, `comun/checks/`, `harnesses/desarrollo/checks/`, la matriz de ES0902, el
  AgentRegistry, `.claude/` y todas las `SKILL.md`.
- **No hubo limpieza oportunista,** y Execution no tiene implementación.
- **El commit:** `0f4e96f 0.30.0 cierra: el modelo de dominio canonico, y el plan pasa a
  orchestration-plan/2.0`, con 57 archivos (+8674 −50).

## El contrato

**`orchestration-plan/2.0`:** el plan tiene tres estados, y la unidad otros tres. La compatibilidad
con 1.0 tiene tres casos:

| Plan guardado | Qué pasa |
|---|---|
| Un 1.0 que escribió 0.29.0 | `refute --compile` lo lee sin reescribirlo, y `--replanificar` lo migra a 2.0 con `plan_version` + 1 y la historia entera |
| Un 1.0 con `DELEGATING` o una unidad `READY` | Se rechaza con 2, sin convertirlo, y hay que regenerarlo. 0.29.0 nunca escribió esos estados |
| Otra versión, o ninguna | Se rechaza con 2 |

Un rechazo no toca el plan, la refutación ni su caché. Lo que ya escribió la compuerta normativa en
esa corrida queda, porque no hay rollback global.

**El impacto del upgrade:** el `-Update` alcanza. Pasan a salir con 2 cuatro cosas que antes se
aceptaban:

- `seguridad` con una TaskKey inválida;
- `contabilidad` con una clave que no es una TaskKey ni un UUID de sesión;
- una propuesta con ids de unidad repetidos;
- una propuesta con una unidad de un dominio que no está en el plan.

## La deuda que queda abierta

Nada de esto se presenta como resuelto. Todo está en `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- **los doce ítems** de *What the canonical domain model found and left open*, con las
  contradicciones que no pasaron D15;
- **los cinco cabos sueltos de la tercera verificación,** en *The canonical domain model closed with
  five loose ends in its text and tests*:
  - el borde de la redacción de secretos sobre `assignedAgent`;
  - la disponibilidad en la fila Catalog de la spec y en I-21;
  - la precedencia de los estados de la unidad, que no está escrita;
  - un plan `READY_FOR_EXECUTION` con `agentExists: false`;
  - el caso de E-19 con un dominio desconocido, que no tiene test;
- **el diagnóstico `SECURITY_CONTROL_ID_TYPE_COLLISION`,** que ningún comando emite;
- **`controles/`,** que sigue sin instalarse, y el C3 que depende de eso;
- **la raíz del schema del plan,** que sigue abierta.

**Execution sigue reservado y sin implementar.** Nada toma una WorkUnit y la lleva a cabo.

## Estado

No queda nada que bloquee. Lo que falta afuera es correr el `-Update` en cada proyecto instalado:
los planes que escribió 0.29.0 siguen andando, y uno editado a mano con un estado retirado hay que
regenerarlo.

TASK 2 CLOSED
