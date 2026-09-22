---
name: dev-observability
description: Use when a WorkUnit touches the operational signals of a GCBA / DGISIS application — application and error logging, log levels configurable at runtime, signals for the core transactions, audit records when they are required, and the liveness and readiness health endpoints with their dependency classification. Nothing sensitive reaches a log or a health response. Owned by dev-backend; dev-devops, dev-quality, dev-security and dev-architecture read it when they need to reason about operational behaviour.
---

# Skill: dev-observability

## Purpose

Provide the application-level operational signals required to understand system behavior, failures, auditability, and health while preserving the project's existing observability mechanisms and complying with GCBA development standards.

This skill is primarily used by the `dev-backend` agent.

Its responsibility is to ensure that the application produces meaningful logs, operational signals for core transactions, audit records when required, runtime-configurable logging levels, and mandatory health endpoints without exposing sensitive information.

---

## Owner

Primary owner:

`dev-backend`

Secondary consumers may include:

- `dev-devops`
- `dev-quality`
- `dev-security`
- `dev-architecture`

when they need to inspect operational behavior, health checks, auditability, logging, or deployment-readiness requirements.

---

## Core Principle

The skill must answer:

> What operational signals does this application need so that its behavior, failures, core transactions, audit events, and runtime health can be understood safely and consistently?

The skill must distinguish:

```text
Logging
≠
Audit
≠
Health
≠
Monitoring Infrastructure
```

The application produces observability signals.

Platform/infrastructure tooling consumes and operates those signals.

---

## Scope

This skill is responsible for:

- application logging
- error logging
- operational alerts/signals
- core transaction observability
- runtime-configurable log levels
- audit behavior when required
- liveness health endpoint
- readiness health endpoint
- optional general health endpoint
- startup-probe requirement detection
- health-check dependency classification
- health-response safety
- observability-focused tests
- coordination with deployment/platform monitoring requirements

This skill does not provision monitoring infrastructure.

---

## Responsibility Boundaries

### `dev-observability` owns

- application-level logging behavior
- operational errors and alerts
- core transaction signals
- runtime log-level configurability
- audit behavior implemented by the application
- `/health/liveness`
- `/health/readiness`
- optional `/health`
- startup-probe requirement detection
- health endpoint safety
- observability-focused tests

### `dev-devops` owns

- OpenShift probe configuration
- deployment manifest integration
- monitoring infrastructure
- platform dashboards
- platform-level alerting
- environment configuration required by observability tooling

### `dev-security` owns

- deep review of sensitive-data exposure
- log-security analysis
- credential/token leakage assessment
- audit/security-control review

### `dev-api` owns

- public API error contracts
- HTTP response semantics
- externally exposed API contracts

### `dev-architecture-analysis` owns

- major observability architecture changes
- distributed tracing architecture
- organization-wide telemetry design
- major asynchronous monitoring architecture

---

## Observability Concepts

The skill must distinguish four concepts.

### Logging

Answers:

> What happened inside the application?

Typical signals:

- startup
- shutdown
- error
- warning
- relevant operational event
- dependency failure
- important state transition

### Audit

Answers:

> Who performed a relevant action, what changed, and when?

Audit is not a replacement for diagnostic logging.

### Health

Answers:

> Is the application alive and ready to operate?

Health behavior includes:

- liveness
- readiness
- optional general health
- optional startup requirements

### Monitoring

Answers:

> What does the platform infer from application signals?

Monitoring infrastructure belongs primarily to `dev-devops`.

---

## Required Context

The skill should receive only the context required for the assigned observability WorkUnit.

Expected context may include:

- WorkUnit objective
- relevant Jira issue / HU / Bug / Task
- acceptance criteria
- relevant TaskContext
- architecture analysis
- applicable ADRs
- existing logging framework
- existing log configuration
- existing health endpoints
- existing audit mechanism
- core business transactions
- critical dependencies
- existing error handling
- existing deployment/probe configuration
- applicable GCBA standards
- applicable policies
- available capabilities
- required checks

