---
name: dev-architecture-analysis
description: Use when a task may touch the architecture of a GCBA / DGISIS project — picking an architecture for a new system, or judging what a change does to module, service, integration, persistence or deployment boundaries, to the non-functional requirements and to the ADRs already in force. Answers PRESERVE, EXTEND, REFACTOR or ARCHITECTURAL_DECISION_REQUIRED, never silently overrides an ADR, and returns MISSING_CONTEXT instead of inventing what it does not have.
---

# Skill: dev-architecture-analysis

## Purpose

Analyze the architectural impact of a software initiative or change and guide architectural decisions according to the existing project context, applicable ADRs, non-functional requirements, repository structure, and GCBA development standards.

This skill is designed to support both:
- architecture selection for new projects
- architecture impact analysis for existing systems

The skill must prefer preserving a valid existing architecture when the requested change can be implemented without introducing unnecessary structural complexity.

## Owner

Primary owner: `dev-architecture`

This skill may be requested by the `dev-orchestrator` when a task has architectural, cross-cutting, integration, infrastructure, scalability, availability, or maintainability impact.

## Core Principle

The skill must answer:

> What architectural impact does this task introduce, and what is the safest and most appropriate architectural decision within the existing GCBA constraints?

The skill must not assume that every change requires an architectural redesign.

A valid result may be:
- `PRESERVE`
- `EXTEND`
- `REFACTOR`
- `ARCHITECTURAL_DECISION_REQUIRED`

## Operating Modes

### 1. Architecture Selection

Use this mode when:
- the project is new
- there is no established architecture
- the current architecture is explicitly being redesigned
- a new subsystem requires an architectural style decision

The skill may evaluate architecture options supported by GCBA standards, including:
- structured monolith
- modular monolith
- service-oriented architecture
- microservices
- event-driven architecture

The skill must evaluate the real project needs before recommending a distributed architecture.

### 2. Architecture Impact Analysis

Use this mode when:
- an existing system receives a new feature
- an issue changes module boundaries
- a new integration is introduced
- a new datastore is proposed
- deployment topology changes
- non-functional requirements change
- infrastructure responsibilities change
- existing architectural decisions may be affected

The default objective is to determine whether the current architecture can safely support the requested change.

## Required Context

The skill should receive as much of the following context as is available:
- task objective
- Jira issue / HU / Bug / Task
- acceptance criteria
- Project Sheet context
- functional requirements
- non-functional requirements
- existing architecture
- current architecture documentation
- relevant ADRs
- repository structure
- module boundaries
- current technology stack
- current integrations
- deployment model
- infrastructure constraints
- current data storage approach
- applicable GCBA standards
- relevant policies
- relevant repository evidence

The skill must never invent missing architectural context.

If critical information is unavailable, return a structured missing-context result instead of making unsupported assumptions.

## Missing Context Conditions

Return `MISSING_CONTEXT` when information required for a reliable architectural decision is unavailable.

Examples:
- current architecture cannot be determined
- repository structure is unavailable
- relevant ADRs are referenced but missing
- required non-functional requirements are unknown
- integration dependencies cannot be identified
- deployment topology is required but unavailable

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - current_architecture
  - relevant_adrs
reason:
  "The requested change may modify module boundaries, but the current architectural constraints are unavailable."
