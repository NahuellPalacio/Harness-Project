---
name: note-a-pending
description: Use when something appears that will not be done now — a defect, a loose end, a proposal. Where it goes between PENDIENTES-FH.md and PENDIENTES-I.md, and the exact format each one takes.
---

# Note a Pending

## The idea

Both files under `Pendientes/` are the source of work for whoever improves the harness. Written in
English, like the rest of `.claude/`. An item that closes **leaves the file** and lands in its
version note — see `close-a-version`.

🔴 **The distinction is commitment, not size.** `PENDIENTES-FH.md` is work that will be done.
`PENDIENTES-I.md` is a proposal that may never be built.

| | File | What lives there |
|---|---|---|
| Fix | `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Bugs, loose ends, capabilities half-built, verification that was not done |
| Idea | `Pendientes/Ideas-Harness/PENDIENTES-I.md` | Proposals not yet decided |

An idea that gets accepted **moves** to the fix file as work with a fix. An idea that gets rejected
stays where it is, with its reason, so it is not proposed again.

## A fix entry

A `###` heading under the thematic `##` section it belongs to. Current sections: *Missing
measurement* · *Incomplete capabilities* · *Verification that was not done* · *Outside the harness,
written down so it is not lost*. Add a section rather than force an item into the wrong one.

There is no status field, no priority field, no assignee, no date field. The heading is a sentence
stating the defect, then free prose: what happens, the evidence with its dates and numbers, and a
paragraph opening with `Fix.` when a remedy is known.

```markdown
### The always loaded cost of agents and skills is neither measured nor capped

Measured by hand on 2026-08-14: 15 pieces, around 1540 tokens, average 103 per piece, estimating
one token every four characters of `name` plus `description`, paid on every turn. Meanwhile
`CLAUDE.md` has five caps with a check that warns. This is exactly the boundary the harness
claims to guard and does not measure. Nothing stops the next piece from doubling that number.

Fix. `-Doctor` measures and reports the total; new cap `techoAssetsSiempreCargados` in
`comun/manifest.json`. It warns, it never blocks.
```

📌 **Write it so it can be picked up cold.** The evidence is the part that decays: a number without
its date, or a symptom without the command that shows it, is unusable in three weeks.

If the remedy is not known, do not invent one. A `###` with no `Fix.` paragraph is honest; a `Fix.`
that was guessed sends the next person down a road nobody checked.

## The priority table

`## What to take first`, at the top of the fix file. *"Ordered by risk times cost, not by section.
The sections below group by theme; this is the running order."*

```markdown
| | What | Why now |
|---|---|---|
| 1 | Two installer tests break versioned files | It can leave `pre-tool-use.py` — the only blocking rule of the harness — broken in the tree, and four agents were killed by a watchdog during 0.13.0 |
```

🔴 **The ranks are positions, not labels.** Inserting at 4 pushes everything below down one;
removing a row closes the gap. A table with two rows numbered 3 has stopped being an order.

Not every item needs a row — the table indexes the ones that are actually queued. Under it goes a
prose paragraph tying the ranks to releases (*"Items 1 and 2 are what 0.13.1 is for"*), and it gets
rewritten when the ranks move.

## An idea entry

The ideas file declares its own format, and it is four prose paragraphs led by a fixed word:

```markdown
### Title of the idea

What it is, in two or three lines.

Problem it solves. Why the harness is worse off without it.

Cost. Rough estimate, and what it touches.

Status. Open, accepted or rejected, with the reason.
```

`Status.` is the state machine: `Open` · `accepted` · `rejected` — 🔴 **always with the reason**. A
rejection without its reason gets proposed again in two months, which is the whole point of keeping
it.

When an idea is somebody's framing rather than a task, say who said it and when, and quote them:

```markdown
Stated by Nahue on 2026-08-17, and it is the sharpest description of the problem so far: *if you
draw what each harness does, the workflow is not clear.*
```

📌 **Parking something is a legitimate outcome.** `Status. Open, parked by Nahue's own call: we
will look at this later.` — written down so the framing is not lost, which is what is worth
keeping.

## Where an item comes from

Most of them come out of a verdict. `verificacion.md` has a section
`## Lo que queda abierto, anotado y no escondido` whose job is to name this file as the destination
— see `write-a-verdict`. The other source is a version note's `## Lo que quedó abierto`.

🔴 **An open item is written down, not remembered.** Something that survives only in the
conversation is gone at the next compaction.

All your output in Spanish, like the rest of the harness.
