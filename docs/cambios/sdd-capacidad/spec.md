# SDD como método de los proyectos instalados

**Estado:** especificado · **Fecha:** 2026-08-12

Esta spec está escrita en el formato que ella misma introduce. Es a propósito: el primer uso
del formato es el cambio que lo crea, y si el formato no sirve conviene enterarse acá.

## Qué problema resuelve

Hoy el harness sabe **qué** reglas rigen —secretos, zonas del `CLAUDE.md`, formato de historia—
pero no sabe **cómo se trabaja**. Un agente puede escribir cuatrocientas líneas sin que nadie
haya escrito antes qué tenían que cumplir, y sin que nadie distinto de quien las escribió
compruebe después que las cumplen.

El método que se adopta es SDD: primero se escribe qué se va a construir y cómo se prueba que
cumple, después se construye, después salen los tests de esa spec, y al final alguien distinto
verifica contra ella.

**TDD queda adentro, no afuera.** Los tests se escriben con el código ya armado, pero los
escenarios que prueban ya estaban en la spec. La deformación de "escribir tests al final" viene
de derivarlos del código que tenés adelante; derivándolos de una spec que es anterior al
código, esa deformación no aparece.

## Qué queda afuera

- **Fases de diseño y tareas.** Pegasus tiene ocho fases; acá hay dos artefactos. Con
  granularidad decidida por la persona, `design.md` y `tasks.md` son papeles que nadie va a
  llenar, y un papel que nadie llena desprestigia a los que sí.
- **Cualquier bloqueo.** Ninguna compuerta de este ciclo frena una herramienta. Los secretos
  siguen siendo lo único que bloquea en todo el harness.
- **Disparador automático.** El harness no decide que algo es un cambio. Lo decide la persona.
- **Este repositorio.** SDD rige para los proyectos que instalan el harness. Que `gcba-harness`
  lo adopte para sí mismo es otra decisión, y se toma después de haberlo visto funcionar.
- **Integración con el gestor de tickets.** El nombre del cambio es libre. Que sea la key de un
  ticket es una convención de proyecto, no una regla del harness.

## Las decisiones, y por qué

### Dos artefactos, no cuatro

```
docs/cambios/<nombre>/
  spec.md           que se construye, escenarios verificables, que queda afuera
  verificacion.md   el veredicto del refutador
```

Van **en el repo**, versionados y diffeables, al lado de `docs/conocimiento/`. Una spec que vive
en `.claude/` se borra en el próximo `-Update`, y una spec que se puede perder no es una fuente.

Build y test no producen artefactos nuevos: el código va a git y los tests van donde el proyecto
ponga sus tests.

### La fase se deriva, no se declara

Un estado declarado en un archivo se desactualiza y a partir de ahí miente. Uno derivado de lo
que existe no puede mentir.

```
no hay spec.md                                  -> SPEC
hay spec.md, con escenarios sin test            -> EN CURSO
todos los escenarios con test, sin verificacion -> VERIFY
verificacion.md sin contradicho ni sin-sustento -> CERRADO
verificacion.md con alguno de los dos           -> EN CURSO
```

📌 **Un `verificacion.md` que existe no cierra nada.** Cierra uno que no tiene ningún escenario
`contradicho` ni `sin-sustento`. Un veredicto con hallazgos devuelve el cambio a `EN CURSO`, que
es donde se resuelven: o el código estaba mal, o faltaba un test, o el escenario no era
verificable como estaba escrito. Tomar la existencia del archivo como cierre convertiría al
verificador en un trámite.

📌 **El estado se llama `EN CURSO` y no `TEST` porque el harness nombra lo que ve.** El método
tiene cuatro pasos —especificar, construir, testear, verificar— pero entre la spec y los tests
en verde el harness no distingue si alguien está construyendo o ya está escribiendo tests. Con
git podría aproximarlo; sin git no, y el harness soporta proyectos sin versionar. Antes que
comportarse distinto según el proyecto, o que reportar `TEST` a alguien que todavía no escribió
una línea de código, se nombra el tramo entero por lo que es. Construir sigue siendo una fase
del método; lo que no existe es un check que pretenda ver la costura adentro.

### El cambio activo es estado de máquina

`.claude/cambio-activo` — una línea con el nombre del cambio.

