---
name: dev-ci-cd
description: Use when the delivery pipeline of a GCBA / DGISIS application has to be designed, fixed or reviewed — how a source change gets built, tested, analysed, packaged, promoted and handed to the approved deployment flow, repeatably and traceably, without any stage bypassing a quality, security, environment or deployment control. It does not own application code, environment values, deployment ordering, OpenShift semantics or the acceptance decisions themselves. Owned by dev-devops, entered through dev-devops-implementation.
---

# Skill: dev-ci-cd

## Purpose

Design, validate, and maintain CI/CD automation for GCBA applications so that source changes are built, tested, analyzed, packaged, promoted, and deployed through repeatable and traceable delivery pipelines without bypassing quality, security, environment, or deployment controls.

This skill belongs to the `dev-devops` agent.

It specializes in the question:

> How should the delivery pipeline automate the path from source code to a deployable/promotable artifact and then invoke the approved deployment flow?

This skill does not own application code, environment values, release-specific deployment ordering, OpenShift platform semantics, quality acceptance, or security acceptance.

---

## Owner

Primary owner:

`dev-devops`

Primary implementation entry point:

`dev-devops-implementation`

Related skills:

- `dev-environments`
- `dev-deployment`
- `dev-openshift`
- `dev-quality-validation`
- `dev-security-analysis`
- `dev-observability`
- `dev-persistence`
- `dev-architecture-analysis`

---

# Core Principle

> The pipeline automates the delivery process; it must not redefine the rules that quality, security, architecture, environment, or deployment already own.

The skill must answer:

> What pipeline stages are required, what each stage proves, what artifact is produced, what gates must block promotion, and how does the pipeline hand off safely to deployment?

---

# Normative Basis

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas include:

```text
Annex I
→ Git / GitLab workflow
→ merge requests
→ static analysis / quality tooling
→ delivery-related controls

Annex II
→ approved tools and versions

Annex III
→ continuous deployment
→ OpenShift build/promotion model
→ configuration outside the artifact
→ automated migrations / initialization where applicable
→ reproducible deployment
```

The skill must preserve traceability when a pipeline rule is derived from the standard.

---

# Responsibility Boundaries

Use the following separation:

```text
dev-ci-cd
→ automates build, test, analysis, package, promotion, and deployment invocation

dev-deployment
→ owns the deployment plan for a concrete release/version

dev-environments
→ owns environment-specific configuration contract and mapping

dev-openshift
→ owns OpenShift-specific platform operations

dev-quality
→ interprets quality results and acceptance

dev-security
→ interprets security results and acceptance

dev-persistence
→ owns migration artifacts

dev-observability
→ owns application health/logging behavior
```

---

# Scope

This skill may own:

```text
pipeline definition
stage ordering
job dependencies
build automation
test execution
lint/static analysis execution
artifact creation
container image build
artifact publication
artifact immutability
pipeline variables/references
quality/security stage integration
migration job integration
promotion jobs
deployment job invocation
manual approval stages
release evidence
pipeline failure propagation
pipeline reproducibility
```

---

# Out of Scope

This skill does not own:

```text
business logic
application API design
environment values
raw secrets
OpenShift resource semantics
migration SQL/schema design
quality waiver approval
security waiver approval
architecture redesign
release rollback decision
```

---

# Mandatory Workflow

```text
1. Inspect existing pipeline
2. Identify source/branch/release model
3. Resolve build inputs
4. Resolve test/analysis stages
5. Resolve artifact strategy
6. Resolve quality/security gates
7. Resolve migration/initialization integration
8. Resolve environment promotion flow
9. Resolve deployment handoff
10. Resolve manual approvals
11. Validate failure propagation
12. Validate artifact traceability
13. Validate secrets/config boundaries
14. Validate reproducibility
15. Return structured pipeline evidence
```

---

# Phase 1 — Inspect Existing Pipeline

Before changing CI/CD, inspect:

```text
pipeline files
includes/templates
stages
jobs
rules/conditions
variables
artifacts
cache usage
container build
release jobs
deployment jobs
manual gates
security scans
quality scans
test jobs
migration jobs
```

Do not replace a valid project pipeline with a generic template without evidence.

If no pipeline exists:

return:

`PIPELINE_MISSING`

---

# Source / Trigger Model

Resolve how the pipeline is triggered.

Possible triggers may include:

```text
push
merge request
tag
release
manual
scheduled
API-triggered
downstream pipeline
```

The correct model must come from project/GitLab evidence.

