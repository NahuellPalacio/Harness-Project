---
id: gcba-cadastral-address-normalization-required
type: POLICY
rule: D5
---

# Policy: gcba-cadastral-address-normalization-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D5
  supportingSections: ["8"]
```

The rule is one sentence: every frontend address search or address entry must be validated and
normalized through the GCBA cadastral option. The supporting material is the first sentence of the
Georreferenciación paragraph, page 19: *"Las aplicaciones deben contar con direcciones de calles
normalizadas y validadas a través del servicio de API GEO disponible en el catálogo."*

🔴 **That paragraph carries two rules, not one.** Its first sentence is **D5** — addresses normalized
and validated. Its second sentence requires the institutional map — that is **D6**. They sit next to
each other in the document and they are independent: an application can normalize addresses
perfectly and draw the result on somebody else's map.

## Applicability

```text
frontendAddressInputPresent = TRUE        → applies
frontendAddressInputPresent = FALSE       → NOT_APPLICABLE
frontendAddressInputPresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Applicability is resolved from an evidence-backed signal before this policy runs. Missing evidence is
never `FALSE`. Not finding an input named after an address is not evidence that no address flow
exists: address fields carry project-specific names, live inside reusable components, and reach the
provider through indirect mappings. **Absence of a keyword is not evidence of absence.**

🔴 `frontendPresent` is not a substitute. A frontend is not an address field.

```text
frontendPresent = TRUE   → implies NOTHING about this rule
frontendPresent = FALSE  + declared, sourced scope completeness → may resolve FALSE
frontendPresent = FALSE  without that declaration               → UNRESOLVED
```

## Scope consistency

The signal and the evaluation of this rule must be computed for the **same** orchestration scope.
Project-wide evidence sustaining the applicability of a single work unit is defensible or not
depending on the case, and whoever declares it is the one who knows — but it cannot be invisible.

```text
either scope undeclared                     → APPLICABILITY_UNRESOLVED
different scopes, no declared relation       → APPLICABILITY_UNRESOLVED
different scopes, relation declared + cited  → evaluated, and the relation is reported
```

## Statement

When applicable, the frontend must not treat arbitrary free-text address data as a validated and
normalized address. Address search or entry must be resolved through the GCBA cadastral option
**before the application treats the value as normalized for the governed flow**.

## Calling the service is not the requirement

The requirement is the whole chain, end to end:

```text
raw user input  →  provider request  →  provider response  →  normalized result
                                                            →  value the application CONSUMES
```

🔴 **A provider call followed by persistence or use of the original raw value does not satisfy D5.**
This is the defect the rule exists to catch, and it is the one that hides best: the call is the
visible part, and a control that verifies the call goes green on an application that does not comply.

## Every material path matters

```text
SEARCH           address search
MANUAL_ENTRY     manual address entry, free text
SELECTION        selecting a suggested address
EDIT_UPDATE      editing or reloading a stored address for modification
ALTERNATE_INPUT  any alternate or fallback input path
```

**A compliant search path does not compensate for an unvalidated manual-entry bypass.** The coverage
inventory declares, for each of the five kinds, either its flows or an absence with its source. A
kind left silent leaves `ADDRESS_FLOW_COVERAGE_UNRESOLVED`: the search path with autocomplete is the
one somebody builds well and the one somebody enumerates, and manual entry and the edit flow are the
ones nobody mentions.

A flow the project declares inactive requires a source from the coverage-source list, is reported in
the output, and cannot empty the governed set: if the signal says an address flow exists in scope and
every declared flow is inactive, that contradicts the signal and the result is unresolved. **What is
not declared is verified.**

## The provider is declared, never guessed

This policy does not invent the technical contract of the cadastral mechanism. **No endpoint, no
request field, no response field, no cadastral identifier, no coordinate field, no authentication
method, no timeout or retry value and no environment URL is attributed to this rule.** None of them
is in any normative extract this harness holds, and writing one here would read as though the
standard required it.

The provider identity is an input, and it carries where it came from:

```yaml
cadastralProvider:
  id: <declared by the project>
  source: GCBA_NORMATIVE | GCBA_CATALOG_ENTRY | ASI_INTEGRATION_CONTRACT |
          PROJECT_INTEGRATION_AGREEMENT | HUMAN_CONFIRMATION
  reference: <where it says so>
```

🔴 **Quoting a name is not holding a contract.** The standard names a catalog service on page 19 and
names the cadastral option on page 13; it does not state that the two are the same mechanism, and it
gives neither of them an endpoint, a field or an authentication method. A project that identifies its
integration by citing that paragraph has a defensible `GCBA_NORMATIVE` source — and the harness still
does not know what using it looks like.

Two separate gaps, because they are answered by different people:

```text
CADASTRAL_PROVIDER_UNRESOLVED   which integration is the cadastral option here
INTEGRATION_CONTRACT_MISSING    it is identified, and how using it looks is not
```

Provider identity is never inferred from a generic URL, a package name or the presence of
autocomplete.

## What never proves compliance on its own

```text
an autocomplete UI exists
an address API is called
coordinates are returned
a regex validates the string
a postal-code library is installed
a free-text field has frontend validation
somebody says the address is normalized
```

These may be supporting evidence. What answers the question is a run: the frontend flow, tied to its
build and environment, showing the provider interaction and which value the application ended up
using.

## Evidence it requires

```yaml
application: {id, environment}
build: {id, runtime}
scope: {id, kind, reference}
testTarget: {available}
cadastralProvider: {id, source, reference}
integrationContract: {id, source, reference}
addressFlows: {source, paths: []}   # one entry per path kind, with flows or a sourced absence
results: []                         # one per flow, with its chain and its consumed value
evidence: []                        # tied to the build and runtime that were tested, with its mode
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
ADDRESS_FLOW_COVERAGE_UNRESOLVED
CADASTRAL_PROVIDER_UNRESOLVED
INTEGRATION_CONTRACT_MISSING
```

Unresolved and partial states are never collapsed into compliant.

## Boundaries

```text
D5   → whether frontend addresses are validated and normalized with the cadastral option
D6   → whether the georeferenced visualization uses the GCBA Map
P5   → whether validation is duplicated in frontend and backend
G1   → whether the integration technology in use is homologated and on an approved version
```

A normalized address does not satisfy D6: coordinates coming out of a cadastral response say nothing
about which map draws them. And this rule does not satisfy P5: it looks at the frontend chain and
reports nothing about backend validation. P5's dual-layer requirement is not duplicated here.

## One compliant path does not cover another

A `NON_COMPLIANT` on any governed flow outranks any number of flows that comply. The common shape of
this defect is exactly the mixed one: a correct search path with autocomplete, and a free-text manual
entry or an edit screen that writes the raw value through.

## Verified by

`address-normalization-integration`

## Owners

`dev-integration`, with `dev-frontend` on the input side, as the normative matrix assigns. This
policy creates no skill and selects none: the responsible agent chooses skills through the registry
according to the actual integration and frontend work required.
