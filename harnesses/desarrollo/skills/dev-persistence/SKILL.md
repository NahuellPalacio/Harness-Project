---
name: dev-persistence
description: Use when a WorkUnit — or a dev-data result — has to be persisted on a GCBA / DGISIS project: entity mapping, repositories and data access, migrations and schema evolution, transaction boundaries and database configuration, on the stack and the framework the project already approved. Keeps business logic out of the database layer and never bypasses the framework. Owned by dev-backend; dev-data, dev-architecture, dev-quality and dev-devops read it when they need to inspect the implementation.
---

# Skill: dev-persistence

## Purpose

Implement persistence changes defined by a WorkUnit and/or `dev-data` result using the project's approved persistence stack, framework conventions, migration mechanism, transaction strategy, and GCBA development rules.

This skill is primarily used by the `dev-backend` agent.

Its responsibility is to convert an already-understood data requirement into a safe, versioned, maintainable persistence implementation without moving business logic into the database layer or bypassing the project's framework.

---

## Owner

Primary owner:

`dev-backend`

Secondary consumers may include:

- `dev-data`
- `dev-architecture`
- `dev-quality`
- `dev-devops`

when they need to inspect persistence implementation, schema evolution, transaction boundaries, or database configuration behavior.

---

## Core Principle

The skill must answer:

> How should the approved data-model change be persisted in this project using its existing framework, ORM/data-access conventions, migration mechanism, and transaction boundaries while preserving GCBA rules?

The skill must distinguish:

```text
Data Requirement
≠
Persistence Implementation
```

`dev-data` determines what the model needs.

`dev-persistence` determines how that model is implemented physically in the current project.

---

## Scope

This skill is responsible for:

- persistence-stack inspection
- ORM/data-access framework usage
- entity/model mappings
- persistence mappings
- repository/data-access implementation
- schema evolution
- migration implementation
- migration ordering/versioning
- transaction implementation
- transaction boundaries
- persistence configuration usage
- database connection configuration inspection
- persistence-focused tests
- initial-data migration/seeding mechanism when explicitly required
- detecting database-side business logic
- detecting direct low-level database access that bypasses the approved framework

This skill does not choose the application data model or database architecture independently.

---

## Responsibility Boundaries

### `dev-persistence` owns

- mapping approved data concepts to persistence structures
- ORM mappings
- repository/data-access implementation
- migration implementation
- schema evolution
- transaction implementation
- persistence-framework conventions
- database configuration consumption
- persistence-focused testing
- detection of persistence anti-patterns

### `dev-data` owns

- data concepts
- data ownership
- source of truth
- conceptual relationships
- integrity requirements
- transactional requirements
- relational vs document-oriented need
- data-model decisions

### `dev-architecture-analysis` owns

- database technology changes
- major persistence architecture changes
- datastore topology changes
- cross-service persistence architecture
- event-sourcing decisions
- major transaction-boundary redesign

### `dev-devops` owns

- database infrastructure provisioning
- secret/configuration platform setup
- environment provisioning
- deployment-time infrastructure changes
- operational database resources

### `dev-security` owns

- deep database security assessment
- credential/security-control review
- vulnerability analysis
- privilege/security risk assessment beyond normal implementation checks

---

## Required Context

The skill should receive only the context required for the assigned persistence WorkUnit.

Expected context may include:

- WorkUnit objective
- `dev-data` result
- relevant Jira issue / HU / Bug / Task
- acceptance criteria
- relevant TaskContext
- current architecture
- applicable ADRs
- current database technology
- existing schema
- existing entities/models
- existing ORM/data-access patterns
- repository/data-access conventions
- current migration mechanism
- transaction conventions
- persistence tests
- dependency declarations
- externalized configuration conventions
- applicable GCBA standards
- applicable policies
- available capabilities
- required checks

The skill must not require the entire repository when targeted inspection is sufficient.

---

## Missing Context Conditions

Return `MISSING_CONTEXT` when reliable persistence implementation is not possible.

