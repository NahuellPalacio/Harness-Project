# checks

## Qué es

Las reglas que corren después de cada escritura y avisan cuando algo no cumple una norma.
Son cinco, todas con el mismo contrato: un `.py` que expone `verificar(evento, proyecto,
config)` y devuelve cero o más strings, uno por hallazgo. Silencio cuando está todo bien.

**Ninguno bloquea.** Lo único que este harness bloquea son los secretos, y eso pasa antes, en
el hook de `PreToolUse`. Un check acá llegaría tarde y con menos autoridad.

Uno lo aporta `comun/` y cuatro los aporta el harness `desarrollo`; se agrupan juntos porque
comparten contrato, presupuesto y la misma regla de diseño: salir temprano.

## Qué expone

- **`claude-md-zonas.py`** (comun) — mide las zonas del `CLAUDE.md` del proyecto contra sus
  techos, avisa cuando falta una, cuando una está escrita con otro nombre (y entonces el
  harness no la mide), cuando hay demasiado contenido fuera de toda zona, y cuando la caché va
  llena, que no es un problema sino conocimiento sin bajar.
- **`dev-codebase-forma.py`** — la forma del índice del código: que el índice y las fichas se
  correspondan en los dos sentidos, y que cada ficha tenga sus cuatro secciones con el título
  exacto. Solo mira lo que cayó adentro del directorio del índice.
- **`dev-api-rutas.py`** — nomenclatura de rutas de API según ES0903: la ruta lleva versión y
  el recurso es un sustantivo, no un verbo. La regla de plural solo se reporta cuando es
  inequívoca.
- **`dev-dependencias.py`** — las dependencias se fijan en una versión exacta (ES0901). Un
  rango delega la elección al gestor de paquetes, que resuelve distinto en cada máquina.
- **`dev-infra-en-codigo.py`** — servidores por nombre DNS y nunca por IP, y configuración
  afuera del código. Una IP solo se reporta en posición de host; las de loopback y las de
  documentación no se tocan nunca.
- **`dev-accesibilidad-html.py`** — lo comprobable del marcado por ley 26.653 / WCAG: `lang`
  en `<html>`, `alt` presente en las imágenes (`alt=""` es correcto y no se reporta), controles
  de formulario que puedan tener etiqueta, y un único `<h1>`. No juzga contraste ni orden de
  lectura: para eso hace falta renderizar.
- **`lib/dev.py`** — lo que todos los checks de desarrollo hacen igual: leer del disco el
  archivo que se acaba de escribir (no del evento, porque una edición manda solo el fragmento),
  descartar rutas generadas, ubicar el número de línea y formatear una lista de ejemplos.

## De qué depende

- `comun/hooks/post-tool-use.py`, que es quien los descubre, los carga por ruta y entrega los
  hallazgos. Un check roto se saltea en silencio: reportarlo en cada escritura sería peor que
  el problema que quiso evitar.
- El presupuesto de ocho hallazgos por corrida, definido en `lib/reglas.py`. Los que gasta un
  check con ruido no los tiene el que encontró algo de verdad.
- `harness.config.json` del proyecto para los techos de zona, el umbral de cobertura y la ruta
  del índice del código. Los defaults viven en el código porque ese archivo se crea una sola
  vez y un proyecto viejo no tiene las claves nuevas.
- `comun/checks/claude-md-zonas.py` importa `lib.zonas` de los hooks; los de desarrollo, no:
  se mantienen sin depender de `comun/` porque se cargan por ruta y resolver esa ruta relativa
  sería frágil.
- Los estándares extractados en `normativa/`, que son la fuente de las reglas de desarrollo.

## Dónde está

- `comun/checks/claude-md-zonas.py`
- `harnesses/desarrollo/checks/dev-codebase-forma.py`, `dev-api-rutas.py`,
  `dev-dependencias.py`, `dev-infra-en-codigo.py`, `dev-accesibilidad-html.py`
- `harnesses/desarrollo/checks/lib/dev.py`
- Los casos de borde de los cuatro checks de desarrollo, en `tests/casos/08_checks_borde.py`.
