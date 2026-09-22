---
name: dev-security-analysis
description: Use when a change, release candidate, integration, dependency, authentication or authorization change, infrastructure change or deployment plan of a GCBA / DGISIS project has to be looked at from application security — which security requirements apply, what evidence exists, which risks are still unresolved and whether the change is ready from a security standpoint. Coordinates dev-security-assessment, dev-appsec-review and dev-vulnerability-management; it never self-approves the official assessment and never replaces ES0902. Primary security skill of the dev-security agent.
---

# Skill: dev-security-analysis

## Purpose

Perform application-security analysis for GCBA software changes, release candidates, integrations, dependencies, authentication/authorization changes, infrastructure changes, and deployment plans.

This is the **primary security skill** of the `dev-security` agent.

Its responsibility is to identify applicable security requirements, gather and interpret security evidence, determine whether a GCBA Security Assessment is required, detect unresolved security risks, coordinate specialized implementation owners, and provide a structured security-readiness result to the orchestrator.

This skill does **not** self-approve the official GCBA Security Assessment and does not replace the requirements of `ES0902 - Estándar de Seguridad`.

---

## Owner

Primary owner:

`dev-security`

Specialized security skills:

- `dev-security-assessment`
- `dev-appsec-review`
- `dev-vulnerability-management`

Related agents / skills:

- `dev-quality`
- `dev-ci-cd`
- `dev-deployment`
- `dev-openshift`
- `dev-environments`
- `dev-backend`
- `dev-frontend`
- `dev-integration`
- `dev-openid-connect`
- `dev-miba`
- `dev-storage`
- `dev-observability`
- `dev-architecture-analysis`
- `dev-tool-builder`
- `dev-refutador`

---

# Core Principle

The skill must answer:

> What security properties may be affected by this WorkUnit, what objective evidence exists, what risks remain unresolved, and is the change allowed to advance from a security perspective?

Apply these rules:

> Security must be evaluated from the actual change and runtime behavior, not only from the ticket description.

> Missing security evidence is not equivalent to secure behavior.

> Automated scanner results are evidence, not the entire security review.

> The official GCBA Security Assessment is an external mandatory control where ES0901 requires it; this agent can prepare for it, consume its result, and block promotion when it is missing, but cannot approve it itself.

---

# Source Hierarchy

## Authoritative GCBA sources

Primary available source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

ES0901 explicitly states that it is complemented by:

`ES0902 - Estándar de Seguridad`

If ES0902 is not present in the current context, this skill must **not invent its detailed rules**.

When a decision requires a rule that ES0901 delegates to ES0902 and ES0902 is unavailable:

return:

`ES0902_CONTEXT_REQUIRED`

## Industry practices

ES0901 G2 requires recognized industry good practices.

Industry security practices may be used as **supplementary analysis**, but they must not be presented as if they were verbatim GCBA normative requirements.

---

# Normative Basis from ES0901

Relevant requirements include:

```text
O1
→ respect current GCBA IT principles and regulations

C1
→ authentication is required when functionality/data requires user identification

C2
→ applications are promoted through DEV, QA, HML, PRD with required controls

D1 / D2
→ GCBA-approved citizen/institutional authentication mechanisms

D8
→ services must be protected with token-based security

P1
→ approved frameworks help enforce security, dependency management and maintainability

P5
→ validations must exist in frontend and backend where applicable

6.5
→ database users receive only the minimum permissions required

6.7
→ applications must generate logs and cannot provide a mechanism that disables required logging

6.8
→ additional software/components are part of the application responsibility
→ external libraries/versions must be documented
→ ASI correlates vulnerabilities with dependency inventory

8.2
→ citizen and institutional authentication requirements
→ application roles/permissions remain application responsibility

Annex I
→ GitLab controls include SAST, DAST and Dependency Scanning

Annex V
→ Security Assessment is mandatory before HML/PRD
→ executed in QA
→ re-assessment criteria are explicitly defined
```

---

# Security Responsibility Model

Security is cross-cutting.

```text
dev-security
→ analyzes security impact
→ consumes scanner/assessment evidence
→ identifies security findings
→ determines security readiness
→ requests official assessment when applicable

domain agents
→ implement the secure change in their domain

dev-ci-cd
→ runs configured security scanners

dev-quality
→ consumes security readiness as release evidence

dev-orchestrator
→ coordinates remediation / approval / blocking
```

