---
name: dev-security-assessment
description: Use when a GCBA / DGISIS change has to face the official Security Assessment of ES0901 Annex V — deciding whether a new or partial assessment is required, checking pre-assessment readiness, assembling the traceable evidence package and consuming the official result. The goal is to arrive with the known issues already found, remediated, retested and documented, so the assessment verifies instead of discovering. It never performs or self-approves the official assessment. Owned by dev-security.
---

# Skill: dev-security-assessment

## Purpose

Prepare a GCBA application change for the **official Security Assessment** defined by ES0901 Annex V, determine whether a new or partial assessment is required, verify pre-assessment readiness, assemble traceable evidence, and consume the official assessment result.

This skill belongs to the `dev-security` agent.

Its operational objective is:

> Reach the official assessment with known security issues already identified, remediated, retested, and documented so the assessment is a verification step rather than the first place where basic security problems are discovered.

This skill does **not** perform or self-approve the official GCBA Security Assessment.

## Owner

Primary owner:

`dev-security`

Primary coordinator:

`dev-security-analysis`

Related skills:

- `dev-appsec-review`
- `dev-vulnerability-management`
- `dev-quality-validation`
- `dev-test-automation`
- `dev-ci-cd`
- `dev-deployment`
- `dev-environments`
- `dev-openshift`
- `dev-openid-connect`
- `dev-miba`

---

# Core Principle

The skill must answer:

```text
Is an assessment required?
What changed since the last approved assessment?
Is the candidate stable and deployed in QA?
Were AppSec, SAST, DAST and dependency findings reviewed?
Are known findings remediated or formally resolved?
Is the evidence package complete?
Can the application be submitted to the official assessment now?
```

---

# Authoritative Normative Basis

Primary available source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Annex V establishes:

```text
- Security Assessment is mandatory.
- It is executed in QA.
- An approved assessment is required before promotion to HML and PRD.
- It validates requirements from ES0901 and ES0902.
```

ES0901 is complemented by:

`ES0902 - Estándar de Seguridad`

If a preparation requirement depends on ES0902 and ES0902 is unavailable:

return:

`ES0902_CONTEXT_REQUIRED`

Do not invent the missing rule.

---

# Assessment Trigger Rules

Based on ES0901 Annex V, reassessment is required when applicable if:

```text
1. A development exists and more than 20 days have elapsed since the previous assessment.
2. Previously detected vulnerabilities were corrected.
   → partial reassessment may apply.
3. A security incident occurred.
4. A development changes functionalities and/or endpoints,
   even when less than 20 days elapsed since the previous assessment.
```

Explicit Annex V change categories:

## Functionalities and endpoints

```text
- add/modify endpoint
- remove frontend/backend sections
- modify form/API parameters
```

## Integrations and external resources

```text
- new external API
- third-party service
- webhook
- iframe/embed
- third-party script
- tracker / analytics / chatbot
```

## Security controls

```text
- CORS change
- CSP change
- cookie-policy change
- role change
- permission change
```

## Dependencies and infrastructure

```text
- library/framework/SDK/dependency add/update
- infrastructure migration
- communication-protocol change
```

## Critical functionality

```text
- upload/download
- sensitive-flow change
- authentication-flow change
- login
- registration
- password recovery
```

---

# Assessment Decision States

```text
NOT_REQUIRED_BY_CURRENT_CHANGE
NEW_ASSESSMENT_REQUIRED
PARTIAL_REASSESSMENT_REQUIRED
ASSESSMENT_PENDING
ASSESSMENT_APPROVED
ASSESSMENT_REJECTED
ASSESSMENT_SCOPE_UNRESOLVED
```

`ASSESSMENT_APPROVED` requires official external evidence.

---

# Scope Resolution

Resolve:

```text
application
candidate version
commit/tag/image
QA deployment
changed endpoints
changed UI sections
changed parameters
changed dependencies
changed auth flows
changed roles/permissions
changed integrations
changed external resources
changed infrastructure/protocols
changed file behavior
incident history
previous assessment date/scope/result
```

If the delta from the previously assessed candidate cannot be established:

return:

`ASSESSMENT_SCOPE_UNRESOLVED`

---

# Candidate Identity

Capture:

```text
commit SHA
tag/release
artifact/image digest
QA deployment reference
configuration reference
migration reference
```

Avoid an assessment against an ambiguous moving target.

If the candidate changes materially after evidence collection:

return:

`ASSESSMENT_CANDIDATE_CHANGED`

and recalculate scope/evidence.

---

# QA Requirement

The official assessment defined by ES0901 is performed in QA.

Before readiness:

```text
candidate deployed in QA
candidate identity verified
configuration resolved
required dependencies reachable
critical flows executable
```

If not:

return:

`QA_ASSESSMENT_TARGET_NOT_READY`

---

# Internal Pre-Assessment Flow

```text
candidate
   ↓
scope delta
   ↓
dev-appsec-review
   ↓
SAST
   ↓
Dependency Scanning
   ↓
DAST
   ↓
auth / authorization / secrets
   ↓
integration / file / platform review
   ↓
findings triage
   ↓
remediation
   ↓
retest
   ↓
READY_TO_REQUEST
   ↓
official Security Assessment
```

