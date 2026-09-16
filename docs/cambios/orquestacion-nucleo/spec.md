# Bloque 3 — El núcleo de orquestación: de un `TaskContext` a un `OrchestrationPlan`

**Estado:** especificado · **Fecha:** 15-09-2026

## Qué problema resuelve

0.17.0 dejó al harness entendiendo una tarea. No sabe qué hacer con ella. Hoy, con el `TaskContext`
escrito, la única forma de seguir es que alguien lea el documento entero y decida solo: qué hay que
tocar, quién debería hacerlo, con qué capacidades, en qué orden y con cuánto modelo. Cada decisión
de esas se toma una vez por tarea, sin dejar rastro, y la siguiente persona la vuelve a tomar.

Este cambio construye el núcleo que convierte contexto en plan: un contrato `OrchestrationPlan`
con sus unidades de trabajo, la resolución de capacidades contra el registro del Bloque 1, el ruteo
de modelo por perfiles, la política de consumo con su compuerta humana, y las reglas de ES0901 §7.1
como dato consultable.

El límite es la palabra **plan**. Nada de este cambio ejecuta una unidad de trabajo, delega a un
especialista ni modifica un archivo del proyecto.

## Qué queda afuera

- **La ejecución.** Ningún especialista corre acá. `READY_FOR_EXECUTION` es un estado del documento,
  no una invocación. La separación es la del pedido: orquestar decide qué, quién, con qué y en qué
  orden; ejecutar modifica.
- **Los siete agentes especialistas como archivos.** `dev-architecture`, `dev-backend`,
  `dev-frontend`, `dev-integration`, `dev-devops`, `dev-quality` y `dev-security` entran como
  **datos del roster**, no como `.md`. El pedido mismo lo dice: la existencia final de cada uno se
  valida contra la matriz normativa, y no se crean agentes porque exista una tecnología. Un agente
  declarado sin su archivo se reporta como hueco, igual que una capacidad faltante.
- **La skill `dev-data`.** Misma razón: se declara y se reporta como hueco hasta que la matriz diga
  qué conocimiento tiene que llevar adentro.
- **La matriz normativa clasificada.** Las 26 reglas de §7.1 entran con su id, su texto y su página;
  la clasificación —`owners`, `skills`, `policies`, `checks`— entra **vacía**. Clasificarlas es
  trabajo de criterio que alguien tiene que validar, y una matriz inventada es peor que ninguna: se
  lee igual de autoritativa. La consecuencia se acepta y se declara: V1 cita pocas reglas.
- **`dev-tool-builder` construyendo tools.** El núcleo detecta el hueco de capacidad, lo deriva y
  clasifica la tool pedida como `TEMPORARY`. Quién la escribe y cómo se promueve es otro cambio.
- **Un sistema de presupuesto financiero.** `sessionBudget` es un contador de llamadas premium y un
  tope de reintentos. Nada de costos, tokens ni facturación.
- **Inventar qué modelos existen.** El runtime se declara en configuración y se detecta sólo lo que
  el runtime expone de verdad. Un perfil sin modelo declarado es un hueco, no un default.
- **Reconstruir el `TaskContext`.** Se consume el que escribió el Bloque 2. Si no está, el comando
  no lo arma: dice que corran `contexto` primero.

## Las decisiones, y por qué

### El bloque se parte por quién decide, no por qué hace

```
DETERMINISTA — Python, se testea        JUICIO — el agente, se verifica por lectura
──────────────────────────────────      ──────────────────────────────────────────
el contrato y su validación             qué hay que hacer y por qué
capacidad requerida -> registro -> gap  qué dominios toca la tarea
señales -> tier de modelo               cómo se parte en unidades de trabajo
política de consumo y compuerta         qué señales de complejidad tiene cada una
reglas aplicables                       qué contexto necesita cada especialista
historial y versiones del plan
```

La costura entre las dos mitades es un archivo: el agente escribe una **propuesta** —objetivo,
dominios, unidades, señales— y el núcleo la ingiere, resuelve todo lo mecánico y emite el plan
validado. Sin esa costura, o el ruteo de modelo vive adentro de un prompt y nadie lo puede testear,
o el núcleo tiene que adivinar dominios y deja de ser determinista.

### El roster es dato, y la existencia la dice el disco

`reglas/roster.json` declara qué agentes, skills y checks **debería** haber, con su dominio. Si
existe el archivo correspondiente lo dice el sistema de archivos, no el roster.

Es lo que hace que el hueco no dependa de que alguien mantenga una lista al día: el día que
`dev-backend.md` se escriba, deja de ser hueco sin tocar una línea de datos. Y mientras no exista,
el plan lo dice en vez de prometer un agente que no está.