The skill must not require the entire repository when targeted inspection is sufficient.

---

## Missing Context Conditions

Return `MISSING_CONTEXT` when reliable observability implementation is not possible.

Examples:

- current logging mechanism cannot be determined
- critical dependencies are unknown
- audit requirements are referenced but undefined
- current health behavior is unavailable
- core transactions cannot be identified
- deployment constraints are required but unavailable
- relevant ADRs are missing

Example:

```yaml
status: MISSING_CONTEXT
missing:
  - critical_dependencies
  - logging_mechanism
reason:
  "Readiness behavior cannot be defined safely because the application's critical dependencies are not known."
```

Do not invent audit or dependency requirements.

---

## Observability Procedure

### Step 1 — Understand the Observability Requirement

Determine:

- what operational behavior must be visible
- which errors matter operationally
- which core transactions must be measurable
- whether audit is required
- whether health endpoints already exist
- what dependencies are critical for readiness
- whether startup behavior is unusual
- what platform/deployment coordination is required

Do not add observability noise without a clear purpose.

---

### Step 2 — Inspect the Existing Logging Mechanism

Before changing logging behavior, inspect:

- logging framework
- logger usage
- logging configuration
- log levels
- structured fields if already used
- existing error logging
- existing operational events
- existing transaction logging
- existing correlation/tracing mechanisms

Preserve the existing approved mechanism.

Do not introduce a second logging framework without explicit justification.

---

## Standard Logging Rules

GCBA development rules require standard logging appropriate to the selected technology.

Logging must include, where relevant:

- errors
- alerts
- core transaction records
- operational events required to assess application health

The skill must avoid indiscriminate logging.

Do not add logs to every line or method solely for visibility.

Operational signals should have a clear purpose.

---

## Step 3 — Identify Core Transactions

Identify application operations whose success/failure is important for measuring application health.

Examples:

```text
CreateAppointment
SubmitProcedure
GenerateDocument
RegisterCitizenRequest
```

For a core transaction, consider signals such as:

```text
START
SUCCESS
FAILURE
```

Example:

```text
CreateAppointment
       ↓
START
       ↓
processing
       ↓
SUCCESS / FAILURE
```

The goal is to make critical application behavior observable.

If important transactions cannot be identified:

return:

`CORE_TRANSACTION_SIGNAL_MISSING`

or request clarification when the business context is insufficient.

---

## Step 4 — Implement Error and Alert Signals

Relevant failures must generate useful operational evidence.

Consider:

- unexpected errors
- expected operational failures
- dependency failures
- timeout conditions
- retry exhaustion
- invalid internal state
- degraded behavior

The skill must distinguish between:

```text
Public API Error
```

and:

```text
Internal Operational Evidence
```

`dev-api` owns the external HTTP contract.

`dev-observability` owns the internal operational signal.

---

## Sensitive Logging Rules

Logs must not intentionally expose:

- passwords
- access tokens
- refresh tokens
- secret keys
- connection credentials
- private cryptographic material
- unnecessary sensitive data

If sensitive information is detected:

return:

`SECURITY_REVIEW_REQUIRED`

and request `dev-security` when appropriate.

---

## Step 5 — Validate Runtime Log-Level Configuration

GCBA requires the logging level to be configurable without requiring a new deployment.

The application should support changes such as:

```text
INFO
WARN
ERROR
DEBUG
```

through an approved runtime/environment configuration mechanism.

The skill must detect configurations where log level is effectively hardcoded.

If the log level cannot be changed without code change/redeployment:

return:

`LOG_LEVEL_NOT_RUNTIME_CONFIGURABLE`

The concrete platform mechanism may require coordination with:

`dev-devops`

---

## Step 6 — Evaluate Audit Requirements

Audit and diagnostic logging are separate concerns.

Audit may be required for relevant business or administrative actions.

Possible audit information may include:

- actor
- action
- target/resource
- timestamp
- relevant before/after reference
- result

The exact audit model must come from project/business requirements.

Do not invent audit requirements.

If audit is referenced but not defined:

return:

`AUDIT_REQUIREMENT_UNCLEAR`

---

## Audit Lifecycle Rules

GCBA requires audit processes to support controlled cleanup based on registration dates and restricted access through the applicable backoffice mechanism.

When audit is required, evaluate:

- restricted access
- cleanup/purge capability
- registration date availability
- traceability
- retention-related project rules

If these controls are missing:

return:

`AUDIT_CONTROL_MISSING`

The skill does not independently define legal/organizational retention periods.

---

## Step 7 — Implement Mandatory Health Endpoints

GCBA requires health checks for production homologation.

Mandatory endpoints:

```text
/health/liveness
/health/readiness
```

Recommended general endpoint:

```text
/health
```

The skill must preserve framework/project conventions when implementing these endpoints.

Do not expose unnecessary internal details.

---

## Liveness

Purpose:

> Determine whether the application process is alive and able to respond.

Liveness should remain simple.

It should not depend on unrelated external services when doing so would cause unnecessary restarts.

Conceptually:

```text
GET /health/liveness
        ↓
Application process responsive?
        ↓
Healthy / Unhealthy
```

If liveness incorrectly depends on secondary resources:

return:

`HEALTH_CHECK_RESPONSIBILITY_MIXED`

---

## Readiness

Purpose:

> Determine whether the application is ready to receive traffic.

Readiness may inspect critical dependencies required for correct operation.

Examples may include:

- database connectivity
- mandatory external service
- critical internal dependency
- required runtime resource

Conceptually:

```text
GET /health/readiness
        ↓
Application ready?
Critical dependencies ready?
        ↓
READY / NOT READY
```

Do not include every optional dependency automatically.

Only critical dependencies should influence readiness.

---

## Liveness vs Readiness

The skill must preserve separate responsibilities.

```text
Liveness
→ Is the process alive?

Readiness
→ Can it safely receive traffic?
```

Do not collapse both checks into one undifferentiated dependency check.

If responsibilities are mixed:

return:

`HEALTH_CHECK_RESPONSIBILITY_MIXED`

---

## General Health Endpoint

A general endpoint such as:

```text
/health
```

may be implemented for monitoring purposes when supported by the project/framework.

It is not a replacement for the mandatory liveness and readiness endpoints.

---

## Startup Probe Requirement

Startup behavior may require an optional startup probe when the application has a slow or unusual startup sequence.

The skill may report:

`STARTUP_PROBE_RECOMMENDED`

when evidence indicates that startup may exceed normal liveness/readiness initialization behavior.

The final OpenShift configuration belongs to:

`dev-devops`

---

## Step 8 — Prevent Sensitive Health Responses

Health endpoints must not expose sensitive or unnecessary infrastructure information.

Do not expose:

- credentials
- tokens
- internal IP addresses
- private hostnames unless explicitly safe/required
- filesystem paths
- secret configuration
- connection strings
- stack traces

Prefer minimal health responses.

Example:

```json
{
  "status": "UP"
}
```

The exact format must follow the current framework/project convention.

If sensitive details are exposed:

return:

`HEALTH_SENSITIVE_DATA_EXPOSURE`

---

## Step 9 — Define DevOps Probe Requirements

The application skill defines required health behavior.

`dev-devops` configures the deployment/platform probes.

The skill should provide enough evidence for DevOps to configure values such as:

- initial delay
- timeout
- period
- success threshold
- failure threshold

Do not invent exact platform values without evidence.

If deployment configuration is required:

return or declare:

`DEVOPS_CONFIGURATION_REQUIRED`

and request:

`dev-devops`

---

## Step 10 — Preserve Existing Metrics / Tracing Mechanisms

If the project already uses:

- metrics
- tracing
- correlation IDs
- structured telemetry
- distributed tracing

