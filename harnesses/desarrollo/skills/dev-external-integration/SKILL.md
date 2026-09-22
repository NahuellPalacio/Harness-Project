---
name: dev-external-integration
description: Use when a GCBA / DGISIS application integrates with an external provider whose contract, availability, authentication, quotas and lifecycle the team does not control — Doppler, SMTP, Google or Microsoft APIs, SaaS platforms, third-party SDKs, external REST APIs, inbound and outbound webhooks, notification or document services. Keeps the provider from leaking into the application, the configuration out of the code and the failures traceable. Owned by dev-integration.
---

# Skill: dev-external-integration

## Purpose

Plan and implement integrations between a GCBA application and an external provider whose contract, availability, authentication model, quotas, lifecycle, and operational behavior are not controlled by the application team.

This skill belongs to the `dev-integration` agent.

Typical examples include:

- Doppler
- SMTP providers
- Google APIs
- Microsoft APIs
- SaaS platforms
- external REST APIs
- official third-party SDKs
- inbound/outbound webhooks
- external notification providers
- external document or messaging services

The skill must protect the application from unnecessary provider coupling and must preserve project architecture, security boundaries, configuration separation, and operational traceability.

---

## Owner

Primary owner:

`dev-integration`

Primary implementation entry point:

`dev-integration-implementation`

Related skills:

- `dev-api`
- `dev-backend-implementation`
- `dev-frontend-implementation`
- `dev-data`
- `dev-storage`
- `dev-observability`
- `dev-security-analysis`
- `dev-devops-implementation`
- `dev-architecture-analysis`
- `dev-openid-connect`
- `dev-miba`

---

# Core Principle

The skill must answer:

> How can this GCBA application consume or receive information from an external provider safely, without leaking provider-specific behavior into the rest of the system and without inventing behavior the provider does not document?

Apply this principle:

> Adapt to the provider contract at the integration boundary. Do not redesign the provider contract and do not spread provider-specific details across the application.

---

# What This Skill Owns

This skill owns external-provider integration behavior such as:

```text
provider discovery
contract discovery
integration mechanism selection
provider adapter/client implementation
request/response mapping
provider-specific error mapping
external authentication configuration
timeouts
retries
rate limits
quotas
idempotency
webhooks
sandbox/test/production environment mapping
provider-specific observability
provider non-regression
provider replacement isolation
```

---

# What This Skill Does Not Own

This skill does not own:

```text
application API contract design
user authentication flows
GCBA identity rules
miBA implementation
OpenID Connect user login
major architecture redesign
platform provisioning
security approval
business fallback rules
provider procurement or commercial decisions
```

Use:

```text
dev-api
→ our API contracts

dev-openid-connect
→ user authentication using OpenID Connect

dev-miba
→ miBA-specific integration

dev-architecture-analysis
→ major integration architecture changes

dev-security-analysis
→ security review

dev-devops-implementation
→ platform/runtime provisioning
```

---

# External Provider Definition

Treat a dependency as an external provider when the application team does not control one or more of:

```text
contract evolution
availability
authentication model
rate limits
quota
maintenance windows
provider infrastructure
provider deployment
provider error semantics
```

The provider may be public, private, commercial, governmental, or organizationally external to the application team.

---

# Provider Types

Classify the provider before implementation.

Supported conceptual types:

```text
REST_API
SOAP_SERVICE
GRPC_SERVICE
SMTP_PROVIDER
SAAS_PLATFORM
OFFICIAL_SDK
WEBHOOK_PROVIDER
EXTERNAL_STORAGE
EXTERNAL_MESSAGING
OTHER
```

The mechanism and provider type are separate.

Example:

```text
provider: Doppler
providerType: SAAS_PLATFORM
mechanism: REST_API
```

or:

```text
provider: corporate-mail
providerType: SMTP_PROVIDER
mechanism: SMTP
```

---

# Mandatory Workflow