### El orquestador piensa en capacidades, no en tools

Una unidad de trabajo pide `repository.read`, no `Glob`. La resolución cruza dos fuentes: el
registro de integraciones que escribió el bootstrap y las capacidades locales que declara el roster
—las que da el propio runtime—. Lo que no está en ninguna de las dos es un hueco, y un hueco se
deriva; **nunca se improvisa con una tool parecida**.

Se descartó que el orquestador nombrara tools directamente: ata el plan a un runtime, y el mismo
plan deja de servir el día que la misma capacidad la provea otra cosa.

### Los tiers son perfiles, nunca nombres de modelo

`low_cost`, `standard`, `reasoning`, `premium`. El nombre concreto lo resuelve el runtime, y si no
hay uno declarado para un perfil, eso es un hueco declarado y no un default silencioso. Un plan que
dice `claude-sonnet-4` deja de ser válido en cuanto el proveedor renombra algo, y peor: deja de ser
portable a otro runtime, que es exactamente lo que el pedido pide evitar.

### La escalada nunca es silenciosa, y no salta tiers

De `low_cost` se pasa a `standard`, no a `premium`. Cada escalada deja escrito qué falló, cuántos
intentos hubo y por qué se recomienda el siguiente. **Un tier que se salta es una decisión de
consumo que nadie vio.**

### `premium` no se ejecuta sin una persona, salvo presupuesto previo

`low_cost` y `standard` se autoaprueban. `reasoning` y `premium` se configuran. Lo que la política
marque como aprobable por humano deja el plan en `WAITING_FOR_HUMAN_APPROVAL` con la solicitud
armada —agente, unidad, tier, motivo, consumo esperado y la alternativa más barata— y el comando
termina sin ejecutar nada.

El presupuesto preautorizado se gasta: dos llamadas premium autorizadas son dos, y la tercera
vuelve a preguntar.

📌 **No es la única forma de saltear la pregunta, y decirlo importa.** Poner `premium` en
`autoApprove` también lo hace, sin tocar el contador — `decidir` evalúa `autoApprove` antes que el
presupuesto. Es una configuración deliberada y E-24 la licencia explícitamente; lo que no se puede
es leer "premium siempre se detiene", porque con esa configuración no se detiene. Lo encontró el
refutador y la primera redacción de esta sección lo afirmaba mal.

### El estado del plan se calcula, no se declara

Con huecos de capacidad el plan no puede estar listo. Con una aprobación pendiente tampoco. Dejar
que el estado lo escriba quien arma el plan es dejar que un plan con huecos diga
`READY_FOR_EXECUTION`, y el estado es justamente lo que el bloque siguiente va a mirar para decidir
si arranca.

### Cada unidad lleva su contexto, no el `TaskContext` entero

El aislamiento no es una optimización de tokens: es que lo que está adelante se usa, y una unidad de
devops que tiene adelante las reglas de negocio del proyecto va a opinar sobre ellas. El núcleo arma
el contexto de cada unidad a partir del dominio declarado, lo que no corresponde no viaja, y lo que
no viajó queda declarado en `omitted` — un aislamiento que no se puede auditar no es un aislamiento.

📌 **Esta sección decía otra cosa: "que una unidad de backend no tenga adelante los criterios de
accesibilidad".** No se puede cumplir filtrando por dominio, porque los criterios de aceptación son
una lista plana de la tarea y no traen marca de a qué disciplina pertenece cada uno. Está corregido
acá y en E-29, que es donde se declaró primero.

### El idioma lo decide quién lee

