---
name: dev-frontend-implementation
description: Use when a WorkUnit asks for frontend implementation on a GCBA / DGISIS project — views, pages, components, forms, client-side validation, state and loading handling — preserving the architecture already there, the repository conventions, the accessibility requirements and the ADRs in force. Favours the smallest coherent change and delegates the detail: UI and design system to dev-ui, accessibility to dev-accessibility, responsive behaviour to dev-responsive, and any authentication flow to dev-integration. Primary implementation skill of the dev-frontend agent.
---

# Skill: dev-frontend-implementation

## Purpose

Implement frontend work units while preserving the existing architecture, repository conventions, applicable ADRs, design-system rules, project constraints, and GCBA development standards.

This skill is the primary implementation skill for the `dev-frontend` agent.

It must favor the smallest coherent frontend change that satisfies the requirement without introducing unnecessary architectural, visual, or technical complexity.

---

## Owner

Primary owner:

`dev-frontend`

This skill may be requested by the `dev-orchestrator` when a `WorkUnit` requires frontend implementation.

---

## Core Principle

The skill must answer:

> What is the smallest correct frontend change that satisfies this WorkUnit while preserving the existing architecture, design system, repository patterns, accessibility requirements, and GCBA rules?

The skill must not reinterpret the whole task from scratch.

The `dev-orchestrator` already provides the scoped `WorkUnit`.

---

## Scope

This skill is responsible for frontend implementation concerns such as:

- views
- pages
- components
- forms
- client-side validation
- state handling
- loading states
- error states
- navigation
- interaction with backend APIs
- visual consistency
- responsive behavior
- design-system usage
- frontend tests
- integration with specialized frontend skills

This skill coordinates specialized frontend knowledge but must not duplicate it.

Primary specialized frontend skills:

- `dev-ui`
- `dev-accessibility`
- `dev-responsive`

Cross-domain skills may also be required depending on the WorkUnit:

- `dev-api`
- `dev-openid-connect`
- `dev-miba`
- `dev-security-analysis`

`dev-ui` is the frontend UI/design-system skill. Obelisco is its official/default GCBA design-system reference; there is no separate mandatory `dev-obelisco` skill in the V1 model.

---

## Required Context

The skill should receive only the context needed for the assigned frontend `WorkUnit`.

Expected context may include:

- WorkUnit objective
- relevant Jira task / HU / Bug / Task
- acceptance criteria
- relevant TaskContext sections
- architecture analysis
- applicable ADRs
- repository structure
- relevant frontend files
- current frontend framework
- current design system
- existing UI patterns
- existing routing conventions
- current authentication flow
- relevant API contracts
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

- relevant frontend files are unavailable
- current framework cannot be determined
- applicable UI pattern is unknown
- design-system context is missing
- required API contract is unavailable
- authentication behavior is required but undefined
- acceptance criteria are insufficient
- referenced ADRs are unavailable

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - relevant_frontend_files
  - api_contract
reason:
  "The WorkUnit requires a new form connected to an API, but the existing form pattern and API contract are unavailable."
```

Do not invent missing project information.

---

## Implementation Procedure

### Step 1 — Understand the Frontend WorkUnit

Determine:

- exact frontend objective
- expected user-visible behavior
- acceptance criteria
- interaction flow
- implementation boundaries
- out-of-scope concerns
- dependencies on other WorkUnits

Do not broaden the scope without justification.

---

### Step 2 — Inspect the Existing Frontend

Before writing code, inspect the relevant implementation.

Depending on the project, inspect:

- pages
- components
- layouts
- routes
- forms
- validators
- services
- API clients
- state management
- styles
- design-system components
- authentication guards
- tests
- accessibility patterns
- responsive behavior

Reuse valid existing patterns.

Do not introduce a new frontend pattern simply because it is preferred in another project.

Example:

```text
Existing project uses standalone Angular components
→ preserve that pattern.

Existing project uses centralized API services
→ reuse the existing service layer.

Existing project uses Obelisco components
→ do not replace them with arbitrary third-party UI components.
```

---

### Step 3 — Identify Frontend Boundaries

Determine what belongs to the current `WorkUnit`.

Example:

```text
WorkUnit:
Add appointment search screen.

In scope:
- page
- filters
- client-side validation
- API consumption
- loading/error states
- responsive layout
- frontend tests

Out of scope:
- backend implementation
- database changes
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
New or materially changed GCBA user interface
→ dev-ui

Accessibility-sensitive interaction
→ dev-accessibility

Responsive layout
→ dev-responsive

OIDC user-authentication behavior
→ dev-openid-connect through dev-integration

miBA authentication behavior
→ dev-miba through dev-integration