Examples:

```text
OIDC implementation
→ dev-openid-connect

API authorization implementation
→ dev-backend / dev-api

secret injection
→ dev-environments / dev-openshift / Block 1

file handling
→ dev-storage

security review of those changes
→ dev-security
```

---

# Security Analysis Dimensions

Select only the dimensions applicable to the WorkUnit.

Possible dimensions:

```text
AUTHENTICATION
AUTHORIZATION
SERVICE_PROTECTION
SESSION_AND_TOKEN_HANDLING
INPUT_VALIDATION
OUTPUT_AND_DATA_EXPOSURE
SECRETS
LOGGING_AND_AUDIT
DEPENDENCIES
STATIC_ANALYSIS
DYNAMIC_ANALYSIS
FILES
EXTERNAL_INTEGRATIONS
NETWORK_AND_PROTOCOLS
DATABASE_PRIVILEGES
CONFIGURATION
CORS
CSP
COOKIES
INFRASTRUCTURE
CLOUD
THIRD_PARTY_SCRIPTS
WEBHOOKS
IFRAMES_EMBEDS
SUPPLY_CHAIN
SECURITY_ASSESSMENT
```

---

# Mandatory Workflow

```text
1. Read WorkUnit and acceptance criteria
2. Inspect actual implementation/diff/configuration
3. Identify affected security dimensions
4. Resolve applicable ES0901 rules
5. Determine whether ES0902 context is required
6. Determine whether official Security Assessment is required
7. Inspect authentication/authorization impact
8. Inspect service/token protection
9. Inspect secrets/configuration handling
10. Inspect input/file/data handling
11. Inspect dependencies/supply chain
12. Consume SAST results
13. Consume Dependency Scanning results
14. Consume DAST results when applicable
15. Inspect infrastructure/network/platform impact
16. Inspect logging/audit exposure
17. Consume `dev-appsec-review` for technical security review
18. Route findings through `dev-vulnerability-management`
19. Consume `dev-security-assessment` for Annex V readiness/status
20. Correlate findings and remove duplicates
21. Classify blocking/unresolved findings
22. Validate remediation/retest evidence
23. Return security readiness and assessment status
```

---

# Security Impact

Inspect actual changes where possible:

```text
Git diff
new/changed endpoints
forms and request parameters
authentication code
authorization rules
roles/permissions
dependencies
infrastructure manifests
OpenShift configuration
CORS/CSP/cookie configuration
external scripts
webhooks
files
storage
database permissions
protocols
integration endpoints
```

If implementation impact cannot be resolved:

return:

`SECURITY_IMPACT_UNRESOLVED`

---

# Security Assessment — Mandatory GCBA Control

ES0901 Annex V states that the Security Assessment:

```text
is mandatory
is executed in QA
must be approved before advancing to HML and PRD
verifies ES0901 + ES0902 security requirements
```

The harness must represent the assessment as an **external authoritative control**.

The agent may:

```text
detect that an assessment is required
prepare evidence
request/schedule the assessment through the approved process
consume the official result
track remediation
request partial reassessment when required
block promotion if approval is missing
```

The agent must not:

```text
declare the official assessment approved
fabricate an assessment result
substitute SAST/DAST for the official assessment
```

---

# Assessment Trigger Rules

Based on ES0901 Annex V, determine whether a new or partial assessment is required.

A new/renewed assessment is required when applicable if:

```text
there is a development and more than 20 days passed since the previous assessment

vulnerabilities detected previously were corrected
→ partial reassessment may be required

a security incident occurred

functionalities and/or endpoints changed
even within 20 days of the previous assessment
```

Changes that explicitly trigger assessment consideration include:

```text
FUNCTIONALITY / ENDPOINTS
- add or modify endpoints
- remove frontend/backend sections
- change form/API parameters

INTEGRATIONS / EXTERNAL RESOURCES
- new external APIs
- third-party services
- webhooks
- iframes / embeds
- third-party scripts, trackers, analytics, chatbots

SECURITY CONTROLS
- CORS changes
- CSP changes
- cookie-policy changes
- role changes
- permission changes

DEPENDENCIES / INFRASTRUCTURE
- add/update libraries
- frameworks
- SDKs
- infrastructure migration
- communication-protocol changes

CRITICAL FUNCTIONS
- upload/download functionality
- sensitive application flows
- authentication-flow changes
- login
- registration
- password recovery
```

