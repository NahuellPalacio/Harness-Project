---
name: dev-service-integration
description: Use when a GCBA / DGISIS application integrates with another system of the GCBA ecosystem — one backend consuming another, backend-to-backend REST, approved internal gRPC, machine-to-machine service tokens, internal callbacks and synchronous dependencies between internal services. It is the internal counterpart of dev-external-integration: here both sides belong to the organism and the contract can be agreed, not just consumed. Owned by dev-integration.
---

# Skill: dev-service-integration

## Purpose

Plan and implement **service-to-service integrations between systems controlled by, operated by, or functionally belonging to the GCBA ecosystem**, while preserving existing contracts, architecture, security boundaries, operational behavior, and non-regression.

This skill belongs to the `dev-integration` agent.

It covers internal system-to-system communication such as:

- one GCBA backend consuming another GCBA backend
- one internal service calling another service
- backend-to-backend REST integrations
- internal gRPC integrations when already approved by project architecture
- internal service tokens / machine-to-machine authentication
- internal synchronous service dependencies
- internal service callbacks
- internal platform services when they are part of the GCBA application ecosystem

This skill is **not** the external-provider skill.

Use:

```text
dev-service-integration
→ internal / GCBA service-to-service integration

dev-external-integration
→ third-party / external provider integration
```

---

## Owner

Primary owner:

`dev-integration`

Primary implementation entry point:

`dev-integration-implementation`

Related skills:

- `dev-api`
- `dev-backend-implementation`
- `dev-data`
- `dev-observability`
- `dev-security-analysis`
- `dev-devops-implementation`
- `dev-architecture-analysis`
- `dev-esb` when applicable
- `dev-openid-connect` when user identity is part of the problem
- `dev-miba` when miBA is part of the problem

---

# Core Principle

The skill must answer:

> How can one GCBA system consume another GCBA service safely, using the correct contract and existing integration path, without duplicating clients, inventing APIs, or increasing coupling unnecessarily?

Apply this rule:

> Reuse the existing internal integration path when valid, consume explicit contracts, keep machine-to-machine concerns separate from user identity, and escalate architecture changes instead of introducing them silently.

---

# Scope

This skill owns:

```text
internal service discovery
consumer/provider identification
internal service contract consumption
internal client / adapter implementation
internal service authentication consumption
request/response mapping
timeouts
retries
idempotency
dependency failure behavior
internal error mapping
internal service observability
environment endpoint mapping
integration tests
non-regression
```

---

# Out of Scope

This skill does not own:

```text
third-party / SaaS provider integration
external provider contracts
user login flows
OpenID Connect user authentication
miBA authentication
API contract design
major architecture redesign
ESB-specific implementation
platform provisioning
security approval
business fallback definition
```

Use:

```text
dev-external-integration
→ external providers such as Doppler, Google, SMTP/SaaS

dev-api
→ API contract design and versioning

dev-openid-connect
→ user authentication with OIDC

dev-miba
→ miBA-specific integration

dev-esb
→ ESB-specific integration when applicable

dev-architecture-analysis
→ architecture changes

dev-security-analysis
→ security review

dev-devops-implementation
→ runtime / platform configuration
```

---

# Internal Service Definition

Treat an integration as `SERVICE_TO_SERVICE` when:

- both sides are systems/services inside the GCBA application ecosystem or under organizational control
- the interaction is application-to-application or backend-to-backend
- the consumer is not authenticating an end user
- the provider exposes a service contract consumed by another GCBA component

The fact that two systems belong to GCBA does not imply they are the same application, repository, team, or deployment unit.

---

# Mandatory Workflow

The skill must execute this sequence:

```text
1. Identify consumer and provider
2. Confirm SERVICE_TO_SERVICE classification
3. Inspect existing integration/client
4. Resolve authoritative service contract
5. Identify authentication mechanism
6. Resolve environment endpoints
7. Define mapping and integration boundary
8. Evaluate timeout/retry/idempotency
9. Define dependency failure behavior
10. Implement the minimum coherent change
11. Add observability
12. Validate contract
13. Validate integration in available environments
14. Validate non-regression
15. Return structured evidence
```

