# Bloque 1 — el conocimiento confiable se vuelve a mirar solo, en momentos controlados

**Estado:** especificado · **Fecha:** 29-09-2026 · **Bloque:** 1

## Qué problema resuelve

Hoy el harness sabe si una fuente gestionada está al día **solo cuando alguien corre
`dev-harness.py fuentes`**. Nadie lo corre: la bienvenida muestra el estado que dejó la última
corrida, y un plan, una evaluación de seguridad o una refutación trabajan sobre ese estado aunque
tenga semanas. Si en la Ficha apareció ES0901 6.4, el harness no se entera hasta que una persona se
acuerda.

Lo que falta no es un motor nuevo: `fuentes.py` ya observa con la metadata primero, `frescura.py`
ya resuelve los doce estados fallando cerrado, y `procedencia.py` ya sabe qué derivados quedan
viejos. Falta **cuándo** mirar, **con qué** permiso, y **dónde** dejar anotado que se miró.

## Qué queda afuera

- **Una llamada de red en SessionStart.** La política trae `sessionStartNetwork: false` y el hook no
  la mira: SessionStart sigue siendo local y de lectura. Un campo en `true` no conecta nada todavía;
  habilitarlo es otro cambio, con su presupuesto de latencia.
- **Aceptar o promover solo.** `UPDATE_AVAILABLE` no dispara `APPLY`, ni reescribe
  `source-registry.json`, ni toca matrices, policies, checks, reviews, agents o skills. Aceptar es
  `fuentes --aceptar`, con quien acepta; promover es el slice de promoción, que no existe todavía.
- **Un comando de promoción.** El disparador `PRE_KNOWLEDGE_PROMOTION` existe y se prueba en la
  función compartida; no hay comando que lo llame hasta que la promoción exista.
- **Bloquear lo que no es normativo.** `contexto`, `setup`, `estado`, `harness`, `contabilidad` y
  la navegación del repositorio no pasan por la compuerta: que Jira no conteste no es razón para no
  poder leer el código.
- **Bloquear `seguridad` por el estado de una fuente.** `seguridad` refresca si vence, pero no
  corta: su trabajo es REPORTAR la alerta, y ya la lleva como condición de bloqueo del reporte.
- **Cambiar el formato de `harness.fuentes.json`.** Las versiones aceptada y observada ya se
  derivan de lo que tiene (`acceptance.version` o `registry_version`, y `observed_version`).
- **Un Agent o una Skill.** Es código determinístico, sin modelo.

## Las decisiones, y por qué

### La autoridad no se mueve

`source-registry.json` sigue siendo la identidad de fábrica, `harness.fuentes.json` la observación y
las decisiones, y `procedencia.py` los derivados. El archivo nuevo,
`.claude/runtime/knowledge-refresh.json`, es **agenda**: cuándo se intentó, cuándo salió bien,
cuándo vence, con qué disparador y con qué error. Su lista `sources` es un resumen que se
**reconstruye** de `harness.fuentes.json` en cada escritura, y la bienvenida no la lee: si los dos
difieren, gana el canónico sin que nadie tenga que decidirlo.

### Un solo camino de observación

`dev-harness.py fuentes` y el refresco automático terminan en la misma función,
`auto_refresh.resolver_y_escribir`, que es `frescura.documento` + `frescura.escribir`. La
observación es `fuentes.observar` / `fuentes.observar_archivos`, sin copia. No hay
`auto_fuentes.py`: dos resolvedores con reglas parecidas son el día en que dan estados distintos
con la misma evidencia.

### El canal es el último que funcionó

Un refresco automático no busca una Ficha nueva. El canal sale de lo que se pasó a
`fuentes --auto` (`<CLAVE>` o `--archivo <dir>`), o del canal que dejó la última corrida en
`harness.fuentes.json`: `jira:<FICHA>` se relee por clave de Ficha, `archivo:<dir>` se vuelve a
leer del directorio. La compuerta de `plan`, `refute` y `seguridad` usa solo el segundo: la clave de
esa tarea no es un canal. Sin ninguno, el refresco queda `AUTO_REFRESH_CHANNEL_UNAVAILABLE` y no
se inventa uno.

