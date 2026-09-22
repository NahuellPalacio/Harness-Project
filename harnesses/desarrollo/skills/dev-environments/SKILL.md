---
name: dev-environments
description: Use when the same approved artifact has to run correctly in each environment of a GCBA / DGISIS project — DEV, QA, HML and PRD, HML internal and DMZ included — through explicit external configuration: environment separation, no hardcoded URLs or per-environment values, credentials that never travel between environments, and promotion validated before it happens. It configures; it does not deploy. Owned by dev-devops.
---

# Skill: dev-environments

## Purpose

Define, validate, and implement environment-specific configuration for GCBA applications across the delivery lifecycle while preserving strict environment separation, configuration externalization, safe promotion, and traceability.

This skill belongs to the `dev-devops` agent.

It specializes in the boundary:

```text
application artifact
        ↓
environment-specific runtime configuration
        ↓
DEV / QA / HML / PRD
```

Its responsibility is not to deploy the application itself. Its responsibility is to ensure that the same approved application can operate correctly in each environment through explicit, controlled, external configuration.

---

## Owner

Primary owner:

`dev-devops`

Primary implementation entry point:

`dev-devops-implementation`

Related skills:

- `dev-deployment`
- `dev-openshift`
- `dev-ci-cd`
- `dev-observability`
- `dev-persistence`
- `dev-integration-implementation`
- `dev-external-integration`
- `dev-service-integration`
- `dev-openid-connect`
- `dev-miba`
- `dev-security-analysis`

---

# Core Principle

> Environment differences belong in explicit external configuration, not in application source code or duplicated environment-specific builds.

The skill must answer:

> What may vary between environments, where is it configured, who owns it, how is it injected, and how do we prove that one environment cannot accidentally use another environment's configuration?

---

# Normative Basis

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant rules:

```text
C2
→ promote through DEV, QA, HML, and PRD with validation before promotion

M2
→ database, service, URL, protocol, path, and other environment variables
  must be external to application code

Section 6.4
→ GCBA environment model and ASI administration

Section 6.5
→ use DNS instead of IP for server references
→ application servers remain independent
→ ASI may change infrastructure addressing transparently

Annex III
→ deployment/environment configuration and artifact promotion model
```

Normative findings must retain source traceability.

---

# Environment Model

Default lifecycle:

```text
DEV
→ QA
→ HML
→ PRD
```

Project/platform naming may differ.

Possible additional contexts:

```text
LOCAL
PRD_INTERNAL
PRD_DMZ
HML_INTERNAL
HML_DMZ
```

Do not assume identifiers are identical across Jira, GitLab, OpenShift, databases, identity providers, internal services, or external providers.

If the real environment model cannot be resolved:

return:

`ENVIRONMENT_MODEL_UNRESOLVED`

---

# Mandatory Workflow

```text
1. Discover actual project environments
2. Resolve project/platform naming
3. Inventory environment-dependent configuration
4. Classify secret / non-secret / derived values
5. Identify configuration owner
6. Identify configuration source/injection mechanism
7. Validate externalization from code
8. Validate DNS/protocol conventions
9. Resolve internal-service mappings
10. Resolve external-provider mappings
11. Resolve identity mappings
12. Validate configuration completeness
13. Detect cross-environment leakage
14. Detect configuration drift
15. Validate artifact/environment decoupling
16. Produce environment matrix and readiness
```

---

# Configuration Inventory

Inventory every environment-dependent logical key required by the application.

Suggested categories:

```text
DATABASE
INTERNAL_SERVICE
EXTERNAL_SERVICE
IDENTITY
STORAGE
OBSERVABILITY
APPLICATION
NETWORK
FEATURE
OTHER
```

Example:

```yaml
configurationItem:
  key: NOTIFICATION_API_BASE_URL
  category: EXTERNAL_SERVICE
  required: true
  classification: NON_SECRET
```

The skill must not rely on undocumented runtime variables.

