# Pending fixes

What is still open, with the context needed to pick it up cold. Each entry says what happens, why
it matters and what should be done.

When an item closes it leaves this file and lands in its version note, under `docs/versiones/`.

## Distribution

### The closure of the remote is not in a version note yet

The remote exists: `https://github.com/NahuellPalacio/Harness-Project`, public, `main`. The
README and `docs/instalacion.md` document both install paths, and `normativa/fuentes/` is
gitignored so the internal GCBA PDFs never go public. What is missing is the release itself:
a `docs/versiones/0.13.0.md` and the `VERSION` bump. Until that happens the repo says 0.12.0
while it already carries distribution.

## Missing measurement

### The always loaded cost of agents and skills is neither measured nor capped

Measured by hand on 2026-08-14: 15 pieces, around 1540 tokens, average 103 per piece, estimating
one token every four characters of `name` plus `description`, paid on every turn. Meanwhile
`CLAUDE.md` has five caps with a check that warns. This is exactly the boundary the harness
claims to guard and does not measure. Nothing stops the next piece from doubling that number.

Fix. `-Doctor` measures and reports the total; new cap `techoAssetsSiempreCargados` in
`comun/manifest.json`. It warns, it never blocks.

### `-Doctor` does not measure hook latency

The original plan said to evaluate rewriting them in Node if the p50 went above roughly 400 ms,
but not before measuring it. It was never measured.

### The budget has to measure the session, not the harness

`superpowers` injects about 900 tokens per session with its `SessionStart` hook. The cap we set
ourselves is 2800, and a third party takes close to a third of it, invisible to the current
`-Doctor`.

## Incomplete capabilities

### Skill routing in `UserPromptSubmit` is mute

The hook exists, it is registered and it does nothing. Its intended job was a single routing line
when the prompt matches the triggers of an installed skill.

### There is no `.sh` shim

Only `run-hook.cmd` exists. If someone uses WSL or Mac, the hooks do not start. The
`.gitattributes` is already prepared so their line endings do not break.

### The reviewer panel is planned and deferred

Three reviewers with different lenses, correctness, security and data, plus an infrastructure
expert, all of them in English, inside `desarrollo`. Deferred on purpose: use `desarrollo` first
and decide the lenses from that experience instead of from a hypothesis.

Full plan, with the decisions already taken and the doctrine to extract from the 8 agents of
`autoliquidador`, in `~\.claude\plans\te-parece-si-planificamos-kind-shell.md`. Estimate: around
3 hours, almost all of it unattended.

## Verification that was not done

### The `desarrollo` skills were never used on a real project

They are verified against the norm, not against the work. That is the test that matters: the
harness is worth it if a session with it comes out better than a session without it.

### The IGE stayed on v0.9.0

It is missing the 8 skills, the 4 checks, `dev-refutador` and the secrets fix from 0.12.0.

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File ./install.ps1 \
  -Project 'C:\Work\GCBA\IGE' -Update
```

### `ES0902.md` was the only extract that did not close as faithful

Its last finding was corrected by hand and never went back through adversarial refutation.

### What the checks witness never exercised, written down the day before the originals died

`tests/fixtures/paridad-checks.json` holds 5 cases and 11 findings, and it is what proved the
Python checks answer exactly what the PowerShell ones answered. It was never a coverage claim: it
proves parity on what it covers and says nothing about the rest. The rest is this list, read off
the five `.ps1` originals by the refuter on 2026-08-17, the day before `hooks-en-python` Task 8
deleted them. After that commit there is no implementation left to compare against, so anything
below that diverges today will diverge unnoticed.

- **`claude-md-zonas`** — a zone whose marker is misspelled ("similar name"), the excess of lines
  outside every zone, the ZONA CACHE warning at 75% or more, and a `CLAUDE.md` with no zones at
  all (the early empty return).
- **`dev.py`** — a file over 512 KB (silently discarded), and `es_ruta_generada` never returning
  `True`: no case runs a check against a path under `node_modules`, `vendor` or the like.
- **`dev-accesibilidad-html`** — a missing `<h1>` (only the duplicated one is exercised), the
  `.blade.php` and `.component.html` extensions, and a fragment with no `<html>`, which should
  skip the lang and heading rules.
- **`dev-api-rutas`** — `prefijoApi` coming from config (always `null` in the witness), a route
  that already carries its version (to prove it is *not* reported), the deduplication of a
  repeated route, and the documented false negative on camelCase verbs (`posts` vs
  `postulaciones`).
- **`dev-dependencias`** — `composer.json` with `require` and `require-dev`, the range forms
  `>=`, `<=`, `||`, the interval (` - `) and the `x`/`*` wildcards, invalid JSON, JSON that is
  not an object, and the documented defect with `false`, `0` or `null` as a dependency value.
- **`dev-infra-en-codigo`** — three of the four IP position patterns (`https://…`,
  `Data Source=…`, and the `jdbc/mongodb/redis/amqp/mysql/postgres` one, which is where its
  documented defect lives), the harmless-IP filter (loopback, `0.0.0.0`), the RFC 5737 range
  filter, the out-of-range octet discard, and the deduplication of a repeated IP.

