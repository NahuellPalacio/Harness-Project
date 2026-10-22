# Pending ideas

Ideas for the harness that are not yet decided work. Anything here is a proposal: it has not been
committed to, and it may never be built.

Each entry says what the idea is, what problem it solves and what it would cost. An idea that gets
accepted moves to `Pendientes/Fix-Harness/PENDIENTES-FH.md` as work with a fix; an idea that gets
rejected stays here with the reason, so it is not proposed again.

## Entry format

### Title of the idea

What it is, in two or three lines.

Problem it solves. Why the harness is worse off without it.

Cost. Rough estimate, and what it touches.

Status. Open, accepted or rejected, with the reason.

## Open

### Let the source registry hold the OWASP project pages

Allow `reglas/source-registry.json` to declare an external web source —an OWASP Top 10, API Security
or Mobile Top 10 edition— with its URL, edition, retrieval date and sha256, and give `frescura.py` a
channel that can observe it.

Problem it solves. ES0902 Vu10 (installed on 2026-09-27) binds each OWASP family to a snapshot and
requires `CURRENT` freshness from the trusted-source mechanism, but the registry schema has no `url`
or edition field, `kind` only admits `norma`, `proceso` and `tecnologia`, and the only channels are Jira
attachments and a local folder. So no OWASP page can ever be `CURRENT`, and every real project stays in
`OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`. Vu10 reads freshness as evidence translated with
`guia_owasp.evidencia_de_frescura`, so it will pick the new states up without changes.

Cost. Medium: the `source-registry/1.1` schema, `frescura.py`'s version comparison (editions like
`2025` already order numerically), an HTTP or file-drop channel, and `57_aceptar_fuentes.py`. It
touches the trusted-knowledge block, so it is specified and refuted on its own.

Status. Open.

### The workflow of each harness cannot be drawn

Stated by Nahue on 2026-08-17, and it is the sharpest description of the problem so far: *if you
draw what each harness does, the workflow is not clear.*

The harness today is a set of parts that work — hooks, checks, skills, agents, zones — grouped by
what they are, not by what somebody does with them. `analisis` has a writer and a refuter, which is
half a method with no cycle around it. `desarrollo` enforces standards but nobody can say at which
moment of the work each rule lands. `comun` is infrastructure. Nothing in the repo answers "what
does a day of work with this look like", so each part is judged on its own instead of by the result
it contributes to.

Problem it solves. A harness whose workflow cannot be drawn cannot be argued about, taught, or
trimmed: there is no way to say a part is missing, or that another one is in the way, because there
is no shape to compare against. It is also why the question "is a session with the harness better
than one without it" has never been answerable.

Cost. Unknown until it is scoped, and it is a redefinition, not a feature: it deserves the
architectural path — questions, two or three approaches, a design in sections, and only then a spec
under `docs/cambios/`.

Status. Open, parked by Nahue's own call: *we will look at this later*. Written down so the framing
is not lost, because it is the framing, not a task.

### ADR-0007 — this repository adopts SDD for its own development

ADR-0006 decided that the projects installing the harness work by SDD, and rule 5 left this
repository explicitly outside: *"gcba-harness does not adopt SDD for its own development for now.
It is decided after having seen it work in a real project, and that decision will be its own
ADR."*

That ADR is the one missing. The spec of the `hooks-en-python` change opens by declaring itself
"the first time this repository uses the spec format for a change of its own" and calls itself
"exactly that after". So the method is already in use here: a spec with 31 numbered scenarios, a
plan of 14 tasks, and a refuter that verifies against them without having built anything.

Problem it solves. What governs this repository is currently unwritten. Somebody arriving cannot
tell whether `docs/cambios/` is the rule or an experiment somebody ran once, and the practice that
nobody wrote down is the one that dies the first busy week.

Cost. Half a page. `docs/adr/0007-*.md`, plus one line in the ADR index. No code.

Status. Open. Worth writing when `hooks-en-python` closes, because that change is the evidence the
ADR argues from — including what it cost: the reviews caught a false positive that blocked
legitimate writes, and a hook that died with a non-zero exit code.

### graphify — a queryable knowledge graph of the codebase

Evaluated on 2026-08-20 against `Graphify-Labs/graphify` branch `v8` (Apache-2.0, 108.7k stars,
pushed that same day). Hard data from the API, README read raw and filtered, nothing cloned and
nothing installed. It parses code with tree-sitter into `{nodes, edges}`, clusters with
Leiden/Louvain, and writes `graph.json`, `GRAPH_REPORT.md` and `graph.html`.

Problem it solves. The visible output is the HTML, but the product is `graph.json`: the agent asks
`graphify query "..."` and gets the twelve nodes that matter instead of grepping and reading forty
files to rebuild the same thing. Every edge is tagged `EXTRACTED`, `INFERRED` or `AMBIGUOUS`, so
what was read is separable from what was deduced.