---

# Configuration Classification

Every item must be classified as:

```text
NON_SECRET
SECRET_REFERENCE
DERIVED_RUNTIME_VALUE
```

Examples:

```text
API_BASE_URL
→ NON_SECRET

DOPPLER_TOKEN
→ SECRET_REFERENCE

platform-injected HOSTNAME
→ DERIVED_RUNTIME_VALUE
```

The skill manages secret references only, never real secret values.

If sensitive material is stored as ordinary configuration:

return:

`SECRET_CLASSIFICATION_RISK`

and request:

`SECURITY_REVIEW_REQUIRED`

---

# Configuration Ownership

Every important configuration item should identify its owner.

Possible owners:

```text
APPLICATION_TEAM
DEVOPS
ASI_PLATFORM
IDENTITY_TEAM
EXTERNAL_PROVIDER
DATABASE_TEAM
OTHER_GCBA_SYSTEM
```

Example:

```yaml
OIDC_CLIENT_ID:
  owner: IDENTITY_TEAM

DATABASE_HOST:
  owner: ASI_PLATFORM

FEATURE_X_ENABLED:
  owner: APPLICATION_TEAM
```

The harness must not invent values owned by another team.

If ownership is unknown:

return:

`CONFIGURATION_OWNERSHIP_UNRESOLVED`

---

# External Configuration

ES0901 M2 requires environment-related variables to remain outside application code.

Detect patterns such as:

```text
hardcoded DEV/QA/HML/PRD URLs
hardcoded database hosts
hardcoded protocols
hardcoded environment filesystem paths
hardcoded provider environment
hardcoded identity callbacks
```

If detected:

return:

`ENVIRONMENT_VALUE_HARDCODED`

Preferred model:

```text
application code
      ↓
logical configuration key
      ↓
runtime injection
      ↓
environment-specific value
```

---

# Configuration Sources

Possible sources may include:

```text
ConfigMap
Secret reference
environment variable
external YAML/properties file
approved runtime configuration file
platform-provided value
```

The exact mechanism depends on the approved stack/platform.

Do not impose one mechanism globally.

---

# DNS over IP

ES0901 Section 6.5 requires server references by DNS rather than IP.

Detect:

```text
hardcoded IPv4
hardcoded IPv6
raw environment-specific server addresses
```

when they represent service/server dependencies.

Return:

`DIRECT_IP_REFERENCE_RISK`

Do not invent a replacement DNS name. Request the authoritative reference.

---

# Protocol Configuration

Inspect:

```text
base URLs
service URLs
callback URLs
redirect URLs
protocol assumptions
```

Do not silently replace `http` with `https` without environment evidence.

When protocol behavior is unresolved:

return:

`PROTOCOL_CONFIGURATION_UNRESOLVED`

---

# Cross-Environment Isolation

Actively detect leakage such as:

```text
PRD → DEV database
QA → PRD service
HML → PRD credentials
DEV → production SaaS without approval
PRD → QA identity client
QA callback → DEV frontend
```

Return:

`CROSS_ENVIRONMENT_CONFIGURATION_RISK`

Production-impacting misrouting should be considered high risk.

---

# Production Guard

Unknown production values must remain explicitly unresolved.

Use:

```text
known production value
→ configure/reference

unknown production value
→ explicit unresolved placeholder/status
```

Never copy lower-environment values into production as a temporary shortcut.

Return:

`PRODUCTION_CONFIGURATION_INCOMPLETE`

when mandatory PRD configuration is missing.

---

# LOCAL Is Not DEV

```text
LOCAL
≠
DEV
```

Local development may use supported local values such as:

```text
localhost
mock services
local database
provider sandbox
local environment variables
```

Do not promote local assumptions into GCBA environments.

---

# Internal Service Mapping

Coordinate with `dev-service-integration`.

Responsibility split:

```text
dev-environments
→ which service endpoint/reference applies in each environment

dev-service-integration
→ how the application consumes the service contract
```

If mapping is unresolved:

return:

`DEPENDENCY_ENVIRONMENT_MAPPING_UNRESOLVED`

---

# External Provider Mapping

Coordinate with `dev-external-integration`.

GCBA environments may map many-to-one to provider environments.

Example:

```text
GCBA DEV ──┐
GCBA QA  ──┼──→ PROVIDER_TEST
GCBA HML ──┘

GCBA PRD ─────→ PROVIDER_PRODUCTION
```

Do not assume one-to-one mapping.

If unresolved:

return:

`EXTERNAL_ENVIRONMENT_MAPPING_UNRESOLVED`

---

# Identity Mapping

Coordinate with `dev-openid-connect` or `dev-miba`.

`dev-environments` owns the environment matrix/reference mapping.

Identity skills own semantic correctness of:

```text
client
redirect URI
logout URI
claims
provider flow
```

Example:

```yaml
DEV:
  identityClientReference: OIDC_CLIENT_DEV

QA:
  identityClientReference: OIDC_CLIENT_QA
```

Real client/secret values remain external.

---

# Database Mapping

Responsibility split:

```text
dev-persistence
→ schema, migrations, persistence behavior

dev-environments
→ DB endpoint/schema/user reference per environment
```

If mapping is unclear:

return:

`DATABASE_ENVIRONMENT_MAPPING_UNRESOLVED`

---

# Environment Switches

Environment-dependent behavior must be explicit.

Avoid hidden logic such as:

```text
if hostname contains "qa"
if IP starts with ...
if URL includes "dev"
```

when an explicit configuration key should exist.

Return:

`IMPLICIT_ENVIRONMENT_BEHAVIOR_RISK`

when environment behavior is inferred indirectly.

---

# Environment Logic in Code

Detect code such as:

```text
if DEV:
    endpoint = A
elif QA:
    endpoint = B
```

Configuration should normally resolve these differences.

If application/business logic becomes environment-aware unnecessarily:

return:

`ENVIRONMENT_LOGIC_IN_CODE_RISK`

---

# Configuration Contract

Treat runtime configuration keys as a contract.

Each logical key should define:

```text
name
purpose
required/optional
type
secret classification
owner
required environments
default behavior
```

Example:

```yaml
configurationContract:

  DATABASE_HOST:
    required: true
    type: string
    classification: NON_SECRET
    owner: ASI_PLATFORM

  EXTERNAL_API_TOKEN:
    required: true
    type: secret-reference
    classification: SECRET_REFERENCE
    owner: EXTERNAL_PROVIDER
```

If application expectations and deployment configuration differ:

return:

`CONFIGURATION_CONTRACT_MISMATCH`

---

# Configuration Completeness

Build a matrix for required keys.

Example:

```text
                          DEV   QA   HML   PRD
DATABASE_HOST              ✓    ✓    ✓     ✓
SERVICE_A_BASE_URL          ✓    ✓    ✓     ✓
OIDC_CLIENT_REFERENCE       ✓    ✓    ✓     ?
PROVIDER_TOKEN_REFERENCE    ✓    ✓    ✓     ?
```

Do not mark an environment ready when mandatory values remain unresolved.

Return:

`ENVIRONMENT_CONFIGURATION_INCOMPLETE`

---

# Configuration Drift

Distinguish:

```text
expected value difference
vs
unexpected key/structure difference
```

Example:

```text
DEV has FEATURE_X_TIMEOUT
PRD has no FEATURE_X_TIMEOUT
```

Return:

`ENVIRONMENT_CONFIGURATION_DRIFT`

when the configuration model diverges unexpectedly.

---

# Safe Defaults

Defaults must never silently route to production-capable dependencies.

Unsafe examples:

```text
missing SERVICE_URL → PRD URL
missing DB_HOST → production DB
missing provider environment → production provider
missing identity client → production client
```

