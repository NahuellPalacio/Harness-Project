# Development Standard Technology Baseline Resolver

## Purpose

Resolve the authoritative technology/version source consumed by ES0902 C3.

This is supporting infrastructure, not a normative rule.

## Inputs

```text
gcba-it-normative-baseline.json
annex-ii-technology-catalog.json
Control Registry
current standard/version metadata
```

## Algorithm

```text
1. Resolve the active LOADED Development Standard source.
2. Require an unambiguous ES0901 version.
3. Load the Annex II technology catalog.
4. Compare catalog source.standard and source.version.
5. Verify required shared controls are installed.
6. Return resolved baseline binding.
```

## Output

```yaml
developmentTechnologyBaseline:
  status: RESOLVED | UNRESOLVED | MISMATCH
  standard: ES0901
  version:
  catalogRef:
  catalogVersion:
  policies:
    - approved-technology-required
    - homologated-version-required
  checks:
    - technology-homologation
    - technology-version-compliance
  evidence: []
```

## Fail-Closed States

```text
DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED
DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH
TECHNOLOGY_CATALOG_UNAVAILABLE
SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE
```

## Supersession

Do not select an older LOADED baseline simply because its catalog exists.

If multiple Development Standard versions are marked active/current and precedence cannot be established:

`DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED`

## Determinism

The resolver uses structured metadata only.

No LLM is required to determine version equality, source identity, catalog presence, or control installation.
