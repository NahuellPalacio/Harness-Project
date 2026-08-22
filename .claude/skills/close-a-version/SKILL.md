---
name: close-a-version
description: Use when a change closed and a version has to be released. The full ritual — VERSION, the note in docs/versiones with its five mandatory sections, the index row, the CHANGELOG entry, UPGRADE, the item leaving Pendientes, and the flow map when the flow moved.
---

# Close a Version

## The idea

Six files move together, and `tests/casos/08-bitacora.ps1` turns the suite red if any of them is
missing. That test exists for a stated reason: *"escribir la nota al cerrar una version es una
intencion que dura hasta la primera semana ocupada. Lo que nadie mide, no se hace."*

Do them in this order. Steps 1 to 3 are one unit — a `VERSION` bumped without its note is a red
suite. Step 7 is outside the test's reach and only fires when the flow moved; it is here because the
map rots exactly the way the log does.

## 1. `VERSION`

A bare string, one line, no BOM. `MAJOR.MINOR.PATCH` — SemVer, and the CHANGELOG says why: *"como
exige ES0901 para el software de aplicación del organismo."*

It flows to four places on its own: the installer banner, `settings.json`, `harness.lock.json`
(from where `session-start.py` echoes it into every session), and the `-Doctor` / `-Update`
comparison that tells a project it is behind.

## 2. `docs/versiones/<version>.md`

Filename is the bare version. Template: `docs/versiones/_plantilla.md`.

🔴 **The five sections are fixed and none is omitted.** If something does not apply, write that it
does not apply. *Una sección ausente se lee como olvido, no como vacío.* The test matches these
strings literally, accents included:

```
## Qué se hizo
## Qué se decidió, y por qué
## Lo que se rompió en el camino
## Lo que quedó abierto
## Dónde seguir
```

Header line: `> <fecha> · commit(s) \`<sha>\` · <N> tests en verde`. Then one paragraph: what
problem the harness had before this version and what is different after. Somebody who reads only
that has to understand why the version existed.

| Section | What actually goes in it |
|---|---|
| Qué se hizo | What was built, in bullets, with real paths. Not the CHANGELOG reworded: here goes the work, there goes the effect on whoever updates |
| Qué se decidió, y por qué | Especially the decisions that discarded an alternative. This is what cannot be reconstructed later and what is most expensive to re-litigate |
| Lo que se rompió en el camino | The bugs found and what caused them. If nothing broke, write it |
| Lo que quedó abierto | Loose ends with their reason, each naming where it now lives. An explicit emptiness counts, a tacit one does not |
| Dónde seguir | 📌 **The section that justifies the whole log.** Written for somebody who was not in the conversation: what was next, what decision was pending on whom, what context is needed to pick it up |

Two standing rules from `docs/versiones/README.md`:

- **Lo que se anota es lo que no se puede reconstruir después.** The diff is in git and the what
  changed is in the CHANGELOG.
- 🔴 **No inventar.** If you do not remember why a decision was taken, write that it is not
  recorded. *Un motivo inventado se lee bien y nadie lo cuestiona.*

## 3. The index in `docs/versiones/README.md`

A new row at the top of the table. Newest first, date as `DD-MM-YYYY`:

```markdown
| [0.13.0](0.13.0.md) | 17-08-2026 | Los cuatro hooks, los cinco checks y la suite, de PowerShell a Python; el shim `.sh` que faltaba |
```

The test looks for the literal `(<version>.md)`. A note that is not indexed fails the suite, because
*un índice desactualizado es peor que ninguno: hace creer que lo que no figura no existe.*

## 4. `CHANGELOG.md`

A new entry at the top, `## [x.y.z] — YYYY-MM-DD` — the test parses that exact shape.

Open with a **bolded thesis sentence**, then two to four lines: the problem, the number, what was
done, what got closed along the way. Then the categories.

`### Agregado` · `### Cambiado` · `### Corregido` are the usual ones, **and they are not fixed**.
A version invents the section it needs to tell the truth — 0.13.0 wrote
`### Lo que no se cumplió, sin maquillar`, 0.11.0 wrote `### Criterio que quedó fijado`.

Bullets are `- **<lo que es>** — <qué y por qué>`. 🔴 marks a breaking change or a promise not kept:

```markdown
- 🔴 **El contrato de un check rompe.** `param($Evento, $Proyecto, $Config)` pasa a ser
  `def verificar(evento, proyecto, config) -> list[str]` — ver [UPGRADE.md](UPGRADE.md)
```

📌 A `contradicho` that closed anyway goes here, under its own heading, with its number. It is not
hidden in the version note.

## 5. `UPGRADE.md`, only if it breaks

A `## X.Y.Z → X.Y.Z` section at the top of the list. It says whether `-Update` is enough or there is
a manual step, and it shows the manual step. If `-Update` is enough, write that in one line —
`0.6.0 → 0.7.0` is the model.

## 6. The item leaves `Pendientes/`

*"When an item closes it leaves this file and lands in its version note."* Delete the `###` block
from `Pendientes/Fix-Harness/PENDIENTES-FH.md` — it is now in `## Qué se hizo`, and what stayed open
is in `## Lo que quedó abierto`.

🔴 **Re-rank the `## What to take first` table.** It is a running order, and the ranks are
positions, not labels: removing row 2 leaves a gap that has to close. See `note-a-pending`.

## 7. The map, if the flow moved

`docs/mapa/recorrido-mensaje.html` draws what the harness does between a person's message and
Claude's answer. If this version touched anything on that path — a hook, a matcher, an event, a form
of output, a decision inside `pre-tool-use.py` or `lib/reglas.py` — the map is part of the version
and closes with it.

🔴 **Republish to the same URL.** It lives in an HTML comment at the top of the file. Pass it as the
`url` parameter of the Artifact tool. Publishing without `url` mints a *new* artifact and strands the
link somebody already has.

`docs/mapa/mapa-harness.html` is the long one — composition, installer, memory, secrets. Same rule,
its own URL in its own header comment.

📌 **Nothing measures this one.** `08-bitacora.ps1` rules on the six files above and knows nothing
about the map. What keeps it honest is that it is cheap: one file, and usually two boxes. A map that
lies is worse than no map, because it lies with the authority of a diagram.

## Before you call it closed

```powershell
.\tests\Invoke-Tests.ps1
```

Green, or the version does not close. `08-bitacora.ps1` is the one that rules on all of the above:
every CHANGELOG version has its note, no note is orphaned, the current `VERSION` has its own, every
note has the five sections, and the README indexes them all.

If the suite dies mid-run, check the tree before anything else — `03-instalador.ps1` breaks
versioned files on purpose and restores them in a `finally` that does not survive the process being
killed:

```bash
git checkout -- comun/hooks/pre-tool-use.py comun/hooks/lib/zonas.py
```

All your output in Spanish, like the rest of the harness.
