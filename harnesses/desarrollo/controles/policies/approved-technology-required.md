---
id: approved-technology-required
type: POLICY
rule: G1
---

# Policy: approved-technology-required

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

A GCBA development may only introduce technologies approved by ASI and listed in Annex II.

## What it constrains

Adding a language, runtime, framework, database, library, server or platform component that is
not present in the Annex II catalog.

## What it does not do

It does not approve anything. A technology absent from Annex II is **not rejected** by this
policy: it is `ASI_EVALUATION_REQUIRED`, and only ASI can resolve it. The harness never
homologates.

It does not govern *how* the technology is used — framework-based development, vanilla-language
prohibition and Node package-manager rules belong to P1, and duplicating them here would put the
same obligation under two owners.

## Evidence it requires

```yaml
technologyInventory:
  - technology: <id or alias>
    version: <as declared>
    role: <optional, TOOLCHAIN_AUXILIARY>
```

The inventory is an input. Without it the policy resolves to `UNRESOLVED` — never to compliant.

## Verified by

`technology-homologation`

## Owners

`dev-architecture`, `dev-devops`