---

# Assessment Decision Model

Return one of:

```text
NOT_REQUIRED_BY_CURRENT_CHANGE
REQUIRED
PARTIAL_REASSESSMENT_REQUIRED
PENDING
APPROVED
REJECTED
UNKNOWN
```

`APPROVED` may only be reported when supported by official assessment evidence.

If HML/PRD promotion is requested and required assessment evidence is not approved:

return:

`SECURITY_ASSESSMENT_BLOCKING`

---

# Assessment Freshness

Track:

```text
assessment date
assessed application/version
scope
changes since assessment
incident status
remediation status
```

Do not treat an old assessment as valid merely because it exists.

If current change invalidates the previous scope:

return:

`SECURITY_ASSESSMENT_REFRESH_REQUIRED`

---

# Authentication

ES0901 requires approved GCBA authentication depending on application audience.

Responsibility split:

```text
dev-openid-connect / dev-miba
→ implementation/integration mechanics

dev-security
→ security review and evidence
```

Validate:

```text
approved identity mechanism selected
credentials delegated appropriately
token/session behavior not exposed unsafely
redirect/callback configuration consistent with intended environment
authentication changes trigger assessment when applicable
```

If authentication behavior is unclear:

return:

`AUTHENTICATION_SECURITY_UNRESOLVED`

---

# Authorization

Authentication does not prove authorization.

Review:

```text
roles
permissions
resource access
privilege boundaries
administrative operations
backend enforcement
```

Sensitive authorization must not rely only on frontend checks.

If backend authorization is missing where required:

return:

`AUTHORIZATION_ENFORCEMENT_RISK`

---

# Least Privilege

Apply least privilege to:

```text
application roles
service accounts
database users
OpenShift/platform permissions
API credentials
external-provider credentials
```

ES0901 explicitly requires minimum permissions for database users.

If privileges materially exceed need:

return:

`EXCESSIVE_PRIVILEGE_RISK`

---

# Service Protection

ES0901 D8 requires services to be protected with a token system.

Review applicable service endpoints for:

```text
token requirement
token validation
authorization after token validation
public endpoint exceptions
machine-to-machine credentials
```

If a protected service lacks the required mechanism:

return:

`SERVICE_TOKEN_PROTECTION_MISSING`

---

# Session / Token Handling

Review token/session handling for exposure risks:

```text
tokens in logs
tokens in URLs
tokens in source control
tokens copied between environments
unsafe logout/session invalidation
unvalidated token context
```

Protocol-specific correctness belongs to the owning identity/integration skill.

---

# Secrets

Secrets include:

```text
API keys
client secrets
passwords
private keys
tokens
database credentials
provider credentials
```

Secrets must not be embedded in:

```text
source code
Git history
Markdown documentation
pipeline logs
generated reports
ConfigMaps/non-secret config
test snapshots
screenshots/traces
```

The harness uses secret references and approved secret storage/injection.

Block 1 owns integration credential acquisition/storage for harness integrations.

If secret material is detected:

return:

`SECRET_EXPOSURE_RISK`

---

# Secret Exposure Response

If a real secret has been exposed, deleting it from the current file is not complete remediation.

Required response may include:

```text
revoke/rotate affected credential
remove exposure source
review history/log/artifact propagation
validate replacement reference
```

The exact incident process may require ES0902 or organizational procedure.

If unavailable:

return:

`SECURITY_INCIDENT_PROCESS_REQUIRED`

---

# Input Validation

ES0901 P5 requires frontend/backend validation where applicable.

Backend validation is authoritative for server-side enforcement.

Review:

```text
request parameters
path/query values
JSON bodies
file metadata
identifiers
sorting/filtering
pagination
external callback payloads
webhooks
```

If sensitive input lacks backend enforcement:

return:

`SERVER_SIDE_VALIDATION_RISK`

---

# Industry Security Review

Under ES0901 G2, supplementary industry analysis may inspect whether untrusted input is interpreted as:

```text
database query
shell command
template
HTML
URL/redirect
filesystem path
expression
deserialization payload
```

