---
name: dev-openshift
description: Use when a GCBA / DGISIS application has to be represented and operated inside the OpenShift runtime — workload and route configuration, least-privilege access, environment isolation, externalized configuration, the ephemeral-container constraint, health-probe semantics, scalability and traceable platform operations. It does not own business logic, environment values, release strategy, CI/CD orchestration or secret values. Owned by dev-devops, entered through dev-devops-implementation.
---

# Skill: dev-openshift

## Purpose

Inspect, configure, validate, and operate GCBA applications on the OpenShift platform while preserving the approved deployment model, least-privilege access, environment isolation, externalized configuration, ephemeral-container constraints, health-probe semantics, runtime scalability, and traceable platform operations.

This skill belongs to the `dev-devops` agent.

It specializes in the platform-specific question:

> How should this application be represented and operated safely inside the GCBA OpenShift runtime?

This skill does not own application business logic, application health implementation, environment-value definition, release strategy, CI/CD orchestration, or secret values.

---

## Owner

Primary owner:

`dev-devops`

Primary implementation entry point:

`dev-devops-implementation`

Related skills:

- `dev-environments`
- `dev-deployment`
- `dev-ci-cd`
- `dev-observability`
- `dev-storage`
- `dev-persistence`
- `dev-security-analysis`
- `dev-architecture-analysis`

---

# Integration with Block 1

OpenShift access must be resolved through **Block 1 — Bootstrap + Integrations**.

Conceptual flow:

```text
User configures OpenShift integration
        ↓
Block 1 receives endpoint + approved credential/token
        ↓
SecretStore stores credential securely
        ↓
OpenShift Integration Adapter validates connectivity
        ↓
Capability discovery
        ↓
Capability Registry exposes only validated OpenShift capabilities
        ↓
dev-openshift requests capabilities
```

The `dev-openshift` skill must never receive or manage raw credentials directly.

Use a logical credential reference such as:

```text
openshift.api.token
```

or the runtime-specific equivalent.

The actual credential type may be an OpenShift access token/API credential according to the real platform integration.

Do not hardcode provider/platform terminology if the configured runtime exposes a different approved authentication mechanism.

---

# Credential Boundary

Block 1 owns:

```text
credential acquisition/configuration
secure storage
connection validation
integration availability
capability discovery
```

`dev-openshift` owns:

```text
platform operations requested through validated capabilities
```

Agents must not:

```text
read raw secrets
store raw tokens
print credentials
copy credentials into manifests
include credentials in logs
include credentials in generated documentation
```

If the OpenShift integration is unavailable:

return:

`OPENSHIFT_INTEGRATION_UNAVAILABLE`

If authentication fails:

return:

`OPENSHIFT_AUTHENTICATION_FAILED`

The skill must not ask the Agent to bypass Block 1 with a manually embedded token.

---

# Core Principle

> Operate OpenShift through validated, least-privilege capabilities; keep application state external, keep environment configuration external, and make every platform mutation explicit, scoped, and traceable.

---

# Normative Basis

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas:

```text
Section 11
→ OpenShift request timeout < 30 seconds
→ application startup < 60 seconds
→ 24x7 availability
→ horizontal scaling
→ stateless/granjable application behavior

Annex III
→ OpenShift Continuous Delivery model
→ DEV / QA / HML / Production environments
→ build once in QA, promote same image
→ ConfigMaps / Secrets / external configuration
→ no persistent local container storage
→ DB outside OpenShift and parameterized
→ configuration repository
→ S2I image selection
→ pipeline configuration
→ user/role assignment
→ later environment/project creation

Annex IV
→ liveness/readiness required
→ startup probe optional
→ health endpoints
→ HTTP / exec / TCP probe methods
→ delays, periods, timeouts, thresholds
```

Normative findings must preserve source traceability.

---

# Scope

This skill owns OpenShift-specific behavior such as:

```text
project / namespace inspection
workload/deployment inspection
runtime manifest inspection
ConfigMap integration
Secret reference integration
Service inspection/configuration
Route inspection/configuration
image/runtime reference inspection
rollout inspection
replica/scaling configuration
resource/runtime configuration inspection
health probe configuration
ephemeral filesystem validation
environment/platform mapping
platform access/permission validation
platform operation evidence
```

The exact resource kinds must follow the real project/OpenShift version and current repository.

Do not assume every project uses the same resource kind.

---

# What This Skill Does Not Own

This skill does not own:

```text
raw OpenShift token/API credential
application health endpoint implementation
application log implementation
environment value definition
database schema migrations
release/deployment ordering
CI/CD stage design
architecture redesign
security approval
quality acceptance
```

Use:

```text
Block 1
→ OpenShift integration authentication and capability discovery

dev-observability
→ /health/liveness and /health/readiness implementation

dev-environments
→ logical configuration and values by environment

dev-deployment
→ release-specific rollout/order/rollback

dev-ci-cd
→ automated pipeline flow

dev-persistence
→ migration implementation

dev-security-analysis
→ security review
```

---

# Mandatory Workflow

```text
1. Resolve OpenShift integration availability
2. Resolve user/service identity and permissions
3. Identify target OpenShift environment/project
4. Inspect current platform resources
5. Resolve workload/runtime model
6. Resolve artifact/image reference
7. Resolve configuration and secret references
8. Resolve Service/Route exposure
9. Resolve health probes
10. Resolve storage constraints
11. Resolve scaling/stateless behavior
12. Resolve runtime/startup constraints
13. Compute planned platform changes
14. Classify mutation risk
15. Apply changes only through approved capabilities
16. Verify rollout/runtime state
17. Capture non-sensitive evidence
```

---

# Phase 1 — Integration Availability

Before any platform operation, verify that Block 1 exposed the required capabilities.

Typical capability examples:

```text
openshift.project.inspect
openshift.workload.inspect
openshift.configmap.inspect
openshift.secret.reference.inspect
openshift.service.inspect
openshift.route.inspect
openshift.probe.inspect
openshift.rollout.inspect
```

Mutation capabilities may include:

```text
openshift.configmap.apply
openshift.workload.apply
openshift.service.apply
openshift.route.apply
openshift.probe.configure
openshift.rollout.execute
openshift.scale
```

Exact capability names are harness implementation details.

If a required capability is unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Least-Privilege Access

OpenShift credentials/roles must expose only the permissions required for the WorkUnit.

The skill must identify whether a requested operation is:

```text
READ_ONLY
MUTATING
DESTRUCTIVE
```

Examples:

```text
inspect project/workload
→ READ_ONLY

update ConfigMap reference
→ MUTATING

delete workload/project/resource
→ DESTRUCTIVE
```

If current credentials are broader than required, this may be reported as:

`OPENSHIFT_PERMISSION_SCOPE_RISK`

The skill does not alter organizational RBAC silently.

---

# Project / Environment Resolution

The skill must identify the target project/namespace and map it to the GCBA environment.

Example:

```yaml
target:
  environment: QA
  openshiftProject: sistema-qa
```

Do not infer the environment solely from a project name when authoritative mapping exists.

If target mapping is unresolved:

return:

`OPENSHIFT_PROJECT_UNRESOLVED`

Coordinate with:

`dev-environments`

---

# Platform Provisioning Boundary

ES0901 Annex III describes initial setup tasks performed by GCBA with development-team collaboration:

```text
project creation
configuration repository creation
S2I image selection
pipeline configuration
development users/roles
later creation/configuration of remaining environments
```

The skill must distinguish:

```text
existing project operations
vs
organizational platform provisioning
```

If the required project/resource does not exist and the harness lacks an approved provisioning capability:

return:

`PLATFORM_PROVISIONING_REQUIRED`

Do not create organizational resources through undocumented bypasses.

---

# Workload Resource Model

Inspect the current project/repository to determine the workload model.

Possible resource types may include:

```text
Deployment
DeploymentConfig
other approved OpenShift/Kubernetes workload resource
```

