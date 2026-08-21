# harnesses/analisis

## Qué es

El harness para el trabajo funcional: relevar, escribir historias de usuario, leer maquetas y
normativa. Se instala en los proyectos donde todavía no hay código, o donde hay gente que
escribe historias y no las implementa.

El corte entre harness es por **tipo de trabajo**, no por proyecto: un analista funcional no
necesita cargar las reglas de diseño de APIs. Un proyecto puede tener los dos a la vez.

Su prefijo de namespace es `hu`, y eso hace estructuralmente imposible que dos harness aporten
dos cosas con el mismo nombre.

## Qué expone

- **`manifest.json`** — su identidad: id, prefijo, qué aporta y los defaults que van al
  `harness.config.json` del proyecto (ruta de las historias, de las maquetas, de las
  definiciones pendientes, y el gestor de tickets, que arranca en solo lectura).
- **`claude-md/bloque.md`** — las reglas que se ejecutan en cada turno: la maqueta manda; las
  maquetas se versionan sin avisar y hay que confirmar que se está mirando la más nueva; las
  maquetas se copian entre módulos y arrastran el texto del original; la pantalla pública es un
  contrato de salida, no un espejo del backoffice; el gestor de tickets nunca se escribe; y las
  historias se referencian por nombre, nunca por número.
- **`hu-redactor`** (agente) — redacta, revisa y corrige historias de backoffice a partir de
  maquetas y documentación. No inventa: lo que la maqueta no sostiene va a definiciones
  pendientes.
- **`hu-refutador`** (agente) — verifica una historia contra su maqueta y devuelve un veredicto
  por afirmación. No escribe, no corrige y no agrega hallazgos propios. Ante evidencia faltante
  el default es `sin-sustento`, y eso no es un descarte: es una definición pendiente que
  alguien iba a inventar.
- **`hu-escribir`** (skill) — el formato de las historias, pensado para que las tome una IA que
  después escribe el código.
- No aporta ningún check. El directorio existe y está vacío.

## De qué depende

- `comun/`, que se instala siempre: los hooks, la regla de secretos y el formato de memoria.
- El instalador, que descubre este harness por la sola presencia de su `manifest.json`.
- Las maquetas y la documentación funcional del proyecto donde se instala; sin eso, los dos
  agentes no tienen fuente contra la cual trabajar.
- `hu-refutador` y `hu-redactor` están adaptados de material de terceros: la forma del
  refutador desacoplado y el reporte de resolución de skill vienen de `terceros/gentle-ai/`,
  con la nota de procedencia arriba de cada archivo.

## Dónde está

- `harnesses/analisis/manifest.json`
- `harnesses/analisis/claude-md/bloque.md`
- `harnesses/analisis/agents/hu-redactor.md`, `hu-refutador.md`
- `harnesses/analisis/skills/hu-escribir/SKILL.md`
- `harnesses/analisis/checks/` — vacío, solo el `.gitkeep`.
