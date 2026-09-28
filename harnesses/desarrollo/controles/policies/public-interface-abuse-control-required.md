---
id: public-interface-abuse-control-required
type: POLICY
rule: Vu9
---

# Policy: public-interface-abuse-control-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu9
```

## Requirement

Every governed public functionality accessible without authentication must have effective use-control mechanisms that mitigate:

```text
excessive resource consumption
automated resource consumption
```

and preserve service stability.

## No Invented Mechanism

Vu9 does not mandate:
- a specific rate limiter
- CAPTCHA
- a WAF
- a specific API gateway
- a numeric rate
- a quota value
- a fixed concurrency limit

Any mechanism must be evaluated by effective outcome and path coverage.

## Enforcement Boundary

Client-only controls are insufficient for server/resource protection.

The effective control may live in application or infrastructure, but the public request path must traverse it.

Bypassable enforcement is non-compliant.

## Coverage

Every material public unauthenticated surface must have resolved control coverage.

Unknown material coverage:

`PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED`

## Excessive Consumption

The mechanism must provide credible evidence that resource use is bounded/controlled against excessive consumption.

Unknown:

`EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED`

## Automated Consumption

The mechanism must provide credible evidence mitigating automated consumption.

Unknown:

`AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED`

## Stability

Evidence must support that the chosen controls preserve service stability under the governed bounded conditions.

Unknown:

`SERVICE_STABILITY_EVIDENCE_UNRESOLVED`

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED
PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED
ABUSE_CONTROL_MISSING
ABUSE_CONTROL_BYPASS_PRESENT
EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED
AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED
SERVICE_STABILITY_EVIDENCE_UNRESOLVED
PUBLIC_ABUSE_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