API contract concern
→ dev-api
```

The frontend implementation skill coordinates these concerns.

It must not duplicate their specialized procedures.

---

### Step 5 — Design the Minimal Change

Apply the principle:

> Implement the smallest coherent change that satisfies the requirement and preserves the existing frontend architecture and design system.

Avoid unrelated UI redesigns or refactoring.

If unrelated technical or UX debt is discovered, report it separately.

Example:

```yaml
finding:
  type: technical-debt
  blocking: false
  description: "The existing form duplicates validation logic across components."
```

Do not automatically fix unrelated issues.

---

### Step 6 — Implement

Perform the frontend changes required by the `WorkUnit`.

Implementation must:

- preserve frontend architectural boundaries
- follow project naming conventions
- follow existing component organization
- use the approved frontend framework
- use the GCBA design system where applicable
- preserve responsive behavior
- include client-side validation where required
- integrate with backend contracts through existing patterns
- avoid unnecessary dependencies
- preserve maintainability
- preserve traceability

The skill must not silently redesign the frontend architecture.

---

### Step 7 — User Interaction States

Frontend behavior must explicitly consider relevant interaction states.

Depending on the WorkUnit:

- initial state
- loading state
- success state
- empty state
- validation error
- business error
- API error
- unauthorized state
- unavailable dependency state

Do not leave critical user states undefined when they are part of the requested behavior.

---

### Step 8 — Validation

Client-side validation must be implemented when required by the interaction.

Frontend validation must not be treated as the only validation layer.

GCBA development rules require validation responsibilities to be preserved on the backend as well.

If the required backend validation is missing, report it as a finding or dependency instead of pretending the frontend is sufficient.

---

### Step 9 — API Integration

When the frontend consumes backend services:

- use the existing project API-client/service pattern
- do not hardcode service URLs
- preserve environment-based configuration
- respect existing authentication/token flow
- handle relevant error responses
- avoid duplicating backend business logic in the frontend

Detailed API contract behavior belongs to `dev-api`.

---

### Step 10 — Responsive Behavior

For user-facing web interfaces, preserve responsive behavior across relevant viewport sizes.

Do not implement fixed layouts that break existing responsive conventions.

Detailed responsive rules belong to `dev-responsive`.

---

### Step 11 — UI and Design System

For GCBA web interfaces, resolve UI behavior through `dev-ui`.

Obelisco V2 is the official/default GCBA design-system reference, but the frontend is not limited to a catalog-only interpretation of Obelisco.

Apply this order:

```text
existing valid project pattern
→ documented Obelisco component/pattern
→ Obelisco composition
→ justified custom GCBA UI
```

When custom UI is necessary, it must preserve applicable Obelisco foundations, accessibility, responsive behavior, semantics, and project conventions.

Custom UI must not be represented as an official Obelisco component.

Do not introduce arbitrary visual libraries or replacement component systems without explicit approval.

Detailed UI/design-system behavior belongs to `dev-ui`.

---

### Step 12 — Accessibility

Preserve accessibility behavior and do not regress existing accessibility support.

When the WorkUnit introduces meaningful interaction, semantic structure, forms, navigation, or dynamic UI behavior, request the specialized accessibility skill when needed.

Detailed accessibility implementation belongs to `dev-accessibility`.

---

### Step 13 — Tests

Update or create tests required by the change.

Possible test types:

- component tests
- unit tests
- form-validation tests
- service/API-client tests
- interaction tests
- routing tests
- accessibility tests
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

### Step 14 — Collect Evidence

Return evidence supporting the implementation.

Examples:

- changed files
- created files
- reused components
- reused project patterns
- design-system components used
- tests executed
- test output
- API contracts used
- specialized skills used
- assumptions
- risks
- unresolved findings

The result must be inspectable by the orchestrator, quality agent, and refutador.

---

## GCBA Development Rules

The authoritative source is:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información`

Relevant frontend rules include, among others:

- approved frameworks and technologies must be used
- applications interacting with citizens must use the approved GCBA authentication mechanism
- frontend code must support responsive behavior where applicable
- frontend and backend validation responsibilities must both be respected
- approved GCBA design-system rules must be used where applicable
- environment-specific URLs and configuration must not be hardcoded in application code
- frontend implementations must preserve maintainability and standard development practices

The skill must not hardcode the complete standard.

It must consume the normative model and applicable policies/checks resolved by the harness.

---

## Dependency Rules

Before introducing a new frontend dependency:

1. determine whether it is necessary
2. determine whether the framework or existing project already solves the problem
3. verify compatibility with the approved technology stack
4. verify applicable policy
5. identify required dependency checks

If approval cannot be established:

return:

`POLICY_BLOCKED`

or:

`APPROVAL_REQUIRED`

