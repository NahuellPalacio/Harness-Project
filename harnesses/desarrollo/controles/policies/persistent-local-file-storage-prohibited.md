---
id: persistent-local-file-storage-prohibited
type: POLICY
rule: D7
---

# Policy: persistent-local-file-storage-prohibited

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D7
```

The second of the three obligations D7 carries: *"No está permitido guardar en forma permanente
archivos en forma local."*

The word that decides is **permanente**. This is a prohibition on a storage **role**, not on a
location: a local file is not forbidden, a local file used as the application's file repository is.

## Applicability

```text
fileHandlingPresent = TRUE        → applies
fileHandlingPresent = FALSE       → NOT_APPLICABLE
fileHandlingPresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Missing evidence is never `FALSE`, and a file flow is more than an upload.

## Statement

When applicable, no governed file may remain permanently in application-local storage.

Evidence requiring review includes:

```text
application filesystem directories
container filesystem paths
local server directories
framework local-disk storage adapters
files written under application runtime paths
persistent mounted paths used as the application file repository
```

🔴 **A mounted volume is not an exception.** Mounting storage into the application and using it as
the permanent repository is the prohibited arrangement with a different letter on the path. What
decides is the role the storage plays, not how it got attached.

## The path name decides nothing

```text
a directory called tmp does not prove a temporary lifecycle
running in a container does not prove the file goes away
an operating-system temp location does not prove anybody deletes anything
```

All three are assumptions shaped like evidence, and all three are declared inert. A local write
whose only evidence is one of them is `LOCAL_STORAGE_LIFECYCLE_UNRESOLVED` — **not** temporary.

## Seven facts, not one

For every material local write the following are established:

```text
pathOrAdapter        where it is written, or through which adapter
purpose              what the write is for
creation             where the file is created
consumption          where it is read
cleanup              where it is removed
expectedLifetime     how long it is expected to live
persistenceBehavior  PERSISTENT | TEMPORARY | UNRESOLVED
```

If any of the seven is missing, the lifecycle is not established and the outcome is
`LOCAL_STORAGE_LIFECYCLE_UNRESOLVED`. *"It is temporary"* with no declared consumption and no
declared cleanup is an assertion, not a lifecycle.

## Boundary with the temporary obligation

```text
temporary local   → allowed, and governed by temporary-file-immediate-destruction-required
persistent local  → prohibited by this policy
```

The two never answer for each other. A temporary local file with an established lifecycle does not
violate this policy **because it is local**; whether it is actually destroyed is the other policy's
question, and this one defers it there explicitly.

## A prohibition with no subject is satisfied

If there are no material local writes in scope, over a complete flow classification, this policy is
`SATISFIED`. That is the asymmetry with the other two obligations of D7: those are conditional
requirements and go `NOT_APPLICABLE` when their subject is missing; this one is a prohibition, and
not doing the prohibited thing is complying with it.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
LOCAL_STORAGE_LIFECYCLE_UNRESOLVED
EVIDENCE_INCOMPLETE
```

🔴 An unresolved lifecycle never becomes `SATISFIED`. Not knowing whether a write is permanent is a
question, and answering it in the convenient direction is how a permanent local repository stays
invisible.

## Remediation boundary

This policy creates no agent and no skill. The normative owner is the agent the matrix declares, and
which installed skill performs the work is resolved by the Agent Registry.
