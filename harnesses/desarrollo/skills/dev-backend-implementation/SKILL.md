---
name: dev-backend-implementation
description: Use when a WorkUnit asks for backend implementation on a GCBA / DGISIS project — application logic, services, handlers, controllers, backend validation, DTOs, repository usage, error handling and backend tests — preserving the architecture already there, the repository conventions and the ADRs in force. Favours the smallest coherent change, coordinates the specialised backend skills instead of duplicating them, and returns MISSING_CONTEXT rather than reinterpreting the task from scratch.
---

# Skill: dev-backend-implementation

## Purpose

Implement backend work units while preserving the existing architecture, repository conventions, applicable ADRs, project constraints, and GCBA development standards.

This skill is the primary implementation skill for the `dev-backend` agent.

It must favor the smallest coherent backend change that satisfies the requirement without introducing unnecessary architectural or technical complexity.

---

## Owner

Primary owner:

`dev-backend`

This skill may be requested by the `dev-orchestrator` when a `WorkUnit` requires backend implementation.

---

## Core Principle

The skill must answer:

> What is the smallest correct backend change that satisfies this WorkUnit while preserving the existing architecture, repository patterns, and GCBA rules?

The skill must not reinterpret the whole task from scratch.

The `dev-orchestrator` already provides the scoped `WorkUnit`.

---

## Scope

This skill is responsible for backend implementation concerns such as:

- application logic
- services
- handlers
- controllers
- backend validation
- DTOs
- domain/application boundaries
- repository usage
- backend configuration usage
- error handling
- backend tests
- integration with specialized backend skills

This skill coordinates specialized backend knowledge but must not duplicate it.

The specialized skills it coordinates:

- `dev-api`
- `dev-data`
- `dev-persistence`
- `dev-storage`
- `dev-observability`

---

## Required Context

The skill should receive only the context needed for the assigned backend `WorkUnit`.

Expected context may include:

- WorkUnit objective
- relevant Jira task / HU / Bug / Task
- acceptance criteria
- relevant TaskContext sections
- architecture analysis
- applicable ADRs
- repository structure
- relevant backend files
- current framework and runtime
- project conventions
- existing backend patterns
- applicable GCBA standards
- applicable policies
- assigned skills
- required checks
- available capabilities

The skill must not require the complete project context when targeted context is sufficient.

---

## Missing Context Conditions

Return `MISSING_CONTEXT` when reliable implementation is not possible.

Examples:

- required backend files are unavailable
- framework cannot be determined
- relevant architecture constraints are missing
- referenced ADRs are unavailable
- acceptance criteria are insufficient
- a required integration contract is missing
- persistence behavior is required but undefined

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - relevant_backend_files
  - architecture_constraints
reason:
  "The WorkUnit requires changing application behavior, but the current backend pattern cannot be determined."
```

Do not invent missing project information.

---

## Implementation Procedure

### Step 1 — Understand the Backend WorkUnit

Determine:

- exact backend objective
- expected behavior
- acceptance criteria
- implementation boundaries
- out-of-scope concerns
- dependencies on other WorkUnits

Do not broaden the scope without justification.

---

### Step 2 — Inspect the Existing Implementation

Before writing code, inspect the relevant existing implementation.

Depending on the project, inspect:

- controllers
- endpoints
- handlers
- services
- use cases
- repositories
- DTOs
- entities
- domain models
- validators
- configuration
- dependency declarations
- tests
- error handling
- logging patterns

Reuse valid existing patterns.

Do not impose a new pattern simply because it is preferred in another project.

Example:

```text
Existing project uses CQRS
→ preserve Query / Command / Handler patterns.

Existing project uses layered architecture
→ preserve Controller → Service → Repository boundaries.
```

---

### Step 3 — Identify Backend Boundaries

Determine what belongs to the current WorkUnit.

Example:

```text
WorkUnit:
Implement appointment query.

In scope:
- API endpoint
- application query
- data access
- backend tests

Out of scope:
- frontend changes
- deployment redesign
- architecture migration
```

If implementation requires changes outside the assigned scope, return:

`SCOPE_ESCALATION`

to the `dev-orchestrator`.

---

### Step 4 — Resolve Specialized Skills

Determine which specialized skills are required.

Examples:

```text
New REST endpoint
→ dev-api

Persistence change
→ dev-data / dev-persistence

