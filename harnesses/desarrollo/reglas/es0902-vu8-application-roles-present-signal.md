# Signal: applicationRolesPresent

## Purpose

Resolve ES0902 Vu8 applicability from evidence of application roles that govern profile/access behavior.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when evidence establishes that the application defines, receives, assigns, or consumes roles/groups/claims that determine user profile or access.

Examples may include application role tables, backoffice role assignment, role claims consumed by backend, group-to-profile mapping, authorization middleware/annotations, or profile permissions linked to roles.

## FALSE

Use only when authoritative evidence establishes that the governed application has no role-based profile/access behavior.

Do not infer FALSE because there is no class/enum named Role, roles are stored in DB/configuration, roles come through claims/groups, or authorization is implemented indirectly.

## UNRESOLVED

Use when role ownership/source is unclear, application profile model is unknown, secondary/backoffice/API role behavior may exist, or authorization coverage cannot be established.

## Evidence

Preserve references to:

```text
role source
profile/access mapping source
application surface
authorization mechanism
environment/scope
```

Do not persist raw credentials or personal data.
