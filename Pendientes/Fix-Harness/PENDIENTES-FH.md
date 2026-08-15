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

## Outside the harness, written down so it is not lost

### Four IGE documents nobody read

At the root of `C:\Work\GCBA\IGE`: `Setup de Proyecto v3 - IGE.docx`, which the DGISIS guide
requires as an attachment in two different procedures, the two annexes on structure and missions,
and the TECBA functional specification.

### Credential in the `siccsir` agents

`siccsir-backend.md:13` and `siccsir-qa.md:12` carry a seed user with its password in clear text,
and the number is an employee file number. Decision taken: it stays, it is a seed for a local
Docker. Written down here in case the criterion changes.
