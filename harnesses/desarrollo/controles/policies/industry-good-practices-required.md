---
id: industry-good-practices-required
type: POLICY
rule: G2
---

# Policy: industry-good-practices-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: G2
```

## Statement

A development must adopt the recognized industry good practices applicable to each technology it
uses.

## What it constrains

Using an approved technology while ignoring the practices its own official documentation, a formal
standard or recognized industry guidance establishes for it.

## Why it has no Check

The obligation cannot be reduced to a mechanical verification without lying. It requires deciding
which practices exist, which apply to this technology and version, whether the implementation
adopts them, and whether a deviation is justified. A function named `goodPractices()` returning
`true` reads as authoritative and verifies nothing.

The obligation is verified by a `REVIEW`, which is a first-class control type precisely for this.

## Boundary

Passing G1 — the technology and version are homologated — does not satisfy this policy. They are
different questions: one asks whether the tool is allowed, this one asks whether it is used well.

G2 is broad, and that breadth is its risk. A concern that already has its own normative rule —
`D3`, `P2`, any other — stays with that rule and is not absorbed here.

## Verified by

`technology-practice-review`

## Owner

`dev-architecture`
