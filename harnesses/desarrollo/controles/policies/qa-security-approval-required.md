---
id: qa-security-approval-required
type: POLICY
rule: C2
---

# Policy: qa-security-approval-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "3"
rule: C2
```

## Requirement

When C2 applies, the application/release must have authoritative security approval in QA for the assessed scope relevant to the current homologation/promotion gate.

## Non-Sufficient Evidence

The following do not satisfy this Policy by themselves:

```text
internal Harness scan
internal dev-security Review
vulnerability scanner with no official approval
CI pipeline green
READY_TO_REQUEST
READY_TO_RESUBMIT
G2 threshold calculation
approval in another environment
approval for another version/release
old approval invalidated by reassessment triggers
```

## QA

Approval environment must be evidenced as QA.

Unknown:
`SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED`

Non-QA:
`SECURITY_APPROVAL_NOT_IN_QA`

## Scope / Artifact

Approval must cover the application/release under evaluation.

Unknown scope:
`SECURITY_APPROVAL_SCOPE_UNRESOLVED`

Unknown assessed artifact/revision:
`SECURITY_APPROVAL_ARTIFACT_UNRESOLVED`

## Reassessment

Apply ES0901 Annex V trigger evaluation before reusing prior approval.

Applicable trigger:
`SECURITY_REASSESSMENT_REQUIRED`

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
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