These are supplementary review areas and must not be presented as verbatim ES0901/ES0902 requirements unless the source supports them.

---

# Data / Output Exposure

Review whether APIs, UI, logs, health endpoints, errors or files expose more information than necessary.

Potential exposures:

```text
credentials
tokens
personal/sensitive information
stack traces
internal infrastructure
unnecessary object fields
administrative metadata
```

If detailed data-classification rules require ES0902:

return:

`ES0902_CONTEXT_REQUIRED`

---

# Logging and Audit

ES0901 requires logging and prevents disabling required logs.

Review:

```text
important security events are observable where applicable
logs cannot be disabled through unsafe behavior
secrets/tokens are not logged
audit/security events retain useful provenance
```

If required audit behavior depends on unavailable ES0902 rules, do not invent it.

Return:

`SECURITY_LOGGING_RISK`

when logs expose secrets or critical security behavior is unobservable.

---

# Files

Upload/download changes explicitly trigger assessment consideration in Annex V.

Coordinate implementation with:

`dev-storage`

Security review may include:

```text
upload/download authorization
content/metadata validation
object/path safety
temporary-file handling
direct-object access
public exposure
storage lifecycle
```

If insufficiently defined:

return:

`FILE_SECURITY_REVIEW_REQUIRED`

---

# Dependencies

Review:

```text
new dependency
updated dependency
transitive dependency impact
known vulnerability findings
unsupported/EOL version
unexpected package-manager change
unapproved component
```

Dependency changes also trigger assessment consideration.

Return:

`DEPENDENCY_SECURITY_RISK`

when unresolved.

---

# Supply Chain

Supplementary industry analysis may inspect:

```text
dependency source
lock files
package integrity
unexpected registries
build plugins
pipeline includes
base images
third-party scripts
```

Do not claim a GCBA-specific requirement unless the available sources support it.

---

# SAST

ES0901 Annex I includes GitLab Static Application Security Testing.

Responsibility split:

```text
dev-ci-cd
→ executes/configures scanner

dev-security
→ interprets findings
```

Validate:

```text
scanner executed
candidate artifact/commit matches
findings available
severity/source preserved
remediation status known
```

If required evidence is missing:

return:

`SAST_EVIDENCE_MISSING`

---

# DAST

ES0901 Annex I describes DAST based on OWASP ZAP.

Validate:

```text
target environment
target version
authentication context where applicable
scan coverage
findings
remediation evidence
```

Do not run intrusive dynamic testing against PRD without explicit approval.

If required evidence is missing:

return:

`DAST_EVIDENCE_MISSING`

---

# Dependency Scanning

ES0901 Annex I includes Dependency Scanning.

Correlate findings to actual candidate dependency versions.

If required evidence is missing:

return:

`DEPENDENCY_SCAN_EVIDENCE_MISSING`

---

# Scanner Evidence Is Not Assessment Approval

Mandatory distinction:

```text
SAST PASS
+ DAST PASS
+ Dependency Scan PASS
≠ official Security Assessment APPROVED
```

Annex V assessment remains a separate control.

---

# Vulnerability Finding Model

Preserve source-defined severity and references.

```yaml
finding:

  id: scanner-or-assessment-id
  source: SAST | DAST | DEPENDENCY_SCAN | ASSESSMENT | MANUAL_REVIEW
  title: ...
  severity: SOURCE_DEFINED

  status:
    OPEN | REMEDIATED | ACCEPTED_EXCEPTION | FALSE_POSITIVE | UNKNOWN

  component: ...
  evidence: ...
  remediation: ...
  retestRequired: true
```

Do not invent CVSS scores or silently remap severity.

---

# Finding Deduplication

The same root issue may appear in:

```text
SAST
DAST
Dependency Scanning
manual review
official assessment
```

Correlate duplicates but preserve all source evidence.

---

# False Positives

A false-positive classification requires evidence.

Do not classify a finding as false positive solely because the implementation owner disagrees.

---

# Remediation

For each real finding:

```text
identify affected component
identify remediation owner
implement through owning Agent
rerun applicable scanner/test
determine whether partial assessment is required
```

Security coordinates and validates remediation; it does not become a super-implementation agent.

---

# Security Exceptions

Exceptions must come from an approved organizational process.

Record:

```text
exception reference
scope
expiration
owner
conditions
```