Do not force a `DeploymentConfig` merely because older/project documentation mentions `DeployConfig`.

Do not migrate resource types during an unrelated WorkUnit.

If the workload resource model is unclear:

return:

`OPENSHIFT_WORKLOAD_MODEL_UNRESOLVED`

---

# Artifact / Image Reference

The workload must reference the artifact selected by `dev-deployment`.

For the ES0901 OpenShift model:

```text
build once in QA
→ promote same immutable image
→ inject environment-specific configuration
```

`dev-openshift` must not rebuild the image to change environment values.

If environment-specific image mutation is detected:

return:

`ARTIFACT_PROMOTION_MODEL_VIOLATION`

---

# S2I / Runtime Image

Where the project uses Source-to-Image or an approved base/runtime image, inspect compatibility with the approved project stack.

Do not change the base/S2I image silently.

If no compatible image can be resolved:

return:

`RUNTIME_IMAGE_UNRESOLVED`

Major runtime-image changes may require:

`ARCHITECTURE_REVIEW_REQUIRED`

or approval according to project governance.

---

# ConfigMaps

ConfigMaps may be used for non-secret runtime configuration.

Responsibility split:

```text
dev-environments
→ logical keys and values per environment

dev-openshift
→ platform representation/injection
```

The skill must validate:

```text
required keys are represented
environment mapping is correct
no secret material is stored in ConfigMap
workload references are correct
changes are scoped to the target environment
```

If secret material is detected:

return:

`SECRET_IN_CONFIGMAP_RISK`

and request:

`SECURITY_REVIEW_REQUIRED`

---

# Secret References

The skill may inspect and configure **references** to approved secret resources.

It must never read, print, export, or generate secret values unless the runtime capability explicitly returns only safe metadata.

Allowed reasoning may include:

```text
secret reference exists?
required key reference exists?
target workload references correct secret name/key?
environment mapping correct?
```

Forbidden:

```text
show secret value
copy secret value
write raw secret into manifest
embed token/API key
```

If a required secret reference is absent:

return:

`OPENSHIFT_SECRET_REFERENCE_MISSING`

Coordinate credential provisioning through the approved Block 1/platform/secret process.

---

# Database Boundary

ES0901 states that the database is outside OpenShift and its host, port, and schema must be parameterizable.

The skill may verify runtime references/configuration.

It does not provision or alter the database.

If application configuration assumes a local/container database unexpectedly:

return:

`DATABASE_PLATFORM_BOUNDARY_RISK`

---

# Ephemeral Filesystem

ES0901 explicitly forbids persistent local storage in the OpenShift deployment model because containers are ephemeral.

Detect application/runtime configuration that persists business/application state to container-local filesystem.

Return:

`LOCAL_PERSISTENT_STORAGE_VIOLATION`

Coordinate file behavior with:

`dev-storage`

Temporary files may be allowed only if application behavior safely removes them and does not treat them as persistent state.

---

# Services

Inspect the internal service exposure required by the workload.

Validate:

```text
selector/target relationship
port mapping
target port
protocol
scope
environment
```

Do not expose a workload externally merely because a Service exists.

Public/external exposure requires explicit routing intent.

---

# Routes

OpenShift Route behavior must follow project/platform evidence.

Before creating/modifying a Route, determine:

```text
is external exposure required?
host known/owned?
TLS behavior known?
target Service known?
environment correct?
security implications reviewed?
```

Do not invent public hostnames.

If host/routing ownership is unclear:

return:

`OPENSHIFT_ROUTE_CONFIGURATION_UNRESOLVED`

Potential public exposure may require:

`SECURITY_REVIEW_REQUIRED`

---

# Network / Egress

If the application requires access to:

```text
internal GCBA services
external providers
databases
identity providers
storage services
```

the skill may detect that platform/network permission is required.

It does not invent network policy or firewall changes.

If connectivity is blocked and requires organizational network configuration:

return:

`OPENSHIFT_NETWORK_CHANGE_REQUIRED`

Coordinate with platform/network governance.

---

