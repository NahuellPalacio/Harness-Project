---
name: dev-integration-implementation
description: Use when a WorkUnit integrates a GCBA / DGISIS application with another system — deciding what is consumer and what is provider, which contract governs the interaction, whether an existing integration can be reused, and what failures, side effects and per-environment configuration have to be handled — preserving the architecture, the contracts, the security boundaries and the behaviour already in place. Primary implementation skill of the dev-integration agent: routes to dev-openid-connect, dev-miba, dev-service-integration and dev-external-integration instead of holding their knowledge itself.
---

# Skill: dev-integration-implementation

## Purpose

Implement integration WorkUnits for GCBA applications while preserving existing architecture, contracts, security boundaries, environment configuration, and operational behavior.

This is the **primary implementation skill** of the `dev-integration` agent.

Its responsibility is to coordinate and implement the smallest safe integration change required by the WorkUnit, using specialized integration skills when the problem belongs to a specific integration domain.

This skill does not try to contain all integration knowledge itself.

It determines:

- what is being integrated
- why the integration is required
- which system is consumer and which is provider
- which contract governs the interaction
- whether an existing integration can be reused
- which specialized skill is required
- what capabilities are needed
- what failures and side effects must be handled
- what evidence is required before the WorkUnit can be considered complete

---

## Owner

Primary owner:

`dev-integration`

Related specialized skills:

- `dev-openid-connect`
- `dev-miba`
- `dev-service-integration`
- `dev-external-integration`
- `dev-esb` when the project and available knowledge justify it

Related cross-domain skills:

- `dev-api`
- `dev-backend-implementation`
- `dev-frontend-implementation`
- `dev-data`
- `dev-storage`
- `dev-observability`
- `dev-architecture-analysis`
- `dev-security-analysis`
- `dev-devops-implementation`
- `dev-quality-validation`

---

# Core Principle

The skill must answer:

> What is the safest and smallest integration change required to connect these systems without inventing contracts, duplicating existing capabilities, or breaking the current architecture?

Apply this rule:

> Inspect first, classify second, reuse before creating, delegate specialized concerns, implement only the required integration boundary, and validate the complete interaction.

---

# Responsibility

`dev-integration-implementation` owns the execution of integration WorkUnits.

Typical responsibilities include:

```text
integration discovery
consumer/provider identification
existing integration inspection
contract discovery
integration type classification
integration boundary definition
specialized-skill routing
client/adapter implementation
configuration consumption
error and failure handling
timeout behavior
retry behavior
idempotency requirements
integration-specific observability
environment-aware validation
integration tests
non-regression evidence
```

The skill must not become a generic architecture, API design, security, DevOps, or identity skill.

---

# Integration Domain Classification

Before implementation, classify the integration.

Supported conceptual categories:

```text
IDENTITY
SERVICE_TO_SERVICE
EXTERNAL_SERVICE
INTERNAL_PLATFORM_SERVICE
ESB
EVENT_DRIVEN
FILE_OR_STORAGE
OTHER
```

Possible specialization:

```text
IDENTITY + OIDC
→ dev-openid-connect

IDENTITY + miBA
→ dev-miba

SERVICE_TO_SERVICE
→ dev-service-integration

EXTERNAL_SERVICE
→ dev-external-integration

ESB
→ dev-esb, if available and applicable
```

If the integration type cannot be determined:

return:

`INTEGRATION_TYPE_UNRESOLVED`

---

# Required Context

The skill should receive the smallest context necessary for the WorkUnit.

Expected context may include:

- WorkUnit objective
- Jira issue / HU / Bug / Task
- project / Ficha de Proyecto context
- relevant ADRs
- current repository state
- existing integrations
- existing API clients/adapters
- current provider/consumer contracts
- environment configuration
- secret references
- identity/authentication requirements
- error-handling conventions
- observability conventions
- applicable GCBA rules
- architecture constraints
- required capabilities
- required checks
- previous implementation evidence

The skill must not invent missing contracts or external-system behavior.

---

# Mandatory Workflow

The skill must execute the following sequence.

```text
1. Inspect integration context
2. Identify consumer and provider
3. Classify integration type
4. Search for existing integration / adapter / client
5. Resolve governing contract
6. Select specialized skill when required
7. Define integration execution plan
8. Implement the minimum coherent change
9. Configure failure behavior
10. Configure environment / secrets usage
11. Add operational evidence
12. Validate end-to-end interaction
13. Validate non-regression
14. Return structured result
```

---

# Phase 1 — Inspect Existing Integration Context