Authentication requirement
(miBA / BAID, OpenID Connect, Keycloak, institutional or citizen authentication)
→ escalate to dev-orchestrator: it belongs to the dev-integration agent, not to backend

External integration
(ESB / system integration, external or internal services)
→ escalate to dev-orchestrator: it belongs to the dev-integration agent, not to backend

Persistent file handling
→ dev-storage

Logging / health / operational behavior
→ dev-observability
```

The backend implementation skill coordinates these concerns.

It must not duplicate their specialized procedures.

---

### Step 5 — Design the Minimal Change

Apply the principle:

> Implement the smallest coherent change that satisfies the requirement and preserves the existing architecture.

Avoid unrelated refactoring.

If unrelated technical debt is discovered, report it separately.

Example:

```yaml
finding:
  type: technical-debt
  blocking: false
  description: "..."
```

Do not automatically fix unrelated issues.

---

### Step 6 — Implement

Perform the backend changes required by the WorkUnit.

Implementation must:

- preserve architectural boundaries
- follow project naming conventions
- follow existing code organization
- use the approved framework
- avoid unnecessary dependencies
- keep business logic in the application/domain layer
- avoid business logic in the database
- preserve maintainability
- preserve traceability

The skill must not silently redesign the architecture.

---

### Step 7 — Validation and Error Handling

Backend input and behavior must be validated appropriately.

Consider:

- invalid input
- missing resources
- conflicts
- domain validation
- external dependency failures
- unexpected failures

Detailed API error-contract behavior belongs to `dev-api`.

Detailed security behavior belongs to the applicable security/authentication skill.

---

### Step 8 — Tests

Update or create tests required by the change.

Possible test types:

- unit tests
- service tests
- handler tests
- repository tests
- API tests
- integration tests

Tests executed during implementation are development feedback.

Formal compliance remains the responsibility of required Checks.

Distinction:

```text
tests.run
→ development feedback Tool

required Check
→ formal validation
```

---

### Step 9 — Collect Evidence

Return evidence supporting the implementation.

Examples:

- changed files
- created files
- reused patterns
- tests executed
- test output
- repository evidence
- dependency changes
- specialized skills used
- relevant standard rules
- assumptions
- risks

The result must be inspectable by the orchestrator, quality agent, and refutador.

---

## GCBA Development Rules

The authoritative source is:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información`

Relevant backend rules include, among others:

- approved frameworks and technologies must be used
- Node.js projects must use NPM as the approved package manager
- standard design patterns and consistent coding style must be respected
- applications must expose a core REST API layer where applicable
- validation must also exist on the backend
- additional components/dependencies must be validated
- business logic must not be implemented in the database layer
- unit tests are required
- environment-specific configuration must remain outside application code
- logging must follow the applicable technology standard

The skill must not hardcode the complete standard.

It must consume the normative model and applicable policies/checks resolved by the harness.

---

## Dependency Rules

Before introducing a new dependency:

1. determine whether it is necessary
2. determine whether existing project/framework capabilities already solve the problem
3. verify compatibility with the approved technology stack
4. verify applicable policy
5. identify required dependency checks

If approval cannot be established:

return:

`POLICY_BLOCKED`

or:

`APPROVAL_REQUIRED`

depending on the applicable policy.

Never add a dependency only because it is convenient.

---

## Business Logic and Data

Business rules must remain in the appropriate application/domain layer.

Do not implement business logic using:

- stored procedures
- database triggers
- database functions
- database-side business rules

unless an explicit approved exception exists.

Detailed persistence design belongs to:

- `dev-data`
- `dev-persistence`

The backend agent remains responsible for integrating the resulting implementation into the WorkUnit.

---

## Architecture Relationship

This skill must respect the result of:

`dev-architecture-analysis`

It must not:

- migrate architecture
- change architectural style
- redefine module boundaries
- split services
- merge services
- change deployment topology

without escalation.

If the implementation reveals an architectural conflict, return:

`SCOPE_ESCALATION`

or:

`ARCHITECTURE_REVIEW_REQUIRED`

to the orchestrator.

---

## Output Contract

Return a structured result.

Example:

```yaml
backendResult:

  status: COMPLETE

  workUnit:
    id: implement-turn-query

  implementation:
    changedFiles:
      - src/application/queries/GetAppointmentsQuery.ts
      - src/api/controllers/AppointmentsController.ts

    createdFiles:
      - src/application/queries/GetAppointmentsHandler.ts

  specializedSkillsUsed:
    - dev-api
    - dev-data

  decisions:
    - description: >
        Reused the existing query handler pattern.
      evidence:
        - src/application/queries/

  validation:
    - "Input validation was added at the application boundary."

  dependencies:
    added: []
    removed: []

  tests:
    executed:
      - unit
    result: PASS

  assumptions: []

  risks: []

  requiredChecks:
    - dev-api-rutas
    - dev-dependencias
    - unit-tests

  evidence:
    - "Existing CQRS pattern found in src/application/queries/."

  findings: []
```

---

## Result Statuses

Supported result states:

- `COMPLETE`
- `PARTIAL`
- `MISSING_CONTEXT`
- `CAPABILITY_GAP`
- `POLICY_BLOCKED`
- `APPROVAL_REQUIRED`
- `SCOPE_ESCALATION`
- `ARCHITECTURE_REVIEW_REQUIRED`
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
dependency.inspect
tests.run
```

Depending on the WorkUnit:

```text
database.schema.inspect
api.routes.inspect
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

- `dev-dependencias`
- `dev-api-rutas`
- unit tests
- coverage checks
- architecture-boundary checks
- security checks
- approved-technology checks

The skill may run development tests for feedback.

It must not self-approve formal Checks.

If a required Check does not exist, report:

`CHECK_GAP`

Do not silently create normative Checks.

---

## Policies

The skill must respect all policies resolved for the WorkUnit.

Examples:

- approved technologies only
- approved framework required
- approved package manager
- no database business logic
- no unapproved dependency
- external configuration required
- no local persistent storage

Policy behavior:

```text
Policy
→ prevents invalid action

Check
→ verifies resulting implementation
```

The skill must never bypass a Policy.

---

## Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

Suggested routing:

### STANDARD

Default for normal backend implementation.

Examples:

- endpoint following existing patterns
- CRUD
- service change
- DTO change
- conventional validation
- normal test implementation

### REASONING

Consider when:

- multiple backend modules are affected
- domain logic is complex
- legacy code has unclear patterns
- significant refactoring is required
- concurrency is involved
- complex integration behavior exists
- repository patterns conflict
- implementation requires resolving meaningful trade-offs

### PREMIUM

Consider only when:

- previous reasoning attempts fail
- backend changes expose major architectural uncertainty
- security/operational risk is high
- the task becomes unusually complex

Premium execution must pass the orchestrator's Human Model Gate.

This skill must never bypass the configured model-consumption policy.

---

## Escalation Conditions

Escalate to the `dev-orchestrator` when:

- required context is missing
- a required capability is missing
- a required Check is missing
- a Policy blocks implementation
- architecture must change
- an ADR appears to require modification
- the WorkUnit scope must expand
- another specialist is required
- human approval is required
- a dependency requires approval
- implementation cannot be completed safely

---

## Prohibited Behavior

This skill must not:

- redesign architecture without escalation
- modify ADRs silently
- choose unapproved technologies
- add unnecessary dependencies
- invent requirements
- implement frontend changes
- change deployment architecture
- bypass policies
- self-approve Checks
- move business logic into the database
- modify unrelated files because it seems convenient
- expand WorkUnit scope without escalation
- invent missing project context
- use the most expensive model by default
- expose secrets or credentials

---

## Evidence Requirements

The implementation result should distinguish:

- observed repository facts
- implementation decisions
- assumptions
- risks
- unresolved findings
- tests executed
- formal Checks still required

All meaningful implementation decisions must be traceable to either:

- the WorkUnit
- project context
- existing architecture
- existing repository pattern
- applicable ADR
- GCBA standard/policy

---

## Success Criteria

This skill is successful when it:

- implements the assigned backend WorkUnit
- preserves valid architecture
- follows repository conventions
- uses specialized skills when needed
- introduces no unnecessary complexity
- respects GCBA policies
- avoids unapproved dependencies
- keeps business logic out of the database
- creates or updates appropriate tests
- produces structured evidence
- declares required Checks
- declares capability gaps
- escalates scope/architecture issues correctly
- does not modify unrelated domains

---

## Source

Authoritative standard:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información - Version 6.3`

Primary references:

- Section 7.1 — Development Principles
- Section 7.2 — System Architectures
- Section 9 — Development Methodology and Continuous Integration
- Section 11 — Non-Functional Requirements
- Annex I — Version Control Repository
- Annex II — Approved Development Tools and Versions

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