# Health Responsibility Split

Mandatory separation:

```text
dev-observability
→ implements health mechanisms/endpoints

dev-openshift
→ configures OpenShift probes to consume them
```

For HTTP applications, ES0901 requires:

```text
/health/liveness
/health/readiness
```

and recommends:

```text
/health
```

Startup probe is optional.

If required application health mechanisms do not exist:

return:

`HEALTH_ENDPOINT_REQUIRED`

and delegate to:

`dev-observability`

---

# Probe Types

ES0901 Annex IV recognizes:

```text
HTTP
EXEC / command
TCP socket
```

Choose the probe type based on actual application/runtime behavior.

Do not use HTTP simply because most applications are HTTP.

---

# Liveness

Liveness should detect whether the process/application is stuck or unhealthy enough to require restart.

It should remain simple.

Do not make liveness fail because an optional/secondary external dependency is unavailable.

If liveness includes inappropriate dependency checks:

return:

`LIVENESS_DEPENDENCY_RISK`

---

# Readiness

Readiness determines whether the workload can safely receive traffic.

It may evaluate critical dependencies where justified by application architecture.

The exact dependency set must come from application/project evidence.

If readiness does not represent traffic-serving capability:

return:

`READINESS_SEMANTICS_RISK`

---

# Startup Probe

Startup probe is optional and may protect slow-starting applications from premature liveness failures.

Do not add it automatically.

If startup behavior justifies it:

record:

`STARTUP_PROBE_RECOMMENDED`

The probe must not be used to hide an unjustified startup performance problem.

---

# Probe Parameters

Probe configuration may include:

```text
initialDelaySeconds
timeoutSeconds
periodSeconds
successThreshold
failureThreshold
```

The ES0901 YAML values are examples.

Do not copy them blindly.

Values must be based on:

```text
real startup behavior
real readiness behavior
runtime characteristics
approved project evidence
```

If they cannot be determined safely:

return:

`HEALTH_PROBE_CONFIGURATION_UNRESOLVED`

---

# Health Sensitive Data

Health mechanisms must not expose sensitive data.

If platform validation reveals sensitive output:

return:

`HEALTH_SENSITIVE_DATA_EXPOSURE`

and request:

`SECURITY_REVIEW_REQUIRED`

---

# Startup Constraint

ES0901 states that applicable OpenShift applications must start in less than 60 seconds.

Inspect actual rollout/startup evidence.

If the application exceeds the requirement:

return:

`STARTUP_TIME_RISK`

Do not solve this only by increasing probe thresholds.

Coordinate application/runtime optimization or architecture review.

---

# Request Timeout Constraint

ES0901 states that exposed requests/services must respond in less than 30 seconds on the relevant OpenShift platform because the platform may terminate longer requests.

The OpenShift skill must detect platform mismatch but does not redesign application flow.

Return:

`PLATFORM_TIMEOUT_RISK`

and escalate to the owning implementation skill / `dev-architecture-analysis` when asynchronous redesign may be needed.

---

# Horizontal Scaling

ES0901 requires horizontal scalability according to architecture, including stateless/granjable application behavior for applicable systems.

Inspect:

```text
replica configuration
session/state assumptions
local filesystem dependency
node-specific behavior
singleton assumptions
```

Do not increase replicas when application statefulness makes scaling unsafe.

If detected:

return:

`STATEFUL_RUNTIME_RISK`

and coordinate with:

`dev-architecture-analysis`

or the owning application agent.

---

# Replica Configuration

Replica count must come from:

```text
architecture
capacity/dimensioning
platform policy
project evidence
```

Do not invent production replica counts.

If WorkUnit requires scaling but no approved target exists:

return:

`REPLICA_CONFIGURATION_UNRESOLVED`

---

# Resource Configuration

CPU/memory requests/limits or equivalent runtime resource parameters must follow project/platform evidence.

Do not invent arbitrary values.

If the application cannot be deployed safely without unresolved resource sizing:

return:

`RESOURCE_CONFIGURATION_UNRESOLVED`

