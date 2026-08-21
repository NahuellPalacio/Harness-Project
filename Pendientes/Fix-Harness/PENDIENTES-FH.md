# Pending fixes

What is still open, with the context needed to pick it up cold. Each entry says what happens, why
it matters and what should be done.

When an item closes it leaves this file and lands in its version note, under `docs/versiones/`.

## What to take first

Ordered by risk times cost, not by section. The sections below group by theme; this is the
running order.

| | What | Why now |
|---|---|---|
| 1 | Two installer tests break versioned files | It can leave `pre-tool-use.py` — the only blocking rule of the harness — broken in the tree, and four agents were killed by a watchdog during 0.13.0 |
| 2 | Review the four contract fixes on their own diff | They rode inside a port that promised not to change behaviour. Until somebody reads them alone, the promise is unverified |
| 3 | The IGE stayed on v0.9.0 | It is now four versions behind, and 0.13.0 breaks the check contract: any `.ps1` check written there stops running |
| 4 | What the checks witness never exercised | 25 branches with no test and no implementation left to compare against |
| 5 | The always loaded cost of agents and skills | The repo went from 53 to 449 tokens per turn during 0.13.0 and nothing caps it |
| 6 | The budget has to measure the session | Same blind spot, one level up |
| 7 | The four minor port divergences | None changes a verdict. Cheap to close while touching the files anyway |
| 8 | Skill routing in `UserPromptSubmit` is mute | A capability that was never built, not a defect |
| 9 | `ES0902.md` did not close as faithful | Predates all of this |
| 10 | The reviewer panel | Deferred on purpose until `desarrollo` is used on real work |

Items 1 and 2 are what 0.13.1 is for. Item 3 is not code: it is running `-Update` on a real
project, and it is what tells whether any of this works outside this repo.

## Missing measurement

### The always loaded cost of agents and skills is neither measured nor capped

Measured by hand on 2026-08-14: 15 pieces, around 1540 tokens, average 103 per piece, estimating
one token every four characters of `name` plus `description`, paid on every turn. Meanwhile
`CLAUDE.md` has five caps with a check that warns. This is exactly the boundary the harness
claims to guard and does not measure. Nothing stops the next piece from doubling that number.

Fix. `-Doctor` measures and reports the total; new cap `techoAssetsSiempreCargados` in
`comun/manifest.json`. It warns, it never blocks.

### The budget has to measure the session, not the harness

`superpowers` injects about 900 tokens per session with its `SessionStart` hook. The cap we set
ourselves is 2800, and a third party takes close to a third of it, invisible to the current
`-Doctor`.

### `SessionStart` declares a 12-line budget it already exceeds

`comun/hooks/session-start.py` opens with *"Presupuesto: 12 lineas. Se paga una vez por sesion,
pero ocupa ventana todo el rato."* Nothing measures it. Measured by hand on 2026-08-21, before
`iniciador-code` added anything, the worst case comes to **13**: the header, `git:`, «Ultimo
trabajo» with its three commits, «En la cache quedo anotado» with four items plus the «y N mas»
line, and the open pending definitions. Every one of those is reachable in a normal project.

Reproduce it with a throwaway project carrying all five sections at once — a `harness.config.json`
with `usuario` and `rutaDefinicionesPendientes`, a lockfile, a git repo with three commits, a
`CLAUDE.md` whose cache zone holds more than four lines, and a pendings file with four unchecked
boxes — then feed a `SessionStart` payload to the hook and count the lines of
`additionalContext`.

This is the same blind spot as the two items above it, one level down: a number written in a
comment is an intention, and intentions do not survive a busy week. It is what made scenario E-04
of `docs/cambios/iniciador-code/spec.md` false as first written, and the correction is recorded
there.

No `Fix.` yet, and the two obvious directions are not equivalent, so it is not this change's call
to make: either the hook trims itself to its budget — and then somebody has to decide which of the
five sections loses lines first, which is a product decision, not a defect — or the budget is
raised to whatever it actually costs and the comment stops lying. What is not defensible is
leaving a cap written down that nothing checks.

## Incomplete capabilities

### Skill routing in `UserPromptSubmit` is mute

The hook exists, it is registered and it does nothing. Its intended job was a single routing line
when the prompt matches the triggers of an installed skill.

### `iniciador-code` closed with ten scenarios unsupported

The verdict is in `docs/cambios/iniciador-code/verificacion.md`, ruled by `harness-spec-refuter` on
2026-08-21 with the suite green: **11 upheld, 0 contradicted, 10 unsupported**. Nothing behaves
differently from what the spec claims — the change is open because ten scenarios have no way to
hold, not because anything is broken.

Two of the ten are closable now and do not depend on anything else:

- **E-10 has a test that by design cannot fail.** The scenario is about the files *the walk writes*;
  the test scans three hand-written fixtures on a corpus where the spec itself declares no secret
  will ever be planted. The subject of the test is not the subject of the scenario. Either the test
  gets a subject that is actually walk output, or the scenario is rewritten to say what it really
  checks.
- **E-20 is half-covered.** It claims *"the walk **and** the notice use `docs/codebase` alike"*. The
  notice half has a test and a real red; the walk half has nothing — the agent's default is a line
  of prose. Cover the second half or split the scenario in two. It is also the only one of the 21
  missing from the spec's *"Cómo se verifica"* section, which is how it got there.

The other eight — E-07, E-11, E-12, E-13, E-14, E-15, E-16, E-17 — all need either a model-driven
walk the deterministic suite cannot invoke, or a second walk that costs another 140.000 tokens. The
root cause is one and it is written down under *Incomplete capabilities*: nothing enforces the
agent's three invariants.