### El permiso es el Registro de Capacidades, no la autenticación

Un canal de Jira pide `jira.issue.read`, `jira.issue.search` y `jira.attachment.read` en
`ENABLED` en `harness.capacidades.json`. Que Jira esté `AVAILABLE` no alcanza: un token que
autentica y no lee adjuntos no puede verificar integridad. Falta una y no se sale a la red. El
refresco no lee el `.env`: el adaptador lo arma la CLI, como para cualquier otro comando.

### Una falla no borra lo que se sabía

Si el canal no contesta, **no se reescribe `harness.fuentes.json`**: el último estado conocido sigue
a la vista, con su fecha. La agenda anota `lastAttemptAt` y el `errorCode`, y conserva
`lastSuccessfulCheckAt` y `nextCheckDueAt`. `fuentes` a mano sin canal sigue haciendo lo de
siempre —escribe `FRESHNESS_UNVERIFIED`—, porque es un pedido explícito de una persona.

### Sin novedades no se reescribe

Un refresco automático que resuelve el mismo documento que ya está —salvo `verified_at`— no
reescribe `harness.fuentes.json`: la hora de la revisión la dice la agenda. Es lo que hace barata
una revisión sin cambios, y lo que mantiene el E-18 de `aceptar-fuentes-en-el-proyecto` («`-Update`
no toca `harness.fuentes.json`») ahora que el `-Update` revisa. `fuentes` a mano escribe siempre.

### Vencido no es desactualizado

`DUE` es de la agenda, no de la fuente: una fuente `CURRENT` con la revisión vencida sigue
`CURRENT`, y la bienvenida lo dice aparte. Vencido no suma una condición pendiente; un refresco que
falló sí (`KNOWLEDGE_REFRESH_UNRESOLVED`), y deja el estado en `PARTIAL`, nunca en `BLOCKED`.

### La compuerta usa la gravedad que ya existe

`ensure_normative_knowledge_fresh` devuelve `allowed`, `blocked` o `unresolved`. `blocked` es una
fuente en `SOURCE_INTEGRITY_ALERT`, `SOURCE_CHANGED_SAME_VERSION` o `VERSION_REGRESSION`: los tres
que la bienvenida ya trata como `BLOCKED`. `allowed` es todo `CURRENT` o `RETIRED`. Lo demás es
`unresolved`. `plan` y `refute --compile` cortan con `blocked` y avisan con `unresolved`.

### Las 24 horas son operativas

`maxAgeHours: 24` es un default de este harness, no un requisito de ES0901 ni de ninguna norma. Un
proyecto lo cambia en la política. Una política ilegible cae a `EVENT_ONLY` con solo el disparador
explícito: ante la duda, menos red, no más.

### Un aviso por novedad

La huella de notificación es un sha256 de id, versión aceptada, versión observada, estado e
identidad del adjunto (id, nombre, tamaño, fecha, sha256) de cada fuente que no está `CURRENT` ni
`RETIRED`. Sin contenido ni credenciales. La bienvenida corta muestra el aviso completo una vez por
huella, y la anota en `harness.installation.json` al mostrarlo.

### La bienvenida copia la identidad observada, y sigue sin resolver

E-09 de `51_bienvenida.py` le prohibía a `bienvenida.py` nombrar `observed_version`,
`registry_version`, `observed_sha256` y `attachmentId`. Mostrar la versión observada y armar la
huella exigen leerlos. Se acota E-09 a lo que protegía: la bienvenida no importa `frescura`, no lee
`registry_sha256` ni `evidence` y no compara versiones. Copia lo que `frescura` escribió; no lo
decide.

### La instalación deja la agenda en `.claude/runtime/`

E-26 de `54-context-bar-instalador.ps1` pedía que no existiera `.claude/runtime/` después de
instalar, para probar que la prueba de la Context Bar no deja un libro. Ahora la instalación anota
ahí su intento de revisión. Se acota E-26 a lo que protegía: no hay `runtime/accounting/`, y en
`runtime/` no hay nada salvo `knowledge-refresh.json`.

