---
id: openid-connect-authentication-required
type: POLICY
rule: C1
---

# Policy: openid-connect-authentication-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "3"
rule: C1
```

## Applicability

When `authenticationPresent = TRUE`.

## Requirement

Every C1-governed user-authentication surface must use OpenID Connect according to authoritative ASI/project identity context.

Library presence is not sufficient evidence.

## Appropriate Flow

The actual OIDC/OpenID flow must be supported by authoritative identity/project evidence and fit the application/client context.

Unknown flow:
`OIDC_FLOW_CONTEXT_UNRESOLVED`

Unknown authority/appropriateness:
`OIDC_FLOW_AUTHORITY_UNRESOLVED`

Do not choose a flow solely from framework defaults.

## ASI Policy Context

Authentication, authorization and resource-protection requirements must be traceable to available ASI/project evidence.

Missing policy context:
`ASI_IDENTITY_POLICY_CONTEXT_REQUIRED`

## Boundary

OIDC authentication does not prove application authorization or role correctness.

Application roles remain an application responsibility under the source text.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED
OIDC_PROTOCOL_EVIDENCE_UNRESOLVED
OIDC_FLOW_CONTEXT_UNRESOLVED
OIDC_FLOW_AUTHORITY_UNRESOLVED
ASI_IDENTITY_POLICY_CONTEXT_REQUIRED
EVIDENCE_INCOMPLETE
```
