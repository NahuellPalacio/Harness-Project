# Check: sensitive-data-transport-protection

## Purpose

Deterministically validate evidence that sensitive data is not transmitted in plaintext across applicable material transmission paths.

## Inputs

```text
sensitiveDataTransmissionPresent
sensitive-data classification evidence
transmission path inventory
application/integration configuration
deployment/network configuration
transport metadata
authorized synthetic/runtime test evidence where needed
```

## Procedure

### 1. Applicability

```text
TRUE       -> continue
FALSE      -> NOT_APPLICABLE
UNRESOLVED -> APPLICABILITY_UNRESOLVED
```

### 2. Classification

Every evaluated sensitive-data element/category must reference authoritative classification evidence.

Unknown classification:

`SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED`

### 3. Transmission-path inventory

Enumerate all material paths carrying the classified data.

Incomplete coverage:

`TRANSMISSION_PATH_COVERAGE_UNRESOLVED`

### 4. Hop decomposition

Represent each path as one or more hops.

Example:

```text
browser -> ingress
ingress -> backend
backend -> external API
```

Do not collapse a multi-hop path into one endpoint if transport protection differs across hops.

### 5. Protection evidence

For every hop carrying sensitive data, determine:

```text
PROTECTED
PLAINTEXT
UNRESOLVED
```

`PROTECTED` requires evidence of confidentiality-in-transit.

Do not mark protected solely because a URL contains `https` when runtime/configuration evidence contradicts it.

### 6. Encoding detection

If sensitive data is merely:

```text
encoded
serialized
compressed
obfuscated
signed but not encrypted
```

and transported without confidentiality, classify the hop as plaintext for Vu2 purposes.

### 7. TLS/configuration sanity

Where relevant and inspectable, detect insecure behavior such as:

```text
certificate validation disabled
hostname verification disabled
explicit HTTP transport
TLS downgrade/redirect exposing payload
plaintext downstream hop
```

Do not turn this into a full TLS-hardening standard; verify only what is necessary to establish plaintext vs protected transmission under available evidence.

### 8. Runtime validation safety

Use synthetic/redacted data.

Never transmit real secrets/personal sensitive payloads solely for testing.

Unsafe conditions:

`SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE`

### 9. Aggregate

All applicable sensitive-data hops must be `PROTECTED`.

Any confirmed plaintext hop:

```text
PLAINTEXT_SENSITIVE_TRANSMISSION_DETECTED
→ FAIL
```

Any unresolved hop prevents PASS.

## Overall Results

```text
PASS
FAIL
NOT_APPLICABLE
APPLICABILITY_UNRESOLVED
SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED
TRANSMISSION_PATH_COVERAGE_UNRESOLVED
TRANSPORT_PROTECTION_UNRESOLVED
PLAINTEXT_SENSITIVE_TRANSMISSION_DETECTED
SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE
TEST_TARGET_UNAVAILABLE
```

## Boundary

PASS does not imply:

```text
data-at-rest encryption
proper authorization
safe logging
Vu7 PASS
D8 PASS
security assessment approval
```
