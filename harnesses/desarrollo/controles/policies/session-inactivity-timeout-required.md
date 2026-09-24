---
id: session-inactivity-timeout-required
type: POLICY
rule: Vu4
---

# Policy: session-inactivity-timeout-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu4
```

## Requirement

Every applicable application session that may remain inactive/standby must have a bounded inactivity period after which the same inactive application session can no longer continue normal protected use.

This limit is independent from the OpenID/OIDC authentication-token timeout.

## Independence Rule

The following alone do not satisfy Vu4:

```text
access-token expiration
refresh-token expiration
OIDC provider session expiration
Keycloak SSO expiration
```

An application inactivity timeout must be evidenced separately.

## No Invented Duration

Vu4 does not define the duration.

Do not invent values such as 5, 10, 15, or 30 minutes.

Use authoritative project/security/session configuration.

## Enforcement Boundary

A UI-only timeout is insufficient if protected application resources still accept the same inactive session after the configured limit.

## Activity Boundary

Do not invent which events reset the timer.

Background token refresh, polling, mouse movement, focus, or network activity count only when authoritative session policy says they count.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
SESSION_COVERAGE_UNRESOLVED
SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED
SESSION_ACTIVITY_SEMANTICS_UNRESOLVED
SESSION_INACTIVITY_TIMEOUT_UNRESOLVED
TOKEN_TIMEOUT_ONLY
INACTIVE_SESSION_REMAINS_USABLE
SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
