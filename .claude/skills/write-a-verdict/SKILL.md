---
name: write-a-verdict
description: Use when harness-spec-refuter has emitted its verdicts on a change and they have to be recorded. How to write docs/cambios/<slug>/verificacion.md — its table, what a contradicho requires, and why the file existing closes nothing.
---

# Write a Verdict

## The idea

`verificacion.md` is what closes a change according to
[ADR-0006](../../../docs/adr/0006-sdd-como-metodo-de-los-proyectos.md): the per-scenario verdict of
whoever verified, who is not whoever built.

🔴 **You write this file, the refuter does not.** `harness-spec-refuter` declares
`tools: Read, Grep, Glob, Bash` — no `Write`, no `Edit` — on purpose. It runs the tests and rules;
recording the ruling is the job of whoever asked for it. That separation is scenario E-20 of
`docs/cambios/sdd-capacidad/spec.md`.

## Where it goes

```
docs/cambios/<slug>/verificacion.md
```

Beside the `spec.md` it rules on. Take `docs/cambios/hooks-en-python/verificacion.md` as the worked
example of everything below.

## The header

```markdown
# Verificación — <el mismo título que la spec>

**Estado:** cerrado · **Fecha:** 17-08-2026 · **Versión:** 0.13.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-…): el veredicto por
escenario de quien verificó, que no es quien construyó. <Quién emitió los veredictos, cuándo, y
corriendo qué.>

**Resultado: 30 escenarios sostenidos, 1 contradicho.**
```

The result line goes in the header, in bold, with the counts. Somebody who reads only that line has
to know how the change came out.

## The table

One row per scenario in the spec. Five columns, none omitted.

```markdown
| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Mismo veredicto que PowerShell, caso por caso | sostenido | sí, específico | `04_secretos.py`, 33 casos del testigo |
| E-29 | El p50 de `pre-tool-use` por debajo de 400 ms | **contradicho** | sí, medido | medición manual y `-Doctor` |
```

| Column | Rule |
|---|---|
| `#` | The id, exactly as the spec writes it |
| `Escenario` | The assertion, shortened. Not rewritten — shortened |
| `Veredicto` | `sostenido` · `contradicho` · `leído` · `sin-sustento`. A `contradicho` goes in **bold** |
| `Rojo visto` | Taken from the spec, never invented. Seen in the wild: `sí` · `sí, específico` · `sí, de módulo` · `sí, las dos mitades` · `sí, medido` · `no consta` |
| `Dónde se prueba` | The test file, and what about it. If it was read and not run, say so |

The four verdicts, and what each one costs:

| Verdict | When | What it means |
|---|---|---|
| `sostenido` | A test names the scenario, it was run, and it passed | The scenario stands |
| `contradicho` | It was run and it failed, or the behaviour differs | Back to work before closing |
| `leído` | The scenario is marked `· verificación: lectura` and a dated reading by a named non-builder says what was observed | It stands on a reading, not on a test |
| `sin-sustento` | It could not be established | Open, with what has to be looked at |

🔴 **Count `leído` apart from `sostenido`, in the header line and everywhere else.** "13
sostenidos, 9 leídos" and "22 sostenidos" do not say the same thing, and
[ADR-0009](../../../docs/adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
exists so that difference is legible in the count instead of hidden inside it. Name where
the reading lives —`lectura.md`— and who signed it, the same way the other verdicts name
their test.

🔴 **A scenario with no test that names it is `sin-sustento`, never `sostenido`.** The asymmetry
that governs this, from `hu-refutador`: marking `sin-sustento` something that was there costs
somebody looking again — cheap. Marking `sostenido` something that was not there ships the
invention with the seal of verified — very expensive. When in doubt, always the cheap side.

Under the table, the note that keeps the mark honest:

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## What a `contradicho` requires

Its own `##` section, named after it — `## E-29, el escenario contradicho` — with the measurement
in a fenced block, the cause, and **the decision taken**.

🔴 **The threshold does not move to make the result fit.** The precedent is E-29: the scenario
stayed contradicted and in plain sight, the 400 ms threshold was not lowered to 600, and `-Doctor`
was put to watch the number on every run. *Un umbral que se acomoda al resultado deja de medir.*

## The three closing sections

| Section | What it holds |
|---|---|
| `## Lo que la verificación encontró y no habría encontrado un test verde` | Numbered. This is what justifies the role existing. If it found nothing, write that |
| `## Lo que queda abierto, anotado y no escondido` | Naming `Pendientes/Fix-Harness/PENDIENTES-FH.md` as where each loose end now lives — see `note-a-pending` |
| `## Lo que ningún test cubre y se mira con los ojos` | What only a person opening a real session can confirm |

## What closes and what does not

```
verificacion.md sin contradicho ni sin-sustento -> CERRADO
verificacion.md con alguno de los dos           -> EN CURSO
```

📌 **Un `verificacion.md` que existe no cierra nada.** A verdict with findings sends the change back
to `EN CURSO`, which is where they get resolved: either the code was wrong, or a test was missing,
or the scenario was not verifiable as written. Taking the file's existence as closure would turn
the verifier into a formality.

The exception exists and has a precedent: a `contradicho` can close if the decision is written down
with its number, as E-29 did. It is not a loophole — it is a documented failure to comply, and it
also goes into the CHANGELOG under its own heading.

All your output in Spanish, like the rest of the harness.
