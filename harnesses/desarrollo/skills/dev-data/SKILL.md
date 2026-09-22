---
name: dev-data
description: Use when a WorkUnit needs the data model worked out on a GCBA / DGISIS project — which concepts the change needs, who owns each piece of information, how it relates to what already exists, what integrity and transactional guarantees apply, and what the schema impact is. Keeps business logic out of the database layer and hands the persistence mechanism to dev-persistence. Owned by dev-backend; dev-architecture, dev-integration and dev-quality read it when they need to reason about ownership or model impact.
---

# Skill: dev-data

## Purpose

Understand and define the data model required by a WorkUnit while preserving data ownership, source-of-truth boundaries, consistency, transactional requirements, architecture constraints, and GCBA development rules.

This skill is primarily used by the `dev-backend` agent.

Its responsibility is to determine what data the system needs, who owns it, how it relates to existing concepts, what integrity and transactional guarantees are required, and what impact the change has on the existing data model.

This skill does not implement persistence mechanisms directly.

---

## Owner

Primary owner:

`dev-backend`

Secondary consumers may include:

- `dev-architecture`
- `dev-integration`
- `dev-quality`

when they need to reason about data ownership, consistency, or model impact.

---

## Core Principle

The skill must answer:

> What data model does this WorkUnit require, who owns each piece of information, and what consistency rules must be preserved without leaking business logic into the database layer?

The skill must distinguish:

```text
Data Model
≠
Persistence Implementation
```

`dev-data` defines the data requirements.

`dev-persistence` defines how those requirements are physically implemented.

---

## Scope

This skill is responsible for:

- data concepts
- domain data boundaries
- data ownership
- source of truth
- relationships between concepts
- integrity requirements
- transactional requirements
- consistency requirements
- relational vs document-oriented data needs
- data volume/access implications
- schema-impact detection
- business-logic placement analysis
- reporting/exploitation impact detection
- cache/source-of-truth boundary analysis

This skill does not own ORM, migrations, repositories, or database implementation details.

---

## Responsibility Boundaries

### `dev-data` owns

- identifying data concepts
- defining conceptual relationships
- identifying data ownership
- identifying source of truth
- determining whether data is transactional
- identifying consistency requirements
- evaluating relational vs document-oriented needs
- detecting data duplication risk
- detecting business logic leakage into the database
- identifying schema impact
- identifying reporting/data-exploitation impact

### `dev-persistence` owns

- ORM configuration
- entity mappings
- repository implementation
- migrations
- transaction implementation
- database-specific schema changes
- index implementation
- persistence framework usage
- connection and driver concerns

### `dev-api` owns

- external API contracts
- request/response schemas
- HTTP-level representation

### `dev-integration` owns

- external authoritative data sources
- system-to-system data exchange
- GCBA integration mechanisms
- identity/source-of-truth integration

### `dev-architecture-analysis` owns

- architecture-level data decisions
- service ownership boundaries
- major datastore strategy changes
- cross-system data architecture

---

## Required Context

The skill should receive only the context required for the assigned data WorkUnit.

Expected context may include:

- WorkUnit objective
- relevant Jira issue / HU / Bug / Task
- acceptance criteria
- relevant TaskContext
- Project Sheet context
- current architecture
- applicable ADRs
- current data model
- repository structure
- existing entities/models
- existing data access patterns
- existing database schema
- existing integrations
- reporting requirements
- non-functional requirements
- applicable GCBA standards
- applicable policies
- available capabilities
- required checks

The skill must not require the entire repository when targeted inspection is sufficient.

---

## Missing Context Conditions

Return `MISSING_CONTEXT` when a reliable data decision cannot be made.

Examples:

- current data model cannot be determined
- data ownership is unknown
- the source of truth is unclear
- relevant ADRs are missing
- the current datastore type is unknown
- transactional requirements are undefined
- required integration ownership is missing
- reporting requirements are referenced but unavailable

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - data_ownership
  - current_data_model
reason:
  "The WorkUnit introduces citizen data, but the authoritative source and current ownership model are not defined."
