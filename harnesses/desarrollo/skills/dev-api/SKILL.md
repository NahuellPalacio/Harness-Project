---
name: dev-api
description: Use when a WorkUnit designs, implements or changes a REST API contract on a GCBA / DGISIS project — routes, request and response shape, status codes, versioning, documentation and API tests — preserving the conventions the project already has instead of inventing a new style. Owned by dev-backend; dev-integration, dev-quality and dev-security read it when they need to reason about a contract.
---

# Skill: dev-api

## Purpose

Design, implement, and modify REST API contracts while preserving existing project conventions, architectural constraints, repository patterns, applicable ADRs, and GCBA development standards.

This skill is primarily used by the `dev-backend` agent.

Its responsibility is to ensure that API changes remain consistent, documented, version-aware, testable, and aligned with GCBA requirements.

---

## Owner

Primary owner:

`dev-backend`

Secondary consumers may include:

- `dev-integration`
- `dev-quality`
- `dev-security`

when they need to inspect or reason about API contracts.

---

## Core Principle

The skill must answer:

> What is the smallest correct API change that satisfies the WorkUnit while preserving the existing API contract, project conventions, and GCBA development rules?

The skill must inspect existing API conventions before creating or modifying endpoints.

It must never invent a new API style when an approved project convention already exists.

---

## Scope

This skill is responsible for:

- REST endpoints
- routes and resource structure
- HTTP method semantics
- request contracts
- response contracts
- JSON payloads
- DTO/API boundaries
- backend request validation
- API error contracts
- API documentation
- controlled API versioning
- breaking-change detection
- API-focused tests
- compatibility with existing API conventions

This skill does not own GCBA identity or integration mechanisms.

Those concerns belong to specialized skills.

---

## Responsibility Boundaries

### `dev-api` owns

- endpoint design
- route design
- HTTP semantics
- request parameters
- query parameters
- request body contracts
- response contracts
- JSON structures
- API DTOs
- backend request validation
- error response semantics
- API documentation
- API versioning impact
- breaking-change detection

### `dev-integration` owns

- miBA / BAID
- OpenID Connect
- Keycloak
- citizen authentication
- institutional authentication
- ESB
- GCBA gateway/integration mechanisms
- system-to-system integration strategy
- identity/token integration flows

### `dev-security` owns

- security assessment
- vulnerability analysis
- authorization/security risk
- abuse scenarios
- security controls beyond normal API implementation

### `dev-architecture-analysis` owns

- architecture selection
- service decomposition
- major service-boundary decisions
- communication architecture changes

### `dev-data` owns

- data modeling
- data boundaries
- database responsibility
- data architecture

---

## Required Context

The skill should receive only the context required for the assigned API WorkUnit.

Expected context may include:

- WorkUnit objective
- relevant Jira issue / HU / Bug / Task
- acceptance criteria
- relevant TaskContext
- architecture analysis
- applicable ADRs
- existing routes
- existing controllers
- existing DTOs/contracts
- existing API documentation
- current versioning strategy
- existing error contract
- relevant tests
- applicable GCBA standards
- applicable policies
- available capabilities
- required checks

The skill must not require the entire repository when targeted inspection is sufficient.

---

## Missing Context Conditions

Return `MISSING_CONTEXT` when reliable API implementation is not possible.

Examples:

- existing route conventions cannot be determined
- current API versioning strategy is unavailable
- API contract is referenced but missing
- expected response format is undefined
- integration/authentication requirements are unknown
- relevant ADRs are unavailable
- acceptance criteria are insufficient

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - api_versioning_strategy
  - existing_error_contract
reason:
  "The requested change modifies an existing public endpoint, but compatibility rules cannot be determined."