### El validador aprende `minimum`

El schema de la política provisto usa `minimum`. El intérprete de subconjunto no lo leía, y la
regla de la casa es ampliar el validador, no aflojar el schema.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/knowledge-refresh-policy.schema.json` | El contrato de la política, tal cual se entregó |
| `comun/schemas/knowledge-refresh-state.schema.json` | El contrato de la agenda, tal cual se entregó |
| `harnesses/desarrollo/reglas/knowledge-refresh-policy.json` | La política por defecto: `EVENT_AND_TTL`, 24 h, sin red en SessionStart |
| `harnesses/desarrollo/bin/orquestacion/auto_refresh.py` | Política, vencimiento, capacidades, refresco, agenda atómica, compuerta |
| `harnesses/desarrollo/bin/dev-harness.py` | `fuentes --auto [--disparador X]`, `fuentes --si-vence`, la compuerta en `plan` y `refute --compile`, el refresco en `seguridad`, la agenda en `harness --verbose` |
| `comun/hooks/lib/bienvenida.py` | Versión aceptada y observada, la agenda, la huella y el aviso único |
| `comun/bin/contexto-armar.py` | `minimum` en el intérprete de subconjunto |
| `install.ps1` | `fuentes --auto --disparador INSTALL` o `HARNESS_UPDATE`, que nunca voltea la instalación |
| `tests/casos/61_conocimiento_auto_refresco.py` | Los escenarios de abajo |

## Escenarios verificables

Cada escenario lleva entre paréntesis su id del paquete entregado (`KRF-nnn`).

### Qué no cambia de lugar

- **E-01** — (KRF-001) No hay un agent nuevo: `comun/agents/` y `harnesses/*/agents/` tienen los
  mismos archivos que en 0.26.0. · rojo visto: no consta
- **E-02** — (KRF-002) No hay una skill nueva: `*/skills/` tiene las mismas carpetas que en 0.26.0.
  · rojo visto: no consta
- **E-03** — (KRF-003) `auto_refresh.py` no define observación propia: importa `fuentes` y no
  compara versiones, no hashea ni reconoce adjuntos (no llama a `re`, `hashlib`, `sha256_de`,
  `comparar`). · rojo visto: no consta
- **E-04** — (KRF-004) El estado de cada fuente sale de `frescura.documento`: el documento que
  escribe el refresco es igual, campo por campo salvo `verified_at`, al que arma `frescura.documento`
  con la misma evidencia. · rojo visto: no consta
- **E-05** — (KRF-005) Un refresco con una versión nueva observada no cambia un byte de
  `source-registry.json`. · rojo visto: no consta
- **E-06** — (KRF-006) Si la lista `sources` de la agenda contradice a `harness.fuentes.json`, el
  refresco siguiente la reconstruye desde el canónico, y la bienvenida muestra el estado del
  canónico. · rojo visto: no consta

### Vencimiento

- **E-07** — (KRF-007) Con `EVENT_AND_TTL` y sin `lastSuccessfulCheckAt`, está vencido.
  · rojo visto: no consta
- **E-08** — (KRF-008) Un segundo antes de `nextCheckDueAt`, no está vencido. · rojo visto: no consta
- **E-09** — (KRF-009) En `nextCheckDueAt` exacto, y después, está vencido. · rojo visto: si
- **E-10** — (KRF-010) Con `EVENT_ONLY` nunca vence por tiempo, ni sin revisión previa; un
  disparador de evento igual refresca. · rojo visto: no consta
- **E-11** — (KRF-011) Una política ilegible, sin un campo obligatorio, con un `mode` fuera del
  enum o con `maxAgeHours: 0` devuelve `AUTO_REFRESH_POLICY_INVALID` y cae a `EVENT_ONLY` con solo
  `explicitSources`. · rojo visto: si
- **E-12** — (KRF-012) La política instalada trae `sessionStartNetwork: false`, `EVENT_AND_TTL` y 24
  horas, y valida contra su schema. · rojo visto: no consta

### Disparadores

- **E-13** — (KRF-013) `INSTALL` con el disparador habilitado refresca aunque no esté vencido.
  · rojo visto: no consta
- **E-14** — (KRF-014) `HARNESS_UPDATE` igual. · rojo visto: no consta
- **E-15** — (KRF-015) `EXPLICIT_SOURCES_COMMAND` refresca siempre que esté habilitado, y
  `fuentes` a mano deja la agenda con ese disparador. · rojo visto: si
- **E-16** — (KRF-016) `PRE_KNOWLEDGE_PROMOTION` refresca aunque no esté vencido.
  · rojo visto: no consta
- **E-17** — (KRF-017) `PRE_NORMATIVE_OPERATION_IF_STALE` refresca si está vencido, y si no, no sale
  al canal y devuelve `AUTO_REFRESH_NOT_DUE`. `plan` con la agenda vencida y un canal local refresca
  antes de armar el plan. · rojo visto: si
- **E-18** — (KRF-018) `session-start.py` y `bienvenida.py` no importan `auto_refresh`, `http`,
  `urllib`, `socket` ni el adaptador de Jira; un SessionStart con la agenda vencida no cambia
  `harness.fuentes.json`. · rojo visto: no consta

### Capacidades

- **E-19** — (KRF-019) Con un canal `jira:` y una de las tres capacidades en `DISABLED`, el refresco
  devuelve `AUTO_REFRESH_BLOCKED_CAPABILITY` y el observador no se llama. · rojo visto: si
- **E-20** — (KRF-020) Ese bloqueo conserva `lastSuccessfulCheckAt`, `nextCheckDueAt` y
  `harness.fuentes.json` byte por byte, y anota `lastAttemptAt`. · rojo visto: si
- **E-21** — (KRF-021) Jira `AVAILABLE` con `jira.attachment.read` en `DISABLED` sigue bloqueado.
  · rojo visto: no consta
- **E-22** — (KRF-022) Con las tres en `ENABLED`, el refresco siguiente sale al canal y limpia el
  `errorCode`. · rojo visto: no consta

### Primero la metadata

- **E-23** — (KRF-023) Con la metadata del adjunto igual a la anterior y el hash ya observado, un
  refresco por Jira no baja ningún documento. · rojo visto: no consta
- **E-24** — (KRF-024) Con una versión posterior en el nombre del adjunto, la fuente queda
  `UPDATE_AVAILABLE` sin bajar el documento. · rojo visto: no consta
- **E-25** — (KRF-025) Después de ese refresco, la versión aceptada sigue siendo la anterior en el
  registro, en las decisiones y en la agenda. · rojo visto: no consta
- **E-26** — (KRF-026) La agenda guarda `acceptedVersion` y `observedVersion` por separado.
  · rojo visto: no consta
- **E-27** — (KRF-027) Misma versión con otro `attachmentId` baja y hashea el documento una vez.
  · rojo visto: no consta
- **E-28** — (KRF-028) Misma versión con otro hash queda `SOURCE_INTEGRITY_ALERT`, nunca `CURRENT`.
  · rojo visto: no consta
- **E-29** — (KRF-029) Dos refrescos seguidos sin cambios dejan los mismos estados y no bajan nada
  la segunda vez. · rojo visto: si
- **E-30** — (KRF-030) La misma evidencia da los mismos estados en dos proyectos distintos.
  · rojo visto: no consta

### Decisión humana

- **E-31** — (KRF-031) `auto_refresh.py` no llama a `aceptable`, `decision_de_aceptacion` ni
  `_aceptar`, y un refresco con `UPDATE_AVAILABLE` deja `decisions` igual. · rojo visto: no consta
- **E-32** — (KRF-032) Ningún refresco escribe `source-registry.json` (sale de E-05 y del código:
  `auto_refresh.py` no abre el registro para escribir). · rojo visto: no consta
- **E-33** — (KRF-033) Una decisión `POSTPONE` sobre la identidad observada se conserva y la fuente
  sigue `ACKNOWLEDGED_PENDING` después del refresco. · rojo visto: no consta
- **E-34** — (KRF-034) Una decisión `APPLY` existente se conserva con su `by` y su `at`, y el
  refresco no crea ninguna. · rojo visto: no consta
- **E-35** — (KRF-035) El observador de Jira solo hace GET: el transporte de prueba ve cero pedidos
  que no sean de lectura, y `auto_refresh.py` no llama a nada que escriba en Jira.
  · rojo visto: no consta

### Promoción

- **E-36** — (KRF-036) Con ES0901 aceptada en una versión que el extracto no declara, el refresco
  deja `KNOWLEDGE_PROMOTION_INCOMPLETE`, no `CURRENT`. · rojo visto: no consta
- **E-37** — (KRF-037) Un refresco no cambia ningún archivo de `harnesses/desarrollo/reglas/`
  (matrices incluidas). · rojo visto: no consta
- **E-38** — (KRF-038) Ni de `harnesses/desarrollo/policies/` ni de ninguna carpeta de policies.
  · rojo visto: no consta
- **E-39** — (KRF-039) Ni de `comun/checks/` ni de `*/controles/checks/`. · rojo visto: no consta
- **E-40** — (KRF-040) Ni de `*/agents/`, `*/skills/` ni de las reviews. · rojo visto: no consta

### La compuerta normativa

- **E-41** — (KRF-041) Con todas las fuentes `CURRENT` o `RETIRED` la compuerta devuelve `allowed`.
  · rojo visto: no consta
- **E-42** — (KRF-042) Con una en `SOURCE_INTEGRITY_ALERT`, `SOURCE_CHANGED_SAME_VERSION` o
  `VERSION_REGRESSION` devuelve `blocked`, y `plan` sale con código 2 sin escribir el plan.
  · rojo visto: si
- **E-43** — (KRF-043) Con la agenda vencida y el refresco fallido, la compuerta no devuelve
  `allowed` aunque el último estado conocido sea `CURRENT`: devuelve `unresolved` con el
  `errorCode`. · rojo visto: no consta
- **E-44** — (KRF-044) `contexto`, `estado` y `harness` no llaman a la compuerta; `plan` con la
  compuerta en `unresolved` arma el plan y lo avisa. · rojo visto: no consta
- **E-45** — (KRF-045) Un refresco fallido deja la versión aceptada y el estado de cada fuente como
  estaban en `harness.fuentes.json`. · rojo visto: si

### Bienvenida

- **E-46** — (KRF-046) La bienvenida completa muestra cada fuente con su versión aceptada
  (`acceptance.version`, o la del registro). · rojo visto: no consta
- **E-47** — (KRF-047) Con una versión observada distinta, la línea dice
  `ES0901 6.3    ACTUALIZACIÓN DISPONIBLE → 6.4`. · rojo visto: si
- **E-48** — (KRF-048) La versión observada no aparece nunca a la izquierda ni junto a `ACTUAL`.
  · rojo visto: si
- **E-49** — (KRF-049) Con la agenda vencida la bienvenida lo dice, sin decir que se verificó, y el
  estado de las fuentes no cambia. · rojo visto: no consta
- **E-50** — (KRF-050) `FRESHNESS_UNVERIFIED` se ve como `VIGENCIA SIN VERIFICAR`, y un refresco
  fallido como pendiente `KNOWLEDGE_REFRESH_UNRESOLVED` con su código. · rojo visto: no consta
- **E-51** — (KRF-051) La misma novedad avisa completa en una sesión y no en la siguiente.
  · rojo visto: si
- **E-52** — (KRF-052) Otra versión observada, u otro adjunto, cambia la huella y vuelve a avisar.
  · rojo visto: no consta

### Secretos

- **E-53** — (KRF-053) La agenda no contiene el token de la prueba. · rojo visto: no consta
- **E-54** — (KRF-054) Ni `Authorization`, ni `Basic `, ni la credencial codificada.
  · rojo visto: no consta
- **E-55** — (KRF-055) Ni el cuerpo crudo de la respuesta de Jira: solo las claves del schema.
  · rojo visto: no consta
- **E-56** — (KRF-056) `auto_refresh.py` no menciona `.env`, `AlmacenSecretos` ni `entorno`.
  · rojo visto: no consta
- **E-57** — (KRF-057) El refresco por Jira usa el adaptador que arma `dev-harness.armar` y el
  registro de `harness.capacidades.json`. · rojo visto: no consta
- **E-58** — (KRF-058) `pre-tool-use.py`, `lib/secretos.py` y `permisos-por-capacidad.json` quedan
  byte por byte como en 0.26.0. · rojo visto: no consta

### Fallas y escritura

- **E-59** — (KRF-059) Un timeout del canal deja `AUTO_REFRESH_TIMEOUT` y `state: UNRESOLVED`.
  · rojo visto: no consta
- **E-60** — (KRF-060) Una falla no mueve `lastSuccessfulCheckAt`. · rojo visto: si
- **E-61** — (KRF-061) Un refresco bien lo mueve a la hora del refresco. · rojo visto: no consta
- **E-62** — (KRF-062) `nextCheckDueAt` es `lastSuccessfulCheckAt` más `maxAgeHours`, y `null` en
  `EVENT_ONLY`. · rojo visto: no consta
- **E-63** — (KRF-063) Una agenda rota se informa `AUTO_REFRESH_STATE_UNREADABLE`, cuenta como nunca
  revisada, y el refresco siguiente la reescribe válida. · rojo visto: no consta
- **E-64** — (KRF-064) Ocho escrituras concurrentes dejan un JSON que valida, y ningún temporal.
  · rojo visto: si

### CLI e instalador

- **E-65** — (KRF-065) `fuentes --archivo <dir>` y `fuentes` sin canal hacen lo mismo que en 0.26.0.
  · rojo visto: no consta
- **E-66** — (KRF-066) `fuentes --archivo <dir>` y `fuentes --auto` sobre el mismo directorio dan los
  mismos estados. · rojo visto: no consta
- **E-67** — (KRF-067) `harness --verbose` muestra modo, última revisión, próxima, disparador y
  error de la agenda, y las versiones aceptada y observada, sin un valor del `.env`.
  · rojo visto: no consta
- **E-68** — (KRF-068) Instalar sin red y sin canal termina bien, y dice que el conocimiento queda
  pendiente. · rojo visto: no consta
- **E-69** — (KRF-069) `fuentes --auto --disparador HARNESS_UPDATE` con una versión nueva no acepta
  nada. · rojo visto: no consta
- **E-70** — (KRF-070) Los tests de `45_conocimiento_fuentes.py` y `57_aceptar_fuentes.py` siguen en
  verde. · rojo visto: no consta
- **E-71** — (KRF-071) Los de `51_bienvenida.py` siguen en verde. · rojo visto: no consta
- **E-72** — (KRF-072) `.\tests\Invoke-Tests.ps1` sale 0. · rojo visto: no consta

## Cómo se verifica

Todo por la suite: `tests/casos/61_conocimiento_auto_refresco.py` para E-01 a E-69 salvo E-68, que
instala de verdad y vive en `61-auto-refresco-instalador.ps1`. E-70 a E-72 son la suite entera.
Ningún escenario tiene por sujeto una corrida de un modelo: no hay `lectura`.

## Riesgos conocidos

- **El canal recordado puede quedar viejo.** Si la Ficha de un proyecto cambia de clave, el refresco
  sigue leyendo la anterior hasta que alguien corra `fuentes <CLAVE>`. Se ve: la agenda dice el
  canal.
- **La hora es local y sin zona**, como el resto del harness. Un cambio de horario corre una hora el
  vencimiento; con 24 h de margen no cambia nada que importe.
- **`plan` puede tardar lo que tarda Jira** cuando la agenda vence. Es el precio de no mirarlo en
  SessionStart, y está acotado por `timeoutIntegraciones`.
