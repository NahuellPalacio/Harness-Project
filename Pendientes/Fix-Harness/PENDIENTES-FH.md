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
| 2 | G1 reads a leading zero or a non-ASCII digit as a canonical version | `php 08.2.30` and an Arabic-Indic `8` come out `HOMOLOGATED`. The only fail-open result in six refuter passes, and a one-line fix |
| 3 | `controles/` never reaches an installed project | Thirty-one normative controls declare `INSTALLED` and the installer never copies them: outside this repository every one of them is `CONTROL_FILE_MISSING`. Each rule installed makes this worse; D7 added six at once, D8 two and P1 five |
| 4 | `19_contexto / E-29` is not deterministic | It fired once and never again. It asserts determinism, so the one time it fires nobody can tell the finding from the flake |
| 5 | Close `integridad-de-repositorio` and `tool-builder` | They shipped in 0.19.0 with their verdict `EN CURSO`: two `sin sustento` in the first, eleven in the second |
| 6 | Review the four contract fixes on their own diff | They rode inside a port that promised not to change behaviour. Until somebody reads them alone, the promise is unverified |
| 7 | The IGE stayed on v0.9.0 | It is now four versions behind, and 0.13.0 breaks the check contract: any `.ps1` check written there stops running |
| 8 | What the checks witness never exercised | 25 branches with no test and no implementation left to compare against |
| 9 | The always loaded cost of agents and skills | The repo went from 53 to 449 tokens per turn during 0.13.0 and nothing caps it |
| 10 | The budget has to measure the session | Same blind spot, one level up |
| 11 | The four minor port divergences | None changes a verdict. Cheap to close while touching the files anyway |
| 12 | Skill routing in `UserPromptSubmit` is mute | A capability that was never built, not a defect |
| 13 | `ES0902.md` did not close as faithful | Predates all of this |
| 14 | The reviewer panel | Deferred on purpose until `desarrollo` is used on real work |
| 15 | `permissions.deny` hides `.env.example` from Claude | The harness ships a template into the project that the agent it serves cannot read |
| 16 | Neither Jira nor GitLab was ever called for real | Two adapters shipped verified against a fake transport; the first real call is what can still disprove the endpoints |
| 17 | The Ficha de Proyecto is a supposition | The whole Block 2 rests on a concept nobody has written yet in a real Jira |
| 18 | Three loadable .md files are in Spanish | ADR-0011 was broken by three files on the day it was written, and nothing measures it |
| 19 | ES0902 declares 38 controls and none of them is built | The largest declared-not-built gap the harness has had. Whoever reads "ES0902 installed" can easily read "ES0902 complied with" |
| 20 | Nothing produces the G2 severity mapping | Every real run of the acceptance threshold comes out `VULNERABILITY_RISK_MAPPING_UNRESOLVED`, so the threshold is installed and unusable |
| 21 | The shared secret catalogue misses five credential forms, and its sample leaks twelve characters | The hook shows 12 of the 20 characters of an AWS key in the transcript, and the security ledger had to grow its own redaction layer to avoid it |

Item 2 is what comes first now: it is the only place where the harness says `HOMOLOGATED` for
something the ratified rule rejects. 0.19.0 released the backlog of verdict files that had piled up
since 0.18.0; two of those changes shipped open (item 5) and G1 shipped with E-17 contradicted and
in plain sight.

🔴 Recount it, do not copy the number: `docs/cambios/*/verificacion.md` that `git ls-files` does
not know are the unreleased ones.

Item 1 is what makes a killed run dangerous, and it stays at the top
for that reason. Item 7 is not code: it is running `-Update` on a real project, and it is what tells
whether any of this works outside this repo.

📌 Two changes still have a `spec.md` and no verdict: `sdd-capacidad` and `mapa-en-la-bitacora`,
which predate the habit of writing one.

## Missing measurement

### Atomic refutation has counters and no baseline

The package asked to compare before and after: semantic refuter calls, tokens, wall and model time,
cost, cache hits and check resolutions. As of 2026-09-25 the counters exist. `refute --summary`
shows `cacheHits`, `checkResolved` and `semanticRuns`, and the Block 4 slice with
`metadata.phase = refutation`. But no measurement has been taken, neither of the old batch pass nor
of the atomic one. By the package's own rule, no performance target was set.

Fix. Measure both shapes on the same real plan, with transcripts ingested through
`contabilidad --ingerir … --refutacion REF-nnn`. Write down the numbers with their date, and only
then decide whether a target is worth having.

### The always loaded cost of agents and skills is neither measured nor capped

Measured by hand on 2026-08-14: 15 pieces, around 1540 tokens, average 103 per piece, estimating
one token every four characters of `name` plus `description`, paid on every turn. Meanwhile
`CLAUDE.md` has five caps with a check that warns. This is exactly the boundary the harness
claims to guard and does not measure. Nothing stops the next piece from doubling that number.

Measured again on 2026-09-18, after the eight agent files landed: the eight `name` plus
`description` pairs add **3175 characters, around 793 tokens per turn**, on top of what was already
there. Nothing warned, because nothing measures it. And 27 skills were installed in the same
stretch, each with its own always-loaded description, none of them counted here.

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

### Eight of the 24 ES0901 §7.1 rules are operationalized

Where this stands on 2026-09-21, written so it can be picked up cold. The rules are installed **one
at a time**, each from its own governance package — the request arrives as a
`prompt-install-dN-governance.md` plus the `dN-*.md` artifacts of its signal, policy and
check/review.

```
G1  approved technologies        2 policies + 2 checks   spec.md, NO verificacion.md
G2  industry good practices      1 policy  + 1 review    spec.md, NO verificacion.md
D1  citizen authentication       1 policy  + 1 check     31 upheld, closed
D2  credential delegation        1 policy  + 1 check     31 upheld, closed
D3  object-oriented design       1 policy  + 1 review    28 upheld, closed
D4  responsive behaviour         1 policy  + 1 check     31 upheld, closed
D6  georeferenced visualization  1 policy  + 1 check     31 upheld, closed
D5  cadastral normalization      1 policy  + 1 check     37 upheld, closed
```

Eighteen controls installed of the 36 policies, 34 checks and 2 reviews the matrix declares. Six of
the fourteen signals have a producer: `citizenFacing`, `authenticationPresent`,
`applicationCodePresent`, `frontendPresent`, `georeferencedVisualizationPresent`,
`frontendAddressInputPresent`. Nobody collects the evidence for any of them yet, so a real WorkUnit
still resolves almost every conditional rule as `APPLICABILITY_UNRESOLVED` — that is the honest
state, not a defect.

**Eight rules have all of their declared controls built: G1, G2 and D1 to D6.** The other sixteen
still declare controls that do not exist, and that is the normal state of a one-rule-at-a-time
rollout — their packages have not arrived. 🔴 Do not restate this as *no rule is left with declared
and unbuilt controls*: that claim was written twice while installing D5 and it is false. Twenty-four
rows, eighteen controls.

D5 was installed last, out of order: its package arrived on 2026-09-20 and D6's on 2026-09-21, and
D6 went first because it does not depend on D5. D5 was the only rule whose package had arrived and
was not installed, and it left two green assertions in D6 that had to be rewritten —
`31_d6 / E-26` and the control count in `31_d6 / E-30`. That was deliberate and it worked: whoever
installed D5 had to change a passing test.

🔴 **G1 and G2 were never refuted.** They have `spec.md` and no `verificacion.md`, and every rule
after them builds on them — D3 extended `revisiones.py`, which G2's scenarios cover. That is item 4
of the table above, and it is now the only change in the repository without a verdict.

The cycle every closed rule used, and worth keeping: spec with `E-nn` scenarios mapped to the
request's `Dn-nn` → build → tests → a deliberate mutation pass for the `rojo visto` mark → verdict
from `harness-spec-refuter` → `verificacion.md`. **None of the five closed on the first verdict.**
D4 needed three passes and D6 needed three; Block 4's E-37 needed six. Every one of those passes
found a test that was green while proving something adjacent to its scenario — and twice, in D6 and
in Block 4, a pass found a defect *introduced by the fix from the pass before*.

### The tool-builder change is half built and its spec says so

`docs/cambios/tool-builder/spec.md` has 37 scenarios. Twenty-six carry `rojo visto: si` — the tool
contract, the Tool Registry, the lifecycle, the versioning and the secret handling, all covered by
`tests/casos/21_tools.py`. Eleven are still `no consta`:

```text
E-12 .. E-16   the two gates: tool risk, separate from model cost
E-32           the non-sensitive execution trace
E-33           TOOL_BUILD_CAPABILITY_GAP: no recursive tool building
E-34, E-35     a CHECK_GAP does not reach dev-tool-builder; no policies, no checks
E-36           agents/dev-tool-builder.md is in English
E-37           a real run of the agent  · verificación: lectura
```

E-36 is the cheap one and it is already true: the agent file landed on 2026-09-18 with the other
seven specialists, in English. It has no test, so the mark stays honest at `no consta`.

Refuted on 2026-09-22: 26 sostenidos, 11 sin sustento — exactly these eleven, and nothing else.
`docs/cambios/tool-builder/verificacion.md` records it and says `EN CURSO`. The code shipped in
0.19.0 declared open.

Fix. Build the two gates in `consumo.py` — the tool-risk gate lives beside the model gate and
neither covers the other — then the trace and the limits. E-37 needs `write-a-lectura` and a person
who is not whoever built it.

### G1 reads a leading zero or a non-ASCII digit as a canonical version

Found on 2026-09-22 by `harness-spec-refuter` in the sixth pass over
`docs/cambios/g1-tecnologias-homologadas/`, and the reason E-17 closed contradicted. The ratified
order of evaluation says form first: what is not written the way Annex II writes it is
`UNRESOLVED`. The number does not obey it:

```
php '08.2.30'           HOMOLOGATED    matched 8.2.30
cib-seven '01.1.0 CE'   HOMOLOGATED    matched 1.1.0 CE
oracle '019c'           HOMOLOGATED    matched 19c (LTR)
php '٨.2.30'       HOMOLOGATED    Arabic-Indic 8
php '８.2.30'       HOMOLOGATED    full-width 8
```

`_NUM` and the numeric part of `_CON_CALIFICATIVO` in `harnesses/desarrollo/bin/orquestacion/anexo2.py`
use `\d+`, which in Python takes leading zeros and any Unicode digit, and `_tupla` converts them
with `int()`. The service pack is already closed with `(?:0|[1-9]\d*)`.

