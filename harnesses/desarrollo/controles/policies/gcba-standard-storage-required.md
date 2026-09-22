---
id: gcba-standard-storage-required
type: POLICY
rule: D7
---

# Policy: gcba-standard-storage-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D7
  supportingSections: ["8.4 Sistema de Archivos"]
```

The rule is one sentence with three obligations inside it: *"Si la aplicación gestiona archivos
(PDF, DOC, PNG, JPG, etc.) debe almacenarlos en el storage estándar del GCABA. No está permitido
guardar en forma permanente archivos en forma local. Para los casos temporales la destrucción de los
mismos debe ser en forma inmediata."* This policy carries the **first** one.

The supporting material is the *Archivos adjuntos* paragraph, page 19: *"Todo documento adjunto que
necesite guardar una aplicación debe resguardarse en el repositorio estándar para tal fin del
GCABA... La tecnología actual está basada en el protocolo S3 (Simple Storage Service)."*

🔴 **That sentence names a technology and does not name a repository.** It says *the standard
repository for that purpose of the GCBA* and stops there. The other two obligations live in
`persistent-local-file-storage-prohibited` and
`temporary-file-immediate-destruction-required`, and neither answers for this one.

## Applicability

```text
fileHandlingPresent = TRUE        → applies
fileHandlingPresent = FALSE       → NOT_APPLICABLE
fileHandlingPresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Applicability is resolved from an evidence-backed signal before this policy runs. Missing evidence
is never `FALSE`. Not finding a `.pdf` literal, not finding an upload component, and not finding a
filesystem call in one file are not evidence that the scope handles no files: file behaviour hides
behind libraries, framework abstractions, shared services, storage adapters and generated artifacts.

🔴 A file flow is more than an upload. Receiving, uploading, downloading, generating, transforming,
staging, storing, serving, importing, exporting and temporary processing all count.

## Statement

When applicable, every governed file whose lifecycle intentionally extends beyond the bounded
operation that created or received it must be stored through the GCBA standard storage mechanism.

A file that only exists to complete a bounded operation is **not** governed by this policy. It is
governed by `temporary-file-immediate-destruction-required`, and the distinction is the lifecycle,
never the location.

## The repository is declared, the protocol is quoted, and no provider is named

This policy does not name the mechanism of the GCBA standard storage, and neither does the check
that verifies it. **No network locator, no infrastructure name, no credential, no geographic
identifier, no tenant, no object prefix and no retention rule is attributed to this rule.** None of
them is in any normative extract this harness holds, and writing one here would read as though the
standard required it.

The identity is an input, and it carries where it came from:

```yaml
standardStorage:
  id: <what the project declares>
  source: GCBA_NORMATIVE | GCBA_CATALOG_ENTRY | ASI_INTEGRATION_CONTRACT |
          PROJECT_INTEGRATION_AGREEMENT | HUMAN_CONFIRMATION
  reference: <where it says so>
  protocol: S3
```

The list says **which sources are defensible**; it does not say which repository is the standard
one. Without an id, without a source from the list, or without a reference, the outcome is
`STANDARD_STORAGE_PROVIDER_UNRESOLVED`.

🔴 **The protocol is not the provider.** `protocol: S3` is what the standard says, and it is
evidence about the technology: speaking that protocol does not identify a repository, the same way
speaking HTTP does not identify a site. Reading it as a specific public-cloud vendor contract is
inventing the half that is missing — and no vendor name appears in any artifact of this rule, as an
identity or as a counterexample.

And identity alone is not enough. The **integration contract** — how one recognizes that a
persistence path uses that mechanism — is a second input, and without it the outcome is
`STORAGE_INTEGRATION_CONTRACT_MISSING`.

> 🔴 Two states and not one, because they are two different holes. *I do not know which repository
> it is* and *I know which one and I do not know what using it looks like* get fixed by asking
> different people.

## Not Sufficient

None of the following, alone, proves compliance:

```text
a library for the protocol exists in the manifest
an object-storage dependency is declared
an environment variable is named after the protocol
something shaped like an object store is configured
a file upload returns success
a remote call leaves the application
the application does not write under a directory it owns
```

Every one of those is evidence of what is **installed** or what is **configured**, not of where a
file ended up. Compliance requires evidence that the governed persistent path actually writes and
reads through the identified standard mechanism.

## No persistent flow, no obligation

If the complete flow classification finds no persistent file flow, this policy has no subject and
the outcome is `NOT_APPLICABLE` — not `SATISFIED`. Reporting compliance would assert that persistent
files go to standard storage about an application that persists none.

🔴 And the identity is **not** demanded in that case. An application that only handles temporary
files does not need a standard storage contract, and asking it for one would make the rule require
configuration that the standard does not require of it.

## §8.4 structural guidance

Page 19 and page 20 also give structure guidance for the standard repository: plan the structure
before storing, avoid structures that concentrate traffic in a single folder, *"intentar equilibrar
el ancho y la profundidad de la estructura de la carpeta"*, *"no crear estructuras de carpetas que
tengan más de 20 niveles de profundidad"*, and *"evitar colocar una gran cantidad de objetos (más de
100.000) en una sola carpeta"*.

These are collected as supporting evidence of this policy's check. They do **not** become a fourth
control, and what cannot be measured stays `NOT_MEASURED`: fabricating an object count or a depth is
worse than not having one, because an invented number reads exactly like a measured one.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
EVIDENCE_INCOMPLETE
STANDARD_STORAGE_PROVIDER_UNRESOLVED
STORAGE_INTEGRATION_CONTRACT_MISSING
```

🔴 None of the unresolved outcomes ever becomes `SATISFIED`. An unresolved state is a question
somebody has to answer, and turning it into compliance is how a rule stops being checked.

## Remediation boundary

The normative owner of the rule is the agent the matrix declares. Selecting the skill that knows how
to integrate the standard storage is the Agent Registry's job, not this policy's: the normative
obligation and the technical procedure stay separate, and this policy creates no agent and no skill.
