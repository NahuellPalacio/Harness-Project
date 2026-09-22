---
name: dev-devops-implementation
description: Use when a WorkUnit turns an approved application design into how it is delivered and run on a GCBA / DGISIS project — deployment model, environment separation, externalized configuration, delivery pipeline, OpenShift runtime requirements, health probes and reproducibility — without taking over development, security, quality or architecture decisions. Routes the detail to dev-environments, dev-deployment, dev-openshift and dev-ci-cd, which specialize the flow without replacing it. Primary implementation skill of the dev-devops agent.
---

# Skill: dev-devops-implementation

## Purpose

Implement and coordinate DevOps WorkUnits for GCBA applications while preserving the approved deployment model, environment separation, configuration externalization, delivery pipeline, OpenShift runtime requirements, health-probe integration, reproducibility, and operational safety.

This is the **primary implementation skill** of the `dev-devops` agent.

Its responsibility is not to replace application development, security, quality, or architecture.

Its responsibility is to translate an approved application/runtime design into a reproducible and environment-aware delivery/runtime configuration.

---

## Owner

Primary owner:

`dev-devops`

Related skills:

- `dev-environments`
- `dev-deployment`
- `dev-openshift`
- `dev-observability`
- `dev-persistence`
- `dev-architecture-analysis`
- `dev-security-analysis`
- `dev-quality-validation`
- `dev-backend-implementation`
- `dev-frontend-implementation`
- `dev-integration-implementation`

Current specialized DevOps skills:

- `dev-environments`
- `dev-deployment`
- `dev-openshift`
- `dev-ci-cd`

These skills specialize the main DevOps implementation flow without replacing the responsibilities of `dev-devops-implementation`.

---

# Core Principle

The skill must answer:

> How can this application be built, configured, promoted, deployed, and operated across GCBA environments in a reproducible way without embedding environment-specific state into the application artifact?

Apply this principle:

> Build once when the platform model requires it, externalize environment configuration, automate repeatable operations, preserve platform/runtime constraints, and never hide deployment assumptions inside application code.

---

# Normative Basis

Primary normative source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas include:

- approved tools and versions
- Git/GitLab delivery practices
- non-functional requirements
- Annex III — Continuous Deployment
- Annex IV — Health Check requirements
- configuration externalization requirements
- OpenShift runtime constraints
- infrastructure and deployment automation requirements

This skill must preserve source traceability when enforcing a normative rule.

Example:

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "Annex III"
  rule: "build-once / promote with external configuration"
```

---

# Responsibility

`dev-devops-implementation` owns WorkUnits involving:

```text
deployment configuration
environment configuration
pipeline configuration
build and promotion flow
OpenShift runtime configuration
ConfigMaps / runtime configuration references
Secret references / runtime injection
health probe platform configuration
container/runtime constraints
release/deployment automation
environment promotion
deployment reproducibility
runtime variable documentation
platform-facing migration execution coordination
infrastructure-as-code handoff/implementation when applicable
deployment evidence
```

---

# What This Skill Does Not Own

This skill does not own:

```text
application business logic
API contract design
database conceptual modeling
migration definition/business schema logic
application health endpoint implementation
application logging implementation
security approval
quality acceptance
architecture redesign
secret values
manual credential management
```

Use:

```text
dev-observability
→ application health endpoints and logging behavior

dev-persistence
→ migration definition and schema evolution implementation

dev-security-analysis
→ security review

dev-quality-validation
→ quality gates and validation