```

Do not invent missing API conventions.

---

## API Change Types

The skill must classify the requested change.

Supported types:

- `CREATE`
- `MODIFY`
- `REMOVE`
- `DEPRECATE`
- `CONSUME`

The selected type affects compatibility analysis and required checks.

---

## Implementation Procedure

### Step 1 — Understand the API Requirement

Determine:

- requested behavior
- API change type
- user/system actor
- expected inputs
- expected outputs
- compatibility expectations
- acceptance criteria

Do not start with route design before understanding the actual operation.

---

### Step 2 — Inspect Existing API Conventions

Before implementing, inspect:

- routes
- resource naming
- controller patterns
- HTTP methods
- DTOs
- schemas
- JSON conventions
- error responses
- pagination/filtering patterns
- versioning conventions
- OpenAPI/Swagger/RAML definitions
- tests

Preserve valid existing conventions.

Do not introduce a new route or response style merely because it is preferable in another project.

---

### Step 3 — Identify Resource and Operation

Determine whether the API represents:

- a resource
- a collection
- a state transition
- an action
- a query
- a command

Prefer resource-oriented REST semantics when compatible with the existing project.

Avoid arbitrary RPC-like routes such as:

```text
/doSomething
/getThingsNow
/processEverything
```

unless the existing approved API contract explicitly uses such conventions.

Do not force theoretical REST purity over an established valid project contract.

---

### Step 4 — Define Route and HTTP Semantics

Define:

- route
- HTTP method
- path parameters
- query parameters
- headers
- body presence

The route must follow existing project conventions and applicable GCBA API standards.

Do not invent `/v1`, `/v2`, or any specific URI versioning mechanism unless the project or standard explicitly requires it.

Controlled versioning is required, but the concrete strategy must follow the project contract or an explicit architectural decision.

---

### Step 5 — Define Request Contract

Describe the request boundary.

Possible elements:

```text
Request
├── path parameters
├── query parameters
├── headers
└── body
```

Requirements:

- inputs must be explicit
- required fields must be distinguishable from optional fields
- backend validation must not depend only on frontend validation
- internal implementation models should not leak unnecessarily into the public contract

---

### Step 6 — Define Backend Validation

Validate incoming API data at the backend boundary where appropriate.

Consider:

- required fields
- malformed values
- invalid identifiers
- invalid ranges
- invalid formats
- invalid enum/value constraints
- incompatible parameter combinations

Business rules should remain in the appropriate application/domain layer.

The API boundary may invoke domain/application validation but should not duplicate business logic unnecessarily.

---

### Step 7 — Define Response Contract

Describe the response boundary.

Possible elements:

```text
Response
├── HTTP status
├── headers
└── JSON schema
```

REST services in applicable GCBA architectures must use JSON payloads.

Avoid exposing directly:

- ORM entities
- database entities
- internal persistence models
- internal domain structures

when doing so creates unnecessary coupling between the external API contract and internal implementation.

Use explicit DTO/API contracts where appropriate.

---

### Step 8 — Define Error Behavior

Preserve meaningful HTTP semantics.

Unexpected application failures must not be masked as successful responses.

Example:

```text
Unexpected internal failure
→ HTTP 500
```

Do not return patterns such as:

```text
HTTP 200
{
  "error": "internal failure"
}
```

for unexpected server errors.

API errors must not expose infrastructure details such as:

- server names
- IP addresses
- filesystem paths
- stack traces
- internal infrastructure topology
- sensitive configuration

The exact error envelope should follow existing project conventions.

If no approved error contract exists and one is required, return:

`API_CONTRACT_DECISION_REQUIRED`

---

### Step 9 — Detect Protection / Integration Requirements

If the service requires authentication, token protection, identity integration, or GCBA integration mechanisms:

do not implement those rules independently.

Request the specialized skill:

`dev-integration`

Examples:

```text
Citizen authentication required
→ dev-integration

Institutional authentication required
→ dev-integration

OpenID Connect required
→ dev-integration

Keycloak required
→ dev-integration

miBA / BAID required
→ dev-integration

