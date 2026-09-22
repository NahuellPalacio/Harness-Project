---
id: service-token-protection-required
type: POLICY
rule: D8
---

# Policy: service-token-protection-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D8
```

The rule is one sentence: *"Los servicios deben estar protegidos con sistema de token."*

## Binding

The installed normative matrix is authoritative for this rule's agents, policy id and check id.
This policy is bound to the D8 row of that matrix, and its check resolves the binding at evaluation
time instead of carrying the ids written inside it. If the D8 row cannot be resolved — the matrix is
absent, unreadable, has no such row, declares a number of applicability signals other than one, or
does not declare the check among its own — the outcome is `D8_MATRIX_BINDING_UNRESOLVED` and nothing
else is evaluated.

🔴 That gate runs **before** applicability. Without the row there is no way to know which signal the
rule depends on, and asking for the value of a signal whose name the module invented is worse than
not asking.

## Applicability

```text
serviceEndpointPresent = TRUE        → applies
serviceEndpointPresent = FALSE       → NOT_APPLICABLE
serviceEndpointPresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Applicability is resolved from an evidence-backed signal. Missing evidence is never `FALSE`. Not
finding a controller, not finding a service-contract file and not finding a route literal are not
evidence that the scope exposes no service: they are evidence that nobody looked there, or that the
behaviour sits behind a framework mapping, a shared library or a generated artifact.

Evidence may come from the TaskContext, the Jira record, controller and router definitions, service
contracts, gateway routes, framework mappings, runtime route discovery, tests, or a scope
classification confirmed by a person. The signal and the D8 evaluation must use the same scope.

## Statement

When applicable, **every material service endpoint in scope must enforce the project's authoritative
token-protection mechanism at the service boundary**, and the enforcement must happen before the
protected application behaviour runs.

Token code existing elsewhere in the application is not enforcement. An endpoint that issues tokens
does not protect the ones that consume them.

## The endpoint set is the whole endpoint set

The obligation is about every material path that reaches protected behaviour, not about the one
somebody tested:

```text
the primary route
an alternate address for the same behaviour
an alternate request method on the same resource
a legacy route still answering
a versioned route still answering
a secondary controller nobody migrated
a path the gateway exposes without passing through enforcement
an administrative route
an upload or download route
```

A path is identified by **which protected behaviour it reaches**, not by its address. Two paths that
reach the same behaviour are two doors to the same room, and one of them being locked says nothing
about the other. If the inventory cannot be established, or declares itself incomplete, the outcome
is `SERVICE_ENDPOINT_COVERAGE_UNRESOLVED`.

🔴 A path that does not declare whether it is still active is **not assumed to be switched off**.
Taking a route for dead because nobody said otherwise is the exact shape of this defect.

## Not Sufficient

None of the following, alone, proves compliance:

```text
a token library exists in the manifest
a security middleware is configured
an endpoint issues tokens
a sign-in path exists
the header that carries the token is parsed
a gateway exists in front of the service
a document says the route is private
an agent states that the service is protected
```

Every one of those is evidence of what is **installed**, **configured** or **claimed**, not of what
happens when a call arrives without a token. Compliance requires evidence that the call is rejected.

## The mechanism is declared, never guessed

This policy does not name the token technology, and neither does the check that verifies it. **No
mechanism name, issuer, audience, algorithm, claim, lifetime, refresh rule, header format, role,
scope, gateway product, network locator, route or rejection code is attributed to this rule.** None
of them is in any normative extract this harness holds, and writing one here would read as though
the standard required it.

The mechanism is an input, and it carries where it came from, where it is enforced and how the token
is supplied:

```yaml
tokenMechanism:
  id: <what the project declares>
  source: GCBA_NORMATIVE | PROJECT_SECURITY_CONTRACT | ASI_INTEGRATION_CONTRACT |
          PROJECT_INTEGRATION_AGREEMENT | HUMAN_CONFIRMATION
  reference: <where it says so>
  enforcementPoint: <where the check happens>
  tokenSupply: <how the call carries it>
  rejectionContract:
    defined: <true when the project contract fixes the rejection response>
    status: <only when defined is true>
```

Without an id, without a source from the list, without a reference, without an enforcement point or
without a supply, the outcome is `TOKEN_MECHANISM_UNRESOLVED`.

🔴 **No rejection code is required unless the authoritative contract defines one.** If it does, the
observed rejection must match it. If it does not, being rejected is enough, and the observed
response is recorded without being judged. Inventing the number would be inventing the contract.

## Nothing is exempt by itself

D8 defines no exemption. A sign-in path, a health path, a readiness path, a liveness path, a
catalogue, a webhook receiver and a deliberately public API are **not** exempted by this rule, and
no artifact of this rule carries a list of exempt categories or a route pattern.

An intentionally public endpoint requires an exception declared with an id, a source from the list
above and a reference. Without it, the outcome is `TOKEN_PROTECTION_EXCEPTION_UNRESOLVED` — the same
as for any other endpoint.

The distinction is deliberate: naming those categories here tells whoever reads that their intuition
is wrong. Putting them in a list would build the exemption this rule exists to refuse.

## What a compliant result does and does not say

```text
says          the endpoint requires the token, and without it the protected behaviour is refused
does not say  that roles or scopes are correct
does not say  which authentication mechanism the application owes its users
does not say  that credentials are not entered inside the application
does not say  that any other standard is met, or that a security assessment approved anything
```

A valid token being accepted proves the path works, not that the authorization behind it is right.
D8 is a boundary check, and the result of this rule carries only this rule's traceability tuple.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
D8_MATRIX_BINDING_UNRESOLVED
SERVICE_ENDPOINT_COVERAGE_UNRESOLVED
TOKEN_MECHANISM_UNRESOLVED
TOKEN_PROTECTION_EXCEPTION_UNRESOLVED
EVIDENCE_INCOMPLETE
```

🔴 None of the unresolved outcomes ever becomes `SATISFIED`. An unresolved state is a question
somebody has to answer, and turning it into compliance is how a rule stops being checked.

## Remediation boundary

The normative owners of the rule are the agents the matrix declares, and which installed skill
performs the work is resolved by the Agent Registry. This policy creates, modifies and renames no
agent and no skill.
