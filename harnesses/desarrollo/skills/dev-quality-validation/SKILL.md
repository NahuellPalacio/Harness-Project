---
name: dev-quality-validation
description: Use when a change or release candidate of a GCBA / DGISIS project has to be judged ready — what must be validated, what evidence actually exists, which required checks apply, which acceptance criteria are satisfied, what quality risk remains, and what has to block, warn or escalate. It interprets evidence; dev-test-automation and dev-performance-validation produce it. It never turns missing evidence into success. Primary validation skill of the dev-quality agent.
---

# Skill: dev-quality-validation

## Purpose

Validate the quality of GCBA software changes and release candidates using explicit evidence, applicable acceptance criteria, normative requirements, automated checks, test results, non-regression evidence, and delivery artifacts.

This is the **primary validation skill** of the `dev-quality` agent.

`dev-quality` is the harness **QA & Quality Engineering Agent**, not only a final-review agent.

Its responsibility is not to implement the feature being reviewed and not to replace formal executable Checks.

Its responsibility is to determine:

- what must be validated
- what evidence exists
- which required Checks apply
- which acceptance criteria are satisfied
- which quality risks remain
- whether the WorkUnit is ready to advance from a quality perspective
- which findings must block, warn, or escalate

This skill must never convert missing evidence into success.

---

## Owner

Primary owner:

`dev-quality`

Specialized QA skills:

- `dev-test-automation`
- `dev-performance-validation`

Related agents / skills:

- `dev-backend`
- `dev-frontend`
- `dev-integration`
- `dev-devops`
- `dev-architecture`
- `dev-security`
- `dev-refutador`
- `dev-ci-cd`
- `dev-deployment`
- `dev-observability`
- `dev-accessibility`
- `dev-responsive`

---

# Core Principle

The skill must answer:

> Is there enough objective evidence to conclude that this change satisfies its functional, technical, non-functional, regression, and normative quality requirements?

Apply this rule:

> Validate against requirements and evidence, not against confidence, intent, or implementation appearance.

---

# QA Skill Model

The `dev-quality` agent uses specialized skills to **produce** evidence and this skill to **interpret** evidence.

```text
dev-test-automation
→ Playwright
→ smoke
→ functional automation
→ regression
→ end-to-end
→ API tests
→ traces / reports / failure diagnosis

dev-performance-validation
→ performance
→ stress
→ scalability
→ startup
→ latency / throughput
→ CPU / RAM profiling

dev-quality-validation
→ acceptance matrix
→ evidence completeness
→ applicable Checks
→ findings
→ quality readiness
```

This separation is mandatory.

`dev-quality-validation` must not become the implementation location for all test automation.

---

# Quality Skill vs Check

This boundary is mandatory.

```text
dev-quality-validation
→ knows what must be validated
→ gathers evidence
→ selects applicable Checks
→ interprets combined quality evidence
→ reports findings and readiness

Check
→ performs one objective verification
→ returns deterministic/verifiable evidence where possible
```

Examples:

```text
dev-quality-validation
→ "this change requires unit tests, API contract validation and accessibility checks"

Check
→ executes the unit-test suite

Check
→ verifies API route conventions

Check
→ scans HTML accessibility rules
```

The skill must not silently invent or self-approve missing formal Checks.

If a required Check is unavailable:

return:

`CHECK_GAP`

---

# Normative Basis

Primary normative source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant source areas include:

```text
Section 3
→ application quality principles and environment promotion controls

Section 4
→ software change-management quality, performance, and security process

Section 5
→ deliverables, acceptance criteria, test plan, unit-test coverage

Section 7.1
→ development principles
→ C2 unit testing
→ P5 frontend/backend validation
→ approved technologies and maintainability rules

Section 9
→ development methodology and continuous integration

Section 11
→ non-functional requirements

Section 13
→ acceptance conditions
→ defect severity / priority
→ code-quality review
→ coverage > 80%
→ duplicated code / bugs / issues
→ cyclomatic complexity
→ dynamic quality controls
→ critical-code sampling
→ unit-test quality
→ CPU/RAM profiling

Annex I
→ Git/GitLab quality controls
→ Code Quality
→ SAST
→ DAST
→ Dependency Scanning
```

