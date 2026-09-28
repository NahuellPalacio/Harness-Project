# ES0902 Vu9 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu9:

```text
Vu9 — Las aplicaciones que expongan funcionalidades accesibles sin autenticación a través de
interfaces públicas (web o API), deberán contemplar mecanismos de control de uso que mitiguen
riesgos por consumo excesivo o automatizado de recursos y garanticen la estabilidad del servicio.
```

Vu9 is an unauthenticated-public-interface abuse-control and service-stability control.

The normative direction is outcome-based:

```text
public unauthenticated functionality
→ use-control mechanism(s)
→ mitigate excessive consumption
→ mitigate automated consumption
→ preserve service stability
```

The source does not mandate a specific product, algorithm, rate, quota, CAPTCHA, WAF rule, or numeric threshold.

## Matrix Binding

Use exactly the installed ES0902 matrix binding:

```yaml
ruleKey: ES0902.Vu9
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - unauthenticatedPublicInterfacePresent

primaryAgents:
  - dev-security
  - dev-backend
  - dev-devops

policies:
  - public-interface-abuse-control-required

checks:
  - public-interface-abuse-protection

reviews: []
```

Do not rename these identifiers.

## Applicability

`unauthenticatedPublicInterfacePresent` is evidence-backed.

```text
TRUE
→ one or more application functionalities are reachable without authentication through a public web/API interface

FALSE
→ authoritative evidence establishes no governed public functionality is reachable without authentication

UNRESOLVED
→ public exposure/authentication coverage cannot be established
```

Do not infer TRUE merely because:
- a static asset is public
- the application has a public DNS name
- a health endpoint exists but is not public functionality in governed scope

Do not infer FALSE because:
- most endpoints require authentication
- the frontend itself is authenticated
- a public endpoint is "read-only"

## Public Surface Inventory

Inventory material public unauthenticated functionality independently.

Examples may include:

```text
public search
public form submission
public lookup
public document retrieval
public API endpoint
public registration/request flow
public webhook-like ingestion endpoint when unauthenticated/public
other unauthenticated functional operation
```

Static assets alone do not make Vu9 applicable unless they expose a governed functionality that consumes controlled service resources.

Incomplete surface coverage:

`PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`

## Use-Control Mechanisms

Vu9 does not prescribe a specific mechanism.

Evidence may include, when actually implemented:

```text
rate limiting
throttling
quota
concurrency control
request cost control
adaptive abuse control
CAPTCHA/challenge
queue/backpressure
resource-specific limits
gateway/reverse-proxy controls
application-level abuse controls
circuit-breaker/load-shedding behavior
```

This is an operational evidence taxonomy only.

Do not require all mechanisms.

The question is whether the effective mechanism(s) mitigate both:

```text
excessive consumption
automated consumption
```

and support service stability.

## Client-Side Controls Are Not Sufficient

A browser-side delay/button-disable/JavaScript counter cannot by itself satisfy Vu9 for a server resource.

Controls must be enforced at a boundary that an external consumer cannot trivially bypass.

## Layered Enforcement

Controls may live in:

```text
application
API gateway
reverse proxy
WAF
OpenShift ingress/router
other authoritative infrastructure layer
```

Vu9 does not require the control to be inside application code.

However, the Harness must verify that the governed public path actually traverses the enforcing layer.

If the origin/backend can be reached publicly while bypassing the declared control:

`ABUSE_CONTROL_BYPASS_PRESENT`

## Excessive Consumption

Do not invent a numeric request threshold.

Verify that the control has a bounded use/resource policy appropriate to the public functionality and that evidence exists showing requests cannot grow without control until service stability is threatened.

If the mechanism exists but effective excessive-consumption mitigation cannot be established:

`EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED`

## Automated Consumption

Do not equate automation mitigation only with CAPTCHA.

Rate controls, behavior controls, quotas, challenges, resource-cost controls, or other mechanisms may mitigate automated use.

If automation-specific risk is relevant but the effective mechanism cannot be established:

`AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED`

## Service Stability

Vu9 explicitly requires mechanisms that guarantee/preserve service stability.

Do not interpret this as a requirement for absolute mathematical proof or a fixed uptime percentage absent another authoritative requirement.

Acceptable evidence may include:

```text
bounded configuration
load/performance test evidence
controlled abuse test
concurrency/backpressure behavior
capacity/limit configuration
health/availability observations during bounded testing
```

If controls exist but no credible stability evidence can be established:

`SERVICE_STABILITY_EVIDENCE_UNRESOLVED`

## Per-Surface Verification

Evaluate each public unauthenticated functionality independently.

One protected endpoint does not prove another public endpoint is protected.

For each surface resolve:

```text
control coverage
enforcement layer
bypassability
excessive-consumption mitigation
automated-consumption mitigation
stability evidence
```

## Shared Infrastructure

A shared gateway/WAF/router policy may cover multiple surfaces.

Reuse the same evidence when the path binding is authoritative.

Do not duplicate the control definition merely to create one record per endpoint.

## Availability / Performance Boundary

Vu9 is a security abuse-control rule with a stability outcome.

Performance/observability evidence may support it, but:

```text
performance test PASS
!=
Vu9 PASS
```

and:

```text
Vu9 PASS
!=
full performance/NFR compliance
```

## Runtime Testing Safety

Do not perform uncontrolled load, denial-of-service simulation, or destructive stress against production.

Preferred order:

```text
configuration inspection
gateway/router/application control inspection
unit/integration tests
bounded QA load/abuse tests
existing authoritative performance evidence
```

Runtime test constraints:

```text
authorized environment
bounded rate/concurrency
synthetic/non-sensitive data
stop conditions
no production DoS behavior
```

Unsafe:

`PUBLIC_ABUSE_TEST_UNSAFE`

## Evidence Hygiene

Do not persist:
- real credentials
- sensitive payloads
- raw tokens/cookies
- personal data
- attack scripts capable of uncontrolled flooding

Persist:
- surface ref
- control ref
- configuration/evidence ref
- environment
- bounded test profile
- summarized result

## Relationship with Vu1

Vu1 governs abuse protection on authentication pages.

Vu9 governs unauthenticated public functionality generally.

A public login page may create evidence for both rules, but final results remain independent.

## Relationship with Vu10

Vu10 references OWASP guidance for applicable assets.

Vu9 is a concrete GCBA control requiring public unauthenticated use controls.

Do not make Vu9 PASS depend solely on a generic OWASP review.

## Atomic Refutation

Vu9 is compatible with the Atomic Refutation Pipeline.

Preferred flow:

```text
WorkUnit
+ ES0902.Vu9
+ bounded public-surface/control evidence
→ public-interface-abuse-protection Check
→ if conclusive: deterministic verdict
→ if semantic evidence remains: one RefutationUnit
```

Do not send the refuter the whole repository.

## Security Reporting

Feed Vu9 findings/results into the existing Security Reporting subsystem.

Recommended grouping:

```text
Public Exposure & Abuse Protection
```

Do not create a Vu9-specific reporting pipeline.

## Completion Criteria

Vu9 is complete when:

```text
- exact matrix binding is preserved
- applicability is evidence-backed
- public unauthenticated functionality is inventoried
- no specific mechanism or threshold is invented
- excessive and automated consumption are both addressed
- enforcement layer/path binding is verified
- client-only controls cannot prove PASS
- control bypass is detectable
- stability evidence is required but not over-specified
- runtime tests are bounded and safe
- Vu1/Vu10/performance controls remain independent
- Atomic Refutation is supported
- no Agent or Skill is created
```