ESB / GCBA integration mechanism required
→ dev-integration
```

The API skill may declare that protection is required, but the integration mechanism belongs to `dev-integration`.

---

### Step 10 — Implement the API Change

Implement the smallest coherent change required by the WorkUnit.

The implementation must:

- preserve existing API conventions
- preserve architectural boundaries
- follow approved framework conventions
- use backend validation
- avoid unnecessary dependencies
- preserve contract consistency
- preserve maintainability
- update related tests
- update API documentation when the contract changes

---

### Step 11 — Update API Documentation

Any API contract change must update the project's API documentation mechanism.

GCBA-supported service architectures require generated documentation using:

- Swagger / OpenAPI
- or RAML

Preserve the project's existing documentation mechanism.

Do not migrate from Swagger/OpenAPI to RAML, or vice versa, without an explicit decision.

If the API contract changes but documentation cannot be updated, return:

`PARTIAL`

or:

`MISSING_CONTEXT`

depending on the cause.

---

### Step 12 — Analyze Versioning and Compatibility

Determine whether the change is backward compatible.

Examples:

### Usually compatible

- adding an optional field
- adding a new endpoint
- adding a non-breaking optional query parameter

### Potentially breaking

- removing a field
- changing a field type
- renaming a response property
- removing an endpoint
- changing route semantics
- making an optional field mandatory
- changing status-code behavior
- changing request shape incompatibly

If a breaking change is detected, return:

`API_BREAKING_CHANGE`

to the `dev-orchestrator`.

Do not silently modify existing public contracts.

A breaking change may require:

- explicit versioning decision
- ADR
- migration strategy
- consumer coordination
- integration review

---

### Step 13 — Analyze Performance Risk

GCBA platform requirements impose response-time constraints on exposed services.

If the proposed endpoint appears to require a long-running synchronous operation, report:

`PERFORMANCE_RISK`

Do not redesign the architecture automatically.

Potential asynchronous/event-driven redesign belongs to:

`dev-architecture-analysis`

and possibly:

`dev-integration`

---

### Step 14 — Tests

Create or update API-related tests as required.

Possible tests:

- route tests
- controller tests
- request validation tests
- response contract tests
- status-code tests
- error-contract tests
- compatibility tests
- integration tests

Tests executed during implementation are development feedback.

Formal compliance is handled through Checks.

---

### Step 15 — Collect Evidence

Return evidence such as:

- routes changed
- contracts changed
- DTOs added/modified
- validation added
- documentation updated
- versioning impact
- tests executed
- existing API conventions reused
- specialized skills requested
- risks
- assumptions
- unresolved findings

---

## GCBA API Rules

The authoritative source is:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información`

Relevant API rules include, among others:

- a core REST API service layer must be available where applicable
- SOA and microservice services must use REST
- service payloads must use JSON
- service contracts must be formalized
- services must use controlled versioning
- API documentation must be generated using Swagger or RAML
- backend validation must exist independently from frontend validation
- service protection requirements must be respected
- HTTP error semantics must not be masked
- unexpected errors must preserve HTTP 500 semantics
- error responses must not expose infrastructure details
- exposed services must respect platform response-time requirements

The complete standard must not be duplicated inside this skill.

The skill must consume the normative model, policies, and checks resolved by the harness.

---

## Documentation Rules

When the contract changes:

```text
API contract change
        ↓
Documentation update required
```

Preserve the existing project documentation mechanism.

Supported mechanisms include:

- OpenAPI / Swagger
- RAML

Documentation should describe, as applicable:

- route
- HTTP method
- request parameters
- request body
- response body
- status codes
- relevant errors
- contract schemas

---

## Versioning Rules

The skill must preserve controlled API versioning.

It must first inspect the project's existing versioning strategy.

Possible strategies may include:

- URI versioning
- header versioning
- media-type versioning
- another explicit existing strategy

Do not introduce a new versioning mechanism without justification.

If the project has no clear versioning strategy and the change is contract-sensitive, return:

`API_CONTRACT_DECISION_REQUIRED`

---

## Output Contract

Return a structured result.

Example:

```yaml
apiResult:

  status: COMPLETE

  operation:
    type: CREATE

  endpoint:
    method: GET
    route: /existing/project/convention/{id}

  contract:
    request:
      pathParameters:
        - id
      queryParameters: []
      body: null

    response:
      format: JSON
      schema: AppointmentResponse

  validation:
    backend: true

  errorHandling:
    preservesHttpSemantics: true
    infrastructureDetailsExposed: false

  documentation:
    type: OpenAPI
    updated: true

  versioning:
    strategy: existing-project-strategy
    breakingChange: false

  protection:
    required: true
    delegatedTo:
      - dev-integration

  specializedSkillsRequired:
    - dev-integration

  requiredCapabilities:
    - repository.read
    - repository.search
    - repository.write
    - api.routes.inspect
    - tests.run

  requiredChecks:
    - dev-api-rutas
    - api-contract-check
    - unit-tests

  risks: []

  assumptions: []

  evidence: []
```

---

## Result Statuses

Supported result states:

- `COMPLETE`
- `PARTIAL`
- `MISSING_CONTEXT`
- `CAPABILITY_GAP`
- `CHECK_GAP`
- `POLICY_BLOCKED`
- `APPROVAL_REQUIRED`
- `API_BREAKING_CHANGE`
- `API_CONTRACT_DECISION_REQUIRED`
- `ARCHITECTURE_REVIEW_REQUIRED`
- `INTEGRATION_REVIEW_REQUIRED`
- `PERFORMANCE_RISK`
- `FAILED`

