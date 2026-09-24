# Check: client-server-validation-parity

## Purpose

Deterministically verify that every material client-side validation has independent server-side enforcement.

## Inputs

```text
clientValidationPresent
client validation inventory
client/server operation mapping
server validation code/configuration
API/schema contracts
unit/integration/contract tests
authorized direct-server test evidence
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Client validation coverage

Inventory every material client-side validation in governed scope.

Incomplete:

`CLIENT_VALIDATION_COVERAGE_UNRESOLVED`

### 3. Map client rule to server operation

For each client validation, resolve the corresponding server input path.

Unknown mapping:

`CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED`

### 4. Identify server enforcement

For each mapped client constraint:

```text
PRESENT
MISSING
UNRESOLVED
```

`MISSING`:

```text
SERVER_VALIDATION_MISSING
→ FAIL
```

### 5. Compare semantics

Classify parity:

```text
EQUIVALENT
SERVER_STRONGER_COMPATIBLE
SERVER_WEAKER
UNRESOLVED
```

Examples:

```text
client required / server required
→ EQUIVALENT

client maxLength 100 / server maxLength 80
→ SERVER_STRONGER_COMPATIBLE only if project/API contract supports it

client enum A,B / server arbitrary string
→ SERVER_WEAKER

client min 1 / server no lower-bound check
→ SERVER_WEAKER
```

`SERVER_WEAKER` causes FAIL.

Unknown semantic relation:

`VALIDATION_EQUIVALENCE_UNRESOLVED`

### 6. Verify enforcement

Where technically applicable, verify that invalid direct input is rejected server-side even when client validation is bypassed.

Evidence may come from:

```text
unit test
integration test
API contract test
authorized QA direct-request test
```

Do not require runtime testing when existing evidence is already authoritative and sufficient.

### 7. Shared/generated schema

If client and server share a schema/library, confirm server execution on the relevant request path.

Shared package presence alone does not PASS.

### 8. Validation vs authorization

Do not satisfy missing validation with an authorization failure.

The test must reach the validation boundary using an appropriately authorized test context when safe and required.

### 9. Error behavior

The server must reject invalid input.

Vu5 does not mandate exact status code/message.

### 10. Multi-client coverage

Evaluate each applicable client/server pair independently.

### 11. Runtime safety

Use synthetic/non-sensitive values and avoid destructive state changes.

Prefer QA/test environments.

Unsafe conditions:

`SERVER_VALIDATION_TEST_UNSAFE`

### 12. Aggregate

All material client-side validations must have server parity.

Any `SERVER_VALIDATION_MISSING` or `SERVER_VALIDATION_WEAKER` causes FAIL.

Any unresolved applicable mapping/equivalence prevents PASS.

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
CLIENT_VALIDATION_COVERAGE_UNRESOLVED
CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED
SERVER_VALIDATION_MISSING
SERVER_VALIDATION_WEAKER
VALIDATION_EQUIVALENCE_UNRESOLVED
SERVER_VALIDATION_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply authorization correctness, business-rule completeness, safe error messages, OWASP compliance, ES0901.P5 PASS, or official security approval.
