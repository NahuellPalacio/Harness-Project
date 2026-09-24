# Signal: sensitiveDataTransmissionPresent

## Purpose

Resolve ES0902 Vu2 applicability from authoritative data classification plus transmission-flow evidence.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when:

```text
data is transmitted across a material boundary
AND
the transmitted data is authoritatively classified as sensitive
```

## FALSE

Use only when authoritative scope evidence establishes that no sensitive data is transmitted.

Do not infer FALSE from:

```text
missing field-name matches
no secret scanner findings
no uploaded privacy document
absence of passwords
```

## UNRESOLVED

Use when:

```text
transmission exists but data classification is missing
data may be sensitive but classification is ambiguous
data classification exists but flow/path coverage is incomplete
a secondary integration/queue/export path may transmit the data
```

Typical states:

```text
SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED
TRANSMISSION_PATH_COVERAGE_UNRESOLVED
```

## Evidence

Preserve references to:

```text
data classification source
field/data category
source component
destination component
transport path/hops
environment/scope
```

Never store raw sensitive values in the signal evidence.