Do not invent a branch/release workflow.

If trigger semantics are unclear:

return:

`PIPELINE_TRIGGER_UNRESOLVED`

---

# Branch / Merge Request Boundary

GitLab workflow rules must follow the project and current standard.

The CI/CD skill may enforce or automate checks around:

```text
merge requests
protected branches
release branches
tags
```

but must not invent organizational branch policies beyond available evidence.

If the project workflow conflicts with normative requirements:

return:

`GIT_WORKFLOW_REVIEW_REQUIRED`

---

# Build Inputs

A build must be reproducible from explicit inputs.

Track:

```text
source commit SHA
dependency manifest
lock file where applicable
runtime/toolchain version
build arguments
base image/runtime image
pipeline definition version
```

Avoid builds that depend on undocumented local state.

If the build cannot be reproduced from version-controlled inputs:

return:

`NON_REPRODUCIBLE_BUILD_RISK`

---

# Dependency Install

Dependency installation must use the project-approved package manager and manifest/lock strategy.

Examples:

```text
Node.js
→ package.json + approved lock/package manager

Java
→ pom.xml / approved build tool

PHP
→ composer.json
```

The CI/CD skill must not change dependency-management policy silently.

If lock/manifests conflict or dependencies drift:

return:

`DEPENDENCY_BUILD_RISK`

---

# Build Stage

The build stage should produce a deterministic application artifact or container image where the platform model requires it.

Examples:

```text
compiled package
frontend bundle
JAR/WAR
container image
other approved artifact
```

The artifact must be traceable to the source commit.

If the build output cannot be identified uniquely:

return:

`BUILD_ARTIFACT_UNRESOLVED`

---

# Tests

The pipeline should execute the tests required by project/quality policy.

Possible categories:

```text
unit
integration
contract
frontend
backend
migration
smoke
```

The CI/CD skill only automates execution.

It does not decide that failed tests are acceptable.

If required tests are missing from the pipeline:

return:

`PIPELINE_TEST_COVERAGE_GAP`

---

# Lint / Static Analysis

Where the project/standard requires static analysis or linting, the pipeline should execute it before promotion.

Possible tools depend on the approved stack.

Do not hardcode a specific tool unless project/standard evidence supports it.

If the pipeline bypasses required static analysis:

return:

`STATIC_ANALYSIS_GATE_MISSING`

---

# Quality Gate

Responsibility split:

```text
dev-ci-cd
→ runs quality analysis and blocks/allows according to configured gate result

dev-quality
→ owns interpretation and quality acceptance policy
```

The pipeline must not convert:

```text
FAIL
```

into:

```text
PASS
```

through `allow_failure`, ignored exit codes, or equivalent behavior unless approved policy explicitly permits it.

If a required quality gate is bypassed:

return:

`QUALITY_GATE_BYPASS_RISK`

---

# Security Gate

Responsibility split:

```text
dev-ci-cd
→ runs configured security scans

dev-security
→ owns interpretation and security acceptance
```

Potential pipeline stages may include:

```text
SAST
dependency scanning
secret detection
container/image scanning
DAST when applicable
```

Do not claim all of these are mandatory unless the current standard/project says so.

If a configured required security stage is bypassed:

return:

`SECURITY_GATE_BYPASS_RISK`

---

# Secret Detection

The pipeline should not expose secrets through:

```text
logs
job output
artifacts
cache
debug mode
generated files
```

If secret detection exists, do not disable it silently.

Raw secret values must be injected through approved protected/secret mechanisms.

Return:

`PIPELINE_SECRET_EXPOSURE_RISK`

when necessary.

---

# Pipeline Variables

Pipeline variables must be classified.

Conceptual classes:

```text
NON_SECRET
SECRET_REFERENCE
PIPELINE_METADATA
ENVIRONMENT_SELECTOR
```

Do not place real secrets in repository-controlled pipeline YAML.

Coordinate environment values with:

`dev-environments`

---

# Artifact Immutability

For the OpenShift model described by ES0901:

```text
QA builds artifact/image
        ↓
same immutable artifact
        ↓
HML / PRD
```

The pipeline must preserve artifact identity across promotion.

If HML or PRD rebuilds the application instead of promoting the already-built artifact:

return:

`ARTIFACT_PROMOTION_MODEL_VIOLATION`

---

# Artifact Identity

Record immutable identity when possible:

```text
image digest
package checksum
release version
commit SHA
```

Avoid using mutable-only references such as:

```text
latest
stable
current
```

