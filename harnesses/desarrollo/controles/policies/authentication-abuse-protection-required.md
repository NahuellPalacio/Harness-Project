---
id: authentication-abuse-protection-required
type: POLICY
rule: Vu1
---

# Policy: authentication-abuse-protection-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu1
```

## Requirement

Every applicable authentication page must have at least one active source-allowed protection:

```text
CAPTCHA
OR
user/account blocking after failed login/session attempts
```

Both are allowed.

## No Silent Substitution

Do not treat the following as automatically equivalent to Vu1:

```text
WAF
IP rate limiting
generic API throttling
gateway quotas
device fingerprinting
bot scoring
MFA
password complexity
```

These may be useful security controls, but Vu1 specifically names CAPTCHA or user blocking after failed attempts.

A different mechanism requires separate authoritative equivalence evidence.

## Active Protection

A platform/provider capability is insufficient unless active/effective behavior is evidenced for the governed authentication page.

## Thresholds

Do not invent:

```text
attempt count
lockout duration
captcha trigger threshold
reset interval
```

Use authoritative provider/project/security configuration.

## Delegation

When the authentication page is provider-owned, protection should be evidenced at provider level.

Do not reimplement provider security locally solely for Vu1.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED
AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED
AUTHENTICATION_ABUSE_PROTECTION_INACTIVE
AUTH_ABUSE_RUNTIME_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
