# Signal: clientValidationPresent

## Purpose

Resolve ES0902 Vu5 applicability from client-side validation evidence.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when at least one material client-side validation is evidenced on a governed input path.

Examples may include:

```text
form validation
frontend DTO/schema validation
mobile input validation
file-selection validation
client-side cross-field validation
generated client validation
```

## FALSE

Use only when authoritative evidence establishes that governed scope contains no material client-side validation.

Do not infer FALSE because validation is declarative/generated or because explicit validation functions were not found.

## UNRESOLVED

Use when client validation coverage, generated behavior, secondary clients, or validation ownership cannot be established.

## Evidence

Preserve references to:

```text
client surface ID
input/field/operation
constraint ID/type
client implementation/schema reference
server endpoint/operation reference when known
environment/scope
```

Do not store raw sensitive values.
