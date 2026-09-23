# ES0902 C1 — Cross-Standard Identity Resolution

## Objective

Prevent unsafe reconciliation between ES0902 C1 and ES0901 identity requirements.

## Source Relationship

ES0902 C1 requires:
- OIDC-based authentication
- authorized Keycloak provider managed by DGSEI
- appropriate OpenID flows
- client registration
- compliance with ASI auth/authz/resource-protection policies
- migration from previous OpenID
- delegated credential entry

ES0901 v6.3 §8.2 distinguishes:
- citizen authentication context
- institutional/non-citizen authentication using GCABA AD/OpenID
- institutional Keycloak/OIDC integration

## Resolution Model

Resolve per authentication surface:

```text
surface
├── audience
├── environment
├── current provider
├── intended provider
├── normative sources
└── project identity evidence
```

Operational audience classification:

```text
CITIZEN
INSTITUTIONAL
MIXED
UNRESOLVED
```

This is not a new normative signal.

## Institutional Surface

When authoritative evidence establishes institutional/non-citizen scope, ES0901 §8.2 and ES0902 C1 align on the Keycloak/OIDC path.

## Citizen Surface

Do not globally declare C1 inapplicable.

Do not globally replace the citizen identity path with Keycloak.

If both standards appear to govern the same citizen-facing surface and authoritative reconciliation is absent:

`CROSS_STANDARD_INTERPRETATION_REQUIRED`

## Project-Specific Evidence

A checkpoint, identity ticket, contract, architecture decision or official identity guidance may resolve only the evidenced project/surface.

Never promote a project-specific resolution into global Harness doctrine.

## Mixed Applications

A mixed application may have separate authentication paths, e.g.:

```text
citizen frontend
administrative backoffice
```

Evaluate each independently.

## Control Reuse

Reuse:
- `credential-entry-delegation-required`
- `authentication-delegation`

with multiple normative sources.

Do not duplicate execution.