dev-architecture-analysis
→ architecture/platform topology decisions
```

---

# Mandatory Workflow

The skill must execute this sequence:

```text
1. Inspect deployment/runtime context
2. Classify target platform
3. Resolve environment model
4. Inspect current pipeline/deployment assets
5. Resolve artifact/build strategy
6. Resolve external configuration
7. Resolve secret references
8. Resolve storage/runtime constraints
9. Resolve health-probe integration
10. Resolve migration/seeding execution
11. Resolve scaling/startup/runtime constraints
12. Implement minimum deployment change
13. Validate pipeline/deployment syntax and behavior
14. Validate environment promotion assumptions
15. Collect deployment evidence
16. Return structured result
```

---

# Platform Classification

Classify the target runtime before implementation.

Supported conceptual types:

```text
OPENSHIFT
VIRTUAL_MACHINE
CLOUD_PAAS
SAAS_CUSTOMIZATION
OTHER_APPROVED_PLATFORM
```

If the target runtime is unclear:

return:

`DEPLOYMENT_PLATFORM_UNRESOLVED`

Do not assume OpenShift when the project explicitly uses an approved exception/platform.

---

# OpenShift as the Primary On-Premise Delivery Model

ES0901 Annex III defines OpenShift Continuous Delivery as the expected model for on-premise GCBA systems.

The documented environments include:

```text
Development
Quality
Homologation
Internal Production
DMZ Production
```

Project naming may use equivalent identifiers such as:

```text
DEV
QA
HML
PRD
```

The skill must map project names to actual platform environments rather than assuming names are identical.

---

# Build Once / Promote Artifact

For the documented OpenShift delivery model, ES0901 defines a build-once approach:

```text
build in QA
      ↓
produce immutable application image/artifact
      ↓
promote same image
      ↓
HML / Production
      ↓
inject environment-specific configuration externally
```

The skill must detect violations such as:

```text
rebuilding different source for HML
rebuilding different source for production
changing application artifact per environment
embedding environment values into the promoted image
```

If the project uses the ES0901 OpenShift model and rebuilds per environment without an approved exception:

return:

`ARTIFACT_PROMOTION_MODEL_VIOLATION`

---

# Environment Configuration

Application configuration must remain external to application code when environment-specific.

Typical configuration includes:

```text
database host
database port
database schema
service URLs
external provider URLs
feature/environment switches
runtime parameters
health-probe timing configuration
non-secret integration identifiers
```

The exact mechanism depends on the runtime.

Possible platform mechanisms may include:

```text
ConfigMaps
Secrets
environment variables
approved runtime configuration files
```

Do not hardcode environment-specific values into source code or promoted artifacts.

If detected:

return:

`ENVIRONMENT_CONFIGURATION_RISK`

---

# Configuration Manifest and Documentation

For the deployment models covered by ES0901 Annex III, environment variables/configuration must be explicitly documented.

Where the standard requires a YAML configuration file and README reference, the skill must verify:

```text
configuration manifest exists
variables are declared
path/location is documented
environment-specific values are not embedded in source
```

If required configuration documentation is missing:

return:

`ENVIRONMENT_CONFIGURATION_DOCUMENTATION_MISSING`

---

# Secrets

This skill manages **references and runtime injection**, not secret values.

The skill must never:

```text
create real production secrets from guesses
hardcode secrets
write tokens/passwords into repository files
print secret values
copy secrets between environments
store secrets in generated documentation
return secret values in results
```

Expected conceptual flow:

```text
application
   ↓ references secret name/key
runtime/platform
   ↓ injects secret