This is not the official assessment.

---

# Mandatory Evidence

Where applicable:

```text
candidate identity
QA target
scope delta
AppSec review
SAST
DAST
Dependency Scanning
open vulnerability list
retest evidence
authentication evidence
authorization evidence
role/permission evidence
CORS/CSP/cookie evidence
external integration evidence
upload/download evidence
secret/configuration evidence
OpenShift/runtime exposure evidence
critical QA-flow evidence
```

Mark true non-applicable items as:

`NOT_APPLICABLE`

with reason.

---

# AppSec Pre-Review

Consume:

`dev-appsec-review`

Expected:

```text
changed attack surface reviewed
trust boundaries resolved
technical findings captured
no unresolved blocking AppSec finding
```

If required and incomplete:

return:

`APPSEC_REVIEW_REQUIRED`

---

# Scanner Preflight

## SAST

Validate:

```text
executed
candidate commit matches
results available
findings triaged
```

## Dependency Scanning

Validate:

```text
executed
candidate dependencies match
known-vulnerability results reviewed
```

## DAST

Validate:

```text
executed against QA candidate
target identity matches
tested surface known
results reviewed
```

Scanner success is not official assessment approval.

---

# DAST Scope

Capture available coverage evidence:

```text
target URLs
authenticated/unauthenticated scope
API/browser surface
scan configuration
excluded paths
```

If a major changed surface was outside scope:

return:

`DAST_SCOPE_GAP`

---

# Findings Gate

Consume:

`dev-vulnerability-management`

Before `READY_TO_REQUEST`, determine:

```text
open blocking findings
findings awaiting remediation
findings awaiting retest
approved exceptions
false positives with evidence
```

Never hide unresolved findings from the package.

---

# Remediation Retest

After remediation:

```text
rerun relevant scanner/test
capture new candidate
capture retest evidence
determine partial/full reassessment requirement
```

Do not close a finding because code changed.

---

# Authentication / Authorization Readiness

Authentication-flow changes trigger assessment consideration.

Consume evidence from:

```text
dev-openid-connect
dev-miba
dev-appsec-review
dev-test-automation
```

Cover, when applicable:

```text
login
callback
logout
session/state behavior
roles/permissions
backend authorization
environment-specific identity configuration
```

Do not invent ES0902 identity requirements.

---

# Security-Control Changes

For CORS/CSP/cookies/roles/permissions changes record:

```text
what changed
why
environment
review result
test evidence
unresolved risk
```

Do not submit unexplained permissive changes.

---

# External Integrations

For new/modified external resources collect:

```text
provider/resource
purpose
endpoint/environment
credential-reference model
data exchanged
callback/webhook behavior
third-party script/embed presence
AppSec result
```

---

# File Flows

For upload/download collect:

```text
authorization
validation
storage target
temporary-file handling
public/private exposure
download access control
```

---

# Dependency Changes

Collect:

```text
package/library
version
reason
approved/homologated status where applicable
scanner result
known-vulnerability status
runtime inclusion
```

---

# Security Incident Trigger

If a security incident occurred since the relevant assessment:

return:

`NEW_ASSESSMENT_REQUIRED`

and:

`SECURITY_INCIDENT_CONTEXT_REQUIRED`

Do not invent incident-response procedure.

---

# Previous Assessment Freshness

Track:

```yaml
previousAssessment:
  date: YYYY-MM-DD
  result: APPROVED
  scopeReference: ...
  candidateReference: ...
```

Use the documented assessment date for the 20-day rule.

---

# Twenty-Day Rule

When there is a development and more than 20 days have elapsed:

```text
NEW_ASSESSMENT_REQUIRED
```

Do not substitute ticket/merge/deploy date unless the official process says so.

---

# HML / PRD Gate

Mandatory:

```text
assessment required
+
official status != APPROVED
+
target = HML or PRD

→ SECURITY_ASSESSMENT_BLOCKING
```

No scanner result can override this.

---

# Assessment Package

```yaml
assessmentPackage:

  candidate:
    application: ...
    commit: ...
    artifact: ...
    qaDeployment: ...

  trigger:
    required: true
    reasons: []

  delta:
    endpoints: []
    integrations: []
    securityControls: []
    dependencies: []
    criticalFlows: []

  evidence:
    appsecReview: ...
    sast: ...
    dast: ...
    dependencyScanning: ...
    qaAutomation: ...

  vulnerabilities:
    open: []
    remediatedAwaitingRetest: []
    exceptions: []

  readiness:
    readyToRequest: true
    blockers: []
```

Never embed secrets.

---

# Ready-to-Request Criteria

Return `READY_TO_REQUEST` only when:

```text
candidate identity resolved
QA candidate available
assessment scope resolved
required AppSec review complete
required scanners current
known findings triaged
blocking findings resolved or externally authorized
retests complete
evidence package complete
ES0902-dependent unknowns not hiding required decisions
```

This state means only internal readiness to request the official assessment.

---

# Readiness States