Do not self-approve exceptions.

If required:

return:

`SECURITY_EXCEPTION_APPROVAL_REQUIRED`

---

# CORS / CSP / Cookies

Annex V explicitly identifies changes to:

```text
CORS
CSP
cookies
roles
permissions
```

as assessment-relevant security changes.

Do not weaken these controls silently to make functionality work.

If intended behavior cannot be established:

return one of:

```text
CORS_SECURITY_UNRESOLVED
CSP_SECURITY_UNRESOLVED
ES0902_CONTEXT_REQUIRED
```

---

# External Integrations

New external APIs, services, webhooks, iframes, embeds and third-party scripts trigger assessment consideration.

Coordinate implementation with:

`dev-external-integration`

Review:

```text
credential scope
data sent externally
callback/webhook trust boundary
provider endpoint/environment
third-party execution
failure/security behavior
```

---

# Webhooks

Supplementary industry review may inspect:

```text
sender authenticity
replay behavior
payload validation
idempotency
authorization
secret handling
```

Implementation belongs to integration/backend owners.

---

# Network / Protocol Changes

Infrastructure migrations and protocol changes trigger assessment consideration.

Coordinate with:

- `dev-devops`
- `dev-openshift`
- `dev-architecture-analysis`

Review:

```text
new exposure
new ingress/egress
TLS/protocol assumptions
trust-boundary changes
route changes
service reachability
```

---

# Database Security

ES0901 requires minimum DB permissions.

Review:

```text
database user role
required operations
cross-schema access
administrative privileges
credential handling
```

If over-privileged:

return:

`DATABASE_PRIVILEGE_RISK`

---

# OpenShift / Platform Security

Consume `dev-openshift` evidence.

Review may include:

```text
credential scope
Secret vs ConfigMap separation
route exposure
service account scope
production mutation
environment isolation
```

Do not duplicate OpenShift implementation logic.

---

# Environment Isolation

Detect:

```text
PRD credentials in DEV/QA
DEV credentials in PRD
production identity client copied into lower environment
lower-environment callback in PRD
cross-environment secrets
production provider used accidentally
```

Coordinate with `dev-environments`.

Return:

`CROSS_ENVIRONMENT_SECURITY_RISK`

---

# Cloud

ES0901 requires ASI evaluation for cloud use and consideration of security compliance and data location/jurisdiction.

If required cloud security context is absent:

return:

`CLOUD_SECURITY_REVIEW_REQUIRED`

Do not invent additional jurisdiction/privacy rules beyond available sources.

---

# Threat-Oriented Review

Under G2 industry-good-practice analysis, high-risk changes may receive a lightweight threat-oriented review:

```text
what new trust boundary exists?
what new input is attacker-controlled?
what privilege is gained if a control fails?
what sensitive action becomes reachable?
what secret/token is involved?
what external system becomes trusted?
what abuse path appears?
```

This is supplementary analysis, not a substitute for ES0902 or the official assessment.

---

# Security Evidence Provenance

Every result should identify:

```text
artifact/commit
environment
scanner/tool/source
assessment date/scope
finding/retest result
```

If evidence belongs to another artifact/environment:

return:

`STALE_SECURITY_EVIDENCE`

---

# Security Readiness

Allowed readiness states:

```text
READY
READY_PENDING_OFFICIAL_ASSESSMENT
BLOCKED
INCOMPLETE_EVIDENCE
REQUIRES_SECURITY_DECISION
```

Important:

```text
READY_PENDING_OFFICIAL_ASSESSMENT
≠ permission to promote to HML/PRD
```

When Annex V assessment is required for HML/PRD and not officially approved:

```text
readiness: BLOCKED
```

---

# DEV / QA / HML / PRD Behavior

## DEV

ES0901 includes:

```text
source-code vulnerability analysis
deployment to DEV
vulnerability detection against deployed application
```

## QA

ES0901 repeats DEV controls and adds:

```text
complementary Security Assessment
```

## HML

Promotion requires satisfactory quality/security controls.

## PRD

Promotion requires required security controls and approved assessment.

---

# CI/CD Boundary

```text
dev-ci-cd
→ executes security scanners

dev-security
→ interprets security evidence
```

Detect bypass patterns:

```text
security job allow_failure
ignored scanner exit status
scan disabled on release path
scan performed against different candidate
```

