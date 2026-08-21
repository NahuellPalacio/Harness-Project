# harnesses/desarrollo

## Qué es

El harness para el trabajo técnico: código, APIs y deploy. Hace cumplir los estándares del
GCBA — ES0901, ES0902, ES0903, PC0901, la guía de la DGISIS y Obelisco v2 — sin que nadie
tenga que acordarse de ellos.

Su prefijo de namespace es `dev`. Aporta la mayor parte de las skills del repo, y lo hace en
skills y no en el `CLAUDE.md` a propósito: lo que no se necesita en cada turno no se carga en
cada turno.

Sus cinco checks están descriptos en la ficha `checks`, junto con el de `comun/`.

## Qué expone

- **`manifest.json`** — id, prefijo `dev` y los defaults del proyecto: la ruta del índice del
  código, el umbral de cobertura, la versión de Obelisco, el nivel de accesibilidad exigido, el
  prefijo de las rutas de API y si se verifican las versiones homologadas.
- **`claude-md/bloque.md`** — las reglas de cada turno: las versiones de las dependencias las
  fija la ASI y no se eligen; la configuración va afuera del código; los servidores se
  referencian por nombre DNS; ante un error inesperado no se expone nada de la infraestructura
  y el estado es 500; Obelisco es obligatorio por resolución; la accesibilidad es exigible por
  ley.
- **`dev-iniciador-code`** (agente) — recorre el código entero una vez y deja escrito qué hay,
  bajo el directorio del índice: una ficha por módulo más un `indice.md`. Existe para pagar una
  sola vez el trabajo que si no se paga en cada sesión.
- **`dev-refutador`** (agente) — verifica código, contratos de API o documentos técnicos contra
  los estándares y devuelve un veredicto por afirmación. No escribe y no corrige. Hermano del
  refutador de `analisis`, del que hereda la forma.
- **Ocho skills**, una por dominio: `dev-api` (ES0903: rutas, versionado, forma de la
  respuesta, errores, contratos OpenAPI/RAML), `dev-identidad` (OpenID Connect contra Keycloak,
  BA ID / miBA, Active Directory, sesión, roles y permisos), `dev-seguridad` (ES0902: datos,
  validación, subida de archivos, logs, assessment, WAF, qué traba un pase), `dev-pantalla`
  (Obelisco v2 y accesibilidad), `dev-ambientes` (pases DESA → QA → HML → PRD, control de
  cambios PC0901, el FUR y sus entregables), `dev-tramites-asi` (cómo se pide cada cosa por
  ticket y qué lleva cada modelo), `dev-repositorio` (estructura, ramas, versionado semántico,
  entrega) y `dev-versiones` (versiones homologadas y dependencias; a propósito no trae ni un
  número, porque los números caducan).

## De qué depende

- `comun/`, que se instala siempre.
- El instalador y su `manifest.json`, que es lo único que hace falta para que el harness exista.
- Los extractos de `normativa/`, que son la fuente de casi todo lo que afirman las skills. Los
  extractos declaran además qué **no** se puede citar desde ellos y hay que ir al PDF original.
- El agente `dev-iniciador-code` depende de la clave `rutaCodebase` de la configuración del
  proyecto, del `git ls-files` del repositorio que recorre, y lo que escribe lo verifica el
  check `dev-codebase-forma`. El hook de `SessionStart` avisa que ese índice falta hasta que
  existe.

## Dónde está

- `harnesses/desarrollo/manifest.json`
- `harnesses/desarrollo/claude-md/bloque.md`
- `harnesses/desarrollo/agents/dev-iniciador-code.md`, `dev-refutador.md`
- `harnesses/desarrollo/skills/dev-api/`, `dev-identidad/`, `dev-seguridad/`, `dev-pantalla/`,
  `dev-ambientes/`, `dev-tramites-asi/`, `dev-repositorio/`, `dev-versiones/` — un `SKILL.md`
  en cada uno.
- `harnesses/desarrollo/checks/` — descripto en la ficha `checks`.
