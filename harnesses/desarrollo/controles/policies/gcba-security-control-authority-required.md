---
id: gcba-security-control-authority-required
type: POLICY
rule: O2
---

# Policy: gcba-security-control-authority-required

## Normative Source

```yaml
source:
  standard: ES0902
  version: "6.2"
  section: "3"
  rule: O2
  ruleKey: ES0902.O2
```

> *"El control de la seguridad informática debe estar a cargo de un organismo perteneciente al
> GCABA."*

## Applicability

`ALWAYS`. Zero applicability signals. No governed scope is exempt from having somebody answer for
its security control.

## Requirement

For the governed project or scope, the controlling security organization must:

```text
exist
be identified
belong to GCABA
own the security-control responsibility
have evidence valid for the assessed scope and time
```

Execution may be delegated. **Control authority may not.** An external or non-GCABA actor may scan,
review, remediate or prepare evidence; it cannot become the authority by doing so.

## Authority is not execution

```text
CONTROL AUTHORITY   answers for security control over the scope
EXECUTION           scans, reviews, remediates, prepares evidence
```

The evidence record has no field for an executor and will not get one. That is not an omission: it
is what makes *"whoever executes cannot become whoever answers"* a property of the file's shape
rather than a habit somebody has to remember.

## Non-sufficient evidence

None of these establishes the authority, alone or together:

```text
dev-security is assigned to the row
a scanner ran
a vendor security team is named
a README says "Security: DGSEI"
an email address ends in a GCBA-looking domain
a repository lives in a GCBA namespace
a developer claims the authority
the organization's own name
```

GCABA membership is supported by authoritative organizational or project evidence, or it stays
unresolved. It is never inferred.

## Multiple authorities

Several GCABA organizations may hold scoped responsibilities — application security control to one,
infrastructure security control to another. That is acceptable when the scopes are explicit.

Two records that claim incompatible authority over the same scope, both current, with responsibilities
that overlap, stay unresolved until authoritative precedence or current assignment is established.

## The registry is the project's

`reglas/security-control-authority.json` ships **empty**. Who controls the security of a project is
the project's datum; a harness that arrives with an answer in it is a harness that answered for the
project. Empty resolves `SECURITY_CONTROL_AUTHORITY_UNRESOLVED`, which is neither a pass nor a fail.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
SECURITY_CONTROL_AUTHORITY_UNRESOLVED
GCABA_MEMBERSHIP_UNRESOLVED
SECURITY_AUTHORITY_SCOPE_UNRESOLVED
SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED
SECURITY_AUTHORITY_EVIDENCE_EXPIRED
CONFLICTING_SECURITY_AUTHORITY_EVIDENCE
AUTHORITY_EVIDENCE_INSUFFICIENT
```

Missing evidence is never `NON_COMPLIANT`. `NON_COMPLIANT` has one path: it is established that the
controlling authority is non-GCABA and no GCABA organization controls that scope. Accusing an
organization of something nobody proved is the failure mode this asymmetry exists to stop.

## Boundary

`SATISFIED` means the organizational-authority requirement of O2 is evidenced. It does not mean the
security assessment was approved, that C2 passed, that vulnerabilities were accepted, or that DGSEI
approval was obtained. Official approval remains external evidence and its own control.

## Verified by

`security-control-authority-evidence`.

## Owner

`dev-security`.