The orchestrator must be able to react to these statuses without relying only on free-form prose.

---

## Required Capabilities

Typical capabilities include:

```text
repository.read
repository.search
repository.write
filesystem.read
filesystem.write
api.routes.inspect
api.contract.inspect
documentation.inspect
tests.run
```

Depending on the WorkUnit:

```text
dependency.inspect
configuration.inspect
repository.structure.inspect
```

The skill declares required capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If a required capability is unavailable, return:

`CAPABILITY_GAP`

The skill must not create missing Tools directly.

---

## Checks

The skill may declare required Checks.

Examples:

- `dev-api-rutas`
- API contract checks
- API documentation checks
- backend validation checks
- HTTP error-semantic checks
- dependency checks
- unit tests
- integration tests

The skill may run development tests for feedback.

It must not self-approve formal Checks.

If a required Check does not exist, report:

`CHECK_GAP`

Do not silently create normative Checks.

---

## Policies

The skill must respect all policies resolved for the WorkUnit.

Potential policy concepts include:

- REST API required
- JSON service contract
- controlled service versioning
- API documentation required
- backend validation required
- HTTP errors must not be masked
- infrastructure details must not be exposed
- service protection required
- approved technology required

Policy names are harness implementation details.

The authoritative requirement remains the GCBA standard.

---

## Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

### STANDARD

Default for normal API work.

Examples:

- new endpoint following existing conventions
- DTO change
- request validation
- response-contract update
- API documentation update
- conventional route change

### REASONING

Consider when:

- breaking contract changes are involved
- API versioning is unclear
- multiple consumers may be impacted
- many endpoints are affected
- API conventions conflict
- compatibility trade-offs exist
- significant API refactoring is required

### PREMIUM

Consider only when:

- previous reasoning attempts fail
- contract changes are high-risk and highly ambiguous
- the change has organization-wide integration impact
- architecture/security implications remain unresolved

Premium execution must pass the orchestrator's Human Model Gate.

This skill must never bypass the configured model-consumption policy.

---

## Escalation Conditions

Escalate to the `dev-orchestrator` when:

- required context is missing
- a required capability is missing
- a required Check is missing
- a Policy blocks implementation
- an API breaking change is detected
- a new API contract decision is required
- architecture must change
- integration/authentication behavior is required
- performance risk may require architectural redesign
- another specialist skill is required
- human approval is required

---

## Prohibited Behavior

This skill must not:

- implement miBA logic directly
- implement BAID logic directly
- design OpenID Connect flows
- configure Keycloak
- implement ESB integration rules
- define GCBA identity architecture
- redesign application architecture
- modify database architecture
- invent API versioning conventions
- silently introduce breaking changes
- expose ORM/database entities unnecessarily
- expose infrastructure details in errors
- mask server errors behind HTTP 200
- bypass backend validation
- bypass policies
- self-approve Checks
- add unnecessary dependencies
- invent missing project context
- use the most expensive model by default

---

## Evidence Requirements

The API result should distinguish:

- observed API conventions
- implementation decisions
- contract changes
- assumptions
- compatibility impact
- risks
- tests executed
- formal Checks still required
- specialized skills requested

All meaningful API decisions must be traceable to either:

- the WorkUnit
- project context
- existing API contract
- applicable ADR
- existing repository convention
- GCBA standard/policy

---

## Success Criteria

This skill is successful when it:

- implements the assigned API WorkUnit
- preserves valid API conventions
- uses REST semantics consistently
- preserves JSON contracts
- performs backend request validation
- preserves meaningful HTTP error semantics
- avoids infrastructure leakage
- detects breaking changes
- preserves controlled versioning
- updates Swagger/OpenAPI or RAML documentation
- identifies integration/authentication concerns without duplicating them
- creates or updates appropriate tests
- produces structured evidence
- declares required Checks
- declares capability gaps
- escalates architecture/integration decisions correctly

---

## Source

Authoritative standard:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información - Version 6.3`

Primary references:

- Section 7.1 — Development Principles
- Section 7.2 — System Architectures
- Section 8 — General Integration Requirements
- Section 11 — Non-Functional Requirements

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
