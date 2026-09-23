# ES0902 C1 Governance Package

## Purpose

Operationalize ES0902 v6.2 §3 C1.

C1 requires application authentication to use OpenID Connect; the authorized and mandatory OpenID identity provider in GCABA environments is Keycloak managed by DGSEI; applications must use appropriate OpenID flows, register in the corresponding server, and respect ASI authentication, authorization and resource-protection policies. New versions must migrate away from the previous OpenID service and delegate credential entry to the new identity portal.

## Matrix Binding

```yaml
ruleKey: ES0902.C1
category: QUALITY
applicability:
  mode: CONDITIONAL
  signals:
    - authenticationPresent
primaryAgents:
  - dev-security
  - dev-integration
policies:
  - openid-connect-authentication-required
  - dgsei-keycloak-provider-required
  - credential-entry-delegation-required
checks:
  - oidc-keycloak-integration
  - authentication-delegation
reviews: []
```

Do not rename these IDs.

## Applicability

Reuse the existing `authenticationPresent` signal from ES0901 D2.

```text
TRUE       -> APPLICABLE
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

Do not create a duplicate signal.

## Authentication Surface Inventory

Evaluate every material authentication surface independently:

```text
frontend login
backoffice login
administrative login
mobile login
legacy login
secondary application/client login
```

Incomplete coverage:

`AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED`

## Mandatory Evidence

For each C1-governed surface establish:

```text
OIDC protocol
authorized DGSEI-managed Keycloak provider
client/application registration in the corresponding server
appropriate OpenID flow
credential-entry delegation
applicable ASI auth/authz/resource-protection policy context
absence of active legacy OpenID for a new-version path
```

## Appropriate Flow

ES0902 does not define one universal flow.

Do not hardcode Authorization Code, PKCE, Client Credentials, Implicit or Hybrid solely from C1.

Unknown flow:
`OIDC_FLOW_CONTEXT_UNRESOLVED`

Unknown authority for the selected flow:
`OIDC_FLOW_AUTHORITY_UNRESOLVED`

## Provider Identity

Do not validate provider authority from hostname shape alone.

Use authoritative identity/project evidence, provider metadata, registration evidence and environment configuration.

Unknown authority:
`KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED`

## Client Registration

A `client_id` string alone is not proof of registration.

Unknown registration:
`OIDC_CLIENT_REGISTRATION_UNRESOLVED`

## Credential Delegation

Reuse existing ES0901 D2 controls:

```text
credential-entry-delegation-required
authentication-delegation
```

Attach `ES0902.C1` as an additional normative source. Do not duplicate implementation.

## Legacy OpenID

Active use of:

`https://oauth2-server.apps.buenosaires.gob.ar/`

for a new-version authentication path must not PASS.

Use:

```text
LEGACY_OPENID_PROVIDER_DETECTED
OIDC_MIGRATION_REQUIRED
```

Historical/inactive references are not automatic failures.

## Environment Boundary

The source names the production identity portal. Do not force that production hostname into DEV/QA/HML if authoritative environment-specific identity evidence defines different endpoints.

## Authorization / Roles Boundary

Authentication identity:
`Keycloak / OIDC`

Application role assignment:
`application responsibility`

Successful Keycloak authentication does not prove correct application authorization.

AD groups may be used where appropriate. The source recommendation about AD-tree/group restriction is not a universal hard-fail criterion unless authoritative project/ASI policy makes it mandatory.

## ASI Policy Context

If the concrete ASI authentication/authorization/resource-protection policy context is unavailable:

`ASI_IDENTITY_POLICY_CONTEXT_REQUIRED`

Do not invent claims, role mappings, token lifetime, scopes, algorithms or resource-protection semantics.

## Cross-Standard Identity Resolution

ES0901 v6.3 §8.2 distinguishes citizen authentication from institutional/non-citizen authentication and explicitly describes the Keycloak/OIDC path for the institutional case.

ES0902 C1 is broader in wording.

Therefore resolve by authentication surface, not whole application.

Institutional/non-citizen surface:
- evaluate Keycloak/OIDC directly when evidence supports the classification.

Citizen-facing surface:
- do not silently replace the citizen identity path with Keycloak.
- preserve ES0901 D1.
- if the same surface appears governed by both standards without authoritative reconciliation, return:
  `CROSS_STANDARD_INTERPRETATION_REQUIRED`

Project-specific evidence may resolve only that project's scope and must not become global doctrine.

## Mixed Applications

A single system may contain:

```text
citizen frontend
+
administrative backoffice
```

Evaluate each independently.

## Skill Boundary

`dev-openid-connect` may implement/inspect C1 after identity context is resolved.

It is not normative authority and must not invent provider contracts, client models, claims, redirects or flows.

## Completion Criteria

C1 is complete only when:
- exact matrix binding is preserved
- `authenticationPresent` is reused
- D2 delegation controls are reused with multi-source trace
- all authentication surfaces are inventoried
- OIDC, Keycloak authority, registration and flow are evidenced
- credential entry is delegated
- active legacy provider use is detected
- authorization is not confused with authentication
- missing ASI policy context stays unresolved
- citizen/institutional surfaces are not silently conflated
- no Agent or Skill is created
