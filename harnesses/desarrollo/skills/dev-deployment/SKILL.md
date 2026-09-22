---
name: dev-deployment
description: Use when a specific application version has to move from one GCBA / DGISIS environment to the next — promotion model, deployment ordering, configuration compatibility, migration safety, rollback viability, runtime readiness and the release evidence that has to stay traceable. It does not own the CI/CD pipeline, the environment values, the OpenShift internals or the migration implementation. Owned by dev-devops, entered through dev-devops-implementation.
---

# Skill: dev-deployment

## Purpose

Plan, validate, and execute application deployments across GCBA environments while preserving the approved artifact-promotion model, deployment ordering, configuration compatibility, migration safety, rollback viability, runtime readiness, and traceable release evidence.

This skill belongs to the `dev-devops` agent.

It specializes in the question:

> How should this specific application version move safely from one environment to another?

It does **not** own the full CI/CD pipeline, environment-value definition, OpenShift platform internals, application business logic, or database migration implementation.

---

## Owner

Primary owner:

`dev-devops`

Primary implementation entry point:

`dev-devops-implementation`

Related skills:

- `dev-environments`
- `dev-openshift`
- `dev-ci-cd`
- `dev-persistence`
- `dev-observability`
- `dev-quality-validation`
- `dev-security-analysis`
- `dev-architecture-analysis`
- `dev-backend-implementation`
- `dev-frontend-implementation`
- `dev-integration-implementation`

---

# Core Principle

The skill must answer:

> What exactly is being deployed, to which environment, in what order, with what prerequisites, with what migration/configuration compatibility, and how can the system recover if the deployment fails?

Apply this rule:

> A deployment is not only "run the pipeline." It is a controlled state transition from one known application/runtime state to another.

---

# Responsibility Boundaries

Use the following separation:

```text
dev-environments
→ defines what varies between DEV / QA / HML / PRD

dev-ci-cd
→ automates build, validation, artifact creation, promotion, and deployment flow

dev-openshift
→ owns OpenShift-specific runtime/platform configuration

dev-deployment
→ owns the deployment plan for a specific version/change
   including prerequisites, order, migrations, rollout, verification, and rollback
```

Related application responsibilities:

```text
dev-persistence
→ creates/version-controls migrations and seed mechanisms

dev-observability
→ application health endpoints and operational signals

dev-quality
→ quality acceptance/gates

dev-security
→ security acceptance/review

dev-architecture
→ architectural/topology decisions
```

---

# Normative Basis

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas:

```text
Section 10
→ continuous deployment requirement

Section 11
→ availability, runtime timeout, startup, scalability, maintainability

Annex III
→ OpenShift continuous delivery model
→ build once in QA and promote same image
→ external configuration per environment
→ migration mechanism
→ initial setup/deployment automation
→ VM/Cloud/SaaS deployment requirements

Annex IV
→ health check requirements used by deployment/runtime validation
```

The skill must preserve traceability to these sources when a normative requirement drives a deployment decision.

---

# Deployment Definition

A deployment is the controlled transition:

```text
CURRENT STATE
     ↓
new artifact/version
+ environment configuration
+ migration state
+ platform/runtime configuration
     ↓
TARGET STATE
```

A deployment must identify:

```text
artifact
target environment
configuration version/reference
migration version/reference
runtime/platform assumptions
health/readiness criteria
verification criteria
rollback strategy
evidence
```

---

# Mandatory Workflow

The skill must execute this sequence:

```text
1. Identify deployment target
2. Identify exact artifact/version
3. Resolve environment readiness
4. Resolve platform/runtime readiness
5. Resolve configuration compatibility
6. Resolve database migration requirements
7. Resolve deployment ordering
8. Resolve rollback strategy
9. Resolve health/readiness criteria
10. Resolve quality/security prerequisites
11. Execute or prepare rollout
12. Verify target state
13. Capture evidence
14. Decide COMPLETE / ROLLBACK_REQUIRED / BLOCKED
```

---

# Phase 1 — Identify Deployment Target

The deployment request must identify:

```text
application/component
version/artifact
source environment
target environment
deployment purpose
```

Example:

```yaml
deploymentTarget:
  component: ba-espacios-backend
  version: 2.4.0
  sourceEnvironment: QA
  targetEnvironment: HML
  purpose: release-validation
```

If the target environment is unclear:

return:

`DEPLOYMENT_TARGET_UNRESOLVED`

---

# Phase 2 — Resolve Artifact Identity

The deployed artifact must be uniquely identifiable.

Possible evidence:

```text
Git commit SHA
Git tag
container image digest
container image tag
package version
release identifier
```

Prefer immutable identity where the platform supports it.

Example:

```yaml
artifact:
  type: CONTAINER_IMAGE
  image: registry/project/app
  digest: sha256:...
  sourceCommit: ...
```

Do not deploy an ambiguous artifact such as:

```text
latest
current
whatever is in branch
```

without a deterministic resolution step.

If the artifact cannot be uniquely resolved:

return:

`DEPLOYMENT_ARTIFACT_UNRESOLVED`

---

# Build Once / Promote Same Artifact

For the OpenShift delivery model defined by ES0901 Annex III:

```text
QA
→ build artifact/image once

HML / PRD
→ promote the same image without modification
```

Environment-specific values are injected externally.

The deployment skill must verify:

```text
same artifact identity
same image digest or equivalent immutable package
different external configuration allowed
```

If HML/PRD requires rebuilding the application solely because the environment changed:

return:

`ARTIFACT_PROMOTION_MODEL_VIOLATION`

Coordinate with:

- `dev-environments`
- `dev-ci-cd`

---

# Phase 3 — Environment Readiness

Before deployment, consume the environment result from:

`dev-environments`

Required readiness may include:

```text
configuration contract complete
mandatory values resolved
secret references present
service mappings resolved
identity mappings resolved
database mapping resolved
cross-environment leakage absent
```

Do not deploy into an environment marked:

```text
NOT_CONFIGURED
PARTIAL
BLOCKED
```

unless the WorkUnit explicitly authorizes a controlled partial environment.

If environment configuration is incomplete:

return:

`ENVIRONMENT_NOT_READY`

---

# Phase 4 — Platform Readiness

The target runtime/platform must exist and be compatible with the release.

Possible prerequisites:

```text
OpenShift project/namespace
deployment resource
service/route
runtime image
ConfigMap references
Secret references
network access
database connectivity
provider connectivity
health-probe configuration
```

OpenShift-specific implementation belongs to:

`dev-openshift`

If platform resources/provisioning are not ready:

return:

`PLATFORM_NOT_READY`

---

# Pre-Deployment Checklist

Before rollout, produce a structured checklist.

Example:

```yaml
preDeployment:

  artifactResolved: true
  environmentReady: true
  platformReady: true
  configurationReady: true

  migrations:
    required: true
    strategyResolved: true

  health:
    endpointsAvailable: true
    probesConfigured: true

  qualityGate:
    passed: true

  securityGate:
    passed: true

  rollback:
    resolved: true
```

A checklist item may be:

```text
PASS
FAIL
NOT_APPLICABLE
PENDING
```

Do not collapse unknown into PASS.

---

# Quality and Security Prerequisites

Deployment may depend on configured acceptance gates.

Responsibility split:

```text
dev-quality
→ determines whether quality findings pass acceptance rules

dev-security
→ determines whether security findings pass acceptance rules

dev-deployment
→ refuses or blocks rollout when required gates are not satisfied
```

The deployment skill must not waive failed quality/security gates.

If a required gate is unresolved:

return:

`DEPLOYMENT_GATE_BLOCKED`

---

# Database Migration Boundary

Responsibilities:

```text
dev-persistence
→ defines migration scripts/artifacts using the approved migration mechanism

dev-deployment
→ decides when/how deployment invokes the approved migration sequence
```

The deployment skill must not invent schema changes.

It must inspect:

```text
migration required?
migration version?
forward-compatible?
backward-compatible?
data migration involved?
long-running?
destructive?
rollback possible?
```

If no approved migration artifact exists:

return:

`MIGRATION_ARTIFACT_MISSING`

---

# Migration Strategy

Possible deployment migration strategies may include:

```text
BEFORE_APPLICATION
DURING_DEPLOYMENT
AFTER_APPLICATION
EXPAND_THEN_CONTRACT
NOT_REQUIRED
```

The strategy must come from application architecture/migration evidence.

Do not choose based on preference alone.

If ordering cannot be proven safe:

return:

`MIGRATION_ORDER_UNRESOLVED`

---

# Backward Compatibility

For rolling or staged deployments, inspect whether:

```text
old application + new schema
new application + old schema
old and new application versions simultaneously
```

can coexist during rollout.

If coexistence is possible, document it.

If not, deployment strategy must explicitly account for it.

If compatibility is unclear:

return:

`DEPLOYMENT_COMPATIBILITY_UNRESOLVED`

---

# Destructive Migrations

Examples:

```text
drop column
drop table
rename without compatibility layer
irreversible data transformation
mass delete
```

These operations require explicit risk treatment.

The deployment skill must not execute destructive migration work silently.

Return:

`DESTRUCTIVE_MIGRATION_RISK`

and require the applicable human/risk gate.

---

# Data Migration

When deployment includes data transformation:

inspect:

```text
estimated volume
expected duration
locking behavior
rollback/recovery
restartability
idempotency
monitoring
```

If the operation may exceed normal deployment/runtime constraints:

return:

`DATA_MIGRATION_REVIEW_REQUIRED`

and coordinate with:

- `dev-persistence`
- `dev-architecture-analysis`
- `dev-quality-validation`

---

# Seed / Initial Data

Initial/reference data must use the approved automated mechanism when required.

Do not make production rollout depend on undocumented manual SQL/data edits.

If manual data setup is required:

return:

`MANUAL_INITIALIZATION_RISK`

---

# Deployment Ordering

A deployment plan must explicitly order dependent actions.

Example:

```text
1. validate target environment
2. validate secret/config references
3. execute compatible migration
4. deploy/promote application artifact
5. wait for startup
6. validate readiness
7. run smoke/integration validation
8. enable traffic / complete rollout
9. collect evidence
```

This is an example, not a universal order.

The real sequence must follow the application's compatibility requirements.

---

# Multi-Component Deployment

A WorkUnit may affect:

```text
backend
frontend
database
integration adapter
scheduled process
multiple services
```

If components must be coordinated, define dependency order.

Example:

```yaml
deploymentOrder:
  - database-compatible-expansion
  - provider-service
  - consumer-service
  - frontend
```

Do not assume repositories can deploy independently when the contract says otherwise.

If ordering across components is unclear:

return:

`MULTI_COMPONENT_ORDER_UNRESOLVED`

---

# API Compatibility During Deployment

When provider/consumer components deploy independently:

coordinate with:

- `dev-api`
- `dev-service-integration`

Avoid deployment sequences that temporarily break existing consumers.

If the deployment introduces a breaking API contract without a compatible transition:

return:

`BREAKING_CONTRACT_DEPLOYMENT_RISK`

---

# Feature Flags

If an approved feature flag already exists, deployment may use it to separate:

```text
code deployment
from
feature activation
```

The skill must not invent a feature-flag platform or strategy solely to simplify rollout.

When feature activation is separate, record:

```text
artifact deployed
feature disabled/enabled
activation owner
activation evidence
```

---

# Runtime Startup

For applicable OpenShift deployments, ES0901 defines a startup requirement under 60 seconds.

The deployment skill must measure or consume evidence of startup behavior.

Do not consider rollout healthy merely because a pod/container exists.

Check:

```text
started
liveness acceptable
readiness achieved
startup duration acceptable
```

If startup exceeds the applicable requirement:

return:

`STARTUP_TIME_RISK`

---

# Health and Readiness

Responsibility split:

```text
dev-observability
→ application health endpoint implementation

dev-openshift
→ platform probe configuration

dev-deployment
→ uses health/readiness results as rollout acceptance evidence
```

Deployment completion should require readiness where applicable.

Do not treat liveness alone as deployment success.

If readiness cannot be established:

return:

`DEPLOYMENT_READINESS_FAILED`

---

# Smoke Validation

After rollout, execute or request the minimum non-destructive validation appropriate for the WorkUnit.

Examples:

```text
application readiness
critical route reachable
basic authentication flow
service dependency reachable
critical API response
frontend loads
integration connectivity
```

The exact smoke test must come from project context.

Do not create arbitrary business transactions in production.

If a real validation would create side effects, use approved safe validation or require human approval.

---

# Production Safety

Production rollout is a high-impact action.

Production-impacting actions may include:

```text
deploy/promote artifact
execute migration
change route
change runtime configuration
scale/restart components
enable feature
rollback
```

The deployment skill must respect the Tool Risk Human Gate / configured production-approval policy.

It must never silently execute production changes.

---

# Rollout Strategies

The skill may work with an existing approved rollout strategy such as:

```text
rolling update
recreate
blue/green
canary
manual traffic switch
platform-native rollout
```

Do not introduce a new rollout strategy without architecture/platform approval.

If no rollout strategy can satisfy the application constraints:

return:

`ROLLOUT_STRATEGY_UNRESOLVED`

---

# Rollback Strategy

Rollback must be resolved before risky deployment execution.

A rollback plan should identify:

```text
previous artifact
previous configuration compatibility
migration rollback/recovery
traffic behavior
feature flag state
rollback trigger
rollback verification
```

Do not claim rollback is safe solely because an old image exists.

---

# Rollback Classification

Possible rollback states:

```text
SAFE
CONDITIONAL
FORWARD_FIX_ONLY
UNRESOLVED
```

## SAFE

Previous artifact/configuration can be restored without incompatible data/schema state.

## CONDITIONAL

Rollback requires specific data/schema/configuration steps.

## FORWARD_FIX_ONLY

Rollback cannot safely restore prior state; recovery requires a corrective forward deployment.

## UNRESOLVED

Evidence is insufficient.

If `UNRESOLVED` for a high-risk deployment:

return:

`ROLLBACK_RISK`

---

# Rollback Trigger

Define what should trigger rollback or deployment stop.

Examples:

```text
readiness never achieved
startup failure
critical smoke test failure
migration failure
critical dependency failure introduced by release
severe error-rate increase where observable
security/runtime failure
```

Do not invent numeric thresholds without project/platform evidence.

---

# Failed Migration

If migration fails:

```text
stop rollout
preserve evidence
determine database state
do not blindly rerun destructive/non-idempotent migration
```

Return:

`MIGRATION_FAILED`

The next action depends on migration idempotency and recovery design.

---

# Failed Rollout

If application rollout fails after migration succeeds:

the skill must determine whether:

```text
application can roll back
schema remains compatible
forward fix is required
```

Do not automatically deploy the previous artifact if its schema compatibility is unknown.

---

# Zero/Low Downtime Considerations

ES0901 expects 24x7 service availability for applicable applications.

The deployment plan should avoid unnecessary interruption where the approved architecture supports it.

This does not mean every deployment is automatically zero-downtime.

If downtime is unavoidable:

return:

`SERVICE_INTERRUPTION_REVIEW_REQUIRED`

and require the approved controlled-maintenance/business process.

---

# Deployment Freeze / Manual Constraints

If project governance defines:

```text
release windows
freeze periods
manual approvals
change tickets
production authorization
```

the deployment skill must consume those rules.

It must not invent organizational approval processes that are not present in context.

If a required organizational prerequisite is unknown:

return:

`DEPLOYMENT_GOVERNANCE_UNRESOLVED`

---

# Deployment Evidence

Collect non-sensitive evidence.

Expected evidence may include:

```text
commit SHA
tag/release
artifact/image digest
pipeline run identifier
source environment
target environment
configuration reference/version
migration version
deployment start/end
rollout result
readiness result
smoke-test result
rollback classification
human approvals
```

Never include secret values.

---

# Deployment State Model

Suggested deployment states:

```text
PLANNED
READY
APPROVAL_REQUIRED
DEPLOYING
VERIFYING
COMPLETE
BLOCKED
FAILED
ROLLBACK_REQUIRED
ROLLED_BACK
FORWARD_FIX_REQUIRED
```

The skill should report state explicitly.

---

# Idempotency

Repeated deployment execution must be considered.

Operations such as:

```text
promote same immutable artifact
apply declarative runtime config
```