Security-specific interpretation remains owned by `dev-security`.

---

# Quality Dimensions

Quality validation may include:

```text
FUNCTIONAL
UNIT_TEST
INTEGRATION
CONTRACT
REGRESSION
CODE_QUALITY
MAINTAINABILITY
NON_FUNCTIONAL
PERFORMANCE
RESOURCE_USAGE
ACCESSIBILITY
RESPONSIVE
DEPLOYMENT_READINESS
DOCUMENTATION
NORMATIVE_COMPLIANCE
```

Not every WorkUnit requires every dimension.

The skill must select only applicable dimensions and explain why.

---

# Mandatory Workflow

The skill must execute this sequence:

```text
1. Identify WorkUnit and acceptance criteria
2. Identify affected components/domains
3. Build quality-validation scope
4. Resolve applicable normative rules
5. Resolve required Checks
6. Gather existing evidence
7. Execute available Checks/tests
8. Evaluate functional acceptance
9. Evaluate non-regression
10. Evaluate code/test quality
11. Evaluate non-functional evidence
12. Consume security result where required
13. Classify findings
14. Determine quality readiness
15. Return structured evidence
```

---

# Phase 1 — Acceptance Criteria

The primary validation baseline is the approved requirement.

Potential sources:

```text
Jira issue / HU / Bug / Task
acceptance criteria
Ficha de Proyecto
PRD
ADR
functional documentation
API contract
design reference
normative rule
```

The skill must not invent missing acceptance criteria.

If the WorkUnit cannot be objectively evaluated because its expected behavior is unclear:

return:

`ACCEPTANCE_CRITERIA_UNRESOLVED`

---

# Acceptance Matrix

Build a matrix connecting each requirement to evidence.

Example:

```yaml
acceptanceMatrix:

  AC-01:
    requirement: "User can create a reservation."
    evidence:
      - backend-test-123
      - frontend-test-456
    result: PASS

  AC-02:
    requirement: "Invalid dates are rejected."
    evidence:
      - validation-test-789
    result: PASS
```

Allowed states:

```text
PASS
FAIL
PARTIAL
NOT_TESTED
NOT_APPLICABLE
BLOCKED
```

Unknown must never become `PASS`.

---

# Phase 2 — Change Impact

Inspect the actual change.

Evidence may include:

```text
Git diff
changed files
changed modules
changed routes
changed database migrations
changed configuration
changed integrations
changed UI
changed infrastructure
```

Do not validate only the ticket description.

The real implementation may have a larger or smaller impact than the WorkUnit expected.

If implementation scope exceeds the approved WorkUnit:

return:

`SCOPE_DEVIATION`

---

# Risk-Based Validation

Validation depth should reflect change risk.

Signals include:

```text
business criticality
number of affected components
data mutation
authentication/authorization
external integration
migration
public API change
custom frontend interaction
production infrastructure
legacy-flow replacement
shared component/library
previous regression history
```

Higher-risk changes require broader evidence.

Do not reduce required quality controls merely because the change is small in lines of code.

---

# Unit Tests

ES0901 requires unit testing to provide code coverage.

The skill must evaluate:

```text
tests exist
tests execute successfully
tests are meaningful
tests cover changed behavior
tests are independent where required
coverage evidence exists
```

A test suite passing with no relevant assertions is not sufficient quality evidence.

Return:

`UNIT_TEST_QUALITY_RISK`

when tests exist but do not meaningfully verify behavior.

---

# Unit-Test Coverage

ES0901 defines a minimum coverage floor of **80%** for delivered software and Section 13 reviews code coverage above 80%.

The quality skill must distinguish:

```text
project/global coverage
changed-code coverage
module coverage
uncovered critical paths
```

The normative minimum must be enforced where applicable.

If coverage evidence is below the required threshold:

return:

`UNIT_TEST_COVERAGE_BELOW_STANDARD`

Do not manufacture coverage from test counts.

---

# Coverage Is Not Quality by Itself

A high coverage percentage does not prove correctness.

The skill must also inspect:

```text
assertion quality
boundary cases
error cases
business rules
negative paths
critical branches
regression behavior
```

Do not return `COMPLETE` only because coverage exceeds 80%.

---

