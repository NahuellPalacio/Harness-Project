---
name: dev-appsec-review
description: Use when a GCBA / DGISIS change needs a deep application-security review before assessment or release — source code, configuration, trust boundaries, authentication and authorization behaviour, input and output handling, secrets, dependencies, integrations, file flows and the runtime controls that apply. Produces the technical evidence that dev-security-analysis, dev-security-assessment and dev-vulnerability-management consume. Owned by dev-security.
---

# Skill: dev-appsec-review

## Purpose

Perform deep application-security review of GCBA software changes before official assessment or release by inspecting source code, configuration, trust boundaries, authentication/authorization behavior, input/output handling, secrets, dependencies, integrations, file flows, and relevant runtime controls.

This skill belongs to the `dev-security` agent.

It provides technical AppSec evidence to:

- `dev-security-analysis`
- `dev-security-assessment`
- `dev-vulnerability-management`

It does not replace the official GCBA Security Assessment.

## Owner

Primary owner:

`dev-security`

Related implementation owners:

- `dev-backend`
- `dev-frontend`
- `dev-integration`
- `dev-openid-connect`
- `dev-miba`
- `dev-storage`
- `dev-devops`
- `dev-openshift`
- `dev-persistence`

---

# Core Principle

> Review the actual attack surface created or modified by the WorkUnit, not a generic checklist detached from the implementation.

The skill must answer:

```text
What trust boundaries changed?
What attacker-controlled inputs were introduced?
What privileges are required?
What data/resources can be accessed?
What authentication/authorization protects them?
What can be abused if a control fails?
What evidence proves the control exists?
```

---

# Normative Sources

## GCBA

Primary available source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas:

```text
D1 / D2
→ approved authentication

D8
→ token protection for services

P1
→ approved frameworks / dependency management

P5
→ frontend/backend validation

6.5
→ minimum DB permissions

6.7
→ mandatory logs

6.8
→ dependency/component responsibility

8.2
→ authentication, roles and permissions

Annex I
→ SAST / DAST / Dependency Scanning

Annex V
→ assessment-triggering changes
```

ES0901 delegates broader security requirements to:

`ES0902 - Estándar de Seguridad`

If a GCBA-specific security rule requires ES0902 and it is unavailable:

return:

`ES0902_CONTEXT_REQUIRED`

## Supplementary industry references

Under ES0901 G2, supplementary guidance may use:

```text
OWASP ASVS 5.0.0
OWASP WSTG 4.2 stable
OWASP Cheat Sheet Series where relevant
```

These do not replace GCBA normative requirements.

---

# Review Scope

Potential domains:

```text
ARCHITECTURE_AND_TRUST_BOUNDARIES
AUTHENTICATION
AUTHORIZATION
SESSION_AND_TOKEN_HANDLING
ACCESS_CONTROL
INPUT_VALIDATION
INJECTION
OUTPUT_ENCODING
BROWSER_SECURITY
CORS
CSP
COOKIES
STATE_CHANGING_REQUESTS
FILES
STORAGE
CRYPTOGRAPHIC_USAGE
SECRETS
ERROR_HANDLING
LOGGING
DATA_EXPOSURE
API_SECURITY
EXTERNAL_INTEGRATIONS
WEBHOOKS
DEPENDENCIES
SUPPLY_CHAIN
DATABASE_PRIVILEGES
OPENSHIFT_RUNTIME
NETWORK_EXPOSURE
BUSINESS_LOGIC_ABUSE
```

Select only applicable domains.

---

# Mandatory Workflow

```text
1. Resolve WorkUnit and actual diff
2. Build changed attack-surface map
3. Identify trust boundaries
4. Identify protected resources/actions
5. Review authentication
6. Review authorization/access control
7. Review token/session handling
8. Review input/data/file flows
9. Review output/error/log exposure
10. Review browser/client security
11. Review API/integration/webhook boundaries
12. Review dependency/supply-chain delta
13. Review runtime/configuration/secrets
14. Correlate SAST/DAST evidence
15. Perform targeted manual reasoning/testing
16. Record findings with evidence
17. Route remediation to owning agent
18. Retest remediated controls
19. Return AppSec readiness
```

---

# Attack-Surface Delta

Start from the real change.

Map additions/modifications to:

```text
routes
endpoints
forms
parameters
webhooks
background jobs
admin actions
file operations
database operations
identity flows
external scripts
third-party APIs
network exposure
runtime permissions
```

