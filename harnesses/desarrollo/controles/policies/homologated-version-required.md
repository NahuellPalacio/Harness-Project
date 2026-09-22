---
id: homologated-version-required
type: POLICY
rule: G1
---

# Policy: homologated-version-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: G1
  supportingSections: ["6.10", "Annex II"]
```

## Statement

An approved technology must run at a version homologated by ASI for that technology.

## The version semantics it enforces

```text
homologated 8.2.30   ->  8.2.30 and 8.2.31 are valid
                     ->  8.2.29 is not
                     ->  8.1.x and 8.4.x do not become valid on their own
```

A branch older than the listed one is `NOT_HOMOLOGATED`. A branch newer than every listed one is
`ASI_EVALUATION_REQUIRED` — nobody has evaluated it yet, which is not the same as rejecting it.

A version listed as deprecated is **tolerated with a formal update observation**. Tolerated is not
homologated: it stays in the report, and ASI may still reject it for a critical vulnerability,
support problem or infrastructure incompatibility.

`latest`, `*` and an unpinned branch are not versions: there is nothing to compare them against.

## What it does not do

It does not decide that a version is two standards behind. That claim needs the catalogs of those
standards, and the installed Annex II is a snapshot of 6.3 — so it returns
`VERSION_HISTORY_REQUIRED` instead of blocking by inference.

## Verified by

`technology-version-compliance`

## Owners

`dev-architecture`, `dev-devops`