Three smaller things from the same six passes, none of which homologates: the spec does not say
which uppercase word counts as an edition (`cib-seven 1.1.0 ABC` gives `NOT_HOMOLOGATED`, `jws 6.0 SP`
gives `UNRESOLVED`), nor what a different suffix in the same branch is (`oracle 19d`), nor how many
components a number has (`php 8.2.30.0` homologates through the patch rule). "An earlier service
pack gives `NOT_HOMOLOGATED`" is ratified and tested only with `SP0`, a builder decision, because
the catalogue lists nothing but `SP1`. And `technology-version-compliance.py` was edited by the
backend engineer, who flagged that a `checks/` directory is the hook engineer's.

Fix. Bound every numeric component to ASCII `(?:0|[1-9][0-9]*)` and assert the five lines above as
`UNRESOLVED`, each seen red. Then a spec-author decision on the three silent cases.

### Three domains route to a blank agent, in silence

Found on 2026-09-17 while removing the `dev-integration` agent. A work unit whose domain has no
`SPECIALIST_AGENT` declared comes out with `assignedAgent: ""`, `agentExists: false`, **no warning
at all**, valid against the schema, and the plan reaches `READY_FOR_EXECUTION`.

Reproduced with `orchestration`, which is in that situation today along with `tooling` and
`refutation` — the three non-specialist domains of `CONTEXTO_POR_DOMINIO` in `plan.py`. An agent
declared and missing is a reported gap; an agent that was never declared for the domain is a blank
string nobody sees.

```python
agente = str(propuesta_unidad.get("assignedAgent") or roster.agente_de_dominio(dominio))
```

Fix. Either those three domains get their declared owner in `agent-registry.json`, or an empty
`assignedAgent` becomes a gap like any other. The second is cheaper and closes the class, not the
three cases.

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

### A declared accounting field can carry a sensitive fragment that no catalogue recognises

Block 4's ledger cannot hold a conversation: `eventos.CLAVES_DE_METADATA` closes `metadata` to
seven keys, `eventos.ESCALARES` forbids a nested object or a list inside any of them, and
`libro.TOPE_DE_TEXTO` trims every string in the event at 300 characters. The ceiling is seven flat
fields by 300 characters, with no turns and no growth.

What it does not stop is a fragment. `metadata={"reason": "la base esta en 10.20.30.40"}` is
written verbatim. `contexto/limpieza` only redacts high-confidence patterns — a deliberate Block 2
decision, because a false positive that mutilates a text is worse than a warning and there is
nobody to ask — and an internal IP, a hostname or a person's name is not one of them.

Verified on 2026-09-20 while closing Block 4. It is asserted **green** in
`tests/casos/30_b4_contabilidad.py::test_e37_el_libro_no_guarda_ni_prompts_ni_secretos` so that
whoever closes it has to change a passing test and talk about it first.

Fix. Not obvious, and it belongs to Block 2 rather than Block 4: either a medium-confidence pass
that only applies inside `.claude/runtime/`, where there is no prose to mutilate, or a rule that
`reason` is built from a closed vocabulary of phrases instead of free text. The second is cheaper
and narrower; it costs the ability to explain an unusual correction in words.

### Block 4 has thirteen event types and only one producer

`eventos.TIPOS` declares the full lifecycle — `TASK_STARTED`, `WORKUNIT_STARTED`,
`AGENT_RUN_STARTED`, `TOOL_CALL_COMPLETED` and the rest. The only thing that emits events today is
a provider adapter reading a transcript, which produces `MODEL_CALL_COMPLETED` and
`SESSION_COMPLETED` and nothing else.

The consequence is not cosmetic: attribution by work unit and by agent comes from fields the
adapter cannot know, so on any real run `WORKUNIT_ATTRIBUTION_UNRESOLVED` and
`AGENT_ATTRIBUTION_UNRESOLVED` are the normal answer, and the per-agent and per-work-unit tables of
`execution-cost.md` are empty unless somebody passes `--unidad` and `--agente` by hand.

This is written down in the spec under `Qué queda afuera` with its reason — Block 3 builds a plan
and executes nothing, so there is no executor to emit them — and it is here so it is not read as a
defect of Block 4 when the executor arrives.

Fix. Whoever builds the block that executes a work unit calls `libro.agregar` at the lifecycle
boundaries. Nothing in Block 4 changes; the contract is already there.

### `.claude/runtime/accounting/` grows and nothing prunes it

One directory per task, three files each, forever. No retention, no rotation, no size cap. A
project with a thousand tasks has a thousand directories, and `-Update` and `-Uninstall` both
preserve them on purpose — losing accounting evidence to an upgrade would be worse.

Fix. A `--podar` on `dev-harness.py contabilidad` that drops the `ledger.jsonl` of tasks closed
more than N days ago while keeping `summary.json`, which is the part anyone reads afterwards. The
number comes from whoever has to answer for the spend, not from here.

### A whitespace-padded `sourceType` lowers a FAIL to a PARTIAL and erases the trail

D6's check normalizes every **identity** field with `declarado()` — provider id and reference,
contract id and reference, view id, the provider a view declares and the one a run reports. The
enumerated fields are read raw on purpose: `source`, `execution`, `mode`, `buildId`, `runtime`,
`evidenceId` and `sourceType`.

Six of the seven err toward not approving. The seventh loses information. Found by
`harness-spec-refuter` on 2026-09-21:

```
sourceType = "RENDERED_MAP_RUN " (trailing space) and the run reports another map
  -> PARTIAL / RENDERED_EVIDENCE_MISSING, and "otro-mapa" appears in no field of the output
  -> with the exact sourceType: FAIL / ALTERNATE_MAP_PROVIDER
```

It is the same **shape** as the E-18/E-19 defect that shipped and was fixed the same day, one field
outside the normalized list.

Fix. Not obvious, and both positions defend themselves. Normalizing the enum fixes it. Leaving it raw
makes a malformed evidence class visible, which is the check's own doctrine — evidence that does not
prove sustains nothing. It needs a scenario in the spec before anything is built; the change closed
without one deliberately.

### D5's integration contract cannot be resolved in any project today

Recorded on 2026-09-21 while installing D5, and it is the mirror image of D6's provider gap rather
than the same one, so it is worth stating precisely.

```
D6   which mechanism is the GCBA Map        in no extract this harness holds
D5   which service is the cadastral option  named on page 19 of ES0901
D5   what using it looks like               in no extract this harness holds
```

So a project **can** resolve D5's provider identity: the Georreferenciación paragraph names a catalog
service, it is transcribed in `normativa/extractos/ES0901.md:461`, and a project that cites it has a
defensible `GCBA_NORMATIVE` source. What no project can supply is the contract — the harness holds no
endpoint, no request or response field, no cadastral identifier, no coordinate field, no
authentication method and no timeout, and inventing one would read as though the standard required
it.

Effect: every real run of `address-normalization-integration` today answers
`INTEGRATION_CONTRACT_MISSING`, which is correct and also means the check will not be exercised end
to end until somebody obtains that contract. It is the same shape as D6's provider gap and it is not
a defect in the check.

🔴 Do not close it by writing a plausible contract into the policy. `D5/E-13` sweeps six artifacts
for exactly that and will catch it — but the sweep permits the **quoted** name of the service,
because a quote is not an invention, so the line between the two is narrower here than in D6.

Fix. Get the contract from the ASI or from a project integration agreement and declare it as data,
with its source. Nothing in this repository changes.

### D5's run evidence proves without a reference or a claim, and its policy lists other names

Two loose ends from D5's second refutation on 2026-09-21. Neither contradicts a scenario and neither
leaks a `PASS`; both are the kind of thing that only shows up when somebody compares two artifacts
of the same change.

**One.** `address-normalization-integration` accepts a `NORMALIZED_ADDRESS_RUN` whose `reference` and
`claim` are both blank, and proves with it. The signal module has enforced the opposite since D1
(`senales._utiles`: *"las evidencias que referencian algo y afirman algo. El resto no cuenta"*), and
the policy of D5 lists both fields under *Evidence it requires*. The check never asks. Repro: take
the happy case and blank `reference` and `claim` on the run evidence — still `PASS`.

**Two.** The policy declares eight `Outcomes` — `SATISFIED`, `NON_COMPLIANT`, `NOT_APPLICABLE`,
`APPLICABILITY_UNRESOLVED`, `EVIDENCE_INCOMPLETE`, `ADDRESS_FLOW_COVERAGE_UNRESOLVED`,
`CADASTRAL_PROVIDER_UNRESOLVED`, `INTEGRATION_CONTRACT_MISSING` — and the check produces nine states
with partly different names. `D5/E-30` checks the check's nine; nothing compares the two lists.
`SATISFIED` and `EVIDENCE_INCOMPLETE` are never produced by anything, and `PASS`/`FAIL`/`PARTIAL`
appear in no policy. The same mismatch exists in D1, D2, D4 and D6 — the shape came from the
governance packages, which write policy outcomes and check states as two vocabularies.

Fix. The first is three lines in the check plus a scenario. The second is a decision, not a bug:
either the policies adopt the check's states, or a mapping is declared and verified once for all six
rules. It is worth one change that touches the six together, not six patches.

### D5's cadastral sweep cannot be widened beyond its six artifacts

Recorded on 2026-09-21. `32_d5 / E-13` sweeps six texts for an invented integration contract, and
the subject is deliberately narrow: the policy, the check, the two registry rows, the D5 matrix row,
the whole matrix, and the two D5 sections of `docs/normativa-7.1.md`.

It cannot be widened to the rest of the repository, and that is not a defect of the sweep:

```
normativa/extractos/ES0901.md   transcribes real URLs from the standard, and "port: 8080"
docs/secretos.md                is about secrets: it says `password = ${DB_PASSWORD}`
docs/contrato-hooks.md          measures latency: "260 ms"
```

The three are legitimate and the sweep fires on them. Widening the subject needs per-document
exemptions, and an exemption list is the thing that ages worst. The three patterns that fired on
**ordinary Spanish prose** were tightened on the same day — a time written in words, a locator key
whose value is a sentence, and `9001` colliding with ISO 9001 — because that is the risk that
actually grows as D5's own artifacts grow. Six legitimate prose forms are pinned green against
exactly that.

### D5 cannot tell a consumed raw value from a consumed normalized one when the provider echoes it

Recorded on 2026-09-21, pinned **green** in `tests/casos/32_d5_normalizacion_catastral.py::test_e22…`
so that closing it forces a conversation.

`address-normalization-integration` decides whether the normalization was consumed by comparing
opaque tokens: `CONSUMED_VALUE` against `NORMALIZED_RESULT` and against `RAW_INPUT`. When the
provider returns exactly what the person typed, all three tokens are equal, and *consuming the raw
value* and *consuming the normalized one* become indistinguishable. The result is `PASS` carrying
`NORMALIZATION_INDISTINGUISHABLE` in `issues`.