Return:

`UNSAFE_CONFIGURATION_DEFAULT`

Prefer fail-fast behavior for critical missing configuration when consistent with project architecture.

---

# Missing Configuration Behavior

Critical missing configuration should not fail silently.

Possible approved behavior:

```text
fail startup with controlled diagnostic
explicitly disable optional feature
use documented degraded behavior
```

Do not invent fallback behavior.

If unresolved:

return:

`MISSING_CONFIGURATION_BEHAVIOR_UNRESOLVED`

---

# ConfigMap Boundary

When OpenShift ConfigMaps are used:

```text
dev-environments
→ logical keys, values by environment, completeness, mapping

dev-openshift
→ OpenShift resource/manifests and injection mechanics
```

Do not duplicate responsibilities.

---

# Secret Boundary

This skill may define:

```text
secret logical reference
required environment
owning team
```

It never manages actual secret content.

If a human/team must supply a secret, report the unresolved reference and owner.

---

# Artifact / Environment Decoupling

Where the deployment model promotes the same artifact between environments, verify that external configuration is sufficient for the same artifact to operate unchanged.

If a new application artifact is required solely because environment values changed:

return:

`ARTIFACT_ENVIRONMENT_COUPLING_RISK`

and coordinate with `dev-deployment`.

---

# Environment Readiness

Suggested configuration readiness states:

```text
NOT_CONFIGURED
PARTIAL
READY_FOR_DEPLOYMENT
BLOCKED
```

Deployment/functional acceptance are separate concerns.

This skill must not declare functional acceptance.

---

# Documentation

Maintain a transferable configuration contract covering:

```text
logical key
purpose
classification
owner
required environments
configuration source
safe example format where applicable
```

Never document real secrets.

Where project/standard deployment rules require configuration manifests or README references, verify they are current.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

configuration.inspect
configuration.contract.inspect
environment.config.inspect
environment.mapping.inspect

