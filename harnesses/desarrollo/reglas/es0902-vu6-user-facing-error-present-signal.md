# Signal: userFacingErrorPresent

## Purpose

Resolve ES0902 Vu6 applicability for externally observable application error messages.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when evidence establishes one or more application error-message surfaces observable by a governed consumer.

Examples may include:

```text
frontend error UI
API error payload
backend error page
mobile error UI/payload
backoffice error
integration error surfaced by the application
```

## FALSE

Use only when authoritative evidence establishes that governed scope exposes no error-message surface.

Do not infer FALSE because:
- a framework handles errors
- one inspected path returns only status codes
- no explicit error component is named
- source inspection is incomplete

## UNRESOLVED

Use when:
- error-path coverage is incomplete
- unhandled/default error behavior is unknown
- secondary/mobile/backoffice/API surfaces may exist
- ownership of the exposed error cannot be established

## Evidence

Preserve:

```text
surfaceId
consumer type
operation/path
error class/scenario
presentation/response owner
evidence reference
environment
```

Do not persist raw secrets, personal data, stack traces containing sensitive values, or credential material.
