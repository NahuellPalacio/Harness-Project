# Signal: sessionPresent

## Purpose

Resolve ES0902 Vu4 applicability for authenticated application sessions.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when evidence establishes at least one material authenticated application session in governed scope.

Examples may include:

```text
server-side session
browser application session
token-based application session
mobile authenticated session
hybrid session model
```

## FALSE

Use only when authoritative architecture/scope evidence establishes that no application session exists.

Do not infer FALSE merely because:

```text
OIDC is used
the backend is stateless
the client stores tokens
there is no server-side session cookie
```

## UNRESOLVED

Use when authentication exists but application-session semantics, secondary/admin/mobile coverage, or session ownership cannot be established.

## Evidence

Preserve references to:

```text
session surface ID
application/session architecture
session model
environment
roles/scope when relevant
authentication surface reference
```

Never persist raw session IDs, cookies, access tokens, refresh tokens, or credentials.