```text
READY_TO_REQUEST
NOT_READY
WAITING_FOR_RETEST
WAITING_FOR_ES0902_CONTEXT
WAITING_FOR_QA_TARGET
WAITING_FOR_OFFICIAL_ASSESSMENT
OFFICIAL_ASSESSMENT_APPROVED
OFFICIAL_ASSESSMENT_REJECTED
BLOCKED
```

---

# Official Result Consumption

Capture official evidence:

```text
assessment identifier
date
scope
candidate/application
result
findings
partial/full
retest requirement
```

Do not normalize away official wording.

Route findings to:

`dev-vulnerability-management`

---

# Rejected Assessment

If rejected:

```text
readiness: BLOCKED
```

Then:

```text
official findings
   ↓
dev-vulnerability-management
   ↓
remediation
   ↓
retest
   ↓
partial/full reassessment
```

---

# Evidence Provenance

Each evidence item should identify:

```text
candidate
commit
artifact
environment
date
tool/source
result
reference
```

Mismatched evidence:

`STALE_ASSESSMENT_EVIDENCE`

---

# Required Capabilities

Typical:

```text
git.diff.inspect
repository.read
deployment.results.inspect
environment.config.inspect

security.sast.results.inspect
security.dast.results.inspect
security.dependency.results.inspect

security.assessment.status.inspect
security.assessment.history.inspect

vulnerability.findings.inspect
test.results.inspect
```

Optional action:

`security.assessment.request`

only if an approved integration exposes it.

If unavailable:

`CAPABILITY_GAP`

---

# Required Checks

Potential:

```text
assessment-trigger
assessment-twenty-day-rule
candidate-identity
qa-target-ready
appsec-review-complete
sast-current
dast-current
dependency-scan-current
open-security-findings
retest-complete
assessment-approved-before-hml-prd
```

If unavailable:

`CHECK_GAP`

---

# Result Statuses

```text
COMPLETE
PARTIAL
MISSING_CONTEXT
NEW_ASSESSMENT_REQUIRED
PARTIAL_REASSESSMENT_REQUIRED
SECURITY_ASSESSMENT_BLOCKING
ASSESSMENT_SCOPE_UNRESOLVED
ASSESSMENT_CANDIDATE_CHANGED
QA_ASSESSMENT_TARGET_NOT_READY
APPSEC_REVIEW_REQUIRED
DAST_SCOPE_GAP
SECURITY_INCIDENT_CONTEXT_REQUIRED
STALE_ASSESSMENT_EVIDENCE
ES0902_CONTEXT_REQUIRED
VULNERABILITY_REMEDIATION_REQUIRED
VULNERABILITY_RETEST_REQUIRED
CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED
FAILED
```

---

# Output Contract

```yaml
securityAssessmentResult:

  status: COMPLETE
  readiness: READY_TO_REQUEST

  candidate:
    application: sistema-x
    commit: abc123
    artifact: sha256:...
    environment: QA
    deploymentReference: qa-deployment-456

  previousAssessment:
    exists: true
    date: 2026-09-01
    status: APPROVED
    reference: assessment-001

  trigger:
    required: true
    type: NEW_ASSESSMENT_REQUIRED
    reasons:
      - ENDPOINT_CHANGED
      - AUTHENTICATION_FLOW_CHANGED

  evidence:
    appsecReview: PASS
    sast: PASS
    dast: PASS
    dependencyScanning: PASS
    qaAutomation: PASS

  vulnerabilities:
    openBlocking: 0
    awaitingRetest: 0
    acceptedExceptions: 0

  officialAssessment:
    status: NOT_REQUESTED

  blockers: []
  assumptions: []
  evidenceReferences: []
```

---

# Model Routing Metadata

## STANDARD

Use for:

```text
assessment-trigger calculation
scope-delta generation
evidence collection
20-day rule
normal readiness checks
```

## REASONING

Use when:

```text
scope changes across many domains
assessment applicability is ambiguous
prior assessment scope differs materially
scanner evidence conflicts
partial vs full reassessment is unclear
```

## PREMIUM

Only for exceptional critical multi-system scope or unresolved major identity/infrastructure changes.

Requires Human Model Gate approval.

---

# Prohibited Behavior

This skill must not:

- self-approve the official Security Assessment
- submit an unstable candidate as READY
- treat scanners as assessment approval
- hide open findings
- reuse stale evidence
- alter the official 20-day trigger
- invent ES0902 requirements
- invent assessment approval
- bypass HML/PRD gate
- embed secrets
- self-approve formal Checks
- create Tools directly
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- determines assessment applicability from Annex V
- computes scope from the actual change
- verifies the QA candidate identity
- performs a complete pre-assessment readiness pass
- consumes AppSec/scanner/QA evidence
- ensures findings are triaged and retested
- preserves freshness/provenance
- blocks HML/PRD without official approval
- packages evidence clearly
- consumes official results without altering meaning
- routes vulnerabilities into remediation lifecycle

---

# Source References

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Primary areas:

```text
Section 4
Annex I
Annex V
```

`ES0902 - Estándar de Seguridad` remains required for rules delegated to it and must not be invented.
