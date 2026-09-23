# ES0902 v6.2 §3 O1 — GCBA IT Normative Governance

## Purpose

Operationalize ES0902 v6.2 §3 O1:

> *"Se deben respetar los principios y normativas vigentes de TI del GCABA."*

O1 is an `ALWAYS` governance umbrella rule. It cannot be reduced to a source-code Check.

## Matrix Binding

The binding is the one the ES0902 matrix already carries. It is not modified by this package:

```yaml
ruleKey: ES0902.O1
applicability:
  mode: ALWAYS
  signals: []
primaryAgents:
  - dev-security
policies:
  - gcba-it-security-normative-compliance-required
checks: []
reviews:
  - gcba-it-security-normative-review
```

## Normative Baseline

`reglas/gcba-it-normative-baseline.json` is a **supporting governance registry**, not a normative
matrix. It declares no rules, classifies nothing, and nobody resolves applicability against it. It
says two things about each source, and only two: whether the harness holds its authoritative
content, and whether it is on record as still current.

Loaded:

```text
ES0901  v6.3   Estándar de Desarrollo
ES0902  v6.2   Estándar de Seguridad
```

Declared by ES0902 and not loaded:

```text
Resolución 177-ASINF-2013
Resolución 239-ASINF/2014
N° 12/ASINF/17
```

🔴 Their content is not transcribed, not summarized and not inferred from the text that cites them.
An invented resolution reads exactly as authoritative as a real one.

## Fail Closed

```text
applicable source not loaded        ->  EXTERNAL_NORMATIVE_CONTEXT_REQUIRED
currency / supersession unknown     ->  NORMATIVE_SUPERSESSION_UNRESOLVED
baseline missing or unreadable      ->  NORMATIVE_BASELINE_UNRESOLVED
```

None of the three can produce `COMPLIANT`.

## Reuse of Existing Results

O1 consumes the ES0901 and ES0902 outcomes that already exist, declared as evidence. No control is
re-executed for O1 alone.

A failing applicable normative outcome prevents `COMPLIANT`.

## Contract Override

The mechanism is the ES0902 standard-level one, reused unchanged:

```text
contract evidence   +   ASI approval evidence   ->  the obligation is lifted, and recorded
contract evidence alone                         ->  nothing is lifted
ASI approval alone                              ->  nothing is lifted
local project configuration                     ->  neither half, ever
```

A granted exception does not make the result disappear: it becomes an observation, and the
exception travels attached to it.

## Review Contract

```text
COMPLIANT
COMPLIANT_WITH_OBSERVATIONS
NON_COMPLIANT
REVIEW_INCOMPLETE
```

O1 is a governance Review, not an automatic code-quality score.

## Official Approval Boundary

`COMPLIANT` on O1 never sets `SECURITY_APPROVED` or `APPROVED`. Official security approval remains
external evidence, produced by the circuit ES0902 §4 keeps separate from the automated system.

## Agent / Skill Boundary

No agent and no skill is created or modified. `dev-security` remains the owner of the row, with the
four skills it already has.

## Where it lives

```text
reglas/gcba-it-normative-baseline.json                              the sources and their status
schemas/gcba-it-normative-baseline.schema.json                      its contract
controles/policies/gcba-it-security-normative-compliance-required.md  the policy
controles/reviews/gcba-it-security-normative-review.md                the review
bin/orquestacion/linea_base.py                                        the resolution
```
