# docs/cambios

## Qué es

Los artefactos del método con el que se trabaja en este repo: una carpeta por cambio, con la
especificación de lo que se construye y la verificación de que cumple.

El método es especificar, construir, testear y verificar. Los tests salen de la spec con el
código ya armado, y quien construye no verifica.

Es la parte del repo que registra el trabajo **antes** de hacerlo. La bitácora por versión
registra lo que pasó después.

## Qué expone

- **`spec.md`** por cambio — qué se construye y cómo se prueba que cumple. Los escenarios se
  numeran `E-nn` y cada uno lleva la marca de que se lo vio fallar antes de arreglarlo. Un test
  que cubre un escenario nombra su id en el título o en un comentario, y así se puede ir del
  escenario al test y al revés.
- **`verificacion.md`** por cambio, cuando ya se verificó — un veredicto por escenario. Un
  veredicto `contradicho` o `sin-sustento` no cierra el cambio, y el archivo existiendo no
  cierra nada por sí solo.
- **`plan.md`** en algunos cambios — el detalle de ejecución. Son los archivos más largos del
  directorio, con el razonamiento paso a paso.
- Cinco cambios registrados hasta ahora: el porteo de los hooks a Python (el único con
  verificación escrita), el agente iniciador del índice de código, la capacidad de trabajar con
  SDD, el estado del mapa declarado en la nota de versión, y el mapa de nodos del código.

## De qué depende

- Las skills de [la fábrica](fabrica.md) que fijan el formato: una para escribir la spec y otra para
  registrar el veredicto.
- El agente refutador de [la fábrica](fabrica.md), que dicta los veredictos contra la spec, corre los tests
  y no escribe nada.
- [La suite](tests.md): los escenarios se verifican corriéndola, no leyéndola.
- El fundamento del método está en `0006-sdd-como-metodo-de-los-proyectos.md`, uno de los ADR
  de [`docs`](docs.md).

## Dónde está

- `docs/cambios/hooks-en-python/` — `spec.md`, `plan.md`, `verificacion.md`
- `docs/cambios/iniciador-code/` — `spec.md`, `plan.md`
- `docs/cambios/sdd-capacidad/` — `spec.md`
