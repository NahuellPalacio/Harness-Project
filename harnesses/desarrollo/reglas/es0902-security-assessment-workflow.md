# ES0902 Security Assessment Workflow

## Source Boundary

ES0902 §4 establishes two security-control activities:

```text
1. automated system
2. internal DGSEI circuit
```

The Harness must not impersonate the DGSEI circuit.

## Harness Flow

```text
Task / Release Candidate
  ↓
Internal Security Assessment
  ↓
Automated evidence / findings
  ↓
Remediation
  ↓
Deliverable Package Resolver (§5)
  ↓
READY_TO_REQUEST
  ↓
Official GCBA / DGSEI assessment
  ↓
official findings / status
  ↓
if findings:
  remediation
  → READY_TO_RESUBMIT
  → official resubmission
```

## Authority

Harness-owned states:

```text
NOT_STARTED
INTERNAL_ASSESSMENT
READY_TO_REQUEST
FINDINGS_RECEIVED
REMEDIATION
READY_TO_RESUBMIT
```

External-evidence states:

```text
REQUESTED
IN_ASSESSMENT
RESUBMITTED
APPROVED
REJECTED
```

`APPROVED` requires official evidence.

## C2

If security homologation is required, official security approval must be evidenced in QA.

```text
environment != QA
→ cannot satisfy C2 approval requirement

environment = QA
+ official approval evidence
→ C2 may PASS
```

Internal Harness review in QA is still not official approval.

## G2

With authoritative severity mapping only:

```text
no finding above LOW
AND
LOW count <= 10
→ G2_THRESHOLD_SATISFIED
```

This does not set `APPROVED`.

Unknown mapping:

`VULNERABILITY_RISK_MAPPING_UNRESOLVED`

## G3

On resubmission:

```text
100% of previously reported vulnerabilities
→ must be rechecked

G2 threshold
→ still applies
```

Preserve previous finding IDs and retest evidence.

## G4

For an application with a previous vulnerability report:

```text
new assessment
→ full-scope assessment

not:
→ previous findings only
```

New findings may appear and are included.

## Deliverable Readiness

`READY_TO_REQUEST` requires all applicable E1-E5 deliverables and WAF requirements to be resolved.

Missing external templates/data remain explicit gaps.

## Recommended Package

```text
security-assessment/
├── manifest.json
├── normative-results.json
├── vulnerability-findings.json
├── deliverables/
├── architecture/
├── waf/
└── assessment-status.json
```

Do not persist credentials or secrets in this package.
