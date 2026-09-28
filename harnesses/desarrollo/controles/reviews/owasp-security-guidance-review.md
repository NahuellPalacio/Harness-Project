---
id: owasp-security-guidance-review
type: REVIEW
rule: Vu10
---

# Review: owasp-security-guidance-review

## Purpose

Perform the semantic ES0902 Vu10 review for every applicable OWASP asset family.

This is a Review, not a deterministic Check.

## Inputs

```text
owaspApplicableAssetPresent
governed asset inventory
resolved authoritative OWASP editions/snapshots
trusted-source freshness state
existing security evidence/findings
bounded repository/configuration/test evidence
other ES0901/ES0902 results
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Resolve applicable families

For every governed asset, map to:

```text
WEB
API_OR_WEB_SERVICE
MOBILE
```

One application may require multiple families.

Incomplete asset/family mapping:

`OWASP_ASSET_COVERAGE_UNRESOLVED`

### 3. Bind authoritative OWASP source

For every applicable family record:

```text
edition/version
authoritative source reference
resolved/retrieved date
source fingerprint when available
freshness state
```

If source is unavailable:

`OWASP_GUIDANCE_SOURCE_UNAVAILABLE`

If freshness/currentness cannot be established:

`OWASP_GUIDANCE_FRESHNESS_UNRESOLVED`

Do not use model memory as source authority.

### 4. Enumerate guidance items

Use the actual guidance-item identifiers/titles from the resolved authoritative edition.

Do not hardcode an eternal item list into Vu10.

The review artifact must allow later edition changes without schema migration.

### 5. Review each guidance item

Every item receives exactly one disposition:

```text
REVIEWED_NO_FINDING
FINDING_PRESENT
NOT_APPLICABLE_WITH_RATIONALE
UNRESOLVED
```

`NOT_APPLICABLE_WITH_RATIONALE` requires:
- a concrete asset/scope reason
- evidence reference when applicable

Do not default items to NOT_APPLICABLE.

### 6. Reuse evidence

Prefer existing evidence already bound to the same asset/revision.

Examples:

```text
Vu5 result/evidence
Vu7 configuration evidence
Vu8 authorization evidence
Vu9 abuse-control evidence
Repository Integrity findings
dependency/configuration evidence
security assessment findings
authorized test evidence
```

Shared evidence is allowed.

Final ES0902 rule results remain independent.

### 7. Findings

When an OWASP item maps to a real issue:

```text
disposition = FINDING_PRESENT
```

Preserve/reference the finding through existing Security Reporting.

Do not duplicate the same finding solely because multiple OWASP items reference it.

Severity and confidence remain finding attributes, not Vu10 coverage states.

### 8. Review completion

Review coverage is complete only when:
- every applicable family has a resolved source edition
- every guidance item in that edition has a disposition
- no material item is UNRESOLVED
- every NOT_APPLICABLE has rationale
- source freshness is resolved

### 9. Vu10 result

```text
PASS
→ review coverage complete and guidance demonstrably considered

FAIL
→ an applicable family/item was ignored or required review was not performed

REVIEW_INCOMPLETE
→ one or more material review dimensions remain unresolved
```

A security finding may coexist with Vu10 PASS because Vu10 does not define a zero-finding threshold.

Security acceptance/readiness is determined separately by the existing assessment and finding policies.

### 10. Atomic Refutation support

Where one guidance item requires semantic interpretation, compile a bounded RefutationUnit using:
- one OWASP item
- one asset
- one bounded evidence scope

Do not replace this Review with Atomic Refutation.

Do not send the whole repository to the refuter.

### 11. Runtime safety

Do not perform uncontrolled exploitation, destructive testing, or unauthorized access.

Unsafe dynamic evidence remains unresolved.

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
OWASP_ASSET_COVERAGE_UNRESOLVED
OWASP_GUIDANCE_SOURCE_UNAVAILABLE
OWASP_GUIDANCE_FRESHNESS_UNRESOLVED
OWASP_GUIDANCE_COVERAGE_INCOMPLETE
OWASP_GUIDANCE_ITEM_UNRESOLVED
REVIEW_INCOMPLETE
```

## Boundary

PASS does not imply:
- zero OWASP-aligned findings
- security assessment approval
- absence of vulnerabilities
- Vu1-Vu9 PASS
- official GCBA/DGSEI approval

## Reviewer

The resolution is mechanical, in `bin/orquestacion/guia_owasp.py`: a model may fill the review record (dispositions, rationale, evidence), never the state. `dev-security` owns it.

## Harness operationalization of §9

The state is computed by `guia_owasp.py`. `FAIL` means one thing only: a performed review (at least one
family) omits an applicable family. An omitted item is `OWASP_GUIDANCE_COVERAGE_INCOMPLETE` and an empty
review is `REVIEW_INCOMPLETE`: both prevent `PASS` without claiming the guidance was ignored.
