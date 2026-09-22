---
id: temporary-file-immediate-destruction-required
type: POLICY
rule: D7
---

# Policy: temporary-file-immediate-destruction-required

## Normative Source

```yaml
source:
  standard: ES0901
  version: "6.3"
  section: "7.1"
  rule: D7
```

The third of the three obligations D7 carries: *"Para los casos temporales la destrucción de los
mismos debe ser en forma inmediata."*

## Applicability

```text
fileHandlingPresent = TRUE        → applies
fileHandlingPresent = FALSE       → NOT_APPLICABLE
fileHandlingPresent = UNRESOLVED  → APPLICABILITY_UNRESOLVED
```

Missing evidence is never `FALSE`, and a file flow is more than an upload.

## Statement

When applicable, every temporary file must be destroyed as part of the same bounded lifecycle that
created it.

A temporary file is one created only to complete a bounded operation — conversion, parsing, upload
staging, report generation, compression, scanning, transfer. Local temporary storage is allowed
**only** when the destruction is tied to the completion of that purpose.

## "Immediate" is a moment, not a number

```text
create or stage the temporary file
→ use it for the bounded operation
→ the operation finishes or fails
→ cleanup runs as part of that same lifecycle
```

🔴 **No numeric duration is invented by this policy, and none appears in any artifact of this
rule.** The requirement is tied to lifecycle completion, not to a made-up count of seconds, minutes
or hours. The standard gives a moment and no threshold; an invented threshold reads exactly as
authoritative as a quoted one, and it would let an implementation comply with the number while
missing the point.

If a separate authoritative project contract defines such a value, that value belongs to that
contract. It does not come from here.

## Success and failure paths

Cleanup evidence must account for every material path out of the bounded operation:

```text
NORMAL_COMPLETION   always
VALIDATION_FAILURE  always
PROVIDER_FAILURE    always — the exception path
CANCELLATION        when the project declares the runtime allows cleanup
```

🔴 **Happy-path-only cleanup is insufficient.** It is the most common shape of the defect: the
delete sits after the last successful step, and every ordinary failure before it leaves the file
behind. A path the runtime genuinely cannot reach is not demanded — but it is not assumed covered
either, and an undeclared material path leaves `CLEANUP_PATH_COVERAGE_UNRESOLVED`.

## What does not substitute for the lifecycle binding

```text
PERIODIC   a daily or hourly cleanup job
STARTUP    cleaning on boot
RESTART    relying on the container being replaced
TTL        an unspecified expiry
MANUAL     a procedure somebody runs
NONE       nothing
```

Alongside a lifecycle-bound cleanup they are defence in depth and they do not hurt. As the **only**
cleanup of a material path they are non-compliant: none of them destroys the file when its purpose
ends, which is what the sentence requires.

A directory named after temporary storage, and the assumption that the operating system or the
runtime will take care of it, are not cleanup at all.

## The technique is not prescribed

```text
finally
defer
using / dispose
context manager
try/finally cleanup
a temporary-file primitive with deterministic removal
```

These are **examples**, per language and framework, and the check does not branch on any of them.
What is required is the structural binding and the evidence of it; which construct expresses that
binding is the implementation's choice, and the declared technique is recorded without changing the
outcome.

## No temporary flow, no obligation

If the complete flow classification finds no temporary file flow, this policy has no subject and the
outcome is `NOT_APPLICABLE`. Over an **incomplete** classification it is not: turning *"we did not
enumerate the flows"* into *"there are no temporary files"* is the substitution this state exists to
prevent.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
TEMPORARY_FILE_LIFECYCLE_UNRESOLVED
CLEANUP_PATH_COVERAGE_UNRESOLVED
EVIDENCE_INCOMPLETE
```

🔴 No unresolved outcome ever becomes `SATISFIED`.

## Remediation boundary

This policy creates no agent and no skill. The normative owner is the agent the matrix declares, and
which installed skill performs the work is resolved by the Agent Registry.