SecretStore / approved secret mechanism
```

If secret material is found in source/deployment files:

return:

`SECRET_EXPOSURE_RISK`

and request:

`SECURITY_REVIEW_REQUIRED`

---

# Environment Isolation

Each environment must have independently controlled runtime configuration.

Do not assume:

```text
DEV configuration == QA configuration
QA credentials == HML credentials
HML endpoints == PRD endpoints
```

The same promoted artifact may be used, but configuration must remain environment-specific.

If lower-environment credentials/endpoints are reused in production without explicit approved evidence:

return:

`CROSS_ENVIRONMENT_CONFIGURATION_RISK`

---

# OpenShift Ephemeral Runtime

ES0901 Annex III explicitly states that local persistent storage must not be used in the OpenShift model because containers are ephemeral.

Therefore:

```text
persistent application data
→ must not depend on container-local filesystem
```

If persistent local storage is detected:

return:

`LOCAL_PERSISTENT_STORAGE_VIOLATION`

Coordinate application file behavior with:

`dev-storage`

---

# Dependency / Build Manifest

The deployment repository must contain the technology-appropriate dependency/build manifest required by the project/runtime.

Examples documented by ES0901 include:

```text
PHP / Laravel → composer.json
Node.js       → package.json
Java          → pom.xml
```

Do not generalize these examples to every technology without checking the approved stack.

If the expected build/dependency manifest is missing:

return:

`BUILD_MANIFEST_MISSING`

---

# Approved Technology / Runtime Compatibility

The project technology and runtime must align with approved/homologated versions where required.

Do not silently upgrade/downgrade runtimes during unrelated DevOps WorkUnits.

If the deployment requires a non-approved or incompatible runtime/image:

return:

`RUNTIME_VERSION_REVIEW_REQUIRED`

Coordinate normative version validation with the appropriate Policy/Check.

---

# Build / Pipeline

Inspect the existing pipeline before changing it.

Possible stages may include:

```text
fetch
compile/build
lint
tests
package
static analysis
security scans
image build
publish
deploy/promote
```

Do not assume a fixed stage list.

Preserve the project's approved pipeline conventions.

Do not bypass existing tests/scans merely to make a deployment succeed.

If a pipeline stage fails:

return the actual failure and evidence.

Do not silently set quality/security gates to ignored unless the project policy explicitly allows it.

---

# GitLab Boundary

GitLab is the source/version-control and delivery integration surface used by the harness.

This skill may:

```text
inspect pipeline configuration
modify approved pipeline configuration
inspect tags/releases
prepare deployment metadata
collect pipeline evidence
```

It must not invent organizational GitLab policies.

Versioning, branch, and release behavior must follow the current project/standard configuration.

---

# Release / Version Evidence

When a WorkUnit changes deployment/release behavior, collect evidence such as:

```text
commit SHA
tag/version
artifact/image identifier
pipeline run identifier
target environment
deployment result
configuration version/reference
migration version/reference
```

Do not treat "pipeline succeeded" as proof that application behavior is correct.

That belongs to quality/integration validation.

---

# Health Checks — Responsibility Split

This boundary is mandatory.

```text
dev-observability
→ implements and validates application health endpoints

dev-devops
→ configures platform probes to consume those endpoints/mechanisms
```

For HTTP applications, ES0901 requires application endpoints:

```text
/health/liveness
/health/readiness
```

and recommends:

```text
/health
```

The startup probe is optional and should be considered for applications with slow startup behavior.

`dev-devops-implementation` must not implement application endpoint business logic itself.

If required endpoints are missing:

return:

`HEALTH_ENDPOINT_REQUIRED`

and delegate to:

`dev-observability`

---

# Health Probe Semantics

Platform probe configuration must preserve the intended responsibilities:

```text
Liveness
→ determines whether the application process is unhealthy/stuck and may need restart

Readiness
→ determines whether the application can safely receive traffic

