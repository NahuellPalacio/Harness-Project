---
id: dgsei-keycloak-provider-required
type: POLICY
rule: C1
---

# Policy: dgsei-keycloak-provider-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "3"
rule: C1
```

## Requirement

For C1-governed OpenID authentication in GCABA environments, the identity provider must be the authorized Keycloak service managed by DGSEI.

Each applicable application/client must be registered in the corresponding identity server.

## Provider Verification

Do not accept provider authority merely because:
- hostname contains `keycloak`
- a Keycloak dependency exists
- README says Keycloak
- an issuer URL looks internal

Require authoritative provider/environment evidence.

Unknown authority:
`KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED`

## Registration

A `client_id` alone is not proof of registration.

Unknown registration:
`OIDC_CLIENT_REGISTRATION_UNRESOLVED`

## Legacy Provider

Active use of the previous OpenID service:

`https://oauth2-server.apps.buenosaires.gob.ar/`

for a new-version authentication path must not PASS.

Use:

```text
LEGACY_OPENID_PROVIDER_DETECTED
OIDC_MIGRATION_REQUIRED
```

Historical/inactive references are not automatic failures.

## Environment Boundary

Do not force a production identity URL into lower environments.

Validate the authorized environment-specific provider using authoritative project/identity evidence.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED
OIDC_CLIENT_REGISTRATION_UNRESOLVED
LEGACY_OPENID_PROVIDER_DETECTED
OIDC_MIGRATION_REQUIRED
ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED
EVIDENCE_INCOMPLETE
```