Cost. `uv tool install graphifyy` plus `graphify install`. Requires Python 3.10+ and `uv` or
`pipx`; none of the two package managers was present on the machine where this was evaluated.

Status. **Discarded by decision on 2026-08-21** — and the `uv` argument below no longer holds, so the decision does not rest on it. Checked against PyPI that same day: `graphifyy` 0.9.48 is a pure-Python package, `requires-python >=3.10`, every dependency a wheel — `pip install graphifyy` needs neither `uv` nor `pipx`, and pip is the package manager ES0901 names (`normativa/extractos/ES0901.md:678`). The first reason still stands and is the one worth remembering. What follows is the record of the evaluation, not an open question.

Original rejection, 2026-08-20, for two reasons that are about this harness and not about the tool. First,
`graphify claude install` registers a `PreToolUse` hook in the project `.claude/settings.json`, and
`New-SettingsProyecto` (`install.ps1:627`) regenerates that file whole on every `-Update` — the
hook would delete itself on the next harness update, silently. Second, `uv` is not in the ES0901
homologated table; arguable as exempt toolchain, but that is a question for the ASI, not a call
made here. See ADR-0008. Three ideas from it survive the rejection and need no graph at all: the
discrete confidence rubric (0.95 / 0.85 / 0.75 / 0.65 / 0.55, never 0.5 — their own spec documents
that models collapse a continuous range into a binary, over 50 % landing on 0.5 in production); the
`EXTRACTED / INFERRED / AMBIGUOUS` axis, which is `verificado / contradicho / sin-sustento` applied
to edges; and deterministic node ids derived from the full path, which is what stops parallel
subagents from producing ghost duplicates. Those three are worth stealing into `dev-refutador` and
`hu-refutador` whenever either is touched.

### codebase-memory-mcp — the same graph, as an MCP server with no runtime

Evaluated on 2026-08-21 against `DeusData/codebase-memory-mcp` (MIT, 39.7k stars, v0.10.8, pushed
that same day). Same method: API plus raw README, nothing downloaded. A single static C binary with
158 vendored tree-sitter grammars that indexes into SQLite and exposes graph queries over MCP —
`trace_path`, `search_graph`, a Cypher read subset. It ships no LLM: the agent already talking to
you is the query translator.

Problem it solves. The same one graphify solves, without any of graphify's costs. No new runtime,
no API key, no model. Their own measurement: five structural queries at ~3,400 tokens against
~412,000 grepping file by file.

Cost. A 37 MB binary and, if configured, a per-account coordination daemon with a file watcher and
an HTTP UI on `localhost:9749` (`auto_watch` defaults to true). `--skip-config` installs the binary
alone, which is the only variant worth considering here. Uninstall is documented and real.

🔴 **pip does not get around this, and it is the first thing anybody proposes.** The project publishes `codebase-memory-mcp` 0.10.8 on PyPI (`requires-python >=3.8`) and on npm, so `pip install codebase-memory-mcp` looks like a homologated route. It is not: the wheel is **0.01 MB**. Its own description says it *"downloads the selected runtime set from GitHub Releases on first run and verifies it"* — pip delivers the downloader, and the same unsigned native executable lands on disk anyway. Checked 2026-08-21. The blocker was never the package manager; it is the Authenticode signature.

Status. Open, blocked — and it is the deferred trigger named in ADR-0008. It clears every bar
graphify failed: MIT, no runtime, 100 % local, no telemetry and no background network calls of its
own, SLSA 3 build provenance plus Sigstore cosign, fail-open context-only hooks that never deny a
tool call, and it writes to the user-scope `~/.claude.json` rather than the project
`.claude/settings.json` — so it does not collide with `New-SettingsProyecto` the way graphify did.
What blocks it is the machine, not the tool: the Windows binary carries no Authenticode signature
and Microsoft Defender flags it as `Trojan:Script/Wacatac.B!ml`, which the project documents as a
known false positive with evidence. On a GCBA machine with centrally managed Defender that is not
something a developer clears. Also pre-1.0, six months old, 467 open issues. Reconsider if it ships
signed or the organisation homologates it; not before.

### The first walk of the code, and the index it writes

Stated by Nahue on 2026-08-21, and it is the first time the main axis of the harness has been said
out loud as a sequence: *usuario instala harness → elige cuál quiere en su proyecto → el harness
sugiere hacer un primer recorrido del código para registrar en codebase.* The index is ours — an
SDD that walks the whole repo — not the external tool evaluated above.

Problem it solves. Two at once. The agent starts every project blind and rebuilds its picture of
the code by grepping, turn after turn, paying for it every time. And the harness has no first step:
today it installs and then nothing happens until somebody types something, so the moment where it
could be most useful — before anyone knows the codebase — passes unused. This is also the concrete
half of the open item above it, *the workflow of each harness cannot be drawn*: it is the first
band of that drawing.