Capacity/dimensioning may require human/platform input.

---

# Rollout Inspection

The skill may inspect:

```text
desired replicas
available replicas
updated replicas
rollout status
pod/container restart state
readiness
image identity
```

`dev-deployment` decides the release strategy and rollout acceptance.

`dev-openshift` provides platform-specific state/evidence.

---

# Platform Mutation Plan

Before changing OpenShift, produce a plan.

Example:

```yaml
platformChangePlan:

  environment: QA
  project: sistema-qa

  operations:
    - capability: openshift.configmap.apply
      sideEffect: MUTATING
      risk: MEDIUM

    - capability: openshift.probe.configure
      sideEffect: MUTATING
      risk: MEDIUM

  destructiveOperations: false
  productionImpact: false
```

Do not mutate the platform before the change set is understood.

---

# Mutation Risk

Use the Tool Builder / orchestrator risk concepts.

Examples:

```text
inspect workload
→ LOW / READ_ONLY

change QA ConfigMap
→ MEDIUM / MUTATING

change PRD route
→ HIGH / MUTATING

delete PRD workload
→ CRITICAL / DESTRUCTIVE
```

Exact classification is governed by the harness risk policy.

Production and destructive actions require the configured Tool Risk Human Gate.

---

# Dry-Run / Validation

Where platform/runtime capabilities support declarative validation or dry-run behavior, prefer validating proposed changes before mutation.

The exact mechanism depends on the tool/runtime.

Do not claim validation occurred if only static text was inspected.

Evidence must distinguish:

```text
STATIC
DRY_RUN
NON_PRODUCTION_APPLIED
PRODUCTION_APPLIED
```

---

# Drift

Compare expected repository/configuration state with actual OpenShift state when possible.

Possible drift:

```text
manual ConfigMap change
unexpected image
missing probe
unexpected Route host
replica mismatch
resource mismatch
secret-reference mismatch
```

If drift affects correctness/safety:

return:

`OPENSHIFT_CONFIGURATION_DRIFT`

Do not overwrite unexplained production drift silently.

---

# Git / Configuration Repository Boundary

ES0901 Annex III refers to a repository for configuration such as ConfigMaps and deployment configuration.

Prefer platform configuration that is traceable to version-controlled sources where the current GCBA process/project supports that model.

If actual platform state contains unmanaged changes not represented in expected configuration:

record drift and require resolution before overwriting high-risk state.

---

# CI/CD Boundary

`dev-ci-cd` owns pipeline automation.

`dev-openshift` owns the OpenShift operations/capabilities that the pipeline may invoke.

Example:

```text
dev-ci-cd
→ pipeline calls deploy/promote action

dev-openshift
→ understands target project, workload, probes, ConfigMap, Route, rollout
```

Do not duplicate pipeline-stage logic in this skill.

---

# Deployment Boundary

`dev-deployment` owns:

```text
which release
which order
migration sequence
rollout strategy
verification
rollback decision
```

`dev-openshift` owns:

```text
how the approved platform operation is represented/executed in OpenShift
```

---

# Required Capabilities

Read-only examples:

```text
openshift.connection.validate
openshift.project.inspect
openshift.permissions.inspect
openshift.workload.inspect
openshift.pod.inspect
openshift.image.inspect
openshift.configmap.inspect
openshift.secret.reference.inspect
openshift.service.inspect
openshift.route.inspect
openshift.probe.inspect
openshift.rollout.inspect
openshift.events.inspect
```

Mutation examples:

```text
openshift.configmap.apply
openshift.workload.apply
openshift.service.apply
openshift.route.apply
openshift.probe.configure
openshift.rollout.execute
openshift.rollout.rollback
openshift.scale
```

Potential destructive capabilities:

```text
openshift.resource.delete
```

Destructive capabilities must never be exposed or invoked casually.

Block 1 capability discovery should register only operations actually supported and authorized by the configured OpenShift integration.

---

# Required Checks

Potential Checks:

```text
OpenShift integration available
least-privilege permission scope
target project/environment mapping
artifact identity
ConfigMap secret separation
secret-reference correctness
persistent local storage
Service/Route correctness
health endpoints available
liveness semantics
readiness semantics
probe parameter validity
health sensitive-data exposure
startup-time requirement
platform request-timeout risk
stateless scaling compatibility
configuration drift
production mutation approval
```

The skill must not self-approve official Checks.

If a required Check does not exist:

return:

`CHECK_GAP`

---

# Result Statuses

Supported statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

OPENSHIFT_INTEGRATION_UNAVAILABLE
OPENSHIFT_AUTHENTICATION_FAILED
OPENSHIFT_PERMISSION_SCOPE_RISK

OPENSHIFT_PROJECT_UNRESOLVED
PLATFORM_PROVISIONING_REQUIRED
OPENSHIFT_WORKLOAD_MODEL_UNRESOLVED

ARTIFACT_PROMOTION_MODEL_VIOLATION
RUNTIME_IMAGE_UNRESOLVED

SECRET_IN_CONFIGMAP_RISK
OPENSHIFT_SECRET_REFERENCE_MISSING
DATABASE_PLATFORM_BOUNDARY_RISK
LOCAL_PERSISTENT_STORAGE_VIOLATION

OPENSHIFT_ROUTE_CONFIGURATION_UNRESOLVED
OPENSHIFT_NETWORK_CHANGE_REQUIRED

HEALTH_ENDPOINT_REQUIRED
LIVENESS_DEPENDENCY_RISK
READINESS_SEMANTICS_RISK
STARTUP_PROBE_RECOMMENDED
HEALTH_PROBE_CONFIGURATION_UNRESOLVED
HEALTH_SENSITIVE_DATA_EXPOSURE

STARTUP_TIME_RISK
PLATFORM_TIMEOUT_RISK
STATEFUL_RUNTIME_RISK
REPLICA_CONFIGURATION_UNRESOLVED
RESOURCE_CONFIGURATION_UNRESOLVED

OPENSHIFT_CONFIGURATION_DRIFT

ARCHITECTURE_REVIEW_REQUIRED
SECURITY_REVIEW_REQUIRED
DEVOPS_CHANGE_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED
TOOL_RISK_APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

