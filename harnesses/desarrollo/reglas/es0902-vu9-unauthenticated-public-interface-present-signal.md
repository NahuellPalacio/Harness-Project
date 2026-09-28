# Signal: unauthenticatedPublicInterfacePresent

## Purpose

Resolve ES0902 Vu9 applicability from evidence of public functionality accessible without authentication.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when evidence establishes at least one governed application functionality that is both:

```text
publicly reachable
and
usable without authentication
```

through web or API.

## FALSE

Use only when authoritative evidence establishes that no governed public unauthenticated functionality exists.

Do not infer FALSE because:
- most endpoints require authentication
- the application is primarily internal
- the public operation is read-only

## UNRESOLVED

Use when:
- route/interface inventory is incomplete
- public exposure cannot be established
- authentication coverage is unclear
- gateway/origin topology is unknown
- a secondary API/public frontend may exist

## Non-functional/public artifacts

Public static assets alone do not automatically make Vu9 applicable.

A public DNS name alone does not prove unauthenticated functionality.

## Evidence

Preserve:

```text
surfaceId
interfaceType
route/operation ref
public exposure evidence
authentication requirement evidence
environment
topology/path ref
```

Do not persist secrets or sensitive request payloads.
