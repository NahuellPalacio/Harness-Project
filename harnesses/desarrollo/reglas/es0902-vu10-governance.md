# ES0902 Vu10 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu10:

```text
Vu10 — Para mejorar la seguridad en las aplicaciones, se debe tener en cuenta la información
suministrada en los siguientes links:
- Aplicaciones Web: OWASP Top 10
- API’s y/o Web Services: OWASP API Security
- Aplicaciones Mobile: OWASP Mobile Top 10
```

Vu10 is a security-guidance review control.

It requires the Harness to determine which OWASP guidance families apply to the governed application assets, bind the review to an authoritative OWASP edition/snapshot, and preserve evidence that the guidance was actually considered.

Vu10 does not state that every application must be free of every OWASP Top 10 risk before the rule can be considered.

## Matrix Binding

Use exactly:

```yaml
ruleKey: ES0902.Vu10
category: SECURITY_PRINCIPLE
applicability:
  mode: CONDITIONAL
  signals:
    - owaspApplicableAssetPresent
primaryAgents:
  - dev-security
policies:
  - owasp-security-guidance-required
checks: []
reviews:
  - owasp-security-guidance-review
```

Do not rename identifiers. Do not invent a deterministic Check for Vu10.

## Applicability

`owaspApplicableAssetPresent` is evidence-backed.

```text
TRUE
→ at least one governed WEB, API_OR_WEB_SERVICE, or MOBILE asset exists

FALSE
→ authoritative evidence establishes none of those asset types exist in scope

UNRESOLVED
→ asset inventory/type coverage is incomplete
```

Internal/authenticated assets still count if they are WEB/API/MOBILE.

## Asset Families

Use:

```text
WEB
API_OR_WEB_SERVICE
MOBILE
```

A single application may require multiple families.

## OWASP Source Binding

ES0902 points to OWASP project URLs rather than fixed editions.

Harness operationalization:

```text
for every applicable family
→ resolve authoritative OWASP release/snapshot
→ record edition/version
→ record retrieval/source date
→ record source reference/fingerprint when available
```

Do not rely silently on model memory.

At package creation time, authoritative OWASP project pages report:
- WEB: OWASP Top 10 2025
- API_OR_WEB_SERVICE: OWASP API Security Top 10 2023
- MOBILE: OWASP Mobile Top 10 2024

These are current-source observations, not eternal hardcoded requirements.

If freshness cannot be established:

`OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`

If source cannot be obtained:

`OWASP_GUIDANCE_SOURCE_UNAVAILABLE`

Neither may become PASS.

## Review Semantics

For every guidance item in each resolved applicable edition, record one disposition:

```text
REVIEWED_NO_FINDING
FINDING_PRESENT
NOT_APPLICABLE_WITH_RATIONALE
UNRESOLVED
```

Missing item/disposition prevents a complete review.

`NOT_APPLICABLE_WITH_RATIONALE` requires evidence/rationale.

## Findings vs Vu10 Completion

Keep separate:

```text
guidance review coverage
≠
absence of security findings
```

A `FINDING_PRESENT` must feed Security Reporting, but it does not automatically mean Vu10 FAIL because the source requires that OWASP guidance be taken into account, not an explicit zero-finding threshold.

These prevent PASS:
- omitted applicable family
- omitted guidance item
- material `UNRESOLVED`
- source freshness unresolved
- source unavailable
- guidance demonstrably ignored

Stricter security-assessment rules may block acceptance independently.

## No Invented OWASP Requirements

Do not add ASVS, MASVS, SAMM, a mandatory scanner, numeric vulnerability thresholds, or mandatory deterministic checks unless another authoritative source requires them.

## Evidence Reuse

Reuse existing:
- security findings
- repository/security analysis
- architecture/configuration evidence
- other ES0901/ES0902 Checks
- authorized tests
- dependency/config evidence
- bounded semantic review

Do not duplicate expensive analysis already bound to the same asset/revision.

## Relationships

Specific rules remain independent:

```text
Vu5 = client/server validation parity
Vu8 = role/profile consistency
Vu9 = public unauthenticated abuse control
Vu10 = applicable OWASP guidance review
```

Evidence can be shared; final results cannot be copied.

## OWASP Edition Changes

A newer authoritative OWASP edition triggers trusted-source freshness/update handling. Do not keep claiming CURRENT against a stale snapshot.

## Atomic Refutation

Vu10 remains a Review. Atomic Refutation may support bounded semantic assertions inside the review, but it must not replace the Review itself.

```text
asset
→ resolved OWASP edition
→ guidance item
→ reuse deterministic evidence
→ bounded semantic review if needed
→ disposition
→ deterministic coverage aggregation
```

Never send the whole repository to `dev-refutador`.

## Runtime Safety

Dynamic evidence collection must remain authorized, bounded, non-destructive, and use synthetic/non-sensitive data.

Unsafe/unavailable dynamic testing remains unresolved evidence.

## Security Reporting

Reuse the existing Security Reporting subsystem.

`FINDING_PRESENT` must reference/create findings through normal reporting paths, preserving severity, confidence, asset and revision scope.

Do not create a Vu10-only ledger/dashboard.

## Completion Criteria

- exact matrix binding preserved
- WEB/API/MOBILE applicability evidence-backed
- each family bound to authoritative OWASP edition/snapshot
- freshness explicit
- every guidance item has a disposition
- NOT_APPLICABLE requires rationale
- findings distinct from review coverage
- no extra OWASP framework silently mandated
- Atomic Refutation only supports bounded semantics
- existing Security Reporting reused
- no Agent or Skill created