The skill must execute this sequence:

```text
1. Identify provider and business purpose
2. Inspect existing integration
3. Discover authoritative provider contract
4. Identify available integration mechanisms
5. Select the mechanism using project evidence
6. Define provider boundary
7. Resolve authentication and secrets
8. Resolve environment mapping
9. Evaluate provider limits
10. Define timeout/retry/idempotency behavior
11. Implement adapter/client
12. Define provider error mapping
13. Configure observability
14. Validate against sandbox/test environment
15. Validate non-regression
16. Return structured evidence
```

---

# Phase 1 — Provider Identification

The skill must identify:

```text
provider name
business purpose
consumer component
direction
operations required
criticality
data exchanged
```

Example:

```yaml
provider:
  name: Doppler
  purpose: transactional-email-delivery
  direction: OUTBOUND
  criticality: MEDIUM
```

If the actual provider or purpose is unclear:

return:

`EXTERNAL_PROVIDER_UNRESOLVED`

---

# Phase 2 — Inspect Existing Integration

Before introducing a new external integration, search for:

```text
existing provider client
existing adapter
existing SDK
existing SMTP configuration
existing OAuth/service account configuration
existing webhook endpoint
existing mapping layer
existing provider error model
existing tests
existing provider configuration
```

Apply:

```text
reuse
  ↓
extend
  ↓
create
```

Do not create a second Doppler/Google/SMTP integration path if the project already has a valid one.

If reuse is possible:

record:

`EXISTING_PROVIDER_INTEGRATION_REUSE`

---

# Phase 3 — Provider Contract

The skill must identify an authoritative provider contract.

Possible sources:

```text
official provider documentation
OpenAPI specification
official SDK documentation
SMTP protocol/provider documentation
provider portal
webhook schema
provider examples
existing approved integration documentation
existing production code
```

The skill must not invent:

```text
endpoint paths
request fields
response fields
headers
webhook fields
error codes
quota values
authentication requirements
retry behavior
```

If the authoritative contract is missing:

return:

`EXTERNAL_PROVIDER_CONTRACT_MISSING`

---

# Phase 4 — Integration Mechanism Selection

External providers may expose multiple mechanisms:

```text
REST API
SOAP
gRPC
SMTP
official SDK
webhook
file exchange
OAuth-based API
service account
```

The skill must not automatically prefer REST.

Evaluate:

```text
existing project mechanism
provider-recommended mechanism
official support level
contract clarity
dependency cost
maintainability
security requirements
operational requirements
testability
portability
```

Example:

```text
Doppler
→ REST API may be appropriate if the project requires transactional email through the provider API.

SMTP
→ may remain appropriate when the provider and project explicitly use SMTP.

Google
→ official API/SDK/service-account mechanism may be appropriate depending on the service.
```

Do not generalize one provider decision to all external integrations.

If mechanism selection changes application architecture:

return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Provider Boundary

Provider-specific behavior should be isolated at an explicit boundary.

Conceptually:

```text
Application / Business Logic
            ↓
     Provider Port / Service
            ↓
       Provider Adapter
            ↓
       External Provider
```

Example:

```text
NotificationService
        ↓
EmailProvider
        ↓
DopplerAdapter
        ↓
Doppler
```

The exact pattern must follow the existing project architecture.

Do not introduce a new abstraction solely because this skill prefers one.

The reusable rule is:

> Provider-specific contracts should not unnecessarily leak into unrelated application code.

---

# Provider Replacement Isolation

Where practical and consistent with project architecture, isolate provider-specific behavior so future provider replacement affects primarily the integration boundary.

Do not over-engineer speculative provider portability.

Create abstraction only when supported by:

```text
current architecture
multiple providers
known migration requirement
existing application boundary
real replacement risk
```

---

# Data Mapping

External provider models and application models must be treated as separate contracts.

Expected pattern:

```text
application model
      ↓
explicit mapping
      ↓
provider model
```

