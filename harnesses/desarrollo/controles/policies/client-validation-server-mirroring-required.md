---
id: client-validation-server-mirroring-required
type: POLICY
rule: Vu5
---

# Policy: client-validation-server-mirroring-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu5
```

## Requirement

Every material validation enforced on the client side must have independent server-side enforcement of the same semantic constraint or a compatible stronger constraint.

## Direction

Required:

```text
CLIENT → SERVER
```

Not required:

```text
SERVER → CLIENT
```

Server-only validations do not violate Vu5.

## No Client Trust

The server must not rely on client validation having executed.

Modified/direct requests must still be rejected when they violate the server constraint.

## No False Equivalence

The following alone do not establish parity:

```text
same field name
same DTO name
same library installed
same schema imported
frontend validation message
HTML input attributes
TypeScript types
client-side sanitization
```

Require actual server enforcement evidence.

## Semantic Parity

Accepted:

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

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
CLIENT_VALIDATION_COVERAGE_UNRESOLVED
CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED
SERVER_VALIDATION_MISSING
SERVER_VALIDATION_WEAKER
VALIDATION_EQUIVALENCE_UNRESOLVED
SERVER_VALIDATION_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
