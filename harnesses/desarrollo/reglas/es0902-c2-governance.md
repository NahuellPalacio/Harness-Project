# ES0902 C2 Governance Package

## Purpose

Operationalize ES0902 v6.2 §3 C2:

```text
C2 — Las aplicaciones homologadas deben tener el aprobado a nivel seguridad en el ambiente QA.
```

C2 is an approval-evidence rule. It is not satisfied by an internal scan, an Agent review, a CI job, or a project team assertion.

## Cross-Standard Context

ES0901 v6.3 Annex V strengthens the operational context:

```text
security assessment is mandatory before an application advances to HML or PRD
assessment is performed in QA
every development must have an approved assessment to advance to homologation/production
assessment must be repeated under defined triggers
```

C2 therefore validates official QA security approval and the applicability/validity of that approval for the exact software scope being promoted.

## Matrix Binding

The installed ES0902 matrix declares:

```yaml
ruleKey: ES0902.C2
category: QUALITY

applicability:
  mode: CONDITIONAL
  signals:
    - securityHomologationPresent

primaryAgents:
  - dev-security

policies:
  - qa-security-approval-required

checks:
  - qa-security-approval-evidence

reviews: []
```

Do not rename these identifiers.

## Applicability Signal

`securityHomologationPresent` is evidence-backed.

Recommended meaning:

```text
TRUE
→ the governed application/release is subject to a security homologation/assessment gate
   for advancement beyond QA, or authoritative evidence explicitly requires security approval

FALSE
→ authoritative scope evidence establishes that C2 is not applicable to this governed item

UNRESOLVED
→ the Harness cannot establish whether the current application/release is subject to the gate
```

Do not infer FALSE merely because the current WorkUnit is still in DEV.

Do not infer TRUE merely because a repository exists.

The producer should consider release/promotion intent, application scope, assessment workflow state, and ES0901 Annex V trigger evidence.

## Approval Is External Evidence

The Harness may produce:

```text
INTERNAL_REVIEW_COMPLETE
READY_TO_REQUEST
READY_TO_RESUBMIT
```

but not official approval.

C2 PASS requires authoritative official approval evidence.

No internal component may synthesize, infer, or upgrade itself into:

```text
APPROVED
SECURITY_APPROVED
```

## QA Is Mandatory

C2 explicitly requires security approval in QA.

An approval or scan performed only in:

```text
DEV
HML
PRD
local
unknown environment
```

does not satisfy C2.

If environment cannot be proven:

`SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED`

If evidence establishes a non-QA environment as the approval environment:

`SECURITY_APPROVAL_NOT_IN_QA`

## Approval Must Bind to a Concrete Subject

Approval evidence must bind to the actual application/release scope.

At minimum preserve:

```text
application/project identity
assessment identifier
environment
approval status
authority/provenance
assessment date
assessed artifact/revision identity where available
scope
evidence reference
```

Where repository/build identity exists, prefer immutable identifiers such as:

```text
commit SHA
release/build identifier
artifact digest
image digest
```

Do not treat a branch name alone as immutable approval identity.

## Approval Freshness / Reuse

C2 itself says QA approval is required.

ES0901 Annex V defines when an assessment must be repeated. Therefore an older approval cannot be reused blindly.

The Annex V triggers are:

```text
more than 20 days since the previous assessment when there is development
corrections of previously detected vulnerabilities
security incident in the application
development with functional and/or endpoint changes within 20 days
```

The Annex also identifies modification categories requiring consideration for a new assessment:

```text
functionality / endpoint changes
external integrations / resources
security-control changes
dependency / infrastructure changes
critical functionality changes
authentication-flow changes
```

If any applicable reassessment trigger exists after the approved assessment:

`SECURITY_REASSESSMENT_REQUIRED`

and that prior approval cannot satisfy the current release gate by itself.

## Assessment Subject Matching

The Harness must determine whether the approval actually covers the release being promoted.

Recommended relation:

```text
EXACT
DESCENDANT_WITH_NO_REASSESSMENT_TRIGGER
SUPERSEDED_BY_CHANGE
UNRESOLVED
```

`EXACT`:
the assessed immutable artifact/revision equals the promotion candidate.

`DESCENDANT_WITH_NO_REASSESSMENT_TRIGGER`:
only when authoritative evidence and Annex V trigger evaluation establish that reuse is allowed.

`SUPERSEDED_BY_CHANGE`:
one or more trigger changes invalidate reuse for the current gate.

`UNRESOLVED`:
artifact relation or changes cannot be established.

Do not invent a generic "approval valid forever" rule.

## Partial Assessment

ES0901 Annex V states that vulnerability corrections may trigger a partial assessment.

A partial assessment is evidence about the remediation scope.

Do not automatically treat a partial assessment as a full approval for a materially changed release unless authoritative official evidence explicitly approves the release/scope.

Use:

`PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED`

when coverage is insufficiently established.

## Authority

C2 approval provenance should be consistent with O2 authority evidence.

However:

```text
O2 PASS
!= C2 PASS
```

O2 establishes who owns security control.

C2 establishes that an official security approval exists in QA for the relevant assessed scope.

If approval issuer/authority cannot be validated:

`SECURITY_APPROVAL_AUTHORITY_UNRESOLVED`

## Status Semantics

The Harness must not convert:

```text
scan clean
findings below threshold
G2 threshold satisfied
internal dev-security Review
READY_TO_REQUEST
```

into C2 PASS.

The approval evidence itself must contain an authoritative approved outcome.

Later ES0902 G2 controls acceptance threshold semantics. C2 must not preempt or duplicate G2.

## Evidence Immutability

Once consumed for a release decision, preserve an immutable reference or fingerprint of the approval evidence.

If approval evidence changes after evaluation:

```text
SECURITY_APPROVAL_EVIDENCE_CHANGED
```

and re-evaluate.

## Fail-Closed States

At minimum:

```text
SECURITY_APPROVAL_REQUIRED
SECURITY_APPROVAL_EVIDENCE_UNRESOLVED
SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED
SECURITY_APPROVAL_NOT_IN_QA
SECURITY_APPROVAL_AUTHORITY_UNRESOLVED
SECURITY_APPROVAL_SCOPE_UNRESOLVED
SECURITY_APPROVAL_ARTIFACT_UNRESOLVED
SECURITY_REASSESSMENT_REQUIRED
PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED
SECURITY_APPROVAL_EVIDENCE_CHANGED
```

None may be coerced to PASS.

## Completion Criteria

C2 is complete when:

```text
- exact matrix binding is preserved
- securityHomologationPresent is evidence-backed
- official approval cannot be internally synthesized
- QA environment is proven
- approval is bound to project/application and assessed scope
- immutable artifact/revision identity is used when available
- ES0901 Annex V reassessment triggers are evaluated
- stale/superseded approvals cannot approve changed releases
- partial assessments cannot silently become full approvals
- O2 authority is reused as provenance context without conflating O2 and C2
- G2 threshold logic is not duplicated
- no Agent or Skill is created
```
