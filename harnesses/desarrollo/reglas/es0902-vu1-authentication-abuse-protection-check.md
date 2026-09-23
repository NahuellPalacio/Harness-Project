# Check: authentication-abuse-protection

## Purpose

Deterministically verify evidence that every applicable authentication page has active CAPTCHA or failed-attempt user blocking.

## Inputs

```text
authenticationPagePresent
C1 authentication-surface inventory
provider/page ownership evidence
authentication abuse-protection evidence
authorized runtime test evidence when used
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Page inventory

Resolve all material interactive authentication pages from existing C1 surfaces.

Incomplete page coverage:

`AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED`

### 3. Page ownership

For each page classify:

```text
APPLICATION
IDENTITY_PROVIDER
UNRESOLVED
```

Ownership determines where evidence should be sourced.

Unknown ownership does not PASS.

### 4. CAPTCHA evidence

If CAPTCHA is claimed, verify active provider/application evidence.

Do not require permanent DOM presence when authoritative evidence establishes conditional CAPTCHA activation.

Capability-only evidence is insufficient.

### 5. Lockout evidence

If user blocking is claimed, verify an active mechanism that blocks the user/account after failed login/session attempts.

Do not invent attempt count or duration.

Capability-only evidence is insufficient.

### 6. OR semantics

A page passes the mechanism dimension when:

```text
CAPTCHA active
OR
lockout active
```

Both active also passes.

A generic anti-abuse control that is not one of the source mechanisms must not satisfy the Check without authoritative equivalence evidence.

### 7. Runtime validation safety

Do not automatically generate repeated failed attempts against real users or production.

Runtime testing requires authorized environment + dedicated test identity + known side effects.

Unsafe runtime test conditions:

`AUTH_ABUSE_RUNTIME_TEST_UNSAFE`

### 8. Aggregate

All applicable pages must pass.

One unresolved/failed page prevents overall PASS.

## Per-Page Results

```text
CAPTCHA_ACTIVE
LOCKOUT_ACTIVE
BOTH_ACTIVE
NO_ALLOWED_MECHANISM_ACTIVE
PROTECTION_UNRESOLVED
```

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED
AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED
AUTHENTICATION_ABUSE_PROTECTION_INACTIVE
AUTH_ABUSE_RUNTIME_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply:

```text
C1 PASS
secure authorization
MFA enabled
Vu9 PASS
security assessment approved
```