That is deliberate. Lowering it to `PARTIAL` would turn every project that validates an
already-normalized address red, and a check that goes red for no reason is a check somebody switches
off. But it does leave a shape a fabricated run could exploit: declare `RAW_INPUT` and
`NORMALIZED_RESULT` as the same token and the raw-value guard cannot fire.

Reproduce it: take the happy case and set `chain.RAW_INPUT == chain.NORMALIZED_RESULT ==
chain.CONSUMED_VALUE`. The state is `PASS` and the only trace is the issue string.

Fix, if it is ever worth it. The discriminator would have to come from outside the token comparison
— the provider response declaring whether it changed the input, or the run declaring both the
pre-call and post-call persisted values under different identities. Both need contract evidence the
harness does not have, which is the item above. Until then the residue is visible and asserted, not
hidden.

### One absurd number from a provider aborts the whole accounting ingest

`eventos.validar` rejects any number over 18 digits, which is what stops a conversation encoded as
an integer from reaching the ledger. But `adaptadores/contrato.a_eventos` builds every event in a
loop and lets `EventoInvalido` escape, so a single bad record kills the run: nothing is written,
including the hundreds of records that were fine.

Reproduced on 2026-09-20 by `harness-spec-refuter` with a transcript carrying
`"input_tokens": 10**30`. It is not reachable from a real Claude Code transcript today — the field
is an int the provider computes — but a future provider, a corrupted file or a truncated write
makes it reachable, and the failure mode is the worst one: total loss instead of partial.

It also contradicts the doctrine the block already states twice. `libro.leer` tolerates a broken
line on purpose — *"un libro con una linea corrupta sigue siendo la mejor fuente que hay"* — and
the whole block is built on *what is missing is not zero, it is unresolved*.

Fix. `a_eventos` catches `EventoInvalido` per record and emits `contrato.sin_resolver` in its
place, so the record becomes `USAGE_UNRESOLVED` with its reason instead of taking the ingest down.
Needs a scenario in the spec before it is built — the change closed without one, deliberately,
rather than shipping behaviour no test covers.

### Four holes in Block 4's invariant sweeps, all of them shapes nobody writes today

Found by `harness-spec-refuter` on 2026-09-20, after the sweeps were already raised once. None of
them is reachable by the code as it stands; all four are ways a future edit could slip past a
guard that is otherwise an invariant.

```
E-03  the destructive-verb sweep covers the eight operations the spec enumerates.
      Path(ruta).write_text("") and shutil.copyfile(x, ruta) are not among them.
E-13  a rate written as a string -- {"input": "3.0"} -- is not a number, so the
      container sweep does not see it. Same for a scalar constant outside a container.
E-28  _aperturas() reads the AST for open/io.open. Path(ruta).read_text() is neither.
E-32  a provider name split across two concatenated strings, or written with no
      separator at all -- "CLAUDECODE" -- passes. No text sweep can catch the first.
```

Fix. For E-03 and E-28, sweep `pathlib` usage too, or assert the package never imports `pathlib` —
it does not today, and that assertion is cheaper and harder to weaken. For E-13, widen the
container sweep to numeric strings. E-32's concatenation case is not fixable by any text sweep and
should be written down as such rather than chased.

### Three evidence helpers are now copy-pasted across three normative checks

Found on 2026-09-21 while installing D8. The same three helpers exist three times, written
independently and already drifting in their names:

```
declarado / declarado            strip a declared value, so a blank is not a declared datum
_de_esta_corrida                 bind a piece of evidence to the build and runtime under test
_evaluar/_usables/usables        resolve evidence references into used / orphan / out-of-build
```

They live in `controles/checks/gcba-map-usage.py` (D6), `controles/lib/flujos.py` (D7),
`controles/checks/service-token-protection.py` (D8) and
`controles/checks/framework-homologation.py` (P1). The D6 and D7 copies were verified
separately, and each one carries the lesson of the bug that produced it — D6's `declarado` has a
four-line comment about normalizing both sides of a comparison that the other two copies do not.
That comment is exactly what gets lost when a fourth rule copies the nearest version.

The counting, on 2026-09-22: about 60 lines repeated **four** times, and the next rule makes it
five. `descubrir_no_declarados` only scans `controles/policies` and `controles/checks`,
so a shared module under `controles/lib/` is not reported as an undeclared control — which is why
D7 could put `flujos.py` there in the first place.

Fix. Move the three into `controles/lib/evidencia.py` and have the four checks import it, keeping
the comments of the strictest copy. It is behaviour-frozen work for `harness-staff-engineer`: the
four changes are already verified, so the fence is that `31_d6`, `34_d7`, `35_d8` and `36_p1` stay
green without editing a single assertion. Doing it inside a rule installation was refused on purpose —
it would mean touching two verified changes from inside a third.

### The plan schema does not close its root

Found on 2026-09-22 while verifying `matriz-normativa`: a `normative` block added at the root of an
`OrchestrationPlan` still validates against `comun/schemas/orchestration-plan.schema.json`. Only the
new assertion of `23_matriz_normativa / E-23` catches it.

Fix. `additionalProperties: false` at the root of the plan schema, after checking nothing writes
an extra root key today.

### G2's reuse of G1's inventory is an instruction, not a fact

`docs/cambios/g2-buenas-practicas/` E-20 was narrowed on 2026-09-22: nothing produces G1's
inventory, so "the inventory is reused" could not be tested. What the test holds is structural — by
AST, `revisiones.py` opens no file but its schema and defines no detector. Two holes the refuter
named: a read at module level, outside any function, and a `subprocess` call both pass.

Fix. When something produces the inventory, test the real path. Meanwhile, extend the AST sweep to
module level and to `subprocess`.

### `descubrir_no_declarados` never looks inside `controles/reviews/`

Found on 2026-09-22 by `harness-spec-refuter` while verifying ES0902 O1.
`controles.descubrir_no_declarados` — `harnesses/desarrollo/bin/orquestacion/controles.py:191` —
walks two directories, `controles/policies/` for `.md` and `controles/checks/` for `.py`.
`controles/reviews/` is not one of them, and it now holds three files:
`object-oriented-design-review.md`, `technology-practice-review.md` and
`gcba-it-security-normative-review.md`.

The consequence is narrow and real: a review document dropped into that directory and never
declared in `control-registry.json` does not show up in `reporte()["undeclared"]`, and
`filesystemClean` stays true. Every scenario that leans on "no stray files" — `36_p1/E-39`,
`35_d8/E-37`, `39_es0902_o1/E-28` — covers less surface than it sounds like it does. Nothing is
wrong today: the three reviews that exist are declared and report `INSTALLED`.

Fix. Add the third directory to the walk, with `.md` as its extension, the same way `policies` is
already handled. It is the same loop; what it needs is the third pair.

### The six managed sources have no accepted hash, so none of them can ever be current

Written on 2026-09-23, when `source-registry.json` shipped with `conocimiento-fuentes-y-frescura`.
All six entries carry `sha256: null`, because the original PDFs are gitignored —
`normativa/fuentes/` holds only its `LEEME.md` — and this machine does not have them. Freshness
resolution is honest about it and fails closed: without an accepted hash there is nothing to
compare an observed document against, so every source resolves to `FRESHNESS_UNVERIFIED` and none
can ever reach `CURRENT`. `dev-harness.py fuentes` says so on every run, six times.

This is the designed behaviour, not a defect in the resolver. What is open is that nothing closes
it: there is no command yet that accepts an original and writes its hash into the registry.

Fix. It belongs to the decisions slice — `conocimiento decidir <source> aplicar` — which is what
turns an observed original into an accepted one. Until that exists, a hash can only be written by
hand, and writing it by hand without the file in front of you is exactly what the registry exists
to prevent.

### `normativa/` never reaches an installed project, so every source there declares a missing extract

Written on 2026-09-23. `source-registry.json` points each source at `normativa/extractos/<id>.md`,
and `normativa/fuentes/LEEME.md` states the folder is the factory's: it is never copied to a
project and no hook, check or skill opens a PDF at runtime. So inside this repository the six
extracts resolve, and in an installed project `registro_fuentes.ruta_de_extracto` returns `None`
for all six, `validar` reports `SOURCE_EXTRACT_MISSING`, and freshness cannot establish the fourth
condition for any of them.

It is the same class as `controles/` never reaching an installed project, and it deserves the same
decision: either the knowledge subsystem is factory-only for `norma` sources — and the installed
harness says so instead of reporting six missing extracts — or the extracts travel with the
install. Nothing chose yet.

### Four source states and the postponement logic are built and no scenario refutes them

Written on 2026-09-23, from the verdict of `conocimiento-fuentes-y-frescura`. The contract
`sources-state/1.1` declares twelve states; the spec's scenarios exercise eight. `NEW_SOURCE`,
`RETIRED`, `ACKNOWLEDGED_PENDING` and `KNOWLEDGE_PROMOTION_INCOMPLETE` are reachable in
`frescura._estado_de` and `frescura._pospuesta` — which also decides that a postponement never
covers an integrity alert or a regression — and not one scenario names them. The refuter flagged
it as a free decision, not as non-compliance: it is code ahead of its scenarios.

Fix. The decisions slice covers `ACKNOWLEDGED_PENDING` and the postponement rules; the promotion
slice covers `KNOWLEDGE_PROMOTION_INCOMPLETE`. `NEW_SOURCE` and `RETIRED` need a scenario of their
own wherever they land — they are one line each and they are the two that nothing else will pick
up.

### The shared secret catalogue misses five credential forms, and its sample leaks twelve characters

Found on 2026-09-23 while building `reporte-de-seguridad`, and confirmed by the refuter's probes on
the same day. `comun/reglas/secretos.patrones.json` does not recognise:
- an Anthropic key (`sk-ant-…`);
- a `JSESSIONID=` or `sessionid=` cookie;
- a `Bearer` token without an `Authorization` header before it;
- the body of a PEM private key. Only the `BEGIN` line is redacted.

Separately, `comun/hooks/lib/secretos.py::muestra_segura` keeps the first 12 characters of the
match in the text it writes. For a 20-character AWS key (`AKIA…`), that is 12 of the 20. The sample
goes into Claude's context and into the transcript. Through `contexto/limpieza` it also reaches
Block 4's `ledger.jsonl`. Both defects reach the hook, the `OrchestrationPlan` and the accounting
ledger. `reporte_seguridad/libro.py` covers them for the security ledger only, with a local pattern
layer and a trimmed sample, so today there are two redaction layers that can diverge.