---

# Phase 1 — Identify Consumer and Provider

The skill must explicitly determine:

```text
consumer system
provider system
direction
operation
business purpose
criticality
```

Example:

```yaml
participants:
  consumer: sistema-a-backend
  provider: sistema-b-api
  direction: OUTBOUND
  purpose: consultar-datos-del-ciudadano
```

If the responsibility boundary is unclear:

return:

`INTEGRATION_BOUNDARY_UNRESOLVED`

---

# Phase 2 — Confirm Classification

Expected classification:

```text
SERVICE_TO_SERVICE
```

If the provider is actually external to the GCBA ecosystem or controlled by a third party:

delegate to:

`dev-external-integration`

If the integration is ESB-mediated and ESB-specific knowledge is required:

delegate to:

`dev-esb`

If the integration changes the architecture from synchronous to asynchronous or introduces a broker/event model:

return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Phase 3 — Inspect Existing Integration

Before creating code, search for:

```text
existing service client
existing adapter
existing gateway
existing shared library
existing HTTP/gRPC client
existing service token handling
existing configuration
existing error mapping
existing tests
existing observability
```

Apply:

```text
reuse
  ↓
extend
  ↓
create
```

Do not create a second client for the same internal provider without evidence.

If reuse is possible:

record:

`EXISTING_SERVICE_INTEGRATION_REUSE`

---

# Phase 4 — Resolve the Service Contract

The integration must be based on an explicit contract.

Possible sources:

```text
OpenAPI / Swagger
RAML
gRPC proto
approved interface documentation
Ficha de Proyecto
existing implementation
provider repository
versioned schema
```

The skill must not invent:

```text
endpoint
method
request field
response field
header
error
version
authentication requirement
```

If the contract does not exist or cannot be proven:

return:

`SERVICE_CONTRACT_MISSING`

If the contract must be created or modified:

delegate to:

`dev-api`

---

# Contract Compatibility

Before implementation, determine whether the consumer is compatible with the provider contract.

Inspect:

```text
contract version
required fields
optional fields
response shape
error shape
breaking changes
deprecations
```

If current consumer/provider expectations do not match:

return:

`SERVICE_CONTRACT_MISMATCH`

Do not silently compensate for breaking contract drift without evidence.

---

# Service Authentication

This skill may handle **machine-to-machine authentication consumption**.

Examples:

```text
service token
API key for internal service
mTLS configuration already defined by project
signed service request
internal client credentials
```

This is not user identity.

Use:

```text
machine-to-machine service authentication
→ dev-service-integration

user identity / login
→ dev-openid-connect or dev-miba
```

The skill must inspect the existing approved mechanism.

Do not invent a new authentication mechanism.

If unclear:

return:

`SERVICE_AUTHENTICATION_UNRESOLVED`

---

# Token Protection

When the internal service requires token protection, the skill must verify that the consumer uses the approved project/provider mechanism.

It must not:

```text
hardcode service tokens
log service tokens
return tokens in results
reuse credentials across environments without approval
```

If secrets handling is unsafe:

return:

`SECRET_CONFIGURATION_RISK`

---

# Environment Endpoint Mapping

The skill must explicitly resolve provider endpoints per environment.

Example:

```yaml
environmentMapping:
  DEV: https://provider-dev...
  QA: https://provider-qa...
  HML: https://provider-hml...
  PRD: https://provider...
```

Do not assume every provider exposes all environments.

Do not silently point lower environments to production.

If the environment mapping is unclear:

return:

`SERVICE_ENVIRONMENT_MAPPING_UNRESOLVED`

---

# Integration Boundary

Follow the current project architecture.

Conceptually:

```text
Application / Domain Logic
        ↓
Internal Service Port / Integration Service
        ↓
Provider Client / Adapter
        ↓
GCBA Provider Service
```

This is a conceptual boundary, not a mandatory design pattern.

Do not introduce new abstractions when the project already has a valid integration convention.

---

# Data Mapping

