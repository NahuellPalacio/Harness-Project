---
name: dev-storage
description: Use when a WorkUnit handles application files on a GCBA / DGISIS project — uploads and downloads, persistent and temporary files, file lifecycle and cleanup, storage references and storage configuration. Persistent files go through the approved GCBA storage mechanism, never local disk; temporary ones are cleaned up right after use and the configuration is not hardcoded. Owned by dev-backend; dev-integration, dev-devops, dev-security and dev-quality read it when they need to reason about storage behaviour.
---

# Skill: dev-storage

## Purpose

Manage application files according to the GCBA standard storage and file-lifecycle requirements while preserving existing project conventions, architectural constraints, repository patterns, applicable ADRs, and GCBA development standards.

This skill is primarily used by the `dev-backend` agent.

Its responsibility is to ensure that persistent files use the approved GCBA storage mechanism, temporary files are cleaned up immediately after use, storage access remains decoupled from business logic, and environment-specific storage configuration is not hardcoded.

---

## Owner

Primary owner:

`dev-backend`

Secondary consumers may include:

- `dev-integration`
- `dev-devops`
- `dev-security`
- `dev-quality`

when they need to inspect or reason about storage behavior, file lifecycle, storage access, configuration, or security implications.

---

## Core Principle

The skill must answer:

> How should this application handle files so that persistent content uses the approved GCBA storage mechanism, temporary files are removed immediately after use, and storage concerns remain decoupled from domain logic?

The skill must distinguish:

```text
Persistent File
≠
Temporary File
```

and:

```text
Binary Content
≠
Business Metadata
```

---

## Scope

This skill is responsible for:

- persistent file handling
- temporary file handling
- file lifecycle
- upload/download storage behavior
- storage abstraction usage
- storage-reference handling
- file cleanup
- storage configuration usage
- storage-pattern inspection
- detection of local persistent storage
- detection of unmanaged temporary files
- coordination with metadata persistence
- storage-focused tests

This skill does not provision storage infrastructure or define identity/security architecture.

---

## Responsibility Boundaries

### `dev-storage` owns

- persistent vs temporary file classification
- storage lifecycle
- storage abstraction
- file creation/read/delete behavior
- temporary-file cleanup
- persistent-file storage routing
- storage reference handling
- storage configuration consumption
- detection of local persistent file storage
- storage-focused tests

### `dev-data` owns

- file metadata model
- metadata ownership
- source-of-truth decisions
- document/domain relationships

### `dev-persistence` owns

- metadata persistence
- repository/data-access implementation
- schema evolution for metadata

### `dev-api` owns

- upload/download HTTP contracts
- multipart request contracts
- API response contracts
- HTTP validation/error semantics

### `dev-integration` owns

- GCBA corporate storage integration details when applicable
- authentication/authorization flows for storage services
- external/internal integration mechanisms

### `dev-devops` owns

- storage infrastructure provisioning
- environment configuration
- secrets/configuration platform setup
- deployment/platform integration

### `dev-security` owns

- malware/security analysis
- file-content security assessment
- access-control risk
- sensitive-file handling review

---

## Required Context

The skill should receive only the context required for the assigned storage WorkUnit.

Expected context may include:

- WorkUnit objective
- relevant Jira issue / HU / Bug / Task
- acceptance criteria
- relevant TaskContext
- architecture analysis
- applicable ADRs
- existing storage abstraction
- existing upload/download flows
- existing file metadata model
- existing storage configuration
- existing temporary-file patterns
- existing storage tests
- applicable GCBA standards
- applicable policies
- available capabilities
- required checks

The skill must not require the entire repository when targeted inspection is sufficient.

---

## Missing Context Conditions

Return `MISSING_CONTEXT` when reliable storage implementation is not possible.

Examples:

- the approved storage mechanism cannot be determined
- storage integration details are missing
- file lifecycle is undefined
- persistent vs temporary behavior is unclear
- required metadata relationships are missing
- storage configuration cannot be determined
- relevant ADRs are unavailable

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - approved_storage_mechanism
  - file_lifecycle
