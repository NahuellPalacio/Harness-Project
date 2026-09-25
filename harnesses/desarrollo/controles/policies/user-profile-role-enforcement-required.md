---
id: user-profile-role-enforcement-required
type: POLICY
rule: Vu8
---

# Policy: user-profile-role-enforcement-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu8
```

## Requirement

The effective application profile and access granted to a user must be consistent with the roles authoritatively assigned to that user.

## Role Assignment Source

The Harness must resolve the authoritative role-assignment source from evidence.

Unknown source:

`ROLE_ASSIGNMENT_SOURCE_UNRESOLVED`

Do not invent a source from naming conventions or framework assumptions.

## Profile / Permission Mapping

The application may model the result through profiles, permissions, claims, groups, routes, operations, workflow actions, or data scopes.

Do not require a specific RBAC framework.

Unknown mapping:

`ROLE_PROFILE_MAPPING_UNRESOLVED`

## Consistency Outcomes

```text
CONSISTENT
OVER_PRIVILEGED_PROFILE
UNDER_PRIVILEGED_PROFILE
UNRESOLVED
```

`OVER_PRIVILEGED_PROFILE` is non-compliant.

`UNDER_PRIVILEGED_PROFILE` is also a role/profile inconsistency when authoritative mapping establishes the expected access.

## Protected Operation Boundary

Client/UI restrictions alone do not prove authorization for a protected server operation/resource.

If direct server/API access succeeds beyond the assigned role/profile:

`DIRECT_ACCESS_BYPASSES_ROLE`

## Multi-Role Boundary

Do not invent conflict-resolution semantics for multiple roles.

Unknown effective behavior:

`MULTI_ROLE_PROFILE_UNRESOLVED`

## Role-Change Boundary

Do not invent mandatory immediate propagation.

Evaluate role changes according to the application's authoritative session/refresh/authorization semantics.

Unknown semantics:

`ROLE_CHANGE_PROPAGATION_UNRESOLVED`

## Authentication Boundary

Successful authentication does not establish authorization compliance.

C1 evidence may be reused but final results remain independent.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
ROLE_ASSIGNMENT_SOURCE_UNRESOLVED
ROLE_PROFILE_MAPPING_UNRESOLVED
MULTI_ROLE_PROFILE_UNRESOLVED
ROLE_CHANGE_PROPAGATION_UNRESOLVED
OVER_PRIVILEGED_PROFILE
UNDER_PRIVILEGED_PROFILE
DIRECT_ACCESS_BYPASSES_ROLE
ROLE_PROFILE_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