If detected:

return:

`SECURITY_GATE_BYPASS_RISK`

---

# Quality Boundary

```text
dev-security
→ security readiness

dev-quality-validation
→ overall QA readiness consuming security result
```

Quality cannot override a blocking security result.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
git.diff.inspect

security.sast.results.inspect
security.dast.results.inspect
security.dependency.results.inspect

dependency.manifest.inspect
dependency.version.inspect

configuration.inspect
secret.reference.inspect
logs.configuration.inspect

api.routes.inspect
authorization.rules.inspect
authentication.config.inspect

deployment.results.inspect
environment.config.inspect

security.assessment.status.inspect
```

Optional:

```text
openshift.permissions.inspect
openshift.route.inspect
cloud.configuration.inspect
network.exposure.inspect
file.flow.inspect
```

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

```text
assessment-required
assessment-approved-for-promotion
SAST evidence
DAST evidence
dependency-scan evidence
service-token protection
backend authorization
least privilege
secret exposure
cross-environment security
server-side validation
dependency vulnerability
security logging
file security
CORS change
CSP change
cookie-policy change
third-party resource change
authentication-flow change
```

If unavailable:

return:

`CHECK_GAP`

The skill must not self-approve formal Checks.

---

# Result Statuses

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

SECURITY_IMPACT_UNRESOLVED
ES0902_CONTEXT_REQUIRED

SECURITY_ASSESSMENT_REQUIRED
SECURITY_ASSESSMENT_REFRESH_REQUIRED
SECURITY_ASSESSMENT_BLOCKING
SECURITY_ASSESSMENT_REJECTED
SECURITY_ASSESSMENT_PENDING

AUTHENTICATION_SECURITY_UNRESOLVED
AUTHORIZATION_ENFORCEMENT_RISK
EXCESSIVE_PRIVILEGE_RISK
SERVICE_TOKEN_PROTECTION_MISSING

SECRET_EXPOSURE_RISK
SECURITY_INCIDENT_PROCESS_REQUIRED
SERVER_SIDE_VALIDATION_RISK
SECURITY_LOGGING_RISK
FILE_SECURITY_REVIEW_REQUIRED

DEPENDENCY_SECURITY_RISK
SAST_EVIDENCE_MISSING
DAST_EVIDENCE_MISSING
DEPENDENCY_SCAN_EVIDENCE_MISSING
STALE_SECURITY_EVIDENCE

SECURITY_EXCEPTION_APPROVAL_REQUIRED

CORS_SECURITY_UNRESOLVED
CSP_SECURITY_UNRESOLVED

DATABASE_PRIVILEGE_RISK
CROSS_ENVIRONMENT_SECURITY_RISK
CLOUD_SECURITY_REVIEW_REQUIRED

SECURITY_GATE_BYPASS_RISK

ARCHITECTURE_REVIEW_REQUIRED
DEVOPS_CHANGE_REQUIRED
SECURITY_REMEDIATION_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

```yaml
securityResult:

  status: COMPLETE
  readiness: READY

  workUnit:
    id: WU-123

  artifact:
    commit: abc123
    version: 2.4.0
    digest: sha256:...

  impact:

    dimensions:
      - AUTHENTICATION
      - AUTHORIZATION
      - DEPENDENCIES

    changedEndpoints: true
    changedAuthentication: true
    changedDependencies: false

  normative:

    es0901:
      applicable: true

    es0902:
      available: false
      requiredForUnresolvedDetails: false

  assessment:

    required: true

    reason:
      - AUTHENTICATION_FLOW_CHANGED
      - ENDPOINTS_CHANGED

    environment: QA
    status: APPROVED
    evidenceReference: assessment-2026-09-001

  authentication:
    result: PASS

  authorization:
    result: PASS
    backendEnforcementValidated: true

  serviceProtection:
    tokenRequired: true
    result: PASS

  secrets:
    exposureDetected: false

  scanners:

    sast:
      executed: true
      artifactMatch: true
      openFindings: 0

    dast:
      executed: true
      environment: QA
      artifactMatch: true
      openFindings: 0

    dependencyScanning:
      executed: true
      openFindings: 0

  findings: []
  blockingFindings: []
  unresolved: []

  reviews:
    architectureRequired: false
    devopsRequired: false

  evidence:
    - git-diff-123
    - pipeline-security-456
    - assessment-2026-09-001

  assumptions: []