preserve the existing approved mechanism where relevant.

This skill must not impose a specific technology such as:

- OpenTelemetry
- Prometheus
- Grafana
- vendor-specific APM

unless project context or the normative model explicitly requires it.

If a major telemetry architecture decision is required:

return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

## Step 11 — Tests

Create or update observability-focused tests when required.

Possible tests:

- logging behavior tests
- health endpoint tests
- liveness tests
- readiness tests
- dependency-failure readiness tests
- health sensitive-data tests
- audit tests
- log-level configuration tests

Tests executed during implementation are development feedback.

Formal compliance remains the responsibility of required Checks.

---

## Step 12 — Collect Evidence

Return evidence such as:

- logging mechanism detected
- log-level configuration mechanism
- core transactions identified
- errors/alerts implemented
- audit behavior
- liveness endpoint
- readiness endpoint
- critical readiness dependencies
- startup behavior
- health-response safety
- tests executed
- DevOps requirements
- assumptions
- risks
- specialized skills requested

---

## GCBA Observability Rules

The authoritative source is:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información`

Relevant observability rules include, among others:

- standard logging must follow the selected technology
- errors and alerts must be logged
- core transactions must generate enough evidence to measure application health
- logging level must be configurable without requiring deployment
- audit processes must support controlled cleanup based on registration dates
- audit access must be restricted through the applicable backoffice mechanism
- health checks are mandatory for production homologation
- `/health/liveness` is mandatory
- `/health/readiness` is mandatory
- `/health` may be exposed for general monitoring
- liveness and readiness must serve distinct purposes
- health endpoints must not expose sensitive information
- development must coordinate health behavior with OpenShift deployment configuration

The complete standard must not be duplicated inside this skill.

The skill must consume the normative model, policies, and checks resolved by the harness.

---

## Output Contract

Return a structured result.

Example:

```yaml
observabilityResult:

  status: COMPLETE

  logging:
    mechanism: existing-project-framework
    errors: true
    alerts: true
    runtimeLevelConfigurable: true

  coreTransactions:
    - name: CreateAppointment
      startSignal: true
      successSignal: true
      failureSignal: true

  audit:
    required: true
    cleanupByRegistrationDate: true
    restrictedAccess: true

  health:
    liveness:
      path: /health/liveness
      implemented: true

    readiness:
      path: /health/readiness
      implemented: true
      criticalDependencies:
        - database

    startup:
      required: false

    general:
      path: /health
      implemented: true

    sensitiveDataExposed: false

  devops:
    probeConfigurationRequired: true
    delegatedTo:
      - dev-devops

  specializedSkillsRequired:
    - dev-devops

  requiredCapabilities:
    - repository.read
    - repository.search
    - repository.write
    - logging.inspect
    - configuration.inspect
    - health.endpoint.inspect
    - tests.run

  requiredChecks:
    - standard-logging
    - configurable-log-level
    - health-liveness
    - health-readiness
    - health-no-sensitive-data

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
- `LOGGING_STANDARD_MISSING`
- `LOG_LEVEL_NOT_RUNTIME_CONFIGURABLE`
- `CORE_TRANSACTION_SIGNAL_MISSING`
- `AUDIT_REQUIREMENT_UNCLEAR`
- `AUDIT_CONTROL_MISSING`
- `HEALTH_CHECK_MISSING`
- `HEALTH_CHECK_RESPONSIBILITY_MIXED`
- `HEALTH_SENSITIVE_DATA_EXPOSURE`
- `STARTUP_PROBE_RECOMMENDED`
- `DEVOPS_CONFIGURATION_REQUIRED`
- `SECURITY_REVIEW_REQUIRED`
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
logging.inspect
configuration.inspect
health.endpoint.inspect
api.routes.inspect
audit.inspect
tests.run
```

Depending on the WorkUnit and available runtime:

```text
logs.query
health.execute
metrics.inspect
tracing.inspect
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

