# ES0902 Vu3 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu3:

```text
Vu3 — Toda aplicación que se cierra a través de las ventanas o en forma directa del browser,
no debe dejar la sesión activa.
```

Vu3 is an application-session termination rule for browser/window close behavior.

It must not be reduced to "a logout button exists", and it must not be expanded into a requirement to terminate the user's global Identity Provider SSO session unless another authoritative source explicitly requires that.

## Matrix Binding

```yaml
ruleKey: ES0902.Vu3
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - browserSessionPresent

primaryAgents:
  - dev-security

policies:
  - browser-close-session-termination-required

checks:
  - browser-close-session-termination

reviews: []
```

Do not rename these identifiers.

## Applicability

`browserSessionPresent` is evidence-backed.

```text
TRUE
→ the governed application has a browser-based authenticated application session

FALSE
→ authoritative evidence establishes no browser-based application session exists in scope

UNRESOLVED
→ browser authentication/session behavior or supported client scope cannot be established
```

Do not infer FALSE because authentication is delegated to Keycloak/OIDC.

## Session Domains

Keep separate:

```text
APPLICATION SESSION
IDENTITY PROVIDER SESSION
ACCESS/REFRESH TOKEN LIFETIME
BROWSER STORAGE/CREDENTIAL ARTIFACTS
```

Vu3 directly governs the application session left after the application/browser is closed.

A provider SSO session may remain active unless another authoritative requirement says otherwise.

## Observable Security Invariant

After an applicable close event, the previously established application session must no longer remain usable as the same active session.

A later OIDC/Keycloak SSO exchange may create a new application session. That is not automatically the same as the previous session remaining active.

## Close Events

Source-relevant events:

```text
APPLICATION_WINDOW_CLOSE
BROWSER_CLOSE
```

A tab-close scenario may be tested only when the project/browser interaction makes it an applicable equivalent close event.

Do not silently turn Vu3 into a universal "every tab close must globally log out" rule.

## Storage Is Evidence, Not Verdict

Session cookies, persistent cookies, localStorage, sessionStorage, tokens, and server-side sessions are implementation evidence.

Do not prescribe one storage mechanism from Vu3 alone.

The verdict is whether the old application session remains active/usable after the governed close event.

## Explicit Logout Is Not Enough

```text
logout button works
!=
browser close terminates application session
```

Vu3 must be evaluated when the user closes the application/browser without explicitly selecting logout.

## Browser/Client Scope

Evaluate supported browser/client contexts evidenced by the project.

Unknown scope:

`SUPPORTED_BROWSER_SCOPE_UNRESOLVED`

Do not invent a universal browser matrix.

## Server-Side / Token Session Evidence

Where technically applicable, verify that the old session artifact is rejected after close.

A login screen alone is insufficient if protected endpoints still accept the old application-session artifact.

Do not invent token revocation requirements solely from Vu3.

## OIDC Reuse

Reuse `dev-openid-connect` logout/session evidence where relevant.

OIDC logout evidence is supporting context only; it does not auto-pass Vu3.

## Reliability Boundary

Presence of browser lifecycle code such as:

```text
beforeunload
unload
pagehide
sendBeacon
```

is not sufficient by itself.

PASS requires behavioral/session-state evidence.

## Safe Runtime Validation

Preferred order:

```text
architecture/configuration evidence
storage/session evidence
authorized QA runtime test with dedicated identity
```

Do not use real-user accounts or persist session secrets.

Unsafe validation:

`BROWSER_SESSION_TERMINATION_TEST_UNSAFE`

## Relationship with Vu4

```text
Vu3 → termination after close
Vu4 → inactivity timeout while open/standby
```

A short inactivity timeout does not substitute for Vu3.

## Completion Criteria

- exact matrix binding preserved
- application session separated from IdP SSO/token lifetime
- explicit logout not confused with close behavior
- old-session reuse verified
- browser lifecycle hooks not trusted without behavioral evidence
- supported client scope evidence-backed
- safe runtime testing
- independent from C1 and Vu4
- no Agent or Skill created
