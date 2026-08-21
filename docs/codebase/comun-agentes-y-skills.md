# comun/agentes-y-skills

## Qué es

Los agentes, las skills y la herramienta de línea de comandos que se instalan **siempre**, con
cualquier harness. Es la parte del esqueleto que no es infraestructura: no corre sola, la
invoca alguien cuando hace falta.

Son pocas a propósito. Cada skill cuesta unos 100 tokens de nombre y descripción en cada turno
de cada sesión, y solo se expande cuando alguien la usa.

## Qué expone

- **`flush-memoria`** (agente) — mantiene chico el `CLAUDE.md` bajando su zona caché al
  directorio de conocimiento del proyecto. Sube lo que falte, verifica que quedó completo y
  recién entonces borra dejando un puntero. Su invariante: nunca se desaloja lo que no se
  escribió; ante la duda, no borra.
- **`leer-docs`** (agente) — abre lo que el resto no puede abrir: PDF, DOCX, XLSX, PPTX, MSG,
  incluidos los diagramas y capturas embebidos, que convierte a imagen y mira. Devuelve solo el
  extracto pedido, no el documento.
- **`instalar-desde-github`** (skill) — qué revisar antes de instalar o adoptar una herramienta,
  plugin o servidor MCP que vive en un repositorio ajeno, y antes de copiar material de terceros
  al repo.
- **`docimg.py`** — la herramienta que usa `leer-docs` para recuperar la capa que markitdown
  descarta. Cuatro verbos: `inventario` (qué hay adentro, sin extraer nada), `extraer`
  (imágenes embebidas de un OOXML, que es un ZIP), `buscar` (en qué páginas de un PDF aparece
  un término) y `render` (páginas a PNG). Todo sale como JSON. En PDF siempre renderiza la
  página y nunca extrae los rasters: los diagramas de los estándares del GCBA son vectoriales
  y una extracción de rasters devuelve nada.

## De qué depende

- El instalador, que los copia a `.claude/agents/` y `.claude/skills/` del proyecto según el
  bloque `aporta` de `comun/manifest.json`.
- `flush-memoria` depende de las zonas del `CLAUDE.md` y de la clave `rutaMemoria` de la
  configuración del proyecto (por defecto, `docs/conocimiento`). Es el que hace posible el
  techo de la zona caché que mide el check.
- `docimg.py` corre con el Python del entorno de markitdown, que ya trae `pypdfium2`,
  `pdfplumber` y `pillow`. No instala nada, y la ruta de ese intérprete es de cada máquina.
- `leer-docs` depende de `docimg.py` y de la herramienta de lectura de imágenes del agente.

## Dónde está

- `comun/agents/flush-memoria.md`
- `comun/agents/leer-docs.md`
- `comun/skills/instalar-desde-github/SKILL.md`
- `comun/bin/docimg.py`
- La política de memoria que sostiene a `flush-memoria` está escrita en `docs/memoria.md`.
