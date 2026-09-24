# Check: browser-close-session-termination

## Purpose

Deterministically validate evidence that closing the governed application/browser does not leave the previous application session active.

## Inputs

```text
browserSessionPresent
authentication-surface inventory
application/session architecture evidence
supported browser/client scope
session storage/cookie/token metadata
OIDC/application logout evidence
authorized close/reopen runtime test evidence
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Session model

Determine:

```text
SERVER_SIDE_SESSION
TOKEN_BASED_APPLICATION_SESSION
HYBRID
OTHER
UNRESOLVED
```

Unknown:

`BROWSER_SESSION_MODEL_UNRESOLVED`

### 3. Supported client scope

Use project evidence to identify applicable supported browser/client contexts.

Unknown:

`SUPPORTED_BROWSER_SCOPE_UNRESOLVED`

Do not invent a browser list.

### 4. Close-event coverage

At minimum evaluate:

```text
APPLICATION_WINDOW_CLOSE
BROWSER_CLOSE
```

Include tab close only when it is an evidenced applicable equivalent for the governed application.

Incomplete coverage:

`BROWSER_CLOSE_BEHAVIOR_UNRESOLVED`

### 5. Old-session reuse

After close/reopen, determine whether the previous application-session artifact can still resume or authorize the same application session.

Possible outcomes:

```text
OLD_SESSION_REJECTED
NEW_SESSION_ESTABLISHED_AFTER_AUTH
OLD_SESSION_STILL_ACTIVE
UNRESOLVED
```

`OLD_SESSION_STILL_ACTIVE`:

```text
OLD_APPLICATION_SESSION_REMAINS_ACTIVE
→ FAIL
```

### 6. Distinguish IdP SSO

If reopen causes:

```text
IdP SSO
→ new authorization/authentication exchange
→ new application session
```

do not classify that as the old application session remaining active solely because credentials were not re-entered.

### 7. UI-only evidence is insufficient

Returning visually to a login page is insufficient if protected endpoints still accept the old application-session artifact.

### 8. Explicit logout evidence

Consume existing OIDC/application logout evidence as supporting context only.

Do not substitute explicit logout success for close-event validation.

### 9. Lifecycle hooks

Presence of:

```text
beforeunload
unload
pagehide
sendBeacon
```

does not produce PASS without behavioral/session evidence.

### 10. Runtime safety

Use QA/authorized environment + dedicated test identity where runtime validation is needed.

Do not log raw cookies, access tokens, refresh tokens, authorization codes, or id_token_hint values.

Unsafe validation:

`BROWSER_SESSION_TERMINATION_TEST_UNSAFE`

### 11. Aggregate

All applicable supported browser/close-event combinations must resolve compliant behavior.

One confirmed old active session -> FAIL.

One unresolved required combination prevents PASS.

## Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
SUPPORTED_BROWSER_SCOPE_UNRESOLVED
BROWSER_SESSION_MODEL_UNRESOLVED
BROWSER_CLOSE_BEHAVIOR_UNRESOLVED
OLD_APPLICATION_SESSION_REMAINS_ACTIVE
BROWSER_SESSION_TERMINATION_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply global IdP SSO termination, Vu4 PASS, C1 PASS, or official security approval.
