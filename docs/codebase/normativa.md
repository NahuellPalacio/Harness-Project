# normativa

## Qué es

Los estándares del GCBA destilados a markdown. Es **insumo de autoría, nunca se copia a un
proyecto**: de acá salen las afirmaciones de las skills de `desarrollo`, los checks que
implementan una regla y los veredictos del refutador.

Los PDF originales son documentación interna del organismo y este repo es público, así que no
se publican: van en un directorio gitignoreado y cada quien pone los suyos. El harness funciona
sin ellos.

Cada extracto declara arriba su fuente, su versión, su cantidad de páginas y la fecha en que
se extractó.

## Qué expone

- **`ES0901`** — Estándar de Desarrollo de la ASI, v6.3, 42 páginas. El más largo: versiones
  homologadas, estructura de repositorio, versionado semántico, entrega, canal de consulta.
- **`ES0902`** — Estándar de Seguridad, v6.2. El circuito de assessment de seguridad y sus
  anexos.
- **`ES0903`** — Estándar de Desarrollo API, v2.2. Nomenclatura de rutas, versionado, forma de
  la respuesta y de los errores.
- **`PC0901`** — Proceso de control de cambios en software de aplicación, v1.0. Quién aprueba
  qué y con qué evidencia.
- **`GuiaDGISIS`** — Guía de Procesos de la DGISIS, v1.0. Los trámites: cómo se pide un
  ambiente, una base, un repositorio, credenciales.
- **`Obelisco`** — Guía de adopción de Obelisco v2, el sistema de diseño obligatorio.
- **La sección "Lo que NO se puede citar desde acá"**, que abre cada extracto. Es lo más
  valioso del formato: dice explícitamente qué quedó afuera —un diagrama que solo existe como
  imagen, una tabla que caducó, un dato personal omitido a propósito— para que nadie complete
  el hueco por analogía y haya que ir al PDF.

## De qué depende

- Los PDF originales, que **no** están en el repo. Sin ellos no se puede volver a extractar ni
  verificar lo no citable, pero todo lo que ya está extractado se lee igual.
- El agente `leer-docs` y `docimg.py`, que son con lo que se produjeron y con lo que se
  vuelven a abrir los originales si aparecen.
- Nada del harness instalado depende de este directorio en tiempo de ejecución: lo que viaja a
  un proyecto son las skills, no los extractos.

## Dónde está

- `normativa/extractos/ES0901.md`, `ES0902.md`, `ES0903.md`, `PC0901.md`, `GuiaDGISIS.md`,
  `Obelisco.md`
- `normativa/fuentes/LEEME.md` — qué va ahí y por qué el directorio está gitignoreado.
- El fundamento de que lo externo nunca sea requisito está en `docs/adr/0008`.