[ADR-0011](../../adr/0011-el-idioma-de-un-archivo-lo-decide-quien-lo-lee.md). El agente nuevo se
escribe en inglés porque lo carga un modelo; todo lo que este cambio le muestre a una persona
—la salida del comando, la solicitud de aprobación, los mensajes de error— va en español.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/orchestration-plan.schema.json` | El contrato `orchestration-plan/1.0`, con `WorkUnit` adentro |
| `bin/orquestacion/plan.py` | Arma, valida, calcula el estado, versiona y guarda el historial |
| `bin/orquestacion/capacidades.py` | Requeridas contra registro y capacidades locales; huecos y derivación |
| `bin/orquestacion/modelo.py` | Señales de complejidad a tier, con su motivo; escalada explícita |
| `bin/orquestacion/consumo.py` | Política, presupuesto y la solicitud de aprobación humana |
| `bin/orquestacion/normativa.py` | Carga las reglas de §7.1 y filtra las aplicables |
| `bin/orquestacion/roster.py` | Agentes, skills y checks declarados; existencia contra el disco |
| `harnesses/desarrollo/reglas/es0901-7.1.json` | Las 26 reglas de §7.1 como dato, sin clasificar |
| `harnesses/desarrollo/reglas/roster.json` | El roster y las capacidades locales del runtime |
| `harnesses/desarrollo/agents/dev-orchestrator.md` | El planificador, en inglés, delgado |
| `install.ps1` | Copia `harnesses/<id>/reglas` a `.claude/harness/reglas/<id>` |
| `dev-harness.py` | Subcomando `plan`, con `--plantilla`, `--propuesta` y `--replanificar` |
| `harnesses/desarrollo/manifest.json` | `modelRouting`, `consumptionPolicy`, `llmRuntime` |
| `docs/orquestacion.md` | Qué decide el núcleo, qué decide el agente y cómo se lee el plan |
| `tests/casos/20_orquestacion.py` | Los escenarios del núcleo |
| `tests/casos/20-orquestacion-instalador.ps1` | Lo que deja el instalador y lo que sobrevive |

## Escenarios verificables

### El contrato del plan

- **E-01** — El plan que se escribe valida contra `orchestration-plan/1.0`, con el mismo validador
  que ya usan `project-context` y `task-context`. · rojo visto: si
- **E-02** — El estado se calcula del contenido: con huecos de capacidad da
  `CAPABILITY_RESOLUTION`, con una aprobación pendiente `WAITING_FOR_HUMAN_APPROVAL`, y sin nada
  pendiente `READY_FOR_EXECUTION`. Con las dos cosas a la vez **gana el hueco**.
  · rojo visto: si

  📌 **La cláusula del empate la agregó la tanda de mutaciones.** Sacarle a `estado_de` la rama de
  los huecos dejaba la suite verde: cada hueco deja además una unidad `BLOCKED`, y la tercera rama
  la atrapaba igual. El único caso que las distingue —una unidad que pide una capacidad que no
  existe **y** además necesita aprobación— no estaba escrito. Se escribió, y con él la decisión
  que el código ya tomaba y nadie había declarado: manda el hueco, porque ninguna aprobación
  arregla una capacidad que falta, y al revés dejaría a una persona firmando algo que después no
  se va a poder hacer igual.
- **E-03** — Una unidad que declara una dependencia inexistente no se escribe: el plan falla con un
  mensaje que nombra la unidad y la dependencia. · rojo visto: si
- **E-04** — Un ciclo de dependencias se rechaza nombrando las unidades del ciclo.
  · rojo visto: si
- **E-05** — El orden de ejecución sale de las dependencias y es determinista: dos corridas sobre
  la misma propuesta dan el mismo orden. · rojo visto: si

### Las capacidades

- **E-06** — Una capacidad que el registro del bootstrap tiene `ENABLED` sale como disponible, y la
  unidad que la pidió queda anotada. · rojo visto: si
- **E-07** — Una capacidad que declara el roster como local del runtime también sale disponible, sin
  pasar por el registro de integraciones. · rojo visto: si
- **E-08** — Una capacidad que no está en ninguna de las dos fuentes sale como faltante y produce un
  hueco que nombra qué unidad la pidió. · rojo visto: si
- **E-09** — Un hueco se deriva a `dev-tool-builder` y la tool pedida se clasifica `TEMPORARY`, nunca
  permanente. · rojo visto: si
- **E-10** — Una capacidad `DISABLED` en el registro es faltante, no disponible: el bootstrap ya
  decidió que esa integración no anda. · rojo visto: si

### El roster

- **E-11** — Un agente declarado en el roster sin su `.md` aparece como hueco, y la unidad asignada
  lo dice en `agentExists`. · rojo visto: si

  📌 **Estuvo contradicho: el hueco lo decía el plan y la unidad no.** La unidad llevaba
  `assignedAgent: "dev-backend"` y ningún campo decía que ese archivo todavía no existe. Importa
  porque un especialista recibe **su unidad suelta**, no el plan entero: el aviso vivía tres
  niveles más arriba de donde se lee. Se agregó `agentExists` a la unidad y al contrato.
- **E-12** — Una skill declarada sin su `SKILL.md` —hoy, `dev-data`— aparece como hueco.
  · rojo visto: si
- **E-13** — Un check declarado que sí existe como archivo no aparece como hueco: la existencia la
  dice el disco, no el roster. · rojo visto: si
- **E-14** — El ruteo por dominio no trae a todos: una propuesta con dominio `backend` no asigna
  `dev-frontend` a ninguna unidad. · rojo visto: si

### El ruteo de modelo

- **E-15** — Una unidad sin ninguna señal de complejidad sale `low_cost`. · rojo visto: si
- **E-16** — Ambigüedad alta más impacto arquitectónico sube el tier por encima de `standard`.
  · rojo visto: si
- **E-17** — El motivo del tier nombra las señales que lo empujaron, no un texto genérico.
  · rojo visto: si
- **E-18** — La escalada sube un tier por vez y deja escrito qué falló, cuántos intentos hubo y cuál
  es el siguiente. · rojo visto: si
- **E-19** — Un perfil sin modelo declarado en el runtime es un hueco declarado, nunca un default
  silencioso. · rojo visto: si

### El consumo y la compuerta humana

- **E-20** — `low_cost` y `standard` se autoaprueban según la política por defecto.
  · rojo visto: si
- **E-21** — Una unidad `premium` sin presupuesto deja el plan en `WAITING_FOR_HUMAN_APPROVAL` y el
  comando termina sin ejecutar nada. · rojo visto: si
- **E-22** — La solicitud de aprobación lleva agente, unidad, tier recomendado, motivo, consumo
  esperado y la alternativa más barata. · rojo visto: si
- **E-23** — Con presupuesto preautorizado se consume sin preguntar hasta el límite; la llamada que
  lo excede vuelve a pedir aprobación. · rojo visto: si
- **E-24** — La política sale de la configuración del proyecto: cambiar qué tiers se autoaprueban
  cambia el resultado sin tocar el código. · rojo visto: si

### La normativa

- **E-25** — Las 26 reglas de §7.1 están como dato, con su id, su texto y su página: G1-G2,
  D1-D8, P1 con sus tres cláusulas, P2-P7, C1-C4 y M1-M3. · rojo visto: si

  📌 **Son 26 y no 22.** El primer conteo salió de un `grep` sobre el extracto y se quedó corto:
  no cuenta las tres cláusulas que ES0901 agrupa bajo `P1` —la prohibición de *vanilla*, la nota de
  Node.js que prohíbe Yarn, y las plataformas de negocio— ni `P7`, porque las cuatro llevan texto
  adentro de la negrita del id. Entran con id propio —`P1`, `P1.node`, `P1.plataformas`, `P7`—
  porque cada una tiene un dueño distinto el día que se clasifiquen: la de Node.js es una policy
  sobre el gestor de paquetes y la de *vanilla* es sobre el framework.

- **E-25b** — El texto de cada regla es el del extracto citable, no una paráfrasis: el dato apunta
  a `normativa/extractos/ES0901.md` y dice lo mismo que él, las 26. · rojo visto: si

  📌 **Estuvo contradicho, y el test era la mitad del problema.** Comprobaba el puntero al
  extracto, la versión y **una** ancla de 37 caracteres sobre G1; el escenario dice "el texto de
  cada regla". El refutador comparó las 26 y encontró dos paráfrasis reales —`P1.plataformas`
  decía "y similares" donde el extracto dice "etc.", y `P1.node` se comía "(Node Package
  Manager)"— y al escribir la comparación completa aparecieron dos omisiones más: `P1` había
  perdido "(por ejemplo, conectores de base de datos usados por un ORM)" y `M3` "(skill
  transfer)". Las cuatro se corrigieron en el dato. El test ahora compara las 26 contra el
  extracto, normalizando comillas: el extracto alterna narración y cita, y exigir un span literal
  sería más estricto que lo que el escenario pide.
- **E-26** — Una regla sin condiciones declaradas nunca se cita como aplicable.
  · rojo visto: si
- **E-27** — Una regla cuya condición coincide con un dominio del plan se cita en
  `applicableStandards` con su id. · rojo visto: si
- **E-28** — El plan declara cuántas reglas quedan sin clasificar, para que la matriz pendiente sea
  visible en cada corrida. · rojo visto: si

### El aislamiento y los secretos

- **E-29** — Cada unidad lleva el contexto de su dominio, declara en `omitted` lo que dejó afuera, y
  **un dominio que nadie declaró no arma plan**. · rojo visto: si

  📌 **Estuvo contradicho por dos cosas, y una era peligrosa.** La chica: el escenario decía "una
  unidad de backend no lleva los criterios de accesibilidad", y eso no se puede cumplir filtrando
  por dominio — los criterios de aceptación son una lista plana de la tarea, sin disciplina
  adentro. Backend necesita las cuatro categorías y su `omitted` sale vacío, con razón.

  La grande: **un dominio fuera de la tabla caía a un default que se llevaba las cuatro
  categorías con `omitted` vacío**, indistinguible de un dominio que tiene derecho a todo.
  Alcanzaba con que el agente escribiera un dominio inventado. Y tres dominios del propio
  `roster.json` —`tooling`, `orchestration`, `refutation`— estaban en ese caso. Ahora tienen su
  fila, y un dominio desconocido levanta con su nombre y la lista de los conocidos.
- **E-30** — Ningún token llega al plan, venga de donde venga: del `TaskContext`, de la propuesta o
  del `--motivo` de una replanificación. · rojo visto: si

  🔴 **Estuvo contradicho y era una fuga de verdad: un PAT escrito en `--motivo` quedaba en claro
  en `.claude/planes/<CLAVE>.json`.** Dos causas, y las dos del mismo error: `_limpiar` recorría
  cuatro campos **por nombre** y `planHistory` no estaba en la lista, y además `replanificar`
  corría **después** de la limpieza, así que el motivo no existía cuando se limpiaba.

  📌 **Es exactamente el error que el Bloque 2 ya había cometido y corregido un bloque antes.**
  Ahí la redacción era campo por campo, se escapaban tres rutas, y la corrección fue recorrer el
  documento entero. Un bloque después, el mismo código se escribió de nuevo con una lista de
  cuatro campos. La lección no era "acordarse de `planHistory`": era que una lista de campos
  obliga a acordarse una vez por campo, para siempre. Ahora `_limpiar` recorre todo menos `meta`,
  y `replanificar` limpia después de escribir el historial.

### La CLI y el instalador

- **E-31** — Sin `TaskContext` para esa clave, `plan` sale con código 2 diciendo que corran
  `contexto` primero, sin escribir nada. · rojo visto: si
- **E-32** — `--plantilla` emite el esqueleto de la propuesta con el resumen de la tarea, las
  capacidades disponibles y el roster, para que el agente sepa qué completar.
  · rojo visto: si
- **E-33** — `--replanificar` sube `planVersion`, guarda el cambio con su motivo y su disparador, y
  conserva las versiones anteriores en el historial. · rojo visto: si
- **E-34** — Con `desarrollo` instalado quedan los módulos de `orquestacion/`, el schema y las reglas
  bajo `.claude/harness/`. · rojo visto: si
- **E-35** — `-Update` y `-Uninstall` no borran `.claude/planes/`. · rojo visto: si

## Cómo se verifica

Los treinta y seis son deterministas. Ninguno tiene por sujeto una corrida de un modelo: el
agente `dev-orchestrator` no se invoca en este cambio, y lo que decide —objetivo, dominios,
unidades, señales— entra a los tests como una propuesta escrita a mano, que es exactamente la
costura que el diseño define. No hay escenario de lectura.

- **E-01 a E-33** corren en `tests/casos/20_orquestacion.py`, sobre proyectos temporales con un
  `TaskContext` y un registro de capacidades escritos por el test.
- **E-34 y E-35** corren en `tests/casos/20-orquestacion-instalador.ps1` sobre proyectos
  descartables.

Ningún test sale a la red ni invoca un modelo.

## Riesgos conocidos

- **El agente `dev-orchestrator` no se prueba acá.** Se escribe su archivo y no lo corre nadie. Que
  produzca una propuesta razonable a partir de un `TaskContext` real es una corrida de un modelo y
  se verifica por lectura, en otro cambio y con ADR-0009 adelante. Lo que este cambio prueba es que
  **lo que se hace con la propuesta** es correcto.
- **Las señales de complejidad las declara el agente, y nadie las audita.** Un agente que declare
  todo `ambiguity: alta` consigue `premium` para cualquier cosa. La compuerta humana es la defensa,
  no el scoring: por eso `premium` se detiene aunque el número diga que corresponde.
- **Las 26 reglas entran sin clasificar y por lo tanto casi no se citan.** Es la decisión, no un
  olvido — pero significa que `applicableStandards` va a salir corto hasta que la matriz exista, y
  alguien puede leer eso como que el estándar no aplica. Por eso el plan declara cuántas quedan sin
  clasificar.
- **Las capacidades locales del roster son una declaración, no una comprobación.** El roster dice
  que el runtime provee `repository.read`; nadie verifica que la sesión tenga habilitada la
  herramienta que la da. Un plan puede quedar listo y toparse con eso recién al ejecutar.
- **El orden topológico es determinista pero no es un cronograma.** Dice qué puede empezar después
  de qué, no qué corre en paralelo ni cuánto tarda.
