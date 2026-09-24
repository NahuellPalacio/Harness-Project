# ES0902 Vu6 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu6:

```text
Vu6 — Todos los mensajes de error deben estar customizados.
```

Vu6 is an externally observable error-message control.

The core objective is to ensure that application consumers do not receive raw/default technical error output that bypasses application-controlled error handling.

## Matrix Binding

```yaml
ruleKey: ES0902.Vu6
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - userFacingErrorPresent

primaryAgents:
  - dev-security

policies:
  - custom-error-messages-required

checks:
  - custom-error-message-compliance

reviews: []
```

Do not rename these identifiers.

## Applicability

`userFacingErrorPresent` is evidence-backed.

For Vu6, externally observable error messages may be delivered to:

```text
human UI users
API consumers
mobile clients
backoffice clients
other governed application consumers
```

Internal-only logs are outside this signal.

Use:

```text
TRUE
→ one or more externally observable application error-message surfaces exist

FALSE
→ authoritative evidence establishes no externally observable error-message surface exists

UNRESOLVED
→ error surfaces/paths are incomplete or cannot be established
```

Do not infer FALSE because a framework handles errors.

## Error Surface Inventory

Evaluate material error surfaces independently.

Examples may include:

```text
frontend error UI
backend-rendered error page
API error payload
mobile error UI/payload
authentication/integration error surfaced by the application
reverse-proxy/framework default error page exposed through the application
validation/business error surfaced to consumers
unexpected/unhandled application error
```

Incomplete coverage:

`ERROR_SURFACE_COVERAGE_UNRESOLVED`

## Meaning of Customized

The source does not define mandatory wording, localization, visual design, HTTP code, or JSON shape.

Operationally, a customized error must be demonstrably application-controlled rather than an unhandled/default framework/server diagnostic exposed as-is.

Do not invent:

```text
specific copy text
specific GCBA wording
specific JSON schema
specific translation language
specific correlation ID format
specific visual component
```

unless another authoritative source requires it.

## Technical Detail Disclosure

Relevant ES0901 v6.3 error-management guidance says unexpected errors must not expose server characteristics, IP, path, or infrastructure properties, while HTTP error semantics must not be masked in a way that prevents proxies/load balancers from understanding application state.

Preserve separate dimensions:

```text
message is customized/application-controlled
technical/infrastructure detail is not exposed
protocol status semantics remain correct when applicable
```

Do not interpret customized as "always return HTTP 200 with a friendly message".

## Default / Raw Error Output

Potential non-compliant evidence includes externally exposed:

```text
framework default error page
raw stack trace
uncaught exception output
server banner/error document
filesystem path
internal IP
database exception text
driver diagnostic
container/platform diagnostic
debug page
```

This is operational evidence, not an exhaustive normative list.

## Internal Logging Boundary

Protected internal logs may retain technical detail.

Vu6 does not require internal logs to be user-friendly.

If internal diagnostic content is forwarded to a consumer, it becomes an exposed error surface.

## Runtime Evidence

Preferred evidence order:

```text
error-handler/middleware configuration
frontend/backend/API error mapping
unit/integration/contract tests
authorized QA runtime error-path validation
```

A centralized error handler does not auto-PASS if uncovered paths still expose raw/default errors.

Unsafe testing:

`ERROR_MESSAGE_TEST_UNSAFE`

## Relationships

```text
Vu5 → validation parity
Vu6 → customized error messages
Vu7 → base-software private-data disclosure
```

They may share evidence but remain independent results.

## Security Reporting

Feed Vu6 evidence/results into the existing Security Reporting subsystem under:

`Validation & Error Handling`

Do not create a parallel report pipeline.

## Completion Criteria

- exact matrix binding preserved
- userFacingErrorPresent evidence-backed
- externally observable error surfaces inventoried
- application-controlled behavior distinguished from raw/default errors
- technical/infrastructure leakage detected where evidenced
- HTTP status semantics not masked merely to customize output
- frontend and backend/API surfaces evaluated independently
- internal logs not incorrectly treated as user-facing errors
- no wording/status/schema invented beyond authoritative sources
- safe runtime testing supported
- Vu5 and Vu7 remain independent
- no Agent or Skill created
