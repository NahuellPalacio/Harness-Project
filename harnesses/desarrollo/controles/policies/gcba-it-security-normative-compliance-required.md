---
id: gcba-it-security-normative-compliance-required
type: POLICY
rule: O1
---

# Policy: gcba-it-security-normative-compliance-required

## Normative Source

```yaml
source:
  standard: ES0902
  version: "6.2"
  section: "3"
  rule: O1
  ruleKey: ES0902.O1
```

> *"Se deben respetar los principios y normativas vigentes de TI del GCABA."*

## Applicability

`ALWAYS`. Zero applicability signals. There is no condition under which a governed solution is
exempt from the IT norms of the organism that runs it.

## Statement

The governed solution must be evaluated against the applicable authoritative GCBA IT principles
and normative sources.

**The baseline is not guessed.** Which sources exist, who issued them, whether the harness holds
their authoritative content and whether they are still current are all read from
`reglas/gcba-it-normative-baseline.json`. Nothing about a source is inferred from the standard
that cites it.

## What it constrains

Every source the baseline declares is applicable. There is no mechanism to declare that one does
not apply: deciding which of them reach a given work unit is normative interpretation, and it would
need authoritative evidence that nobody produces today.

If an applicable source is referenced and its authoritative content or its current status is not
available, O1 must not be reported fully compliant.

## Reuse, never re-execution

O1 is answered with the results ES0901 and ES0902 already produced. Existing normative outcomes are
consumed as evidence for O1. No control is re-run under O1's name — two executions of the same
control are two answers to the same question, and the day they differ both will be right.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NORMATIVE_BASELINE_UNRESOLVED
EXTERNAL_NORMATIVE_CONTEXT_REQUIRED
NORMATIVE_SUPERSESSION_UNRESOLVED
EVIDENCE_INCOMPLETE
```

Only `SATISFIED` and `NON_COMPLIANT` are conclusions. The other four say what is missing, and none
of them is a pass.

## Why it has no Check

"Respect the current IT principles and norms of the GCABA" does not reduce to a mechanical
assertion over a repository without lying. What can be checked mechanically — a technology, a
version, a token, a session timeout — is already some other rule of ES0901 or ES0902, and O1
consumes those results. What is left is exactly the part that needs judgment over explicit
evidence, which is what a `REVIEW` is for.

Inventing a Check for O1 would produce a function that reads authoritative and verifies nothing.

## Contractual exception

The override mechanism is the standard-level one of ES0902, unchanged: it requires **contract
evidence and ASI approval evidence, both**. Either half alone removes nothing, and local project
configuration is neither half — a project that exempts itself by writing a file in its own
repository does not have an exception, it has a file.

## Boundary

A `SATISFIED` outcome is never an official security approval. Official approval of a solution is
external evidence, produced by the DGSEI circuit that ES0902 §4 keeps separate from the automated
system.

## Verified by

`gcba-it-security-normative-review`, resolved by
`bin/orquestacion/linea_base.py`.

## Owner

`dev-security`.