may be naturally repeatable.

Operations such as:

```text
data migration
one-time seed
destructive change
manual external action
```

may not be.

Do not blindly rerun failed deployment steps.

If repeatability is unclear:

return:

`DEPLOYMENT_IDEMPOTENCY_RISK`

---

# Drift Detection

Before deployment, compare expected target state to current target state where capabilities allow.

Potential drift:

```text
different runtime configuration
manual platform modifications
unexpected image/version
missing probes
unexpected route
configuration key mismatch
```

If drift may invalidate the deployment plan:

return:

`TARGET_ENVIRONMENT_DRIFT`

Coordinate platform-specific drift with `dev-openshift`.

---

# Deployment Documentation

The deployment plan should be understandable by another engineer.

At minimum document:

```text
what is deployed
where
artifact identity
configuration assumptions
migration steps
order
verification
rollback
known risks
```

Avoid hidden operational knowledge.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search

artifact.inspect
artifact.promote

environment.config.inspect

deployment.state.inspect
deployment.execute
deployment.verify
deployment.rollback

migration.inspect
migration.execute

health.readiness.inspect
health.liveness.inspect

tests.smoke.run

gitlab.pipeline.inspect
gitlab.release.inspect
```

Depending on platform:

```text
openshift.rollout.inspect
openshift.rollout.execute
openshift.rollout.rollback
openshift.deployment.inspect
openshift.image.inspect
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If a required capability is unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

```text
artifact identity
artifact promotion consistency
environment readiness
configuration compatibility
migration compatibility
migration ordering
rollback viability
health/readiness
startup time
smoke validation
breaking-contract deployment
production approval
deployment evidence completeness
```

The skill must not self-approve formal Checks.

If unavailable:

return:

`CHECK_GAP`

---

# Result Statuses

Supported statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

DEPLOYMENT_TARGET_UNRESOLVED
DEPLOYMENT_ARTIFACT_UNRESOLVED
ENVIRONMENT_NOT_READY
PLATFORM_NOT_READY
DEPLOYMENT_GATE_BLOCKED

ARTIFACT_PROMOTION_MODEL_VIOLATION
TARGET_ENVIRONMENT_DRIFT

MIGRATION_ARTIFACT_MISSING
MIGRATION_ORDER_UNRESOLVED
MIGRATION_FAILED
DESTRUCTIVE_MIGRATION_RISK
DATA_MIGRATION_REVIEW_REQUIRED
MANUAL_INITIALIZATION_RISK

DEPLOYMENT_COMPATIBILITY_UNRESOLVED
MULTI_COMPONENT_ORDER_UNRESOLVED
BREAKING_CONTRACT_DEPLOYMENT_RISK

ROLLOUT_STRATEGY_UNRESOLVED
DEPLOYMENT_READINESS_FAILED
STARTUP_TIME_RISK

ROLLBACK_RISK
ROLLBACK_REQUIRED
FORWARD_FIX_REQUIRED
DEPLOYMENT_IDEMPOTENCY_RISK

SERVICE_INTERRUPTION_REVIEW_REQUIRED
DEPLOYMENT_GOVERNANCE_UNRESOLVED

ARCHITECTURE_REVIEW_REQUIRED
SECURITY_REVIEW_REQUIRED
QUALITY_REVIEW_REQUIRED
DEVOPS_CHANGE_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

Return a structured deployment result.

Example:

```yaml
deploymentResult:

  status: COMPLETE
  state: COMPLETE

  target:
    component: sistema-backend
    sourceEnvironment: QA
    targetEnvironment: HML

  artifact:
    type: CONTAINER_IMAGE
    version: 2.4.0
    digest: sha256:...
    sourceCommit: ...
    immutable: true
    sameArtifactPromoted: true

  environment:
    readiness: READY_FOR_DEPLOYMENT
    configurationCompatible: true

  platform:
    readiness: READY

  gates:
    quality: PASS
    security: PASS
    humanApproval: NOT_REQUIRED

  migration:
    required: true
    version: V042
    strategy: BEFORE_APPLICATION
    backwardCompatibility: true
    execution: PASS

  rollout:
    strategy: PLATFORM_NATIVE_ROLLING
    execution: PASS

  health:
    startup: PASS
    liveness: PASS
    readiness: PASS

  validation:
    smoke: PASS
    nonRegression: PASS

  rollback:
    classification: SAFE
    previousArtifact: sha256:...
    tested: false

  evidence:
    - pipeline-run-...
    - deployment-...
    - migration-...
    - readiness-...

  risks: []
  assumptions: []
```

