# ES0902 Vu7 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu7:

```text
Vu7 — Todo el software de base debe estar configurado para no entregar datos privados.
```

Vu7 is a base-software configuration and data-disclosure control.

It governs the effective configuration of the base software used by the application so that the base software does not expose private data to unauthorized consumers.

## Matrix Binding

```yaml
ruleKey: ES0902.Vu7
category: SECURITY_PRINCIPLE

applicability:
  mode: ALWAYS

primaryAgents:
  - dev-security

policies:
  - base-software-private-data-disclosure-prohibited

checks:
  - base-software-data-disclosure-configuration

reviews: []
```

Do not rename these identifiers.

## ALWAYS Semantics

Vu7 is an ALWAYS rule.

Do not create an applicability Signal to avoid evaluation.

If the governed deployment/runtime stack cannot be established:

`BASE_SOFTWARE_INVENTORY_UNRESOLVED`

This prevents PASS.

## Base-Software Scope

Use authoritative project/deployment/architecture evidence to determine the base-software inventory.

Potential categories may include, when present:

```text
operating system
web server / reverse proxy
application server / runtime
database engine
container/runtime/platform component
message broker
cache
document server
other infrastructure-provided runtime software
```

This is an operational inventory aid, not a new normative taxonomy.

## Private-Data Boundary

ES0902 Vu7 does not define a complete taxonomy of "datos privados".

Do not invent one.

Use authoritative classification/evidence from project/GCBA security, privacy, architecture, assessment, or contractual sources.

If a disclosure path may expose private data but classification cannot be established:

`PRIVATE_DATA_CLASSIFICATION_UNRESOLVED`

Do not silently convert "private" into "all technical metadata".

## Configuration, Not Only Code

Vu7 targets effective base-software configuration.

Relevant evidence may live in:

```text
OpenShift/Kubernetes manifests
ConfigMaps / Secret references
web-server configuration
application-server/runtime configuration
database/network configuration
container/runtime configuration
reverse-proxy configuration
platform routing configuration
infrastructure configuration
```

Application source code alone cannot prove Vu7.

## Disclosure Surfaces

Evaluate material base-software surfaces that can return or expose data.

Operational examples may include:

```text
directory/file listing
static file serving
backup/config file exposure
default management/status/debug endpoints
default error documents
server/runtime diagnostic endpoints
database/admin interfaces
metrics/status endpoints where private data may be present
temporary/generated files exposed by the server
misconfigured document/file roots
```

A surface is non-compliant when its effective configuration causes unauthorized disclosure of authoritatively classified private data.

## Version/Banner Boundary

Version disclosure and private-data disclosure are related concerns but are not automatically identical.

Do not fail Vu7 solely because a version banner exists unless authoritative classification/control evidence makes that disclosure part of Vu7 scope.

Version/tool compliance belongs to C3/Ve1 and other applicable controls.

## Vu6 Boundary

```text
Vu6
→ externally observable error messages are customized

Vu7
→ base software is configured not to disclose private data
```

Shared evidence is allowed; final rule results remain independent.

## Environment Binding

Vu7 is environment-sensitive.

DEV configuration does not prove QA/HML/PRD configuration.

Evidence should identify the evaluated environment and deployment/configuration binding.

## Static-First Validation

Preferred order:

```text
runtime/deployment configuration inspection
manifest/configuration analysis
base-software configuration tests
authorized QA endpoint/file-path validation
```

Do not probe production destructively.

Do not attempt unauthorized access to real private data.

Unsafe validation:

`BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE`

## Evidence Hygiene

Never persist raw private data merely to prove disclosure.

Record:

```text
data class/category
surface
location/path
redacted sample
fingerprint
evidence reference
authorization context
```

Do not copy credentials, tokens, personal data, private keys, or sensitive payloads into reports.

## Relationships

Repository Integrity may detect suspicious configuration changes that weaken Vu7 controls, but its verdict is not the Vu7 result.

Security Reporting consumes Vu7 findings/evidence through the shared ledger/summary.

## Completion Criteria

- exact matrix binding preserved
- ALWAYS semantics preserved
- base-software inventory evidence-backed
- private-data classification authoritative
- effective runtime configuration evaluated
- disclosure surfaces mapped to authorization/data classification
- default configuration not blindly trusted or blindly failed
- version disclosure not automatically conflated with private data
- Vu6/C3/Ve1/Repository Integrity remain independent
- environment binding preserved
- runtime validation safe
- evidence redacted
- no Agent or Skill created