Before changing code, inspect:

```text
existing clients
existing adapters
existing gateways
existing service wrappers
existing authentication mechanisms
existing configuration conventions
existing error conventions
existing retry/timeout behavior
existing integration tests
```

Do not create a second integration path when a valid one already exists.

If an existing implementation may be reusable:

return or record:

`EXISTING_INTEGRATION_REUSE`

as the preferred strategy.

---

# Phase 2 — Identify Consumer and Provider

Every integration must explicitly identify:

```text
consumer
provider
direction
trigger
expected result
```

Example:

```yaml
participants:
  consumer: ba-espacios-backend
  provider: notification-service
  direction: OUTBOUND
```

The skill must not proceed with an ambiguous responsibility boundary.

If unclear:

return:

`INTEGRATION_BOUNDARY_UNRESOLVED`

---

# Phase 3 — Resolve the Integration Contract

The integration must be based on an explicit contract.

The contract may already exist in:

- OpenAPI / Swagger
- RAML
- provider documentation
- existing source code
- event schema
- file specification
- identity-provider configuration
- project documentation
- approved integration documentation

The skill must not invent request fields, response fields, endpoints, headers, claims, events, or provider behavior.

If the provider contract is missing:

return:

`INTEGRATION_CONTRACT_MISSING`

If the WorkUnit requires creating or changing an API contract:

delegate to:

`dev-api`

---

# Integration Contract Model

The skill should reason over a structure similar to:

```yaml
integrationContract:

  integrationType: SERVICE_TO_SERVICE

  consumer: system-a
  provider: system-b

  protocol: HTTP

  interaction:
    mode: SYNCHRONOUS
    direction: OUTBOUND

  contractSource:
    type: OPENAPI
    reference: ...

  authentication:
    mechanism: ...

  request:
    mapping: ...

  response:
    mapping: ...

  timeout:
    required: true

  retry:
    required: false

  idempotency:
    required: false

  failureBehavior:
    strategy: ...

  environments:
    - DEV
    - QA
    - HML

  secretsRequired: []

  observability:
    required: true
```

This model is conceptual.

The exact implementation may differ by project/runtime.

---

# Phase 4 — Reuse Before Creating

The skill must apply:

```text
reuse existing integration
        ↓
extend existing integration safely
        ↓
create new integration path only if required
```

Search for:

- existing service client
- existing HTTP client
- existing adapter
- existing gateway
- existing SDK
- existing shared library
- existing ESB route
- existing identity integration
- existing configuration conventions

Do not duplicate a provider client merely because the current WorkUnit uses it from another module.

If reuse is possible:

prefer reuse unless architecture, coupling, security, or compatibility evidence justifies separation.

---

# Phase 5 — Select Specialized Skill

This main skill coordinates specialized knowledge.

## OpenID Connect

If the integration is OpenID Connect:

delegate to:

`dev-openid-connect`

This skill must not duplicate OIDC-specific implementation rules.

---

## miBA

If the integration is miBA:

delegate to:

`dev-miba`

miBA is a separate integration domain and must not be modeled as part of OpenID Connect.

---

## Service-to-Service

If the WorkUnit is a system/service integration:

delegate to:

`dev-service-integration`

when the specialized skill exists and is applicable.

---

## ESB

If the integration requires an Enterprise Service Bus:

delegate to:

`dev-esb`

only when that skill exists and the project context confirms ESB usage.

If ESB is required but the specialized knowledge is unavailable:

return:

`SPECIALIZED_SKILL_REQUIRED`

or:

`MISSING_CONTEXT`

depending on the missing element.

---

# Phase 6 — Integration Execution Plan

Before implementation, produce a small execution plan.

Example:

```yaml
integrationPlan:

  strategy: EXTEND_EXISTING_CLIENT

  affectedComponents:
    - service-a
    - provider-client

  specializedSkills:
    - dev-service-integration

  requiredCapabilities:
    - repository.read
    - repository.write
    - configuration.inspect
    - tests.run

  contractChanges: false

  authenticationChanges: false

  dataModelChanges: false

  infrastructureChanges: false

  securityReviewRequired: false

  architectureReviewRequired: false
```

If the WorkUnit would introduce a major architectural change:

return:

`ARCHITECTURE_REVIEW_REQUIRED`

and delegate to:

`dev-architecture-analysis`

---

# Phase 7 — Implement the Minimum Coherent Change

Implementation should affect only the components required by the integration.

Typical implementation elements may include:

```text
provider client
adapter
mapper
configuration binding
request/response transformation
error mapping
integration service
tests
observability hooks
```

Avoid unrelated refactoring.

Do not redesign the provider or consumer unless the WorkUnit explicitly requires it.

---

# Client / Adapter Boundary

Prefer explicit integration boundaries.

Conceptually:

```text
Application / Domain Logic
        ↓
Integration Port / Service
        ↓
Provider Adapter / Client
        ↓
External or Internal System
```

The exact pattern must follow the existing project architecture.

Do not introduce a new architectural pattern solely because the skill prefers it.

---

# Data Mapping

When provider and consumer models differ, mappings must be explicit.

Do not leak provider-specific DTOs deeply into application/domain logic unless the existing architecture intentionally does so.

The skill should identify:

```text
consumer model
provider model
mapping location
required transformations
lossy transformations
unmapped fields
```

If the mapping changes business meaning:

delegate to:

`dev-data`

or request domain clarification.

---

# Synchronous vs Asynchronous Integration

The skill may implement the interaction mode already approved by architecture.

If the WorkUnit implies changing:

```text
synchronous → asynchronous
request/response → event-driven
direct call → queue/event bus
```

this is an architectural decision.

Return:

`ARCHITECTURE_REVIEW_REQUIRED`

Do not silently change the interaction model.

---

# Timeout Behavior

Every remote synchronous integration must explicitly evaluate timeout behavior.

Do not rely blindly on framework defaults.

The skill should determine:

```text
timeout exists?
timeout is configurable?
timeout aligns with project/platform limits?
failure behavior after timeout?
```

If timeout strategy is undefined for a critical remote dependency:

return:

`TIMEOUT_POLICY_UNRESOLVED`

Timeout values must come from project/platform evidence or approved configuration.

Do not invent arbitrary values.

---

# Retry Behavior

Retries must be intentional.

Do not automatically retry every failed integration.

Evaluate:

```text
operation semantics
idempotency
provider contract
failure type
side effects
existing retry policy
```

Safe conceptual rule:

```text
READ operation
→ retry may be possible

IDEMPOTENT mutation
→ retry may be possible if policy allows

NON-IDEMPOTENT mutation
→ automatic retry requires explicit evidence/policy
```

If retry safety is unclear:

return:

`RETRY_POLICY_UNRESOLVED`

---

# Idempotency

For operations that may be retried or invoked more than once, evaluate idempotency.

The skill must not claim an operation is idempotent without evidence.

Possible sources:

- HTTP semantics
- provider contract
- idempotency key
- business identifier
- application logic
- provider documentation

If duplicate execution may cause business impact:

return:

`IDEMPOTENCY_RISK`

---

# Failure Model

Every integration must define what happens when the dependency fails.

Possible strategies may include:

```text
fail request
return controlled error
fallback
defer processing
retry
partial completion
circuit/open-state behavior already present in project
```

Do not invent fallback behavior.

Fallbacks are business decisions unless explicitly defined.

If failure behavior is not defined:

return:

`DEPENDENCY_FAILURE_BEHAVIOR_UNRESOLVED`

---

# Error Mapping

Provider errors should not leak uncontrolled infrastructure details to application consumers.

The skill should preserve:

```text
provider error
      ↓
integration error mapping
      ↓
application/API error contract
```

If a public API contract must change:

delegate to:

`dev-api`

If sensitive information may be exposed:

delegate to:

`dev-security-analysis`

---

# Authentication and Authorization

Authentication mechanisms belong to their specialized integration domain.

Examples:

```text
OIDC
→ dev-openid-connect

miBA
→ dev-miba
```

For generic service credentials/tokens:

- inspect existing project/provider mechanism
- externalize secrets
- use approved secret injection
- never hardcode credentials

If the authentication mechanism is unclear:

return:

`AUTHENTICATION_MECHANISM_UNRESOLVED`

---

# Secrets

The skill must never:

```text
hardcode credentials
write secrets into source code
log secrets
return secrets in results
copy credentials between environments
include secrets in generated documentation
```

Use the harness-approved SecretStore/runtime injection mechanism.

If violated:

return:

`SECRET_CONFIGURATION_RISK`

---

# Environment Configuration

Integration configuration must remain external to code where required.

Typical environment-specific values include:

```text
base URL
client identifier
timeouts
feature toggles
routing identifiers
credentials references
callback URLs
provider-specific environment values
```

Do not silently reuse DEV values in QA/HML/PRD.

If cross-environment leakage is detected:

return:

`ENVIRONMENT_CONFIGURATION_RISK`

