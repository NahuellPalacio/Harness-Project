# fabrica

## Qué es

Cómo se trabaja **en este repo**, que no es lo mismo que lo que el repo produce. Este proyecto
es la fábrica del harness: acá se construye lo que después se instala en otros proyectos, y
esta capa gobierna a quien lo construye.

Son los agentes y skills que rigen las sesiones de este repositorio, el `CLAUDE.md` que se
carga en cada una, la configuración del repo y el trabajo que queda abierto.

Nada de acá se instala en ningún proyecto: el instalador solo copia desde `comun/` y
`harnesses/<id>/`.

## Qué expone

- **`CLAUDE.md`** — el contrato de cada sesión: el método, la compuerta de la suite, quién es
  dueño de qué, las skills de la fábrica y la regla de idioma (español rioplatense para todo lo
  que se distribuye; inglés adentro de `.claude/`, los pendientes, los nombres de archivo y el
  código). Trae además el aviso de qué hacer si la suite se corta a la mitad.
- **Cinco agentes con dueño declarado** — el ingeniero de hooks (dueño de los hooks y los
  checks), el de backend (el instalador, la suite, los manifiestos y el lockfile), el staff
  engineer (rendimiento, tamaño y simplicidad, con el comportamiento congelado), el refutador
  de specs (dicta veredictos, corre los tests y no escribe nada) y el auditor de presupuesto
  (mide lo que el harness cuesta en cada turno y no bloquea nunca).
- **Cinco skills** — escribir una spec, registrar un veredicto, cerrar una versión, anotar un
  pendiente, y la de respuestas concisas, que rige cada respuesta de cada sesión.
- **`Pendientes/`** — dos archivos, escritos en inglés, que son la fuente de trabajo de esos
  agentes. Uno lleva los defectos y arreglos, ordenados por riesgo por costo y no por tema; el
  otro las ideas, que son propuestas que pueden no construirse nunca. Un ítem que cierra sale
  de ahí y aterriza en la nota de su versión.
- **`.gitattributes`** — los saltos de línea fijados a propósito: CRLF para los scripts de
  Windows, LF obligatorio para los `.sh` incluso escritos desde Windows, LF para el contenido.
  Sin esto manda la configuración de cada máquina y un `.sh` con CRLF falla con un error que no
  nombra su causa.
- **`.gitignore`** — el bloque de secretos, el directorio de fuentes de normativa (el repo es
  público) y las salidas de prueba.

## De qué depende

- La suite en verde como condición de cerrar cualquier cosa.
- Los artefactos de `docs/cambios/`, que son lo que producen las skills de spec y veredicto.
- La separación de dueños: quien construye no verifica, y el refutador dicta contra la spec
  pero no escribe su propio veredicto.
- El costo de contexto: los agentes y skills de acá se cargan en cada turno de cada sesión de
  este repo, y el auditor de presupuesto existe justamente porque nada más lo limita.

## Dónde está

- `CLAUDE.md` — en la raíz.
- `.claude/agents/harness-hook-engineer.md`, `harness-backend-engineer.md`,
  `harness-staff-engineer.md`, `harness-spec-refuter.md`, `harness-budget-auditor.md`
- `.claude/skills/write-a-spec/`, `write-a-verdict/`, `close-a-version/`, `note-a-pending/`,
  `concise-replies/` — un `SKILL.md` en cada uno.
- `Pendientes/Fix-Harness/PENDIENTES-FH.md`, `Pendientes/Ideas-Harness/PENDIENTES-I.md`
- `.gitattributes`, `.gitignore`