Va ahí y no en el repo porque **en qué cambio estoy trabajando yo ahora no es un dato del
proyecto**: dos personas en el mismo repositorio están en cambios distintos, y versionarlo
produciría un conflicto por cada `git pull`. Si un `-Update` lo borra, se vuelve a apuntar y no
se perdió nada — que es exactamente lo que la invariante de `.claude/` promete.

### Un escenario se rastrea por id

Cada escenario de la spec lleva un identificador correlativo (`E-01`, `E-02`) y **el test que lo
cubre lo nombra en su título o en un comentario**. El check busca el id.

Es mecánico, funciona en cualquier lenguaje sin saber nada del runner, y deja la trazabilidad
visible en las dos direcciones: desde la spec se ve qué escenario no tiene test, y desde el test
se ve qué escenario justifica que exista.

🔴 **El check mide nombres, no cobertura, y su mensaje no puede decir otra cosa.** Un test
llamado `E-03` prueba que coincide una cadena. Alguien puede escribir ese id arriba de un test
vacío y el check se pondría verde — y si además dijera "todos los escenarios cubiertos", habría
tapado un hueco con una afirmación falsa, que es peor que dejarlo a la vista.

Por eso el check afirma únicamente lo que puede sostener:

| | |
|---|---|
| ✅ | `E-03 no aparece nombrado en ningún test` |
| ❌ | `E-03 no está cubierto` |
| ❌ | `todos los escenarios cubiertos` |

La cobertura real la establece el refutador, que corre los tests y contrasta cada escenario
contra su resultado. El id es un aviso temprano y barato; la compuerta está después.

### Cada escenario declara si se vio su test en rojo

Un test escrito con el código en verde adelante puede pasar por la razón equivocada. Por eso la
fase de test cierra rompiendo el código a propósito y confirmando que el test falla — y cada
escenario de la spec lleva la marca de si eso se hizo:

```
- **E-03** — Con spec.md que tiene un escenario sin test, la fase es EN CURSO.
  · rojo visto: si
```

Valores: `si` · `no consta`. No hay un tercero: `no` y `no consta` son lo mismo a los efectos de
quien lee, y ofrecer los tres invita a elegir el que queda mejor.

