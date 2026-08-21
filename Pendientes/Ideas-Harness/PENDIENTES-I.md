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

Status. Rejected, for two reasons that are about this harness and not about the tool. First,
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
