# Check: base-software-data-disclosure-configuration

## Purpose

Deterministically verify that the effective base-software configuration does not disclose private data to unauthorized consumers.

## Inputs

```text
base-software inventory
environment/deployment binding
private-data classification evidence
base-software configuration
surface/exposure inventory
authorization context
authorized static/runtime test evidence
```

## Procedure

### 1. Base-software inventory

Resolve all material base-software components for the evaluated environment.

Incomplete:

`BASE_SOFTWARE_INVENTORY_UNRESOLVED`

### 2. Private-data classification

Resolve the private-data categories relevant to the application and base-software surfaces from authoritative evidence.

Unknown required classification:

`PRIVATE_DATA_CLASSIFICATION_UNRESOLVED`

### 3. Disclosure-surface inventory

Map material surfaces where base software may return, serve, expose, or make data accessible.

Incomplete:

`DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED`

### 4. Effective configuration

For each component/surface, resolve the effective environment-specific configuration.

Possible states:

```text
RESOLVED
UNRESOLVED
```

Unknown effective configuration:

`BASE_SOFTWARE_CONFIGURATION_UNRESOLVED`

### 5. Authorization context

For each tested/inspected disclosure path, establish whether the consumer is authorized for the private data.

Do not label legitimate authorized access as leakage.

### 6. Disclosure verdict

Per surface:

```text
NO_PRIVATE_DATA_DISCLOSURE
AUTHORIZED_PRIVATE_DATA_ACCESS
UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE
UNRESOLVED
```

Confirmed unauthorized disclosure:

```text
UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE
→ FAIL
```

### 7. Default/debug/management behavior

Inspect actual effective behavior.

Do not automatically fail a default endpoint by name.

Fail only when the configuration causes prohibited disclosure or when another bound control explicitly prohibits the exposure.

### 8. Version/banner boundary

Version disclosure alone does not establish Vu7 failure.

Route version/tool compliance to C3/Ve1 or another applicable control unless authoritative evidence binds the disclosure to private-data protection.

### 9. Vu6 overlap

If a base-software error response exposes private data:

```text
share evidence
evaluate Vu6 separately
evaluate Vu7 separately
```

Do not copy final results.

### 10. Environment binding

Do not reuse DEV result as QA/HML/PRD proof without matching deployment/configuration evidence.

### 11. Runtime safety

Prefer static/configuration evidence.

If runtime validation is needed:

```text
authorized QA/test environment
synthetic/redacted fixtures
non-destructive requests
no real unauthorized access to private data
```

Unsafe:

`BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE`

### 12. Evidence hygiene

Do not store raw disclosed private values.

Use redaction/fingerprints/categories and evidence references.

### 13. Aggregate

PASS requires:

```text
complete material inventory
resolved required classification
resolved material configurations/surfaces
no confirmed unauthorized private-data disclosure
```

Any confirmed unauthorized disclosure causes FAIL.

Any material unresolved dimension prevents PASS.

## Overall Results

```text
PASS
FAIL
BASE_SOFTWARE_INVENTORY_UNRESOLVED
PRIVATE_DATA_CLASSIFICATION_UNRESOLVED
DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED
BASE_SOFTWARE_CONFIGURATION_UNRESOLVED
UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE
BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply:

```text
Vu6 PASS
C3/Ve1 PASS
general secret-management compliance
Repository Integrity PASS
official security approval
```
