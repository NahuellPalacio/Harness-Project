# Signal: authenticationPagePresent

## Purpose

Resolve ES0902 Vu1 applicability from the existing authentication-surface inventory.

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu1
```

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when at least one material interactive authentication flow includes an authentication / credential-entry page.

This includes:

```text
application-hosted login page
delegated identity-provider login page
backoffice/admin login page
mobile web-based delegated authentication page
legacy login page still reachable in governed scope
```

## FALSE

Use only when authoritative evidence establishes that the governed scope has no interactive authentication page.

Example may include a strictly non-interactive machine identity flow, but do not infer this without evidence.

## UNRESOLVED

Use when:

```text
authentication exists but page/interactivity cannot be established
authentication-surface inventory is incomplete
provider flow is unresolved
a secondary/legacy login may still exist
```

## Reuse

Derive from the C1 authentication-surface inventory.

Do not create a second independent authentication-page inventory.

## Evidence

Preserve:

```text
surfaceId
scope
provider
interactive/non-interactive evidence
page ownership: APPLICATION | IDENTITY_PROVIDER | UNRESOLVED
source references
```
