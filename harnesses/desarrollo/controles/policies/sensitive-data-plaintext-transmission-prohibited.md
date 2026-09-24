---
id: sensitive-data-plaintext-transmission-prohibited
type: POLICY
rule: Vu2
---

# Policy: sensitive-data-plaintext-transmission-prohibited

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu2
```

## Requirement

Sensitive data must not be transmitted in plaintext over any applicable material transmission path.

## Classification Boundary

This Policy does not invent what counts as sensitive.

Unknown classification:

`SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED`

## Prohibited False Equivalences

The following do not constitute encryption:

```text
Base64
URL encoding
hex
compression
serialization
signing-only JWT
obfuscation
```

## Transport Boundary

Evaluate all relevant hops.

A path such as:

```text
HTTPS edge -> plaintext internal hop
```

cannot be considered fully protected solely because the public edge uses TLS.

## Cryptographic Detail Boundary

Do not invent from Vu2:

```text
TLS minimum version
cipher suites
certificate algorithm
key size
mTLS requirement
certificate rotation period
```

Apply those only when another authoritative source provides them.

## Evidence Handling

No plaintext sensitive value may be copied into Harness findings, logs, reports, or Block 4 accounting.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
APPLICABILITY_UNRESOLVED
SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED
TRANSMISSION_PATH_COVERAGE_UNRESOLVED
TRANSPORT_PROTECTION_UNRESOLVED
PLAINTEXT_SENSITIVE_TRANSMISSION_DETECTED
SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