reason:
  "The WorkUnit requires persistent file handling, but the approved GCBA storage mechanism cannot be determined from available project context."
```

Do not invent the concrete storage technology.

---

## Storage Procedure

### Step 1 — Understand the File Requirement

Determine:

- file purpose
- file type
- file lifecycle
- persistence requirement
- temporary processing requirement
- metadata requirement
- access pattern
- retention expectation
- downstream dependencies

Do not assume that every file is persistent.

---

### Step 2 — Classify File Lifecycle

Each file must be classified as:

```text
PERSISTENT
```

or:

```text
TEMPORARY
```

### Persistent

Persistent files must use the approved GCBA standard storage mechanism.

### Temporary

Temporary files may exist only for the duration required to perform the operation and must be removed immediately after use.

If classification cannot be determined:

return:

`FILE_LIFECYCLE_UNCLEAR`

---

## Persistent Storage Rules

GCBA development rules require application-managed persistent files to use the approved GCBA standard storage mechanism.

The skill must not persist application files permanently in:

- local application directories
- container-local filesystem
- developer machine paths
- arbitrary shared folders
- temporary directories
- hardcoded server paths

Examples of invalid persistent patterns:

```text
/app/uploads/document.pdf
```

```text
C:\app\files\document.pdf
```

If detected:

return:

`LOCAL_PERSISTENT_STORAGE_VIOLATION`

---

## Temporary File Rules

Temporary local processing is allowed only when required by the operation.

The lifecycle must follow:

```text
create temporary file
        ↓
process
        ↓
cleanup immediately
```

The implementation must provide a guaranteed cleanup path.

Preferred conceptual pattern:

```text
try:
    create temp
    process temp
finally:
    delete temp
```

Do not rely on eventual operating-system cleanup as the primary mechanism.

If immediate cleanup cannot be guaranteed:

return:

`TEMPORARY_FILE_CLEANUP_RISK`

---

## Step 3 — Inspect Existing Storage Pattern

Before implementing a new storage path, inspect the existing project.

Look for abstractions such as:

- `DocumentStorageService`
- `FileStorageAdapter`
- `StorageClient`
- file service interfaces
- existing storage repositories/adapters
- existing configuration keys

Reuse valid existing patterns.

Do not introduce a new storage abstraction only because another architecture is preferred.

---

## Step 4 — Separate Binary Content from Metadata

The skill must distinguish:

```text
Binary Content
```

from:

```text
Business Metadata
```

Example:

```text
Storage:
PDF binary