🔴 **Es una declaración, no una comprobación, y el harness no finge lo contrario.** Ningún check
puede saber si alguien rompió el código. Lo único que se logra es que la ausencia sea visible: el
refutador reporta la marca al lado de cada veredicto, y un `sostenido` con `no consta` sigue
siendo `sostenido` — pero quien lo lee sabe cuánto vale. Ver
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md).

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/skills/cambio-especificar/SKILL.md` | Cómo se escribe una spec: escenarios verificables con id, qué queda afuera, y la ley de no inventar aplicada a lo que nadie definió. **Cierra explicando que quien especifica no es quien verifica, y qué hacer con cada veredicto cuando vuelve** — igual que `hu-redactor`. No hay una skill aparte para leer un veredicto de tres valores |
| `comun/agents/cambio-refutador.md` | El verificador. Corre los tests y contrasta cada escenario contra su resultado real |
| `comun/checks/cambio-fase.ps1` | Deriva la fase y emite los avisos |
| `comun/hooks/session-start.ps1` | Una línea más cuando hay cambio activo |
| `comun/claude-md/bloque-comun.md` | Las tres o cuatro líneas del método que sí se necesitan cada turno |
| `docs/adr/0006-sdd-como-metodo.md` | La decisión, y por qué supera lo escrito en `terceros/gentle-ai/ORIGEN.md` |
| `docs/sdd.md` | La documentación de la capacidad, al lado de `memoria.md` |

## Escenarios verificables

### Derivación de fase

- **E-01** — Sin `.claude/cambio-activo`, el check no emite nada y sale con código 0.
- **E-02** — Con cambio activo y sin `spec.md`, la fase derivada es `SPEC`.
- **E-03** — Con `spec.md` que tiene un escenario sin test que lo nombre, la fase es `EN CURSO`.
- **E-04** — Con todos los escenarios nombrados por algún test y sin `verificacion.md`, la fase
  es `VERIFY`.
- **E-05** — Con `verificacion.md` presente, la fase es `CERRADO`.
- **E-06** — Si `cambio-activo` apunta a una carpeta que no existe, el check lo dice y sale con
  código 0. No explota y no inventa una fase.
- **E-07** — Una `spec.md` sin ningún escenario con id se reporta como tal, y no como
  "todos los escenarios cubiertos".

### Avisos

📌 **"Escribir código" acá quiere decir escribir cualquier archivo que no sea la spec del cambio
activo.** No se intenta distinguir código de documentación: en un repositorio de relevamiento
todo es markdown, y una regla que dependa de la extensión no sirve para la mitad de los
proyectos. Lo que se mide es si alguien está produciendo algo mientras el cambio que declaró
abierto todavía no dice qué tenía que cumplir.

- **E-08** — Se escribe fuera de `docs/cambios/<activo>/` con un cambio activo que no tiene
  `spec.md`: el check avisa.
- **E-09** — Se escribe sin cambio activo: el check no emite nada.
- **E-09b** — Se escribe la propia `spec.md` del cambio activo: el check no emite nada, ni
  siquiera cuando todavía no existía. Especificar no es construir.
- **E-10** — Un escenario de la spec sin test que lo nombre: el check avisa e identifica cuál.
- **E-10b** — El aviso afirma que el escenario **no aparece nombrado en ningún test**, nunca que
  no está cubierto. Y cuando todos los escenarios aparecen nombrados, el check no declara
  cobertura: eso lo establece el refutador corriendo los tests.
- **E-11** — Todo aviso de este ciclo sale con código 0 y por `additionalContext`. Ninguno
  emite `permissionDecision deny`.
- **E-12** — El aviso dice qué hacer, no solo qué falta.

### SessionStart

- **E-13** — Con cambio activo, el saludo suma una línea con el nombre del cambio y su fase.
- **E-14** — Sin cambio activo, el saludo no cambia: no se gasta ninguna de sus doce líneas.
- **E-15** — Con `cambio-activo` roto o apuntando a la nada, el saludo lo reporta y el hook sale
  con código 0.

### El refutador

- **E-16** — Un escenario sin test que lo cubra recibe `sin-sustento`, nunca `sostenido`.
- **E-17** — Un escenario cuyo test corrió y falló recibe `contradicho`.
- **E-18** — Un escenario cuyo test corrió y pasó recibe `sostenido`, citando el comando
  ejecutado y su resultado.
- **E-19** — Si no puede ejecutar los tests, lo dice y frena. No deduce un veredicto de leer el
  código.
- **E-20** — El agente declara `tools:` sin `Write` ni `Edit`. Corre, no modifica.
- **E-20b** — El veredicto de cada escenario incluye su marca `rojo visto`, tomada de la spec.
  Un escenario sin la marca se reporta como `no consta`, nunca se omite la columna.
- **E-20c** — Un `sostenido` con `rojo visto: no consta` **sigue siendo `sostenido`**. La marca
  informa, no degrada el veredicto: el refutador no inventa una cuarta categoría.

### Instalación

- **E-21** — Los artefactos nuevos viajan con `comun`, o sea que se instalan siempre.
- **E-22** — `-Uninstall` saca los artefactos del harness y **no toca `docs/cambios/`**: adentro
  está el trabajo de alguien.

## Cómo se verifica

Los escenarios E-01 a E-15 y E-21 a E-22 son PowerShell y van por rojo→verde en
`tests/casos/`, con payloads reales de hook como el resto de la suite.

E-16 a E-20 son el comportamiento de un agente. Se verifican leyendo su definición para E-20, y
con un caso armado a mano para los otros cuatro: una spec de juguete con un escenario cubierto,
uno fallando y uno sin test, y se comprueba que los tres veredictos salgan como corresponde.

## Riesgos conocidos

- **Nadie abre un cambio nunca.** Es el precio de que lo decida la persona, y es aceptado. El
  harness recuerda, no obliga. Si a los tres meses no hay ninguna carpeta en `docs/cambios/`, la
  respuesta no es empezar a bloquear: es que el ciclo no servía y hay que revisarlo.
- **El id del escenario se pega mal.** Un test que nombra `E-03` cuando cubre el `E-04` deja el
  hueco tapado. El refutador lo detecta porque contrasta contra el escenario, no contra el id.
- **Una spec escrita para pasar el check.** Escenarios vagos que cualquier test satisface. No
  hay defensa mecánica; la defensa es la skill de especificar y el refutador.
