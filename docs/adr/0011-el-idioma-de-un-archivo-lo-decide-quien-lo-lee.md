---
estado: aceptada
creado: 2026-09-15
---

# ADR-0011 — El idioma de un archivo lo decide quién lo lee

## Contexto

`CLAUDE.md` tiene una regla de idioma escrita desde el principio:

> Spanish, rioplatense, for everything that ships: `comun/`, `harnesses/`, `docs/`, `CHANGELOG.md`,
> commit messages and every reply. English inside `.claude/`, `Pendientes/`, file names, commands,
> code and identifiers.

El criterio es **dónde vive el archivo**. Y el repositorio ya no lo cumple, porque el criterio no
alcanza:

| Archivo | Vive en | Idioma | Según la regla |
|---|---|---|---|
| `harnesses/desarrollo/agents/dev-iniciador-code.md` | `harnesses/` | inglés | debería ser español |
| `harnesses/desarrollo/agents/dev-refutador.md` | `harnesses/` | español | cumple |
| Las ocho `skills/dev-*/SKILL.md` | `harnesses/` | inglés | deberían ser español |
| `harnesses/analisis/agents/hu-*.md` | `harnesses/` | español | cumplen |

Ocho skills y un agente se escribieron en inglés y nadie lo objetó, porque quien los escribió sabía
algo que la regla no dice. `dev-iniciador-code.md` lo tiene anotado en su segunda línea, que es la
única vez que el repositorio lo declaró:

> *"Everything you write for people is in **Spanish, rioplatense** — it is read by the project
> team. These instructions are in English; what you produce is not."*

La mitad de la regla estaba descubierta. Un archivo `.md` de este repositorio puede tener dos
lectores muy distintos —una persona del equipo, o un modelo al que se le carga como instrucción— y
la regla vigente no los distingue.

## Decisión

**El idioma de un archivo lo decide quién lo lee, no dónde está guardado.**

```
Lo lee un modelo, como instrucción     -> inglés
Lo lee una persona                     -> español, rioplatense
```

En concreto:

| En inglés | En español |
|---|---|
| `agents/*.md` | `docs/` entero |
| `skills/*/SKILL.md` | `CHANGELOG.md`, `UPGRADE.md`, `README.md` |
| `standards/`, `policies/`, `instructions/` | `docs/versiones/`, `docs/adr/`, `docs/cambios/` |
| Cualquier `.md` que se cargue como prompt | Mensajes de hooks, checks e instaladores |
| Nombres de archivo, comandos, código, identificadores | Mensajes de commit |
| Los campos de un contrato JSON | **Toda respuesta al usuario, siempre** |

🔴 **Lo que un agente produce no hereda el idioma de sus instrucciones.** Un agente escrito en
inglés que le contesta a una persona, le contesta en español. Es lo que ya hacía
`dev-iniciador-code` y lo que la regla nueva generaliza: el idioma de la instrucción y el idioma de
la salida son dos decisiones, y la segunda la decide el lector de la salida.

### Por qué el inglés para lo que consume un modelo

No es preferencia estética ni suposición sobre en qué idioma "piensa" mejor un modelo — nadie midió
eso acá y este ADR no lo afirma. Son tres razones verificables:

1. **El vocabulario técnico no tiene traducción estable.** *Merge request*, *rate limit*,
   *capability*, *work unit*, *tier*. Traducirlos inventa términos que después no coinciden con la
   documentación de la herramienta que el agente tiene que usar, y no traducirlos deja un texto
   mitad y mitad que es peor que cualquiera de los dos.
2. **Los contratos ya están en inglés.** `project-context/1.1` y `task-context/1.0` tienen sus
   claves en inglés porque un schema JSON se lee con las convenciones de su formato. Un agente que
   lee `gaps_and_conflicts` y recibe instrucciones sobre "huecos y conflictos" tiene que hacer una
   traducción en el medio, y ahí es donde un campo se confunde con otro.
3. **Es lo que el repositorio ya venía haciendo**, en ocho de sus once piezas cargables. La regla no
   introduce una práctica: describe la que hay y le da un motivo.

### La fuente normativa se queda en español

`normativa/extractos/` es el destilado de estándares del organismo escritos en español. **No se
traduce.** Es material citable, y una cita traducida deja de ser una cita. Lo que puede estar en
inglés es la representación operativa que se derive de esos extractos —una regla como dato, con su
id y sus condiciones— siempre que apunte al extracto original para el texto.

```
Fuente normativa en español  ->  representación operativa en inglés  ->  respuesta en español
```

## Consecuencias

**A favor:**

- La regla pasa a describir lo que el repositorio hace, en vez de contradecirlo en ocho archivos.
- Un archivo nuevo ya no necesita que alguien decida caso por caso: se pregunta quién lo lee.
- El criterio se puede verificar: un `.md` con frontmatter `name:`/`description:` es una pieza
  cargable y va en inglés. No hace falta juicio para clasificarlo.

**En contra:**

- 🔴 **`harnesses/desarrollo/agents/dev-refutador.md` queda incumpliendo la regla el mismo día que
  se escribe.** Está en español y es una pieza cargable. No se traduce acá a propósito: mezclarlo
  con el cambio que introduce la regla haría que un solo diff dijera dos cosas. Queda anotado en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`, y lo mismo vale para
  `harnesses/analisis/agents/hu-redactor.md` y `hu-refutador.md`.
- El repositorio pasa a tener dos idiomas conviviendo por diseño, y alguien que entra tiene que
  entender el criterio antes de escribir su primer archivo. Es el costo de que el criterio anterior
  —uno solo para todo— no fuera cierto.
- **Un agente puede contestar en el idioma equivocado y ningún check lo detecta.** El idioma de la
  salida es una propiedad de una corrida de un modelo, no de un archivo: entra en el territorio de
  ADR-0009, se verifica por lectura y nada más.

## Revisión

Se revisa si aparece una pieza cargable que **tenga que** estar en español por una razón de fondo
—un agente cuyo trabajo sea redactar en español y que necesite los ejemplos en ese idioma adentro
de sus instrucciones, por ejemplo—. Ahí la regla no se rompe: se le agrega la excepción con su
motivo, que es lo que este repositorio hace con `.gitignore`, con las zonas del `CLAUDE.md` y con
cada exclusión de una spec.
