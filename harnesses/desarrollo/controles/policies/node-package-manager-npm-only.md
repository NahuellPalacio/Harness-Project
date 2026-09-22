---
id: node-package-manager-npm-only
type: POLICY
rule: P1
---

# Policy: node-package-manager-npm-only

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: P1
derivedClause: P1.node
```

> *"En desarrollos que utilicen tecnologías basadas en Node.js (como Angular, React o NestJS), se
> establece que el administrador de paquetes permitido es NPM (Node Package Manager). No está
> permitido el uso de YARN u otras alternativas, a fin de garantizar la compatibilidad y
> trazabilidad de dependencias en los entornos de GCABA."*

## Applicability within P1

P1 is `ALWAYS`. This policy carries a technology branch of that rule:

```text
a Node.js-based application surface exists   → the clause is evaluated
no Node.js-based application surface exists  → the clause is NOT_RELEVANT
```

🔴 **`NOT_RELEVANT` is not `NOT_APPLICABLE`, and the difference is the whole point.** A project
without Node still owes homologated frameworks: what has no subject is this clause, not the rule. No
applicability signal is created for it — Node relevance comes from the technology inventory that
already exists.

If the technology context is incomplete, relevance cannot be established:
`NODE_TECHNOLOGY_CONTEXT_UNRESOLVED`.

## Statement

For Node.js-based development, installing, administering and running dependencies must use the
package manager the standard names as permitted.

## Compared against the permitted one, not against a list of forbidden ones

The standard names one and says the alternatives are not allowed. So the comparison is against the
permitted one, and **every** active manager that is not it is an alternative — the one that shipped
last month included.

🔴 No artifact of this rule carries a list of forbidden package managers. A list of forbidden things
ages, and the fourth one arrives saying *mine is not on the list*.

## The evidence is about the governed path, not about the files lying around

Useful evidence:

```text
the repository manifest
lockfiles
package-manager metadata in the manifest
install, build and run commands in the pipeline
container build definitions
build scripts
build documentation
```

A lockfile that a migration left behind and the lockfile the build uses every day look identical
from outside, and confusing them breaks the rule in both directions: it fails a correct project, or
it approves one that installs with something else in the pipeline.

## Historical artefacts are investigated, not ignored and not failed

```text
active, and it is the permitted one         complies
active, and it is not                       non-compliant
historical, with its investigation cited    an observation. It does not fail and does not vanish
historical and uninvestigated               the question stayed open; it does not pass
activity not declared                       NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED
two different active managers               NODE_PACKAGE_MANAGER_CONFLICT
```

🔴 **What does not declare whether it is active is not assumed dead.** Taking a lockfile for dead
because nobody said otherwise is this clause's defect on the approving side.

## No version requirement is invented

The standard says which package manager is permitted and fixes no version for it. Node's own version
homologation is G1's, and no artifact of this rule carries a version number.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_RELEVANT
NODE_TECHNOLOGY_CONTEXT_UNRESOLVED
NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED
NODE_PACKAGE_MANAGER_CONFLICT
```

🔴 No unresolved outcome ever becomes `SATISFIED`.

## Remediation boundary

This policy creates, modifies and renames no agent and no skill. The normative owners are the agents
the matrix declares.