depending on the applicable policy.

Never add a UI dependency only because it is convenient.

---

## Architecture Relationship

This skill must respect the result of:

`dev-architecture-analysis`

It must not:

- change frontend architectural style
- introduce a new state-management architecture
- replace the design system
- redefine major module boundaries
- change authentication architecture
- change deployment topology

without escalation.

If implementation reveals an architectural conflict, return:

`SCOPE_ESCALATION`

or:

`ARCHITECTURE_REVIEW_REQUIRED`

to the orchestrator.

---

## Output Contract

Return a structured result.

Example:

```yaml
frontendResult:

  status: COMPLETE

  workUnit:
    id: implement-appointment-search

  implementation:
    changedFiles:
      - src/app/appointments/appointment-search.component.ts
      - src/app/appointments/appointment-search.component.html

    createdFiles:
      - src/app/appointments/appointment-search.service.ts

  specializedSkillsUsed:
    - dev-ui
    - dev-responsive
    - dev-api

  decisions:
    - description: >
        Reused the existing filter-form pattern used by the project.
      evidence:
        - src/app/shared/search/

  validation:
    - "Client-side required-field validation added."
    - "Backend validation remains required."

  dependencies:
    added: []
    removed: []

  tests:
    executed:
      - component
      - service
    result: PASS

  assumptions: []

  risks: []

  requiredChecks:
    - dev-accesibilidad-html
    - dev-dependencias
    - frontend-tests

  ui:
    strategy: OBELISCO_COMPOSITION
    customGcbaUi: false

  evidence:
    - "Existing Obelisco form components reused through dev-ui guidance."

  findings: []
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
- `SCOPE_ESCALATION`
- `ARCHITECTURE_REVIEW_REQUIRED`
- `UI_REVIEW_REQUIRED`
- `ACCESSIBILITY_REVIEW_REQUIRED`
- `RESPONSIVE_REVIEW_REQUIRED`
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
frontend.routes.inspect
frontend.components.inspect
api.contract.inspect
configuration.inspect
accessibility.inspect
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

- `dev-accesibilidad-html`
- `dev-dependencias`
- frontend tests
- responsive reflow checks
- approved-technology checks
- API contract checks
- design-system / Obelisco compatibility checks
- custom UI justification checks

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
- approved frontend framework required
- approved package manager
- approved GCBA design system / UI governance
- no hardcoded environment configuration
- no unauthorized authentication mechanism
- no unnecessary third-party UI framework

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

Default for normal frontend implementation.

Examples:

- page or component following existing patterns
- conventional form
- API consumption
- normal client-side validation
- straightforward responsive change
- common interaction behavior

### REASONING

Consider when:

- multiple frontend modules are affected
- interaction behavior is complex
- state management is non-trivial
- accessibility requirements are complex
- significant UI refactoring is required
- existing patterns conflict
- authentication flow changes
- multiple API contracts are involved

### PREMIUM

Consider only when:

- previous reasoning attempts fail
- frontend changes expose major architectural uncertainty
- accessibility/security impact is high and ambiguous
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
- frontend architecture must change
- an ADR appears to require modification
- the WorkUnit scope must expand
- backend changes are required
- a specialist skill is required but unavailable
- human approval is required
- a dependency requires approval
- implementation cannot be completed safely

---

## Prohibited Behavior

This skill must not:

- redesign architecture without escalation
- modify ADRs silently
- choose unapproved technologies
- add unnecessary frontend dependencies
- invent requirements
- implement backend business logic
- duplicate backend validation as the only source of truth
- hardcode environment URLs or secrets
- replace the GCBA design system without approval
- bypass accessibility requirements
- bypass policies
- self-approve Checks
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
- approved design system

---

## Success Criteria

This skill is successful when it:

- implements the assigned frontend WorkUnit
- preserves valid architecture
- follows repository conventions
- uses specialized skills when needed
- uses the approved design system where applicable
- preserves responsive behavior
- preserves accessibility
- respects frontend/backend validation boundaries
- introduces no unnecessary complexity
- respects GCBA policies
- avoids unapproved dependencies
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
- Section 8.2 — Authentication
- Section 11 — Non-Functional Requirements
- Annex II — Approved Development Tools and Versions

UI/design-system operational references:

- https://gcba.github.io/Obelisco-V2/getting-started
- https://gcba.github.io/Obelisco-V2/components/grid
- https://gcba.github.io/Obelisco-V2/patterns
- https://gcba.github.io/Obelisco-V2/docs/Guía_de_adopción_de_Obelisco_v2.pdf

The frontend implementation skill delegates detailed UI rules to `dev-ui`, accessibility behavior to `dev-accessibility`, and responsive behavior to `dev-responsive`.

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
