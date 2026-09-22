---
id: technology-practice-review
type: REVIEW
rule: G2
---

# Review: technology-practice-review

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: G2
```

## What it decides

Whether the implementation adopts the recognized industry practices applicable to each technology
in scope — and, when it does not, whether the deviation is justified.

This is a `REVIEW`, not a `CHECK`. Its structure is validated mechanically and always; the
technical judgment is contributed by whoever reviews and no test can contradict it.

## Scope input

The technology inventory comes from **G1**. Do not build a second stack detector: one inventory,
one place to fix it when it is wrong.

## Evidence

Six source classes, and the last two do not stand alone:

```text
GCBA_NORMATIVE                      the organism's own norm
OFFICIAL_TECHNOLOGY_DOCUMENTATION   the technology's official documentation
FORMAL_STANDARD                     a formal standard
RECOGNIZED_INDUSTRY_GUIDANCE        recognized industry guidance
PROJECT_IMPLEMENTATION              how the project is built — evidence of adoption
PROJECT_CONVENTION                  how the project does things — NOT proof of recognition
```

**An agent statement is not evidence.** A finding whose only backing is the reviewer's opinion does
not support a compliant result.

**A project convention does not make a practice industry-recognized.** It may prove the project is
consistent; it proves nothing about the industry.

## Practice strength

```text
REQUIRED_BY_SOURCE
RECOMMENDED_BY_SOURCE
OPTIONAL_BY_SOURCE
UNRESOLVED
```

The source's modality is preserved. What the source recommends is not enforced as required, and
what it requires is not downgraded to a suggestion. Changing modality silently rewrites the source.

## Applicability

```text
APPLICABLE
NOT_APPLICABLE
UNRESOLVED
```

Missing context resolves to `UNRESOLVED`, never to `NOT_APPLICABLE`. A practice marked not
applicable must carry its rationale — otherwise it is indistinguishable from one nobody looked at.

When the guidance behind a finding changes between versions of the technology, the finding
declares `versionDependent: true`. Declaring it is the reviewer's judgment; what follows is not: a
version-dependent finding on a subject without `version` is not judged either way — neither
adopted nor not applicable — and the review is `REVIEW_INCOMPLETE` with
`REVIEW_VERSION_CONTEXT_MISSING`.

## Result

```text
COMPLIANT                      every applicable practice adopted, evidence complete
COMPLIANT_WITH_OBSERVATIONS    deviations only from recommendations, evidence complete
NON_COMPLIANT                  deviation from an applicable REQUIRED_BY_SOURCE practice
REVIEW_INCOMPLETE              material evidence missing, applicability unresolved,
                               or version missing where the guidance depends on it
```

**Missing evidence never becomes success.** `REVIEW_INCOMPLETE` is the honest answer when the
review could not be completed, and it is not a pass.

## Deviations and exceptions

A deviation produces a finding. A justification may be recorded — and recording it **does not
approve the exception**: the result is `JUSTIFICATION_PENDING` until an approval authority that
does not exist yet decides.

## Source conflict

When two credible sources contradict each other, emit `SOURCE_CONFLICT` and preserve both. Choosing
the one that makes the implementation pass is the cheapest bias a reviewer can have, and it leaves
no trace.

## Reviewer

Owner: `dev-architecture`. Domain specialists contribute according to the technology —
`dev-backend`, `dev-frontend`, `dev-integration`, `dev-devops`, `dev-security`, `dev-quality`.

Every agent named must be declared in the Agent Registry. The review does not create agents.