Database / application model:
documentId
fileName
contentType
storageReference
createdAt
business association
```

Persistent binary content belongs in the approved storage mechanism.

Metadata belongs to the application data model and persistence layer.

When metadata is required:

request:

- `dev-data`
- `dev-persistence`

as applicable.

---

## Step 5 — Determine Storage Reference Strategy

Application/domain logic should depend on a storage reference or abstraction rather than a physical local path.

Preferred concept:

```text
storageReference
```

instead of:

```text
/volume01/files/2026/09/document.pdf
```

The concrete reference format must follow the existing approved project/storage convention.

Do not invent storage identifiers.

---

## Step 6 — Implement Upload Flow

When the WorkUnit requires upload behavior:

1. receive the file through the approved API contract
2. validate the basic file input expected by the application
3. classify persistent vs temporary behavior
4. store persistent content through the approved storage abstraction
5. process temporary content only for the required duration
6. persist business metadata separately when required
7. return/store the approved storage reference
8. guarantee cleanup of temporary artifacts

Detailed HTTP upload contracts belong to:

`dev-api`

Security-specific file validation belongs to:

`dev-security`

---

## Step 7 — Implement Download / Read Flow

When the WorkUnit requires download/read behavior:

1. resolve the approved storage reference
2. access the file through the existing storage abstraction
3. avoid exposing internal physical storage paths
4. preserve application authorization/integration boundaries
5. stream/return content according to the API contract

Detailed HTTP response behavior belongs to:

`dev-api`

Authentication/authorization integration belongs to:

`dev-integration`

---

## Step 8 — Implement Cleanup

Cleanup must cover all temporary artifacts created by the operation.

Consider:

- success path
- validation failure
- processing error
- external-service failure
- timeout
- exception path

A temporary file left behind after failure is still a cleanup failure.

Return:

`TEMPORARY_FILE_CLEANUP_RISK`

when cleanup is incomplete or non-deterministic.

---

## Step 9 — Preserve Externalized Configuration

GCBA requires environment-dependent configuration to remain outside application code.

Storage configuration must not be hardcoded when environment-specific.

Examples:

- storage endpoint
- container/bucket identifier
- base path
- credentials
- secret values
- environment-specific connection data

The skill consumes approved configuration.

Provisioning/configuration belongs to:

`dev-devops`

If credentials/secrets are found in source code:

return:

`SECRET_EXPOSURE_RISK`

---

## Step 10 — Resolve Corporate Storage Integration

This skill must not invent the concrete technology behind the GCBA standard storage mechanism.

If the project already contains an approved storage adapter:

reuse it.

If a persistent-file WorkUnit requires corporate storage behavior but the concrete integration mechanism is unavailable:

return:

`INTEGRATION_REVIEW_REQUIRED`

and request:

`dev-integration`

Do not assume technologies such as:

- S3
- Azure Blob
- MinIO
- NFS
- local filesystem

unless supported by project context or the normative model.

---

## Step 11 — Tests

Create or update storage-focused tests when required.

Possible tests:

- persistent-storage routing tests
- temporary-file cleanup tests
- storage-adapter tests
- upload-flow tests
- download-flow tests
- failure cleanup tests
- configuration tests
- metadata-reference tests

Tests executed during implementation are development feedback.

Formal compliance remains the responsibility of required Checks.

---

## Step 12 — Collect Evidence

Return evidence such as:

- lifecycle classification
- storage abstraction reused
- persistent/local storage findings
- temporary-file handling
- cleanup behavior
- storage-reference strategy
- configuration mechanism
- metadata dependencies
- tests executed
- specialized skills requested
- risks
- assumptions

---

## GCBA Storage Rules

The authoritative source is:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información`

Relevant storage rules include, among others:

- application-managed files must use the approved GCBA standard storage mechanism
- persistent local file storage is not allowed
- temporary files must be removed immediately after use
- environment-specific configuration must remain outside application code
- maintainability and decoupling must be preserved
- security and access requirements must be respected through the appropriate specialized concerns

The complete standard must not be duplicated inside this skill.

The skill must consume the normative model, policies, and checks resolved by the harness.

---

## Output Contract

Return a structured result.

Example:

```yaml
storageResult:

  status: COMPLETE

  file:
    purpose: citizen-document
    lifecycle: persistent

  storage:
    type: gcba-standard-storage
    existingAbstractionReused: true
    localPersistentStorage: false

  temporaryProcessing:
    required: true
    cleanupGuaranteed: true

  metadata:
    required: true
    delegatedTo:
      - dev-data
      - dev-persistence

  api:
    required: true
    delegatedTo:
      - dev-api

  integration:
    required: false

  configuration:
    externalized: true
    secretsInCode: false

  specializedSkillsRequired:
    - dev-data
    - dev-persistence

  requiredCapabilities:
    - repository.read
    - repository.search
    - repository.write
    - storage.pattern.inspect
    - filesystem.inspect
    - configuration.inspect
    - tests.run

  requiredChecks:
    - no-local-persistent-files
    - temporary-file-cleanup
    - storage-configuration-external

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
- `FILE_LIFECYCLE_UNCLEAR`
- `LOCAL_PERSISTENT_STORAGE_VIOLATION`
- `TEMPORARY_FILE_CLEANUP_RISK`
- `STORAGE_CONFIGURATION_RISK`
- `INTEGRATION_REVIEW_REQUIRED`
- `SECURITY_REVIEW_REQUIRED`
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
filesystem.inspect
storage.pattern.inspect
configuration.inspect
tests.run
```

