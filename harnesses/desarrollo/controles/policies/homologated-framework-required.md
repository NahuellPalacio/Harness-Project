---
id: homologated-framework-required
type: POLICY
rule: P1
---

# Policy: homologated-framework-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: P1
derivedClauses:
  - P1.plataformas
```

> *"Todo desarrollo debe realizarse utilizando frameworks homologados en este documento."*

And the clause that opens the second path, `P1.plataformas`: *"Para ERP, CRM, FSM, etc., su uso está
habilitado bajo los lineamientos propios de cada plataforma, siempre que no contradigan los
principios contenidos en este documento."*

## Applicability

P1 is `ALWAYS`. It has **no** applicability signal, and none is added: the technology branches of
this rule are internal evaluation branches, not new normative rules.

🔴 This policy therefore never returns `NOT_APPLICABLE`. Every material delivered
application-development surface is evaluated, always.

## Statement

Every material delivered application surface must be covered by one of two paths:

```text
a homologated framework that actually governs the surface
or
a structured business platform, evidenced as governed
```

Anything else is non-compliant.

## The boundary with G1, which is not negotiable

```text
G1 owns   whether a technology is approved, and whether its version is homologated
P1 owns   whether the delivered application is actually built through a framework
```

This policy **reuses** the authoritative Annex II catalog — the same file G1 reads, never a copy —
and **consumes** the verdict G1 produced for the technology, cited. It does not compare versions, it
does not tolerate deprecation, and it does not count standards backwards. That logic exists, is
verified, and having a second answer to the same question is worse than having none.

```text
no cited G1 verdict for the technology     → G1_EVIDENCE_REQUIRED
a verdict that is not the homologated one  → that state is preserved, and it does not pass
```

No artifact of this rule carries a technology list or a version number.

## The framework must govern, not merely exist

```text
framework identity, declared
+
the G1 verdict for that technology, cited
+
evidence that the surface executes through the framework's structured application model
```

The third one is the one that is almost never there, and it is the whole point. These do not prove
it by themselves:

```text
the package exists in the manifest
a dependency entry names it
one framework-managed module exists
the project documentation says the project uses it
an agent states that it does
```

If framework identity cannot be established: `FRAMEWORK_CONTEXT_UNRESOLVED`.

## The business-platform path

A platform surface satisfies this policy when **all four** are evidenced:

```text
a structured development environment provided by the platform
authoritative platform development guidelines, with their source and reference
customization happens inside that governed environment
no declared contradiction with ES0901
```

🔴 **The product name alone establishes nothing.** Naming a platform is not evidence that it
provides a normed development environment, and it is not evidence that the customization stayed
inside it.

```text
any of the first three missing        → BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED
a guideline that contradicts ES0901   → BUSINESS_PLATFORM_STANDARD_CONFLICT
```

## It is a path, not an exemption

A project may hold a platform customization **and** custom services of its own. Each surface is
evaluated independently, and the platform path exempts none of the others. *"We use a platform"* is
not an answer about the three services next to it.

## Surfaces are what gets delivered, and they are declared

```text
FRAMEWORK_GOVERNED          a homologated framework governs it
BUSINESS_PLATFORM_GOVERNED  a structured platform governs it, with evidence
AUXILIARY_TOOLING           tooling: not a delivered application surface
VANILLA_APPLICATION         pure language without the framework it owes
UNRESOLVED                  could not be established
```

🔴 `AUXILIARY_TOOLING` is **declared, never inferred**, exactly as G1 declares toolchain auxiliaries.
Inferring it is the cheapest way to shed any uncomfortable surface. And the reverse holds: a script
that takes part in the delivered runtime is an application surface whatever it is called.

If the inventory has no source, has unidentified surfaces, carries an unresolved class or declares
itself incomplete: `DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED`, and never compliance.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
FRAMEWORK_CONTEXT_UNRESOLVED
BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED
BUSINESS_PLATFORM_STANDARD_CONFLICT
DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED
G1_EVIDENCE_REQUIRED
```

🔴 No unresolved outcome ever becomes `SATISFIED`.

## Remediation boundary

The normative owners are the agents the matrix declares, and which installed skill performs the work
is resolved by the Agent Registry. This policy creates, modifies and renames no agent and no skill.
