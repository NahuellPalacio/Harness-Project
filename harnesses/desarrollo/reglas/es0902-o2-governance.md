# ES0902 O2 Governance Package

## Purpose

Operationalize ES0902 v6.2 §3, rule O2:

```text
O2 — El control de la seguridad informática debe estar a cargo de un organismo perteneciente al GCABA.
```

## Matrix Binding

The installed ES0902 matrix declares:

```yaml
ruleKey: ES0902.O2
category: ORGANIZATION

applicability:
  mode: ALWAYS
  signals: []

primaryAgents:
  - dev-security

policies:
  - gcba-security-control-authority-required

checks:
  - security-control-authority-evidence

reviews: []
```

Do not rename these identifiers.

## Applicability

O2 is `ALWAYS`.

It has no applicability signal.

## Core Interpretation

O2 is an organizational-authority requirement, not a code-security rule.

The question is not:

```text
"Does dev-security run security checks?"
```

The question is:

```text
"Is the security-control responsibility for this governed scope
assigned to an organization that is demonstrably part of GCABA?"
```

## Authority vs Execution

Separate:

```text
CONTROL AUTHORITY
→ owns / governs the security-control responsibility

EXECUTION
→ may perform scans, reviews, remediation, evidence preparation
```

A contractor, development team, vendor, external assessor, automated scanner, or Harness Agent may execute security activities without becoming the O2 authority.

O2 is satisfied only when the control authority is evidence-backed as a GCABA organization.

## Harness Boundary

The following can never satisfy O2 by themselves:

```text
dev-security Agent
security Skill
automated scanner
CI security job
repository owner
vendor security team
project developer
external consultant
```

The Harness may prepare evidence and verify authority evidence.

It must not appoint itself or any Agent as the official security-control authority.

## Project-Scoped Authority Evidence

Security-control authority is project/scope evidence.

The Harness must not ship with a pre-filled project authority.

Use a project-owned evidence record validated by `security-control-authority.schema.json`.

No authority record:

`SECURITY_CONTROL_AUTHORITY_UNRESOLVED`

## Evidence Requirements

A valid authority claim must establish at least:

```text
organization identity
GCABA membership
security-control responsibility
scope
authoritative source/provenance
effective/current status
```

Do not infer GCABA membership from:

```text
organization name
email domain
repository namespace
person's employer text
project naming
network location
```

Membership must be supported by authoritative organizational/project evidence.

## Evidence Source Classes

Acceptable evidence may include, depending on availability:

```text
OFFICIAL_GCBA_DOCUMENT
OFFICIAL_GCBA_ORGANIZATIONAL_SOURCE
OFFICIAL_SECURITY_WORKFLOW
PROJECT_CONTRACT_OR_ACTA
ASI/DGSEI_PROJECT_EVIDENCE
OTHER_AUTHORITATIVE_GCBA_SOURCE
```

Harness-generated files, Agent assertions, comments, README text, or user-entered labels are context but not sufficient authority evidence by themselves.

## Delegation

Execution may be delegated.

Example:

```text
GCABA security organization
        ↓ owns/control authority
external vendor
        ↓ executes scan
Harness/dev-security
        ↓ prepares evidence
```

This can satisfy O2 if the controlling GCABA organization and responsibility are evidenced.

This cannot satisfy O2:

```text
external vendor
        ↓ sole security-control authority
no GCABA controlling organization
```

## Multiple Authorities

Multiple GCABA organizations may be involved when responsibility is scoped.

Example:

```text
application security control
→ organization A

infrastructure security control
→ organization B
```

That is acceptable when scopes are explicit.

If two authority records conflict for the same scope and precedence/current authority cannot be established:

`CONFLICTING_SECURITY_AUTHORITY_EVIDENCE`

## Temporal Validity

Authority evidence must be current enough for the governed assessment/release.

If evidence has an explicit end date and is expired:

`SECURITY_AUTHORITY_EVIDENCE_EXPIRED`

If it appears historical and current validity cannot be established:

`SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED`

Do not silently reuse an old authority assignment forever.

## Scope Inheritance

A project-level authority record may be inherited by WorkUnits only when:

```text
WorkUnit scope ⊆ authority scope
```

If scope relation is unclear:

`SECURITY_AUTHORITY_SCOPE_UNRESOLVED`

Do not automatically apply one project's authority to another project.

## Relationship with ES0902 C2

```text
O2
→ who owns security control

C2
→ official security approval in QA
```

O2 PASS does not imply C2 PASS.

The same authority evidence may support provenance of C2 evidence, but official approval still requires its own authoritative QA approval artifact.

## Relationship with Assessment Workflow

The §4 DGSEI internal process is official-process context.

Do not hardcode that every O2 authority must literally be named `DGSEI` unless project/normative evidence establishes it.

O2 text requires a GCABA organization; use evidence, not assumption.

## Result Semantics

Deterministic Check states:

```text
PASS
FAIL
SECURITY_CONTROL_AUTHORITY_UNRESOLVED
GCABA_MEMBERSHIP_UNRESOLVED
SECURITY_AUTHORITY_SCOPE_UNRESOLVED
SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED
SECURITY_AUTHORITY_EVIDENCE_EXPIRED
CONFLICTING_SECURITY_AUTHORITY_EVIDENCE
AUTHORITY_EVIDENCE_INSUFFICIENT
```

## Completion Criteria

O2 is complete when:

```text
- exact matrix binding is preserved
- O2 remains ALWAYS
- project authority evidence is project-owned and initially empty/unresolved
- authority and execution are structurally separated
- GCABA membership requires authoritative evidence
- external/vendor execution cannot become authority implicitly
- multiple scoped authorities are supported
- stale/conflicting authority evidence fails closed
- O2 PASS does not imply C2 or official security approval
- no Agent or Skill is created
```
