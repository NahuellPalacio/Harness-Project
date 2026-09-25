# ES0902 Vu8 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu8:

```text
Vu8 — Los perfiles de usuarios armados en las aplicaciones deben respetar los roles asignados.
```

Vu8 is a role/profile consistency and authorization-enforcement control.

The normative direction is:

```text
ASSIGNED ROLES
→ EFFECTIVE APPLICATION PROFILE / ACCESS
```

The Harness must verify that the profile and access effectively granted by the application are consistent with the roles assigned to the user.

## Matrix Binding

Use exactly the installed ES0902 matrix binding:

```yaml
ruleKey: ES0902.Vu8
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - applicationRolesPresent

primaryAgents:
  - dev-security
  - dev-backend

policies:
  - user-profile-role-enforcement-required

checks:
  - role-profile-consistency

reviews: []
```

Do not rename these identifiers.

## Applicability

`applicationRolesPresent` is evidence-backed.

```text
TRUE
→ the governed application defines or consumes assigned roles that affect user profiles or access

FALSE
→ authoritative evidence establishes that the governed application has no role-based profile/access model

UNRESOLVED
→ the role/profile model cannot be established
```

Do not infer FALSE because no enum named `Role` exists, roles come from configuration/database, authorization is implemented by middleware/annotations, or roles are represented as groups/claims/permissions.

## Role / Profile Boundary

Do not assume one specific RBAC implementation.

A project may represent authorization through:

```text
roles
groups
claims
permission sets
application profiles
role-to-permission mappings
```

Vu8 requires consistency with the assigned roles, not a specific framework or storage model.

## Authoritative Role Assignment

Determine where the application gets the role assignment that governs access.

Possible evidence may include:

```text
application database
backoffice assignment
identity/group claims
configuration
authoritative integration
```

Do not invent which source is authoritative.

If the authoritative source cannot be established:

`ROLE_ASSIGNMENT_SOURCE_UNRESOLVED`

## Profile Semantics

Determine what the application profile means operationally.

The profile may affect routes/endpoints, operations, UI functions, data scope, workflow actions, or administrative functions.

If the profile-to-access semantics cannot be established:

`ROLE_PROFILE_MAPPING_UNRESOLVED`

## Consistency

Vu8 requires the effective application profile/access to remain consistent with the assigned role set.

Operational result classes:

```text
CONSISTENT
OVER_PRIVILEGED_PROFILE
UNDER_PRIVILEGED_PROFILE
UNRESOLVED
```

`OVER_PRIVILEGED_PROFILE` means the effective profile grants an operation/data scope not supported by the assigned-role evidence.

`UNDER_PRIVILEGED_PROFILE` means the effective profile denies an operation/data scope that authoritative role/profile mapping says the assigned role should receive.

Both are mapping inconsistencies. Security severity may differ, but Vu8 compliance remains independent from severity.

## UI Is Not Sufficient Enforcement

A hidden/disabled UI element is useful evidence but cannot by itself prove role enforcement.

When a role governs a server-side operation or protected resource, the server-side authorization boundary must also be consistent with the role/profile mapping.

Example:

```text
button hidden for role X
but direct API request succeeds
→ DIRECT_ACCESS_BYPASSES_ROLE
→ FAIL
```

Do not require server-side enforcement for a purely local presentation option that has no protected operation/resource behind it.

## Multi-Role Users

Evaluate the effective profile for the actual assigned role set.

Do not assume highest role wins, first role wins, permissions are always additive, or permissions are always restrictive unless authoritative project evidence defines that behavior.

If multiple-role resolution semantics are missing:

`MULTI_ROLE_PROFILE_UNRESOLVED`

## Role Changes

A role assignment may change during a session.

Vu8 does not define a mandatory propagation time.

Do not invent immediate revocation/refresh semantics.

Use the application's authoritative refresh/session/authorization model.

If consistency after a role change cannot be established because refresh semantics are unknown:

`ROLE_CHANGE_PROPAGATION_UNRESOLVED`

## Authentication vs Authorization

Keep separate:

```text
authentication
→ who is the user?

role/profile authorization
→ what may this authenticated user do?
```

A successful OpenID/Keycloak login does not prove Vu8.

## Data Scope

If assigned roles constrain which records/data subsets a profile may access, include that scope in verification.

Do not invent data-scope rules not evidenced by the project.

## Runtime Verification

Preferred evidence order:

```text
role/profile mapping configuration or code
backend authorization rules
unit/integration authorization tests
API/contract tests
authorized QA tests with dedicated test identities
```

Use synthetic or approved test identities.

Do not use real privileged citizen/staff accounts merely to prove Vu8.

Unsafe testing:

`ROLE_PROFILE_TEST_UNSAFE`

## Evidence Hygiene

Do not persist passwords, tokens, cookies, real personal data, or raw identity-provider credentials.

Use test identity references, role IDs/names, profile refs, permission/operation refs, and redacted evidence references.

## Relationships

```text
C1 PASS != Vu8 PASS
Vu5 PASS != Vu8 PASS
```

C1 governs authentication/OpenID/Keycloak requirements. Vu5 governs validation parity. Vu8 governs application role/profile consistency.

## Security Reporting

Feed Vu8 results/findings/evidence references into the existing Security Reporting subsystem under:

`Identity & Authorization`

Do not create a separate Vu8 reporting pipeline.

## Completion Criteria

- exact matrix binding is preserved
- applicationRolesPresent is evidence-backed
- authoritative role assignment source is resolved
- role/profile mapping is evidence-backed
- effective access is compared against assigned roles
- over-privilege and under-privilege are distinguishable
- UI hiding alone cannot prove protected-operation authorization
- multi-role semantics are not invented
- role-change propagation timing is not invented
- C1 and Vu5 remain independent
- runtime tests are safe
- no Agent or Skill is created