without resolving and recording immutable identity.

Return:

`MUTABLE_ARTIFACT_REFERENCE_RISK`

when traceability is insufficient.

---

# Artifact Publication

If the pipeline publishes artifacts/images, validate:

```text
target registry/repository
version/tag strategy
immutable reference
source commit linkage
publication result
```

Do not publish to production registries/environments from unapproved branches/triggers.

---

# Promotion

Promotion jobs must move the same approved artifact between environments.

Promotion must not:

```text
recompile source
change application package
inject environment config into artifact
change dependency versions
```

Environment-specific configuration remains external.

Coordinate with:

`dev-environments`

---

# Environment Order

The pipeline should respect the approved lifecycle.

Typical order:

```text
DEV
→ QA
→ HML
→ PRD
```

Do not skip required validation environments unless project/governance explicitly authorizes it.

If the pipeline can promote directly to PRD in violation of required lifecycle controls:

return:

`ENVIRONMENT_PROMOTION_BYPASS_RISK`

---

# Manual Gates

Some promotion or deployment stages may require explicit approval.

Manual gates may be appropriate for:

```text
HML promotion
PRD promotion
production deployment
destructive migration
security exception
high-risk infrastructure mutation
```

The exact approvals come from project/governance policy.

Do not invent unnecessary manual approval gates.

Do not remove required gates silently.

---

# Human Gate Boundary

Model-cost approval and deployment/tool-risk approval are separate from CI/CD stage logic.

A manual CI/CD job is not automatically equivalent to the harness Tool Risk Human Gate.

The harness must preserve both mechanisms when both are required.

---

# Migration Integration

The pipeline may invoke approved migration mechanisms.

Responsibility split:

```text
dev-persistence
→ migration artifacts

dev-deployment
→ migration order for release

dev-ci-cd
→ automation/invocation of the approved migration step
```

Do not generate ad hoc database scripts inside the pipeline.

If the pipeline runs unmanaged manual SQL as a deployment shortcut:

return:

`PIPELINE_MIGRATION_POLICY_RISK`

---

# Migration Failure

Migration jobs must propagate failure.

Do not continue application deployment after a failed required migration unless the approved deployment strategy explicitly permits it.

If failure is swallowed/ignored:

return:

`PIPELINE_FAILURE_PROPAGATION_RISK`

---

# Initial Data / Seed

If initial data is required and the project has an approved seeding mechanism, the pipeline may invoke it where the deployment strategy requires.

Do not embed manual data manipulation in pipeline scripts.

Return:

`PIPELINE_INITIALIZATION_RISK`

when setup depends on undocumented/manual mutation.

---

# Deployment Handoff

The pipeline may invoke:

`dev-deployment`

or the platform deployment mechanism approved by the harness.

Conceptual flow:

```text
artifact approved
     ↓
promotion job
     ↓
deployment request
     ↓
dev-deployment
     ↓
dev-openshift / target runtime
```

The CI/CD skill should not duplicate release-specific deployment planning.

---

# OpenShift Handoff

For OpenShift:

```text
dev-ci-cd
→ decides when pipeline invokes platform deployment action

dev-openshift
→ understands OpenShift project/workload/config/probe/rollout semantics
```

Do not embed undocumented `oc`/platform behavior directly into random pipeline scripts if an approved Tool/capability exists.

---

# Pipeline Failure Propagation

A required job failure must normally stop dependent stages.

Detect patterns such as:

```text
|| true
exit 0 after failure
allow_failure on mandatory gates
ignored test exit code
ignored scanner exit code
```

Return:

`PIPELINE_FAILURE_PROPAGATION_RISK`

when failures are masked.

---

# Retry in CI/CD

Pipeline retries must be bounded and intentional.

Possible retryable failures:

```text
transient registry/network issue
temporary runner failure
provider availability issue
```

Do not automatically retry:

```text
test failures
security failures
migration failures
deterministic build errors
```

without evidence.

If retry behavior masks real failures:

return:

`PIPELINE_RETRY_POLICY_RISK`

---

# Cache

Pipeline cache may improve speed but must not compromise reproducibility.

Validate that cache does not:

```text
inject stale dependencies
cross incompatible branches/runtimes
contain secrets
replace artifact/version control
```

If cache can affect correctness unpredictably:

return:

`PIPELINE_CACHE_RISK`

---

# Generated Artifacts

Generated reports may include:

```text
test results
coverage
lint reports
security reports
build metadata
release metadata
```

Store only non-sensitive artifacts according to project policy.