Depending on the WorkUnit and available integration:

```text
storage.read
storage.write
storage.delete
storage.metadata.inspect
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

- no local persistent files
- temporary-file cleanup
- storage configuration externalization
- no secrets in source code
- approved storage usage
- storage-focused tests

The skill must not self-approve formal Checks.

If a required Check does not exist, report:

`CHECK_GAP`

Do not silently create normative Checks.

---

## Policies

The skill must respect all policies resolved for the WorkUnit.

Potential policy concepts include:

- persistent files must use GCBA standard storage
- no local persistent file storage
- temporary files must be deleted immediately
- environment-specific storage configuration must be externalized
- secrets must not be stored in source code
- approved storage integration only

Policy names are harness implementation details.

The authoritative requirement remains the GCBA standard.

---

## Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

### STANDARD

Default for normal storage work.

Examples:

- integrating an upload with an existing storage adapter
- implementing download behavior
- adding temporary-file cleanup
- reusing an established file-storage pattern
- adding storage tests

### REASONING

Consider when:

- file lifecycle is ambiguous
- multiple systems/storage mechanisms are involved
- migration from local to corporate storage is required
- large-file behavior is complex
- cleanup behavior spans multiple failure paths
- metadata ownership/integration is non-trivial

### PREMIUM

Consider only when:

- previous reasoning attempts fail
- storage architecture is highly ambiguous
- storage changes affect critical organizational data
- multiple major integration alternatives remain unresolved

Premium execution must pass the orchestrator's Human Model Gate.

This skill must never bypass the configured model-consumption policy.

---

## Escalation Conditions

Escalate to the `dev-orchestrator` when:

- required context is missing
- file lifecycle is unclear
- a required capability is missing
- a required Check is missing
- a Policy blocks implementation
- approved GCBA storage integration is unavailable
- integration/authentication behavior is required
- storage infrastructure changes are required
- file security requires deeper review
- metadata model changes are required
- secrets or credentials are exposed
- another specialist skill is required
- human approval is required

---

## Prohibited Behavior

This skill must not:

- persist application files permanently on local filesystem
- leave temporary files without guaranteed cleanup
- assume the concrete GCBA storage technology
- expose internal physical storage paths as domain contracts
- hardcode storage endpoints or credentials
- store secrets in source code
- implement metadata persistence directly without the appropriate data/persistence concern
- implement miBA/OIDC/Keycloak behavior
- provision infrastructure
- bypass policies
- self-approve Checks
- invent missing project context
- use the most expensive model by default

---

## Evidence Requirements

The storage result should distinguish:

- observed project storage patterns
- lifecycle decisions
- persistent/local storage findings
- temporary-file cleanup behavior
- metadata dependencies
- configuration evidence
- assumptions
- risks
- tests executed
- formal Checks still required
- specialized skills requested

All meaningful storage decisions must be traceable to either:

- the WorkUnit
- project context
- existing architecture
- applicable ADR
- repository evidence
- existing storage abstraction
- GCBA standard/policy

---

## Success Criteria

This skill is successful when it:

- correctly classifies persistent vs temporary file behavior
- routes persistent files to the approved GCBA storage mechanism
- prevents local persistent file storage
- guarantees cleanup of temporary files
- reuses existing approved storage abstractions
- keeps binary content separate from business metadata
- preserves externalized configuration
- avoids exposing physical storage paths
- delegates metadata persistence correctly
- identifies integration/security requirements without duplicating them
- creates or updates appropriate tests
- produces structured evidence
- declares required Checks
- declares capability gaps
- escalates integration/infrastructure decisions correctly

---

## Source

Authoritative standard:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información - Version 6.3`

Primary references:

- Section 7.1 — Development Principles
- Section 11 — Non-Functional Requirements

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