When consumer and provider models differ:

```text
consumer model
      ↓
mapping
      ↓
provider contract model
```

The skill must identify:

```text
renamed fields
type conversions
optional/required differences
identifier conversions
lossy transformations
defaults
```

If the mapping changes business meaning or source-of-truth semantics:

delegate to:

`dev-data`

---

# Synchronous Interaction

This skill primarily owns the implementation of an already-approved synchronous service-to-service interaction.

Typical mechanisms:

```text
REST / HTTP
gRPC
internal RPC mechanism already present in project
```

It must not independently redesign the interaction to asynchronous messaging.

If the WorkUnit requires:

```text
queue
event bus
broker
EDA
async orchestration
```

return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Timeout

Every remote synchronous call must explicitly evaluate timeout behavior.

Inspect:

```text
existing client timeout
provider expected response time
platform limits
operation criticality
failure behavior
```

Do not rely blindly on framework defaults.

Do not invent arbitrary timeout values.

If unresolved:

return:

`TIMEOUT_POLICY_UNRESOLVED`

---

# Retry

Retries must be intentional.

Evaluate:

```text
operation semantics
HTTP/gRPC error type
idempotency
provider behavior
side effects
existing project policy
```

Do not blindly retry:

```text
all errors
all POST operations
all mutations
```

If retry safety is unclear:

return:

`RETRY_POLICY_UNRESOLVED`

---

# Idempotency

Evaluate duplicate execution when the operation can be retried or invoked more than once.

Possible evidence:

```text
idempotent provider operation
business key
request identifier
idempotency token/key
safe read semantics
provider contract
```

If duplicate execution may create business impact:

return:

`IDEMPOTENCY_RISK`

---

# Dependency Failure Behavior

Every internal dependency must define what happens when the provider is unavailable.

Possible behaviors may include:

```text
fail request
controlled error
defer processing
fallback already defined by business
partial result already defined by business
```

The skill must not invent fallback behavior.

If undefined:

return:

`DEPENDENCY_FAILURE_BEHAVIOR_UNRESOLVED`

---

# Error Mapping

Provider errors should be mapped into controlled internal/application errors.

Expected boundary:

```text
provider error
      ↓
internal service client
      ↓
integration error
      ↓
application / API behavior
```

Do not leak:

```text
stack traces
internal provider URLs
infrastructure details
tokens
sensitive provider payload
```

If public API behavior changes:

delegate to:

`dev-api`

---

# Internal Error Categories

Where useful, map provider failures into stable categories such as:

```text
AUTHENTICATION
AUTHORIZATION
VALIDATION
NOT_FOUND
CONFLICT
TIMEOUT
UNAVAILABLE
CONTRACT_ERROR
REMOTE_BUSINESS_REJECTION
UNKNOWN_SERVICE_ERROR
```

The mapping must follow actual provider behavior.

Do not invent semantics.

---

# Observability

Coordinate with:

`dev-observability`

The integration should produce non-sensitive operational evidence when appropriate:

```text
provider service
operation
duration
result
error category
retry count
environment
request/correlation identifier if already supported
```

Do not log:

```text
tokens
credentials
secret headers
sensitive payload
personal data unless explicitly allowed
```

---

# Health and Dependency Semantics

Do not automatically make service liveness depend on a secondary service.

If the provider is a critical dependency for readiness, coordinate with:

`dev-observability`

and:

`dev-devops-implementation`

The exact health/readiness behavior must follow the project's approved health model.

---

# Service Versioning

Inspect provider API/service versioning.

Do not silently move the consumer to another major version.

If the current version is deprecated or incompatible:

return:

`SERVICE_VERSION_RISK`

If migration requires contract redesign:

delegate to:

`dev-api`

and possibly:

`dev-architecture-analysis`

---

# ESB Boundary

If the current GCBA integration must go through an ESB:

```text
dev-service-integration
→ detects the requirement and consumer/provider contract

dev-esb
→ owns ESB-specific implementation/procedure
```

If ESB-specific knowledge is required but the skill is unavailable:

return:

`SPECIALIZED_SKILL_REQUIRED`

Do not bypass the ESB merely because a direct endpoint is technically reachable.

---

# Security Review

Escalate to:

`dev-security-analysis`

when the integration introduces or changes:

```text
service credentials
privileged service access
sensitive data exchange
token validation
mTLS/certificate behavior
new internal exposure
authorization behavior
security-sensitive headers
```

Return:

`SECURITY_REVIEW_REQUIRED`

when applicable.

---

# DevOps Boundary

Delegate to:

`dev-devops-implementation`

for:

```text
new environment variables
secret provisioning
network/egress configuration
DNS/service discovery configuration
certificates
OpenShift configuration
platform routing
service mesh changes
deployment configuration
```

Return:

`DEVOPS_CHANGE_REQUIRED`

when applicable.

---

# Architecture Boundary

Escalate to:

`dev-architecture-analysis`

when the WorkUnit requires:

```text
new integration style
new gateway
new broker
new shared orchestration layer
sync → async redesign
new enterprise integration platform
major coupling change
cross-system transaction redesign
```

Return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Testing

The skill should validate at the useful levels available.

Possible evidence:

```text
unit tests
mapping tests
client tests
contract tests
mocked provider tests
DEV integration test
QA integration test
HML integration test
end-to-end test
non-regression test
```

Evidence must distinguish:

```text
MOCKED
LOCAL
DEV
QA
HML
PRD
```

Do not claim the provider was validated when only a mock was executed.

---

# Non-Regression

When extending an existing service integration, validate behavior required by current consumers.

Inspect:

```text
existing operations
existing contract version
existing authentication
existing timeout/retry behavior
existing error mapping
existing environment configuration
```

If no usable baseline exists:

return:

`BASELINE_MISSING`

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

configuration.inspect
environment.config.inspect

api.contract.inspect
api.routes.inspect

integration.client.inspect
integration.adapter.inspect
integration.contract.inspect

tests.run
logs.inspect
```

Depending on the WorkUnit:

```text
http.request.execute
grpc.contract.inspect
service.discovery.inspect
database.query.inspect
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

- internal service contract consistency
- service authentication configuration
- environment endpoint isolation
- secret externalization
- timeout configuration
- retry safety
- idempotency safety
- error mapping
- service version compatibility
- integration observability
- service-to-service non-regression
- security review requirement

The skill must not self-approve official Checks.

If unavailable:

return:

`CHECK_GAP`

---

# Result Statuses

Supported statuses include:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

INTEGRATION_BOUNDARY_UNRESOLVED
SERVICE_CONTRACT_MISSING
SERVICE_CONTRACT_MISMATCH
SERVICE_AUTHENTICATION_UNRESOLVED
SERVICE_ENVIRONMENT_MAPPING_UNRESOLVED
SERVICE_VERSION_RISK

EXISTING_SERVICE_INTEGRATION_REUSE
SPECIALIZED_SKILL_REQUIRED

TIMEOUT_POLICY_UNRESOLVED
RETRY_POLICY_UNRESOLVED
IDEMPOTENCY_RISK
DEPENDENCY_FAILURE_BEHAVIOR_UNRESOLVED

SECRET_CONFIGURATION_RISK
BASELINE_MISSING
REGRESSION_RISK

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
serviceIntegrationResult:

  status: COMPLETE

  classification:
    integrationType: SERVICE_TO_SERVICE
    interactionMode: SYNCHRONOUS
    direction: OUTBOUND

  participants:
    consumer: sistema-a
    provider: sistema-b

  purpose: consultar-informacion

  strategy:
    type: EXTEND_EXISTING_CLIENT
    reusedComponents:
      - sistema-b-client

  contract:
    source: OPENAPI
    version: v1
    validated: true
    mismatchDetected: false

  authentication:
    type: SERVICE_TOKEN
    configured: true
    externalized: true

  environments:
    DEV:
      endpointResolved: true
    QA:
      endpointResolved: true
    HML:
      endpointResolved: true
    PRD:
      endpointResolved: true

  reliability:
    timeout:
      configured: true

    retry:
      configured: false

    idempotency:
      evaluated: true
      risk: LOW

    dependencyFailure:
      defined: true

  mapping:
    explicit: true
    businessSemanticChange: false

  observability:
    implemented: true
    sensitiveDataLogged: false

  validation:
    unitTests: PASS
    contractTests: PASS
    DEV: PASS
    QA: PASS
    HML: NOT_EXECUTED
    PRD: NOT_EXECUTED
    nonRegression: PASS

  reviews:
    architectureRequired: false
    securityRequired: false
    devopsRequired: false

  requiredCapabilities:
    - repository.read
    - repository.write
    - integration.contract.inspect
    - tests.run

  requiredChecks:
    - service-contract
    - service-authentication
    - secret-externalization
    - retry-safety
    - service-integration-regression

  risks: []
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