Do not expose credentials or sensitive payloads.

---

# Pipeline Templates / Includes

Reusable templates are allowed when the project/GitLab model supports them.

Before modifying a shared pipeline template, inspect blast radius.

A shared template change may affect many repositories.

Return:

`SHARED_PIPELINE_CHANGE_REVIEW_REQUIRED`

when the change has organization-wide or multi-project impact.

---

# Runner / Execution Environment

Do not assume runner/runtime availability.

Inspect:

```text
runner type
required image
runtime/toolchain
network access
registry access
environment protections
```

If the required runner capability is unavailable:

return:

`PIPELINE_RUNTIME_UNAVAILABLE`

---

# Protected Variables / Environments

Production-capable variables and deployment environments should use the protections supported by the current GitLab/project configuration.

The CI/CD skill must not reduce protections to unblock a pipeline.

If protections conflict with required behavior:

return:

`PIPELINE_PROTECTION_REVIEW_REQUIRED`

---

# Release Evidence

Collect evidence such as:

```text
pipeline ID
commit SHA
tag/release
artifact digest
test result
quality result
security result
promotion result
deployment job result
target environment
manual approval evidence
```

Do not include raw secret values.

---

# Pipeline State Model

Suggested states:

```text
NOT_CONFIGURED
VALIDATING
READY
RUNNING
BLOCKED
FAILED
PASSED
PROMOTION_READY
DEPLOYMENT_REQUESTED
COMPLETE
```

The exact implementation may differ.

---

# Pipeline as Code

Pipeline definitions should be version-controlled where the current project/platform model supports it.

Avoid undocumented manual UI-only pipeline logic when a code-based definition is expected.

If production-critical behavior exists only as an undocumented manual configuration:

return:

`UNMANAGED_PIPELINE_CONFIGURATION_RISK`

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

gitlab.pipeline.inspect
gitlab.pipeline.modify
gitlab.pipeline.run

gitlab.job.inspect
gitlab.artifact.inspect
gitlab.release.inspect

build.execute
tests.run
static.analysis.run
```

Depending on project:

```text
security.scan.run
artifact.publish
artifact.promote
migration.execute
deployment.request
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If a capability is unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

```text
pipeline syntax
pipeline trigger model
reproducible build
dependency manifest/lock consistency
required tests
static analysis presence
quality gate behavior
security gate behavior
secret exposure
artifact immutability
artifact traceability
environment promotion order
migration failure propagation
pipeline failure propagation
production/manual gate
pipeline evidence
```

The skill must not self-approve official Checks.

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

PIPELINE_MISSING
PIPELINE_TRIGGER_UNRESOLVED
GIT_WORKFLOW_REVIEW_REQUIRED

NON_REPRODUCIBLE_BUILD_RISK
DEPENDENCY_BUILD_RISK
BUILD_ARTIFACT_UNRESOLVED
PIPELINE_TEST_COVERAGE_GAP
STATIC_ANALYSIS_GATE_MISSING

QUALITY_GATE_BYPASS_RISK
SECURITY_GATE_BYPASS_RISK
PIPELINE_SECRET_EXPOSURE_RISK

ARTIFACT_PROMOTION_MODEL_VIOLATION
MUTABLE_ARTIFACT_REFERENCE_RISK
ENVIRONMENT_PROMOTION_BYPASS_RISK

PIPELINE_MIGRATION_POLICY_RISK
PIPELINE_INITIALIZATION_RISK
PIPELINE_FAILURE_PROPAGATION_RISK
PIPELINE_RETRY_POLICY_RISK
PIPELINE_CACHE_RISK

SHARED_PIPELINE_CHANGE_REVIEW_REQUIRED
PIPELINE_RUNTIME_UNAVAILABLE
PIPELINE_PROTECTION_REVIEW_REQUIRED
UNMANAGED_PIPELINE_CONFIGURATION_RISK

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