Fix. Not one fix but a decision first: whether an agent's invariants are allowed to live only in
its prompt. If they are, those scenarios never become mechanical and the spec should say so instead
of listing them as verifiable. If they are not, it needs a mechanism, and that is a change of its
own.

### The agent's three invariants are enforced by nothing

Raised by `harness-spec-refuter` on 2026-08-21 while ruling on `iniciador-code`, and it is the
reason six of that change's ten unsupported scenarios cannot be verified.

`dev-iniciador-code` declares three: it does not write outside `docs/codebase/`, it does not delete,
and it never returns raw source. All three live in the prose of the prompt. The agent carries
`PowerShell` among its tools and the harness has no hook that limits where an agent writes — the
only thing `PreToolUse` blocks is secrets.

It is a free decision and no scenario asks for the opposite. What it costs is written down: E-11
(does not write outside), E-14 (does not delete) and E-16 (no source in the report) have no
mechanical form. It also showed up in the tree — commit `dd9f5bb` carries `docs/codebase/` together
with two files a person wrote, and from the repository there is no way to tell which is which.

Fix. Unknown, and the two directions are not equivalent. A `PostToolUse` check could report writes
outside the declared directory after the fact, which is cheap and late. A `PreToolUse` matcher
scoped to an agent would be a second blocking rule, and the harness has exactly one on purpose.
Neither should be picked while writing this down.

### `tests/generar-testigo.ps1` imports four modules that no longer exist

Found on 2026-08-21 by the first run of `dev-iniciador-code` over this repo — the first thing the
index paid for. Lines 30-33 and 262 `Import-Module` `Hook.psm1`, `Secretos.psm1`, `Reglas.psm1`
and `Zonas.psm1` from `comun/hooks/lib/`. All four stopped existing when the hooks were ported to
Python in 0.13.0: `ls comun/hooks/lib/*.psm1` returns nothing. The script cannot run.

It may well be deliberate — the file's own header says re-running it after the port makes no
sense, since its whole job was to capture the PowerShell verdicts that the Python implementation
is compared against, and those are already frozen in `tests/fixtures/paridad-*.json`. But nothing
in the file says it is retired, and a script that fails on its first line reads as broken, not as
finished.

Fix. Either delete it — the witnesses it generated are committed and it has no second use — or
leave a header saying it is a historical artifact of the 0.13.0 port and is not expected to run.
What is not defensible is a script in `tests/` that looks runnable and is not.

### `aporta` in every manifest is decorative — nothing reads it

Found on 2026-08-21 while building `iniciador-code`. A mutation removed `"agents": "agents"` from
`harnesses/desarrollo/manifest.json` expecting the agent to stop being installed, and the whole
suite stayed green. `grep -n "aporta" install.ps1` returns nothing: the installer never reads the
key. What it actually does is copy `<harness>/skills` and `<harness>/agents` unconditionally
(`install.ps1:1107-1108`), and the same for `checks`.

The key reads as load-bearing and is not. Somebody adding a harness will fill it in, expect it to
select what gets installed, and be wrong in a way no test catches — a directory they forgot to
declare gets installed anyway, and one they declared without creating fails silently. It is also
why `analisis` can declare `checks` with an empty directory and nobody notices, which is already
written down as a gap in `docs/mapa/mapa-harness.html`.

Fix. Two ways out and they are not the same. Either the installer reads `aporta` and copies only
what it declares — which turns a comment into a contract and needs `docs/agregar-un-harness.md`
updated to say so — or `aporta` comes out of the three manifests and the convention stays "the
directory is the declaration", like checks discovery already works. The second is smaller and
consistent with `os.walk(checks/)`; the first is what a reader of the manifest already believes is
happening.

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

### Two installer tests break versioned files, and `finally` does not survive a killed process

`tests/casos/03-instalador.ps1` covers E-20 and E-27 by appending a syntax error to a real,
versioned file — `comun/hooks/lib/zonas.py` for one, `comun/hooks/pre-tool-use.py` for the other —
running the installer against it, and restoring the file in a `finally`.

`try/finally` only unwinds inside a live process. If the PowerShell process running the suite is
killed outright — `Stop-Process -Force`, a CI timeout, an agent watchdog — the `finally` never
runs and the file stays broken in the working tree. During the `hooks-en-python` change four
agents were killed by a watchdog, so the window is not theoretical. The worst case leaves
`pre-tool-use.py` — the hook that carries the only blocking rule in the harness — with a syntax
error, and nothing detects it beyond somebody running `git status`.

Recovery, if it ever happens:

```bash
git checkout -- comun/hooks/pre-tool-use.py comun/hooks/lib/zonas.py
```

Fix. Run those two cases against a copy of the repo in a temporary directory instead of against
the working tree. It is a change to how the suite is built, not a one-line patch, which is why it
was left out of 0.13.0 rather than rushed into it.

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

Reviewed adversarially on 2026-08-17, with the burden of proof inverted — the default was that
each one comes out, and only what could not be knocked down survives. **The four survived.** The
first and the fourth close a promise the module already made, cheaply, with a test that sees the
real failure. The second is unreachable in today's code but costs nothing and changes no output.

What is still owed, and it is narrower than the original item:

- **The single-emission guard trades a noise for a silence.** If a future hook warns and then
  throws on every run, its `systemMessage` is never seen, not even once. Nothing keeps a trace of
  the discarded message anywhere.
- **Nobody checked whether `systemMessage` and `hookSpecificOutput` are allowed as sibling keys of
  the same top-level object.** If Claude Code accepts that, the right design was never "first write
  wins" — it was merging both into one JSON, and this fix should be replaced rather than kept.
- **There is no test that forces the marker write to fail** (permission denied, full disk) and
  confirms the message still went out. That path is covered by reading, not by a red.

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
