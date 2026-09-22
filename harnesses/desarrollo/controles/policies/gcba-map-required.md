---
id: gcba-map-required
type: POLICY
rule: D6
---

# Policy: gcba-map-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D6
  supportingSections: ["8"]
```

The rule is one sentence: georeferenced object visualizations must use the GCBA Map. The supporting
material is the Georreferenciación paragraph of the standard, page 19: *"Adicionalmente para el caso
de visualización de direcciones en mapa, debe utilizarse el mapa del GCABA."*

🔴 **That paragraph carries two rules, not one.** Its first sentence requires street addresses to be
normalized and validated through API GEO — that is **D5**. Its second sentence requires the map —
that is **D6**. They sit next to each other in the document and they are independent: an application
can normalize addresses perfectly and draw the result on somebody else's map.

## Applicability

```text
georeferencedVisualizationPresent = TRUE        → applies
georeferencedVisualizationPresent = FALSE       → NOT_APPLICABLE
georeferencedVisualizationPresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Applicability is resolved from an evidence-backed signal before this policy runs. Missing evidence
is never `FALSE`. Not finding a component named after a map, and not finding a coordinate literal,
are not evidence that no georeferenced visualization exists.

🔴 Neither `frontendPresent` nor `frontendAddressInputPresent` is a substitute. A frontend is not a
map, and an address field is not a map either.

## Statement

When applicable, every governed georeferenced visualization must use the GCBA Map. A generic
third-party mapping library, a custom tile source or an unrelated mapping SDK is **not equivalent by
default**, and becomes equivalent only with authoritative evidence that says so.

## The provider is declared, never guessed

This policy does not name the mechanism of the GCBA Map, and neither does the check that verifies
it. **No SDK or package name, no endpoint, no tile source, no layer identifier, no authentication
method, no CRS, no environment URL and no access token is attributed to this rule.** None of them is
in any normative extract this harness holds, and writing one here would read as though the standard
required it.

The provider identity is an input, and it carries where it came from:

```yaml
mapProvider:
  id: <declared by the project>
  source: GCBA_NORMATIVE | GCBA_CATALOG_ENTRY | ASI_INTEGRATION_CONTRACT |
          PROJECT_INTEGRATION_AGREEMENT | HUMAN_CONFIRMATION
  reference: <where it says so>
```

The list says which sources are defensible. It does not say what the mechanism is.

Two separate gaps, because they are answered by different people:

```text
GCBA_MAP_PROVIDER_UNRESOLVED     which mechanism is the GCBA Map is not established
MAP_INTEGRATION_CONTRACT_MISSING it is established, and how using it looks is not
```

## No provider is named here, not even as a counter-example

Third-party map libraries are not listed. A list of forbidden providers ages, invites *mine is not
on the list*, and moves the axis: the rule is not **avoid these**, it is **use the institutional
one**. Identity is compared against what the project declared, never against a catalogue of others.

## What never proves compliance on its own

```text
a map component exists in the code
a mapping library is in the manifest
coordinates are present in the data
a tile or layer configuration exists
a map screenshot exists
API GEO is called
somebody says the map is the institutional one
```

These may be supporting evidence. What answers the question is a run: the rendered view, tied to its
build and environment, reporting which provider actually drew it.

## Evidence it requires

```yaml
application: {id, environment}
build: {id, runtime}
testTarget: {available}
mapProvider: {id, source, reference}
integrationContract: {id, source, reference}
mapViews: {source, views: []}      # every material georeferenced view, with its id
results: []                        # one per governed view, with its provider and evidence
evidence: []                       # tied to the build and runtime that were tested, with its mode
```

The evidence is an input. Without it the policy resolves to `EVIDENCE_INCOMPLETE` — never to
compliant. Evidence declared as `MOCKED` documents the case and does not prove the behaviour.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
EVIDENCE_INCOMPLETE
MAP_VIEW_COVERAGE_UNRESOLVED
GCBA_MAP_PROVIDER_UNRESOLVED
MAP_INTEGRATION_CONTRACT_MISSING
```

## Boundaries

```text
D5   → whether addresses are normalized and validated with the cadastral option
D6   → whether the georeferenced visualization uses the GCBA Map
G1   → whether the mapping technology in use is homologated and on an approved version
D4   → whether that view adapts to the device it is seen on
```

A normalized address does not satisfy D6, and a compliant map does not satisfy D5. A homologated
library does not satisfy D6 either: being allowed to use a technology and being required to use the
institutional map are different obligations.

## One compliant view does not cover another

A `FAIL` on any governed view outranks any number of views that pass. The common shape of this
defect is exactly the mixed one: the main screen on the institutional map and an older screen on
something else.

## Verified by

`gcba-map-usage`

## Owners

`dev-integration`, with `dev-frontend` on the rendering side. This policy creates no skill: the
specialized knowledge of how the institutional map is integrated is declared as a gap through the
agent registry, and it is not filled by inventing it.