Examples:

- the current persistence stack cannot be determined
- the migration mechanism is unknown
- the target data-model change is undefined
- the existing schema is unavailable
- transaction requirements are referenced but unavailable
- database technology cannot be determined
- relevant ADRs are unavailable
- persistence conventions conflict and no approved pattern can be identified

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - migration_mechanism
  - existing_schema
reason:
  "The WorkUnit requires a schema change, but the project's approved migration mechanism and current schema cannot be determined."
```

Do not invent persistence conventions.

---

## Persistence Procedure

### Step 1 — Understand the Approved Data Change

Start from the assigned WorkUnit and, when available, the `dev-data` result.

Determine:

- concepts affected
- schema impact
- integrity requirements
- transactional requirements
- data ownership constraints
- compatibility expectations

Do not redefine the domain/data model unless a contradiction is discovered.

If the data model itself is unclear, request:

`dev-data`

---

### Step 2 — Inspect the Existing Persistence Stack

Before modifying persistence code, inspect:

- framework
- ORM/data-access layer
- database engine
- entity/model mappings
- repository/data-access patterns
- migration mechanism
- transaction mechanism
- connection/configuration approach
- persistence tests
- dependency declarations

Examples of stack evidence may include:

```text
Spring Boot
Hibernate ORM
JPA
Flyway
Oracle
```

or:

```text
NestJS
TypeORM
approved relational database
```

The skill must preserve the project's approved stack.

---

## Framework-First Persistence

GCBA development rules require development through approved frameworks and allow low-level database components only when used indirectly through the corresponding framework, such as database connectors used by an ORM.

Therefore:

```text
Approved Framework / ORM
        ↓
Persistence Access
        ↓
Database Connector
```

is preferred over:

```text
Application Code
        ↓
Direct Low-Level Driver Access
```

If direct low-level access is detected without an approved reason:

return:

`DIRECT_DATABASE_ACCESS_REVIEW_REQUIRED`

Do not bypass the project's ORM/framework because a direct driver appears simpler.

---

## Step 3 — Inspect Existing Mapping Conventions

Determine how the project maps application concepts to persistence structures.

Inspect:

- entity classes
- table mappings
- field mappings
- relationship mappings
- naming conventions
- nullability conventions
- identifiers
- generated values
- enum/value mappings
- timestamps
- audit fields

Preserve existing valid conventions.

Do not introduce a different mapping strategy without justification.

---

## Step 4 — Implement Persistence Mapping

Translate the approved data-model change into the project's persistence representation.

Possible changes include:

- adding a mapped field
- adding a mapped relationship
- adding a new persistence entity
- modifying constraints
- changing an existing mapping

The skill must avoid leaking persistence concerns unnecessarily into domain/application logic.

---

## Repository / Data-Access Rules

The skill must preserve the existing project's valid data-access pattern.

If the project uses repositories:

```text
Existing Repository Pattern
→ preserve it
```

If the framework uses another approved abstraction:

```text
Existing Approved Data-Access Pattern
→ preserve it
```

GCBA does not require a specific Repository Pattern in every application.

Do not introduce a repository abstraction solely because it is preferred in another codebase.

---

## Step 5 — Determine Schema Evolution Requirement

If the persistence change affects the schema:

mark:

`SCHEMA_CHANGE_REQUIRED`

Determine the concrete changes required, such as:

- add column
- add table
- add relationship
- add/remove constraint
- modify type
- modify nullability
- remove obsolete structure

Do not execute uncontrolled schema changes directly against an environment.

---

## Step 6 — Use the Approved Migration Mechanism

GCBA requires the use of framework/project migration mechanisms to version database structure and avoid unmanaged database-change execution.

The skill must inspect and preserve the project's existing approved migration mechanism.

Examples may include technologies already established in the project or normative model, such as:

- Flyway
- Laravel migration tooling / Artisan
- framework-native migration mechanisms
- other approved migration managers

Do not introduce a new migration tool without approval.

### Normative Interpretation Note

ES0901 states that database-structure versioning must use migration managers available within the chosen framework and says to avoid scripts. The same standard also references approved persistence stacks that include Flyway and requires automated mechanisms for initial data loading.

Operationally, this skill must therefore:

- avoid ad hoc/manual schema execution outside the approved migration process
- preserve the project's approved migration manager
- treat migration artifacts managed by that approved mechanism as part of the versioned migration process
- never assume that an arbitrary standalone SQL script is acceptable merely because it changes the schema

If the project/standard interpretation remains unclear:

return:

`MIGRATION_POLICY_REVIEW_REQUIRED`

---

## Migration Requirements

A migration must, where applicable:

- be versioned
- be stored in the repository
- follow project naming/order conventions
- represent only the required schema change
- be reproducible across environments
- avoid environment-specific hardcoding
- preserve compatibility requirements
- avoid embedding application business logic

If migration ordering conflicts or cannot be determined:

return:

`MIGRATION_CONFLICT`

---

## Initial Data / Seeding

When the WorkUnit explicitly requires initial/reference data:

use the approved automated mechanism already established by the project/framework.

Do not require a human to execute ad hoc production scripts.

Examples may include:

- migrations
- seeders
- framework-native initialization mechanisms

The data itself must still respect ownership and business requirements defined elsewhere.

If the initial-data requirement is conceptually unclear:

request:

`dev-data`

---

## Step 7 — Implement Transaction Boundaries

If `dev-data` or architecture context identifies transactional requirements:

implement them using the project's approved framework mechanism.

Example:

```text
dev-data:
Appointment creation + availability reservation
must remain atomic.

