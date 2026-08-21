# comun/hooks

## Qué es

Los cuatro hooks del harness y el contrato que comparten: leer el evento por stdin, forzar el
encoding, atrapar cualquier excepción y salir siempre con código 0.

## Qué expone

`invoke_hook(nombre, cuerpo)`, y las tres salidas: `avisar`, `bloquear` y `preguntar`.

## De qué depende

De la biblioteca estándar de Python y de `comun/reglas/`. De nada más: un hook que necesitara
`pip install` no correría en la máquina donde tiene que correr.

## Dónde está

`comun/hooks/`, y `comun/hooks/lib/` para lo compartido.