```

Do not invent ownership, relationships, or source-of-truth decisions.

---

## Analysis Procedure

### Step 1 — Understand the Data Requirement

Determine:

- what information the WorkUnit requires
- whether the information already exists
- whether the information is new
- whether the information is authoritative or derived
- whether the information is transactional
- whether the information belongs to this system

Do not start by creating tables or fields.

Start by understanding the information model.

---

### Step 2 — Inspect the Existing Data Model

Before introducing new concepts, inspect:

- existing entities
- existing domain models
- existing schema
- naming conventions
- relationships
- ownership boundaries
- duplicated concepts
- existing reporting structures

Avoid creating duplicate concepts.

Example:

```text
Requested concept:
appointment_status

Existing concepts:
status
appointmentState

→ inspect semantic overlap before creating a new field.
```

---

### Step 3 — Determine Data Ownership

For each relevant concept, determine:

- owner
- source of truth
- local responsibility
- whether the current application is authoritative
- whether the data is consumed from another GCBA system

Conceptual model:

```text
Data
 ↓
Owner
 ↓
Source of Truth
 ↓
Local Responsibility
```

Do not assume ownership because the current application stores a copy.

If ownership is unclear, return:

`DATA_OWNERSHIP_UNCLEAR`

---

## Source of Truth Rules

The skill must distinguish between:

- authoritative data
- replicated/cached data
- derived data
- reference data
- local transactional data

If the authoritative source is external:

the local system must not silently become the business owner of that data.

When external ownership requires system integration, request:

`dev-integration`

---

## Step 4 — Identify Data Concepts

Identify the real domain concepts involved.

Examples:

- Appointment
- Citizen
- Procedure
- Availability
- Status
- Document
- AuditRecord

Do not confuse:

- API DTOs
- ORM entities
- database tables
- domain concepts

These representations may differ.

---

## Step 5 — Identify Relationships

Define conceptual relationships without prematurely selecting database implementation details.

Example:

```text
Citizen
   1
   │
   N
Appointment
```

The skill may describe:

- one-to-one
- one-to-many
- many-to-many
- ownership
- reference
- composition
- dependency

Do not define concrete foreign keys unless required for analysis.

Physical implementation belongs to `dev-persistence`.

---

## Step 6 — Define Integrity Requirements

Identify data integrity constraints.

Examples:

- required values
- uniqueness
- referential integrity
- valid ranges
- valid states
- immutable identifiers
- consistency between related concepts

The skill must distinguish:

```text
Data Integrity Constraint
≠
Business Behavior
```

Examples of data integrity:

- PRIMARY KEY
- FOREIGN KEY
- UNIQUE
- NOT NULL

These are not automatically considered forbidden database business logic.

---

## Step 7 — Identify Transactional Requirements

Determine whether the WorkUnit requires operations to remain consistent as one logical unit.

Example:

```text
Create Appointment
+
Reserve Availability

→ transactional consistency may be required
```

The skill identifies the need.

`dev-persistence` defines how the transaction is implemented.

Return:

```yaml
transactionalRequirements:
  required: true
  reason: "Appointment creation and availability reservation must remain consistent."
```

when applicable.

---

## Step 8 — Evaluate Data Access Pattern and Volume

Consider:

- expected data volume
- query frequency
- read/write balance
- access patterns
- filtering needs
- pagination needs
- reporting needs
- concurrency
- performance sensitivity

The skill must detect designs that may transfer or load excessive data.

Example:

```text
Large dataset
+
unbounded query
→ DATA_VOLUME_RISK
```

The API contract response is handled by `dev-api`.

The data model/access implications belong to `dev-data`.

---

## Step 9 — Evaluate Relational vs Document-Oriented Need

Determine the type of data model required.

### Relational model is generally appropriate when:

- strong relationships exist
- transactional consistency is required
- structured schema is stable
- relational queries are central
- the system is transactional

### Document-oriented model may be considered when:

- schema variability is meaningful
- large volumes of document-like content exist
- high scalability is required
- the access model is naturally document-oriented
- relational behavior is not required

A document database must not be selected to simulate a relational transactional model.

The skill may recommend:

```text
RELATIONAL_MODEL_REQUIRED
```

or:

```text
DOCUMENT_MODEL_MAY_APPLY
```

but must not arbitrarily select a concrete database engine.

Technology selection must respect:

- architecture
- normative model
- approved technology policy
- GCBA approval requirements

---

## Step 10 — Detect Business Logic Leakage

GCBA development rules prohibit placing business logic in the database layer.

The skill must detect proposed or existing business behavior implemented through:

- stored procedures
- triggers
- database functions
- database-side business workflows
- database artifacts acting as domain logic

If detected:

return:

`BUSINESS_LOGIC_IN_DATABASE`

and associate the applicable Policy/Check.

Example:

```text
Trigger:
When status changes to APPROVED,
calculate business eligibility.

