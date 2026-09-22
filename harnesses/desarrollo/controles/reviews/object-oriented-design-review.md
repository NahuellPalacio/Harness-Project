---
id: object-oriented-design-review
type: REVIEW
rule: D3
---

# Review: object-oriented-design-review

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D3
```

## What it decides

Whether the application code in scope satisfies D3's object-oriented and high-level coding
obligation, using explicit evidence from the implementation.

This is a `REVIEW`, not a `CHECK`, and the reason is the same one G2 already paid for: the
mechanical version of this question — `classCount > 0`, `inheritancePresent`, `isOOP` — reads as
authoritative and verifies nothing. Its structure is validated mechanically and always; the
technical judgment is contributed by whoever reviews and no test can contradict it.

## Owner

Primary owner: `dev-architecture`.

Supporting agents: `dev-backend` and `dev-frontend`, according to the code domain. All three are
resolved against the Agent Registry — a review that names an agent the registry does not declare is
invalid, and the agent is not created.

## Scope input

```yaml
applicationCodePresent: TRUE | FALSE | UNRESOLVED
technologyInventory: []        # from G1. There is no second stack detector
codeEvidence: []
architectureEvidence: []
g2Evidence: []                 # supporting material only
workUnitContext: {}
```

## Evidence

D3 asks how **this system** is built, so the evidence that answers it is the system:

```text
PROJECT_IMPLEMENTATION   what the code actually does — the primary evidence
PROJECT_ARCHITECTURE     documented boundaries and responsibilities
```

🔴 This is the opposite of G2's rule, and deliberately so. G2 asks whether a practice is recognized
*outside*, so an official guide sustains a finding and the project's own code does not. Here an
official guide proves nothing about this codebase. `PROJECT_CONVENTION` does not stand alone either:
that something is done a certain way in the project is not evidence that *this* code does it.

Every material conclusion cites evidence that exists. A finding whose references point at nothing is
structurally invalid.

## Review dimensions

```text
responsibility encapsulation
cohesion
controlled coupling
abstraction boundaries
domain / application / service responsibilities
framework-native object, component and service organization
procedural concentration
maintainability of collaboration
```

🔴 These are **operational review dimensions, not additional quoted requirements of ES0901**. The
standard says one sentence and that sentence enumerates none of this. Citing them as if they were
the norm would be inventing normative text.

## Finding states

```text
ADOPTED
OBSERVATION
DEVIATION
EVIDENCE_MISSING
TECHNOLOGY_PARADIGM_CONFLICT
JUSTIFICATION_PENDING
```

A deviation is weighed by `materiality`:

```text
MATERIAL      the organization of the code contradicts the obligation   → NON_COMPLIANT
MINOR         deviations that do not change the character of the design → COMPLIANT_WITH_OBSERVATIONS
not declared  nobody said how much it weighs                            → REVIEW_INCOMPLETE
```

🔴 A deviation with no declared materiality does not resolve to the soft side. Defaulting to "it
was probably minor" is how a `NON_COMPLIANT` becomes an observation without anybody deciding it.

## Results

```text
COMPLIANT
COMPLIANT_WITH_OBSERVATIONS
NON_COMPLIANT
REVIEW_INCOMPLETE
```

The result is **calculated** from the findings and their evidence, never declared by whoever writes
the review.

## Technology-paradigm conflict

When application code is present and the selected technology or implementation paradigm materially
conflicts with the obligation, the finding is `TECHNOLOGY_PARADIGM_CONFLICT` and the review does not
reach `COMPLIANT`.

It does not make the rule `NOT_APPLICABLE`, and it does not approve an exception: the authority that
approves one does not exist here. The conflict is preserved and requires architecture or human
resolution.

## Boundaries

```text
G2 COMPLIANT                != D3 COMPLIANT
a named design pattern      != D3 COMPLIANT   — that is P2, and it has its own control
style and linting in green  != D3 COMPLIANT   — that is P3, and it has its own control
G1 HOMOLOGATED              != D3 COMPLIANT
```

Evidence is reused across rules; results are not. This review emits no verdict belonging to any
other rule.
