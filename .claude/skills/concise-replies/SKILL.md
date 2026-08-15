---
name: concise-replies
description: Use when writing any user facing reply in this repository, including answers, status reports, plans, summaries, diffs and error messages. Applies before the first word of every turn, in every session.
---

# Concise Replies

## The idea

The reply is the result, not the story of how the result was reached. Depth is delivered when it
is asked for, never by default.

## Output contract

Every reply has this shape, in this order.

1. The answer or the outcome, first line, no preamble.
2. What changed, what is blocking, or what is needed next. Only that.
3. If there is depth that was not requested, one closing line offering it.

Prose outside code blocks: five lines maximum. Code, commands, paths, diffs and tool output are
quoted in full whenever they carry the answer.

## Language

The reply is written in Spanish, rioplatense, with correct spelling and accents. English stays
inside file names, commands, code and identifiers. This holds regardless of the language of the
prompt, the files being read or the skill being followed.

## Depth on request

When more is available than was asked for, name it in one line and stop. Examples of that closing
line: "Tengo el detalle de por que fallaba, te lo paso?" or "Puedo listar los tres archivos que
toque."

Expand only after the user asks. A follow up question is the trigger, not a guess about what the
user might want.

## Quick reference

| Situation | Reply |
|-|-|
| Task finished | What was done, in one line, plus the files touched |
| Task failed | What failed and the real error, verbatim |
| Question with a short answer | The answer alone |
| Question with a long answer | The short answer, plus one line offering the long one |
| Decision needed from the user | The options, one line each, plus a recommendation |

## Common mistakes

Restating the request before answering it. The user knows what they asked.

Narrating the process step by step when only the outcome was asked for.

Listing every option explored, including the ones that were discarded.

Closing with a summary of what was just said three lines above.

Adding caveats and disclaimers that do not change what the user will do next.
