# ES0902 C2 / ES0901 Annex V — Assessment Validity Resolver

## Purpose

Determine whether an existing QA security approval can still be used for the current candidate.

This resolver is cross-standard operational logic. It is not a new normative source rule.

## Sources

```text
ES0902.C2
→ official security approval in QA

ES0901 v6.3 Annex V
→ assessment performed in QA
→ mandatory before HML/PRD
→ reassessment frequency and change triggers
```

## Required Inputs

```text
approved assessment id/date
approved artifact/revision identity
current candidate identity
change set since assessment
security incident history since assessment
vulnerability remediation history since assessment
promotion target
```

## Trigger Evaluation

Return a trigger set, not a single boolean only.

Example:

```yaml
reassessment:
  required: true
  triggers:
    - type: AUTHENTICATION_FLOW_CHANGED
      evidence: ...
    - type: DEPENDENCY_CHANGED
      evidence: ...
```

Supported trigger categories derived from Annex V:

```text
DEVELOPMENT_OVER_20_DAYS
VULNERABILITY_REMEDIATION
SECURITY_INCIDENT
FUNCTIONALITY_CHANGED
ENDPOINT_ADDED_OR_MODIFIED
FRONTEND_OR_BACKEND_SECTION_REMOVED
FORM_OR_API_PARAMETER_CHANGED
EXTERNAL_INTEGRATION_CHANGED
IFRAME_OR_EXTERNAL_EMBED_ADDED
THIRD_PARTY_SCRIPT_ADDED
SECURITY_POLICY_CHANGED
ROLE_OR_PERMISSION_CHANGED
DEPENDENCY_CHANGED
INFRASTRUCTURE_MIGRATED
COMMUNICATION_PROTOCOL_CHANGED
FILE_UPLOAD_OR_DOWNLOAD_ADDED
SENSITIVE_FLOW_CHANGED
AUTHENTICATION_FLOW_CHANGED
```

Do not invent additional normative triggers without another authoritative source.

## Twenty-Day Rule

Do not apply the 20-day condition as "all approvals expire after 20 days" without context.

The Annex states:

```text
when there is development and more than 20 days have passed since the previous assessment
```

So the resolver must preserve the development/change context.

Unknown date/change relation:

`ASSESSMENT_AGE_CONTEXT_UNRESOLVED`

## Determinism

Trigger detection may be deterministic when the required evidence is structured.

Where classification of a change is ambiguous:

`ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED`

Do not use an LLM-only guess to suppress a reassessment.

## Result

```text
REUSE_ALLOWED
REASSESSMENT_REQUIRED
ASSESSMENT_VALIDITY_UNRESOLVED
```

`REUSE_ALLOWED` is not security approval; it only means no Annex V invalidating trigger was found in complete evidence.
