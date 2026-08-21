# docs/versiones

## Qué es

El registro de lo que pasó, en dos formatos que contestan preguntas distintas y por eso hacen
falta los dos.

El `CHANGELOG.md` mira hacia afuera: lo lee quien instala o actualiza, y se escribe para no
romperle nada a nadie. La bitácora mira hacia adentro: la lee quien sigue el trabajo, y guarda
el razonamiento, los caminos que se probaron y se descartaron y las puntas sueltas.

Va de 0.1.0 a 0.13.0, una nota por versión, sin huecos.

## Qué expone

- **`CHANGELOG.md`** — qué cambió a nivel funcional en cada versión, en `MAJOR.MINOR.PATCH`
  como exige ES0901.
- **`UPGRADE.md`** — qué hacer al pasar de una versión a la siguiente, y si el `-Update`
  alcanza o hay algo manual. Aclara que no hay un `git pull` en el medio porque todavía no hay
  remoto.
- **Una nota por versión**, con cinco secciones obligatorias. La que justifica todo esto es
  **"Dónde seguir"**: una conversación de trabajo se compacta y se pierde el hilo de qué se
  estaba por hacer y qué faltaba.
- **`_plantilla.md`** — la forma que toma cada nota.
- **`README.md`** del directorio — por qué existe la bitácora si ya hay un CHANGELOG, y qué va
  en cada uno.

## De qué depende

- La skill de la fábrica que dicta el ritual de cerrar una versión: el `VERSION`, la nota con
  sus cinco secciones, la fila en el índice, la entrada del CHANGELOG, el `UPGRADE`, el
  pendiente que sale de su archivo y el mapa del flujo cuando el flujo se movió.
- El caso de la suite que verifica la bitácora. Sin él, escribir la nota al cerrar una versión
  sería una intención que dura hasta la primera semana ocupada: lo que nadie mide, no se hace.
- El archivo `VERSION` de la raíz, que tiene que coincidir con la última nota.

## Dónde está

- `CHANGELOG.md` y `UPGRADE.md` — en la raíz.
- `docs/versiones/README.md` — por qué existe.
- `docs/versiones/_plantilla.md` — la forma de una nota.
- `docs/versiones/0.1.0.md` a `0.13.0.md` — trece notas.
