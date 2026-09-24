# Check: custom-error-message-compliance

## Purpose

Deterministically verify that every externally observable error-message surface is application-controlled/customized and does not fall back to raw/default technical output.

## Inputs

```text
userFacingErrorPresent
error-surface inventory
frontend/backend/API error handlers
framework/server error configuration
application/API contracts
unit/integration/contract tests
authorized QA error-path evidence
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Error-surface coverage

Inventory every material externally observable error surface.

Incomplete:

`ERROR_SURFACE_COVERAGE_UNRESOLVED`

### 3. Resolve presentation owner

For each surface classify:

```text
APPLICATION_CONTROLLED
FRAMEWORK_DEFAULT
SERVER_PLATFORM_DEFAULT
UNRESOLVED
```

A framework/server-owned surface is not automatically a FAIL if project configuration explicitly customizes the exposed result; evaluate actual behavior.

### 4. Evaluate exposed message

Classify each inspected/tested scenario:

```text
CUSTOMIZED_SAFE
DEFAULT_ERROR_EXPOSED
RAW_TECHNICAL_ERROR_EXPOSED
INFRASTRUCTURE_DETAIL_EXPOSED
UNRESOLVED
```

Confirmed default/raw/infrastructure exposure causes FAIL.

### 5. Technical detail

Where applicable, detect exposed evidence such as:

```text
stack trace
server/IP/path
framework debug metadata
database exception/driver detail
container/platform diagnostic
```

Do not create a universal banned-token list and call it proof.

Use actual exposed error evidence.

### 6. HTTP/API semantics

If the surface is HTTP/API, verify that customization does not incorrectly mask the actual error state where an authoritative contract/standard requires protocol status preservation.

If customization converts an authoritative error into misleading success semantics:

`HTTP_ERROR_SEMANTICS_MASKED`

Do not invent exact codes where no authoritative contract defines them.

### 7. Frontend/backend independence

A customized frontend does not hide a raw API.

A safe API does not prove every frontend/backoffice/mobile error path is customized.

Evaluate each exposed surface independently.

### 8. Internal logs

Do not inspect internal-only logs as if they were user-facing messages.

If internal diagnostic text is forwarded directly to a consumer, it becomes an exposed surface and must be evaluated.

### 9. Runtime evidence

Use safe synthetic scenarios.

Examples may include:

```text
known validation error
not-found/invalid request
controlled unexpected exception in QA test harness
integration failure fixture
```

Do not cause destructive infrastructure outages merely to produce an error page.

Unsafe conditions:

`ERROR_MESSAGE_TEST_UNSAFE`

### 10. Aggregate

All applicable exposed error surfaces must be `CUSTOMIZED_SAFE`.

Any confirmed:

```text
DEFAULT_ERROR_EXPOSED
RAW_TECHNICAL_ERROR_EXPOSED
INFRASTRUCTURE_DETAIL_EXPOSED
```

causes FAIL.

Any unresolved material surface prevents PASS.

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
ERROR_SURFACE_COVERAGE_UNRESOLVED
DEFAULT_ERROR_EXPOSED
RAW_TECHNICAL_ERROR_EXPOSED
INFRASTRUCTURE_DETAIL_EXPOSED
ERROR_CUSTOMIZATION_UNRESOLVED
HTTP_ERROR_SEMANTICS_MASKED
ERROR_MESSAGE_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply Vu5 validation parity PASS, Vu7 base-software disclosure PASS, OWASP compliance, complete observability, or official security approval.