Cost. Unknown, and it is a capability rather than a fix: an SDD that walks the code, a place to
write, and one line inside `SessionStart` that notices the index is missing. Three decisions were
already taken on 2026-08-21 and are drawn in `docs/mapa/recorrido-mensaje.html`: `SessionStart`
suggests the walk on the first session, not `install.ps1` — the installer runs in a console where
there is no agent to walk anything; the index lives in a **new `docs/codebase/`**, versioned and
inside the repo, kept apart from `docs/conocimiento/` because it is generated and regenerated whole
while that one is written by hand and purged by `flush-memoria`; and Obsidian is a footnote, never
a box, per ADR-0008.

Status. Open, and it is the next thing. Written down because it was defined in conversation and
the drawing alone does not carry the reasons — the choice of `docs/codebase/` over
`docs/conocimiento/` is the one that would be re-litigated first.

### Which PROJECT_CONTEXT fields serve `dev-refutador`, and the two axes the contract does not model

Mapped on 2026-08-24 at Nahue's request, before deciding whether to build steps 3 to 5 of
`QA_Agent_Project_Context_Contract_v1_1.pdf`. Steps 1 and 2 are built — see
`docs/cambios/contexto-de-proyecto/spec.md` — and `project-context.json` today has **no reader**.
The question was whether `dev-refutador` should be the first one.

🔴 **First, the distinction Nahue drew, because it changes the answer.** `dev-refutador` is *not* a
small `dev-qa` and *not* a step toward it. They are siblings on different axes:

| | `dev-refutador` | `dev-qa` (the PDF's) |
|---|---|---|
| Compares | implemented **vs the standard** — ES0901, ES0903, Obelisco | expected **vs implemented** — HU, acceptance criteria |
| Source of truth | the `dev-*` skills | PROJECT_CONTEXT + CHANGE_CONTEXT |
| Executes | nothing. It only reads | yes: boots the system, drives Playwright and the API |
| Verdicts | `cumple` / `incumple` / `sin-verificar` | PASS / FAIL / BLOCKED / INCONCLUSIVE |

Chapter 06 of the PDF says *"separate intended behavior from implemented behavior; the QA Agent
exists precisely to compare both"*. The refuter lives on a third axis the PDF never models:
**regulatory compliance**, which is neither what the product meant to do nor what the code does,
but what the resolution requires.

The mapping, field by field:

| Field | What the refuter would do with it | Where it is |
|---|---|---|
| `meta.repo_revision`, `meta.context_hash` | Anchor every verdict to a snapshot. Today a verdict row says nothing about *when* it ruled, so nobody can tell a stale `cumple` from a current one | emitted |
| `architecture.components[]`, `important_paths[]` | Resolve a batch of files to modules, so the scope of a review is stated instead of implied. It already refuses to widen scope; this is what lets it say what the scope *was* | emitted |
| `sources[].type` | Decide which `dev-*` skill applies: `openapi` pulls `dev-api`, `config` pulls `dev-versiones`, `tests` is not production code | emitted |
| `technology.languages`, `frameworks`, `package_managers` | Decide whether a rule applies **at all**. Obelisco (`dev-pantalla`) is moot on a project with no frontend, and `dev-versiones` needs to know the package manager before it can judge a pin | emitted |
| `gaps_and_conflicts` | The strongest match of the whole contract. Its `missing` / `stale` / `conflicted` are the same asymmetry that makes the refuter default to `sin-verificar`: uncertainty travels instead of being resolved silently | emitted |
| `interfaces[]` | `dev-api`: route naming and versioning, status codes, the error body, the OpenAPI contract | step 4 |
| `identity_and_access` | `dev-identidad`: OpenID against Keycloak, where the session lives, which endpoints stay public | step 4 |
| `environments[]` | `dev-ambientes`: how far a build is from production, which approvals a gate needs | step 4 |
| `business_rules[]`, `functional_model` | **Nothing.** That is intended behaviour and belongs to `dev-qa`. The refuter reports non-compliance only where a standard says something; a free decision of the project is not a finding | step 3 |
| `quality_landscape` | **Nothing.** Existing suites, Playwright and fixtures are assets for whoever *runs* tests, and the refuter runs none | step 5 |
| `project_profile.purpose`, `lifecycle_stage` | Nothing load-bearing. Useful to a person reading the verdict, not to the ruling | emitted |

🔴 **The finding, and it is the reason this entry exists.** The contract has **no place for the
regulatory axis**. `sources[].type` offers `code | functional_doc | prd | mvp | adr | openapi |
config | tests` and none of them is a standard; there is no block saying *which standards govern
this project and at which version*. For a GCBA project that is not a detail: ES0901 tolerates one
previous version of the standard and two or more back stops a deployment, and the homologated
versions of its Annex II are the canonical `sin-verificar` case because the table converted
misaligned and is not citable. Today that lives only inside the `dev-*` skills, which are the same
for every project — so a project pinned to an older standard has nowhere to say so.

Two shapes are worth weighing, and neither is decided: a `compliance` block alongside
`quality_landscape` (`standards[]` with id, version, scope and `source_refs`), or a `standard`
value added to `sources[].type`. The first models the axis; the second smuggles it into a list that
means "where the knowledge came from". The first looks right and costs a schema version.

🔴 **The second axis, found on 2026-08-26 checking the three skills the mapping left out.** Of the
eight `dev-*` skills, `dev-repositorio` is the one the refuter is explicitly told to use —
*"repositorio y entregables"* — and it is the one the contract feeds worst. What it rules on is
branch names (`develop` / `master`), semantic tags with `-BETA`, `-RC` and `-HOTFIX`, the RC that
increments instead of being replaced, the three root files `README.md` / `CHANGELOG.md` /
`UPGRADE.md`, and the `source/` and `scripts/` layout. The contract emits **one** git fact:
`meta.repo_revision`, a bare commit sha. No branch, no tag, no release state — and `sources[].type`
has no value for a delivery artifact, so `CHANGELOG.md` and `UPGRADE.md` land as `functional_doc` or
`config`, and neither is what they are.

So the contract models what the code **is** and not how the repository is **governed and released**,
which is the same shape as the compliance gap above: two axes missing, and steps 3 to 5 do not add
either one. The other two skills are not gaps of the contract and it is worth saying why.
`dev-seguridad` is almost entirely `identity_and_access` and `environments`, which are step 4 — not
missing, just not built; what may have no home even there is the **dated state of the assessment**,
which expires after 20 days of development and is a gate, not a structural fact. `dev-tramites-asi`
is neither: it is a procedure for a person opening tickets at ASI, and the refuter has nothing in a
repository to rule it against.

📌 A third finding came out of the same review and it is a defect, not a proposal, so it went to
`PENDIENTES-FH.md`: the refuter's own sentence names five topics for eight skills, and its rule
about uncovered topics turns the three unnamed ones into `sin-verificar`.

Problem it solves. `project-context.json` is written and nobody reads it, so nothing yet proves
chapter 17's claim that PROJECT_CONTEXT is *"a contract of the harness, not a private detail of the
QA Agent"*. A second consumer on a different axis is exactly the proof — and it is cheap, because
five of the fields it needs are already emitted.

Cost. Small for what is already there: `dev-refutador` gains a step that reads the contract before
grepping, and a column in its output row naming the `repo_revision` it ruled against. Unknown for
the compliance block, which is a schema version and a decision that has not been taken.

Status. Built on 2026-08-29, in `docs/cambios/dev-refutador-lee-el-contrato/`: `dev-refutador` now
reads `docs/codebase/project-context.json` before grepping, uses it as evidence — never as norma —
to scope, decide applicability and pick which skill applies, and its output row names the
`repo_revision` it ruled against. Absent/broken/insufficient contract → the affected conclusions
are `sin-verificar`, never inferred. 7 of its 9 scenarios `sostenido`; the other 2
(`docs/cambios/dev-refutador-lee-el-contrato/lectura.md`) need a real run against a project with a
contract and one without, read by someone who did not build this. Deliberately not given: an
execution tool — no script validates the contract for it, it reads the JSON with `Read` like
everything else, so what it notices about a corrupt contract depends on the model, not a mechanism.

Still open: the compliance axis and the repo-governance axis this entry names — neither gained a
field. Step 3 (`business_rules`) stays outside `dev-refutador`'s reach by design (it's `dev-qa`
territory). What was Recommended is now done; what is left is the reading that proves it works
against a real project, and then deciding whether the compliance axis is worth its own schema
version.

### Classify `dev-harness.py presupuesto` in the tool policy instead of leaving it UNRESOLVED

`presupuesto` arrived with 0.28.0 and the tool policy of Flow Governance (`comun/hooks/lib/tool_policy.py`,
`_harness`) has no row for it, so it falls to `UNRESOLVED_TOOL_CLASS`. Seen during the integration of
Flow Governance with 0.28.0 on 2026-10-05 (`docs/cambios/flow-governance/integracion-0.28.md`). With
the governed task healthy it passes; with the task blocked, a human decision pending or the binding
ambiguous it is denied, even plain `presupuesto` with no flags, which only reads the policy.

Problem it solves. A conservative overblock: someone with a blocked task cannot look at the Context
Bar policy. Not a hole: `--context-defaults` writes `.claude/harness.presupuesto.json`, and
`UNRESOLVED_TOOL_CLASS` already gets the restrictions of `MUTATING`.

Cost. One branch in `_harness` (no flags -> `READ_ONLY`, `--context-defaults` -> `MUTATING`) and its
tests in `63_compuerta_del_flujo.py`. It changes the classification table, not the contract of
`UNRESOLVED_TOOL_CLASS`.

