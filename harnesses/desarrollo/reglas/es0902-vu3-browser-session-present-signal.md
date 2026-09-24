# Signal: browserSessionPresent

## Purpose

Resolve ES0902 Vu3 applicability for browser-based authenticated application sessions.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when evidence establishes that an authenticated application session exists in a browser-based application flow.

Examples may include:

```text
session cookie
server-side application session
application token/session state stored or managed by the browser
authenticated browser context after OIDC/Keycloak login
```

## FALSE

Use only when authoritative scope evidence establishes no browser-based authenticated application session exists.

Do not infer FALSE merely because authentication is delegated to an IdP or because tokens are used instead of server sessions.

## UNRESOLVED

Use when authentication exists but browser/application session semantics, supported client scope, or session ownership cannot be established.

## Evidence

Preserve references to:

```text
authentication surface
application/session architecture
browser/client scope
session artifact type without secret value
provider/application ownership
environment
```

Never persist raw session IDs, tokens, cookies, or secrets.
