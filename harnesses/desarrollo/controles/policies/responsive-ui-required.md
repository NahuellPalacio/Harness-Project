---
id: responsive-ui-required
type: POLICY
rule: D4
---

# Policy: responsive-ui-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D4
```

The rule is one sentence: application code must be responsive, adapting to the device it is viewed
on. It names no size, no device model and no number of viewports, and neither does this policy.

## Applicability

```text
frontendPresent = TRUE        → applies
frontendPresent = FALSE       → NOT_APPLICABLE
frontendPresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Applicability is resolved from an evidence-backed signal before this policy runs. Not finding a
frontend directory is not `FALSE` unless project coverage is known to be complete.

## Statement

When applicable, the frontend must keep its layout and its content usable across the representative
device and viewport classes defined for the application. It must not rely on a single fixed viewport
or on a desktop-only layout when the application is meant to be viewed across devices.

## The viewport matrix is configuration, not norm

The matrix is operational configuration of the project. It is explicit, it is evidence-backed, and
it declares where it comes from:

```text
PROJECT_UX_REQUIREMENT
GCBA_DESIGN_SYSTEM_GUIDANCE
SUPPORTED_DEVICE_REQUIREMENT
TEAM_APPROVED_TEST_PROFILE
```

Without a defensible matrix the answer is `VIEWPORT_MATRIX_UNRESOLVED`.

🔴 **No breakpoint value is attributed to this rule.** The standard defines none. Writing one into
this harness and verifying it would read as though the norm required it, and the first person to see
it would believe that. If another authoritative GCBA source defines values, they come from there and
they are cited.

## What never proves compliance on its own

```text
Bootstrap is installed
the design system is installed
CSS media queries exist
the framework supports responsive layouts
a mobile stylesheet exists
somebody says it is responsive
one desktop screenshot
```

These may be supporting evidence. Rendered behaviour is what answers the question, and it is
verified by running the interface, not by reading the repository.

## Operational verification dimensions

```text
layout reflow and adaptation
content visibility
material clipping or overlap
horizontal overflow caused by layout defects
navigation usability
form and control usability
responsive media behaviour
critical action reachability
```

🔴 These are **operational dimensions of verification, not additional quoted requirements of
ES0901**. The standard says one sentence and that sentence enumerates none of them.

## Evidence it requires

```yaml
application: {id, environment}
build: {id, runtime}
testTarget: {available}
viewportMatrix: {source, viewports: []}
results: []        # one per required viewport and flow, with its evidence
evidence: []       # tied to the build and runtime that were tested
```

The evidence is an input. Without it the policy resolves to `EVIDENCE_INCOMPLETE` — never to
compliant.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
EVIDENCE_INCOMPLETE
VIEWPORT_MATRIX_UNRESOLVED
```

## Boundaries

```text
G1                → whether the design system is approved and on a homologated version
D4                → whether the interface adapts to the device
accessibility     → a separate obligation, with its own skill and its own path
```

An approved design system does not satisfy D4, and D4 says nothing about accessibility. Adapting to
a screen width and being usable with a screen reader are two different questions.

## Verified by

`responsive-behavior`

## Owners

`dev-frontend`, with `dev-quality` supporting the execution.