- standard logging
- configurable log level
- core transaction observability
- health liveness
- health readiness
- health responsibility separation
- health sensitive-data exposure
- audit restricted access
- audit cleanup capability
- observability tests

The skill must not self-approve formal Checks.

If a required Check does not exist, report:

`CHECK_GAP`

Do not silently create normative Checks.

---

## Policies

The skill must respect all policies resolved for the WorkUnit.

Potential policy concepts include:

- standard logging required
- log level must be runtime configurable
- health checks required
- liveness required
- readiness required
- health responsibilities must remain separated
- health endpoints must not expose sensitive information
- audit cleanup required
- audit access restricted
- secrets must not be logged

Policy names are harness implementation details.

The authoritative requirement remains the GCBA standard.

---

## Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

### STANDARD

Default for normal observability work.

Examples:

- adding application logs
- adding transaction start/success/failure signals
- implementing liveness/readiness
- making log level configurable
- adding health tests
- adapting an existing audit mechanism

### REASONING

Consider when:

- multiple critical dependencies affect readiness
- audit behavior is complex
- legacy logging patterns conflict
- distributed transaction visibility is required
- health responsibilities are ambiguous
- major observability inconsistencies exist

### PREMIUM

Consider only when:

- previous reasoning attempts fail
- observability architecture is organization-wide
- security/operational risk is high
- multiple high-impact telemetry alternatives remain unresolved

Premium execution must pass the orchestrator's Human Model Gate.

This skill must never bypass the configured model-consumption policy.

---

## Escalation Conditions

Escalate to the `dev-orchestrator` when:

- required context is missing
- a required capability is missing
- a required Check is missing
- a Policy blocks implementation
- audit requirements are unclear
- critical readiness dependencies cannot be determined
- health behavior requires deployment changes
- sensitive information is exposed
- a major telemetry architecture decision is required
- another specialist skill is required
- human approval is required

---

## Prohibited Behavior

This skill must not:

- introduce a new logging framework without justification
- log every line/method without operational purpose
- log credentials, tokens, or secrets
- use permanent DEBUG logging as a default solution
- invent audit requirements
- mix liveness and readiness responsibilities
- expose sensitive infrastructure data through health endpoints
- provision Prometheus, Grafana, or other monitoring infrastructure
- configure OpenShift deployment directly
- impose OpenTelemetry or another telemetry stack without project/normative evidence
- bypass policies
- self-approve Checks
- invent missing project context
- use the most expensive model by default

---

## Evidence Requirements

The observability result should distinguish:

- observed logging mechanisms
- implemented signals
- core transaction evidence
- audit requirements/evidence
- health behavior
- readiness dependency evidence
- configuration evidence
- assumptions
- risks
- tests executed
- formal Checks still required
- specialized skills requested

All meaningful observability decisions must be traceable to either:

- the WorkUnit
- project context
- existing architecture
- applicable ADR
- repository evidence
- existing observability mechanism
- GCBA standard/policy

---

## Success Criteria

This skill is successful when it:

- preserves the approved logging mechanism
- logs relevant errors and alerts
- makes core transactions operationally visible
- supports runtime-configurable log levels
- implements audit behavior when required
- implements `/health/liveness`
- implements `/health/readiness`
- preserves distinct liveness/readiness responsibilities
- avoids exposing sensitive health information
- coordinates deployment probe requirements with `dev-devops`
- creates or updates appropriate observability tests
- produces structured evidence
- declares required Checks
- declares capability gaps
- escalates security/architecture/deployment concerns correctly

---

## Source

Authoritative standard:

`ES0901 - Estándar de Desarrollo - Agencia de Sistemas de Información - Version 6.3`

Primary references:

- Section 7.1 — Development Principles
- Section 11 — Non-Functional Requirements
- Annex IV — Health Checks

The authoritative source remains the original GCBA standard.

This Markdown file is the operational AI representation and must remain aligned with the source standard.
