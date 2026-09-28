# Signal: owaspApplicableAssetPresent

## Purpose

Resolve ES0902 Vu10 applicability from governed application asset types.

## States

```text
TRUE
FALSE
UNRESOLVED
```

## TRUE

Use when authoritative evidence establishes at least one governed asset in:

```text
WEB
API_OR_WEB_SERVICE
MOBILE
```

One application may produce multiple applicable OWASP families.

## FALSE

Use only when authoritative scope evidence establishes that none of the Vu10-referenced asset families are present.

Do not infer FALSE because:
- the web application is internal
- the API is authenticated/private
- the mobile client is hybrid
- only one layer changed in the current WorkUnit

Vu10 applicability is evaluated against governed assessment scope, not only changed files.

## UNRESOLVED

Use when:
- asset inventory is incomplete
- API/web-service presence is unclear
- mobile client presence is unclear
- assessment scope cannot be mapped to project assets

## Evidence

Preserve:

```text
assetId
assetType
component/path/service reference
environment/scope
project-context or architecture reference
evidence reference
```

Do not persist credentials, tokens, or sensitive payloads.
