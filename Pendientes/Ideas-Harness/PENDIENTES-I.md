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