---

# Observability

Integration failures must be diagnosable.

Coordinate with:

`dev-observability`

At minimum, when appropriate, capture non-sensitive evidence such as:

```text
integration name
provider
operation
result
duration
error category
retry count
correlation context if the project already supports it
```

Do not log:

```text
tokens
credentials
secret headers
sensitive payloads
sensitive provider URLs
```

Do not introduce a new observability stack from this skill.

---

# Security Boundary

This skill implements integration behavior.

It does not self-approve high-risk security decisions.

Escalate to:

`dev-security-analysis`

when the WorkUnit includes:

```text
new authentication mechanism
new credentials/secrets
sensitive data exchange
privileged external operation
security-sensitive headers
token handling
new exposure surface
untrusted external provider
authentication-flow modification
```

Return:

`SECURITY_REVIEW_REQUIRED`

when applicable.

---

# DevOps Boundary

The skill may identify required runtime configuration.

It does not own:

```text
platform secret provisioning
OpenShift deployment configuration
network policy
ingress/egress configuration
service mesh policy
platform certificates
production deployment
```

Delegate those concerns to:

`dev-devops-implementation`

If runtime/platform changes are required:

return:

`DEVOPS_CHANGE_REQUIRED`

---

# API Boundary

`dev-integration-implementation` consumes or connects contracts.

`dev-api` owns API contract design.

Use:

```text
dev-api
→ endpoint contract, URI, HTTP semantics, DTO/API validation, public error contract, versioning

dev-integration-implementation
→ provider consumption, adapters, mapping, failure handling, integration execution
```

If a provider API must be redesigned:

delegate to:

`dev-api`

---

# Architecture Boundary

The skill must preserve the approved architecture.

Escalate to `dev-architecture-analysis` when the integration requires:

- new architectural style
- new shared integration platform
- synchronous/asynchronous redesign
- new cross-system orchestration
- major coupling change
- new shared gateway
- new enterprise integration pattern
- new critical infrastructure dependency

Return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Testing

The integration must be validated at the lowest useful levels available.

Possible tests include:

```text
unit tests
mapping tests
client/adapter contract tests
mocked provider tests
integration tests
environment validation
end-to-end validation
non-regression tests
```

Do not claim a real provider interaction succeeded if only a mocked test ran.

Evidence must distinguish:

```text
MOCKED
LOCAL
DEV
QA
HML
PRODUCTION
```

---

# Contract Validation

When possible, validate the implementation against the provider contract.

Examples:

```text
OpenAPI schema
request/response examples
event schema
identity-provider contract
provider documentation
existing compatibility tests
```

If implementation contradicts the known contract:

return:

`INTEGRATION_CONTRACT_MISMATCH`

---

# Non-Regression

When an existing integration is modified, capture and validate the existing behavior that must remain unchanged.

Examples:

```text
existing consumers
existing endpoints
existing provider operations
existing auth paths
existing configuration
existing error behavior
```

If evidence is insufficient:

return:

`BASELINE_MISSING`

or:

`REGRESSION_RISK`

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
database.schema.inspect
database.query.inspect
identity.provider.inspect
storage.inspect
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If a required capability does not exist:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential required Checks include:

- integration contract consistency
- environment configuration isolation
- secret externalization
- timeout configuration
- retry safety
- idempotency safety
- error mapping
- provider/consumer mapping
- integration observability
- integration non-regression
- security review requirement
- architecture review requirement

The skill must not self-approve official Checks.

If a required Check does not exist:

return:

`CHECK_GAP`

---

# Result Statuses

Supported statuses include:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

INTEGRATION_TYPE_UNRESOLVED
INTEGRATION_BOUNDARY_UNRESOLVED
INTEGRATION_CONTRACT_MISSING
INTEGRATION_CONTRACT_MISMATCH

EXISTING_INTEGRATION_REUSE
SPECIALIZED_SKILL_REQUIRED

AUTHENTICATION_MECHANISM_UNRESOLVED
TIMEOUT_POLICY_UNRESOLVED
RETRY_POLICY_UNRESOLVED
IDEMPOTENCY_RISK
DEPENDENCY_FAILURE_BEHAVIOR_UNRESOLVED