dev-persistence:
Preserve the existing application transaction boundary
using the project's framework transaction mechanism.
```

The skill must inspect where transactions are currently controlled.

Do not move transaction responsibility into database-side business procedures unless explicitly approved and consistent with the standard.

---

## Transaction Rules

The skill should evaluate:

- atomicity requirements
- transaction scope
- rollback behavior
- interaction with repositories/data access
- nested/propagated transaction conventions when already used
- cross-system boundaries

If the required transaction crosses independent services or systems:

return:

`ARCHITECTURE_REVIEW_REQUIRED`

or:

`INTEGRATION_REVIEW_REQUIRED`

Do not invent distributed-transaction architecture.

---

## Step 8 — Detect Database Business Logic

GCBA development rules prohibit placing business logic in the database layer.

Detect business behavior implemented using:

- stored procedures
- triggers
- database functions
- database workflows
- database-side domain rules

If detected:

return:

`BUSINESS_LOGIC_IN_DATABASE`

and associate the applicable Policy/Check.

Example:

```text
Trigger:
When Appointment becomes APPROVED,
calculate citizen eligibility.

→ BUSINESS_LOGIC_IN_DATABASE
```

Technical integrity constraints are not automatically business logic.

Examples that may be valid persistence concerns:

- PRIMARY KEY
- FOREIGN KEY
- UNIQUE
- NOT NULL

The skill must distinguish integrity from domain behavior.

---

## Step 9 — Preserve Externalized Configuration

GCBA requires environment-dependent configuration, including database configuration, to remain outside application code.

The persistence implementation must not hardcode:

- database hosts
- environment URLs
- credentials
- passwords
- environment-specific connection strings
- secret values

The skill should preserve the project's existing external configuration mechanism.

If deployment/platform configuration changes are required:

request:

`dev-devops`

If credentials or secrets appear in code:

return:

`SECRET_EXPOSURE_RISK`

---

## Step 10 — Evaluate Database Technology Compatibility

The skill must not select or replace a database engine independently.

If the current database technology is established and approved:

preserve it.

If the WorkUnit appears to require:

- changing database engine
- adding a second datastore
- introducing document storage
- changing persistence topology

return:

`DATABASE_TECHNOLOGY_REVIEW_REQUIRED`

and request:

`dev-architecture-analysis`

plus `dev-data` when appropriate.

---

## Step 11 — Evaluate Physical Schema Optimization

The skill may inspect physical schema concerns when directly relevant to the WorkUnit.

Examples:

- index requirements
- relationship efficiency
- excessive query cost
- missing constraints
- obvious N+1 persistence behavior
- inefficient fetch strategy

Do not add indexes or redesign storage speculatively.

If significant performance redesign is required:

return:

`PERFORMANCE_REVIEW_REQUIRED`

and escalate to the orchestrator.

---

## Step 12 — Tests

Create or update persistence-focused tests when required.

Possible tests:

- repository tests
- ORM mapping tests
- migration tests
- transaction tests
- rollback tests
- persistence integration tests
- schema compatibility tests

Tests executed during implementation are development feedback.

Formal compliance remains the responsibility of required Checks.

---

## Step 13 — Collect Evidence

Return evidence such as:

- persistence stack detected
- mappings changed
- repositories/data-access components changed
- migrations created/modified
- transaction boundaries used
- configuration mechanism preserved
- tests executed
- database-side logic findings
- compatibility risks
- assumptions
- specialized skills requested

---

## GCBA Persistence Rules

The authoritative source is:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información`