Startup
→ optional protection for applications with slow startup
```

Do not configure liveness to depend on every secondary dependency.

Do not make liveness and readiness identical without evidence.

If probe responsibilities are mixed:

return:

`HEALTH_PROBE_RESPONSIBILITY_MIXED`

---

# Health Probe Parameters

For configured probes, resolve and document values such as:

```text
path / method
port
initialDelaySeconds
timeoutSeconds
periodSeconds
successThreshold
failureThreshold
```

Values must be justified by actual application characteristics.

Do not copy sample values from the standard as universal production values.

The standard's YAML is an example, not an application-specific tuning mandate.

If realistic values cannot be determined:

return:

`HEALTH_PROBE_CONFIGURATION_UNRESOLVED`

Coordinate startup characteristics with the development team and `dev-observability`.

---

# Health Check Security

Health endpoints/probe responses must not expose sensitive information.

If sensitive information is exposed:

return:

`HEALTH_SENSITIVE_DATA_EXPOSURE`

and request:

`SECURITY_REVIEW_REQUIRED`

---

# Startup Time

ES0901 non-functional requirements state that applications on the relevant OpenShift platform must complete startup in less than 60 seconds.

The skill must evaluate deployment/runtime evidence against that requirement when applicable.

If startup exceeds the platform requirement:

return:

`STARTUP_TIME_RISK`

A startup probe does not automatically waive platform startup requirements.

---

# Request Timeout / Runtime Constraint

ES0901 states that exposed requests/services on the relevant OpenShift platform must respond within 30 seconds because the platform may terminate longer requests.

The DevOps skill must identify when runtime/platform behavior conflicts with an application flow.

It must not redesign the application by itself.

If an operation requires more than the platform limit:

return:

`PLATFORM_TIMEOUT_RISK`

and escalate to:

`dev-architecture-analysis`

or the owning implementation agent to consider an approved asynchronous design.

---

# Horizontal Scaling and Stateless Runtime

ES0901 requires horizontal scalability according to the architecture, including stateless/granjable application behavior for applicable systems.

The DevOps skill must inspect whether deployment configuration assumes:

```text
single replica state
local session dependency
local persistent data
node-specific behavior
```

If runtime configuration conflicts with required horizontal scaling/statelessness:

return:

`STATEFUL_RUNTIME_RISK`

Coordinate application changes with the appropriate implementation/architecture skill.

---

# Availability

ES0901 defines 24x7 availability expectations for applicable applications.

The skill must preserve deployment practices that avoid unnecessary service interruption where the approved architecture supports that behavior.

Do not invent high-availability topology.

If the WorkUnit requires a new HA/topology decision:

return:

`ARCHITECTURE_REVIEW_REQUIRED`

---

# Database Migration Boundary

The responsibilities are separated:

```text
dev-persistence
→ defines and implements versioned schema migrations / seed mechanisms