The skill must identify:

```text
mapped fields
defaulted fields
provider-required fields
ignored fields
lossy transformations
provider-specific identifiers
```

Do not let provider DTOs become the application domain model unless the current project architecture explicitly does so.

If mapping changes business semantics:

delegate to:

`dev-data`

---

# External Authentication

This skill may handle provider authentication when it exists only to authenticate the application/service to the external provider.

Examples:

```text
API key
Basic Auth
service token
OAuth client credentials
service account
provider secret
signed request
```

This is different from user authentication.

Use:

```text
external provider service credentials
→ dev-external-integration

user login / OIDC identity
→ dev-openid-connect

miBA user identity
→ dev-miba
```

If authentication affects user identity/session:

delegate to the appropriate identity skill.

If provider authentication is unclear:

return:

`EXTERNAL_AUTHENTICATION_UNRESOLVED`

---

# Secrets

External credentials must use the approved secret mechanism.

Never:

```text
hardcode API keys
hardcode passwords
hardcode client secrets
store service-account secrets in source control
log Authorization headers
log refresh tokens
log access tokens
include secrets in generated docs
copy secrets between environments
```

If violated:

return:

`SECRET_CONFIGURATION_RISK`

---

# Environment Mapping

GCBA environments and provider environments may not map one-to-one.

The skill must explicitly resolve this mapping.

Example:

```text
GCBA DEV ──┐
GCBA QA  ──┼──→ Provider TEST
GCBA HML ──┘

GCBA PRD ─────→ Provider PRODUCTION
```

or any other mapping actually approved by the provider/project.

Represent explicitly:

```yaml
environmentMapping:

  DEV:
    providerEnvironment: TEST

  QA:
    providerEnvironment: TEST

  HML:
    providerEnvironment: TEST

  PRD:
    providerEnvironment: PRODUCTION
```

Do not infer environment mapping.

If unknown:

return:

`EXTERNAL_ENVIRONMENT_MAPPING_UNRESOLVED`

---

# Provider Limits

The skill must inspect provider-specific limits when relevant.

Examples:

```text
rate limits
request quotas
daily quotas
concurrency limits
payload size limits
attachment limits
recipient limits
API pagination limits
webhook delivery policies
SDK limits
provider timeout limits
```

Never invent limits.

If they are important to the WorkUnit but unavailable:

return:

`EXTERNAL_PROVIDER_LIMITS_UNKNOWN`

---

# Rate Limiting

When the provider publishes rate limits:

the skill must determine whether the current usage pattern may exceed them.

Possible mitigations may include:

```text
request pacing
queueing
batching
caching
provider-recommended retry-after handling
business throttling
```

Do not introduce these mechanisms without evidence that they are needed and compatible with architecture.

If a major asynchronous redesign is required:

return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Timeout

Every remote provider interaction must evaluate timeout behavior.

The skill should determine:

```text
provider expected latency
project/platform timeout constraints
client timeout
failure behavior
```

Do not use arbitrary timeout values.

Use provider documentation, existing project values, or platform rules.

If unresolved:

return:

`TIMEOUT_POLICY_UNRESOLVED`

---

# Retry

Retries must be provider-aware and operation-aware.

Never:

```text
retry every error
retry every POST
retry indefinitely
```

Evaluate:

```text
operation type
provider error category
HTTP/status semantics
provider Retry-After behavior
idempotency
side effects
existing retry policy
```

Typical examples:

```text
connection failure
→ may be retryable

HTTP 429
→ may require provider-defined backoff / Retry-After

HTTP 5xx
→ may be retryable depending on operation/provider

validation error
→ normally not retryable

authentication error
→ normally requires configuration correction
```

These are general diagnostic categories, not universal provider guarantees.

If retry behavior cannot be safely determined:

return:

`RETRY_POLICY_UNRESOLVED`

---

# Idempotency

