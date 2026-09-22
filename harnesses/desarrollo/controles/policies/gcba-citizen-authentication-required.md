---
id: gcba-citizen-authentication-required
type: POLICY
rule: D1
---

# Policy: gcba-citizen-authentication-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D1
  supportingSections: ["8"]
```

The supporting material is the integrations section of the standard, page 18: *"Toda aplicación que
genere una interacción con el ciudadano debe contar con la autenticación con BAID en su frontend"*,
and miBA provides that service *"siguiendo las especificaciones de OpenID Connect"*.

## Applicability

```text
citizenFacing = TRUE         → applies
citizenFacing = FALSE        → NOT_APPLICABLE
citizenFacing = UNRESOLVED   → APPLICABILITY_UNRESOLVED
```

Applicability is resolved before this policy runs, and it is resolved from an evidence-backed
signal. A missing signal is never `FALSE`.

## Statement

An application that interacts directly with the citizen must use the GCBA citizen authentication
mechanism. It must not replace it with an independent or local citizen credential system.

## What it constrains

Introducing a citizen login that issues, stores or verifies its own citizen credentials — a local
user table, a custom registration flow, a separate password reset — instead of the GCBA mechanism.

## What it does not do

It does not define miBA integration internals. It does not name client identifiers, claims,
redirect URIs, logout behaviour, token endpoints, registration procedures or environment-specific
provider values. That material is not authoritative in this harness yet, and writing it without a
source produces a file that reads authoritative and is not.

It does not govern credential entry and delegation. That is **D2**, with its own policy and its own
check. The supporting authentication material mentions OpenID Connect; that does not move D2's
verification here.

It does not govern institutional authentication. The same section of the standard requires the
opposite for what is not citizen-facing — Active Directory and the DGSEI OpenID provider — and
those are two mechanisms for two audiences.

## Evidence it requires

```yaml
application:
  id: <application or component id>
  environment: <environment the evidence belongs to>
authenticationFlows:
  - flowId: <id>
    audience: CITIZEN | INTERNAL | UNRESOLVED
    mechanism: GCBA_CITIZEN_AUTHENTICATION | CUSTOM_LOCAL_CREDENTIALS | INSTITUTIONAL_DIRECTORY | UNRESOLVED
    evidenceRefs: [<evidenceId>, ...]
evidence:
  - evidenceId: <id>
    sourceType: GCBA_NORMATIVE | PROJECT_CONFIGURATION | PROJECT_DOCUMENTATION | REPOSITORY_CONFIGURATION | HUMAN_CONFIRMATION | AGENT_STATEMENT
    reference: <where it is>
    claim: <what the source states>
```

The evidence is an input. Without it the policy resolves to `EVIDENCE_INCOMPLETE` — never to
compliant.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
EVIDENCE_INCOMPLETE
SPECIALIZED_SKILL_GAP
```

`SPECIALIZED_SKILL_GAP` surfaces when remediation requires miBA-specific implementation knowledge
while `dev-miba` remains `DECLARED_NOT_INSTALLED`. 🔴 It does not make D1 compliant: it names what
is missing to fix it.

## Verified by

`citizen-authentication-mechanism`

## Owners

`dev-integration`