# Integration Tests

For interactions between components/services, evaluate whether integration behavior was actually tested.

Possible evidence:

```text
database integration
service-to-service test
external-provider sandbox
OIDC flow test
storage integration
frontend/backend integration
```

Evidence must distinguish:

```text
MOCKED
LOCAL
DEV
QA
HML
PRD
```

Do not claim real integration validation when only mocks were executed.

Return:

`INTEGRATION_EVIDENCE_INSUFFICIENT`

when required real interaction is unproven.

---

# Contract Tests

When a WorkUnit affects an explicit contract:

```text
REST API
gRPC
event schema
webhook
external-provider contract
database migration compatibility
configuration contract
```

validate compatibility.

If a known contract is violated:

return:

`CONTRACT_VALIDATION_FAILED`

Coordinate ownership with the specialized implementation skill.

---

# Regression

Every change must identify behavior that must remain unchanged when regression risk exists.

Evidence may include:

```text
existing tests
baseline captured before change
historical behavior
API compatibility tests
visual regression
authentication baseline
integration baseline
deployment baseline
```

If regression-sensitive behavior exists but no usable evidence is available:

return:

`REGRESSION_EVIDENCE_MISSING`

---

# Functional Validation

The skill must evaluate behavior, not merely code structure.

Functional evidence may include:

```text
automated functional tests
API tests
UI interaction tests
manual QA evidence
UAT evidence
environment validation
```

For critical flows, a passing unit test alone may be insufficient.

---

# Frontend / Backend Validation

ES0901 P5 requires duplicated validation in frontend and backend where applicable.

For input-validation WorkUnits, inspect both relevant layers.

Example:

```text
frontend validation
+
backend authoritative validation
```

If only frontend validation exists for a server-enforced rule:

return:

`BACKEND_VALIDATION_MISSING`

If frontend behavior required by the UX is missing:

return:

`FRONTEND_VALIDATION_MISSING`

---

# Code Quality

Section 13 defines review focus including:

```text
duplicated code
issues and bugs
coverage
cyclomatic complexity
unit-test quality
critical-code samples
```

The skill may consume automated Code Quality results and inspect changed code.

Do not interpret one metric in isolation.

Potential findings:

```text
DUPLICATED_CODE_RISK
COMPLEXITY_RISK
MAINTAINABILITY_RISK
STATIC_QUALITY_FINDINGS
```

---

# Cyclomatic Complexity

Complexity is a risk indicator, not an automatic defect.

If complexity exceeds configured/project thresholds or materially harms maintainability:

return:

`COMPLEXITY_RISK`

Do not invent a numeric threshold if the project/tool has not defined one.

---

# Code Duplication

Detect meaningful duplication that increases maintenance risk.

Do not require zero repeated syntax mechanically when duplication is incidental or generated.

Use tool/project evidence.

---

# Static Analysis

Consume configured static-quality tooling results.

The skill may interpret:

```text
code smells
bugs
maintainability findings
duplication
complexity
style findings
```

Security-specific static findings must be handed to:

`dev-security`

Do not silently mix security acceptance into general code-quality acceptance.

---

# Security Boundary

ES0901's quality/change process includes security controls such as SAST, DAST and Dependency Scanning.

Responsibility split:

```text
dev-ci-cd
→ executes configured scanners

dev-security
→ interprets security findings and security acceptance

dev-quality
→ verifies required security evidence exists before overall readiness
```

If a required security result is missing:

return:

`SECURITY_EVIDENCE_REQUIRED`

The quality skill must not override security rejection.

---

# DAST / Dynamic Quality

Dynamic testing must be evaluated where applicable.

Possible evidence:

```text
API robustness
runtime errors
invalid-input behavior
service behavior
deployment behavior
browser behavior
stress/performance tests
```

Security DAST interpretation remains `dev-security`.

---

# Defect Classification

When findings are defects, use the applicable project/standard severity and priority model.

The skill must preserve the distinction:

```text
severity
→ impact of the defect

priority
→ urgency/order of correction
```

Do not infer priority solely from severity.

Where ES0901 applies, use its documented categories rather than inventing a scoring system.

---

# Blocking vs Non-Blocking Findings

A finding can be:

```text
BLOCKING
NON_BLOCKING
INFORMATIONAL
REQUIRES_DECISION
```

Blocking rules must come from:

```text
normative requirement
acceptance criteria
configured quality policy
security result
architecture policy
deployment policy
explicit project threshold
```

The quality skill must not create arbitrary release policy.

---

# Non-Functional Requirements

When the WorkUnit affects NFRs, validate applicable evidence.

Examples:

```text
performance
stress
scalability
availability
startup
request timeout
resource usage
maintainability
accessibility
interoperability
```

If a relevant NFR has no evidence:

return:

`NON_FUNCTIONAL_EVIDENCE_MISSING`

---

# Performance

QA in ES0901 includes performance, stress, scalability and availability testing.

The quality skill should determine whether the change requires these tests.

Signals:

```text
high-volume endpoint
database-heavy change
batch process
new caching behavior
large file processing
new external integration
high concurrency
critical citizen flow
```

Do not run expensive performance suites for every trivial change without risk evidence.

---

# Resource Profiling

Section 13 calls for profiling CPU and RAM usage.

When applicable, consume or request profiling evidence.

Return:

`RESOURCE_PROFILING_REQUIRED`

when profiling is required but absent.

The skill does not invent acceptable CPU/RAM thresholds.

Thresholds must come from project/NFR/platform evidence.

---

# Scalability

When horizontal scaling is required, quality evidence should include applicable validation.

Examples:

```text
stateless behavior
concurrent replicas
session behavior
batch behavior
container scaling
```

Coordinate platform execution with `dev-devops`.

---

# Accessibility

For frontend WorkUnits, consume `dev-accessibility` evidence when accessibility is applicable.

The quality skill should not duplicate detailed accessibility analysis.

Possible result:

```text
accessibilityResult.status == COMPLETE
```

If required accessibility evidence is absent:

return:

`ACCESSIBILITY_EVIDENCE_REQUIRED`

---

# Responsive

For frontend WorkUnits, consume `dev-responsive` evidence where applicable.

If responsive behavior is part of the standard/acceptance criteria and evidence is absent:

return:

`RESPONSIVE_EVIDENCE_REQUIRED`

---

# Documentation Quality

Applicable deliverables may require:

```text
README
UPGRADE
CHANGELOG
architecture documentation
test plan
installation manual
operation manual
user documentation
```

The quality skill checks required presence/completeness based on the WorkUnit/project.

It does not invent documents that are not required.

Return:

`REQUIRED_DOCUMENTATION_MISSING`

when applicable.

---

# Dependency / Approved Technology Evidence

Quality validation should consume approved-technology/version Checks.

If the WorkUnit introduces an unapproved dependency without required validation:

return:

`UNAPPROVED_DEPENDENCY_RISK`

Detailed technology policy belongs to the normative/policy layer and architecture.

---

# Deliverable Readiness

A software package should not be considered ready solely because compilation succeeds.

Potential readiness evidence:

```text
source committed
tests pass
coverage threshold satisfied
quality checks satisfied
security result available
required documents updated
migration/deployment instructions available
acceptance criteria covered
non-regression proven
```

---

# Environment Progression

ES0901 requires validation before promotion through:

```text
DEV
→ QA
→ HML
→ PRD
```

Quality evidence should preserve environment provenance.

Do not reuse a DEV-only test result as if it proves QA/HML validation when the standard/process requires those stages.

---

# DEV Validation

ES0901 describes DEV controls including:

```text
code quality
security code scanning
unit tests
package generation
deployment to DEV
runtime security checks
smoke tests
basic integration tests
```

`dev-quality` owns interpretation of quality/test evidence, not security-specific findings.

---

# QA Validation

ES0901 adds in QA:

```text
exploratory testing
non-functional testing
performance
stress
scalability
availability
exhaustive integration/service testing
security assessment
```

The quality skill should expand the validation scope accordingly.

---

# HML / UAT

HML includes user control/verification and approval/rejection.

If user acceptance is required but no evidence exists:

return:

`UAT_EVIDENCE_REQUIRED`

The quality agent must not impersonate the business/user approval.

---

# PRD

Production validation may include monitoring and online behavioral checks.

The quality skill may consume production verification evidence but must not create production mutations to test quality without approval.

