---
id: custom-error-messages-required
type: POLICY
rule: Vu6
---

# Policy: custom-error-messages-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu6
```

## Requirement

Every externally observable application error message must be application-controlled/customized rather than an unhandled/default technical error exposed as-is.

## No Invented Copy Contract

Vu6 does not define:
- exact message text
- exact localization
- exact JSON structure
- exact UI component
- exact HTTP status code

Do not invent these requirements.

## Supporting Error-Handling Boundary

Where HTTP/API errors are involved:

```text
customized body/presentation
must not
mask authoritative protocol error semantics
```

Unexpected errors must not expose infrastructure/technical properties when supporting authoritative development-standard evidence applies.

## Non-Compliant Patterns

Examples of evidence that may violate the Policy:

```text
raw stack trace
default framework debug/error page
server error page/banner
filesystem path
internal IP
database-driver exception text
unhandled exception payload
infrastructure/platform diagnostic exposed externally
```

## Internal Logging Boundary

Technical detail may exist in protected internal logs.

Do not require internal logs to be user-friendly.

Do not expose those details to consumers.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
ERROR_SURFACE_COVERAGE_UNRESOLVED
DEFAULT_ERROR_EXPOSED
RAW_TECHNICAL_ERROR_EXPOSED
INFRASTRUCTURE_DETAIL_EXPOSED
ERROR_CUSTOMIZATION_UNRESOLVED
HTTP_ERROR_SEMANTICS_MASKED
ERROR_MESSAGE_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