```yaml
openshiftResult:

  status: COMPLETE

  integration:
    available: true
    authentication: VALIDATED
    rawCredentialExposed: false

  target:
    environment: QA
    project: sistema-qa

  permissions:
    validated: true
    leastPrivilegeRiskDetected: false

  workload:
    kind: Deployment
    name: sistema-api
    image: registry/project/app@sha256:...
    replicas:
      desired: 2
      available: 2

  configuration:
    configMaps:
      validated: true
    secretReferences:
      validated: true
    secretValuesRead: false

  exposure:
    service:
      validated: true
    route:
      required: true
      validated: true

  storage:
    localPersistentStorageDetected: false

  health:
    liveness:
      configured: true
      semanticsValidated: true

    readiness:
      configured: true
      semanticsValidated: true

    startup:
      configured: false
      required: false

    sensitiveDataExposed: false

  runtime:
    startupRequirementSatisfied: true
    platformTimeoutRisk: false
    statelessScalingCompatible: true

  drift:
    detected: false

  mutation:
    executed: true
    environment: QA
    productionImpact: false
    destructive: false
    approvalRequired: false

  validation:
    rollout: PASS
    readiness: PASS

  requiredCapabilities:
    - openshift.project.inspect
    - openshift.workload.inspect
    - openshift.configmap.inspect
    - openshift.probe.inspect

  requiredChecks:
    - openshift-environment
    - secret-reference
    - local-storage
    - health-probes
    - stateless-runtime

  risks: []
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

This skill may emit complexity signals to `automatic-consumption`.

It does not select the final model.

## LOW_COST / STANDARD

Use for:

```text
resource inspection
ConfigMap mapping
Secret-reference validation
Service/Route inspection
probe configuration following known application values
rollout evidence collection
static/dry-run manifest validation
```

## REASONING

Consider when:

```text
platform state differs from repository state
permissions are ambiguous
multiple OpenShift projects/environments interact
Route/network behavior is unclear
health probe semantics are complex
statefulness conflicts with scaling
resource/workload models are inconsistent
migration between resource types is proposed
```

## PREMIUM

Consider only when:

```text
critical production platform migration
major shared OpenShift configuration change
complex security/RBAC exposure
high-impact routing/topology change
repeated lower-tier reasoning attempts fail
```

Premium execution must pass the Human Model Gate.

Platform mutation risk remains independently governed by the Tool Risk Human Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- Block 1 OpenShift integration is unavailable
- authentication fails
- required capability is unavailable
- permissions are insufficient or unexpectedly broad
- target project/environment is unresolved
- organizational provisioning is required
- workload model is unclear
- runtime image cannot be resolved
- secret/config separation is unsafe
- Route/public exposure is unresolved
- network changes are required
- health endpoints are missing
- probe semantics cannot be determined
- startup/runtime constraints are violated
- scaling conflicts with application state
- production/destructive mutation is requested
- platform drift invalidates expected state
- architecture/security review is required
- a required Check is missing

---

# Prohibited Behavior

This skill must not:

- manage raw OpenShift API tokens directly
- place OpenShift credentials in repository files
- log or return OpenShift credentials
- bypass Block 1 integration/authentication
- invent target project names
- create organizational platform resources without approved capability/process
- force a workload resource type without project evidence
- rebuild artifacts to change environment configuration
- put secrets in ConfigMaps
- expose secret values
- persist application state on container-local filesystem
- invent Route hosts
- silently expose an internal service publicly
- invent network/firewall rules
- implement application health endpoints
- copy example probe values blindly
- make liveness depend on optional external systems
- hide startup performance problems by probe tuning alone
- scale a stateful application blindly
- invent replica/resource values
- overwrite unexplained production drift silently
- execute destructive/production mutations without approval
- create Tools directly
- self-approve formal Checks
- bypass Policies

---

# Evidence Requirements

The result must distinguish:

```text
Block 1 integration evidence
authentication availability
capability availability
permission evidence
target project/environment evidence
repository/manifest evidence
actual OpenShift state
configuration evidence
secret-reference metadata
Service/Route evidence
health/probe evidence
rollout evidence
drift evidence
human approval evidence
assumptions
risks
```

All meaningful decisions should be traceable to one or more of:

- WorkUnit
- Block 1 OpenShift integration status
- Capability Registry
- Jira / Ficha de Proyecto
- configuration repository
- application repository
- OpenShift project state
- `dev-environments` result
- `dev-deployment` result
- `dev-observability` result
- ES0901
- platform operation result

---

# Success Criteria

This skill is successful when it:

- consumes OpenShift access only through Block 1
- never exposes raw platform credentials
- resolves the correct project/environment
- respects least privilege
- understands the real workload/resource model
- preserves immutable artifact promotion
- maps ConfigMaps and secret references safely
- keeps persistent state outside ephemeral containers
- configures Services/Routes only with explicit evidence
- preserves health-check responsibility boundaries
- configures liveness/readiness/startup probes appropriately
- evaluates startup and request-timeout requirements
- validates horizontal-scaling/stateless assumptions
- detects platform drift
- classifies platform mutations by risk
- requires approval for high-risk production/destructive actions
- returns non-sensitive platform evidence to the orchestrator

---

# Source References

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Key areas:

```text
Section 11
→ OpenShift timeout/startup/scalability/runtime constraints

Annex III
→ OpenShift delivery model
→ environments
→ immutable promotion
→ ConfigMaps/Secrets
→ ephemeral containers
→ DB externalization
→ S2I
→ configuration repository
→ pipeline/setup responsibilities

Annex IV
→ liveness/readiness/startup
→ HTTP/exec/TCP probes
→ probe parameters and health endpoint requirements
```

Examples in the standard must not be treated as universal resource values or application-specific probe thresholds.