deployment.config.inspect
dns.reference.inspect
secret.reference.inspect
```

Optional/specialized:

```text
openshift.configmap.inspect
openshift.secret.reference.inspect
external.provider.config.inspect
identity.config.inspect
service.discovery.inspect
```

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

```text
environment configuration externalization
hardcoded environment values
direct IP references
configuration contract
configuration completeness
cross-environment leakage
production configuration
unsafe defaults
secret classification
environment drift
artifact/environment coupling
```

If a formal Check is unavailable:

return:

`CHECK_GAP`

The skill must not self-approve official Checks.

---

# Result Statuses

Supported statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

ENVIRONMENT_MODEL_UNRESOLVED
ENVIRONMENT_CONFIGURATION_INCOMPLETE
ENVIRONMENT_CONFIGURATION_DRIFT

CONFIGURATION_OWNERSHIP_UNRESOLVED
CONFIGURATION_CONTRACT_MISMATCH

ENVIRONMENT_VALUE_HARDCODED
ENVIRONMENT_LOGIC_IN_CODE_RISK
IMPLICIT_ENVIRONMENT_BEHAVIOR_RISK

SECRET_CLASSIFICATION_RISK
CROSS_ENVIRONMENT_CONFIGURATION_RISK
PRODUCTION_CONFIGURATION_INCOMPLETE

DIRECT_IP_REFERENCE_RISK
PROTOCOL_CONFIGURATION_UNRESOLVED

DEPENDENCY_ENVIRONMENT_MAPPING_UNRESOLVED
EXTERNAL_ENVIRONMENT_MAPPING_UNRESOLVED
DATABASE_ENVIRONMENT_MAPPING_UNRESOLVED

UNSAFE_CONFIGURATION_DEFAULT
MISSING_CONFIGURATION_BEHAVIOR_UNRESOLVED
ARTIFACT_ENVIRONMENT_COUPLING_RISK

SECURITY_REVIEW_REQUIRED
ARCHITECTURE_REVIEW_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

```yaml
environmentResult:

  status: COMPLETE

  environments:
    - LOCAL
    - DEV
    - QA
    - HML
    - PRD

  lifecycle:
    promotionOrder:
      - DEV
      - QA
      - HML
      - PRD

  configurationContract:

    DATABASE_HOST:
      classification: NON_SECRET
      owner: ASI_PLATFORM
      required:
        - DEV
        - QA
        - HML
        - PRD

    OIDC_CLIENT_SECRET:
      classification: SECRET_REFERENCE
      owner: IDENTITY_TEAM
      required:
        - DEV
        - QA
        - HML
        - PRD

  mapping:

    DEV:
      database: database-dev
      serviceA: service-a-dev
      externalProvider: PROVIDER_TEST

    QA:
      database: database-qa
      serviceA: service-a-qa
      externalProvider: PROVIDER_TEST

    HML:
      database: database-hml
      serviceA: service-a-hml
      externalProvider: PROVIDER_TEST

    PRD:
      database: database-prd
      serviceA: service-a-prd
      externalProvider: PROVIDER_PRODUCTION

  validation:
    externalized: true
    hardcodedValuesDetected: false
    directIpReferencesDetected: false
    crossEnvironmentLeakageDetected: false
    unsafeDefaultsDetected: false

  readiness:
    DEV: READY_FOR_DEPLOYMENT
    QA: READY_FOR_DEPLOYMENT
    HML: READY_FOR_DEPLOYMENT
    PRD: PARTIAL

  unresolved:
    PRD:
      - OIDC_CLIENT_SECRET
      - PROVIDER_PRODUCTION_TOKEN

  reviews:
    securityRequired: false
    architectureRequired: false

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
configuration inventory
matrix generation
hardcoded URL/IP detection
completeness checks
simple environment mappings
documentation updates
```

## REASONING

Consider when:

```text
many services/providers differ by environment
environment naming is inconsistent
identity/external-provider mappings interact
configuration drift exists
artifact behavior differs by environment
multiple configuration repositories exist
ownership is ambiguous
```

## PREMIUM

Consider only when environment topology or production-routing risk is exceptionally complex and lower-tier reasoning is insufficient.

Premium execution must pass the orchestrator Human Model Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- environment model is unclear
- configuration ownership is unresolved
- production configuration is incomplete
- cross-environment leakage exists
- sensitive data appears in non-secret configuration
- application logic is environment-coupled
- DNS/service reference is unavailable
- external/identity mapping is unresolved
- artifact behavior differs by environment
- required capability/check is missing
- security or architecture review is required

---

# Prohibited Behavior

This skill must not:

- invent environment-specific values
- invent production endpoints
- copy DEV/QA/HML credentials into PRD
- store real secret values
- hardcode environment URLs in source
- use raw IPs where DNS is required
- infer environment from host/IP when explicit configuration should exist
- silently point non-production to production
- silently point production to test/sandbox
- assume external-provider environments map one-to-one with GCBA environments
- treat LOCAL as DEV
- define unsafe production defaults
- mark environments ready with mandatory unresolved configuration
- silently modify deployment architecture
- create Tools directly
- self-approve formal Checks
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- identifies actual project environments
- maps environments to platform and dependencies
- inventories all environment-dependent configuration
- classifies secrets correctly
- keeps configuration outside application code
- uses DNS/service references where required
- detects cross-environment leakage
- prevents guessed PRD configuration
- distinguishes LOCAL from DEV
- validates internal/external/identity/database mappings
- detects configuration drift
- defines a maintainable configuration contract
- prevents unsafe defaults
- identifies missing-config behavior
- validates artifact/environment decoupling
- returns readiness and unresolved values explicitly
- produces structured evidence for the orchestrator

---

# Source References

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas:

```text
3 / C2
6.4
6.5
7.1 / M2
Annex III
```

This skill must not convert project-specific examples into universal environment values.
