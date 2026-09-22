---
name: dev-openid-connect
description: Use when planning or implementing an OpenID Connect integration in a GCBA application — client and realm decisions, redirect and post-logout URIs, identifier normalization, state handling, logout flow and per-environment configuration — without breaking the authentication path that already works. Encodes the real sequence, the decision points and the failure patterns of an integration already executed, and resolves the identity prerequisites before any authentication code is touched. Owned by dev-integration; points at dev-identidad for the norm and dev-tramites-asi for the ticket instead of restating them.
---

# Skill: dev-openid-connect

## Purpose

Plan and implement OpenID Connect integrations in GCBA applications while preserving the existing authentication path, resolving identity prerequisites before coding, maintaining environment-specific configuration, and preventing regressions discovered in previous real integrations.

This skill belongs to the `dev-integration` domain.

Its value is not to re-document the entire OpenID Connect protocol or duplicate GCBA identity procedures. Its value is to encode the **real integration sequence, decision points, failure patterns, and non-regression practices** learned from an already-executed migration.

---

## Owner

Primary owner:

`dev-integration`

Related skills / references:

- `dev-identidad`
- `dev-tramites-asi`
- `dev-api`
- `dev-backend-implementation`
- `dev-frontend-implementation`
- `dev-security-analysis`
- `dev-miba`

This skill must reference identity norms and ticket procedures rather than duplicating them.

---

## Core Principle

The skill must answer:

> How can this application integrate OpenID Connect safely, with the correct identity configuration, without breaking the authentication path that already works?

The skill must apply this principle:

> Resolve identity, client, redirect, identifier, and environment decisions before modifying authentication code.

A migration must not begin from implementation details when critical identity decisions are still unresolved.

---

# Knowledge Classification

This skill must explicitly distinguish four categories of knowledge.

## 1. Observed Evidence

Facts verified in the reference integration through code, plans, or project documentation.

These facts are evidence from one real integration and must not automatically be generalized to every application.

## 2. Operational Rules

Rules derived from the observed integration that should guide execution order, validation, regression protection, and escalation.

## 3. Criterion Recommendations

Recommendations explicitly identified as `[criterion]` in the source material.

They are reusable engineering guidance, not GCBA normative requirements unless another authoritative source confirms them.

## 4. Open Decisions

Questions that remained unresolved in the reference integration.

The skill must not silently answer these questions.

It must escalate or request confirmation.

---

# Source Boundaries

This skill does **not** own:

- the GCBA identity norm
- the full definition of authentication requirements
- the administrative identity ticket procedure
- the canonical list of ticket fields
- security assessment approval
- the implementation or operational behavior of miBA

Those responsibilities remain outside this skill.

Use:

```text
dev-identidad
→ normative identity rules

dev-tramites-asi
→ identity-request / ticket procedure

dev-security-analysis
→ security assessment and security validation

dev-miba
→ miBA-specific authentication integration, configuration, session behavior, login/logout, and provider-specific rules
```

This skill owns:

```text
real integration sequence
client-context handling
redirect/logout coordination
identifier verification
login non-regression
OIDC troubleshooting
claim-contract verification
state handling
legacy-provider migration order
OIDC coexistence and migration boundaries with other authentication providers
```

---

# Required Context

The skill should receive the smallest context necessary for the assigned OpenID Connect integration.

Expected context may include:

- WorkUnit objective
- Jira issue / HU / Bug / Task
- identity request status
- target environments
- current authentication flow
- current login/logout behavior
- current OIDC provider configuration
- application/backend/frontend structure
- identity client configuration
- redirect URI configuration
- post-logout redirect URI configuration
- current claims
- current user identifier mapping
- current user database model
- existing roles/access rules
- applicable ADRs
- relevant project documentation
- existing security assessment status
- applicable GCBA rules
- available capabilities
- required checks

The skill must not invent any missing identity configuration.

---

# Result Statuses

Supported result states:

- `COMPLETE`
- `PARTIAL`
- `MISSING_CONTEXT`
- `CAPABILITY_GAP`
- `CHECK_GAP`
- `POLICY_BLOCKED`
- `APPROVAL_REQUIRED`
- `IDENTITY_PREREQUISITES_INCOMPLETE`
- `OIDC_CLIENT_MODEL_UNRESOLVED`
- `IDENTITY_CONFIGURATION_DECISION_REQUIRED`
- `USER_IDENTIFIER_UNVERIFIED`
- `IDENTIFIER_NORMALIZATION_REQUIRED`
- `BASELINE_MISSING`
- `OIDC_CLIENT_CONTEXT_MISMATCH`
- `OIDC_REDIRECT_URI_MISMATCH`
- `OIDC_POST_LOGOUT_URI_MISMATCH`
- `OIDC_STATE_NOT_VALIDATED`
- `CLAIM_CONTRACT_MISMATCH`
- `SECRET_CONFIGURATION_RISK`
- `PRODUCTION_CONFIGURATION_RISK`
- `LEGACY_FLOW_REGRESSION_RISK`
- `SECURITY_ASSESSMENT_REQUIRED`
- `INTEGRATION_REVIEW_REQUIRED`
- `SECURITY_REVIEW_REQUIRED`
- `FAILED`

The orchestrator must be able to react to these states without relying only on free-form prose.

---

# Mandatory Execution Order

The reference integration demonstrated that the highest-cost rework occurred before coding.

Therefore the skill must execute in phases.

```text
Phase 0 — Identity prerequisites
Phase 1 — User identifier verification
Phase 2 — Existing-login baseline
Phase 3 — Application/client variation model
Phase 4 — Backend OIDC flow
Phase 5 — Frontend authorization flow
Phase 6 — Logout flow
Phase 7 — End-to-end + regression validation
Phase 8 — Legacy provider removal
```

Phases 0, 1, and 2 should complete before authentication code is changed.

Phase 8 must remain last.

---

# Phase 0 — Identity Prerequisites

## Objective

Confirm that the identity-request prerequisites required to design the integration are known.

The skill must not duplicate the complete administrative ticket procedure.

It should reference `dev-tramites-asi` when procedural details are required.

## Required Information

At minimum, resolve or explicitly mark pending:

```text
target environments
client model
redirect URI list
post-logout redirect URI list
identity-provider-specific unresolved fields
production-client status
```

Example:

```yaml
identityPrerequisites:

  environments:
    - DEV
    - QA
    - HML

  clientModel:
    status: CONFIRMED
    value: DEDICATED_CLIENT_PER_APPLICATION

  redirectUris:
    status: CONFIRMED

  postLogoutRedirectUris:
    status: CONFIRMED

  unresolvedIdentityFields: []
```

If these are incomplete:

return:

`IDENTITY_PREREQUISITES_INCOMPLETE`

---

# Phase 1 — Verify the User Identifier

## Objective

Prove how the OIDC identity is mapped to the application's actual user model before changing authentication logic.

The skill must inspect:

```text
OIDC claim
    ↓
application mapping
    ↓
database/application identifier
```

Never assume that the claim used in one GCBA application applies to another.

## Reference Integration Evidence

In the reference integration:

```text
preferred_username
→ CUIL
→ USUARIOS.USUARIO
```

The backend explicitly mapped `preferred_username` into the application's document-number field.

This is **reference evidence**, not a universal GCBA rule.

## Multi-Environment Verification

The identifier must be checked against available environments.

Do not treat one environment as sufficient evidence when no representative data exists there.

The important operational rule is:

> Verify the real stored identifier against environments that actually contain representative data.

If no representative environment can prove the mapping:

return:

`USER_IDENTIFIER_UNVERIFIED`

## Identifier Normalization

The skill must detect whether normalization is required.

Do not assume that one identifier can always be safely reconstructed from another.

If normalization is required:

return:

`IDENTIFIER_NORMALIZATION_REQUIRED`

and request an explicit data/business decision.

---

# Phase 2 — Capture the Existing Login Baseline

## Objective

Produce concrete evidence of the authentication path that currently works before changing it.

Required baseline evidence may include:

```text
login request sequence
authorization redirect
callback behavior
session/token result
role/access result
logout behavior
environment used
```

If the existing path is expected to remain operational but no baseline was captured:

return:

`BASELINE_MISSING`

---

# Phase 3 — Resolve the Client Model

## Objective

Determine how identity clients are assigned across applications before implementing OIDC variation logic.

The skill must not assume:

```text
shared client
```

or:

```text
dedicated client per application
```

without explicit confirmation.

Possible states:

```text
SHARED_CLIENT
DEDICATED_CLIENT_PER_APPLICATION
PENDING_CONFIRMATION
```

If unresolved:

return:

`OIDC_CLIENT_MODEL_UNRESOLVED`

## Observed Evidence

The reference integration went through multiple redesigns because the client model was assumed before Identity confirmed what would actually be delivered.

Therefore:

> Identity configuration must override assumptions derived from examples or permissive wording in guidance.

## Criterion Recommendation — Variation Point per Application

`[criterion]`

Even when the client model is not yet confirmed, design the backend so that application-specific OIDC configuration can vary without redesigning the complete authentication flow.

The reference implementation needed four variation points:

```text
redirect URI
client ID
client secret
logout URL
```

A minimal application discriminator may be used conceptually:

```text
FRONT
BACKOFFICE
```

The exact implementation may differ by language/framework.

---

# Phase 4 — Backend OIDC Flow

The backend OIDC path must be inspected and validated end-to-end.

Expected conceptual sequence:

```text
Authorization Code
       ↓
Token Exchange
       ↓
Token Introspection
       ↓
UserInfo
       ↓
Identifier Mapping
       ↓
Application User Resolution
       ↓
Role / Access Policy
```

A successful token exchange alone does not prove the complete login path.

## Client Context Propagation

When multiple OIDC clients/applications exist, the selected application/client context must be propagated consistently.

Operational rule:

> Never exchange, introspect, log, or logout using credentials/configuration from a different client context than the one that originated the flow.

If a token is validated/introspected using the wrong client context:

return:

`OIDC_CLIENT_CONTEXT_MISMATCH`

## Preserve the Existing Path

The migration must not silently replace a working authentication path before the new path is validated.

Principle:

```text
Existing authentication
→ preserved

New OIDC flow
→ added through an explicit variation point
```

The reusable rule is:

> Extend without changing the behavior of the existing login path unless the WorkUnit explicitly requires replacement.

If the change risks breaking the old path:

return:

`LEGACY_FLOW_REGRESSION_RISK`

---

# Role / Access Rules

Role and access rules must remain readable, testable application logic when they represent business/access policy.

Do not hide complex role semantics inside database query behavior when doing so makes the rule ambiguous or accidental.

If a role rule belongs to identity/security policy:

coordinate with:

- `dev-identidad`
- `dev-security-analysis`
- `dev-miba`

---

# Phase 5 — Frontend Authorization Flow

## State Handling

If `state` is used, it must actually be validated.

Expected lifecycle:

```text
generate state
      ↓
store temporary state
      ↓
send state in authorization request
      ↓
receive callback
      ↓
compare returned state
      ↓
delete stored state
```

The reference integration used:

```text
crypto.getRandomValues
sessionStorage
single-use deletion
```

Treat those as reference implementation evidence, not mandatory framework choices.

Operational rule:

> State must be unpredictable, validated, and single-use.

If state is sent but not validated:

return:

`OIDC_STATE_NOT_VALIDATED`

---

# Phase 6 — Redirect URI and Logout

## Redirect URI and Post-Logout URI Are Different Sets

The skill must always model these separately:

```text
Valid Redirect URIs
≠
Valid Post Logout Redirect URIs
```

Do not infer one list from the other.

## Redirect URI Authority

The skill must identify which component actually determines the `redirect_uri` used during token exchange.

Possible controllers:

```text
frontend
backend
gateway / adapter
```

Do not assume the frontend is authoritative.

If authorization and token-exchange redirect URIs differ:

return:

`OIDC_REDIRECT_URI_MISMATCH`

## Logout Flow