If the surface cannot be identified:

`APPSEC_SCOPE_UNRESOLVED`

---

# Trust Boundaries

Identify transitions such as:

```text
browser → frontend
browser → backend
backend → database
backend → internal service
backend → external provider
provider → webhook
internet → route
application → object storage
pipeline → deployment platform
harness → external API
```

For each changed boundary record:

```text
caller
target
authentication
authorization
data
credentials
validation
failure behavior
```

---

# Authentication Review

Implementation belongs to identity/integration skills.

AppSec validates evidence around:

```text
approved authentication mechanism
credential delegation
callback/redirect handling
state/context correlation
session establishment
logout behavior
environment configuration
legacy-path coexistence during migration
```

Use `dev-openid-connect` / `dev-miba` as implementation context.

Do not invent provider behavior.

---

# Authorization Review

For each sensitive operation identify:

```text
who may call it
what resource may be accessed
where authorization is enforced
what object/user context is checked
```

Frontend hiding/disabling is not authorization.

Server-side enforcement is required for protected resources.

Potential finding:

`BROKEN_AUTHORIZATION_RISK`

---

# Object-Level Access

When an endpoint accepts a resource identifier, verify authorization against the requested object where required.

Do not assume:

```text
authenticated user
→ may access any object identifier
```

---

# Function-Level Access

Review privileged actions:

```text
admin endpoints
backoffice operations
role management
bulk operations
export/download
configuration actions
```

Verify backend privilege enforcement.

---

# Session / Token Handling

Inspect:

```text
token source
audience/context when relevant
storage
transport
logging
URL leakage
refresh/session behavior
logout/invalidation
environment separation
```

Do not duplicate protocol-specific implementation rules owned by identity skills.

---

# Secrets

Inspect likely sources:

```text
source code
properties/yaml
.gitlab-ci.yml
README/Markdown
test fixtures
Playwright auth state
logs
traces
screenshots
build args
ConfigMaps
```

If a real secret is exposed:

`SECRET_EXPOSURE_RISK`

Removal alone is not complete remediation; route rotation/incident handling through `dev-security-analysis`.

---

# Input Validation

Review untrusted input:

```text
path/query params
headers
JSON/form bodies
file metadata
webhook payloads
sorting/filtering
identifiers
redirect targets
URLs
serialized content
```

Backend validation is authoritative.

Frontend validation is not a security boundary.

---

# Injection-Oriented Review

Under supplementary industry guidance, inspect attacker-controlled input reaching interpreters such as:

```text
SQL/ORM query construction
shell/process execution
template engines
HTML/DOM sinks
URL/redirect construction
filesystem/object paths
expression languages
deserializers
```

Do not report a vulnerability solely from pattern similarity; verify data flow/evidence.

---

# SQL / Persistence Review

Inspect dynamic query construction and authorization around persistence.

Remediation ownership:

`dev-persistence`

Do not redesign persistence from this skill.

---

# Browser / Frontend Security

Where applicable inspect:

```text
unsafe DOM insertion
token exposure
third-party scripts
iframe/embed behavior
CSP changes
CORS assumptions
cookie/session behavior
sensitive browser storage
```

Frontend code is not trusted authorization enforcement.

---

# CORS

Review:

```text
allowed origins
credential behavior
methods
headers
environment mapping
business/technical reason
```

Permissive changes require evidence.

Return:

`CORS_SECURITY_RISK`

when unsafe/unresolved.

---

# CSP

Review CSP changes relative to:

```text
script sources
frames
external assets
inline execution
third-party services
```

Do not weaken CSP only to bypass browser errors.

Return:

`CSP_SECURITY_RISK`

when unsafe/unresolved.

---

# Cookies

Review security-relevant cookie behavior using project/ES0902 evidence.

If GCBA-specific required settings depend on unavailable ES0902:

`ES0902_CONTEXT_REQUIRED`

Do not invent policy values.

---

# State-Changing Requests

Review protection according to the actual authentication/session architecture.

Do not mechanically require one technique for every architecture.

Determine the real threat and control.

---

# API Security

For changed APIs review:

```text
authentication
authorization
object-level access
function-level access
input constraints
response minimization
error behavior
abuse/rate controls when requirements exist
token protection
contract/versioning
```

D8 token protection does not replace authorization.

---

# Webhooks

Review:

```text
sender authentication/verifiability
payload validation
replay/idempotency behavior
secret handling
authorization
failure behavior
```

Exact mechanisms depend on provider contracts.

---

# External Providers

Review:

```text
credential scope
environment
data exchanged
callbacks
provider URLs
trust assumptions
third-party scripts/SDKs
error handling
```

Use `dev-external-integration` for implementation evidence.

---

# File Upload / Download

Annex V treats file features as assessment-relevant.

Review:

```text
upload/download authorization
metadata/content constraints from requirements
storage destination
object/path construction
temporary-file lifecycle
public exposure
download authorization
error/log exposure
```

Implementation remains with `dev-storage` / backend.

---

# Data Exposure

Review data returned through:

```text
API responses
UI
exports
files
logs
health endpoints
errors
debug output
```

Check whether more information is exposed than needed.

Do not invent classification requirements absent ES0902/project context.

---

# Error Handling

Review leakage of:

```text
stack traces
internal paths
SQL errors
provider secrets
tokens
internal hosts
debug details
```

Maintain useful operational diagnostics through `dev-observability`.

---

# Logging

Review:

```text
security-event observability where required
token/secret redaction
useful provenance
mandatory logging not disabled
```

Never log credentials/tokens to improve debugging.

---

# Dependencies

Inspect:

```text
direct dependencies
transitive impact
versions
lock files
approved framework/tool context
runtime inclusion
scanner findings
```

Known vulnerability lifecycle goes to:

`dev-vulnerability-management`

---

# Supply Chain

Supplementary review may inspect:

```text
unexpected package registry
dependency confusion risk
unpinned external script
pipeline include
build plugin
base image
downloaded executable
```

Only report evidence-backed concerns.

---

# Database Privileges

ES0901 requires minimum permissions for application DB users.

Compare required operations with granted privileges where evidence exists.

Return:

`DATABASE_PRIVILEGE_RISK`

when materially over-privileged.

---

# OpenShift / Runtime

Consume `dev-openshift` evidence:

```text
Secret references
ConfigMaps
Route exposure
service account/RBAC
environment mapping
persistent-local-storage violations
```

Do not duplicate platform implementation.

---

# Manual Security Testing

Use targeted manual testing when automated evidence is insufficient.

OWASP WSTG 4.2 may be used as supplementary methodology.

Select scenarios based on the changed attack surface.

Do not run intrusive testing against PRD without approval.

---

# ASVS Mapping

OWASP ASVS 5.0.0 may be used as a supplementary verification catalog.

When used:

```text
select applicable requirement
record versioned ID
record evidence
record PASS / FAIL / NOT_APPLICABLE / NOT_TESTED
```

Do not claim full ASVS conformance unless the agreed scope and evidence truly support it.

---

# SAST Correlation

Use SAST as evidence and as a pointer to suspicious code.

Do not:

```text
dismiss findings without evidence
treat zero SAST findings as proof of security
```

---

# DAST Correlation

Map DAST runtime findings back to implementation where possible.

Preserve environment and candidate provenance.

---

# Finding Model

```yaml
appsecFinding:

  id: ...
  source: MANUAL_REVIEW | SAST | DAST | ASVS | WSTG
  title: ...
  component: ...

  severity: SOURCE_DEFINED_OR_POLICY_DEFINED
  confidence: HIGH | MEDIUM | LOW

  evidence: []
  impact: []

  remediationOwner: dev-backend
  remediationRequired: true

  retest:
    required: true
```

If no severity model/source exists:

`SEVERITY_UNRESOLVED`

Do not invent CVSS.

---

# Evidence vs Hypothesis

Distinguish:

```text
CONFIRMED_FINDING
POTENTIAL_RISK
UNRESOLVED_QUESTION
FALSE_POSITIVE_CANDIDATE
```

Speculation is not a confirmed vulnerability.

---

# Remediation Ownership

Examples:

```text
backend authorization
→ dev-backend

OIDC callback
→ dev-openid-connect

CORS/runtime route
→ dev-devops / dev-openshift

storage authorization
→ dev-storage / backend

dependency update
→ owning application agent
```

Security identifies/validates the requirement; the correct domain Agent implements it.

---

# Retest

After remediation:

```text
inspect changed code/config
rerun targeted test/scanner
verify original attack path/control
capture new candidate identity
```

Do not close because a ticket says "fixed".

---

