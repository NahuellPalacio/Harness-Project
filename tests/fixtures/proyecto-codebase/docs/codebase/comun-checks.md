# comun/checks

## Qué es

Las reglas que corren después de cada escritura. Se descubren por estar en el directorio: no hay
registro que actualizar para sumar una.

## Qué expone

`verificar(evento, proyecto, config)`, que devuelve cero o más strings. Cada string es un hallazgo.

## De qué depende

De `comun/hooks/lib/reglas.py`, que las descubre, las ordena alfabéticamente y corta a los ocho
hallazgos.

## Dónde está

`comun/checks/` para las de todos, y `*/checks/` para las de cada harness.
