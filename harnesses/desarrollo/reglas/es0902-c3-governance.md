# ES0902 C3 Governance Package

## Purpose

Operationalize ES0902 v6.2 §3 C3:

```text
C3 — Las aplicaciones deben respetar las herramientas versionadas y autorizadas
que se indican en el documento Estándar de Desarrollo, en su sección
“Versiones y Herramientas aceptadas por la ASI”.
```

C3 is intentionally implemented through shared controls with ES0901 G1.

It must not create a second technology catalog, a second version-comparison engine, or a second technology inventory.

## Matrix Binding

The installed ES0902 matrix declares:

```yaml
ruleKey: ES0902.C3
category: QUALITY

applicability:
  mode: ALWAYS
  signals: []

primaryAgents:
  - dev-architecture
  - dev-security

policies:
  - approved-technology-required
  - homologated-version-required

checks:
  - technology-homologation
  - technology-version-compliance

reviews: []
```

Do not rename these identifiers.

## Applicability

C3 is `ALWAYS`.

No applicability signal is introduced.

If technology inventory evidence is unavailable, C3 is unresolved; it is not NOT_APPLICABLE.

## Source-of-Truth Relationship

C3 explicitly delegates the concrete technology/version baseline to the Development Standard.

Current installed baseline:

```text
ES0901 v6.3
§6.10
§7.1 G1
Annex II
```

Current installed catalog:

```text
annex-ii-technology-catalog.json
source.standard = ES0901
source.version = 6.3
```

C3 consumes that baseline.

## No Parallel Homologation System

Do not create:

```text
es0902-technology-catalog.json
security-approved-technologies.json
c3-version-rules.json
second technology inventory
second version matcher
```

Reuse:

```text
approved-technology-required
homologated-version-required
technology-homologation
technology-version-compliance
annex-ii-technology-catalog.json
existing technology inventory
```

## Multi-Source Trace

The shared controls must preserve both normative sources:

```yaml
normativeSources:
  - standard: ES0901
    version: "6.3"
    rule: G1
  - standard: ES0902
    version: "6.2"
    rule: C3
```

One technical execution may satisfy evidence needs for both rules.

Do not copy the final G1 rule result into C3.

Instead:

```text
shared control outputs
→ ES0901.G1 aggregation
→ ES0902.C3 aggregation
```

This keeps source-specific rule trace intact.

## Active Development Standard Resolution

C3 references the Development Standard rather than freezing a forever-version inside ES0902.

The Harness must resolve the active authoritative Development Standard technology baseline.

Currently that is ES0901 v6.3.

If a newer ES0901 becomes authoritative but the Harness still holds an old catalog/control baseline:

`DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH`

If the active Development Standard cannot be determined:

`DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED`

Never silently continue using a superseded catalog.

## Catalog Integrity

Before C3 executes shared controls, verify:

```text
catalog source standard = active Development Standard
catalog source version = active Development Standard version
catalog status is usable
control implementation is installed
```

Mismatch or missing catalog:

```text
DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH
TECHNOLOGY_CATALOG_UNAVAILABLE
```

## Outcome Reuse

Preserve existing G1 semantics.

Examples:

```text
HOMOLOGATED
DEPRECATED_TOLERATED
NOT_HOMOLOGATED
ASI_EVALUATION_REQUIRED
TOOLCHAIN_AUXILIARY_REVIEW
VERSION_CONTEXT_REQUIRED
PROVIDER_VERSION_REQUIRED
UNRESOLVED
```

C3 must not reinterpret:

```text
DEPRECATED_TOLERATED
```

as fully current/homologated.

Likewise, "newer" does not mean "authorized".

## Provider-Assigned Technology Versions

The Development Standard catalog includes technologies such as:

```text
OpenID Connect
Keycloak
```

whose version context is provider-assigned by DGSEI.

C3 reuses the existing `PROVIDER_VERSION_REQUIRED` semantics.

Do not manufacture numeric versions.

## Security Boundary

C3 verifies authorized/versioned technology use.

It does not prove:

```text
absence of vulnerabilities
secure configuration
OWASP compliance
security assessment approval
acceptable vulnerability threshold
```

Those belong to other ES0902 rules and assessment controls.

C3 PASS must not automatically satisfy:

```text
Vu7
Vu10
G2
C2
```

## Relationship with Ve1

ES0902 Ve1 later expresses a materially overlapping versioning requirement.

Do not pre-implement a second control set for Ve1.

When Ve1 is installed, bind it to these same shared controls as another normative source if exact semantics remain aligned.

## Completion Criteria

C3 is complete when:

```text
- exact matrix binding is preserved
- C3 remains ALWAYS
- active Development Standard baseline is resolved
- ES0901 v6.3 catalog is reused for the current baseline
- existing G1 Policies/Checks are reused
- technology inventory is reused
- no duplicate technology catalog or matcher exists
- shared controls carry ES0901.G1 + ES0902.C3 trace
- C3 result is aggregated independently from shared control outputs
- baseline version drift fails closed
- security-specific conclusions are not inferred from technology compliance
- no Agent or Skill is created
```
