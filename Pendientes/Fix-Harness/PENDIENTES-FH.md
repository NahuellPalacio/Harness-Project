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
| 11 | The installer ships `__pycache__` | Every install carries bytecode compiled on the author's machine, and the lockfile inventory depends on whether they ran the tests first |
| 12 | `permissions.deny` hides `.env.example` from Claude | The harness ships a template into the project that the agent it serves cannot read |

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

### `CLAUDE.md`'s own budget check abstains, because the file has no zones to measure

Found on 2026-08-30 by `harness-budget-auditor`, auditing a 3-line addition (the ADR-0010 pointer).
`CLAUDE.md` carries no `<!-- ZONA ... -->` markers at all, so every line falls under
`techoFueraDeZonas` — 12 lines — and the file was already at **65** lines outside any zone before
that addition, 5.4 times the cap. `comun/checks/claude-md-zonas.py:104-106` skips the measurement
entirely when a file has no recognised zone, on purpose ("no es un error del turno: no se avisa
nada") — so nobody has ever been warned about this, and adding three more lines (68 now) changes
nothing about that silence.

The 3-line addition itself is not the defect — it is what surfaced it. The defect is that the one
check meant to catch a runaway `CLAUDE.md` cannot see a `CLAUDE.md` that was never carved into
zones in the first place. Fix unknown: either the zones get defined retroactively (a real content
decision — which of the file's sections is "fija" vs "cache" vs unzoned prose is not obvious), or
`techoFueraDeZonas` needs a meaning that holds even for a file with zero zones marked.

## Incomplete capabilities

### Skill routing in `UserPromptSubmit` is mute

The hook exists, it is registered and it does nothing. Its intended job was a single routing line
when the prompt matches the triggers of an installed skill.

### `dev-refutador` names five topics and the harness has eight `dev-*` skills

Found on 2026-08-26 while mapping which `PROJECT_CONTEXT` fields serve the refuter. The agent takes
the norm from the skills, and the sentence that sends it there enumerates:

> Invocá la que corresponda al tema que estás verificando —contrato de API, repositorio y
> entregables, identidad, pantalla, ambientes— y trabajá con lo que traiga.

Five topics. `harnesses/desarrollo/skills/` holds eight directories and three are not named:
`dev-seguridad`, `dev-versiones` and `dev-tramites-asi`. The list was never in sync: the agent and
the eight skills entered the repository in the same commit, `7db0d5c`.

A stale enumeration on its own would be cosmetic. What makes it a defect is the rule two paragraphs
below it:

> 🔴 **Si ninguna skill cubre el tema, no lo verifiques.** Decilo y seguí.

Read together, the dashes read as the catalogue and the rule turns everything outside them into
`sin-verificar`. The omission lands on **the whole ES0902** — `dev-seguridad` is the only skill that
carries it — which is at once the largest normative surface of the harness and the one where a false
`cumple` costs the most: the assessment is the gate before HML and PRD, it is redone after 20 days
of development, and G2 is the only numeric threshold the standard fixes. That is the exact failure
the agent's own asymmetry argument exists to prevent, committed by the agent. `dev-versiones` is the
second loss, and it has a mechanical check behind it (`dev-dependencias`). `dev-tramites-asi` is not
a loss: it describes how a person opens a NOC or Jira ticket, and there is nothing in a repository
to rule against it.

📌 The agent carries the `Skill` tool, so the real catalogue is reachable at runtime. Whether a
session reads the dash list as exhaustive or as an example has never been observed — `desarrollo`
was never run on a real project, which is its own entry below.

Done on 2026-08-26. The enumeration is out of `harnesses/desarrollo/agents/dev-refutador.md`:
the paragraph now says the catalogue is every installed `dev-*` skill, that it is deliberately not
listed there, and why — a list written into a prompt ages, and the rule below would turn the aged
list into `sin-verificar` over norm that was covered. No list is kept, because keeping one makes
adding a skill two edits and the second is the one that gets forgotten.

🔴 **Nothing verifies it, and it is not going to.** The subject is a run of a model, so it is
ADR-0009 territory: the suite has no way to observe whether a session reads a paragraph as
exhaustive. The agent file has no literal `dev-*` skill name in it — before or after — so a parity
test between the prompt and `harnesses/desarrollo/skills/` passes vacuously either way and would
have given a false green on the defect itself. The change is a prompt edit that leaves this entry
when the version closes; whoever writes that note says it carries no verdict.

📌 It also does not fix what is under it: **the eight skills were never used on a real project**,
so the refuter has never had to reach `dev-seguridad` for anything. That entry is below and this
change does not touch it.

### The contract calls a source `current` when its file is gone from `git ls-files`

Found on 2026-08-28 by the walker itself, during run 3 of the reading bank, and verified against
the file it wrote. `C:\Users\Asus\lecturas-0.14.0\reservas` at `084cdfa`, where the commit had just
deleted `src/legado/importador.ts`:

```
source_id : code:src-legado
location  : src/legado/importador.ts
status    : current               <- and the file does not exist
gaps_and_conflicts.stale_sources : []
git ls-files src/legado/         : 0 files
```

`componentes_y_fuentes()` (`comun/bin/contexto-armar.py:383`) stamps every card's source with
`"status": "current"` unconditionally and never crosses the card's paths against the versioned
listing — which the same script already reads, for `fuentes_de_contrato()`.

🔴 **It is structural, not incidental.** It falls straight out of invariant 3 of
`dev-iniciador-code`, the one that says a card whose module is gone gets named and left in place.
So the contract will carry a dead source on **every** project that ever deletes a module, and
`status` plus `stale_sources` — the two fields whose whole job is to say how fresh a source is —
both say the opposite of the truth. A consumer reads that path as live.

The walker did its part: it named the orphan in its report and in `indice.md`, marked. The script
is what does not notice.

Fix. Cross `location` against the versioned listing already in hand, and emit `status: "stale"`
plus an entry in `gaps_and_conflicts.stale_sources` when the file is not there. Not in the priority
table: the contract still has no reader, so nothing consumes the wrong value today.

### A `Qué falta saber` bullet that wraps to a second line enters the contract cut in half

Same run, same day, also found by the walker. On `reservas` a wrapped bullet reached the contract as
`"Express se importa en tres archivos de la API y no figura en las dependencias de"` — the sentence
stops at the line break.

`bullets_sueltos()` (`comun/bin/contexto-armar.py:215`) iterates `cuerpo.splitlines()`. The first
line matches `BULLET` and is captured; the continuation line is indented with no `- `, so it matches
nothing and is dropped without a word.

Same family as E-11b and E-11c of `docs/cambios/contexto-de-proyecto/spec.md` — prose read with a
rule meant for something else — and it survived both because **this repository writes its
`proyecto.md` bullets on one line each**. It took a walk over a foreign project to show it. That is
the argument for the reading bank, made by the bank.

Fix. Join continuation lines onto the open bullet before matching, the way any markdown list is
read. The rule ends a bullet at the next `- ` or at a blank line, not at the next `\n`.

### `architecture.important_paths[]` carries backtick spans that are not paths

Found on 2026-08-26 over the versioned `docs/codebase/project-context.json` of this repository, at
revision `5e7b443`. **52 of its 118 entries do not resolve** from the root of the repo:

```bash
python -c "import json,os; p=json.load(open('docs/codebase/project-context.json'))['architecture']['important_paths']; print(len(p), sum(1 for x in p if not os.path.exists(x.rstrip('/'))))"
118 52
```

Two shapes produce them. A range written in prose, `docs/codebase/docs.md:54`:

    - `docs/adr/0001` a `0006` y `0008` — siete archivos, sin el 0007.

Three spans and one path: `0006` and `0008` are the ends of a range. And an enumeration of siblings,
where every item after the first drops its directory — `dev-dependencias.py`, `pre-tool-use.py`,
`zonas.py`, `verificacion.md`, `SKILL.md`, `checks`.

The cause is one line, `comun/bin/contexto-armar.py:391`: the field is every backtick span of the
`## Dónde está` section of every ficha, deduped and nothing else. That section is prose written for
a person, and its spans were never promised to be paths.

Same family as E-11b of `docs/cambios/contexto-de-proyecto/spec.md` — prose read as if it were a
list of paths — caught there on `sources[].type` and not here.

What it costs: `important_paths[]` is one of the five already emitted fields that `PENDIENTES-I.md`
maps to `dev-refutador`, for stating the scope of a review instead of implying it. A scope that
names `0006` is not a scope.

Fix. Keep only the spans that resolve against the versioned listing the walk already reads for
`fuentes_de_contrato()`, and drop the rest. Deliberately not in the priority table: the contract has
no reader yet, so nothing consumes the bad values today.

### The agent's three invariants are enforced by nothing

Raised by `harness-spec-refuter` on 2026-08-21 while ruling on `iniciador-code`. Six of that
change's scenarios closed anyway — five by delegated reading under ADR-0010, one (E-12) by a
mechanical test — but the underlying gap they all sit on is not resolved by either path: nothing
in the harness enforces these invariants, only the prompt's prose does.

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

🔴 **And a `PreToolUse` matcher may not be reachable at all.** The hook contract's payload carries
`session_id`, `cwd`, `tool_name` and `tool_input` — nothing that says **which agent** is writing.
A path rule written today would land on the person's whole session, not on the walker. Whoever
picks this up starts there: either the event grows a field that identifies the caller, or the
mechanical form of E-11 does not exist and the scenario belongs in the contract group.

Same for E-16: the report is the subagent's answer, and none of the four events the harness
registers sees it. Claude Code has `SubagentStop`, which reads the transcript; that would be a
fifth hook and a change of its own.

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

## Installer defects

### `permissions.deny` blocks `.env.example`, the template the harness itself ships

`comun/settings/permissions.deny.json` carries `"Read(./.env)"` and `"Read(./.env.*)"`. The second
pattern was written for `.env.local`, `.env.production` and the rest of the family, and it also
matches `.env.example` — which is not a secret: it is the versioned template that 0.15.0 started
shipping into the root of every project that installs `desarrollo`, and it is committed on purpose
(`.gitignore` carries `!.env.example`).

The effect, found on 2026-09-14 while closing 0.15.0: Claude cannot read the file the harness left
for it. Asked "what credentials does this project expect", the agent cannot answer from the
template — it has to be told. Nothing breaks and no scenario fails; the cost is that a deliberate
piece of documentation is invisible to its reader.

Fix. Add `"Read(./.env.example)"` to an allow list, or narrow the deny pattern so it stops at the
example. The deny list has no allow counterpart today, so the narrow pattern is likely the cheaper
route: check whether Claude Code resolves a more specific allow over a broader deny before choosing.

### The installer ships `__pycache__` into the project and inventories it in the lockfile

Found on 2026-08-22 installing `-Harness desarrollo` on a throwaway clone, in order to run
`dev-iniciador-code` for real. The lockfile of the installed project carries entries like:

```
".claude\\harness\\bin\\__pycache__\\mapa-codigo.cpython-313.pyc"
".claude\\harness\\checks\\desarrollo\\__pycache__\\dev-codebase-forma.cpython-313.pyc"
```

**13 of the 50 files in that lockfile are `.pyc`** — a quarter of the inventory. `Copy-Arbol`
copies from disk and not from git, and nothing filters bytecode: on this machine `git ls-files |
grep -c __pycache__` gives **0** while `find comun harnesses -name "*.pyc" | wc -l` gives **13**,
because the suite had been run. `install.ps1` mentions neither `__pycache__` nor `.pyc` anywhere.

What is certain. **The install is not reproducible.** Installing from a clean clone and installing
from a working copy where somebody ran `Invoke-Tests.ps1` produce a different file count and a
different lockfile, from the same version of the harness. And what gets distributed is bytecode
compiled by whatever interpreter the person installing happens to have — 3.13 here.

What is a risk and was **not** observed. A `.pyc` regenerated by another interpreter, or after the
copy makes the `.py` newer than the bytecode that came with it, changes its hash — and `-Doctor`
compares lockfile hashes against disk precisely to report files edited by hand. That would be a
false positive in the tool people run to find out whether their install is sane. It did not happen
here: `-Doctor` right after installing, on the same machine and the same Python, reported *"ningún
archivo del harness fue editado a mano"*. So it is stated as a mechanism, not as a symptom.

It predates this: it has been true for every `.py` of the harness since the hooks were ported in
0.13.0. It surfaced now only because **installing is not part of the suite** — the tests exercise
`install.ps1` on a throwaway project, but nothing asserts what the inventory ends up containing.

Fix. Exclude `__pycache__` and `*.pyc` in `Copy-Arbol` (`install.ps1`), so neither the copy nor the
lockfile ever sees them. Worth a case beside it: install and assert the lockfile has zero `.pyc`
entries. The reason nobody caught this is that no test looks at what an install actually put on
disk.

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