SECRET_CONFIGURATION_RISK
ENVIRONMENT_CONFIGURATION_RISK

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
integrationResult:

  status: COMPLETE

  workUnit:
    id: WU-123

  classification:
    integrationType: SERVICE_TO_SERVICE
    interactionMode: SYNCHRONOUS
    direction: OUTBOUND

  participants:
    consumer: system-a
    provider: system-b

  strategy:
    type: EXTEND_EXISTING_INTEGRATION
    reusedComponents:
      - provider-client

  specializedSkills:
    used:
      - dev-service-integration

  contract:
    source: OPENAPI
    reference: ...
    validated: true
    changed: false

  authentication:
    mechanism: EXISTING_SERVICE_TOKEN
    changed: false

  configuration:
    externalized: true
    environmentsValidated:
      - DEV
      - QA

  reliability:
    timeout:
      configured: true
    retry:
      configured: false
    idempotency:
      required: false
    failureBehavior:
      defined: true

  implementation:
    affectedComponents:
      - backend-service
      - provider-client
    completed: true

  observability:
    implemented: true
    sensitiveDataLogged: false

  validation:
    unitTests: PASS
    contractTests: PASS
    integrationTests: PASS
    endToEnd: PASS
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
    - integration-contract
    - secret-externalization
    - integration-regression

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

- extending an existing client
- adding a straightforward provider operation
- implementing an established contract
- simple request/response mappings
- environment configuration changes
- ordinary integration tests

## REASONING

Consider when:

- multiple systems participate
- provider and consumer contracts differ significantly
- failure semantics are ambiguous
- retry/idempotency behavior requires analysis
- multiple authentication mechanisms coexist
- environment behavior diverges
- legacy and new integration paths coexist
- shared adapters are affected
- contract compatibility is unclear

## PREMIUM

Consider only when:

- integration architecture is highly complex
- security impact is high
- shared enterprise integration infrastructure is affected
- multiple critical systems are coupled
- repeated reasoning attempts failed
- a major migration has substantial rollback risk

Premium execution must pass the orchestrator's Human Model Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- integration type is unresolved
- consumer/provider responsibility is unclear
- provider contract is missing
- a specialized skill is required
- architecture must change
- authentication mechanism is unknown
- security review is required
- DevOps/platform changes are required
- retry safety is unclear
- idempotency cannot be proven
- dependency failure behavior is undefined
- environment configuration is unsafe
- a required capability is missing
- a required Check is missing
- human approval is required

---

# Prohibited Behavior

This skill must not:

- invent provider contracts
- invent endpoints
- invent provider fields
- invent authentication mechanisms
- duplicate an existing integration without evidence
- silently redesign APIs
- silently change synchronous integration to asynchronous
- silently introduce a new integration platform
- hardcode secrets
- copy credentials between environments
- blindly retry mutating operations
- claim idempotency without evidence
- invent fallback business behavior
- leak provider infrastructure errors publicly
- log secrets or sensitive tokens
- bypass specialized skills
- duplicate `dev-openid-connect`
- duplicate `dev-miba`
- self-approve security decisions
- self-approve architecture decisions
- provision platform infrastructure directly
- create Tools directly
- create official Checks silently
- bypass Policies
- invent missing project context

---

# Evidence Requirements

The result must distinguish:

- current-project facts
- contract evidence
- provider evidence
- configuration evidence
- implementation evidence
- environment used for validation
- mocked vs real integration evidence
- assumptions
- unresolved decisions
- risks
- formal reviews required

All meaningful decisions must be traceable to one or more of:

- WorkUnit
- Jira / Ficha de Proyecto
- repository code
- existing integration implementation
- provider contract
- project configuration
- applicable ADR
- GCBA standard
- environment evidence
- test result
- specialized skill result

---

# Success Criteria

This skill is successful when it:

- identifies the consumer and provider
- classifies the integration correctly
- discovers and reuses existing integrations when appropriate
- resolves the real provider contract
- delegates specialized identity/integration knowledge correctly
- implements the minimum coherent change
- preserves the approved architecture
- keeps configuration and secrets externalized
- handles timeout/retry/idempotency intentionally
- defines dependency failure behavior
- maps provider errors safely
- provides operational evidence
- validates against the contract
- validates the interaction end-to-end when possible
- preserves non-regression
- reports architecture/security/DevOps needs explicitly
- returns structured evidence to the orchestrator

---

# Sources and Normative Alignment

This skill should remain aligned with:

- current GCBA development standards
- project ADRs
- project/Ficha de Proyecto documentation
- provider contracts
- existing repository architecture
- specialized integration skills

Identity-specific operational knowledge must remain in its specialized skill.

For example:

```text
OpenID Connect
→ dev-openid-connect

miBA
→ dev-miba
```

The primary implementation skill coordinates those concerns without duplicating them.