```

---

# Model Routing Metadata

## STANDARD

Use for:

```text
scanner result correlation
simple dependency review
secret/reference checks
assessment-trigger evaluation
straightforward authorization/configuration review
```

## REASONING

Consider when:

```text
authentication/authorization changes
multiple trust boundaries
conflicting scanner evidence
complex role/permission model
new third-party integration
infrastructure/protocol migration
complex remediation or false-positive analysis
cross-environment credential/security issues
```

## PREMIUM

Consider only when:

```text
critical security architecture
high-impact production exposure
complex multi-system auth/trust redesign
security incident analysis
repeated lower-tier reasoning fails
```

Premium execution must pass the orchestrator's Human Model Gate.

Security-sensitive mutations remain independently governed by the Tool Risk Human Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- ES0902 is required but unavailable
- official Security Assessment is required/pending/rejected
- security evidence is stale or missing
- a blocking scanner/assessment finding exists
- authentication or authorization semantics are unresolved
- a secret was exposed
- excessive privilege exists
- production/environment credential mixing exists
- dependency vulnerability has no remediation path
- CORS/CSP/cookie changes lack required security context
- a new third-party trust boundary exists
- infrastructure/protocol change requires security review
- cloud security context is incomplete
- architecture/devops remediation is required
- required capability/check is unavailable

---

# Prohibited Behavior

This skill must not:

- self-approve the official GCBA Security Assessment
- fabricate ES0902 rules when ES0902 is unavailable
- treat SAST/DAST/Dependency Scanning as equivalent to assessment approval
- treat scanner PASS as proof that the application is secure
- dismiss a finding without evidence
- invent CVSS/severity values
- invent security exceptions
- expose raw secrets/tokens
- copy production credentials into lower environments
- use developer assertion as authorization evidence
- treat frontend-only authorization as sufficient backend security
- weaken CORS/CSP/cookies merely to fix functionality
- run intrusive DAST/security actions against PRD without approval
- change identity/security architecture silently
- take over implementation owned by another specialized agent
- create Tools directly
- self-approve formal Checks
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- identifies security impact from the real implementation
- applies available ES0901 requirements
- refuses to invent missing ES0902 rules
- correctly determines when Annex V assessment is required
- blocks HML/PRD when required assessment approval is missing
- reviews authentication and authorization boundaries
- validates token/service protection
- validates least privilege where evidence exists
- detects secret exposure and environment credential mixing
- consumes SAST, DAST and Dependency Scanning evidence
- correlates vulnerabilities without hiding real findings
- validates remediation/retest evidence
- recognizes security-impacting CORS/CSP/cookie/dependency/infrastructure changes
- coordinates implementation owners rather than becoming a super-agent
- returns an explicit, evidence-backed security readiness state

---

# Security Skill Model

The `dev-security` agent is composed of four complementary skills:

```text
dev-security-analysis
→ coordinates security impact, evidence, and overall readiness

dev-security-assessment
→ determines Annex V assessment applicability and prepares the QA candidate/evidence package

dev-appsec-review
→ performs deep technical application-security review of code, configuration, trust boundaries and controls

dev-vulnerability-management
→ manages findings from discovery through remediation, retest, reassessment, and closure
```

Mandatory separation:

```text
assessment preparation
≠ official assessment approval

AppSec review
≠ vulnerability lifecycle management

scanner execution
≠ security readiness

remediation implemented
≠ finding closed until retested
```

---

# Source References

Primary available source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Key areas:

```text
1
→ ES0901 complements ES0902

3
→ authentication / environment controls

4
→ security as a core software-change objective

6.5
→ minimum database permissions

6.7
→ mandatory logging

6.8
→ dependency/component responsibility and vulnerability inventory

7.1
→ D1, D2, D8, P1, P5

8.2
→ GCBA authentication / roles / permissions

Annex I
→ SAST / DAST / Dependency Scanning

Annex V
→ mandatory Security Assessment
→ QA execution
→ HML/PRD promotion gate
→ reassessment frequency
→ change categories requiring renewed assessment consideration
```

This skill must not silently infer the detailed contents of `ES0902 - Estándar de Seguridad`.