Logout must be treated as an explicit authentication flow.

Expected conceptual sequence:

```text
application context
      ↓
correct OIDC client
      ↓
correct logout endpoint
      ↓
correct post_logout_redirect_uri
      ↓
provider logout
      ↓
application return
```

When multiple applications/clients exist, logout must resolve the correct client context.

If post-logout configuration is invalid:

return:

`OIDC_POST_LOGOUT_URI_MISMATCH`

## Logout Observability

Logout failures must leave operational evidence.

Do not log sensitive complete logout URLs when they contain sensitive values such as:

```text
id_token_hint
```

Coordinate with:

- `dev-observability`
- `dev-security-analysis`
- `dev-miba`

---

# Claim Contract Validation

Claims written by one component and read by another must be checked as a contract.

Operational rule:

```text
claim produced
      ↓
claim consumed
      ↓
exact contract comparison
```

If producer and consumer names differ:

return:

`CLAIM_CONTRACT_MISMATCH`

---

# JWT Validation Rules

Do not add ad hoc JWT validation that duplicates or conflicts with the approved JWT/OIDC library without a documented requirement.

Operational rule:

> Prefer protocol/library validation over custom assumptions about token structure unless an explicit project/security requirement exists.

If custom validation exists:

request:

`dev-security-analysis`

when its necessity or correctness is unclear.

---

# Phase 7 — End-to-End and Regression Validation

The new OIDC path must be validated end-to-end.

Minimum validation areas:

```text
authorization
token exchange
introspection
userinfo
identifier mapping
application user resolution
role/access policy
state validation
session behavior
logout
redirects
claims
existing login regression
```

The old authentication path must be re-tested if it is expected to remain available.

---

# Boundary with miBA

miBA is **not** part of OpenID Connect and must not be modeled as an OIDC implementation detail.

When a project currently uses miBA and is migrating to OpenID Connect, this skill may inspect the existing miBA path only to:

```text
capture the current authentication baseline
preserve non-regression
identify coexistence requirements
plan rollback
determine when the old provider can be safely removed
```

The actual implementation and provider-specific behavior of miBA belong to:

`dev-miba`

Therefore:

```text
dev-openid-connect
→ owns the new OIDC integration and migration coordination

dev-miba
→ owns miBA-specific integration behavior
```

This skill must not duplicate or redefine miBA authentication rules.

---

# Phase 8 — Legacy Provider Removal

Legacy provider cleanup must happen only after:

```text
new login validated
new logout validated
target environments validated
identity configuration confirmed
regression of existing path validated
security requirements satisfied
rollback no longer required
```

Therefore:

```text
legacy provider removal
→ LAST PHASE
```

If removal is attempted too early:

return:

`LEGACY_FLOW_REGRESSION_RISK`

---

# Production Configuration Rules

Production must not silently reuse lower-environment client configuration.

Operational rule:

```text
production client not delivered
→ explicit placeholder / blocked configuration

NOT:
→ DEV credentials copied into PROD
```

If lower-environment credentials appear in production configuration:

return:

`PRODUCTION_CONFIGURATION_RISK`

---

# Secrets

Secrets must remain outside source code.

The skill must never:

```text
hardcode client secrets
write secrets into repository files
print secrets
return secrets in structured results
log secrets
copy secrets between environments
```

If violated:

return:

`SECRET_CONFIGURATION_RISK`

---

# Security Assessment

Authentication-flow changes may require a new security assessment.

Therefore the skill must evaluate:

```text
authentication flow changed?
        ↓
YES
        ↓
SECURITY_ASSESSMENT_REQUIRED
```

The skill must not self-approve the assessment.

Delegate to:

`dev-security-analysis`

---

# Diagnostic Guidance

The following are **observed diagnostic hypotheses from the reference integration**.

They are not universal protocol guarantees.

| Symptom | High-probability hypothesis from reference integration |
|---|---|
| `invalid_client` with placeholder credentials | The request reached the real provider; local flow may be structurally correct but credentials are intentionally invalid |
| `unauthorized_client` | Re-check client credentials, especially secret/configuration |
| `active: false` without visible cause | Possible client-context mismatch during introspection |
| `invalid_grant` | Check whether authorization and token-exchange `redirect_uri` values match exactly |
| Login works but a field is `undefined` | Check claim producer/consumer naming |

