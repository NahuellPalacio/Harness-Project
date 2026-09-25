# Check: role-profile-consistency

## Purpose

Deterministically verify that the effective user profile/access in the application is consistent with the roles assigned to that user.

## Inputs

```text
applicationRolesPresent
role-assignment source
role/profile or role/permission mapping
authorization configuration/code
backend access-control evidence
unit/integration/API authorization tests
authorized QA test evidence
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Resolve authoritative role-assignment source

Identify where the governed application obtains the roles that control access.

If unresolved:

`ROLE_ASSIGNMENT_SOURCE_UNRESOLVED`

### 3. Resolve role/profile mapping

For each material role or role set, determine the expected application profile/access from authoritative project evidence.

If unresolved:

`ROLE_PROFILE_MAPPING_UNRESOLVED`

Do not infer access from role names alone.

### 4. Resolve effective access

For each evaluated role/profile pair, determine the access effectively granted by the application.

Relevant dimensions may include:

```text
route/endpoint
operation
UI function
workflow action
administrative action
data scope
```

Only include dimensions evidenced by the project.

### 5. Compare expected vs effective

Per mapping classify:

```text
CONSISTENT
OVER_PRIVILEGED_PROFILE
UNDER_PRIVILEGED_PROFILE
UNRESOLVED
```

`OVER_PRIVILEGED_PROFILE`:
- observed access exceeds authoritative role/profile mapping

`UNDER_PRIVILEGED_PROFILE`:
- observed access is less than authoritative role/profile mapping

Any confirmed mismatch causes FAIL.

### 6. Protected server operations

Where the profile governs a protected server/API operation, verify that direct access cannot bypass the role/profile restriction.

Example:

```text
UI hides admin action
API accepts same action for non-admin role
→ DIRECT_ACCESS_BYPASSES_ROLE
→ FAIL
```

Do not fail a purely local presentation difference when no protected resource/operation is involved.

### 7. Multi-role users

If a user can hold multiple roles, resolve the expected effective profile from authoritative project semantics.

Do not assume additive, restrictive, first-role, or highest-role behavior.

Unknown:

`MULTI_ROLE_PROFILE_UNRESOLVED`

### 8. Role changes

If role assignment can change during a session, evaluate the resulting profile according to documented refresh/session semantics.

Do not invent an immediate-propagation requirement.

Unknown semantics/evidence:

`ROLE_CHANGE_PROPAGATION_UNRESOLVED`

### 9. Authentication separation

Do not satisfy Vu8 merely because authentication succeeded or because a role claim is present.

The Check must verify that the assigned role actually controls the effective profile/access.

### 10. Runtime verification

Preferred evidence order:

```text
static role/profile mapping
backend authorization rules
unit/integration tests
API contract/authorization tests
authorized QA role tests
```

Use dedicated/synthetic test identities.

Unsafe runtime conditions:

`ROLE_PROFILE_TEST_UNSAFE`

Do not use real privileged identities merely to prove role enforcement.

### 11. Evidence hygiene

Do not persist passwords, tokens, cookies, or real personal data.

Use test identity references and redacted evidence.

### 12. Aggregate

PASS requires all material evaluated role/profile mappings to be consistent and all required protected-operation checks to be resolved.

Any confirmed:

```text
OVER_PRIVILEGED_PROFILE
UNDER_PRIVILEGED_PROFILE
DIRECT_ACCESS_BYPASSES_ROLE
```

causes FAIL.

Any material unresolved mapping/source/semantics prevents PASS.

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
ROLE_ASSIGNMENT_SOURCE_UNRESOLVED
ROLE_PROFILE_MAPPING_UNRESOLVED
MULTI_ROLE_PROFILE_UNRESOLVED
ROLE_CHANGE_PROPAGATION_UNRESOLVED
OVER_PRIVILEGED_PROFILE
UNDER_PRIVILEGED_PROFILE
DIRECT_ACCESS_BYPASSES_ROLE
ROLE_PROFILE_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply:

```text
C1 PASS
Vu5 PASS
complete authentication security
least-privilege beyond the authoritative role model
official security approval
```
