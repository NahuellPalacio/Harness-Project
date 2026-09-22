---
id: high-level-oop-design-required
type: POLICY
rule: D3
---

# Policy: high-level-oop-design-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D3
```

The rule is one sentence: object-oriented programming, implemented with high-level coding and good
practices. It does not enumerate anything, and neither does this policy.

## Applicability

```text
applicationCodePresent = TRUE        → applies
applicationCodePresent = FALSE       → NOT_APPLICABLE
applicationCodePresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Applicability is resolved from an evidence-backed signal before this policy runs. Absence of
discovered source files is not `FALSE` unless repository coverage is known to be complete.

## Statement

Application code in scope must demonstrate object-oriented and high-level design, rather than
low-level, unstructured or purely procedural organization that contradicts the rule.

## What it does not prescribe

Class counts, inheritance depth, a pattern catalogue, a layering diagram or a specific framework.
The rule is about how responsibility is organized, and there is more than one defensible way to
organize it in every language this harness will meet.

## What never proves compliance on its own

```text
classes exist
inheritance exists
an ORM is used
the framework is object-oriented internally
a pattern name appears in the code
the code compiles
the tests pass
an agent says the design is clean
```

Each of these may be evidence. None of them is the answer. A system with two hundred classes and
all of its logic in one three-thousand-line helper satisfies every line above.

## Verified by

`object-oriented-design-review` — a **REVIEW**, not a check. There is no mechanical check for this
rule and none is created: `classCount > 0` reads as authoritative and verifies nothing.

## Evidence it requires

```yaml
technologyInventory: []        # reused from G1, never re-detected
codeEvidence: []               # what the implementation actually looks like
architectureEvidence: []       # boundaries and responsibilities, where documented
g2Evidence: []                 # optional, as supporting material only
workUnitContext: {}
```

The evidence is an input. Without it the policy resolves to `REVIEW_INCOMPLETE` — never to
compliant.

## Technology conflict

If application code is present and the selected technology or paradigm cannot reasonably
demonstrate the obligation, the answer is `TECHNOLOGY_PARADIGM_CONFLICT`.

🔴 It is not `NOT_APPLICABLE` — the rule still applies, there is code. It is not an approved
exception, because the authority that approves one does not exist in this harness. It is preserved
and it requires architecture or human resolution. Reinterpreting the rule so the already-chosen
technology fits is the shortcut this state exists to close.

## Boundaries

```text
G1 → technology and version homologation
G2 → recognized industry practices per technology
D3 → object-oriented and high-level design
P2 → standard design patterns
P3 → unified coding style
```

A control from one rule may supply evidence to another; no compliant result is ever inherited.
`G2 COMPLIANT` is not `D3 COMPLIANT`, a Strategy in the code is not `D3 COMPLIANT`, and a green
linter is not `D3 COMPLIANT`.

## Owners

`dev-architecture`, with `dev-backend` and `dev-frontend` supporting according to the code domain.