Fix. Add the five forms to the catalogue at high confidence. Make `muestra_segura` show the
pattern id and the length, never characters of the value. Then drop the local layer in
`reporte_seguridad/libro.py`, or reduce it to what the catalogue cannot express. Owner:
`harness-hook-engineer`, since it changes what `pre-tool-use` reports.

### The security ledger's password rule leaves four forms out, and its temp file can stay behind

Found by the refuter's final pass on `reporte-de-seguridad`, on 2026-09-23. The rule of E-03b
recognises a password by the keyword and redacts the first value on the same line. By the rule's
own letter these four still reach `security-ledger.ndjson` raw:
- `PASSWORD=` with the value on the next line. The second pass redacted it, so this is a
  regression in behaviour even though it does not break the letter.
- `password='He said \'x\' value'`. The value ends at the first quote, so only "He" is redacted.
- `Bearer:value`, with a colon.
- A PEM body with no `BEGIN` header.

E-03b declares that a syntax outside the rule is a catalogue item, not a contradiction of E-03.
That narrows what E-03 covered with "una contraseña", and it was left visible on purpose.

Separately, `reporte_seguridad/archivo.escribir_atomico` creates its temp file with
`tempfile.mkstemp`. If the write fails, the temp file stays in the folder, because the package has
no verb that deletes. That absence is what E-01 asserts.

Fix. The first two forms belong in the local rule: let the value continue on the next line after a
bare `=`, and honour escaped quotes. The last two belong in the shared catalogue item above. For
the temp file, removing the package's own freshly created temp name on failure does not reopen
E-01, but it has to be argued in the spec before it is written.

### ES0902 Vu5 rule 5 lets a block hide a later step's own unresolved state

Found by the refuter's second pass on Vu5, on 2026-09-24, with no scenario naming it. The case is a
mapped validation with `enforcementStatus: PRESENT` and `parity: UNRESOLVED` declared, whose only
server evidence is a cited unsafe test (`environment: PRD`). Step 2 finds no support and returns the
block's state, so the reported state is `SERVER_VALIDATION_TEST_UNSAFE`, and step 3's
`VALIDATION_EQUIVALENCE_UNRESOLVED` only shows in `states[]`. Rule 5 of the spec says the opposite:
a block never replaces an earlier-step unresolved, and step 3's unresolved has nothing to do with
the test. PASS stays impossible, so no verdict moves.

Fix. In `controles/checks/client-server-validation-parity.py`, return the block's state from a step
without support only when no later step has its own unresolved state. Add the case to E-69.

### Nobody knows since which Claude Code version a hook's `shell` field exists

