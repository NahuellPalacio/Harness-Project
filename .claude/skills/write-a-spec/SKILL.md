---
name: write-a-spec
description: Use when starting any change to the harness in this repository, before writing code. How to write docs/cambios/<slug>/spec.md — its sections, its verifiable E-nn scenarios and the rojo visto mark.
---

# Write a Spec

## The idea

A spec says **what gets built and how it is proved to comply**, before anything is built. It is
written first because it is what somebody else will judge the work against — and if the criteria
are derived from the code that already exists, the verification proves nothing.

The method is [ADR-0006](../../../docs/adr/0006-sdd-como-metodo-de-los-proyectos.md):

```
especificar   que se construye y como se prueba que cumple
construir
testear       los tests salen de la spec, con el codigo ya armado
verificar     alguien distinto contrasta contra la spec
```

🔴 **Whoever specifies is not whoever verifies.** The spec is the contract handed to
`harness-spec-refuter`, which will run the tests and rule against it. Write it for that reader.

## Where it goes

```
docs/cambios/<slug>/spec.md
```

`<slug>` is free — a short name in kebab-case describing the change (`hooks-en-python`,
`sdd-capacidad`). It is not a ticket key. The folder is versioned and diffable; a spec that lives
in `.claude/` of an installed project is erased by the next `-Update`, and something that can be
lost is not a source.

## The sections

Take them from `docs/cambios/sdd-capacidad/spec.md`, which is written in the format it introduces.

| Section | What goes in it |
|---|---|
| `# <Título>` + `**Estado:** especificado · **Fecha:** …` | The header line |
| `## Qué problema resuelve` | What the harness cannot do today, concretely. Numbers and dates if there are any |
| `## Qué queda afuera` | Bulleted exclusions, **each with its reason**. This section is load-bearing: it is what stops the change from growing while it is being built |
| `## Las decisiones, y por qué` | One `###` per decision. Especially the ones that discarded an alternative: what was considered and why it was left out |
| `## Qué se construye` | A table `\| Artefacto \| Qué hace \|`, with real paths |
| `## Escenarios verificables` | The heart of the file. Grouped by `###` theme |
| `## Cómo se verifica` | Which scenarios go through the suite and which are read by a person, with the reason |
| `## Riesgos conocidos` | What can go wrong that this design does not prevent |

## The scenario format

```
- **E-01** — Los cuatro hooks salen con código 0 siempre: con evento válido, con stdin vacío y
  con JSON roto. · rojo visto: no consta
```

Bullet · bolded correlative id · em-dash · the assertion in Spanish · the mark. Insertions after
the fact get a letter: `E-23b`, `E-25b`.

🔴 **A scenario is an assertion somebody can contradict.** "El instalador funciona bien" is not a
scenario. "Tras `-Update` no quedan `.ps1` huérfanos" is. If you cannot picture the test that would
fail, it is not written yet.

The residual risk ADR-0006 names and has no mechanical defence against: *"una spec escrita para
pasar el check — escenarios tan vagos que cualquier test los satisface."* This section is where you
are the defence.

## The `rojo visto` mark

Every scenario carries it. Two values, and only two:

| | |
|---|---|
| `si` | The code was deliberately broken, the test was seen failing, and it was restored |
| `no consta` | It was not done, or nobody recorded it |

📌 **`no` and `no consta` are the same thing to whoever reads it**, and offering three values
invites picking the one that looks best. So there are two.

The mark is written as `no consta` when the spec is written — it turns to `si` during the test
phase, when the code is broken on purpose. 🔴 **It is a declaration, not a check.** No check can
know whether somebody broke the code. What it buys is that the absence is visible: the refuter
reports the mark beside every verdict, and a `sostenido` with `no consta` is still `sostenido` —
but whoever reads it knows what it is worth.

## Before you call it written

- Every scenario has a unique id, and the ids are correlative.
- Every scenario carries its mark.
- `## Qué queda afuera` has at least one entry with its reason. A change with nothing left out has
  not been scoped.
- No scenario describes the implementation. It describes the observable behaviour.
- The tests that will come later must name their scenario id in the title or in a comment. That is
  what makes the trace visible in both directions.

All your output in Spanish, like the rest of the harness.