dev-devops
→ ensures the approved migration mechanism can be executed reproducibly in the deployment flow
```

ES0901 favors framework/approved migration mechanisms rather than unmanaged/manual database scripts.

The DevOps skill must not create ad hoc schema SQL to bypass the migration system.

If deployment depends on unmanaged/manual schema execution:

return:

`MIGRATION_EXECUTION_POLICY_RISK`

---

# Initial Data / Seed

Where initial data is required, ES0901 expects an automated mechanism such as migrators/seeders rather than manual setup.

The exact data definition belongs to the application/persistence domain.

The DevOps skill validates that the deployment process can execute the approved automated mechanism.

If initial setup requires undocumented manual data manipulation:

return:

`MANUAL_INITIALIZATION_RISK`

---

# Migration Ordering

When application deployment and schema migration must occur together, determine:

```text
migration before deploy?
migration during deploy?
migration after deploy?
backward compatibility required?
rollback implications?
```

Do not invent ordering when the project has no approved migration strategy.

If deployment compatibility cannot be guaranteed:

return:

`MIGRATION_ORDER_UNRESOLVED`

and coordinate with:

- `dev-persistence`
- `dev-architecture-analysis` when needed

---

# Rollback

The skill must identify whether deployment rollback is technically possible.

Evidence may include:

```text
previous immutable image
previous release version
configuration compatibility
migration backward compatibility
feature-toggle strategy already approved
```

Do not claim rollback is safe when irreversible schema/data changes exist.

If rollback safety is unclear:

return:

`ROLLBACK_RISK`

---

# OpenShift Setup Boundary

ES0901 describes initial OpenShift setup activities performed by GCBA with collaboration from the development team, including:

```text
project creation
configuration repository creation
S2I image selection
pipeline configuration
users/roles in development environment
```

The skill must distinguish:

```text
team-controlled repository changes
vs
platform/organizational provisioning
```

If the harness lacks permissions/capability to perform platform provisioning:

return:

`PLATFORM_PROVISIONING_REQUIRED`

Do not attempt to bypass missing organizational permissions.

---

# S2I / Container Image

Use the approved image/build strategy already defined for the project/platform.

Do not invent or replace the base/S2I image during unrelated WorkUnits.

If no compatible approved image/runtime can be resolved:

return:

`RUNTIME_IMAGE_UNRESOLVED`

---

# Virtual Machine Deployments

ES0901 permits virtualized environments only when OpenShift is not feasible, with prior agreement and justification.

For a VM deployment, verify the applicable requirements such as:

```text
externalized YAML/environment configuration
README path documentation
parameterized installation automation
Ansible-based installation where required by the standard
development-environment validation
```

Do not choose VM deployment merely because it appears simpler.

If OpenShift is being bypassed without documented justification:

return:

`DEPLOYMENT_PLATFORM_POLICY_RISK`

---

# Cloud PaaS

For applicable Cloud/PaaS implementations, ES0901 requires automation of infrastructure and code deployment.

The standard identifies:

```text
source/scripts delivered in Git
infrastructure/services defined as code
Terraform or CloudFormation as documented options
Ansible for code implementation/deployment automation
external environment configuration
automated initial data mechanism
```

Treat tool names as normative only where the current standard/project actually requires them.

Do not generalize cloud tooling to OpenShift/on-premise WorkUnits unless applicable.

---

# SaaS Customization

For SaaS customization, the standard requires a process to update all environments and documentation/scripts/configuration necessary to recreate/update the environment.

This is distinct from consuming an external SaaS API.

External API consumption belongs to:

`dev-external-integration`

SaaS environment customization/deployment belongs here when explicitly part of the WorkUnit.

---

# Infrastructure as Code

Infrastructure/runtime changes should be reproducible and version-controlled where the applicable platform model requires it.

Do not make undocumented manual platform changes when an automated/configuration-as-code mechanism is expected.

If a required runtime change exists only as a manual console action:

return:

`UNMANAGED_INFRASTRUCTURE_CHANGE`

unless the platform process explicitly defines the manual action as organizational provisioning.

---

# CI/CD vs Quality/Security

The pipeline may execute:

```text
tests
linters
static analysis
security scans
dependency scans
DAST/SAST
```

Responsibility boundaries:

```text
dev-devops
→ integrates/configures the pipeline execution path

dev-quality
→ owns quality interpretation/gates

dev-security
→ owns security interpretation/acceptance
```

The DevOps skill must not self-approve failed quality/security findings.

---

# Deployment Evidence

Every completed deployment-related WorkUnit should return material evidence where available.

Examples:

```text
pipeline configuration diff
pipeline run
artifact/image identifier
deployment manifest/configuration diff
target environment
probe configuration
configuration keys
migration reference
deployment result
rollback reference
```

Do not include secret values.

---

# Required Capabilities

Typical capabilities include:

```text
repository.read
repository.search
repository.write

gitlab.pipeline.inspect
gitlab.pipeline.modify
gitlab.pipeline.run

deployment.config.inspect
deployment.config.modify

environment.config.inspect

runtime.manifest.inspect
runtime.manifest.modify

health.probe.inspect
health.probe.configure

tests.run
```

Depending on platform:

```text
openshift.project.inspect
openshift.deployment.inspect
openshift.route.inspect
openshift.configmap.inspect
openshift.secret.reference.inspect
openshift.rollout.inspect

iac.inspect
iac.validate

ansible.inspect
ansible.validate
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If a required capability is unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential required Checks include:

```text
environment configuration externalization
secret exposure
cross-environment configuration
deployment manifest validity
approved runtime/version
build manifest presence
artifact promotion consistency
local persistent storage
health probe presence
health probe responsibility
health sensitive-data exposure
startup-time requirement
platform request-timeout risk
migration execution policy
pipeline validation
infrastructure-as-code validation
deployment non-regression
```

The skill must not self-approve official Checks.

