# Signal: securityHomologationPresent

## Purpose

Resolve ES0902 C2 applicability without treating every repository state as an approval gate.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when authoritative evidence establishes that the governed application/release is subject to security approval/homologation for the current lifecycle gate.

Evidence may include:

```text
promotion target beyond QA
security assessment workflow/request
release/homologation context
ES0901 Annex V assessment trigger
project/change-control evidence requiring security approval
official assessment package context
```

## FALSE

Use only when authoritative scope evidence establishes that C2 does not apply to the governed item.

Do not use FALSE merely because:

```text
the WorkUnit is still in DEV
no approval file was found
no assessment request has been created yet
the project team did not mention security
```

Missing approval evidence is not non-applicability.

## UNRESOLVED

Use when lifecycle/promotion/security-homologation applicability cannot be established.

## Reuse

If an existing lifecycle/security-assessment signal already expresses exactly this fact, reuse it rather than creating duplicate producers.

## Evidence

Preserve:

```text
source
scope
target environment/lifecycle gate
assessment trigger evidence
reference
```