Status. Open. Classified USABILITY / CONSERVATIVE_OVERBLOCK / NON-BLOCKING by the person on
2026-10-05, who asked for no hurried exception during the integration.

### Typed MCP authority targets: let R11 read a wildcard in an MCP only where the field is known

An adapter or extractor that knows, for a specific MCP tool, which of its `tool_input` fields is a
path, a target or a command, so the R11 wildcard analysis of `comun/hooks/lib/tool_policy.py`
(`_patron_alcanza` / `_patron_de_autoridad`, today reached only through `destino_de_autoridad` for
Bash and PowerShell) can run on that value the way it runs on a Bash or PowerShell destination.

Problem it solves. Since the second pass of R11 (Final Qualification, 2026-10-06) a generic MCP is a
declared boundary: `mcp__fs__delete {"path": ".cla*/harness"}` or `mcp__shell__run {"command": "rm
-rf .cla*/harness"}` is not `FLOW_AUTHORITY_PROTECTED`, and only stays `UNRESOLVED_TOOL_CLASS`. With
the governed task healthy it passes. The literal `.claude` / `.git` in any MCP value stays protected.
The first pass globbed every MCP string and denied `SELECT * FROM t` (FP2). Pinned by R11-10, the MCP
part of R11-13 and the MCP row of R11-22 in `tests/casos/70_r11_glob_de_autoridad.py`, and written in
`docs/cambios/flow-governance/final-qualification.md` («La MCP genérica, frontera de R11»).

Decision by the person on 2026-10-06, and it fences this idea: *no global list of MCP field names,
no `path/file/target/destination/command/script` heuristic over arbitrary JSON. Generic MCP values
are not typed authority targets. If closing a concrete MCP requires knowing the semantics of its
fields and the repo does not own that contract, do not invent it in R11.*

Cost. Unknown until a contract source exists: per-tool declarations (a typed table for MCP servers
the harness ships or pins, or the server's own input schema if one becomes reliably available to
the hook), a classification step that hands only typed values to `_patron_alcanza`, and one
test per adapter. It must not reopen a word bag nor change `UNRESOLVED_TOOL_CLASS`. It also covers
B7 (`file:///` with a glob in a generic MCP).

Status. Open, POST_QUALIFICATION_WORK. Out of scope of the Flow Governance qualification by the
person's decision of 2026-10-06; future work.

### Flow governance as its own bounded context

Make the flow (task flow state, required inputs, human intent and decision, session binding, flow
notice, flow gate) its own bounded context in `docs/dominio/modelo-canonico.md`, instead of spreading
its six concepts over Work Intake, Planning and Guardrails.

The tenth context is now Execution (ADR-0014, `docs/cambios/execution-contract/spec.md`, written on
2026-10-08 while integrating that contract with 0.31.0), so the flow would be the eleventh. The
integration did not make the flow a context: the execution admission reads `delegationAllowed` from
the TaskFlowState, which stays in Planning.

Problem it solves. Raised on 2026-10-07 while mapping the six Flow Governance schemas (D7 of
`docs/cambios/integracion-flow-governance-0-31/spec.md`). By the model's own criteria for a context
(language, invariants, owner, data, lifecycle) the flow could stand alone: it has its own
vocabulary, its own derived state and its own gate. Spread over three contexts, nobody reading the
model sees it as one thing.

Cost. ADR-0013 fixed nine contexts and ADR-0014 added Execution as the tenth;
`64_modelo_de_dominio.py` and `65_contrato_de_ejecucion.py` pin the ten. So it is a new ADR (or a
revision of 0013 and 0014), the map of contexts, the six concepts moved, the Planning → Execution
relation, and the tests. No code changes.

Status. Open. Left as an open question in D7 of the integration spec; not decided by anyone yet.

### Run the independent units of a GraphRun in parallel

A GraphRun takes a whole plan to a terminal one WorkUnit at a time (ADR-0016). The idea is to dispatch
together the units whose dependencies are already satisfied, with a bounded number of workers or with
all of them. Written on 2026-10-14 as GP-03 of `docs/cambios/graph-execution/spec.md`.

Problem it solves. The time of a GraphRun is the sum of the time of its Executions, even when the plan
has branches that do not depend on each other.

Cost. It cannot be had without changing Task 4, and the spec of Task 5 says why. The evidence rule is
per project (T4 MD-20) and the working tree is one, so two Executions that overlap make each other's
evidence `CHANGES_UNATTRIBUTABLE`. The guards close both ways of getting there: ME-E47 of Task 4
forbids importing `threading`, `multiprocessing`, `asyncio` and `concurrent`, and E-41 of
`64_modelo_de_dominio.py`, adapted inside ME-E47, lets `subprocess` launch only `git`, `markitdown`,
`taskkill` and the Host. It also multiplies R1, a Host that outlives its engine, by the number of
workers. A Task with its own spec would need: evidence attributed per Execution, a revision of ME-E47
and E-41 with an ADR, and a way to keep the working tree of each Execution apart.