---

# Evidence Provenance

Every quality result should identify:

```text
what was tested
where
when
against which version
using which test/check
what result
what evidence reference
```

Example:

```yaml
evidence:
  type: UNIT_TEST
  environment: CI
  artifact: sha256:...
  result: PASS
  reference: pipeline-123/job-456
```

---

# Stale Evidence

Evidence from another version or materially different commit must not automatically validate the current artifact.

If provenance does not match the candidate:

return:

`STALE_QUALITY_EVIDENCE`

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
git.diff.inspect

tests.run
tests.results.inspect
coverage.inspect

quality.scan.inspect
static.analysis.inspect

artifact.inspect
pipeline.results.inspect

api.contract.inspect
integration.results.inspect

performance.results.inspect
profiling.results.inspect
```

Depending on WorkUnit:

```text
browser.test.run
accessibility.results.inspect
responsive.results.inspect
deployment.results.inspect
```

The skill declares capabilities.

The `dev-orchestrator` resolves them through the Capability Registry.

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks include:

```text
unit tests
coverage >= normative/project threshold
test quality
acceptance criteria mapping
frontend/backend validation
API contract
integration contract
regression
code duplication
complexity
static code quality
approved dependencies
documentation presence
performance
resource profiling
accessibility
responsive
deployment readiness
```

If a required Check is unavailable:

return:

`CHECK_GAP`

The quality skill must not silently implement a fake replacement Check.

---

# Quality Gate Model

The skill produces a quality decision state, not a subjective score.

Allowed readiness states:

```text
READY
READY_WITH_NON_BLOCKING_FINDINGS
BLOCKED
INCOMPLETE_EVIDENCE
REQUIRES_DECISION
```

Do not produce arbitrary numeric quality scores.

---

# Result Statuses

Supported statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

ACCEPTANCE_CRITERIA_UNRESOLVED
SCOPE_DEVIATION

UNIT_TEST_QUALITY_RISK
UNIT_TEST_COVERAGE_BELOW_STANDARD
PIPELINE_TEST_COVERAGE_GAP

INTEGRATION_EVIDENCE_INSUFFICIENT
CONTRACT_VALIDATION_FAILED
REGRESSION_EVIDENCE_MISSING

FRONTEND_VALIDATION_MISSING
BACKEND_VALIDATION_MISSING

DUPLICATED_CODE_RISK
COMPLEXITY_RISK
MAINTAINABILITY_RISK
STATIC_QUALITY_FINDINGS

SECURITY_EVIDENCE_REQUIRED
NON_FUNCTIONAL_EVIDENCE_MISSING
RESOURCE_PROFILING_REQUIRED
ACCESSIBILITY_EVIDENCE_REQUIRED
RESPONSIVE_EVIDENCE_REQUIRED

REQUIRED_DOCUMENTATION_MISSING
UNAPPROVED_DEPENDENCY_RISK

UAT_EVIDENCE_REQUIRED
STALE_QUALITY_EVIDENCE

QUALITY_GATE_BLOCKED
QUALITY_GATE_WARNING
QUALITY_EVIDENCE_INCOMPLETE

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

Return a structured result.

Example:

```yaml
qualityResult:

  status: COMPLETE
  readiness: READY

  workUnit:
    id: WU-123

  artifact:
    commit: abc123
    version: 2.4.0
    digest: sha256:...

  acceptance:

    total: 5
    passed: 5
    failed: 0
    partial: 0

  tests:

    unit:
      executed: true
      result: PASS
      coveragePercent: 86.4
      coverageStandardSatisfied: true
      qualityReviewed: true

    integration:
      executed: true
      environment: QA
      result: PASS

    regression:
      executed: true
      result: PASS

  contracts:

    api:
      required: true
      result: PASS

  codeQuality:

    staticAnalysis: PASS
    duplicatedCodeRisk: false
    complexityRisk: false

  nonFunctional:

    performance:
      required: false

    profiling:
      required: false

  frontend:

    accessibility:
      required: true
      result: PASS

    responsive:
      required: true
      result: PASS

  security:

    required: true
    resultReference: security-result-123
    status: PASS

  documentation:

    required:
      - CHANGELOG
      - UPGRADE

    complete: true

  findings: []

  blockingFindings: []

  nonBlockingFindings: []

  requiredChecks:
    - unit-tests
    - coverage
    - api-contract
    - regression

  evidence:
    - pipeline-123
    - coverage-report-456
    - integration-run-789

  assumptions: []
