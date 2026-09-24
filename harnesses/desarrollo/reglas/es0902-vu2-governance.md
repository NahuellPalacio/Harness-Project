# ES0902 Vu2 Governance Package

## Purpose

Operationalize ES0902 v6.2 §6, rule Vu2:

```text
Vu2 — Todo dato sensible no puede ser enviado en texto plano.
```

Vu2 is a confidentiality-in-transit rule.

It governs transmission of data classified as sensitive. It does not, by itself, define the organization's sensitive-data taxonomy, encryption-at-rest rules, retention rules, or masking rules.

## Matrix Binding

The installed ES0902 matrix declares:

```yaml
ruleKey: ES0902.Vu2
category: SECURITY_PRINCIPLE

applicability:
  mode: CONDITIONAL
  signals:
    - sensitiveDataTransmissionPresent

primaryAgents:
  - dev-security

policies:
  - sensitive-data-plaintext-transmission-prohibited

checks:
  - sensitive-data-transport-protection

reviews: []
```

Do not rename these identifiers.

## Applicability

`sensitiveDataTransmissionPresent` is evidence-backed.

```text
TRUE
→ at least one material transmission path carries data authoritatively classified as sensitive

FALSE
→ authoritative data-flow/classification evidence establishes no sensitive data is transmitted in scope

UNRESOLVED
→ data is transmitted but sensitivity classification and/or transmission coverage cannot be established
```

Do not infer FALSE because no field is named `password`, `token`, `dni`, or `secret`.

Do not infer TRUE only from a field name. Sensitivity comes from authoritative classification/context.

## Sensitive-Data Classification

ES0902 Vu2 does not define a complete taxonomy of sensitive data.

The Harness must not invent one.

Preferred evidence sources:

```text
authoritative GCBA/ASI data-classification policy
project security/privacy requirements
official architecture/data documentation
approved assessment findings
contractual classification approved for the project
other authoritative project security evidence
```

If data may be sensitive but authoritative classification is unavailable:

`SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED`

This state prevents a false PASS.

## Transmission Scope

Vu2 applies to material transmission paths carrying sensitive data.

Inventory at least where present:

```text
browser/mobile client -> application
application -> application/service
application -> external provider
service -> message broker/queue
application -> email/message delivery provider
application -> file-transfer endpoint
application -> database over network
application -> cache over network
CI/CD or automation -> external/internal service
telemetry/log exporter -> collector
webhook -> destination
```

The list is operational, not a new normative taxonomy.

If a path carries sensitive data, every network/service hop that transports the data must be evaluated.

## Hop-by-Hop Doctrine

A secure outer edge does not automatically protect an internal plaintext hop.

Example:

```text
client --HTTPS--> reverse proxy --HTTP--> backend
```

If sensitive data crosses the proxy-to-backend hop in plaintext, Vu2 cannot PASS for that path unless authoritative architecture evidence establishes that the hop is not a material transmission boundary governed by the rule.

Do not assume TLS termination at an ingress is sufficient for every downstream hop.

## Plaintext Meaning

Vu2 prohibits sensitive data being sent in plaintext.

The following are not encryption:

```text
Base64
URL encoding
hex encoding
compression
serialization
JWT signing without encryption
obfuscation
```

They must not be treated as transport confidentiality.

Hashing is not transport encryption. A one-way transformed value may no longer expose the original data, but the Harness must evaluate the actual transmitted value and project classification rather than call hashing "encryption".

## Transport Protection

Evidence may include secure transport or an equivalent confidentiality mechanism supported by authoritative architecture/security evidence.

Examples may include:

```text
TLS-protected HTTP
TLS-protected database/service connection
secure message transport
secure file-transfer protocol
application-level encryption over a transport
```

These are examples, not a source-defined whitelist.

Do not invent required TLS versions, cipher suites, certificate algorithms, key sizes, or mutual-TLS requirements from Vu2 alone.

If another authoritative standard/policy defines them, apply that source separately.

## HTTPS Is Evidence, Not Always Proof

`https://` is useful evidence but not sufficient in all cases.

Check, where technically applicable and evidence exists:

```text
transport actually negotiates confidentiality
certificate validation is not disabled
hostname verification is not disabled
redirect/downgrade does not expose sensitive payload
proxy/service downstream hops are covered
runtime configuration matches reviewed configuration
```

Do not invent runtime facts from source code only.

## Test Safety

Never send real sensitive data merely to test Vu2.

Prefer:

```text
configuration inspection
deployment/runtime transport configuration
connection metadata
safe synthetic test data
packet/trace metadata without sensitive payload capture
```

Do not persist raw sensitive payloads in Harness evidence.

If packet capture or proxy inspection is required, use redacted/synthetic data and approved environments.

Unsafe validation:

`SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE`

## Secrets in Evidence

Evidence must not reproduce full:

```text
passwords
tokens
private keys
connection credentials
personal/sensitive payloads
```

Use references, redaction, fingerprints, field names, path metadata, and transport metadata.

## Relationship with Other Rules

```text
Vu2
→ sensitive data confidentiality in transit

Vu7
→ base software configured not to disclose private data

D8
→ token protection for services

C1
→ authentication / identity provider

Repository Incident Review
→ suspicious exfiltration / malicious transmission behavior
```

A PASS in one does not imply a PASS in another.

## Completion Criteria

Vu2 is complete when:

```text
- exact matrix binding is preserved
- sensitive-data classification is evidence-backed
- material transmission paths are inventoried
- every sensitive-data path/hop is evaluated
- encoding/obfuscation is not confused with encryption
- HTTPS is not treated as unconditional proof
- internal plaintext hops cannot be hidden behind TLS termination
- no TLS/cipher/key-size requirement is invented
- test evidence never requires real sensitive payload exposure
- secrets/sensitive payloads are redacted from Harness evidence
- no Agent or Skill is created
```
