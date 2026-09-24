# ES0902 Vu5 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu5:

```text
Vu5 — Toda validación del lado del cliente, debe estar espejada del lado del servidor.
```

Vu5 is a client/server validation parity rule.

The normative direction is:

```text
CLIENT-SIDE VALIDATION
→ equivalent or stronger SERVER-SIDE ENFORCEMENT
```

The rule does not require identical code, identical libraries, identical error messages, or identical UI behavior.

## Matrix Binding

```yaml
ruleKey: ES0902.Vu5
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - clientValidationPresent

primaryAgents:
  - dev-security

policies:
  - client-validation-server-mirroring-required

checks:
  - client-server-validation-parity

reviews: []
```

Do not rename these identifiers.

## Applicability

`clientValidationPresent` is evidence-backed.

```text
TRUE
→ one or more material client-side input validations exist in governed scope

FALSE
→ authoritative evidence establishes no material client-side validation exists in governed scope

UNRESOLVED
→ client-side validation coverage cannot be established
```

Do not infer FALSE merely because frontend validation is implicit, declarative, or generated.

Do not infer TRUE from a validation library dependency alone.

## Directionality

Vu5 requires:

```text
client constraint
→ server counterpart
```

It does not require every server-side validation to be duplicated on the client.

Server-only validation is allowed.

## Validation Inventory

Inventory material client-side validation constraints.

Operational categories may include:

```text
required
type
length
range
format
pattern
allowed values
cross-field constraint
file type/size
structured payload shape
domain/business input constraint
```

These categories are operational, not new normative rules.

Incomplete coverage:

`CLIENT_VALIDATION_COVERAGE_UNRESOLVED`

## Parity Meaning

"Mirrored" means the server independently enforces the same semantic constraint, or a compatible stronger constraint.

Examples:

```text
client: required
server: accepts null
→ not mirrored

client: enum [A,B]
server: arbitrary string
→ not mirrored

client: maxLength 100
server: maxLength 80
→ potentially stronger, but contract compatibility must be evidenced
```

Do not require source-code symmetry.

## Client Validation Is Not a Security Boundary

The server must remain secure when client validation is bypassed.

A modified request, disabled client validator, direct API call, or alternate client must not bypass server-side validation.

## Validation vs Authorization

Keep separate:

```text
validation
→ is the input acceptable?

authorization
→ is this actor allowed to perform the operation?
```

Vu5 does not replace authorization controls.

## Validation vs Sanitization

Do not treat client-side sanitization, masking, formatting, or normalization as sufficient server validation.

## Equivalent or Stronger Server Validation

Accepted parity states:

```text
EQUIVALENT
SERVER_STRONGER_COMPATIBLE
```

Non-compliant:

```text
SERVER_WEAKER
SERVER_MISSING
```

Unknown:

`VALIDATION_EQUIVALENCE_UNRESOLVED`

Do not auto-pass based on similar names or shared DTO/library presence.

## Error Behavior

Vu5 does not define exact status codes or error messages.

The server must reject invalid input rather than process it as valid.

## Multi-Surface Coverage

Evaluate every applicable client/API pair independently.

Examples:

```text
public frontend → backend API
backoffice → backend API
mobile client → backend API
legacy frontend → backend API
```

Incomplete mapping:

`CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED`

## Generated / Shared Validation Schemas

Shared schemas may provide strong evidence when both client and server demonstrably enforce them.

Shared package presence alone is insufficient.

## Direct Server Verification

Preferred evidence order:

```text
server validation configuration/code
unit/integration tests
API contract tests
authorized QA direct-request tests
```

Use safe synthetic values and non-destructive test cases.

Unsafe direct testing:

`SERVER_VALIDATION_TEST_UNSAFE`

## Relationship with ES0901 P5

ES0902 Vu5 may overlap with ES0901 P5.

Until ES0901 P5 is implemented and its exact semantics are compared, keep:

`EQUIVALENCE_REVIEW_REQUIRED`

Do not bind or auto-reuse a final P5 result before that review.

## Completion Criteria

- exact matrix binding preserved
- clientValidationPresent evidence-backed
- every material client-side validation inventoried
- every client constraint mapped to independent server enforcement
- semantic parity evaluated
- client bypass cannot bypass the server constraint
- server-only validation allowed
- validation separate from authorization
- shared schema presence alone cannot PASS
- safe direct-server evidence supported
- ES0901 P5 remains EQUIVALENCE_REVIEW_REQUIRED
- no Agent or Skill created
