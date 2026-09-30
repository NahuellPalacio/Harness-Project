# Verificación — Bloque 1: el conocimiento confiable se vuelve a mirar solo, en momentos controlados

**Estado:** cerrado · **Fecha:** 30-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` en dos
pasadas.

- **Primera, 29-09-2026:** sobre los 72 escenarios, con la compuerta entera (`37552/37552`, exit 0)
  y sondas de mutación en memoria. Dio 69 sostenidos, 1 contradicho (E-55) y 2 sin sustento (E-20 y
  E-48).
- **Segunda, 30-09-2026:** sobre E-17, E-18, E-20, E-48, E-55 y E-67, después de los arreglos.
  `python tests/correr.py -k 61_conocimiento` dio 283/283 y la compuerta, 37568/37568 con exit 0.

**Resultado: 72 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Ningún agent nuevo contra 0.26.0 | sostenido | no consta | `61_conocimiento_auto_refresco.py`, `git diff --name-status 6cff4b4 05dc830` |
| E-02 | Ninguna skill nueva contra 0.26.0 | sostenido | no consta | `61_conocimiento_auto_refresco.py`; no mira `.claude/skills` |
| E-03 | `auto_refresh.py` no tiene observación propia | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-04 | El documento del refresco es el de `frescura.documento` | sostenido | no consta | `61_conocimiento_auto_refresco.py`, campo por campo salvo `verified_at` |
| E-05 | Una versión nueva observada no cambia `source-registry.json` | sostenido | no consta | `61_conocimiento_auto_refresco.py`, byte por byte |
| E-06 | Una agenda que contradice al canónico se reconstruye desde él | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-07 | `EVENT_AND_TTL` sin revisión previa está vencido | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-08 | Un segundo antes de `nextCheckDueAt` no vence | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-09 | En el límite exacto, y después, vence | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-10 | `EVENT_ONLY` no vence por tiempo; un evento igual refresca | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-11 | Una política inválida da `AUTO_REFRESH_POLICY_INVALID` y cae a `EVENT_ONLY` | sostenido | sí | `61_conocimiento_auto_refresco.py`, las cuatro formas |
| E-12 | La política instalada: sin red en SessionStart, `EVENT_AND_TTL`, 24 h, y valida | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-13 | `INSTALL` refresca aunque no esté vencido | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-14 | `HARNESS_UPDATE` igual | sostenido | no consta | `61_conocimiento_auto_refresco.py` y `61-auto-refresco-instalador.ps1` |
| E-15 | `EXPLICIT_SOURCES_COMMAND` refresca, y `fuentes` a mano lo anota | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-16 | `PRE_KNOWLEDGE_PROMOTION` refresca aunque no esté vencido | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-17 | `PRE_NORMATIVE_OPERATION_IF_STALE` solo si venció; `plan` refresca antes | sostenido | sí | `61_conocimiento_auto_refresco.py` (segunda pasada) |
| E-18 | SessionStart no importa red ni cambia `harness.fuentes.json` | sostenido | no consta | `61_conocimiento_auto_refresco.py` (segunda pasada); débil, ver abajo |
| E-19 | Una capacidad `DISABLED` bloquea sin llamar al observador | sostenido | sí | `61_conocimiento_auto_refresco.py`, las tres capacidades |
| E-20 | El bloqueo conserva las fechas y el canónico, y anota `lastAttemptAt` | sostenido | sí | `61_conocimiento_auto_refresco.py` (segunda pasada) |
| E-21 | `AVAILABLE` sin `jira.attachment.read` sigue bloqueado | sostenido | no consta | `61_conocimiento_auto_refresco.py`, la función pura; de punta a punta, por E-19 |
| E-22 | Con las tres `ENABLED` sale al canal y limpia el `errorCode` | sostenido | no consta | `61_conocimiento_auto_refresco.py`; una sonda de mutación lo hace fallar |
| E-23 | Metadata igual y hash ya observado: no baja nada | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-24 | Versión posterior en el nombre: `UPDATE_AVAILABLE` sin bajar | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-25 | La aceptada sigue siendo la anterior en registro, decisiones y agenda | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-26 | La agenda separa `acceptedVersion` y `observedVersion` | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-27 | Otro `attachmentId` con la misma versión baja y hashea una vez | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-28 | Misma versión con otro hash: `SOURCE_INTEGRITY_ALERT`, nunca `CURRENT` | sostenido | no consta | `61_conocimiento_auto_refresco.py`; la segunda parte va por `resolver_y_escribir` |
| E-29 | Dos refrescos sin cambios: mismos estados y nada bajado la segunda vez | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-30 | La misma evidencia da lo mismo en dos proyectos | sostenido | no consta | `61_conocimiento_auto_refresco.py`; débil, ver abajo |
| E-31 | No llama a aceptar, y `decisions` queda igual | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-32 | Ningún refresco escribe `source-registry.json` | sostenido | no consta | `61_conocimiento_auto_refresco.py` y E-05; débil, ver abajo |
| E-33 | Un `POSTPONE` se conserva y la fuente sigue `ACKNOWLEDGED_PENDING` | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-34 | Un `APPLY` se conserva con `by` y `at`, y no se crea ninguno | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-35 | El observador de Jira solo lee | sostenido | no consta | `61_conocimiento_auto_refresco.py`; débil, ver abajo |
| E-36 | Aceptada en una versión que el extracto no declara: `KNOWLEDGE_PROMOTION_INCOMPLETE` | sostenido | no consta | `61_conocimiento_auto_refresco.py`, con una fixture de ES0902 |
| E-37 | El refresco no cambia `reglas/` | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-38 | Ni las policies | sostenido | no consta | `61_conocimiento_auto_refresco.py`, `harnesses/desarrollo/controles/policies` |
| E-39 | Ni los checks | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-40 | Ni agents, skills ni reviews | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-41 | Todas `CURRENT` o `RETIRED`: `allowed` | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-42 | Integridad, cambio con la misma versión o regresión: `blocked`, y `plan` sale 2 | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-43 | Vencida y con el refresco fallido: `unresolved`, nunca `allowed` | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-44 | Solo `plan` llama a la compuerta, y en `unresolved` arma el plan y avisa | sostenido | no consta | `61_conocimiento_auto_refresco.py`; débil, ver abajo |
| E-45 | Un refresco fallido deja aceptada y estados como estaban | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-46 | La bienvenida muestra la versión aceptada | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-47 | `ES0901 6.3    ACTUALIZACIÓN DISPONIBLE → 6.4` | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-48 | La observada nunca a la izquierda ni junto a `ACTUAL` | sostenido | sí | `61_conocimiento_auto_refresco.py` (segunda pasada), fixture ES0903 |
| E-49 | Con la agenda vencida la bienvenida lo dice, sin decir verificado | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-50 | `VIGENCIA SIN VERIFICAR`, y el pendiente con su código | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-51 | La misma novedad avisa una sola vez | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-52 | Otra versión u otro adjunto vuelve a avisar | sostenido | no consta | `61_conocimiento_auto_refresco.py`; "otro adjunto" solo prueba la huella |
| E-53 | La agenda sin el token | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-54 | Ni `Authorization`, ni `Basic `, ni la credencial | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-55 | Ni el cuerpo crudo: solo las claves del schema | sostenido | sí | `61_conocimiento_auto_refresco.py` (segunda pasada), claves tomadas del schema |
| E-56 | `auto_refresh.py` no menciona `.env` ni el almacén | sostenido | no consta | `61_conocimiento_auto_refresco.py`, chequeo textual |
| E-57 | Jira por el adaptador de `armar` y el registro de capacidades | sostenido | no consta | `61_conocimiento_auto_refresco.py`, chequeo textual |
| E-58 | `pre-tool-use.py`, `secretos.py` y los permisos, como en 0.26.0 | sostenido | no consta | `61_conocimiento_auto_refresco.py`, `git diff --quiet` |
| E-59 | Un timeout deja `AUTO_REFRESH_TIMEOUT` y `UNRESOLVED` | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-60 | Una falla no mueve `lastSuccessfulCheckAt` | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-61 | Un refresco bien la mueve a su hora | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-62 | `nextCheckDueAt` es la última más `maxAgeHours`, y `null` en `EVENT_ONLY` | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-63 | Una agenda rota da `AUTO_REFRESH_STATE_UNREADABLE` y se reescribe válida | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-64 | Ocho escrituras concurrentes dejan un JSON válido y ningún temporal | sostenido | sí | `61_conocimiento_auto_refresco.py` |
| E-65 | `fuentes --archivo` y `fuentes` sin canal hacen lo de 0.26.0 | sostenido | no consta | `61_conocimiento_auto_refresco.py`; se apoya en E-70 |
| E-66 | Manual y automático dan los mismos estados | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-67 | `harness --verbose` muestra la agenda y las versiones, sin el `.env` | sostenido | no consta | `61_conocimiento_auto_refresco.py` (segunda pasada), también la línea `Canal` |
| E-68 | Instalar sin red y sin canal termina bien y dice pendiente | sostenido | no consta | `61-auto-refresco-instalador.ps1` |
| E-69 | `HARNESS_UPDATE` con una versión nueva no acepta nada | sostenido | no consta | `61_conocimiento_auto_refresco.py` |
| E-70 | `45` y `57` siguen en verde | sostenido | no consta | `45_conocimiento_fuentes.py` 265/265, `57_aceptar_fuentes.py` 159/159 |
| E-71 | `51` sigue en verde | sostenido | no consta | `51_bienvenida.py` 658/658 |
| E-72 | La compuerta sale 0 | sostenido | no consta | `Invoke-Tests.ps1`, `37568/37568` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

Quince escenarios llevan `sí` y cincuenta y siete `no consta`. Para los `no consta`, el refutador
juzgó uno por uno si una falla plausible del código haría fallar el test. En varios lo comprobó con
sondas de mutación en memoria, sin tocar el repositorio, como en E-22. Los que marcó débiles figuran
así en la tabla. El `sí` de E-20, E-48 y E-55 ahora es específico: el constructor vio fallar cada
test reforzado bajo la mutación que antes se le escapaba, el 30-09-2026.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-55: la agenda escribía una clave que su schema no tiene.** `auto_refresh.py:298` guardaba
   `channel` en `.claude/runtime/knowledge-refresh.json`, y el test pasaba porque tenía `channel`
   fijado entre las claves esperadas. Se decidió el 30-09-2026 sacarlo de la agenda y no tocar el
   schema. El canal vive en `harness.fuentes.json` (`ficha.channel`), como ya decía la decisión
   "El canal es el último que funcionó". La bienvenida y la línea `Canal` de `harness --verbose`
   ahora lo leen de ahí. E-55 toma las claves permitidas del schema, y E-67 falla si el canal vuelve
   a leerse de la agenda.
2. **E-20 no veía "anota `lastAttemptAt`".** El bloqueo corría sobre una agenda que ya traía
   `lastAttemptAt` de la corrida anterior. Una falla que conservaba el intento viejo pasaba los 272
   asserts. Ahora el bloqueo corre en un momento distinto del intento anterior, y el test pide
   exactamente ese momento.
3. **E-48 no veía "ni junto a `ACTUAL`".** La única línea `ACTUAL` tenía la observada igual a la
   aceptada, así que no podía mostrar la diferencia. Con la flecha agregada también en `CURRENT`,
   todo pasaba. Se sumó la fixture ES0903, en `CURRENT` con 2.2 aceptada y 2.3 observada.
4. **Una afirmación de E-42 es vacía.** El assert `sin plan escrito` no puede fallar, porque la
   fixture no puede escribir un plan de ningún modo. El escenario igual lo sostiene el assert
   `por la compuerta`.
5. **`docs/reporte-de-seguridad.md:16-17` quedó viejo.** Dice que el estado del conocimiento es el
   que dejó `fuentes`, pero ahora `seguridad` refresca antes si la revisión venció.
6. **La tabla `Qué se construye` dice menos que el código.** La política, el vencimiento y la huella
   viven en `bienvenida.py`, y `auto_refresh.py:103-145` los envuelve. `bienvenida.py:400-402` también
   aprendió `minimum`, y eso no figura en la tabla.
7. **"La bienvenida no compara versiones", en las decisiones, no lo cubre ningún escenario.**
   `linea_de_version` compara la observada con la aceptada, por igualdad.

## Lo que queda abierto, anotado y no escondido

- **Los tests débiles, la afirmación vacía de E-42, el doc viejo y la tabla incompleta** quedan en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en
  *The knowledge auto-refresh closed with weak tests, a stale doc and a spec table that says less
  than the code*. Ninguno contradice un escenario.
- **E-55 lo sostiene solo el test.** El schema de la agenda no declara
  `additionalProperties: false`, así que `escribir_agenda` no rechazaría una clave de más. El test
  discrimina, y cerrar el schema cambiaría el contrato del pedido. Queda anotado en el mismo ítem.
- **Los riesgos de la spec siguen vigentes.** El canal recordado puede quedar viejo, la hora es
  local y sin zona, y `plan` puede tardar lo que tarda Jira cuando la agenda vence.

## Lo que ningún test cubre y se mira con los ojos

- Un `fuentes --auto` contra una Ficha real en Jira. Hoy no hay ninguna: ver
  *Neither the Ficha de Proyecto nor the acceptance-criteria field exists in any real Jira yet*, en
  `PENDIENTES-FH.md`.
- La bienvenida de una sesión real de Claude Code, con una fuente en
  `ACTUALIZACIÓN DISPONIBLE → x.y`, que avisa una vez y en la sesión siguiente calla.
- Un `install.ps1 -Update` sobre un proyecto real con un canal recordado: la instalación dice si el
  conocimiento quedó revisado o pendiente, y nunca lo da por verificado sin una revisión que salió
  bien.