The skill must explicitly evaluate whether duplicate requests can create duplicate external side effects.

Examples:

```text
send email
create contact
create calendar event
submit document
charge/payment-like operation
create remote resource
```

Evidence may include:

```text
provider idempotency key
business key
provider documented deduplication
safe HTTP semantics
existing application control
```

If duplicate execution may create business impact:

return:

`IDEMPOTENCY_RISK`

Never claim idempotency without evidence.

---

# SMTP-Specific Boundary

SMTP may be treated as an external integration mechanism.

When using SMTP, inspect:

```text
host
port
TLS requirements
authentication
sender restrictions
timeouts
delivery response handling
environment configuration
credentials
provider limitations
```

Do not assume SMTP delivery success means final message delivery.

The skill must distinguish:

```text
SMTP accepted by server
≠
message delivered to recipient
```

If final delivery tracking is required, provider-specific delivery events or another mechanism may be necessary.

---

# REST API-Specific Boundary

For external REST APIs, inspect:

```text
base URL
resource paths
HTTP methods
headers
authentication
request schema
response schema
pagination
status codes
timeouts
rate limits
versioning
```

Do not redesign the provider's REST contract.

Our application adapts to it.

---

# Official SDK Use

If an official provider SDK exists, the skill must evaluate rather than automatically adopt it.

Inspect:

```text
official support status
language/runtime compatibility
version compatibility
dependency weight
security/maintenance status
contract coverage
existing project usage
provider recommendation
testability
```

If the SDK adds unnecessary coupling or conflicts with approved dependencies, direct API use may be preferable.

If the provider requires the SDK for supported functionality, respect that evidence.

---

# Webhooks

Inbound provider webhooks are part of this skill.

The skill must inspect:

```text
webhook contract
provider authentication/signature
source validation
payload validation
replay behavior
idempotency
duplicate delivery
retry policy
response requirements
observability
sensitive data
```

Conceptual flow:

```text
External Provider
      ↓
Webhook Endpoint
      ↓
Provider Validation
      ↓
Payload Mapping
      ↓
Application Processing
```

If the webhook changes our public API surface:

coordinate with:

`dev-api`

If signature/security verification is required:

coordinate with:

`dev-security-analysis`

---

# Webhook Replay and Duplicate Delivery

Do not assume webhook delivery occurs once.

If provider documentation indicates retries or duplicate delivery are possible, the application must evaluate idempotency/replay protection.

If the provider behavior is unknown and duplicate processing would be harmful:

return:

`WEBHOOK_REPLAY_RISK`

---

# Error Mapping

Provider errors must be translated into controlled application errors.

Expected boundary:

```text
provider error
      ↓
provider adapter
      ↓
integration error
      ↓
application behavior
```

Do not leak uncontrolled provider/internal details to users or public APIs.

Provider-specific diagnostics may remain in internal logs when safe.

If public API behavior must change:

coordinate with:

`dev-api`

---

# Provider Error Categories

Where useful, classify provider failures into stable internal categories such as:

```text
AUTHENTICATION
AUTHORIZATION
VALIDATION
RATE_LIMIT
TIMEOUT
UNAVAILABLE
CONTRACT_ERROR
REMOTE_BUSINESS_REJECTION
UNKNOWN_PROVIDER_ERROR
```

Do not pretend provider-specific error codes are universal.

The mapping must be evidence-based.

---

# Fallback Behavior

The skill must not invent business fallback behavior.

Examples of fallback decisions:

```text
send email later
switch provider
store request for retry
continue without external data
return partial response
```

These are business/architecture decisions.

If no approved fallback exists:

return:

`EXTERNAL_FAILURE_BEHAVIOR_UNRESOLVED`

---

# Observability

External integrations require operational evidence because failures may occur outside GCBA-controlled infrastructure.

Coordinate with:

`dev-observability`

When appropriate, capture non-sensitive fields such as:

```text
provider
operation
provider environment
duration
result
status category
retry count
rate-limit event
provider request identifier
application correlation identifier if already supported
```

Never log:

```text
API keys
passwords
OAuth secrets
tokens
Authorization headers
sensitive payloads
full URLs containing secrets/tokens
service-account private keys
```

---

# Provider Availability

The application must explicitly understand how provider unavailability affects the WorkUnit.

Possible impact classifications:

```text
BLOCKING
DEGRADED
DEFERRED
NON_CRITICAL
```

Do not decide this based solely on technical preference.

Use product/business/architecture evidence.

If unknown:

return:

`EXTERNAL_FAILURE_BEHAVIOR_UNRESOLVED`

---

# Versioning and Provider Evolution

External contracts may change outside the application's release cycle.

Inspect:

```text
API version
SDK version
deprecation notices
sunset dates
provider compatibility guarantees
```

Do not automatically upgrade SDK/API versions during unrelated WorkUnits.

If current provider version is deprecated or unsupported:

return:

`EXTERNAL_PROVIDER_VERSION_RISK`

---

# Contract Drift

If current provider behavior differs from documented contract:

record evidence and return:

`EXTERNAL_PROVIDER_CONTRACT_DRIFT`

Do not silently code around undocumented behavior without review.

---

# Production Safety

Production provider configuration must be explicit.

Never:

```text
reuse test API keys in production
point production to sandbox accidentally
point DEV/QA to production without explicit approval
reuse test webhook secrets in production
```

If environment/provider configuration is unsafe:

return:

`EXTERNAL_ENVIRONMENT_CONFIGURATION_RISK`

---

# Provider-Specific Business Side Effects

The skill must classify external operations by side effect.

Suggested conceptual classes:

```text
READ_ONLY
REMOTE_MUTATION
REMOTE_NOTIFICATION
REMOTE_RESOURCE_CREATION
REMOTE_DESTRUCTIVE
```

Examples:

```text
read Google Calendar
→ READ_ONLY

create Google Calendar event
→ REMOTE_RESOURCE_CREATION

send Doppler email
→ REMOTE_NOTIFICATION

delete remote file
→ REMOTE_DESTRUCTIVE
```

This classification should influence:

```text
retry behavior
idempotency analysis
approval requirements
test strategy
production safety
```

---

# Test Strategy

The skill must distinguish test evidence by environment/type.

Possible levels:

```text
MOCKED
LOCAL
PROVIDER_SANDBOX
PROVIDER_TEST
DEV
QA
HML
PRODUCTION
```

Do not report:

```text
integration validated
```

when only mocked behavior was tested.

Return the actual validation scope.

---

# Real Provider Validation

When possible and safe, validate:

```text
authentication
contract
request
response
error handling
timeout behavior
provider environment
mapping
observability
```

Do not execute destructive or production-impacting operations without the required approval.

---

# Security Review

Escalate to `dev-security-analysis` when the integration introduces:

```text
new secrets
OAuth/service accounts
signed webhooks
sensitive data transfer
privileged remote operations
external callbacks
public inbound endpoints
third-party data processors
provider token handling
remote destructive capabilities
```

Return:

`SECURITY_REVIEW_REQUIRED`

when applicable.

---

# DevOps Boundary

Delegate to `dev-devops-implementation` when the external integration requires:

```text
new runtime secrets
new environment variables
egress/network changes
DNS configuration
certificates
proxy configuration
OpenShift configuration
new scheduled runtime jobs
platform-level webhook exposure
```

Return:

`DEVOPS_CHANGE_REQUIRED`

when applicable.

---

# Architecture Boundary

Escalate to `dev-architecture-analysis` when the integration requires:

```text
new message broker
new queueing platform
new gateway
provider failover architecture
multi-provider strategy
sync → async redesign
new shared integration layer
enterprise integration platform
significant cross-system orchestration
```

Return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

configuration.inspect
environment.config.inspect

