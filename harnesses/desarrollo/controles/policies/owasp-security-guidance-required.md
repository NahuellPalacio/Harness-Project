---
id: owasp-security-guidance-required
type: POLICY
rule: Vu10
---

# Policy: owasp-security-guidance-required

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu10
```

## Requirement

For every applicable WEB, API_OR_WEB_SERVICE, or MOBILE asset in governed scope, the corresponding OWASP guidance referenced by Vu10 must be explicitly considered through an evidence-backed Review.

## Applicable Families

```text
WEB
→ OWASP Top 10

API_OR_WEB_SERVICE
→ OWASP API Security Top 10

MOBILE
→ OWASP Mobile Top 10
```

Do not collapse multiple applicable families into one generic review.

## Source Freshness

The Review must bind each family to an authoritative OWASP edition/snapshot.

Required metadata:

```text
source family
edition/version
source reference
retrieved/resolved date
source fingerprint when available
freshness state
```

If freshness is unresolved:

`OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`

If source is unavailable:

`OWASP_GUIDANCE_SOURCE_UNAVAILABLE`

## Guidance Coverage

Every guidance item in the resolved edition must have one disposition:

```text
REVIEWED_NO_FINDING
FINDING_PRESENT
NOT_APPLICABLE_WITH_RATIONALE
UNRESOLVED
```

No silent omission is allowed.

## Findings Boundary

`FINDING_PRESENT` means the OWASP guidance surfaced or aligns with an actual finding.

That finding must feed existing Security Reporting.

Do not automatically fail Vu10 solely because a finding exists.

Vu10 evaluates whether OWASP guidance was actually considered with complete traceable coverage.

## No Extra Frameworks

Vu10 does not itself mandate ASVS, MASVS, SAMM, a particular scanner, or a vulnerability threshold.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
OWASP_ASSET_COVERAGE_UNRESOLVED
OWASP_GUIDANCE_SOURCE_UNAVAILABLE
OWASP_GUIDANCE_FRESHNESS_UNRESOLVED
OWASP_GUIDANCE_COVERAGE_INCOMPLETE
OWASP_GUIDANCE_ITEM_UNRESOLVED
OWASP_GUIDANCE_IGNORED
EVIDENCE_INCOMPLETE
```
