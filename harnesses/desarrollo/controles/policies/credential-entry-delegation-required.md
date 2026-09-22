---
id: credential-entry-delegation-required
type: POLICY
rule: D2
---

# Policy: credential-entry-delegation-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D2
  supportingSections: ["8"]
```

The supporting material is the integrations section of the standard, pages 18 and 19. It states two
contexts and one obligation common to both: the user's credentials are entered at the GCBA identity
service, not at the application.

## Applicability

```text
authenticationPresent = TRUE         → applies
authenticationPresent = FALSE        → NOT_APPLICABLE
authenticationPresent = UNRESOLVED   → APPLICABILITY_UNRESOLVED
```

Applicability depends on `authenticationPresent` and on nothing else. A missing signal is never
`FALSE`, and a declared dependency does not set it to `TRUE`: a package in the manifest proves what
is installed, not what the application does.

## Statement

When authentication is present, application code must not collect or validate GCBA user credentials
directly. Credential entry is delegated to the GCBA authentication mechanism that corresponds to the
authentication context.

## The two contexts

```text
citizen-facing      → the GCBA citizen authentication service, which the standard states follows
                      OpenID Connect
institutional       → GCBA Active Directory through the OpenID authentication portal managed by
                      DGSEI, with Keycloak as the authorized and mandatory identity provider
```

The context is read from evidence. Where authentication exists and the audience cannot be
established, the answer is `AUTHENTICATION_CONTEXT_UNRESOLVED` — never a guess.

## Prohibited patterns

```text
application-owned username/password validation
an application database holding GCBA user passwords for login
a custom institutional login that captures credentials directly
the superseded identity endpoint used in place of the current authorized portal
```

The standard states that credentials are no longer issued on the superseded endpoint and that new
application versions must point at the current portal. Delegating to it is delegation to the wrong
place, which is not compliance.

🔴 A local login form does not become delegation because it calls an API afterwards. If the
application sees the password, credential entry was not delegated.

## What it does not do

It does not select the mechanism a citizen-facing application must use. That is **D1**, with its own
policy and its own check. D2 asks whether credential entry is delegated and whether the target
matches the context; it does not rule on whether the application should be citizen-facing.

It does not define the authorization model: application roles, permissions and token validation are
governed elsewhere.

It does not define provider internals — client identifiers, claims, redirect URIs, endpoints, logout
rules, registration procedures, secrets or environment-specific values. None of that is
authoritative in this harness.

## The ES0902 boundary

The standard refers security requirements to ES0902. This harness does not carry ES0902 as a
declared normative source. Requirements that depend specifically on it resolve to
`ES0902_CONTEXT_REQUIRED`, and none of them is invented. That boundary does not block what ES0901
states directly: delegation and the authorized provider are verified regardless.

## Evidence it requires

```yaml
application:
  id: <application or component id>
  environment: <environment the evidence belongs to>
authenticationFlows:
  - flowId: <id>
    audience: CITIZEN | INSTITUTIONAL | UNRESOLVED
    credentialEntry: DELEGATED | APPLICATION_OWNED | UNRESOLVED
    provider: GCBA_CITIZEN_AUTHENTICATION | DGSEI_OPENID_KEYCLOAK | LEGACY_OPENID_ENDPOINT | APPLICATION_LOCAL | UNRESOLVED
    evidenceRefs: [<evidenceId>, ...]
evidence:
  - evidenceId: <id>
    sourceType: GCBA_NORMATIVE | PROJECT_CONFIGURATION | PROJECT_DOCUMENTATION | REPOSITORY_CONFIGURATION | REPOSITORY_DEPENDENCY | HUMAN_CONFIRMATION | AGENT_STATEMENT
    reference: <where it is>
    claim: <what the source states>
```

The evidence is an input. Without it the policy resolves to `EVIDENCE_INCOMPLETE` — never to
compliant.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
AUTHENTICATION_CONTEXT_UNRESOLVED
ES0902_CONTEXT_REQUIRED
EVIDENCE_INCOMPLETE
SPECIALIZED_SKILL_GAP
```

`SPECIALIZED_SKILL_GAP` surfaces when remediating a citizen flow requires operational knowledge of
the citizen authentication service while `dev-miba` remains `DECLARED_NOT_INSTALLED`. 🔴 It does not
make D2 compliant, and `dev-openid-connect` is not a substitute for it: that skill covers
institutional OpenID Connect work, which is a different thing.

## Verified by

`authentication-delegation`

## Owners

`dev-integration`