If a required Check is missing:

return:

`CHECK_GAP`

---

# Result Statuses

Supported result statuses include:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

DEPLOYMENT_PLATFORM_UNRESOLVED
DEPLOYMENT_PLATFORM_POLICY_RISK

ARTIFACT_PROMOTION_MODEL_VIOLATION

ENVIRONMENT_CONFIGURATION_RISK
ENVIRONMENT_CONFIGURATION_DOCUMENTATION_MISSING
CROSS_ENVIRONMENT_CONFIGURATION_RISK
SECRET_EXPOSURE_RISK

LOCAL_PERSISTENT_STORAGE_VIOLATION
BUILD_MANIFEST_MISSING
RUNTIME_VERSION_REVIEW_REQUIRED
RUNTIME_IMAGE_UNRESOLVED

HEALTH_ENDPOINT_REQUIRED
HEALTH_PROBE_RESPONSIBILITY_MIXED
HEALTH_PROBE_CONFIGURATION_UNRESOLVED
HEALTH_SENSITIVE_DATA_EXPOSURE

STARTUP_TIME_RISK
PLATFORM_TIMEOUT_RISK
STATEFUL_RUNTIME_RISK

MIGRATION_EXECUTION_POLICY_RISK
MANUAL_INITIALIZATION_RISK
MIGRATION_ORDER_UNRESOLVED
ROLLBACK_RISK

PLATFORM_PROVISIONING_REQUIRED
UNMANAGED_INFRASTRUCTURE_CHANGE

ARCHITECTURE_REVIEW_REQUIRED
SECURITY_REVIEW_REQUIRED
QUALITY_REVIEW_REQUIRED

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
devopsResult:

  status: COMPLETE

  workUnit:
    id: WU-123

  platform:
    type: OPENSHIFT
    validated: true

  environments:
    model:
      - DEV
      - QA
      - HML
      - PRD
    externalConfiguration: true
    crossEnvironmentLeakageDetected: false

  artifact:
    strategy: BUILD_ONCE_PROMOTE
    sourceEnvironment: QA
    immutablePromotion: true
    identifier: "image@sha256:..."

  configuration:
    manifestPresent: true
    readmeDocumented: true
    secretsExternalized: true

  runtime:
    localPersistentStorageDetected: false
    horizontalScaleCompatible: true
    startupRequirementSatisfied: true

  health:
    livenessEndpointAvailable: true
    readinessEndpointAvailable: true

    livenessProbe:
      configured: true

    readinessProbe:
      configured: true

    startupProbe:
      required: false
      configured: false

    responsibilitiesSeparated: true

  database:
    migrationMechanism: FRAMEWORK_MANAGED
    deploymentExecutionAutomated: true
    migrationOrderResolved: true
    rollbackRisk: LOW

  pipeline:
    validated: true
    testsIntegrated: true
    qualityStagesPresent: true
    securityStagesPresent: true

  deployment:
    targetEnvironment: QA
    validated: true

  reviews:
    architectureRequired: false
    securityRequired: false
    qualityRequired: false

  requiredCapabilities:
    - repository.read
    - deployment.config.inspect
    - gitlab.pipeline.inspect
    - health.probe.inspect

  requiredChecks:
    - environment-config-externalization
    - secret-exposure
    - artifact-promotion
    - health-probes
    - local-storage

  risks: []
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

## LOW_COST / STANDARD

Use for:

- inspecting manifests
- checking environment variables
- simple pipeline changes
- adding documented probe configuration
- repository/configuration validation
- deterministic YAML/config changes
- straightforward deployment metadata updates

## REASONING

Consider when:

- deployment model is ambiguous
- multiple environments diverge
- pipeline promotion behavior is complex
- migration ordering is risky
- rollback compatibility is unclear
- health-probe tuning requires cross-component analysis
- stateful application behavior conflicts with horizontal scaling
- VM/cloud/OpenShift exception paths must be evaluated
- multiple deployment repositories/components are affected

