# comun/hooks

## Qué es

Los cuatro hooks que corren dentro de la sesión de otra persona, y la librería que comparten.
Son infraestructura: leen el evento que manda Claude Code por stdin y contestan una de tres
cosas — avisar, bloquear o preguntar — o se callan.

Desde 0.13.0 corren en Python 3.9+. El contrato de fondo no cambió: **un hook jamás rompe la
sesión y siempre sale con código 0**, pase lo que pase.

La única regla que bloquea en todo el harness es la de secretos, y vive acá.

## Qué expone

- **`session-start.py`** — contesta "en qué quedamos": quién sos, qué harness rige, el estado
  de git, los últimos commits, lo que alguien dejó anotado en la zona caché del `CLAUDE.md` y
  cuántas definiciones quedaron abiertas. Presupuesto: 12 líneas. Todo sale de fuentes que ya
  pasaron por el filtro humano de "esto vale la pena escribirlo"; no captura nada por su
  cuenta. También avisa, una sola vez y solo con `desarrollo` instalado, que todavía no hay
  índice del código.
- **`pre-tool-use.py`** — exclusivamente el bloqueo de secretos. Nada más entra ahí: es la
  puerta, dispara antes de cada llamada a herramienta y cada regla de más se paga siempre.
- **`post-tool-use.py`** — el caballo de batalla: corre los checks contra lo que se acaba de
  escribir y devuelve los hallazgos como contexto adicional. Es el único evento portátil donde
  el aviso llega de verdad al modelo. Sin hallazgos, silencio.
- **`user-prompt-submit.py`** — un solo trabajo, rutear a una skill. Hoy calla siempre: el
  ruteo por disparadores está declarado pero no implementado.
- **`lib/hook.py`** — lo que es idéntico en los cuatro y que, hecho mal, falla en silencio:
  lectura del evento tolerando BOM, un único JSON de salida por corrida, escritura en bytes
  UTF-8 (en Windows `stdout` sale en cp1252 y un aviso con tilde llegaría corrupto), las tres
  salidas válidas, un mensaje de sistema que se emite una sola vez por sesión y evento, y el
  envoltorio que garantiza salida 0.
- **`lib/secretos.py`** — el detector. Dos niveles de confianza y la distinción es lo
  importante: **alta bloquea**, **media pregunta**. Describe el hallazgo sin repetir el valor.
  Decide qué hacer el hook, no el detector.
- **`lib/reglas.py`** — carga y corre los checks por ruta (se llaman con guiones y un guion no
  es un nombre importable), lee la config del proyecto y corta a ocho hallazgos.
- **`lib/zonas.py`** — mide las zonas del `CLAUDE.md`: cuáles existen, cuántas líneas de
  contenido tiene cada una, qué marcadores parecen una zona escrita con otro nombre y cuánto
  quedó fuera de toda zona. Tiene además una interfaz de línea de comandos que usa el
  instalador, para que la definición de las zonas viva en un solo lado.

## De qué depende

- Python 3.9+ del sistema, invocado por los lanzadores que escribe el instalador.
- El catálogo `comun/reglas/secretos.patrones.json`: doce patrones (diez de confianza alta,
  dos media) y quince patrones de excepción para lo que parece un secreto y no lo es —
  variables de entorno, placeholders, ejemplos. El falso positivo es el riesgo existencial de
  todo esto: un bloqueo que traba trabajo legítimo se desinstala esa misma semana.
- `harness.config.json` del proyecto, cuando existe. Nunca es obligatorio.
- Los checks, que son N y son reglas. La separación entre hooks y checks existe para que
  agregar una regla no pueda romper el manejo de stdin, el encoding ni el control de errores.
- `git`, opcional: si no está, el bloque de estado no sale y nada se rompe.

## Dónde está

- `comun/hooks/session-start.py`, `pre-tool-use.py`, `post-tool-use.py`,
  `user-prompt-submit.py` — los cuatro eventos.
- `comun/hooks/lib/hook.py`, `secretos.py`, `reglas.py`, `zonas.py` — la librería compartida.
- `comun/reglas/secretos.patrones.json` — el catálogo de patrones de secreto y de excepciones.
- El contrato completo, con las trampas de cada salida, está escrito en `docs/contrato-hooks.md`.