# Required Capabilities

Typical:

```text
repository.read
repository.search
git.diff.inspect

api.routes.inspect
authorization.rules.inspect
authentication.config.inspect
dependency.manifest.inspect
configuration.inspect
secret.reference.inspect

security.sast.results.inspect
security.dast.results.inspect

test.execute
http.request.execute
browser.automation.run
```

Optional:

```text
openshift.route.inspect
openshift.permissions.inspect
file.flow.inspect
database.permissions.inspect
```

If unavailable:

`CAPABILITY_GAP`

---

# Required Checks

Potential:

```text
attack-surface-delta
backend-authorization
service-token-protection
secret-exposure
server-side-validation
cors-policy
csp-policy
file-access-control
dependency-security
database-least-privilege
logging-secret-exposure
runtime-secret-separation
```

If unavailable:

`CHECK_GAP`

---

# Result Statuses

```text
COMPLETE
PARTIAL
MISSING_CONTEXT
APPSEC_SCOPE_UNRESOLVED
ES0902_CONTEXT_REQUIRED
BROKEN_AUTHORIZATION_RISK
SERVICE_TOKEN_PROTECTION_MISSING
SECRET_EXPOSURE_RISK
SERVER_SIDE_VALIDATION_RISK
CORS_SECURITY_RISK
CSP_SECURITY_RISK
FILE_SECURITY_REVIEW_REQUIRED
DATA_EXPOSURE_RISK
SECURITY_LOGGING_RISK
DEPENDENCY_SECURITY_RISK
DATABASE_PRIVILEGE_RISK
CONFIRMED_SECURITY_FINDING
POTENTIAL_SECURITY_RISK
SEVERITY_UNRESOLVED
REMEDIATION_REQUIRED
RETEST_REQUIRED
CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED
FAILED
```

---

# Output Contract

```yaml
appsecReviewResult:

  status: COMPLETE
  readiness: READY

  workUnit:
    id: WU-123

  candidate:
    commit: abc123
    environment: QA

  scope:
    changedEndpoints:
      - POST /api/example
    authChanged: false
    fileHandlingChanged: false
    dependenciesChanged: true

  trustBoundaries:
    - browser-to-backend
    - backend-to-provider

  review:
    authentication: PASS
    authorization: PASS
    inputValidation: PASS
    secrets: PASS
    apiSecurity: PASS
    dependencies: PASS

  supplementaryStandards:
    asvs:
      version: 5.0.0
      mappedRequirements: []
    wstg:
      version: 4.2
      scenarios: []

  findings:
    confirmed: []
    potential: []

  blockingFindings: []
  retestRequired: false
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

## STANDARD

Use for routine source/config review, simple endpoint authorization, dependency delta and scanner correlation.

## REASONING

Use for complex authorization, identity migration, multiple trust boundaries, webhook/provider flows, unclear data flows, scanner triage and business-logic abuse analysis.

## PREMIUM

Only for critical auth/security architecture or unresolved high-impact multi-system security analysis.

Requires Human Model Gate approval.

---

# Prohibited Behavior

This skill must not:

- replace the official Security Assessment
- invent ES0902 rules
- claim full ASVS compliance without full scoped verification
- call speculative patterns confirmed vulnerabilities
- invent severity/CVSS
- use frontend checks as authorization proof
- expose secrets during review
- run intrusive PRD testing without approval
- silently weaken security controls
- implement every remediation itself
- self-approve exceptions
- self-approve formal Checks
- create Tools directly
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- scopes review from the real implementation delta
- maps trust boundaries and attack surface
- reviews authentication/authorization correctly
- checks server-side input enforcement
- reviews secrets/data/log exposure
- reviews APIs, files, integrations and dependencies
- correlates scanners with manual analysis
- uses OWASP ASVS/WSTG only as labeled supplementary guidance
- separates confirmed vs potential findings
- assigns remediation to the correct owner
- verifies remediation through retest
- produces evidence usable by `dev-security-assessment`

---

# Source References

## GCBA

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

## Supplementary industry references

OWASP ASVS 5.0.0:
https://owasp.org/projects/asvs/

OWASP WSTG 4.2:
https://wstg.owasp.org/v4.2/

OWASP Web Security Testing Guide:
https://owasp.org/projects/web-security-testing-guide/

These supplement ES0901 G2 and do not replace ES0902 or the official GCBA Security Assessment.
