---
id: gcba-it-security-normative-review
type: REVIEW
rule: O1
---

# Review: gcba-it-security-normative-review

## Normative Source

```yaml
source:
  standard: ES0902
  version: "6.2"
  section: "3"
  rule: O1
  ruleKey: ES0902.O1
```

## What it decides

Whether the governed solution respects the applicable current IT principles and norms of the
GCABA — and, when that cannot be established, exactly what is missing.

This is a **governance** Review. It is not an automatic code-quality score, and no aggregation of
passing controls produces it.

## Inputs

```text
subject                the work unit or project under review
normative baseline     reglas/gcba-it-normative-baseline.json
ES0901 results         already produced, declared as evidence
ES0902 results         already produced, declared as evidence
overrides              contractual exception requests, ES0902 shape
```

The baseline and the results are data the harness already holds. Nothing here asks a reviewer to
transcribe by hand what the harness already knows.

## Procedure

1. Resolve scope. A review that does not say what it is about is not a review.
2. Resolve the applicable normative sources from the authoritative baseline. Every declared source
   is applicable.
3. Verify authority, version, loaded status and supersession status of each one.
4. Reuse the existing normative outcomes instead of duplicating controls.
5. Applicable source content missing → `EXTERNAL_NORMATIVE_CONTEXT_REQUIRED`.
6. Current/supersession status unknown → `NORMATIVE_SUPERSESSION_UNRESOLVED`.
7. Any supported failing applicable normative outcome prevents `COMPLIANT`.
8. Contractual exceptions require contract evidence **and** ASI approval evidence.

## Source status

```text
LOADED                        the harness holds the authoritative content
DECLARED_EXTERNAL_NOT_LOADED  a standard names it and the content is not here
```

There is no third status. "Known roughly" is not a status, it is permission to invent.

## Currency

```text
CURRENT      it is on record that the source is still in force
SUPERSEDED   it was replaced — and by which source has to be declared
UNRESOLVED   nothing is on record
```

Absent is `UNRESOLVED`, deliberately. That the harness loaded a version is not evidence that the
version is the current one.

## Result

```text
COMPLIANT
COMPLIANT_WITH_OBSERVATIONS
NON_COMPLIANT
REVIEW_INCOMPLETE
```

The four are the ones every normative Review of this harness uses; they are imported, not
redefined.

Unknown baseline, unknown supersession or missing external context ⇒ `REVIEW_INCOMPLETE`.

A failing applicable result titles the review as `NON_COMPLIANT` even when something else is
unresolved beside it. That ordering is the opposite of the generic review resolver, and it is
deliberate: O1's incompleteness is permanent today, and if it titled, a real normative failure
would hide behind a state that never moves. The incompleteness does not disappear — it travels in
`states` and in `issues`.

## Today's standing result

The installed baseline holds two loaded sources — ES0901 v6.3 and ES0902 v6.2 — and three sources
that ES0902 references and the harness does not hold: Resolución 177-ASINF-2013, Resolución
239-ASINF/2014 and N° 12/ASINF/17. None of the five declares its currency.

So every real run of this Review is `REVIEW_INCOMPLETE`. That is the correct result, not a defect
to be fixed by declaring `LOADED` or `CURRENT` without evidence.

## Approval boundary

This Review cannot create official DGSEI/GCBA security approval. `COMPLIANT` here sets nothing in
the assessment flow: an official state requires declared external provenance, and this Review is an
internal producer by construction.

## Reviewer

Owner agent `dev-security`. The resolution is mechanical —
`bin/orquestacion/linea_base.py` — and what it resolves is what the baseline and the
declared results say, never a judgment it makes up.