Status. Open, not planned. ADR-0016 chose serial on purpose, and its review clause names parallelism
as one of the reasons to revisit it.

### Keep going with the independent branches after a unit fails

A GraphRun is fail-fast: the first unit that does not end `SUCCEEDED` closes it, and the independent
units that came after it in the order are not run (GC-17 of the Task 5 spec). The idea is to go on with
every unit that does not depend, directly or not, on the one that failed. Written on 2026-10-14 as
GP-04 of that spec.

Problem it solves. A plan with independent branches loses all of them when one fails. A person has to
fix the unit, run `ejecutar --unidad` if the unit has to be retried, and launch the graph again, which
adopts what already ended `SUCCEEDED` and runs the rest.

Cost. A Task with its own spec: which units stay eligible after a failure, what the result says about
the ones left unrun, and a revision of the fail-fast decision of ADR-0016. It does not need
parallelism, and it should not be bundled with it.

Status. Open, not planned. ADR-0016 names it among the reasons to review the decision.

### Serve the normative extracts as a Knowledge Access corpus

Add `normativa/extractos/` as a fifth corpus of Knowledge Access, next to `adr`, `dominio`, `codebase` and
`memoria`, with the state of Normative Sources read without refreshing it. Written on 2026-10-18 as KP-04
of `docs/cambios/knowledge-api/spec.md`; KC-22 of that spec left it out of Task 6 and wrote the rule for
when it comes in: only together with that state, and never as current if its owner does not say so.

Problem it solves. No code reads the content of an extract: `bin/orquestacion/frescura.py:170-180`
(`version_de_extracto`) reads only the version in its header. A consumer that needs a passage of a standard
cannot ask for it with a citation and a revision, as it can for an ADR.

Cost. A catalogue row in `bin/conocimiento/corpus.py`, and an amendment of ADR-0017 and of the canonical
model. The three reasons it was left out are the real cost. There is no consumer. The factory has no
`.claude/harness.fuentes.json` (its `.claude/` holds `agents`, `skills` and `scheduled_tasks.lock`), so
every extract would come out unverified. And the normative gate writes the RefreshAgenda, the SourceState
and downloads, so consulting it is not a read-only act.

Status. Open, not planned. Without a consumer it would be a corpus nobody reads, and Task 6 chose to build
none ahead of the one that needs it.

### A channel from the agents to Knowledge Access

Today an agent reads with `repository.read` and `repository.search`. The idea is to give it Knowledge
Access: either the capabilities `knowledge.lookup` and `knowledge.search`, one per operation like the
`repository.*` pair, with a real provider, or the hybrid, with references in the plan and the content read
through `repository.read`, which needs `orchestration-plan/2.2` and `execution-request/1.1`. The name
`knowledge.retrieve` is discarded because it names the mechanism (KC-46). Written on 2026-10-18 as KP-05 of
`docs/cambios/knowledge-api/spec.md`.

Problem it solves. Knowledge Access exists and no agent can reach it. A pull capability needs a Host tool
that reaches a `.py`: `Bash` is not offered on Windows (`bin/ejecucion/host_claude_code.py:55-61`) and an MCP
server is ruled out by ADR-0008 (`docs/adr/0008-lo-externo-nunca-es-requisito.md:40-41`). Declaring a
capability with no provider would show it as available in every plan and reject it at delivery
(`bin/orquestacion/capacidades.py:28-32`, `bin/ejecucion/admision.py:301-305`).

Cost. It depends on GP-02 (the Host offering a shell tool on Windows, see «`tests.run` is not mapped to
`PowerShell` on Windows, so no unit that asks for it runs there» in `PENDIENTES-FH.md`) or on a spec that
accepts the 2.2 plus 1.1 chain. It touches the Host Adapter, the roster, the permissions and `tools:` of each
agent, two closed contracts, and the guards EX-G11, ME-E49, GE-E65 and KA-E53.

Status. Open, not planned. Task 6 declared no channel (KD-23 and KD-24) because none was needed for the
contract to exist and be proved; it is the direction of Task 7 and Task 8.

### More corpora for Knowledge Access: specs, `Pendientes/` and version notes

Add the specs, `Pendientes/`, `CLAUDE.md` and the version notes as corpora of Knowledge Access, each with its
own root, extensions and derivation. Written on 2026-10-18 as KP-13 of
`docs/cambios/knowledge-api/spec.md`, which left them out of Task 6 (KC-24).

Problem it solves. None today: no consumer asks for them (KC-24). It is written down so that the list of
corpora is not widened out of habit, and is not forgotten when a consumer does ask.

Cost. A catalogue row in `bin/conocimiento/corpus.py` per corpus, a scenario for each, and an amendment of
ADR-0017 and of the `KnowledgeCorpus` concept of the canonical model.

