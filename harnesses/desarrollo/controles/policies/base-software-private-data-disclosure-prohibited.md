---
id: base-software-private-data-disclosure-prohibited
type: POLICY
rule: Vu7
---

# Policy: base-software-private-data-disclosure-prohibited

## Source

```yaml
standard: ES0902
version: "6.2"
section: "6"
rule: Vu7
```

## Requirement

Base software used by the governed application must be configured so that it does not disclose private data to unauthorized consumers.

## Scope

The governed base-software inventory comes from authoritative project/runtime evidence.

Do not hardcode a universal product list.

## Private-Data Classification

Vu7 does not define a complete private-data taxonomy.

Unknown classification:

`PRIVATE_DATA_CLASSIFICATION_UNRESOLVED`

Do not invent classification from field names, file extensions, or infrastructure metadata alone.

## Effective Configuration

The Policy evaluates deployed/effective configuration, not merely intended source configuration.

A safe repository default with an unsafe environment override remains non-compliant in the affected environment.

## Unauthorized Disclosure

The same data may be legitimately returned to an authorized consumer and prohibited for an unauthorized consumer.

Therefore evaluate:

```text
data classification
surface
authorization context
effective configuration
environment
```

## Examples of Disclosure-Relevant Configuration

Operational evidence may include:

```text
directory listing / file root
default management/debug/status endpoints
backup/config/static file exposure
database/admin interfaces
metrics/status endpoints containing private data
temporary/generated file exposure
server/runtime default responses
```

These examples do not create new universal prohibitions.

## Boundaries

Do not automatically equate:

```text
version banner
technical metadata
Vu6 raw error
public endpoint
```

with Vu7 non-compliance unless private-data disclosure is established.

## Outcomes

```text
SATISFIED
NON_COMPLIANT
BASE_SOFTWARE_INVENTORY_UNRESOLVED
PRIVATE_DATA_CLASSIFICATION_UNRESOLVED
DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED
BASE_SOFTWARE_CONFIGURATION_UNRESOLVED
UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE
BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE
EVIDENCE_INCOMPLETE
```
