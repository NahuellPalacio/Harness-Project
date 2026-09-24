# Check: session-inactivity-timeout

## Purpose

Deterministically validate that every applicable application session has an effective inactivity/standby timeout that is independent from the OIDC/OpenID token timeout.

## Inputs

```text
sessionPresent
session/authentication surface inventory
application session architecture
session timeout configuration
OIDC token/session timeout metadata where available
activity-reset policy
authorized runtime/unit/integration test evidence
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Session coverage

Resolve all material application-session surfaces.

Incomplete:

`SESSION_COVERAGE_UNRESOLVED`

### 3. Session model

Classify each session surface as needed:

```text
SERVER_SIDE_SESSION
TOKEN_BASED_APPLICATION_SESSION
HYBRID
OTHER
UNRESOLVED
```

Unknown semantics prevent PASS for that surface.

### 4. Inactivity-timeout evidence

For each applicable session, identify the application inactivity timeout configuration/behavior.

Possible state:

```text
CONFIGURED
NOT_CONFIGURED
UNRESOLVED
```

Do not infer the value from token lifetime.

### 5. OIDC independence

Preserve, where known:

```text
application inactivity timeout
OIDC access-token timeout
OIDC refresh-token timeout
IdP SSO timeout
```

Verify that the application inactivity timeout is independently defined/effective.

If the only timeout is an OpenID/OIDC token timeout:

```text
TOKEN_TIMEOUT_ONLY
→ FAIL
```

### 6. Duration

Verify that a bounded application inactivity timeout exists.

Do not judge whether the exact duration is acceptable unless another authoritative policy defines an acceptable duration.

### 7. Activity-reset semantics

When implementation requires a definition of activity, use authoritative project/session evidence.

Unknown required semantics:

`SESSION_ACTIVITY_SEMANTICS_UNRESOLVED`

Do not automatically count background token refresh or polling as user activity.

### 8. Post-timeout behavior

After the application inactivity interval expires, verify that the previous inactive session cannot continue normal protected use as the same active session.

Possible outcomes:

```text
SESSION_REJECTED
REAUTHENTICATION_REQUIRED
NEW_SESSION_REQUIRED
OLD_INACTIVE_SESSION_STILL_USABLE
UNRESOLVED
```

`OLD_INACTIVE_SESSION_STILL_USABLE`:

```text
INACTIVE_SESSION_REMAINS_USABLE
→ FAIL
```

### 9. UI-only timeout

A modal, login redirect, or local UI state is insufficient if protected resources still accept the same inactive application session.

Where technically applicable, verify enforcement at the application/resource boundary.

### 10. Multiple policies

If sessions or roles have different policies, evaluate each.

Incomplete mapping:

`SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED`

### 11. Runtime safety

Use authorized QA/test environment + dedicated test identity where runtime timeout validation is needed.

Do not:
- use real-user sessions
- log raw tokens/cookies/session IDs
- weaken PRD timeout settings merely to accelerate a test

Unsafe validation:

`SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE`

### 12. Aggregate

All applicable session surfaces must demonstrate an effective application inactivity timeout independent from OIDC token timeout.

One `TOKEN_TIMEOUT_ONLY` or `OLD_INACTIVE_SESSION_STILL_USABLE` result causes FAIL.

One unresolved applicable session prevents PASS.

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
SESSION_COVERAGE_UNRESOLVED
SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED
SESSION_ACTIVITY_SEMANTICS_UNRESOLVED
SESSION_INACTIVITY_TIMEOUT_UNRESOLVED
TOKEN_TIMEOUT_ONLY
INACTIVE_SESSION_REMAINS_USABLE
SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply Vu3 PASS, C1 PASS, global IdP SSO timeout compliance, absolute-session-lifetime compliance, or official security approval.