→ BUSINESS_LOGIC_IN_DATABASE
```

Recommended direction:

```text
Application / Domain Layer
```

Do not automatically treat technical integrity constraints as business logic.

---

## Step 11 — Identify Schema Impact

Determine whether the WorkUnit requires a physical schema change.

Possible result:

```text
SCHEMA_CHANGE_REQUIRED
```

Examples:

- new concept
- new attribute
- new relationship
- removed field
- changed cardinality
- changed constraint

The skill must describe the conceptual change.

Physical implementation belongs to `dev-persistence`.

---

## Step 12 — Evaluate Reporting / Exploitation Impact

When the data model may be used for reporting, operational export, or analytical consumption, determine whether the change affects those concerns.

Examples:

- reporting field removed
- key entity renamed
- new operational dimension added
- extraction semantics changed

If relevant:

return a finding such as:

```yaml
reportingImpact:
  detected: true
  description: "The changed status model affects operational reporting."
```

This skill does not implement analytics.

---

## Step 13 — Evaluate Cache vs Source of Truth

The skill must distinguish:

```text
Persistent authoritative data
≠
Cache
```

If cache technology is proposed as the only source of truth for business data:

return:

`CACHE_SOURCE_OF_TRUTH_RISK`

Caching may be appropriate for performance, but authoritative persistence must be explicit.

---

## Step 14 — Delegate Persistence Implementation

When the data model is defined and persistence changes are required:

request:

`dev-persistence`

Example:

```text
dev-data
→ "Appointment requires a new relational concept and transactional consistency."

dev-persistence
→ "Implement the mapping, migration, repository, and transaction mechanism."
```

---

## GCBA Data Rules

The authoritative source is:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información`

Relevant data rules include, among others:

- business logic must not be implemented in the database layer
- application and database responsibilities must remain separated
- database users must use the minimum required permissions
- document databases must not be used as relational databases
- document databases must not be used for transactional systems
- approved database technologies and versions must be respected
- database technology selection may require prior validation with GCBA technical areas
- information transfer volume must be controlled
- data models should support operational reporting/exploitation requirements where applicable
- source and responsibility of application information must remain clear

The complete standard must not be duplicated inside this skill.

The skill must consume the normative model, policies, and checks resolved by the harness.

---

## Database Technology Rules

This skill must not hardcode current database versions.

Approved engines and versions must come from the normative model.

The skill may determine:

```text
relational model required
```

but must not automatically decide:

```text
use PostgreSQL
```

unless that decision is already established by architecture/project context and compliant with the approved technology policy.

If a new database technology decision is required:

return:

`DATABASE_TECHNOLOGY_REVIEW_REQUIRED`

---

## Output Contract

Return a structured result.

Example:

```yaml
dataResult:

  status: COMPLETE

  dataImpact:
    level: medium

  concepts:
    - name: Appointment
      operation: MODIFY

  ownership:
    - concept: Appointment
      owner: current-application
      sourceOfTruth: current-application

    - concept: Citizen
      owner: external-gcba-system
      sourceOfTruth: external

  model:
    type: relational

  relationships:
    - from: Appointment
      to: Citizen
      type: reference

  integrityRequirements:
    - "Appointment date is required."

  transactionalRequirements:
    required: true
    reason: >
      Appointment creation and availability reservation
      must remain consistent.

  businessLogic:
    databaseLogicRequired: false

  schema:
    changeRequired: true

  persistence:
    delegatedTo:
      - dev-persistence

  reportingImpact:
    detected: false

  specializedSkillsRequired:
    - dev-persistence

  requiredCapabilities:
    - repository.read
    - data.model.inspect
    - database.schema.inspect

  requiredChecks:
    - no-db-business-logic
    - data-model-consistency

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
- `DATA_OWNERSHIP_UNCLEAR`
- `DATA_MODEL_DECISION_REQUIRED`
- `DATABASE_TECHNOLOGY_REVIEW_REQUIRED`
- `SCHEMA_CHANGE_REQUIRED`
- `PERSISTENCE_REVIEW_REQUIRED`
- `ARCHITECTURE_REVIEW_REQUIRED`
- `BUSINESS_LOGIC_IN_DATABASE`
- `DATA_VOLUME_RISK`
- `CACHE_SOURCE_OF_TRUTH_RISK`
- `FAILED`

The orchestrator must be able to react to these statuses without relying only on free-form prose.

---

## Required Capabilities

Typical capabilities include:

```text
repository.read
repository.search
data.model.inspect
database.schema.inspect
database.metadata.inspect
architecture.inspect
documentation.read
```

Depending on the WorkUnit:

```text
dependency.inspect
reporting.model.inspect
integration.contract.inspect
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
- data model consistency
- approved database technology
- data ownership
- transaction boundary
- schema consistency
- data volume controls