external.contract.inspect
external.provider.config.inspect
external.client.inspect

tests.run
logs.inspect
```

Depending on provider/mechanism:

```text
http.request.execute
smtp.connection.test
webhook.contract.inspect
oauth.config.inspect
sdk.dependencies.inspect
provider.sandbox.execute
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks include:

- external provider contract consistency
- external environment mapping
- secret externalization
- provider authentication configuration
- timeout configuration
- retry safety
- idempotency safety
- rate-limit handling
- provider error mapping
- webhook signature validation
- webhook replay/idempotency
- provider version compatibility
- production-provider isolation
- external integration observability
- external integration non-regression

The skill must not self-approve official Checks.

If a required Check is unavailable:

return:

`CHECK_GAP`

---

# Result Statuses

Supported result statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

EXTERNAL_PROVIDER_UNRESOLVED
EXTERNAL_PROVIDER_CONTRACT_MISSING
EXTERNAL_PROVIDER_CONTRACT_DRIFT
EXTERNAL_PROVIDER_LIMITS_UNKNOWN
EXTERNAL_PROVIDER_VERSION_RISK

EXISTING_PROVIDER_INTEGRATION_REUSE

EXTERNAL_AUTHENTICATION_UNRESOLVED
EXTERNAL_ENVIRONMENT_MAPPING_UNRESOLVED
EXTERNAL_ENVIRONMENT_CONFIGURATION_RISK

TIMEOUT_POLICY_UNRESOLVED
RETRY_POLICY_UNRESOLVED
IDEMPOTENCY_RISK
WEBHOOK_REPLAY_RISK
EXTERNAL_FAILURE_BEHAVIOR_UNRESOLVED

SECRET_CONFIGURATION_RISK

ARCHITECTURE_REVIEW_REQUIRED
SECURITY_REVIEW_REQUIRED
DEVOPS_CHANGE_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

Return a structured result.

Example:

```yaml
externalIntegrationResult:

  status: COMPLETE

  provider:
    name: Doppler
    providerType: SAAS_PLATFORM
    purpose: transactional-email-delivery

  direction: OUTBOUND

  mechanism:
    type: REST_API
    rationale: EXISTING_PROJECT_DECISION

  strategy:
    type: EXTEND_EXISTING_PROVIDER_ADAPTER
    reusedComponents:
      - doppler-client

  contract:
    source: OFFICIAL_PROVIDER_DOCUMENTATION
    version: ...
    validated: true
    driftDetected: false

  boundary:
    applicationPort: EmailProvider
    adapter: DopplerAdapter
    providerSpecificLeakageDetected: false

  authentication:
    type: API_TOKEN
    externalized: true

  environmentMapping:
    DEV: PROVIDER_TEST
    QA: PROVIDER_TEST
    HML: PROVIDER_TEST
    PRD: PROVIDER_PRODUCTION

  providerLimits:
    rateLimitKnown: true
    quotaKnown: true
    payloadLimitsKnown: true

  reliability:
    timeout:
      configured: true
    retry:
      configured: true
      safe: true
    idempotency:
      evaluated: true
      risk: LOW

  webhooks:
    used: false

  errorMapping:
    implemented: true
    providerDetailsLeaked: false

  observability:
    implemented: true
    sensitiveDataLogged: false

  validation:
    mocked: PASS
    providerSandbox: PASS
    QA: PASS
    production: NOT_EXECUTED

  reviews:
    architectureRequired: false
    securityRequired: true
    devopsRequired: true

  requiredCapabilities:
    - repository.read
    - repository.write
    - external.contract.inspect
    - http.request.execute
    - tests.run

  requiredChecks:
    - external-provider-contract
    - secret-externalization
    - external-environment-mapping
    - retry-safety
    - idempotency-safety
    - external-integration-regression

  risks: []
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

This skill may emit complexity signals to `automatic-consumption`.

It does not choose the final model.

## STANDARD

Use for:

- straightforward provider client implementation
- documented REST/SMTP integration
- simple provider mapping
- existing adapter extension
- ordinary environment configuration
- well-documented webhook integration
- provider contract validation

## REASONING

Consider when:

- multiple provider mechanisms are possible
- SDK vs REST tradeoff requires analysis
- rate limits affect design
- retries/idempotency are non-trivial
- sandbox/production mapping is complex
- provider contract is ambiguous
- webhook replay/security is complex
- legacy provider migration is involved
- provider-specific behavior leaks into the application
- multiple environments behave differently

## PREMIUM

Consider only when:

- provider integration is business-critical
- major security risk exists
- multi-provider/failover design is involved
- provider contract is unstable or contradictory
- large-scale migration affects many systems
- repeated reasoning attempts fail

Premium execution must pass the orchestrator's Human Model Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- provider is unresolved
- provider contract is missing
- provider contract drift exists
- integration mechanism cannot be selected safely
- authentication is unresolved
- environment mapping is unresolved
- provider limits are required but unknown
- retry/idempotency cannot be established
- fallback behavior is undefined
- architecture must change
- security review is required
- DevOps/platform work is required
- a required capability is unavailable
- a required Check is unavailable
- human approval is required

---

# Prohibited Behavior

This skill must not:

- invent external provider contracts
- invent provider limits
- invent provider error semantics
- automatically prefer REST
- automatically prefer SDKs
- spread provider DTOs across unrelated application code
- create duplicate provider integrations without evidence
- hardcode provider credentials
- copy provider credentials across environments
- silently point non-production systems to provider production
- silently point production to provider sandbox
- blindly retry remote mutations
- claim idempotency without evidence
- invent business fallback behavior
- leak external provider errors publicly
- log secrets or tokens
- assume webhook delivery occurs exactly once
- execute destructive provider operations without approval
- redesign application architecture silently
- duplicate OIDC or miBA user-authentication knowledge
- create Tools directly
- self-approve security reviews
- self-approve architecture changes
- self-approve formal Checks
- bypass Policies
- invent missing project/provider context

---

# Evidence Requirements

The result must distinguish:

```text
provider documentation evidence
current-project evidence
existing provider integration evidence
provider sandbox/test evidence
real environment evidence
mocked evidence
assumptions
open decisions
provider limitations
risks
formal reviews required
```

All meaningful decisions must be traceable to one or more of:

- WorkUnit
- Jira / Ficha de Proyecto
- repository code
- existing provider adapter/client
- provider official documentation
- provider contract
- provider environment
- current project configuration
- applicable ADR
- GCBA standard
- test result
- specialized review

---

# Success Criteria

This skill is successful when it:

- identifies the external provider and purpose
- reuses existing integration paths where appropriate
- uses an authoritative provider contract
- selects the integration mechanism using evidence
- isolates provider-specific behavior at the integration boundary
- keeps provider credentials externalized
- explicitly maps GCBA environments to provider environments
- evaluates provider limits
- defines timeout behavior
- defines retry behavior safely
- evaluates idempotency
- handles provider failures without inventing business behavior
- maps provider errors into controlled application errors
- supports inbound webhooks safely when required
- captures provider-specific observability
- distinguishes mocked validation from real provider validation
- detects provider contract/version risk
- preserves application architecture and non-regression
- escalates security/DevOps/architecture needs explicitly
- returns structured evidence to the orchestrator

---

# Example Provider Categories

These examples are conceptual and do not prescribe implementation:

```text
Doppler
→ external email/SaaS provider
→ REST API or documented provider mechanism

SMTP provider
→ external email transport
→ SMTP

Google
→ external platform
→ API / official SDK / service account / OAuth depending on service

Microsoft external service
→ API / official SDK / OAuth/service credentials depending on service
```

The skill must determine the real mechanism from project and provider evidence rather than from these examples.