Found on 2026-09-24 while fixing the hook registration (`docs/cambios/hooks-con-shell-powershell/`).
Every hook in `settings.json` is now registered with `"shell": "powershell"`, and the three manifests
still say `requiereClaudeCode: 2.1.0`. A Claude Code that predates the field ignores it and runs the
PowerShell command in its default shell, Git Bash where it exists, where it fails the other way
round (the spec's first known risk).

Evidence: the hooks documentation describes `shell` without saying when it appeared; the
downloadable changelog covers only 2.1.273 to 2.1.281 and does not mention it; the registration was
proved by hand on 2.1.281 only. `requiereClaudeCode` was left as it is on purpose, because raising it
to 2.1.281 would lock out every older machine without knowing that it has to.

What is missing is a fact, not a design: the first version with `shell`. It has to come from an
older changelog or from Anthropic, and until then there is no version to write.

### `evento=harness.listo` is emitted in every state, including PARTIAL and BLOCKED

Found by the refuter's first pass on `bloque-1-bienvenida`, on 2026-09-24. `dev-harness.py` ends
every `setup`, `estado` and `reconfigurar` run with `evento=harness.listo disponibles=<n>`, whatever
the resolver says. Since that change the human `Estado` section of `setup` prints the resolver's line
(`Harness GCBA ◐ PARCIAL · ...`), so a run with Jira down now says PARCIAL in the text and `listo` in
the event right above it. E-21 excludes `evento=` lines on purpose, because they are the stable
telemetry of `integraciones-bootstrap` and not text for the person.

Why it matters. Anything that reads the event log (a script, a future bitácora consumer, a person
grepping) reads "ready" for a harness the resolver calls PARTIAL or BLOCKED.

Fix. It is a change to `integraciones-bootstrap`, not a code tweak: either rename the event (for
example `harness.bootstrap.fin`) or add the resolver status to it (`estado=PARTIAL`). Both change a
stable event, so the spec of `integraciones-bootstrap` has to be amended first, with a scenario, and
`18_integraciones` updated alongside.

### The Context Bar shipped with six loose ends the refuter found outside the letter

Found by the refuter on `bloque-1-context-bar`, on 2026-09-24. None contradicts a scenario, and each
one is visible to a person using the bar:
- **Without Git Bash, the bar counts as tested with PowerShell alone.** The spec says the installer
  runs it under `bash -c` and `powershell.exe`. The schema's description of `commandTested` claims
  both ran, and in that case it is not true.
- **The 1.1 schema adds fields the package does not have.** `commandTested`, `fingerprints` and
  `lastSessionId` are new, and `reloadRequired` and `activeInCurrentSession` are now required.
  The spec declares only the flattening, `pendingConditions` and `upgradeFrom`.
- **An empty ledger leaves `block4: OK` and the bar `ACTIVE`,** while the line says "sin datos del
  Bloque 4". The package asks for `BLOCK4_SOURCE_UNAVAILABLE` when Block 4 is not initialised.
- **A project path with an apostrophe** leaves the bar `INSTALLED`, because no quoting works in both
  shells. `describir` recommends `install.ps1 -Update`, which does not fix it.
- **Hand-edited files.** `install.ps1` registers the bar (around line 1891) before it restores
  hand-edited files (around 2021). If a new version bumps `INTEGRATION_VERSION` and the person's copy
  keeps the old one, no heartbeat can ever prove the reload, and `RELOAD_REQUIRED` stays forever.
  Read from the code, not executed.
- **`-Uninstall` leaves `.claude/runtime/contextbar.json` and `accounting/` behind.**

Separately, `tests/medir_barra.py`, and therefore `-Doctor`, launches the renderer directly, without
a shell. Measured by the refuter on 2026-09-24, PowerShell adds about 180 ms on top: 103 ms direct,
149 ms under bash and 282 ms under PowerShell. That leaves about 370 ms with one message per draw,
close to the 400 ms budget and out of sight.

## Installer defects

### The installer tests fail at random under load, and the python test counts drift

Found on 2026-09-22 while installing the repository-integrity capability. Right after a mutation
pass — 49 subprocess suites, thousands of `__pycache__` directories created and deleted — the gate
came back with seven failures, all of them in the PowerShell installer cases:

```
[Instalador - el indice del codigo]     -Uninstall sale con codigo 0   esperado <0> / obtenido <1>
[Instalador - el contrato del contexto] instalar desarrollo sale con codigo 0  esperado <0> / obtenido <1>
[14-contexto-instalador] No se pudo encontrar 'harness.lock.json'
```

Running `install.ps1` by hand with the exact arguments of the failing case returned **0**, and the
next full gate run — with the same tree — returned `24061/24061`. So the installer is fine and the
cases are not deterministic: they shell out to `powershell.exe -File install.ps1` into `%TEMP%` and
something under load (antivirus lock, temp contention) makes a run exit 1.

🔴 The cost is not the red: it is that a gate which fails at random teaches people to re-run it, and
a re-run that goes green hides the failure that was real. This nearly happened here — a bisection
pointed at the new files and was wrong.

A second, smaller symptom of the same family: **the python test counts drift between runs of the
same tree** — `33_bases_de_datos` reported 3565, 3586 and 3604 in three consecutive runs, and
`30_b4_contabilidad` 793, 795 and 796. A test that emits a variable number of assertions over a
fixed tree is measuring something that is not the tree.

🔴 And the same day, a third symptom that names the cause out loud. `19_contexto` E-29 —
*"dos resoluciones de los mismos datos dan el mismo hash; el reloj no cuenta"* — failed once with
two different `context_hash` values for the same input, and then passed three consecutive runs on
the untouched tree. The test's own title states the invariant that broke: **the clock counted.**
Whatever leaks time into `context_hash` is almost certainly the same thing drifting the counts, so
the two should be chased together.

Fix. Two separate pieces. For the installer cases: retry the subprocess once on a non-zero exit
before asserting, or serialize them behind a lock, and print the installer's own output on failure
so the next person does not have to reproduce it by hand. For the drifting counts: find what varies
— a timestamp, a directory listing, a clock — and pin it; the exact-count assertions of the control
registry already show the shape of the fix.


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

### `controles/` never reaches an installed project

Found on 2026-09-19 while building D1. `install.ps1:1155-1161` copies a hardcoded list per
harness — `checks`, `bin`, `reglas`, `skills`, `agents` — and `controles/` is not in it. The
directory was born with G1 and holds the normative controls: **sixteen policies, thirteen checks and two
reviews** today (`harnesses/desarrollo/controles/`), thirty-one in all. It was four, three and one
when this was found; every rule installed since has made it worse, and D7 added six at once — the
largest single jump. D7 also added `controles/lib/`, which holds no control and is not copied
either, so its three checks would fail to import outside this repository.

The effect is invisible in this repository and total outside it. `controles.py` resolves a control
file against `roster._dir_del_harness`, which in an installed project points at `.claude`; nothing
was copied there, so every declared control resolves to `CONTROL_FILE_MISSING` and
`controles.reporte()["result"]["registryValid"]` goes false. Here the suite is green because the
factory reads the repository tree. `G1`, `G2` and `D1` all ship a control registry that says
`INSTALLED` and an installed project where nothing is.

Reproduce it: install `desarrollo` into an empty project and look for
`.claude\harness\controles\` — it is not created, and neither is `.claude\controles\`.

Fix. Two decisions and they are not independent. First, where the controls live once installed:
`.claude\harness\controles\<id>\` follows what `checks` already does and keeps the harnesses
apart, and then `controles._ruta_de` needs the same second candidate that `roster.existe_check`
already carries for `harness/checks/<id>/`. Second, whether the copy is added to the hardcoded
list or the list is replaced by reading `aporta` — which is the item above, and doing this one by
hand makes that one a little worse. It needs its own spec: it touches `install.ps1`, `controles.py`
and a new installer case.

### ES0902 C2 leaves four identity and freshness choices as the spec wrote them

Found on 2026-09-23 by `harness-spec-refuter`, first pass over ES0902 C2
(`harnesses/desarrollo/controles/checks/qa-security-approval-evidence.py`). None breaks a scenario;
each is a policy decision the C2 spec took and nobody has confirmed against the real circuit:

- **A shared `releaseId` alone establishes `EXACT`.** A candidate that declares only
  `releaseId: 1.4.0` and omits its commit relates exactly to an approval of `1.4.0`. `releaseId` is
  one of the five immutable identifiers the package lists; whether a release label is immutable
  enough on its own is exactly the "similar version" doubt the package wanted closed.
- **A change dated on or before the assessment is ignored**, even inside the change set that runs
  from the approved artifact to the candidate. The spec decided it ("the assessment already saw
  it"); a mis-dated change is the way around it.
- **The fingerprint depends on the order of lists inside the approval.** Reordering `scope` or
  `authorityEvidence` reads as `SECURITY_APPROVAL_EVIDENCE_CHANGED`. It fails safe.
- **A newer approval in DEV hides an older one in QA** and reads `SECURITY_APPROVAL_NOT_IN_QA`. It
  fails safe; whether the latest-wins rule should look only at QA approvals is open.
- **A readable previous decision about another approval id is ignored.** If `previousDecision`
  names `apr-1 ` (or any id other than the chosen one), no change is flagged. The spec says "for that
  approval"; whether a decision about a different id should force re-evaluation is open. Found on
  the second pass.
- **An evaluation date before the assessment, with `development: false`, passes.** The age is
  discarded as invalid only when there was development. Found on the second pass.

No fix is decided for any of them.

### ES0902 C2 closed with three leftovers of its own class, outside every scenario's letter

Found on 2026-09-23 by `harness-spec-refuter`, fourth pass over ES0902 C2. The change closed at 56
sustained; these three are the same class the four passes spent closing —something that can say
"no" arrives unreadable and is lost— and no scenario's letter reaches them:

- **A homoglyph is not "written another way".** A newer `REJECTED` approval whose `projectId` is
  `trаmites` with a Cyrillic «а» is treated as another subject, and the older approval passes.
  `canonico()` folds accents, format characters, case and separators; it does not fold scripts.
- **The work-unit projection is filtered on two of five fields.** `c2_para_unidad` filters
  `approvalEvidenceRef` and `evidence`, and still copies `reassessment.triggers`,
  `reassessment.required` and `assessedArtifactRelation` as they come. The real check never emits
  anything else there; a hand-built result can.
- **A non-dict link in O2's scope chain is skipped.** `"PROJECT:licencias"` as a string does not
  contradict the candidate's project, and the approval passes. The real O2 never emits string links.

Fix. Each one is a line: a confusables fold (or rejecting mixed scripts) in `canonico`; the same
field-by-field shape filter on the three remaining fields; any non-dict link makes the chain
unreadable. It needs the C2 scenarios E-24, E-56 and E-13 to grow the text that reaches them.

### ES0902 C3 leaves four behaviours of the shared G1 path as they are

Found on 2026-09-23 by `harness-spec-refuter`, first pass over ES0902 C3
(`harnesses/desarrollo/bin/orquestacion/estandar_de_desarrollo.py`). None breaks a C3 scenario:

- **An unknown `role` is ignored by G1.** `role: "BOGUS"` with a homologated version reads
  `HOMOLOGATED`. It is G1's semantics, reused untouched; changing it is a G1 change.
- **The check cache ignores `desde`.** `_check` caches the loaded G1 module by id only; a second
  harness root in the same process would get the first one's module.
- **Empty normative sources say nothing.** If the control registry cannot be read, `ejecutar`
  leaves `normativeSources` empty with no issue raised.
- **Nobody aggregates G1 from the shared path in production.** "One execution, two aggregations"
  exists as an API and the C3 tests exercise it; no harness path calls `agregar(..., "ES0901.G1")`,
  because ES0901 rules have no per-rule result function yet.

And from the second pass, the same fail-open class outside every scenario's letter:

- **Shared results passed through the API are matched by `(technology, declaredVersion)` only.**
  Forged rows with the right `control` ids and `HOMOLOGATED` for Cobol 85 pass; `role` and
  `context` are not compared. `seguridad.resultado` never reaches it —the evidence channel ignores
  shared results since the first pass—; only a direct caller of `evaluar_c3(compartidos=...)` can.
  Nor do shared rows record which catalog they ran against: rows from `ejecutar(..., catalogo=<6.2>)`
  passed later as `compartidos` with no `catalogo` are gated against the installed one and pass
  (third pass).
- **Identifiers that look like `ES0901` and are not, by Unicode's count.** The source-id rule of
  E-16 folds spaces, signs, combining marks, case and width. It does not fold scripts or digit
  systems: Cyrillic homoglyphs (`ЕЅ0901`), Arabic-Indic digits (`ES٠٩٠١`), `ESO9O1`, a truncated
  `ES901`, modifier letters that look like signs (`ESʼ0901`, `ESʹ0901`, the Arabic tatweel), and
  the invisible Hangul filler U+3164 —alone, it counts as "a text with a letter"— all let the
  baseline resolve on the remaining 6.3. Same class as the C2 homoglyph leftover; a confusables
  fold would close both. Found on the fourth and fifth passes.
- **`c3_para_unidad` trusts any result that says `ruleKey: ES0902.C3`**, even one with no technology
  or one whose own states contradict `COMPLIANT`. Same level of trust `c2_para_unidad` has.
- **An explicit `currency: UNRESOLVED` on the single ES0901** resolves like a missing currency. The
  spec names the missing case as a known risk; the explicit one is not named.
- **`COMPLIANT_WITH_OBSERVATIONS` reaches the work unit as plain `COMPLIANT`**, and the observations
  do not travel.
- **`anexo2.cargar` and the check module load still sit outside the `try`.** A catalog with the
  right source but broken entries, or a G1 check with a syntax error, still breaks
  `seguridad.resultado` instead of leaving C3 unresolved.

No fix is decided.

### ES0901's hotfix path contradicts Annex V, and ES0902 C2 does not resolve it

Found on 2026-09-22 while building ES0902 C2. `normativa/extractos/ES0901.md`, internal
contradiction 2: page 29 says a hotfix gets its security assessment *after* the production
deployment, in QA; Annex V (page 42) says the assessment is mandatory *before* HML and PRD and does
not mention the hotfix. C2's check treats a hotfix like any other version, so a hotfix promoted under
the page-29 path reads `SECURITY_APPROVAL_REQUIRED` until its after-the-fact assessment exists.

No fix is decided, and none belongs in code: it is a normative contradiction. What it needs is an
authoritative reading of which path governs, and then a C2 scenario for it.

### ES0902 C1 does not treat contradicting well-formed evidence as a veto

Found on 2026-09-22 by `harness-spec-refuter`, fifth pass over ES0902 C1
(`harnesses/desarrollo/controles/checks/oidc-keycloak-integration.py`). Two cases, both with
well-formed evidence, both outside every scenario of the C1 spec:

- A surface whose protocol is proven by `PROJECT_CONFIGURATION` and that also cites a
  `RUNTIME_INTEGRATION_TEST` with `outcome: FAIL` passes. The failed test simply does not count;
  it does not veto. The spec says each class proves on its own and a test counts only with
  `CONFIRMED`; it never says a failed test blocks.
- An `INSTITUTIONAL` surface citing one `AUDIENCE` evidence with `value: INSTITUTIONAL` and another
  with `value: CITIZEN` (both valid classes, both naming the surface) passes: the institutional one
  wins and the contradiction is not reported.

Neither is a defect against the spec; both are a policy decision nobody has taken. Malformed
evidence that could say "no" is already fail-closed since that pass.

A third one, found on the seventh and eighth passes: a contrary reconciliation that is legible but
carries no authority (`sourceType: AGENT_STATEMENT`, blank `reference`, `establishes: []`) does not
count, and the citizen surface passes on the other reconciliation. Same question: whether a
contrary piece without authority should still block.

No fix is decided. The candidate is the same shape C1 already uses for reconciliations: two
well-formed pieces that contradict each other on the same dimension leave it unresolved. It needs a
spec change and new scenarios.

### ES0902 C1 reads a misspelled catalog value as "not this dimension", in silence

Found on 2026-09-22 by `harness-spec-refuter`, eighth pass over ES0902 C1. A contrary
reconciliation with `establishes: ["CROSS_STANDARD_RECONCILIATON"]` (one letter missing) or
`sourceType: "IDENTITY_TIKET"` does not qualify as a reconciliation, is dropped without an entry in
`issues`, and the citizen surface passes on the other reconciliation. It is the same class the C1
change spent eight passes closing — something that can say "no" arrives unreadable and is lost —
one field earlier than the `resolution` value that was closed on the seventh pass. No C1 scenario's
letter reaches it; the cycle was cut there on purpose, and the change closed at 50 sustained.

Fix. The refuter's suggestion, which closes the class rather than the case: a value that is in no
known catalogue — the keys of `SUFICIENTES`, `INSUFICIENTES`, the dimensions — makes the evidence
unreadable, and an unreadable cited id already blocks the reconciliation path since the sixth pass.
It needs a C1 scenario of its own.

### Four project-owned registries live in `reglas/`, which every `-Update` overwrites

Found on 2026-09-22 while building ES0902 C1; ES0902 C2 added the fourth the same day. Four files
ship empty on purpose because their content belongs to the project, not to the harness:
`reglas/database-profiles.json` (database environments), `reglas/security-control-authority.json`
(ES0902 O2), `reglas/authentication-surfaces.json` (ES0902 C1) and
`reglas/security-approval-evidence.json` (ES0902 C2). All four sit in `reglas/`, which the
installer copies with `-Force`. A project that fills any of them and then runs `-Update` gets the
empty copy back and loses what it wrote, silently. For C2 it is worse than lost data: the check
fingerprints consumed approvals, and an overwritten registry loses the record the fingerprint was
taken from.

The O2 spec says this debt "queda anotada en `Pendientes/`"; it was not, until this entry. Nothing
fails today because no real project has filled any of the three.

No fix is decided. The two obvious roads are a separate project-owned directory that `-Update`
never touches, or an exclusion list in `install.ps1`; either one touches `roster.ruta_de_regla`,
which is how the four checks find their file, and needs an installer case.

Since 2026-09-23 there is a fourth: `reglas/authentication-abuse-protection.json`, installed empty
by ES0902 Vu1, with the same exposure.

### ES0902 Vu1 has no field for "expected side effects known" on a runtime test

The Vu1 package lists four conditions for a failed-login runtime test: authorized environment,
dedicated test identity, no real-user account, and known expected side effects. The provided
`authentication-abuse-protection.schema.json` has `runtimeTest.authorized`,
`environment`, `dedicatedTestIdentityRef` and `result`, and nothing for the fourth. Since
2026-09-23 the check reads `authorized: true` as the authorization of the test with its side
effects, which is a reading, not evidence. The schema is closed with `additionalProperties: false`,
so a project cannot add the field on its own.

Fix. Add `expectedSideEffectsAcknowledged` (boolean or null) to `runtimeTest` in the schema and
require it `true` in `prueba_segura` of `controles/checks/authentication-abuse-protection.py`, with
a scenario in `tests/casos/44_es0902_vu1_proteccion_de_autenticacion.py`. It changes a provided
contract, so it needs whoever owns the package to agree.

### ES0902 Vu1 closed with E-39 and E-42 contradicted, and one equivalence leftover

Third and final refuter pass, 2026-09-23: 42 upheld, 2 contradicted, documented in
`docs/cambios/es0902-vu1-proteccion-de-la-pagina-de-autenticacion/verificacion.md`.

E-39. The credential pattern in `controles/checks/authentication-abuse-protection.py` starts with
`(?<![:/\w-])` so the `:secret:` segment of a secrets-manager ARN does not close the registry.
The same lookbehind lets `app:password=hunter2`, `env/DB_PASSWORD=hunter2`, `ci-job:api_key=abc123`
and `realm:token=abc123` through, in `details` and in a `surfaceId`, into the output.

Fix. Decide on the value, not on the key: allow the ARN only when the whole string is an ARN
(`^arn:[^\s]+$`), and drop `:` and `/` from the lookbehind. Re-run the legitimate texts of E-39
(`passwordPolicy:`, `tokenLifespan=`, `Bypass:`, the ARN) as the guard.

E-42. `evaluar_pagina` finds unreadable evidence about a page with
`sid in json.dumps(e, sort_keys=True, default=str)`. `json.dumps` escapes non-ASCII and quotes, so
`trámites-login` or `log"in` are never found and malformed or repeated uncited INACTIVE evidence
about them is discarded in silence (PASS). The same substring match also over-blocks: malformed
evidence about `ciudadano-v2` leaves `ciudadano` unresolved.

Fix. Walk the strings of the evidence (`_textos`) and compare each one, or each item of a
`surfaceIds` list, for equality with the surfaceId; fall back to the substring only when
`surfaceIds` is not a list. That closes both sides.

Equivalence. A `MECHANISM_EQUIVALENCE` with `value: SUPPORTED` counts and avoids FAIL; the module
rejects that value everywhere else as a capability claim. Fix: exclude `VALORES_DE_CAPACIDAD` from
equivalence values, with a line in `test_e22`.

### ES0902 Vu2 closed with E-08, E-13 and E-43 contradicted: NFC left out of the duplicate counts

Third and final refuter pass, 2026-09-23: 44 upheld, 3 contradicted, documented in
`docs/cambios/es0902-vu2-datos-sensibles-en-transito/verificacion.md`. In `derivar` of
`controles/checks/sensitive-data-transport-protection.py`, `ids_clase.count(...)`,
`ids_camino.count(...)`, `missing` and the hop ids `hids` compare raw text while the classes dict is
keyed in NFC. Two classes `salúd` (NFC and NFD) are not flagged as duplicated and the second
overwrites the first by input order: [NFC, NFD] gives APPLICABILITY_UNRESOLVED and [NFD, NFC] PASS;
with a NOT_SENSITIVE twin the signal goes FALSE in one order.

Fix. Normalize every id to NFC once, when reading the inventory, and count on the normalized ids.
`controles/lib/evidencia.py` (born with Vu3) already has the helper.

### ES0902 Vu2 E-47 blocks more than it says

Same pass. `sueltas` in `evaluar_camino` blocks the path for any evidence naming it without a
matching `hop` or with an unknown value, without source filter, without `_lectura`, and for a "yes"
too: a PROTECTED evidence shared by two paths (hop only in the other one) leaves this one unresolved;
a `REDIRECT_DOWNGRADE` with `value: NO_EXPOSURE` blocks, so "no downgrade" cannot be declared; a
README without hop blocks while a README with hop is ignored (which contradicts E-45's "a weak
source does not count"); an unsafe or target-less test without hop is labelled
TRANSPORT_PROTECTION_UNRESOLVED instead of its own state. Never FAIL, so it only fails closed.

Fix. Restrict `sueltas` to evidence that says "no" (PLAINTEXT, EXPOSES_PAYLOAD, or an unknown
value), from `FUENTES_DE_TRANSPORTE`, passed through `_lectura`, and only when the `hop` is missing —
a hop that exists in another path the evidence also names is not loose.

### ES0902 Vu3 moved the evidence helpers to `controles/lib/evidencia.py`; Vu1 and Vu2 keep copies

Since 2026-09-23 the closed catalog, the NFC id comparison and the single secret output rule live in
`controles/lib/evidencia.py`, used by Vu3. Vu1 (`authentication-abuse-protection.py`, with its E-39
regex bug) and Vu2 (`sensitive-data-transport-protection.py`) still carry their own versions. Two
copies of a secret detector drift: Vu1's already differs.

Fix. Migrate both checks to the lib in one change for `harness-staff-engineer`, behaviour frozen
except for the documented Vu1 E-39 and E-42 fixes, which need their own scenarios.

### A registered hook whose `run-hook.cmd` cannot be found exits 0 and does nothing

Found on 2026-09-24 during the `rojo visto` pass of `hooks-con-shell-powershell` E-04. The command
the spec fixes is `& "$env:CLAUDE_PROJECT_DIR/.claude/harness/run-hook.cmd" <hook>; exit $LASTEXITCODE`.
When `&` cannot find the launcher, PowerShell writes a `CommandNotFoundException` to stderr and
`exit $LASTEXITCODE` exits **0**: `$LASTEXITCODE` is still `$null`, because no program ran. The
output is empty, and empty is a valid answer from a hook. Measured with `CLAUDE_PROJECT_DIR` set to
`C:\no\existe`: exit 0, empty stdout, one CLIXML error record in stderr.

The installer's gate catches it since this change: `Test-HooksInstalados` counts a PowerShell error
record in stderr as a failure even with exit 0, and E-03 and E-04 assert it. That is stricter than
the spec's text ("otro código que 0 o una salida que no es JSON") and it was the only way for E-04 to
go red when the path broke. What nothing catches is the session: with `.claude\harness\` gone or
half restored, Claude Code sees exit 0 and no output, and a missing launcher is silent. The old bash
command at least left `hook_non_blocking_error` in the transcript. For `pre-tool-use`, silent means a
secret goes through.

Not fixed here: the command text is fixed by the spec (E-01), so failing when `$?` is false is a spec
change, and how Claude Code reports a non-zero exit from a `shell: powershell` hook has not been
observed.

## Verification that was not done

### No real `dev-refutador` run over a `refutation-unit/1.0` has been read

Atomic refutation (`docs/cambios/refutacion-atomica/spec.md`, 2026-09-25) proves the boundary
deterministically: what `refute --unit` hands out and what `refute --record` accepts or rejects.
It cannot prove what a real run does between the two. A model that opens a file outside
`evidenceScope.paths`, or globs the repository, and then cites only in-scope paths passes
`--record`. Nobody has run the evolved agent on a real unit and read the result.

Fix. Run `dev-refutador` on at least five real units of a real plan, then read each run for three
things: reads outside the scope, a second claim, and prose around the JSON. Record the reading
through `write-a-lectura`, with a spec whose scenarios carry `· verificación: lectura`.

### `integridad-de-repositorio` shipped with E-04 and E-41 unsupported

Four refuter passes on 2026-09-22 took it from four `sin sustento` to two, and found a real leak on
the way (the provider URL travelled inside `diffMeta` into the sealed snapshot; fixed). No scenario
is contradicted and the module behaves correctly in every case tried. What remains is the test:

- E-04: `reason: "ES0902_APPROVED"` or `verdict: "ES0902_PASSED"` added to a clean review stays
  green. The value sweep deliberately ignores compound tokens so it does not flag the baseline
  provenance `APPROVED_RELEASE`, and no premise checks that `ES0902_APPROVED` *is* caught.
- E-41: the 560-signal product fixes `location`, `evidence` and the validity of the category.
  Exposing the facts only when `location` is present, or dropping them when the finding is
  `REVIEW_INCOMPLETE`, stays green.

Also: `instantanea()` copies whatever `diffMeta` it receives. It does not leak today because the
adapters normalize first.

Fix. Add the compound tokens to the value vocabulary with a premise that each is caught and
`APPROVED_RELEASE` is not; add `location`, `evidence` and an invalid category to the E-41 product.
Then a fifth refuter pass.

### The leak half of `26_d1 / E-28` degrades silently if its first half is weakened

Found on 2026-09-19 by `harness-spec-refuter` while re-verifying E-28, and it does not contradict
the scenario — E-28 says nothing about this. The case has two halves: the first runs the forbidden
patterns over the two D1 artifacts, the second injects eight realistic leaks and asserts
`any(re.search(p, base + fuga) for p in PROHIBIDOS)`.

That `any()` is only meaningful because the base text matches nothing, which is what the first half
proves. The coupling is implicit: delete or weaken the first bucle and the second keeps passing for
every leak, including one nothing catches. Eight assertions turn into decoration, in green.

Fix. Assert the premise instead of relying on it: one line that the base matches zero patterns,
inside the leak half, before the loop. Two lines of test and the coupling stops being implicit.
`27_d2 / E-28` was written with that assertion from the start; this item is only about the D1
case, whose verdict is already closed and which is not touched without re-verifying it.

### Two of D2's seven result states are never produced by a real run

Found on 2026-09-19 by `harness-spec-refuter` while verifying D2, and it does not contradict any
scenario. `NOT_APPLICABLE` and `APPLICABILITY_UNRESOLVED` are exercised in
`tests/casos/27_d2_delegacion_credenciales.py` only as synthetic dictionaries `{"state": X}` fed to
`aprueba()`. No call to `CHECK.evaluar` in that case passes the signal as `FALSE` or unresolved, so
the two branches of `harnesses/desarrollo/controles/checks/authentication-delegation.py` that
produce them are never run.

The same shape appeared in D1 and was closed there before the verdict, by adding the assertion to
`E-18`. In D2 the scenario text is narrower —E-17 says `PASS` is the only state that approves, a
proposition about `aprueba()`— so the verdict stands; what is missing is coverage, not compliance.

Fix. Two calls in `E-17`: one with the signal `FALSE` asserting `NOT_APPLICABLE` and that it does
not approve, one with it unresolved asserting `APPLICABILITY_UNRESOLVED` and `missingSignals`. It
re-opens a closed verdict, so it goes back through `harness-spec-refuter` for that scenario.

### `FUENTES_INSUFICIENTES` in D1's check says less than the code does

Found on 2026-09-19 while verifying D2.
`harnesses/desarrollo/controles/checks/citizen-authentication-mechanism.py` declares

    FUENTES_INSUFICIENTES = ("REPOSITORY_CONFIGURATION", "AGENT_STATEMENT")

and does not list `REPOSITORY_DEPENDENCY`, which D2 split out of `REPOSITORY_CONFIGURATION` and
which the D2 check does list. Behaviour is identical in both: the real gate is the whitelist
`sourceType in FUENTES_SUFICIENTES`, so the new class is already insufficient in D1 by omission.
What is wrong is the constant, which is declarative and reads as the list of what does not count.

Somebody adding a class tomorrow will read that tuple as the inventory it looks like and conclude
the new one was considered and left out. Both files are verified and closed, so this is a one-line
change that still goes back through the refuter for the scenarios that name the constant — `E-21`
in D1 and `E-16` in D2.

### `applicability: NOT_APPLICABLE` erases a finding's state, including a paradigm conflict

Found on 2026-09-20 by `harness-spec-refuter` while verifying D3. In `revisiones.resolver` the
applicability branch runs before the status branch, so a finding that declares
`applicability: NOT_APPLICABLE` is skipped whatever its `status` says. Verified in-session:

```
TECHNOLOGY_PARADIGM_CONFLICT + NOT_APPLICABLE  ->  COMPLIANT, states [], issues []
JUSTIFICATION_PENDING        + NOT_APPLICABLE  ->  COMPLIANT
EVIDENCE_MISSING             + NOT_APPLICABLE  ->  COMPLIANT
```

The conflict disappears with no trace. The three scenario texts that say these never reach
compliant — `G2/E-16`, `G2/E-17` and `D3/E-19` — are all flat, and all three are currently upheld
because no test combines the two fields. The precedence is inherited from G2; D3 did not introduce
it, which is why D3's verdict does not turn on it.

Requiring a `rationale` does not help: these findings carry one and still resolve to compliant.

Fix. Decide which states survive a `NOT_APPLICABLE` and make the loop check them first. A finding
that says "the paradigm conflicts with the rule" and "the rule does not apply here" is either
contradictory — and should be rejected structurally — or it means the reviewer scoped the conflict
out, which is a decision that has to stay visible. It touches `G2` and `D3`, both of which then go
back through the refuter for those scenarios.

### `resolver` carries a dead branch for a missing weighting axis

Found on 2026-09-20 by `harness-spec-refuter` while verifying D3, and reported again when it
checked that the first report had been written down — it had not. In
`harnesses/desarrollo/bin/orquestacion/revisiones.py`, `resolver` tests `if peso is None or peso ==
"UNRESOLVED"`. The `is None` half is unreachable: `validar_estructura` already rejects a finding
that does not declare its rule's axis, so `resolver` returns early with `SCHEMA_INVALID` and never
reaches the weighting. Only the explicit `UNRESOLVED` value gets there.

It changes no output, which is why it is here and not in a verdict. What it costs is a reader who
concludes the missing-axis case is handled in two places and only patches one.

Fix. Drop the `peso is None` half, or move the axis requirement out of `validar_estructura` and
leave `resolver` as the single place that decides. Whichever way, `G2/E-14`, `G2/E-15` and `D3/E-17`
name the behaviour and go back through the refuter.

### A same-size mutation in the same second leaves stale bytecode behind

Found on 2026-09-20 while running the `rojo visto` pass for D3. A mutation script that rewrites a
`.py`, runs the suite and restores the original leaves `__pycache__` holding the bytecode compiled
from the mutated source: Python invalidates a `.pyc` by (mtime, size), and `"G1"` -> `"D3"` keeps
the size while the restore lands in the same filesystem second.

The effect: `24_g1`, `25_g2` and `28_d3` failed against a traceability value that was no longer on
disk, minutes after the same suite had been green. `git status` showed nothing, because the file
really was restored. Fifteen minutes to find.

Fix. Any script that mutates sources deliberately purges `__pycache__` after restoring, and the
red-seen driver in the scratchpad already does. Worth a line in `write-a-spec` where it explains
the mark, because the next person to break code on purpose will hit exactly this.

### Nothing enforces "unless project coverage is known to be complete"

Found on 2026-09-20 by `harness-spec-refuter` while verifying D4, on a doctrine the signal module
inherited from D1. `responsive-ui-required.md` writes the boundary the way every signal contract
writes it: *"Not finding a frontend directory is not `FALSE` unless project coverage is known to be
complete."* The module has no notion of complete coverage. It has a table of source classes, and
which one an absence gets labelled with is chosen by whoever writes the evidence.

Reproduced in-session with one claim — "no aparecio ninguna carpeta frontend" — under seven classes:

```
REPOSITORY_DEPENDENCY, AGENT_STATEMENT            -> D4 unresolved
REPOSITORY_CONFIGURATION, PROJECT_CONTEXT,
TASK_CONTEXT, HUMAN_CONFIRMATION,
PROJECT_DOCUMENTATION                             -> D4 NOT_APPLICABLE
```

The same absence, relabelled, takes a rule out of the report. It does not contradict any scenario:
`D4/E-05` walks four paths that all stay unresolved, and `D4/E-07` *requires* structured evidence to
resolve `FALSE` — reading E-05 as universal would put the two in direct conflict. What is missing is
anything that holds the policy's own sentence.

Fix. Either the signal carries a `coverage` field that a `FALSE` from an absence has to declare, or
the contracts stop promising the "unless" and say plainly that a `FALSE` is whatever the evidence
class says. The first is more work and matches what the policies already claim; the second is honest
and cheap. Both touch `senales.py` and every installed signal contract, so they go back through the
refuter for `D1/E-06`, `D2/E-05`, `D3/E-05` and `D4/E-05`.

📌 **D5 closed this for itself on 2026-09-21, and only for itself.** Its check takes
`scopeCompleteness: {complete, source, reference}` and is the one place in the harness where a
`FALSE` derived from an absence — `frontendPresent = FALSE` — has to declare its coverage with a
source from a closed list and a citation. See `aplicabilidad()` in
`controles/checks/address-normalization-integration.py` and `D5/E-07`. It is a working precedent for
the first option above, and it is worth reading before choosing: the derivation lives in the rule's
check, not in `senales.py`, precisely because D5 was the only rule that needed it. Generalizing it
is the open half.

### `EVIDENCIA_QUE_NO_PRUEBA` and `EVIDENCIA_DE_APOYO` read load-bearing and are inert

Found on 2026-09-20 while verifying D4. In
`harnesses/desarrollo/controles/checks/responsive-behavior.py`, three constants declare how evidence
classes are treated. Only one is used:

```
EVIDENCIA_DE_CORRIDA        4 occurrences   (read by _evaluar_caso)
EVIDENCIA_DE_APOYO          1 occurrence    (its own definition)
EVIDENCIA_QUE_NO_PRUEBA     1 occurrence    (its own definition)
```

The gate is a whitelist — a class not in `EVIDENCIA_DE_CORRIDA` cannot sustain a passing case, which
is why closure by default works and why an unforeseen class is rejected. The other two tuples are
documentation shaped like configuration. Test assertions of the form
`"REPOSITORY_DEPENDENCY" in CHECK.EVIDENCIA_QUE_NO_PRUEBA` assert that a string is in a tuple and
prove nothing about behaviour; the state assertions beside them are what hold `D4/E-09` to `E-13`.

Same smell as `aporta` in the manifests, one item above: a name that reads like a contract and is a
comment. Fix. Either drop the two tuples into the module docstring where a reader expects prose, or
have `_evaluar_caso` reject a declared-useless class explicitly instead of by omission. Touches
`D4/E-09`..`E-13`, which name the constants.

### The `D4 / E-16` guard will break on a correct edit, not on a leak

Found on 2026-09-20 by `harness-spec-refuter` on the third pass over D4, and it is the durability
observation, not a hole. `E-16` rests on an invariant — a D4 artifact carries no number, because the
standard defines none — implemented as `\d{2,4}` over both artifacts. The invariant is true
today: zero matches, verified independently.

The cost is that legitimate prose goes red:

```
ES0901 §7.1 D4, pag. 12      RED        Bootstrap 5 esta instalado   RED
revisado en 2026             RED        Angular 17                   RED
ver tambien ISO 9241         RED        Section 7 of the standard    RED
```

And citing the page is the house style. Of the seven installed policies,
`responsive-ui-required.md` is the **only** one with no numbers:

```
approved-technology-required.md            10
credential-entry-delegation-required.md    18, 19
gcba-citizen-authentication-required.md    18
homologated-version-required.md            10, 29, 30, 31
technology-version-compliance.py           29, 30, 31
responsive-ui-required.md                  none          <- the outlier
```

The day somebody adds `pág. 12` to the D4 policy — which four of the others already do — the case
goes red against correct content, and the fix under pressure will be to loosen the half that is an
invariant today. That is how this guard dies.

Fix. Scope the band instead of dropping it: page citations and versions in this repository are one
or two digits, and a viewport value is three or four, or two with a unit. Moving to `\d{3,4}`
plus the existing unit pattern lets the house style through and keeps every declared leak red — all
18 are three digits or carry a unit. Two known escapes go with the decision: `ANCHO = 1_440`, where
Python's thousands separator kills the word boundary and which matters because one artifact is a
`.py`, and the lowercase brand form `fairphone 5`, because the model pattern requires an initial
capital. It touches `D4/E-16`, so it goes back through the refuter.

### `19_contexto / E-29` is not deterministic, and what it asserts is determinism

Seen on 2026-09-16: in a full suite run, `E-29 mismo hash` failed with two different hashes for two
resolutions of the same data. It then passed in three isolated runs of `19_contexto` and in every
full run since — dozens of them between 2026-09-16 and 2026-09-18.

```text
MAL 19_contexto / E-29 mismo hash
  esperado <'sha256:8892b287cc232fc30fea60279f07994e10046ae4603938849e3a68276803d497'>
  obtenido <'sha256:419bbae8f20deb810b372238aaa4929a824db5b98ba18c08f1b039ef1ee3f8a2'>
```

The scenario asserts that two resolutions of the same data give the same hash — which is exactly
what failed. A test that is itself non-deterministic about determinism is worse than no test: the
one time it fires, nobody knows whether it found the bug or was the bug.

Nothing was changed. The cause was not found and is not guessed here.

### The redaction guarantee lives in the assembler, not in the resolvers

0.17.0 moved secret redaction out of the individual resolvers and into
`contexto/ensamblador.py::_limpiar`, which walks the whole document. That was the right fix — the
per-field version leaked through three paths (acceptance criteria, the ficha's `title`, and the
`reference` of a source) and each one had to be remembered separately.

What it leaves open: **the guarantee is a property of `armar`, not of the resolvers.** A future
consumer that calls `tarea.resolver` or `proyecto.resolver` directly and skips the assembler gets
unredacted text. Today nothing does — `dev-harness.py contexto` always assembles — so this is a
shape to keep in mind, not a defect in the tree.

Fix. When Block 3 starts consuming resolvers, either it goes through `armar` or the redaction moves
down into a boundary both paths cross. Decide it then, with the second caller in front of you
instead of guessed. Worth a scenario either way: today no test says "a resolver used on its own
returns unredacted text", because nothing uses one on its own.

### Three loadable .md files are in Spanish, against ADR-0011

[ADR-0011](../../docs/adr/0011-el-idioma-de-un-archivo-lo-decide-quien-lo-lee.md), accepted
2026-09-15, says the language of a file is decided by who reads it: English for anything a model
loads as instructions, Spanish for anything a person reads. The ADR names its own debt in the
"En contra" section, because three files broke the rule the day it was written:

- `harnesses/desarrollo/agents/dev-refutador.md`
- `harnesses/analisis/agents/hu-redactor.md`
- `harnesses/analisis/agents/hu-refutador.md`

They were not translated with the ADR on purpose: mixing the translation with the change that
introduces the rule would make one diff say two things.

Fix. Translate the three to English, keeping every rule and every example intact — these are
working agents, not drafts, and `hu-refutador` in particular is the one `dev-refutador` inherited
its shape from. What they output for people stays in Spanish, and each one should say so in its
second line, the way `dev-iniciador-code.md` already does.

### Nothing measures whether a loadable .md is in the right language

ADR-0011 claims its criterion is checkable: *"un `.md` con frontmatter `name:`/`description:` es una
pieza cargable y va en inglés. No hace falta juicio para clasificarlo."* Nothing checks it. The
three files above prove the rule does not enforce itself.

Fix. A case in `06-composicion.ps1` — the one that already audits the repo's composition — asserting
that every `.md` with `name:` frontmatter under `harnesses/*/agents/` and `harnesses/*/skills/` is
in English. Detecting "is in English" mechanically is the hard part; a cheap proxy that would have
caught all three is the presence of Spanish function words (`que`, `debe`, `para`, `cuando`) in the
first 40 lines. It warns, it does not block — the same shape as every other measurement in this
repo.

### Neither the Ficha de Proyecto nor the acceptance-criteria field exists in any real Jira yet

Two suppositions shipped in 0.17.0 that only a real run can confirm or break:

- **The Ficha de Proyecto** is a concept this block introduces: an issue of a reserved type, one per
  Jira project, whose description carries `Objetivos`, `Alcance`, `Reglas` and `Arquitectura` as
  headings. Nobody has written one. If the organism models it differently — a separate Jira project,
  a Confluence space — the Project Resolver changes strategy, though the contract it produces does
  not.
- **`campoCriteriosAceptacion`** ships empty, because there is no standard Jira field for acceptance
  criteria. Until somebody says which custom field holds them in the organism's Jira, every
  `TaskContext` comes out with an empty `acceptance_criteria` and a declared gap.

Fix. Not code: one real ticket and one real ficha. Run
`python .claude/harness/bin/desarrollo/dev-harness.py contexto <CLAVE>` against the organism's Jira
and read what comes back. It also settles whether `/rest/api/3/search/jql` is the right endpoint
there — see the item about Jira and GitLab never being called for real.

### Neither Jira nor GitLab was ever called for real

0.16.0 shipped two integration adapters, five diagnostic states and a capability registry, and the
whole thing was verified against an injected fake transport. That was deliberate — the suite must
not depend on a network, a VPN or a token that expires on demand — but it means **not one line of
this code has ever spoken to a GCBA server.**

What a real run can still disprove, with the reason each one is a real risk:

- `GET /rest/api/3/search/jql` is the current Jira Cloud endpoint; `/rest/api/3/search` is the one
  it replaced. The adapter falls back from the first to the second on 404/410, and the fallback is
  tested — against the fake.
- `GET /api/v4/personal_access_tokens/self` does not exist in older GitLab. There is a probe-based
  fallback, tested the same way.
- A corporate proxy or a TLS interception appliance in the middle turns everything into
  `CONNECTION_FAILED`, and the message will say "revisá la red o la VPN" without naming the proxy.

Fix. Not code: run it. `python .claude/harness/bin/desarrollo/dev-harness.py setup` on a real
project with a real Jira and a real GitLab of the organism, and read what comes back. Whatever it
finds is the first thing 0.16.1 is for.

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
agents were killed by a watchdog, so the window is not theoretical.

🔴 **And there is a second way in that has nothing to do with being killed: two runs at once.**
On 22-09-2026 two refuter agents were launched in parallel and both ran the full gate. One
appended `def (((` while the other was between its own break and its own restore, so one
`finally` wrote back a copy that already carried the other's damage. Both agents reported the
tree broken; the suite had been green minutes earlier. The window is a few seconds wide and it
does not need anybody to kill anything — **running the PowerShell gate twice concurrently is
enough**, which is easy to do by accident with background agents. Until the fix below lands,
never run `.\tests\Invoke-Tests.ps1` while another agent might be running it. The worst case leaves
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

### ES0902 declares thirty-eight controls and not one of them is built

Twenty policies, sixteen checks and two reviews. Six more are already installed because ES0901 G1
and D2 share them, which is why the number is not forty-four.

This is the correct state of a harness that classified before building — the same decision ES0901
took for its own twenty-four rows — but it is the biggest instance of it so far, and the risk is
not technical. It is that somebody reads "ES0902 installed" and understands "ES0902 complied
with". `docs/seguridad-es0902.md` says it on the first screen and `37_es0902 / E-70` pins the
exact counts, so a control that appears later moves the number and somebody has to look.

What is missing: the controls themselves, rule by rule, each one its own change.

### Nothing produces the authoritative severity mapping that ES0902 G2 needs

The acceptance threshold — no finding above LOW and at most ten LOW — is only computed when the
scanner's severity labels are mapped to the ES0902 risk categories by an authoritative source.
Nobody produces that mapping today, so every real run comes out
`VULNERABILITY_RISK_MAPPING_UNRESOLVED` and no count is published at all.

That is the correct behaviour — deciding that a tool's `medium` is the standard's `LOW` is an
equivalence somebody has to sign — and it is also a hole: the threshold is installed and cannot be
used until the mapping exists. Where it comes from is not a code question; it is a question for
whoever owns the scanner and DGSEI.

### ES0901 P5 does not exist, so Vu5's equivalence cannot be decided

`es0902-cross-standard-map.json` declares `ES0902.Vu5 -> ES0901.P5` as
`EQUIVALENCE_REVIEW_REQUIRED`, resolving to `CROSS_STANDARD_CONTROL_BINDING_REQUIRED`. P5 is one of
the sixteen ES0901 rules still unclassified, so there is nothing to compare semantics against and
nothing to deduplicate.

The day P5 is implemented this has to be resolved for real: compare the exact semantics of both
and deduplicate execution **only** if the outcomes are equivalent. Deduplicating first and
comparing later is how one rule silently stops being evaluated.

### The provided ES0902 matrix declares one control id with two types

`security-vulnerability-acceptance-threshold` is declared by G2 as a policy **and** as a check.
The file is a provided normative artifact and it is not corrected here: correcting provided
normative content is inventing it. `seguridad.colisiones_de_id` reports
`SECURITY_CONTROL_ID_TYPE_COLLISION` with the id and both types, and the id shows up twice in the
not-installed report, once per type.

What should happen: whoever owns the ES0902 matrix splits the id, or confirms that one control
plays both roles. Until then the double entry is correct and intentional.

### A signal name shared by the two standards is not prevented from colliding

`senales.declaradas` now reads both matrices, so a signal declared only by ES0902 is valid. That
also means two rules from different standards can declare the same signal id and get resolved by
the same document.

Today that happens once and on purpose: `authenticationPresent` is shared between ES0901 D2 and
ES0902 C1 because the installation package says to reuse it. But nothing stops a future signal
from colliding by accident with a different meaning, and the collision would be silent — the
second standard would simply read somebody else's evidence.

What should happen: either namespace the signal ids per standard, or declare the shared ones
explicitly so an undeclared collision is an error.

### `docs/normativa-7.1.md` is a reconstruction, and nobody has the original

The file was truncated by accident on 22-09-2026: a patch script opened it with
`io.open(path, "w")` — which truncates on open — and the `.write()` on the next line raised a
`UnicodeEncodeError` on a badly escaped emoji. It was **untracked**, like most of `docs/cambios/`,
`comun/schemas/` and `harnesses/desarrollo/agents/`, so `git checkout` could not bring it back and
there was no copy anywhere on disk.

It was rebuilt against the assertions of the five test groups that read it — `31_d6`, `32_d5`,
`34_d7`, `35_d8`, `36_p1` — which turned out to be a fairly precise specification: the exact
section titles, the minimum lengths, the sentences that must appear inside D7's section, and the
leak patterns no section may contain. All five groups pass. **The text is not the original.**

What the rebuild already got wrong and was corrected: the section "Lo que está y lo que falta"
carried "eight complete rules and sixteen incomplete", a number that was true when D5 closed and
went stale when D7, D8 and P1 landed. Measured: **eleven and thirteen**. No test reads that
section, so the stale number survived the rebuild without anything turning red — which is exactly
the shape of thing to look for if anything else in that file reads wrong.

What should happen: somebody who knows what the file said reads it once against the five specs it
documents. Until then it is an honest reconstruction and not a restoration.

## Outside the harness, written down so it is not lost

### Four IGE documents nobody read

At the root of `C:\Work\GCBA\IGE`: `Setup de Proyecto v3 - IGE.docx`, which the DGISIS guide
requires as an attachment in two different procedures, the two annexes on structure and missions,
and the TECBA functional specification.

### Credential in the `siccsir` agents

`siccsir-backend.md:13` and `siccsir-qa.md:12` carry a seed user with its password in clear text,
and the number is an employee file number. Decision taken: it stays, it is a seed for a local
Docker. Written down here in case the criterion changes.