```yaml
cicdResult:

  status: COMPLETE

  pipeline:
    platform: GITLAB_CI
    validated: true

  triggerModel:
    mergeRequest: true
    tag: true
    manualPromotion: true

  build:
    reproducible: true
    sourceCommit: ...
    runtimeVersion: ...
    dependencyManifestValidated: true

  tests:
    unit: PASS
    integration: PASS

  analysis:
    staticAnalysis: PASS
    qualityGate: PASS
    securityGate: PASS

  artifact:
    type: CONTAINER_IMAGE
    version: 2.4.0
    digest: sha256:...
    immutable: true
    published: true

  promotion:
    model: BUILD_ONCE_PROMOTE
    sourceEnvironment: QA
    targets:
      - HML
      - PRD
    sameArtifact: true

  migrations:
    integrated: true
    managedByApprovedMechanism: true
    failurePropagation: true

  deployment:
    delegatedTo: dev-deployment

  protection:
    productionManualGate: true
    requiredProtectionsPreserved: true

  evidence:
    - pipeline-id
    - commit-sha
    - artifact-digest
    - quality-report
    - security-report

  reviews:
    architectureRequired: false
    qualityRequired: false
    securityRequired: false

  risks: []
  assumptions: []
```

---

# Model Routing Metadata

This skill may emit complexity signals to `automatic-consumption`.

It does not select the final model.

## LOW_COST / STANDARD

Use for:

```text
pipeline syntax/config updates
adding known test jobs
artifact metadata
simple promotion jobs
known quality/security stage integration
routine GitLab CI changes
```

## REASONING

Consider when:

```text
pipeline stages have complex dependencies
shared templates are affected
migration/release automation is non-trivial
artifact promotion is inconsistent
branch/tag behavior is ambiguous
multiple repositories/pipelines coordinate
quality/security gates conflict with delivery flow
```

## PREMIUM

Consider only when:

```text
organization-wide shared pipeline changes
critical production delivery redesign
multi-project pipeline orchestration
major security/release-control implications
repeated lower-tier reasoning fails
```

Premium execution must pass the orchestrator's Human Model Gate.

Pipeline operations that cause production mutation remain independently governed by Tool Risk approval.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- pipeline is missing or trigger model is unclear
- Git workflow needs review
- build is not reproducible
- required tests/analysis are missing
- quality/security gates are bypassed
- artifact identity is not immutable/traceable
- environment promotion can be bypassed
- migration automation is unsafe
- required failures are masked
- shared pipeline templates are affected
- runner/runtime capability is unavailable
- production protections would need to be weakened
- architecture/security/quality review is required
- required capability/check is unavailable

---

# Prohibited Behavior

This skill must not:

- replace a valid pipeline with a generic template without evidence
- invent branch/release policy
- hide build/test/scanner failures
- use `allow_failure` to bypass required quality/security controls without policy
- store raw secrets in pipeline YAML
- print secrets in job logs
- rebuild HML/PRD artifacts when immutable promotion is required
- use mutable artifact tags without recording immutable identity
- skip required lifecycle environments silently
- invent migration SQL in the pipeline
- continue rollout after required migration failure
- retry deterministic failures blindly
- weaken protected-environment or protected-variable controls to unblock delivery
- change shared pipeline templates without blast-radius review
- perform release-specific deployment planning that belongs to dev-deployment
- implement OpenShift semantics that belong to dev-openshift
- self-approve quality/security findings
- create Tools directly
- self-approve formal Checks
- bypass Policies

---

# Evidence Requirements

The result must distinguish:

```text
pipeline definition evidence
source/trigger evidence
build evidence
test evidence
quality evidence
security evidence
artifact evidence
promotion evidence
migration evidence
deployment handoff evidence
manual approval evidence
assumptions
risks
open decisions
```

All meaningful pipeline decisions should be traceable to one or more of:

- WorkUnit
- Jira / Ficha de Proyecto
- GitLab repository
- pipeline configuration
- pipeline run
- Git commit/tag/release
- artifact registry
- quality result
- security result
- `dev-environments`
- `dev-deployment`
- `dev-openshift`
- ES0901

---

# Success Criteria

This skill is successful when it:

- inspects and preserves the real project pipeline model
- builds from reproducible/versioned inputs
- executes required tests and analysis
- preserves quality/security gates
- produces a uniquely traceable immutable artifact
- preserves build-once/promote behavior where applicable
- keeps environment configuration outside the artifact
- automates migration invocation only through approved mechanisms
- propagates failures correctly
- preserves protected production controls
- delegates release-specific deployment to `dev-deployment`
- delegates platform semantics to `dev-openshift`
- captures non-sensitive delivery evidence
- returns a structured result to the orchestrator

---

# Source References

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Key areas:

```text
Annex I
→ Git / GitLab workflow and delivery-related controls

Annex II
→ approved tools / runtime versions

Annex III
→ continuous deployment
→ build/promotion model
→ external configuration
→ migrations / initial data automation
→ reproducible delivery
```

Examples in the standard must not be treated as project-specific pipeline definitions without repository/project evidence.
