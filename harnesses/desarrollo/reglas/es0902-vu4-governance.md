# ES0902 Vu4 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu4:

```text
Vu4 — Toda sesión en stand by, tiene que tener un tiempo límite para su utilización.
Esto, independientemente del límite de tiempo que posee el token de autenticación del OpenID.
```

Vu4 is an application-session inactivity/standby timeout rule.

Its central requirement is that an application session that remains inactive/standby must have its own bounded usage lifetime, independently from the authentication-token timeout managed by OpenID/OIDC.

## Matrix Binding

```yaml
ruleKey: ES0902.Vu4
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - sessionPresent

primaryAgents:
  - dev-security

policies:
  - session-inactivity-timeout-required

checks:
  - session-inactivity-timeout

reviews: []
```

Do not rename these identifiers.

## Applicability

`sessionPresent` is evidence-backed.

```text
TRUE
→ at least one material authenticated application session exists in governed scope

FALSE
→ authoritative evidence establishes that no application session exists in governed scope

UNRESOLVED
→ authentication/session behavior exists or may exist, but session semantics cannot be established
```

Do not infer FALSE because the application uses tokens.

A token-based frontend/mobile application can still maintain an application session.

## Session Inventory

Evaluate each material application-session surface independently.

Examples may include:

```text
browser citizen session
backoffice/admin session
mobile application session
legacy authenticated session
secondary client/session
```

Reuse C1/Vu3 evidence where it applies.

Incomplete coverage:

`SESSION_COVERAGE_UNRESOLVED`

## Standby / Inactivity Semantics

Vu4 requires a bounded period after which an inactive/standby session can no longer continue as the same active application session.

The standard does not define:

```text
timeout duration
exact user activity that resets it
warning-dialog timing
grace period
role-specific timeout
absolute session lifetime
```

Do not invent those values.

## Independence from OpenID/OIDC Token Timeout

This is the core semantic of Vu4.

The application inactivity timeout must not be treated as satisfied merely because:

```text
access token expires
refresh token expires
OIDC session expires
Keycloak SSO expires
```

Preserve separately:

```text
applicationInactivityTimeout
oidcTokenTimeout
```

An evidenced token timeout without an application inactivity timeout does not satisfy Vu4.

## Application Session vs IdP Session

Keep separate:

```text
APPLICATION SESSION
APPLICATION INACTIVITY TIMER
OIDC ACCESS TOKEN LIFETIME
OIDC REFRESH TOKEN LIFETIME
IDENTITY PROVIDER SSO SESSION
```

Vu4 directly governs the application's inactive-session behavior.

## Timeout Enforcement

The standard does not mandate which layer enforces the timeout.

Potential evidence may come from:

```text
server-side session middleware
application backend
frontend session controller
mobile session controller
gateway/session component
```

A client-only visual timer is insufficient if the same inactive session can still access protected resources after the supposed timeout.

## Observable Security Invariant

After the configured application inactivity interval elapses without qualifying activity:

```text
the previous inactive application session must not continue to authorize normal protected application use as the same active session
```

Possible compliant outcomes may include:

```text
session terminated
reauthentication required
new application session required
protected operation rejected until session is re-established
```

Do not prescribe a specific UX flow from Vu4 alone.

## Activity Reset Boundary

Do not invent that:

```text
mouse movement
scroll
background polling
API refresh
token refresh
tab focus
```

must count as user activity.

If activity semantics are required but unavailable:

`SESSION_ACTIVITY_SEMANTICS_UNRESOLVED`

Token refresh must not silently reset the application inactivity timeout unless authoritative policy explicitly defines that behavior.

## Multi-Session / Multi-Role Coverage

If different sessions or roles use different timeout policies, evaluate each separately.

Incomplete mapping:

`SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED`

## Relationships

```text
Vu3 → session termination after application/browser close
Vu4 → session expiration after inactivity while open/standby
C1  → authentication protocol/provider/delegation
```

These remain independent.

## Safe Runtime Validation

Preferred order:

```text
session architecture/configuration evidence
unit/integration/session-control tests
authorized QA runtime timeout test with dedicated test identity
```

Do not lower production security settings merely to make testing faster.

Do not use real-user sessions.

Do not log raw cookies/tokens/session identifiers.

Unsafe validation:

`SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE`

## Completion Criteria

- exact matrix binding preserved
- sessionPresent evidence-backed
- all material session surfaces covered
- inactivity timeout separated from OIDC token timeout
- no duration invented
- activity-reset semantics not invented
- token refresh not assumed to equal user activity
- effective post-timeout behavior evidenced
- client-only UI timeout cannot hide active backend session
- Vu3 and C1 remain independent
- runtime validation safe and secret-free
- no Agent or Skill created