Status. Open, not planned. It comes back with the first consumer that names the corpus it needs.

### An operation that states absence

`lookup` is exact and `search` does not prove absence: an empty `search` does not show that the corpus does
not say it, and even `complete: true` only means that every corpus asked for could be examined by the
strategy in use, not that the examination was exhaustive in meaning. The idea is an operation built to
affirm that something is not there. Written on 2026-10-18 as KP-14 of `docs/cambios/knowledge-api/spec.md`
(KC-38).

Problem it solves. A consumer that wants to say «the docs do not mention X» has nowhere to get it, and the
risk is that it reads an empty `search` as that answer, which the contract forbids.

Cost. A contract of its own, with a definition of «exhaustive» that holds for each retriever, and a
consumer to design it against. It also interacts with Task 7, which brings retrievers that are not lexical.

Status. Open, not planned. KC-38 chose not to build it: no code asserts absence by retrieval today, and it
is to be revisited when the first consumer that needs it appears.

### Measure the suite with and without Defender exclusions

Run the same benchmark pair (serial and parallel, same tree hash, same conditions) twice: with the temporary
directory, the repository and the resource lock excluded from Windows Defender and without. Written on 2026-10-22
as VX-01 of `docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1).

Problem it solves. Risk R15 of that spec: Defender or the indexer can slow the temporary directories and the lock
file of the parallel runner, and it was never measured. Without the number nobody can tell whether an exclusion is
worth asking for, or whether the 0.7089 ratio of 2026-10-22 owes something to it.

Cost. Small in work and large in access: an exclusion needs a policy or an administrator (spec section 8.2), and
the benchmark of a pair takes about 1.5 hours of machine. It touches no file of the repository.

Status. Open, not planned. 6.1 left it out for needing a permission it does not have.

### Run the suite in parallel in CI

Use the parallel runner, or one equivalent, in a continuous integration job. Written on 2026-10-22 as VX-02 of
`docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1).

Problem it solves. Whoever pushes would get the fast result without waiting for a person to run the suite. Today
the gate runs only on the machine of whoever builds.

Cost. Not estimated. A different environment from the one the suite was measured in (a different machine, a
different `PATH`, no Git Bash by default), and it needs the preconditions of the oracle written down first (see
«The preconditions of the oracle are in a version note and not in «The gate» of `CLAUDE.md`» in
`PENDIENTES-FH.md`). The spec declared CI/CD, containers and remote execution «another problem, another machine»
(section 8.2).

Status. Open, not planned. 6.1 is local and Windows PowerShell 5.1 only.

### Run the suite remotely or in shards

Split the case files among several machines or runs, and combine their reports in the same shapes as the oracle.
Written on 2026-10-22 as VX-03 of `docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1).

Problem it solves. The runner of 6.1 is bounded by one machine and by N = 2 on this one; the measured floor of the
suites in a lane (`motor`, 15.8 min on `d86b285`) and the sum of all of them (51.8 min) do not shrink with more
processes on the same machine.

Cost. Large. It needs a way to launch and to collect, the same equivalence rule across machines (same tree hash,
same totals suite by suite, spec section 20.4) and a decision about who trusts a remote green. It touches
`tests/Invoke-Tests-Parallel.ps1` and `tests/Compare-TestRuns.ps1`.

Status. Open, not planned. Out of scope in 6.1 (section 8.2).

### Promote the parallel runner to the oracle

Make `tests/Invoke-Tests-Parallel.ps1` the command that closes a change, a verdict and a release, replacing
`.\tests\Invoke-Tests.ps1` as the gate. It is phase D of the migration in section 28 of
`docs/cambios/verification-pipeline-performance/spec.md`, written on 2026-10-22 as VX-04.

Problem it solves. While the oracle is the only command that closes, every closing pays the serial wall clock
(49:36 on 2026-10-22) and the runner is a feedback tool only.

Cost. A new ADR that replaces ADR-0018, a refutation and the approval of a person. The spec asks for pairs over at
least two Tasks and trees, and for the drift of `30_b4_contabilidad`, `33_bases_de_datos` and `19_contexto` E-29 to
be solved or contemplated. It would change `CLAUDE.md` under «The gate», the refuter, the staff engineer and
`close-a-version`; `install.ps1` would not change.

Status. Open, not planned. It waits for phases B and C to run and for the pairs of evidence; 6.1 only builds phase A.

### A Job Object per worker of the parallel runner

Put each worker of the parallel runner in a Windows Job Object so that killing the runner kills its whole tree.
Written on 2026-10-22 as VX-08 of `docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1).

Problem it solves. Today a cancelled run kills the tree of each worker with `taskkill /T /F` (VD-11, VD-12), but if
the runner itself dies the operating system releases both locks with the load still alive (R20, WU10:CW4 of the
6.1 discovery) and a grandchild can survive and keep something in `%TEMP%` (spec section 18; risk R4). The same
orphans exist in serial: `72_motor_de_ejecucion.py` leaves them on purpose (`72:299-305`).

