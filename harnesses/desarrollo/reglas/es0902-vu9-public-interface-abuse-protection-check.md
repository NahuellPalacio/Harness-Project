# Check: public-interface-abuse-protection

## Purpose

Deterministically verify ES0902 Vu9 for public application functionality accessible without authentication.

## Inputs

```text
unauthenticatedPublicInterfacePresent
public surface inventory
authentication/public-exposure evidence
gateway/router/application control configuration
topology/path evidence
test evidence
stability evidence
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Public unauthenticated surface inventory

Inventory all material public functionality reachable without authentication.

Incomplete:

`PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED`

### 3. Control coverage

For every applicable surface, identify the effective use-control mechanism(s).

If a surface has no control:

`ABUSE_CONTROL_MISSING`
→ FAIL

If material coverage is unclear:

`PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED`

### 4. Enforcement path

Resolve the actual path:

```text
client
→ public entry point
→ gateway/router/WAF/app control
→ protected resource
```

A configured control only counts if the governed request path traverses it.

If a public origin/backend path bypasses the control:

`ABUSE_CONTROL_BYPASS_PRESENT`
→ FAIL

### 5. Client-only control

A JavaScript delay, disabled button, client counter, or UI-only throttle cannot alone satisfy server-resource abuse control.

If no authoritative server/infrastructure enforcement exists:

`ABUSE_CONTROL_MISSING`
→ FAIL

### 6. Excessive-consumption mitigation

Determine whether effective controls bound or control excessive consumption for the surface.

Do not require a specific numeric rate unless an authoritative project requirement defines one.

Unknown effectiveness:

`EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED`

### 7. Automated-consumption mitigation

Determine whether effective controls mitigate automated use.

Do not require CAPTCHA specifically.

Unknown:

`AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED`

### 8. Stability evidence

Resolve credible evidence that controls support service stability.

Evidence may be configuration-based, test-based, or supported by existing performance/capacity evidence.

Do not require a numeric SLA unless authoritative.

Unknown:

`SERVICE_STABILITY_EVIDENCE_UNRESOLVED`

### 9. Shared controls

A shared gateway/WAF/router policy may cover multiple surfaces when topology/path evidence proves the binding.

Do not duplicate control configuration unnecessarily.

### 10. Runtime safety

Prefer static/config evidence before bounded runtime testing.

Runtime verification must use:

```text
authorized QA/test
bounded rate/concurrency
synthetic data
explicit stop conditions
non-destructive scenarios
```

Never run uncontrolled stress/DoS against PRD.

Unsafe:

`PUBLIC_ABUSE_TEST_UNSAFE`

### 11. Aggregate

PASS requires every material applicable public unauthenticated surface to have:

```text
resolved control coverage
non-bypassable enforcement
credible excessive-consumption mitigation
credible automated-consumption mitigation
credible service-stability evidence
```

Any confirmed missing/bypassable control causes FAIL.

Any material unresolved dimension prevents PASS.

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED
PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED
ABUSE_CONTROL_MISSING
ABUSE_CONTROL_BYPASS_PRESENT
EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED
AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED
SERVICE_STABILITY_EVIDENCE_UNRESOLVED
PUBLIC_ABUSE_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply:
- Vu1 PASS
- Vu10 PASS
- full performance/NFR compliance
- WAF approval
- official security approval