Fix. Not a bug, a hole in the net: every line above is a case somebody can add to
`tests/casos/07_checks.py` as a plain assertion — no witness needed, since the expected answer is
whatever the rule says it should be. Worth doing before the checks are touched again for any
reason.

### Four behaviour fixes rode inside the Python port, so their diff never said one thing

The `hooks-en-python` change was bound to parity: port the behaviour, defects included, so that the
migration cannot hide a rule change. Four fixes broke that rule. They are in
`comun/hooks/lib/hook.py`, they are real, and `Hook.psm1` had every one of them identical:

- `mensaje_de_sistema` emitted outside its own `try`. A `BrokenPipeError` — the parent stopped
  reading — escaped `invoke_hook` and the process died with a non-zero exit code, in the very path
  that exists as the last line of defence.
- `except SystemExit: raise` re-raised any code, so a non-zero exit could leak out of a hook whose
  entire contract is that it always exits 0.
- Nothing stopped two JSON objects reaching stdout: a body that warned and then threw wrote both,
  concatenated without a separator, which breaks parsing and loses the legitimate warning too.
- The "already warned" marker was written before emitting and with a non-atomic check, so a failed
  emission lost the warning for the whole session.

They were closed on the argument that "a hook never breaks the session" is a global constraint of
the change and is scenario E-06 — not a business rule. The argument holds. What does not hold is
that they landed mixed into a port, which is exactly what the change promised not to do.

Fix. Nothing to write: the code is in and tested, with the red seen for the first and the third.
What is owed is the review this never got as its own change — read those four hunks on their own,
against `Hook.psm1`, and decide whether each one was worth taking. If any was not, it comes out.

### The Python port left four minor divergences written down and unfixed

None of them changes a verdict. They are here so they are not rediscovered as surprises.

- `texto_de_herramienta` has no test covering `new_string: null` inside `tool_input.edits`. The
  handling is correct by inspection; a regression there would not be caught by the suite.
- `importar_patrones` uses `os.path.isfile`, stricter than the `Test-Path` it ports, which also
  accepts a directory. No impact: the catalogue path is a fixed literal of the repo.
- There is no end-to-end case with a corrupt or missing catalogue. The path is covered by the
  generic mechanism of `invoke_hook` (E-07 and E-08), not by a case tied to the real hook.
- `_correr` and `_correr_proceso` live duplicated as local functions in each case file. It is a
  pre-existing pattern; if a third variant appears, that is when it earns a shared module.

## Outside the harness, written down so it is not lost

### Four IGE documents nobody read

At the root of `C:\Work\GCBA\IGE`: `Setup de Proyecto v3 - IGE.docx`, which the DGISIS guide
requires as an attachment in two different procedures, the two annexes on structure and missions,
and the TECBA functional specification.

### Credential in the `siccsir` agents

`siccsir-backend.md:13` and `siccsir-qa.md:12` carry a seed user with its password in clear text,
and the number is an employee file number. Decision taken: it stays, it is a seed for a local
Docker. Written down here in case the criterion changes.
