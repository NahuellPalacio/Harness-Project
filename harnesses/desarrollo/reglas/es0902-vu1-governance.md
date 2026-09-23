# ES0902 Vu1 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu1:

```text
Vu1 — Toda página de autenticación debe contener captcha o bloqueo de usuarios
por intentos de sesión, funcionalidad que se encuentra contenida en OpenID.
```

Vu1 is an authentication-abuse-protection rule.

It does not require both mechanisms simultaneously. The normative condition is satisfied when at least one of the two source mechanisms is effectively active for each applicable authentication page:

```text
CAPTCHA
OR
user blocking after failed login/session attempts
```

Do not broaden the rule silently into generic rate limiting, WAF rules, IP throttling, or another anti-abuse mechanism unless a separate authoritative GCABA/ASI source establishes equivalence.

## Matrix Binding

The installed ES0902 matrix declares:

```yaml
ruleKey: ES0902.Vu1
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - authenticationPagePresent

primaryAgents:
  - dev-security

policies:
  - authentication-abuse-protection-required

checks:
  - authentication-abuse-protection

reviews: []
```

Do not rename these identifiers.

## Applicability

`authenticationPagePresent` is evidence-backed and should be derived from the authentication-surface inventory created for C1.

Recommended resolution:

```text
TRUE
→ at least one material interactive authentication surface includes a credential-entry/authentication page,
   whether application-hosted or delegated to an identity provider

FALSE
→ authoritative evidence establishes that the governed scope has no interactive authentication page

UNRESOLVED
→ authentication surfaces exist or may exist, but page/interactivity cannot be established
```

Do not use FALSE simply because the application redirects to Keycloak. A delegated identity-provider login page is still part of the authentication flow.

Do not use TRUE for a purely non-interactive machine-to-machine flow unless an actual authentication page exists.

## Surface-Level Evaluation

Vu1 must evaluate every applicable authentication page independently.

Example:

```text
citizen login page
admin/backoffice login page
legacy login page
secondary client login page
```

One protected page does not make another page compliant.

If page coverage cannot be established:

`AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED`

## Effective Protection, Not Capability Presence

Do not PASS because the identity provider or framework merely supports CAPTCHA or lockout.

Require evidence that at least one allowed mechanism is active/effective for the page.

Insufficient examples:

```text
"Keycloak supports brute-force protection"
"the provider can show CAPTCHA"
"a security library is installed"
```

without active configuration/provider evidence.

## Allowed Source Mechanisms

### CAPTCHA

Evidence must show CAPTCHA protection is actually active for the authentication page or becomes active under the applicable authentication-failure behavior.

Do not require CAPTCHA to be permanently visible if authoritative behavior/configuration establishes conditional activation.

### User blocking after failed attempts

Evidence must show a user/account blocking mechanism exists and is active after failed login/session attempts.

The standard does not define:

```text
number of attempts
blocking duration
progressive delay
reset interval
```

Do not invent these values.

If the values are required for implementation, obtain them from authoritative identity/security configuration or project evidence.

## C1 / Identity Provider Reuse

Reuse the C1 authentication-surface inventory and provider evidence.

If C1 establishes delegated authentication to an authorized identity provider, Vu1 should inspect or consume provider-level protection evidence rather than require the application to reimplement CAPTCHA/lockout locally.

Do not duplicate identity-provider functionality in application code solely to satisfy Vu1.

## OpenID Wording Boundary

The ES0902 source states that this functionality is contained in OpenID.

The Harness must preserve the source requirement but should validate effective provider behavior/configuration rather than invent protocol-level semantics.

No assumption that "OIDC configured" automatically means Vu1 PASS.

## Safe Validation Doctrine

Testing failed-login protection can lock accounts or disrupt users.

Therefore default validation is:

```text
configuration/provider evidence first
authorized runtime validation second
```

Runtime failure-attempt testing may run only when:

```text
environment is explicitly authorized for security testing
a dedicated test identity exists
the test does not target real-user accounts
the expected lockout/captcha side effect is understood
the action passes the existing Tool Risk Gate when applicable
```

Do not automatically brute-force:

```text
PRD
real accounts
shared privileged accounts
unknown identity environments
```

If runtime testing is needed but safe test conditions are unavailable:

`AUTH_ABUSE_RUNTIME_TEST_UNSAFE`

This does not imply non-compliance; it means evidence remains unresolved.

## Delegated Provider Evidence

Acceptable evidence may include:

```text
authoritative identity-provider configuration
official project/identity ticket
provider security configuration evidence
approved security documentation
authorized QA runtime test using dedicated test identity
official assessment evidence
```

Do not treat screenshots or informal statements alone as sufficient if they cannot establish the active mechanism for the governed surface.

## Mechanism Result

Per authentication page:

```text
CAPTCHA_ACTIVE
LOCKOUT_ACTIVE
BOTH_ACTIVE
NO_ALLOWED_MECHANISM_ACTIVE
PROTECTION_UNRESOLVED
```

Overall Vu1 PASS requires every applicable page to be either:

```text
CAPTCHA_ACTIVE
LOCKOUT_ACTIVE
BOTH_ACTIVE
```

## Relationship with C1

```text
C1
→ authentication protocol/provider/delegation

Vu1
→ protection of authentication pages against repeated login attempts
```

C1 PASS does not imply Vu1 PASS.

Vu1 PASS does not imply C1 PASS.

## Relationship with Security Incident Review

Repository/security-incident evidence may reveal removal or weakening of authentication-abuse protections.

Such evidence may feed Vu1, but Repository Integrity Review remains a separate operational capability.

## Completion Criteria

Vu1 is complete when:

```text
- exact matrix binding is preserved
- authenticationPagePresent is derived from existing authentication surfaces
- every authentication page is evaluated independently
- CAPTCHA OR user-lockout semantics are preserved
- generic anti-abuse controls are not silently substituted
- capability presence is not confused with active protection
- provider-level protection is reused rather than duplicated in app code
- no thresholds/durations are invented
- runtime validation is safety-gated
- C1 PASS cannot auto-pass Vu1
- no Agent or Skill is created
```