```

## Analysis Procedure

### Step 1 — Understand the Change

Determine:
- what is being requested
- why it is required
- whether the change is local or cross-cutting
- which system responsibilities are affected

Do not infer architecture from the technology name alone.

Example: Spring Boot does not automatically imply microservices.

### Step 2 — Identify the Current Architecture

Determine, using project evidence:
- architecture style
- module boundaries
- service boundaries
- deployment boundaries
- integration boundaries
- persistence boundaries
- relevant infrastructure constraints

Possible architecture classifications include:
- structured monolith
- modular monolith
- SOA
- microservices
- event-driven
- hybrid / mixed

If the architecture cannot be reliably classified, explicitly state the uncertainty.

### Step 3 — Identify Affected Components

Identify the components and responsibilities affected by the change.

Examples:
- backend
- frontend
- API
- authentication
- persistence
- integration
- messaging
- infrastructure
- deployment
- observability
- security
- external services

### Step 4 — Identify Architectural Constraints

Gather constraints from:
- existing ADRs
- Project Sheet
- GCBA standards
- repository conventions
- deployment platform
- approved technologies
- existing integrations
- security requirements
- project-specific decisions

Existing ADRs must be treated as active architectural constraints unless they are explicitly superseded.

The skill must not silently override an ADR.

### Step 5 — Evaluate Non-Functional Requirements

Evaluate architectural impact against relevant non-functional requirements.

Consider:
- scalability
- availability
- performance
- concurrency
- resilience
- maintainability
- interoperability
- deployability
- observability
- security
- operational complexity

The skill must distinguish functional need from architectural need.

A new feature alone does not justify a more complex architecture.

### Step 6 — Evaluate Integration Impact

Determine:
- whether new systems must communicate
- whether the change introduces coupling
- whether synchronous or asynchronous interaction is required
- whether an existing GCBA integration mechanism applies
- whether the change affects service contracts
- whether versioning is required
- whether an integration crosses existing boundaries

Delegate implementation details to integration-related skills when needed.

### Step 7 — Compare Against GCBA Architectural Rules

Evaluate the proposed or existing architecture against applicable GCBA development rules.

The authoritative source is:
`ES0901 - Estándar de Desarrollo - ASI`

Primary references for this skill:
- Section 5 — Deliverables / Architecture Document
- Section 6 — Infrastructure Definitions
- Section 7.1 — Development Principles
- Section 7.2 — System Architectures
- Section 11 — Non-Functional Requirements

The skill must preserve traceability to the applicable source rule whenever a recommendation depends on a GCBA standard.

## Architecture Evaluation Guidance

### Structured Monolith

Appropriate only when the project does not require significant independent scaling, independent deployment, distributed integration, or strong domain decoupling.

Evaluate:
- transaction volume
- concurrency
- availability
- integration needs
- independent deployment needs
- modular maintainability

### Modular Monolith

Consider when:
- a single deployable unit is acceptable
- internal separation by domain or responsibility is valuable
- distributed-system operational cost is not justified
- maintainability and modular boundaries are required

### SOA

Consider when:
- shared business capabilities exist
- integration with multiple GCBA systems is required
- formal service contracts are needed
- scalability and interoperability are relevant
- service autonomy is justified

### Microservices

Consider only when the system actually requires:
- independent service deployment
- independent scaling
- strong service autonomy
- high availability
- clear service boundaries
- operational maturity
- distributed-system complexity

Do not recommend microservices because they are perceived as more modern.

### Event-Driven Architecture

Consider when the problem requires:
- asynchronous processing
- event-based workflows
- loose coupling
- high scalability
- event traceability
- reaction to business events
- resilient processing

Do not introduce event-driven architecture for simple synchronous flows without a concrete requirement.

## Decision Rules

The skill should prefer the lowest-complexity architecture that safely satisfies:
- functional requirements
- non-functional requirements
- existing architectural constraints
- GCBA standards

Principle:

> Do not introduce architectural complexity without a concrete requirement that justifies it.

## Output Contract

Return a structured result.

Example:

```yaml
architectureAnalysis:

  status: COMPLETE

  mode: impact-analysis

  currentArchitecture:
    type: modular-monolith
    confidence: high

  changeImpact:
    level: medium

  affectedComponents:
    - appointments-api
    - appointments-domain

  affectedDomains:
    - backend
    - integration

  applicableStandards:
    - source: ES0901
      version: "6.3"
      section: "7.2"
    - source: ES0901
      version: "6.3"
      section: "11"

  constraints:
    - ADR-004
    - approved-technologies-only

  findings:
    - Existing modular boundaries can support the requested change.
    - Independent deployment is not required.
    - No new infrastructure component is necessary.

  recommendation:
    decision: PRESERVE
    rationale: >
      The requirement can be implemented within the existing module
      without introducing distributed-system complexity.

  adr:
    required: false

  risks:
    - "The new integration may increase coupling if implemented directly."

  requiredSkills:
    - dev-api
    - dev-integration

  requiredCapabilities:
    - repository.read
    - repository.search

  requiredChecks:
    - dev-api-rutas
    - dev-dependencias