Relevant persistence rules include, among others:

- approved frameworks must be used
- low-level database connectors may only be used indirectly through the approved framework, for example through an ORM
- business logic must not be implemented in the database layer
- maintainability, traceability, portability, layered architecture, and decoupling must be preserved
- environment-specific database configuration must remain outside application code
- unit tests are required
- database structure must be versioned using approved framework/project migration mechanisms
- repository-delivered software must include schema/migrations/scripts required by the project
- automated migration/seeding mechanisms must be used where required instead of uncontrolled manual execution
- approved persistence technologies and versions must come from the normative model

The complete standard must not be duplicated inside this skill.

The skill must consume the normative model, policies, and checks resolved by the harness.

---

## Output Contract

Return a structured result.

Example:

```yaml
persistenceResult:

  status: COMPLETE

  persistenceStack:
    framework: Spring Boot
    orm: Hibernate
    specification: JPA
    migrationTool: Flyway
    database: Oracle

  modelChanges:
    - concept: Appointment
      operation: MODIFY

  mappings:
    - field: cancelledAt
      type: timestamp
      nullable: true

  dataAccess:
    pattern: existing-project-pattern
    modified:
      - AppointmentRepository

  migrations:
    required: true
    mechanism: Flyway
    created:
      - V23__add_cancelled_at_to_appointment.sql

  transactions:
    required: false
    mechanism: existing-project-mechanism

  configuration:
    externalized: true
    secretsInCode: false

  businessLogicInDatabase:
    detected: false

  specializedSkillsRequired: []

  requiredCapabilities:
    - repository.read
    - repository.search
    - repository.write
    - database.schema.inspect
    - persistence.mapping.inspect
    - migration.inspect
    - tests.run

  requiredChecks:
    - no-db-business-logic
    - migration-mechanism
    - persistence-tests

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
- `SCHEMA_CHANGE_REQUIRED`
- `MIGRATION_POLICY_REVIEW_REQUIRED`
- `MIGRATION_CONFLICT`
- `DIRECT_DATABASE_ACCESS_REVIEW_REQUIRED`
- `BUSINESS_LOGIC_IN_DATABASE`
- `DATABASE_TECHNOLOGY_REVIEW_REQUIRED`
- `ARCHITECTURE_REVIEW_REQUIRED`
- `INTEGRATION_REVIEW_REQUIRED`
- `PERFORMANCE_REVIEW_REQUIRED`
- `SECRET_EXPOSURE_RISK`
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
database.schema.inspect
database.metadata.inspect
persistence.mapping.inspect
migration.inspect
dependency.inspect
configuration.inspect
tests.run
```

Depending on the WorkUnit:

```text
database.query.inspect
database.executionplan.inspect
transaction.inspect
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

- no database business logic
- approved persistence technology
- migration mechanism compliance
- schema migration consistency
- transaction-boundary validation
- externalized database configuration
- no secrets in code
- persistence tests
- dependency compliance

The skill must not self-approve formal Checks.

If a required Check does not exist, report:

`CHECK_GAP`

Do not silently create normative Checks.

---

## Policies

The skill must respect all policies resolved for the WorkUnit.

Potential policy concepts include:

- approved framework required
- approved persistence technology only
- low-level database access only through approved framework
- no business logic in database
- migrations must use approved mechanism
- no uncontrolled manual schema execution
- database configuration external to application code
- no secrets in source code
- database technology change requires review

Policy names are harness implementation details.

The authoritative requirement remains the GCBA standard.

---

## Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

### STANDARD

Default for conventional persistence work.

Examples:

- adding a mapped field
- adding a normal migration
- modifying an existing repository
- adding a simple relationship
- implementing a known transaction pattern
- updating persistence tests

### REASONING

Consider when:

- migration compatibility is complex
- transaction boundaries are unclear
- multiple entities/tables are affected
- legacy persistence patterns conflict
- significant schema evolution is required
- data-access performance is non-trivial
- persistence framework behavior is ambiguous

### PREMIUM

Consider only when:

- previous reasoning attempts fail
- migration risk is high
- persistence changes affect critical data
- major architecture/persistence uncertainty remains
- multiple high-impact alternatives remain valid

Premium execution must pass the orchestrator's Human Model Gate.

This skill must never bypass the configured model-consumption policy.

---

## Escalation Conditions

Escalate to the `dev-orchestrator` when:

- required context is missing
- the data model is unclear
- a required capability is missing
- a required Check is missing
- a Policy blocks implementation
- migration policy is ambiguous
- migration ordering conflicts
- database technology must change
- architecture must change
- a cross-system transaction is implied
- performance requires major redesign
- secrets or credentials are exposed
- another specialist skill is required
- human approval is required

---

## Prohibited Behavior

This skill must not:

- redefine the domain/data model without escalation
- choose a database engine arbitrarily
- replace an established database technology independently
- bypass the approved framework
- introduce direct low-level database access without approved justification
- place business logic in stored procedures
- place business logic in triggers
- place business logic in database functions
- execute uncontrolled schema changes
- introduce a new migration mechanism without approval
- hardcode environment-specific database configuration
- hardcode credentials or secrets
- invent transaction requirements
- redesign architecture without escalation
- bypass policies
- self-approve Checks
- invent missing project context
- use the most expensive model by default

---

## Evidence Requirements

The persistence result should distinguish:

- observed persistence-stack facts
- implementation decisions
- mappings changed
- migrations changed
- transaction decisions
- configuration evidence
- assumptions
- compatibility risks
- tests executed
- formal Checks still required
- specialized skills requested

All meaningful persistence decisions must be traceable to either:

- the WorkUnit
- `dev-data` result
- existing architecture
- applicable ADR
- repository evidence
- existing persistence conventions
- normative model
- GCBA standard/policy

---

## Success Criteria

This skill is successful when it:

- converts an approved data requirement into a correct persistence implementation
- preserves the project's approved framework and persistence stack
- preserves existing mapping/data-access conventions
- uses the approved migration mechanism
- versions schema evolution safely
- implements required transaction boundaries
- keeps business logic out of the database
- keeps environment-specific database configuration outside application code
- does not expose secrets
- creates or updates appropriate persistence tests
- produces structured evidence
- declares required Checks
- declares capability gaps
- escalates database/architecture decisions correctly

---

## Source

Authoritative standard:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información - Version 6.3`

Primary references:

- Section 7.1 — Development Principles
- Section 7.2 — System Architectures
- Annex I — Version Control Repository
- Annex II — Approved Development Tools and Versions
- Annex III — Continuous Deployment

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