```

---

# Model Routing Metadata

This skill may emit complexity signals to `automatic-consumption`.

It does not select the final model.

## STANDARD

Use for:

```text
normal test-result interpretation
acceptance-matrix validation
coverage verification
basic regression assessment
standard static-quality findings
documentation checks
```

## REASONING

Consider when:

```text
multiple domains changed
evidence conflicts
tests pass but implementation risk remains
coverage is high but test quality is questionable
complex regression scope
multiple environments provide inconsistent evidence
NFR validation is required
shared components are affected
```

## PREMIUM

Consider only when:

```text
critical release has contradictory quality evidence
large multi-system change
high-impact regression analysis
complex acceptance ambiguity remains after lower tiers
repeated reasoning attempts fail
```

Premium execution must pass the orchestrator's Human Model Gate.

---

# Escalation Conditions

Escalate to `dev-orchestrator` when:

- acceptance criteria are unresolved
- implementation scope exceeds WorkUnit scope
- required Check is missing
- required capability is unavailable
- coverage is below required threshold
- significant regression evidence is missing
- contract validation fails
- required NFR evidence is missing
- user/UAT approval is required
- security result is missing or blocking
- architecture/security/deployment decision is required
- quality policy requires human decision

---

# Prohibited Behavior

This skill must not:

- implement the feature it is validating
- mark unknown evidence as PASS
- use confidence as evidence
- approve its own formal Checks
- invent acceptance criteria
- invent performance thresholds
- invent code-complexity thresholds
- declare security findings acceptable
- declare UAT on behalf of users
- treat high coverage as proof of correctness
- treat mocked tests as real-environment integration evidence
- reuse stale evidence without provenance validation
- hide blocking findings
- create arbitrary numeric quality scores
- bypass Policies
- create Tools directly

---

# Evidence Requirements

The result must distinguish:

```text
requirement evidence
implementation evidence
test evidence
coverage evidence
static-quality evidence
contract evidence
regression evidence
non-functional evidence
security evidence
accessibility/responsive evidence
UAT evidence
environment provenance
artifact/version provenance
assumptions
risks
open decisions
```

All meaningful quality conclusions must be traceable to one or more of:

- WorkUnit / Jira
- Ficha de Proyecto
- acceptance criteria
- repository / diff
- test execution
- coverage report
- quality scanner
- pipeline
- integration result
- deployment result
- accessibility/responsive result
- security result
- ES0901
- human/UAT evidence

---

# Success Criteria

This skill is successful when it:

- maps requirements to objective evidence
- consumes Playwright/smoke/regression/E2E/API evidence from `dev-test-automation`
- consumes performance/stress/scalability/profiling evidence from `dev-performance-validation`
- validates the real implementation scope
- selects risk-appropriate quality dimensions
- verifies meaningful unit tests
- enforces applicable unit-test coverage requirements
- validates contracts and integrations
- validates non-regression
- consumes code-quality evidence
- requests NFR/performance/profiling evidence when applicable
- consumes security evidence without overriding security ownership
- consumes accessibility/responsive evidence for frontend changes
- preserves environment/artifact provenance
- identifies stale or incomplete evidence
- classifies findings as blocking/non-blocking/decision-required
- returns a structured readiness state without subjective scoring
- explicitly reports missing Checks/capabilities instead of inventing them

---

# Source References

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Key source areas:

```text
3
→ application quality and environment-promotion controls

4
→ change-management quality/performance/security process

5
→ deliverables, test plan, unit-test coverage floor

7.1
→ unit tests, frontend/backend validation, development principles

9
→ methodology / continuous integration

11
→ non-functional requirements

13
→ acceptance conditions, defect classification, code quality,
   coverage, complexity, unit-test quality, profiling

Annex I
→ Git/GitLab Code Quality and security-related scanner integration
```

Security scanner interpretation belongs to `dev-security`; quality only verifies that required security evidence exists and is compatible with release readiness.