## PREMIUM

Consider only when:

- critical production deployment topology changes
- major platform migration is required
- rollback/data migration risk is high
- security/platform constraints are unusually complex
- multiple critical systems share deployment infrastructure
- repeated lower-tier reasoning attempts fail

Premium execution must pass the orchestrator's Human Model Gate.

Tool-risk approval remains separate from model-cost approval.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- target platform is unresolved
- project attempts to bypass the approved deployment model
- artifact promotion strategy conflicts with the standard
- environment configuration is unsafe
- secret exposure is detected
- required health endpoints are missing
- runtime violates startup/timeout/scaling requirements
- migration ordering or rollback is unresolved
- platform provisioning is required
- architecture must change
- security review is required
- quality review is required
- a required capability is unavailable
- a required Check is unavailable
- a production-impacting action needs approval

---

# Production Safety

Production-impacting operations must not be executed silently.

Examples:

```text
production rollout
production rollback
production secret reference change
production route change
production scaling/topology change
production migration execution
production destructive platform operation
```

The orchestrator/Tool Risk policy determines the required human approval.

This skill must never bypass that gate.

---

# Prohibited Behavior

This skill must not:

- hardcode environment-specific configuration into application code
- hardcode secrets
- copy lower-environment secrets to production
- rebuild environment-specific application artifacts when the approved model requires promotion
- use persistent container-local storage in OpenShift
- invent health endpoints
- implement application health logic that belongs to dev-observability
- copy sample probe thresholds as universal production values
- make liveness depend on every external dependency
- bypass failed quality/security stages without policy evidence
- create ad hoc database schema scripts to bypass approved migrations
- invent migration ordering
- claim rollback safety without evidence
- manually mutate infrastructure when reproducible configuration is required
- bypass OpenShift without documented justification
- silently change application architecture
- silently introduce cloud/IaC tooling where not applicable
- create Tools directly
- self-approve official Checks
- self-approve security findings
- self-approve quality acceptance
- bypass Policies
- invent missing project/platform context

---

# Evidence Requirements

The result must distinguish:

```text
normative requirement
project configuration
current repository evidence
pipeline evidence
platform evidence
environment evidence
deployment evidence
application evidence
assumptions
open decisions
risks
formal reviews required
```

All meaningful deployment decisions should be traceable to one or more of:

- WorkUnit
- Jira / Ficha de Proyecto
- repository code/configuration
- GitLab pipeline
- deployment manifests
- current OpenShift/platform configuration
- ADR
- ES0901 source rule
- environment evidence
- pipeline/deployment result
- specialist skill result

---

# Success Criteria

This skill is successful when it:

- identifies the real deployment platform
- preserves the approved build/promotion model
- externalizes environment configuration
- keeps secrets outside source and generated output
- preserves environment isolation
- avoids local persistent storage on ephemeral runtimes
- validates required build/dependency manifests
- keeps runtime versions aligned with approved project constraints
- configures health probes against application-owned health endpoints
- preserves liveness/readiness responsibility separation
- evaluates startup, request-timeout, scaling, and statelessness constraints
- coordinates migrations/seeding without bypassing the application migration mechanism
- identifies rollback risk
- preserves reproducible pipeline/deployment behavior
- distinguishes platform provisioning from repository-controlled changes
- collects non-sensitive deployment evidence
- escalates architecture/security/quality concerns instead of self-approving them
- returns a structured result to the orchestrator

---

# Source References

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Key source areas:

```text
6.10
→ approved tools and versions

11
→ non-functional/runtime requirements

Annex I
→ Git / GitLab and delivery-related quality/security tooling

Annex III
→ continuous deployment, OpenShift, environment configuration,
   build/promotion model, migrations, VM/Cloud/SaaS deployment requirements

Annex IV
→ liveness, readiness, startup probe, endpoint and probe configuration requirements
```

This skill must not convert examples in the standard into universal application-specific parameter values.