---

# Model Routing Metadata

This skill may emit complexity signals to `automatic-consumption`.

It does not choose the final model.

## STANDARD

Use for:

```text
promoting an already validated immutable artifact
simple non-migration deployment
straightforward environment promotion
standard health/readiness validation
release evidence collection
```

## REASONING

Consider when:

```text
schema migration exists
multiple components deploy together
rollback compatibility is uncertain
artifact/configuration compatibility is complex
breaking-contract risk exists
environment drift exists
rollout sequencing matters
service interruption risk exists
```

## PREMIUM

Consider only when:

```text
high-risk production migration
irreversible data transformation
critical multi-system deployment
complex rollback/forward-fix analysis
major shared-service release
repeated reasoning attempts fail
```

Premium execution must pass the orchestrator's Human Model Gate.

Production-impacting Tool execution must independently pass the Tool Risk Human Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- deployment target/artifact is unresolved
- environment or platform is not ready
- a quality/security gate is blocked
- artifact promotion violates the approved model
- migration artifact/order is unresolved
- destructive migration is involved
- rollback is unresolved
- deployment affects multiple tightly coupled components
- a breaking contract may be introduced
- production approval is required
- service interruption is expected
- environment drift invalidates assumptions
- a required capability is unavailable
- a required Check is unavailable

---

# Prohibited Behavior

This skill must not:

- deploy an ambiguous artifact
- rebuild HML/PRD artifacts when the approved model requires immutable promotion
- deploy into an environment with unresolved mandatory configuration
- invent migration SQL/schema changes
- execute destructive migrations silently
- assume migration rollback exists
- rerun failed non-idempotent migrations blindly
- declare rollback safe solely because a previous image exists
- change rollout strategy without approval
- deploy breaking API changes without transition analysis
- bypass quality/security gates
- execute production changes without required human approval
- treat liveness alone as deployment success
- claim deployment success before readiness/verification
- invent smoke-test business actions in production
- hide environment drift
- create Tools directly
- self-approve formal Checks
- bypass Policies

---

# Evidence Requirements

The result must distinguish:

```text
normative requirement
artifact evidence
environment evidence
platform evidence
migration evidence
quality/security gate evidence
rollout evidence
health/readiness evidence
smoke-test evidence
rollback evidence
human approval evidence
assumptions
risks
open decisions
```

All meaningful decisions should be traceable to one or more of:

- WorkUnit
- Jira / Ficha de Proyecto
- Git commit/tag/release
- immutable artifact/image reference
- `dev-environments` result
- platform/OpenShift state
- migration artifact
- GitLab pipeline/release
- quality result
- security result
- ES0901
- deployment verification result

---

# Success Criteria

This skill is successful when it:

- resolves the exact artifact and target environment
- confirms environment/platform readiness
- preserves the build-once/promote model where applicable
- validates configuration compatibility
- coordinates migrations without owning migration implementation
- defines safe deployment ordering
- evaluates old/new schema and application compatibility
- identifies destructive/data-migration risk
- defines rollout strategy from approved project/platform behavior
- uses readiness as deployment acceptance evidence
- performs safe smoke validation
- resolves rollback or explicitly declares forward-fix-only behavior
- blocks unsafe production operations
- captures complete non-sensitive release evidence
- returns a structured deployment state to the orchestrator

---

# Source References

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Key source areas:

```text
10
→ continuous deployment

11
→ availability, startup, timeout, scalability, maintainability

Annex III
→ build once in QA
→ promote same image to HML/PRD
→ external configuration
→ migrations
→ automated deployment requirements
→ OpenShift / VM / Cloud / SaaS deployment models

Annex IV
→ liveness/readiness/startup health behavior used by rollout validation
```

Examples in ES0901 must not be converted into application-specific deployment values without project evidence.