Always confirm against the current provider response and application configuration.

---

# Open Decisions

The source integration left unresolved questions around:

- localhost post-logout URI approval
- backoffice local callback registration
- production client delivery
- unresolved Identity ticket fields
- non-TLS redirect URI acceptance in some non-production environments

The skill must treat equivalent unresolved items as explicit decisions.

Do not silently fill them with general OIDC assumptions.

Return:

`IDENTITY_CONFIGURATION_DECISION_REQUIRED`

when provider/identity-team confirmation is required.

---

# Required Capabilities

Typical capabilities include:

```text
repository.read
repository.search
repository.write
configuration.inspect
environment.config.inspect
authentication.flow.inspect
oidc.client.inspect
oidc.claim.inspect
oidc.redirect.inspect
database.schema.inspect
database.query.inspect
api.routes.inspect
tests.run
```

Depending on the environment:

```text
http.request.execute
identity.provider.inspect
logs.query
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If a required capability is unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Checks

The skill may declare required Checks.

Examples:

- OIDC identifier mapping
- OIDC client context consistency
- redirect URI consistency
- post-logout URI consistency
- state validation
- claim contract consistency
- secret externalization
- production configuration isolation
- logout observability
- login non-regression
- security assessment requirement

The skill must not self-approve formal Checks.

If a required Check does not exist:

return:

`CHECK_GAP`

---

# Policies

Potential policy concepts include:

- identity prerequisites before implementation
- no assumption of client model
- preserve existing authentication path until validation
- secrets externalized
- no cross-environment secret reuse
- no unvalidated OIDC state
- redirect and post-logout URI separation
- no legacy provider removal before regression completion
- security assessment required after authentication-flow change

Policy names are harness implementation details.

---

# Output Contract

Return a structured result.

Example:

```yaml
openidIntegrationResult:

  status: COMPLETE

  identityPrerequisites:
    ticketReady: true
    environments:
      - DEV
      - QA
      - HML
    clientModel: DEDICATED_CLIENT_PER_APPLICATION
    redirectUrisValidated: true
    postLogoutRedirectUrisValidated: true
    unresolvedDecisions: []

  identifier:
    claim: preferred_username
    applicationIdentifier: CUIL
    persistenceField: USUARIOS.USUARIO
    verified: true

  baseline:
    existingLoginCaptured: true
    existingLogoutCaptured: true

  clientVariation:
    applications:
      - FRONT
      - BACKOFFICE
    varies:
      - redirectUri
      - clientId
      - clientSecret
      - logoutUrl

  backendFlow:
    token: VERIFIED
    introspection: VERIFIED
    userInfo: VERIFIED
    userResolution: VERIFIED
    rolePolicy: VERIFIED

  frontendFlow:
    authorization: VERIFIED
    state:
      generated: true
      validated: true
      singleUse: true

  redirects:
    authorization: VERIFIED
    postLogout: VERIFIED

  logout:
    dedicatedPerApplication: true
    operationalLogging: true
    sensitiveUrlLogged: false

  claims:
    contractsVerified: true

  secrets:
    externalized: true
    environmentReuseDetected: false

  regression:
    previousLoginPathPreserved: true
    previousLoginPathValidated: true

  security:
    assessmentRequired: true
    delegatedTo:
      - dev-security-analysis

  cleanup:
    legacyProviderRemovalAllowed: true

  requiredChecks:
    - oidc-identifier-mapping
    - oidc-client-context
    - oidc-redirect-uri
    - oidc-post-logout-uri
    - oidc-state-validation
    - oidc-claim-contract
    - oidc-secret-externalization
    - oidc-regression

  risks: []

  assumptions: []

  evidence: []