This skill may emit complexity signals to `automatic-consumption`.

It does not select the final model.

## STANDARD

Use for:

- consuming an established internal API
- extending an existing service client
- simple request/response mappings
- straightforward environment configuration
- ordinary contract tests
- well-defined service-token usage

## REASONING

Consider when:

- multiple internal services participate
- contracts differ significantly
- version compatibility is unclear
- retry/idempotency behavior is non-trivial
- legacy and new integration paths coexist
- environment behavior diverges
- authorization behavior is complex
- shared integration clients are affected

## PREMIUM

Consider only when:

- integration affects critical shared GCBA services
- security risk is high
- architecture is unusually complex
- cross-system migration has large rollback impact
- repeated reasoning attempts fail

Premium execution must pass the orchestrator's Human Model Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- consumer/provider boundary is unclear
- service contract is missing
- contract mismatch exists
- service authentication is unresolved
- environment mapping is unresolved
- ESB-specific work is required
- timeout/retry/idempotency cannot be resolved
- dependency failure behavior is undefined
- architecture must change
- security review is required
- DevOps work is required
- a required capability is unavailable
- a required Check is unavailable
- human approval is required

---

# Prohibited Behavior

This skill must not:

- treat an external SaaS/provider as an internal service
- invent service contracts
- invent endpoints
- invent fields or headers
- invent authentication mechanisms
- bypass an existing approved ESB path
- create duplicate internal service clients without evidence
- silently change contract versions
- silently change sync integration to async
- hardcode service credentials
- copy credentials across environments
- point lower environments to PRD without explicit approval
- blindly retry mutating operations
- claim idempotency without evidence
- invent business fallback behavior
- leak provider infrastructure details publicly
- log tokens or credentials
- duplicate OIDC or miBA user-authentication logic
- self-approve security decisions
- self-approve architecture decisions
- provision platform infrastructure directly
- create Tools directly
- self-approve formal Checks
- bypass Policies
- invent missing project context

---

# Evidence Requirements

The result must distinguish:

```text
current-project evidence
provider-service contract evidence
existing client/adapter evidence
environment evidence
mocked evidence
real service integration evidence
assumptions
open decisions
risks
formal reviews required
```

All meaningful decisions must be traceable to one or more of:

- WorkUnit
- Jira / Ficha de Proyecto
- repository code
- existing internal client/adapter
- provider service contract
- project configuration
- applicable ADR
- GCBA standard
- environment evidence
- test result
- specialized skill result

---

# Success Criteria

This skill is successful when it:

- correctly classifies the WorkUnit as `SERVICE_TO_SERVICE`
- identifies consumer and provider
- reuses existing internal clients/adapters where appropriate
- consumes an explicit service contract
- preserves API ownership boundaries
- keeps machine-to-machine authentication separate from user identity
- externalizes service credentials
- resolves environment endpoints explicitly
- maps consumer/provider models intentionally
- evaluates timeout, retry, and idempotency
- defines dependency failure behavior
- maps provider errors safely
- preserves service version compatibility
- coordinates ESB when required
- produces operational evidence
- distinguishes mocked from real integration tests
- validates non-regression
- escalates architecture/security/DevOps needs explicitly
- returns structured evidence to the orchestrator
