---
id: browser-close-session-termination-required
type: POLICY
rule: Vu3
---

# Policy: browser-close-session-termination-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu3
```

## Requirement

When a governed browser-based application is closed through an applicable window/browser close event, the previously established application session must not remain active/usable as the same session.

## Application vs IdP Session

Vu3 does not automatically require termination of global Identity Provider SSO.

A later provider SSO flow may establish a new application session. The old application session itself must not remain active/usable.

## Explicit Logout Boundary

A logout button or provider logout endpoint does not satisfy Vu3 by itself.

## Implementation Neutrality

Do not mandate from Vu3 alone:

```text
specific cookie flags
sessionStorage
localStorage prohibition
token revocation endpoint
server-side session framework
beforeunload
sendBeacon
```

These may be evidence, but the Policy is outcome-based.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
SUPPORTED_BROWSER_SCOPE_UNRESOLVED
BROWSER_SESSION_MODEL_UNRESOLVED
BROWSER_CLOSE_BEHAVIOR_UNRESOLVED
OLD_APPLICATION_SESSION_REMAINS_ACTIVE
BROWSER_SESSION_TERMINATION_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