```

## Allowed Recommendations

### PRESERVE
The current architecture safely supports the requested change.

### EXTEND
The current architecture remains valid, but a new module, boundary, integration, component, or architectural element should be added.

### REFACTOR
The requested change exposes an architectural problem that should be corrected while preserving the general architectural style.

### ARCHITECTURAL_DECISION_REQUIRED
The change introduces a new architectural decision with meaningful trade-offs.

An ADR should be created or an existing ADR should be updated/superseded through the proper process.

## ADR Rules

The skill must determine whether an ADR is required.

An ADR should be recommended when the task introduces or changes decisions such as:
- architecture style
- service boundaries
- module boundaries
- communication pattern
- persistence strategy
- messaging model
- deployment topology
- integration strategy
- major technology choice
- security architecture
- infrastructure architecture

Do not create an ADR for trivial implementation details.

The skill may recommend ADR creation, but it must not silently modify or override an existing ADR.

## Related Skills

This skill may request additional specialist skills when detailed implementation knowledge is required.

Examples:
- `dev-api`
- `dev-data`
- `dev-persistence`
- `dev-authentication`
- `dev-integration`
- `dev-storage`
- `dev-observability`
- `dev-health-checks`
- `dev-deployment`
- `dev-security`

The architecture skill defines the architectural direction.

The specialized skill defines how to implement the specific concern.

## Required Capabilities

Depending on the task, this skill may require capabilities such as:
- `repository.read`
- `repository.search`
- `repository.structure.inspect`
- `documentation.read`
- `adr.read`
- `task-context.read`
- `dependency.inspect`
- `architecture.inspect`

The skill must declare required capabilities.

It must not directly invent or implement missing tools.

If a capability is missing, return:
`CAPABILITY_GAP`

to the `dev-orchestrator`.

The orchestrator will decide whether to invoke `dev-tool-builder`.

## Checks

This skill may declare checks that must be executed after implementation.

It does not execute or self-approve those checks.

Potential checks include:
- `dev-api-rutas`
- `dev-dependencias`
- `dev-infra-en-codigo`
- architecture-boundary checks
- approved-technology checks
- integration checks
- security checks

The exact checks depend on the task and the normative matrix.

## Policies

The skill must respect all applicable policies.

Examples:
- `approved-technologies-only`
- `no-unapproved-architecture`
- `no-direct-integration-when-gcba-standard-service-applies`
- `no-local-persistent-storage`
- `external-configuration-required`

Policies prevent invalid planning.

Checks verify the resulting implementation.

## Model Routing Metadata

This skill may provide complexity signals to the orchestrator.

It does not select the final model.

Suggested routing hints:

### STANDARD
Use when:
- analyzing a localized architectural impact
- checking an existing boundary
- determining whether a change fits the current architecture
- reviewing a small integration impact

### REASONING
Use when:
- selecting architecture for a new project
- comparing architectural alternatives
- evaluating cross-domain changes
- analyzing significant NFR impact
- evaluating service decomposition
- analyzing distributed architecture

### PREMIUM
Consider only when:
- the decision is highly ambiguous
- the architectural impact is organization-wide or high-risk
- several major architectural alternatives remain valid
- the decision has significant security or operational impact
- previous reasoning attempts were insufficient

Premium execution must follow the orchestrator's human approval policy.

The skill must never bypass `automatic-consumption` or the Human Model Gate.

## Escalation Conditions

Escalate back to the `dev-orchestrator` when:
- required context is missing
- a required capability is missing
- an applicable policy blocks the proposed direction
- a new ADR is required
- architecture alternatives have significant unresolved trade-offs
- specialist analysis is required
- human approval is required
- the change exceeds the scope of the current WorkUnit

## Prohibited Behavior

This skill must not:
- modify application code directly
- create infrastructure directly
- deploy applications
- execute migrations
- choose unapproved technologies
- ignore existing ADRs
- silently override architectural decisions
- approve its own architecture
- bypass policies
- bypass required checks
- bypass human approval
- assume microservices are preferable
- infer architecture solely from the programming language or framework
- invent missing project context
- consume the entire repository when targeted inspection is sufficient

## Evidence Requirements

Architectural recommendations must be supported by evidence.

Possible evidence:
- TaskContext
- Project Sheet
- existing ADRs
- repository structure
- configuration files
- architecture documentation
- ES0901 rule references
- non-functional requirements
- integration definitions

The result should distinguish:
- observed facts
- inferred architecture
- assumptions
- recommendations

## Success Criteria

This skill is successful when it:
- correctly identifies the current architectural context
- evaluates the real impact of the requested change
- avoids unnecessary architectural complexity
- preserves existing valid decisions
- identifies applicable GCBA constraints
- identifies when an ADR is required
- produces a structured architecture analysis
- requests specialist skills when necessary
- declares required capabilities
- declares required checks
- preserves traceability to source standards
- never invents missing architectural information

## Source

Authoritative standard:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información - Version 6.3`

Primary source sections:
- Section 5 — Deliverables
- Section 6 — Infrastructure Definitions
- Section 7.1 — Development Principles
- Section 7.2 — System Architectures
- Section 11 — Non-Functional Requirements

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