The skill must not self-approve formal Checks.

If a required Check does not exist, report:

`CHECK_GAP`

Do not silently create normative Checks.

---

## Policies

The skill must respect all policies resolved for the WorkUnit.

Potential policy concepts include:

- no business logic in database
- approved database technologies only
- document database not for relational use
- document database not for transactional systems
- database selection requires approved process
- minimum database permissions
- controlled data ownership
- no cache as implicit source of truth

Policy names are harness implementation details.

The authoritative requirement remains the GCBA standard.

---

## Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

### STANDARD

Default for normal data-model analysis.

Examples:

- adding a field to an existing concept
- adding a simple relationship
- identifying transactional need
- reviewing data ownership in a known domain
- evaluating an existing relational model

### REASONING

Consider when:

- data ownership is unclear
- multiple systems share authoritative data
- transaction boundaries are complex
- relational vs document-oriented choice is non-trivial
- large schema impact exists
- multiple domains share the model
- reporting and operational requirements conflict
- significant data duplication risk exists

### PREMIUM

Consider only when:

- previous reasoning attempts fail
- the data architecture is organization-wide
- ownership decisions are highly ambiguous
- the choice has significant architectural/operational impact
- multiple major alternatives remain valid

Premium execution must pass the orchestrator's Human Model Gate.

This skill must never bypass the configured model-consumption policy.

---

## Escalation Conditions

Escalate to the `dev-orchestrator` when:

- required context is missing
- data ownership is unclear
- a required capability is missing
- a required Check is missing
- a Policy blocks the proposed model
- a new database technology decision is required
- architecture must change
- integration/source-of-truth analysis is required
- persistence implementation is required
- reporting impact requires another specialist
- human approval is required

---

## Prohibited Behavior

This skill must not:

- create migrations directly
- implement repositories
- configure ORM mappings
- implement transaction mechanisms
- select a database engine arbitrarily
- implement business logic in stored procedures
- implement business logic in triggers
- assume data ownership
- duplicate authoritative external data without justification
- use a document database as a relational database
- use a document database for transactional behavior contrary to GCBA rules
- treat cache as authoritative persistence without explicit design
- design API contracts
- redesign architecture without escalation
- bypass policies
- self-approve Checks
- invent missing project context
- use the most expensive model by default

---

## Evidence Requirements

The data result should distinguish:

- observed data-model facts
- inferred relationships
- ownership evidence
- assumptions
- recommendations
- risks
- schema impact
- transactional requirements
- formal Checks still required
- specialized skills requested

All meaningful data decisions must be traceable to either:

- the WorkUnit
- Project Sheet
- existing architecture
- existing ADR
- current data model
- repository evidence
- integration ownership
- GCBA standard/policy

---

## Success Criteria

This skill is successful when it:

- identifies the real data concepts required by the WorkUnit
- preserves clear ownership and source-of-truth boundaries
- avoids duplicate concepts
- identifies integrity requirements
- identifies transactional requirements
- distinguishes relational and document-oriented needs correctly
- prevents business logic from leaking into the database
- identifies schema impact
- identifies reporting/data-volume risks when relevant
- delegates physical persistence implementation to `dev-persistence`
- produces structured evidence
- declares required Checks
- declares capability gaps
- escalates architecture/integration decisions correctly

---

## Source

Authoritative standard:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información - Version 6.3`

Primary references:

- Section 3 — Application Principles
- Section 6.5 — Logical Architecture
- Section 7.1 — Development Principles
- Section 8.5 — Report Generation
- Section 8.6 — Document Database
- Section 11 — Non-Functional Requirements
- Annex II — Approved Development Tools and Versions
- Annex III — Continuous Deployment

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