```

---

# Model Routing Metadata

The skill may provide complexity signals to `automatic-consumption`.

It does not select the final model.

## STANDARD

Use for:

- inspection of an established OIDC integration
- simple client-configuration updates
- redirect/logout configuration review
- claim-contract verification
- baseline/regression validation
- straightforward state-handling implementation

## REASONING

Consider when:

- multiple applications/clients exist
- client model is ambiguous
- identifier mapping is unclear
- multiple environments diverge
- legacy and new authentication paths coexist
- role/access behavior is complex
- redirects are controlled by different application layers
- introspection/userinfo behavior is inconsistent
- migration requires non-trivial non-regression design

## PREMIUM

Consider only when:

- previous reasoning attempts fail
- authentication architecture is unusually complex
- security risk is high
- multiple unresolved identity models remain valid
- the integration affects many applications or shared identity infrastructure

Premium execution must pass the orchestrator's Human Model Gate.

---

# Escalation Conditions

Escalate to the `dev-orchestrator` when:

- identity prerequisites are incomplete
- the client model is unresolved
- identifier mapping cannot be proven
- no representative environment exists
- the existing login baseline is missing
- configuration contradicts provider behavior
- redirect/post-logout configuration requires Identity confirmation
- the old authentication path may regress
- a security assessment is required
- secrets are incorrectly configured
- production configuration is unsafe
- another specialist skill is required
- a required capability is unavailable
- a required Check is unavailable

---

# Prohibited Behavior

This skill must not:

- invent values for undefined Identity fields
- assume a shared client without confirmation
- assume dedicated clients without confirmation
- assume a specific user-identifying claim
- validate only DEV when DEV has no representative data
- generalize Desalojos-specific mappings to every project
- hardcode secrets
- copy DEV credentials into PROD
- remove the previous provider before end-to-end/regression validation
- modify the working login path without capturing a baseline
- hide role/business policy inside accidental query behavior
- send `state` without validating it
- invent provider redirect behavior
- treat redirect URI and post-logout URI as the same list
- log sensitive logout URLs or token hints
- duplicate `dev-identidad`
- duplicate `dev-tramites-asi`
- implement or redefine miBA-specific authentication behavior
- self-approve the security assessment
- bypass Policies
- self-approve Checks
- invent missing project context

---

# Evidence Requirements

The result must distinguish:

- observed project facts
- reference-integration evidence
- current-project evidence
- assumptions
- `[criterion]` recommendations
- open decisions
- tests executed
- regression evidence
- unresolved Identity questions
- formal Checks still required

All meaningful integration decisions must be traceable to one or more of:

- WorkUnit
- project code
- project configuration
- current identity ticket/status
- current environment evidence
- existing authentication behavior
- applicable identity/security rules
- reference integration evidence

---

# Success Criteria

This skill is successful when it:

- resolves identity prerequisites before coding
- proves the user identifier mapping
- validates against representative environment data
- captures the previous login baseline
- confirms the real client model
- supports application-specific client variation when required
- propagates the correct client context through token/introspection/userinfo/logout
- preserves the previous authentication path until replacement is safe
- validates redirect and post-logout configuration separately
- validates OIDC state correctly
- validates claim producer/consumer contracts
- keeps secrets externalized
- prevents lower-environment credentials from leaking into production
- validates logout independently
- performs end-to-end and non-regression verification
- triggers security assessment when authentication flow changes
- removes the legacy provider only after successful migration validation
- produces structured evidence
- escalates unresolved Identity decisions instead of inventing them

---

# Reference Integration Evidence

This skill was derived from a real GCBA migration **from an existing miBA authentication path to a new OpenID Connect integration** in the Desalojos frontend (August 2026).

miBA and OpenID Connect are treated as separate integration domains. The reference migration is evidence about coexistence, sequencing, rollback, and migration risk; it does not make miBA part of this OIDC skill.

The source material explicitly states that it is:

- not the normative identity rule
- not the administrative ticket procedure
- operational integration knowledge learned from an executed migration

The skill must preserve that distinction.

---

# Source

Primary operational-learning source:

`openid-integracion-aprendizajes.md`

This skill must remain aligned with the reference evidence and must not silently turn project-specific observations into universal GCBA rules.
