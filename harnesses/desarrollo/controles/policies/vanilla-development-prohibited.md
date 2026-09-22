---
id: vanilla-development-prohibited
type: POLICY
rule: P1
---

# Policy: vanilla-development-prohibited

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: P1
```

> *"No se permite el uso del lenguaje puro ('vanilla') sin el soporte de su respectivo framework.
> Las bibliotecas o componentes de bajo nivel podrán utilizarse únicamente cuando estén integrados
> de forma indirecta a través del framework correspondiente (por ejemplo, conectores de base de
> datos usados por un ORM)."*

## Applicability

P1 is `ALWAYS`, with no applicability signal. This policy evaluates every material delivered
application surface.

## Statement

Material application runtime behaviour must not be implemented as standalone pure-language
development where P1 requires framework-based development.

Cases that require evaluation:

```text
a raw-language server implementation answering delivered traffic
persistence written directly against the driver, outside the framework's architecture
delivered modules executed outside the declared framework's application model
a framework declared in the manifest that does not govern the surface
```

## Declaring a framework is not using one

The most common shape of this defect is not a project without a framework. It is a project **with**
one: the package installed, one managed module, a README that names it, and a hand-written runtime
serving half the traffic next to it.

So the framework being present proves nothing here either. What is verified is that the governed
surface executes through the framework's structured application model, and the evidence that proves
it is a trace of that execution. A trace that reports the runtime bypassing the framework decides
against whatever the surface declares.

## The low-level clause, which is a third thing

The standard is precise: low-level libraries and components are allowed **when integrated
indirectly, through the corresponding framework**. So each declared low-level component states how it
is used:

```text
THROUGH_FRAMEWORK   behind the architecture the framework manages  → may comply
DIRECT_REPLACEMENT  used directly in place of the framework path   → non-compliant
UNRESOLVED          how it is used was not established             → not resolved
```

🔴 **This is not inferred from the package name.** A database connector behind an approved ORM and
the same connector used as the application's persistence architecture are the same package and two
different things. Which one it is comes from evidence about the architecture, like everything else
here.

## The auxiliary-tooling boundary, in both directions

A pure-language script that is only auxiliary tooling is not a P1 violation:

```text
build scripts
CI helpers
one-off repository maintenance utilities
code generators
migration launchers
test harness scripts
```

🔴 But the boundary cuts both ways, and the dangerous direction is the other one: a script that takes
part in the delivered business runtime **is** an application surface, whatever its folder is called,
and it is evaluated. The classification is declared with the inventory's source behind it; where it
cannot be established the outcome is `DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED`, not an
assumption in either direction.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
VANILLA_RUNTIME_PATH_DETECTED
LOW_LEVEL_DIRECT_USE_BYPASS
DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED
EVIDENCE_INCOMPLETE
```

The two middle ones say **why** a surface fails; they are not a different result from failing, and a
surface carrying both is not in two states.

🔴 No unresolved outcome ever becomes `SATISFIED`.

## Remediation boundary

This policy creates, modifies and renames no agent and no skill. The normative owners are the agents
the matrix declares.