Cost. Not estimated: a Job Object from PowerShell 5.1, and tests of the cut. The precedent of the repo defers it
«when a real case asks for it» (ME:1697 of the execution engine spec, MP-01 applied to tests).

Status. Open, not planned. It is built when a real orphan appears after a cut; none has been seen.

### The role of the parallel runner in the refutation

Decide whether `harness-spec-refuter` may explore with the runner, and under what rule. Written on 2026-10-22 as
VX-14 of `docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1, section 28 phase C; WU05:B3 of the
discovery).

Problem it solves. A refuter that runs the suite many times pays the serial wall clock each time. The spec's
candidate rule: it explores with the runner, and a `sostenido` that closes cites the oracle or
`python tests\correr.py -k <suite>` and never the runner (ADR-0018 section 4).

Cost. A note in `.claude/agents/harness-spec-refuter.md`, only if it is decided, and the equivalence record of
phase B to rely on. It is phase C of the migration and belongs to Task 8.

Status. Open, not planned. It depends on phase B closing without discrepancies, and on Task 8.

### Choose the suites to run by the files a Task touched, and reuse a result by tree hash

Two ways of running less, not of running faster: pick the case files that a Task's changed files can affect, and
reuse the result of a suite when the hash of its inputs is the same. Written on 2026-10-22 as VX-15 of
`docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1); first named in «The full test suite takes 45
to 70 minutes and every Task pays for it many times» of `PENDIENTES-FH.md`.

Problem it solves. Even with two workers a Task pays 35 minutes each time it runs the whole tree.

Cost. A map from files to suites that nobody has and that goes stale, and a hash of what a suite reads, which the
discovery found to be much more than `tests/` (suites read `comun/`, `harnesses/`, `docs/`, `manifest.json` and
git tags: spec sections 1.3 and 5.2). A wrong reuse is a false green, the one thing the runner must not give.

Status. Open, not planned. 6.1 left it out (section 8.2).

### Wait for the resource lock, with a witness of reentry

Let the runner wait with a deadline for `pesada.lock` when another runner holds it, and add a test witness that a
process can reenter. Written on 2026-10-22 as VX-16 of
`docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1, section 19.3; WU10:D5 and D6 of the discovery).

Problem it solves. Today a second runner exits 2 at once with `LOCK_OCUPADO` and runs nothing; a person who launches
two has to retry by hand.

Cost. Small, but the lock of 6.1 is one operation, try to take, and avoids the probe that takes and releases that
Graph Execution had to remove (N1, `docs/cambios/graph-execution/spec.md:872-899`). Waiting with a deadline means a
loop of such attempts.

Status. Open, not planned. 6.1 chose to fail fast (section 19.3).

### A RAM floor for a parallel run

Set a minimum of free RAM below which the runner or the measurer refuses to start, or lowers N. Written on
2026-10-22 as VX-28 of `docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1, section 5.2).

Problem it solves. The rule of the discovery was «the peak of a parallel run plus 2 GB of margin», and it was
never fixed. The measurer samples `FreePhysicalMemory`, which is that of the whole machine, with no sampling by
process; in the closing pair (2026-10-22) the free RAM fell to 3.20 GB at 2001.7 s of the parallel leg, 8.91 GB
below its first sample, and could not be attributed: 5.5 GB were still free at the end with no process of the run
alive. The other legs bottomed at 11.55 to 14.31 GB.

Cost. Medium. It first needs the run's own consumption measured, by process, to know what the peak is; the floor is
a number after that.

Status. Open, not planned. 6.1 recorded the minima and set no floor (section 5.2).

### Normalize the volatile names of green rows, or declare that the comparator's fifth point does not apply to the real tree

About 129 rows that are `ok` in existing suites carry data that changes on every run in their name: the time in
`57_aceptar_fuentes` E-19, paths of the temporary directory and pids in `63_compuerta_del_flujo` E-28, E-31 and
E-65, and observed values in `75_runner_paralelo`. Written on 2026-10-22 as VX-29 of
`docs/cambios/verification-pipeline-performance/spec.md` (Task 6.1, D-T5).

Problem it solves. Point 5 of the equivalence (section 20.4, same multiset of `(group, name, ok)` rows with
`-Detallado`) can never hold on the real tree, not even between two serial runs: pair 1b of WU03-b
(2026-10-21/22) came out `NO_EQUIVALENTE` only by that point. 6.1 got out of it with D-T5, by running the pairs
without `-Detallado`, so the point is defined and proved on synthetic layouts and is not evaluated on the real one.

Cost. Either rename about 129 rows in their suites, which changes names that tests, specs and verdicts may cite, or
declare in the spec of phase B that point 5 does not apply to the real tree. It has to be decided before phase B.

Status. Open, not planned. It is for phase B (Task 7).
