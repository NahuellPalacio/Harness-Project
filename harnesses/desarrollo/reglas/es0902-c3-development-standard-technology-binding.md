# ES0902 C3 — Development Standard Technology Binding

## Objective

Bind ES0902 C3 to the technology/version authority defined by the active ES0901 Development Standard.

## Current Binding

```yaml
securityRule:
  standard: ES0902
  version: "6.2"
  rule: C3

developmentTechnologyAuthority:
  standard: ES0901
  version: "6.3"
  sections:
    - "6.10"
    - "7.1/G1"
    - "Annex II"

catalog:
  file: annex-ii-technology-catalog.json

sharedPolicies:
  - approved-technology-required
  - homologated-version-required

sharedChecks:
  - technology-homologation
  - technology-version-compliance
```

## Resolution Rule

The binding is valid only when the authoritative normative baseline identifies the same active ES0901 version as the installed catalog/control source.

Expected current relation:

```text
gcba-it-normative-baseline
ES0901 = 6.3 / LOADED

annex-ii-technology-catalog
source.standard = ES0901
source.version = 6.3
```

## Version Drift

If:

```text
active ES0901 version != catalog source version
```

return:

`DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH`

Do not continue with stale technology authorization results.

If active ES0901 cannot be resolved:

`DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED`

## Shared Execution

Execute each shared control once per identical evidence/input set.

Then attach source-specific normative traces.

Do not execute `technology-version-compliance` twice merely because two standards consume it.

## Rule Aggregation

C3 aggregation uses the shared control outcomes directly.

Do not perform:

```text
if ES0901.G1 == PASS:
    ES0902.C3 = PASS
```

Instead:

```text
technology-homologation result
+
technology-version-compliance result
→ C3 result
```

This avoids coupling final rule states while still eliminating duplicate work.

## Catalog Rules

All G1 catalog/version semantics remain authoritative, including:

```text
same-major/minor patch rule
deprecated tolerance
newer branch requires ASI evaluation
historical two-or-more-standard deployment block when evidenced
toolchain auxiliary treatment
provider-assigned version treatment
framework-dependent version treatment
```

C3 does not override these semantics.

## Evidence

C3 result should preserve:

```text
technology inventory reference
catalog version/source
shared Policy results
shared Check results
Development Standard baseline version
normative source trace
```
