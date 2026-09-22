# ES0902 v6.2 — Security Governance Architecture

## Baseline

```text
standard: ES0902
version: 6.2
date: 2025-08
authority: Agencia de Sistemas de Información (ASI)
```

Security is fail-closed:

```text
missing evidence -> UNRESOLVED
ambiguous interpretation -> HUMAN / AUTHORITY REQUIRED
internal Harness review != official GCBA security approval
passing controls != approved assessment
```

## Architecture

```text
TaskContext
  ↓
Asset Classification
  ↓
Normative Resolver
  ├── ES0901 v6.3
  └── ES0902 v6.2
  ↓
Policies / Checks / Reviews
  ↓
Cross-Standard Resolver
  ↓
Security Evidence Package
  ├── internal assessment
  ├── required deliverables
  ├── WAF requirement
  └── official assessment state
```

## Rule Inventory

Exactly 21 source rules:

```text
O1 O2
C1 C2 C3
Vu1 Vu2 Vu3 Vu4 Vu5 Vu6 Vu7 Vu8 Vu9 Vu10
Ve1 Ve2
G1 G2 G3 G4
```

Global references must use a composite key because ES0901 also has G1/G2:

```text
ES0901.G1
ES0902.G1
```

## Contract Override

A project-contract exception is valid only with both contract evidence and ASI approval evidence.

Without both:

`SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED`

A project-local config cannot waive ES0902.

## Official Approval Boundary

Harness-owned results may include:

```text
INTERNAL_REVIEW_COMPLETE
READY_TO_REQUEST
READY_TO_RESUBMIT
G2_THRESHOLD_SATISFIED
```

The Harness must never manufacture `SECURITY_APPROVED`.

Only authoritative GCBA/DGSEI evidence may set official approval.

## Assessment State

```text
NOT_STARTED
INTERNAL_ASSESSMENT
READY_TO_REQUEST
REQUESTED
IN_ASSESSMENT
FINDINGS_RECEIVED
REMEDIATION
READY_TO_RESUBMIT
RESUBMITTED
APPROVED
REJECTED
OFFICIAL_STATUS_UNRESOLVED
```

`APPROVED` requires official evidence.

## C1 / ES0901 D1 Guard

ES0902 C1 requires OpenID Connect with Keycloak/DGSEI for authentication. ES0901 D1 is already modeled separately for citizen-facing authentication.

Do not invent a reconciliation.

Potential conflict:

`CROSS_STANDARD_INTERPRETATION_REQUIRED`

Resolution requires authoritative GCBA/ASI project or normative evidence.

## Shared Controls

When two standards require the same technical outcome, prefer one executed control with multiple normative sources:

```yaml
normativeSources:
  - standard: ES0901
    version: "6.3"
    rule: ...
  - standard: ES0902
    version: "6.2"
    rule: ...
```

Shared execution does not imply shared applicability or automatic PASS.

## Security Ownership

Existing assets remain:

```text
dev-security
dev-security-analysis
dev-security-assessment
dev-appsec-review
dev-vulnerability-management
```

No new security Agent is created by ES0902.

Internal review and remediation do not impersonate DGSEI.

## Assessment Layers

```text
Layer 1 — Harness security controls
Layer 2 — automated/internal security assessment
Layer 3 — official GCBA/DGSEI assessment
```

Layers 1/2 prepare and validate; Layer 3 owns official approval.

## Deliverables

Section 5 requirements are modeled separately from rules.

Asset types may overlap. Requirements are the UNION of all applicable asset types.

## WAF

Web Applications and Web Services require the WAF policy form supplied by the Prevention team.

The Harness must not invent its fields.

Missing template:

`WAF_FORM_CONTEXT_REQUIRED`

## G2 Acceptance Threshold

Only with authoritative risk-category mapping:

```text
no finding above LOW
AND
LOW count <= 10
-> G2_THRESHOLD_SATISFIED
```

This is not official approval.

Unknown mapping:

`VULNERABILITY_RISK_MAPPING_UNRESOLVED`

## G3 / G4

G3 resubmission:
- recheck 100% of previously reported vulnerabilities
- G2 still applies

G4 reassessment:
- full assessment, not previous findings only
- new findings may appear
- G2 still applies

Do not collapse G3 and G4.

## Versioning

C3 and Ve1 should reuse ES0901 G1 technology/version controls where appropriate.

Ve2 adds:

```text
newer or allegedly safer version
-> Infrastructure consensus required before use
```

## OWASP

Vu10 requires considering the applicable OWASP guidance for Web, API/Web Services and Mobile.

Use version/date-aware source references; do not freeze an old cached list as if it were ES0902 text.

## Completion

Installed only when:

```text
21 rules load exactly
composite cross-standard rule keys exist
ASI-approved override mechanism exists
official approval cannot be self-issued
assessment workflow exists
E1-E5 deliverables matrix exists
WAF requirement is modeled
cross-standard relations are explicit
C1/D1 conflict fails closed
G2 threshold does not masquerade as approval
existing security Agent/Skills remain authoritative
```
