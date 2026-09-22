---
name: dev-test-automation
description: Use when automated tests of a GCBA / DGISIS application have to be designed, written, run, maintained or diagnosed — smoke, functional, regression, end-to-end and API — with Playwright as the primary browser and API automation framework when the project stack supports it, plus the traces and reports that make a failure readable. It produces evidence for dev-quality-validation and never decides release readiness itself. Owned by dev-quality.
---

# Skill: dev-test-automation

## Purpose

Design, implement, execute, maintain, and diagnose automated quality tests for GCBA applications, with **Playwright as the primary browser/API automation framework** when the project stack supports it.

This skill belongs to the `dev-quality` agent, which acts as a **QA & Quality Engineering Agent**.

Its responsibility is to generate trustworthy automated evidence for functional behavior, smoke, regression, end-to-end, and API validation.

This skill does not decide release readiness by itself.

It produces evidence consumed by:

`dev-quality-validation`

---

## Owner

Primary owner:

`dev-quality`

Primary quality consumer:

`dev-quality-validation`

Related skills:

- `dev-frontend-implementation`
- `dev-backend-implementation`
- `dev-integration-implementation`
- `dev-openid-connect`
- `dev-miba`
- `dev-accessibility`
- `dev-responsive`
- `dev-ci-cd`
- `dev-deployment`
- `dev-security-analysis`

---

# Core Principle

The skill must answer:

> What behavior should be automated, at which test level, with which data and environment, and how can the resulting evidence remain reliable, diagnosable, isolated, and maintainable?

Apply these rules:

> Automate behavior, not implementation details.

> A retry may reveal flakiness; it must never be treated as a fix for flakiness.

> Passing tests are useful only when they are trustworthy and relevant to the changed behavior.

---

# Playwright Position

Playwright is the primary automation framework for browser-oriented QA in this skill when compatible with the project.

Official Playwright capabilities used by this skill include:

- resilient locators
- auto-waiting
- browser contexts
- fixtures
- projects
- APIRequestContext
- authentication-state reuse
- retries
- traces
- screenshots/videos
- multi-browser execution
- mobile/device emulation
- parallel execution
- CI integration

Primary documentation:

- https://playwright.dev/docs/locators
- https://playwright.dev/docs/test-fixtures
- https://playwright.dev/docs/test-projects
- https://playwright.dev/docs/test-retries
- https://playwright.dev/docs/trace-viewer
- https://playwright.dev/docs/auth
- https://playwright.dev/docs/api-testing

Playwright must not be forced onto a project when the runtime/testing context makes it inappropriate.

---

# Test Taxonomy

The skill must distinguish test intent.

```text
SMOKE
FUNCTIONAL
REGRESSION
END_TO_END
API
INTEGRATION
UI_COMPONENT_FLOW
CROSS_BROWSER
RESPONSIVE_FLOW
AUTHENTICATION_FLOW
```

A single automated test may contribute evidence to more than one category, but its primary intent must be clear.

---

# Smoke Testing

Smoke tests answer:

> Is the deployed application alive enough for critical usage to continue?

Smoke suites should be:

```text
small
fast
high-value
stable
non-destructive where possible
environment-aware
```

Typical smoke coverage may include:

```text
application loads
critical route is reachable
authentication works where required
main navigation works
critical API dependency responds
primary business flow reaches a safe success point
```

Do not turn smoke into a full regression suite.

---

# Regression Testing

Regression tests answer:

> Did this change break behavior that previously worked?

Regression scope must come from:

```text
change impact
critical flows
historical defects
shared components
affected integrations
existing baseline
```

Do not execute every test in every context blindly when targeted regression evidence is sufficient.

Do not under-test shared or high-risk changes.

---

# End-to-End Testing

E2E validates complete user/system behavior across relevant components.

Example:

```text
browser
   ↓
frontend
   ↓
backend
   ↓
database / internal service / provider
   ↓
observable user result
```

The skill must distinguish real E2E from:

```text
frontend + mocked backend
```

Evidence must state whether dependencies are:

```text
REAL
SANDBOX
MOCKED
STUBBED
```

---

# API Testing

Playwright `APIRequestContext` may be used for API-level automation when appropriate.

Use API automation for:

```text
test setup
test data preparation
backend contract/behavior validation
faster functional checks
authentication setup when approved
cleanup
```

Do not use browser UI automation when an API test gives clearer and faster evidence.

Do not use API-only evidence to claim browser UI behavior was tested.

---

# Mandatory Workflow

```text
1. Read WorkUnit / acceptance criteria
2. Inspect changed behavior and existing suites
3. Build test strategy
4. Select test level(s)
5. Define test data
6. Define environment
7. Define authentication strategy
8. Reuse fixtures/helpers/page objects where valid
9. Implement stable locators/assertions
10. Execute locally/CI as appropriate
11. Diagnose failures
12. Classify flaky behavior
13. Capture traces/reports/evidence
14. Update regression/smoke suites where justified
15. Return structured automation evidence
```

---

# Test Strategy

Before coding tests, produce a small strategy.

Example:

```yaml
testStrategy:

  workUnit: WU-123

  required:
    smoke: true
    functional: true
    regression: true
    e2e: true
    api: true

  environment:
    primary: QA

  browsers:
    - chromium

  criticalFlows:
    - create-reservation
    - cancel-reservation

  testData:
    strategy: isolated-fixtures
```

Do not write automation without knowing what requirement it proves.

---

# Acceptance Criteria Mapping

Every new automated test should map to:

```text
acceptance criterion
regression behavior
known defect
quality requirement
critical smoke flow
```

Avoid low-value tests that assert incidental rendering without proving useful behavior.

---

# Locator Strategy

Playwright recommends user-facing locators and explicit testing contracts.

Preferred order when appropriate:

```text
getByRole
getByLabel
getByText
getByPlaceholder / getByAltText where semantically appropriate
getByTestId when a stable explicit testing contract is needed
```

Avoid brittle selectors tied to DOM structure such as:

```text
deep CSS chains
nth-child dependency
long XPath
implementation-specific class chains
```

Use CSS/XPath only when better semantic/testing contracts are unavailable and document the reason.

---

# Assertions

Prefer assertions on observable outcomes.

Examples:

```text
visible user result
URL/route
accessible role/state
API response
business state
network result when relevant
```

Avoid assertions on internal implementation details that users/contracts do not depend on.

---

# Auto-Waiting

Use Playwright's locator/action/assertion waiting behavior before introducing manual sleeps.

Prohibited by default:

```text
waitForTimeout(5000)
sleep
fixed-delay synchronization
```

unless the test is explicitly validating time behavior and there is no event/state-based alternative.

Return:

`FIXED_WAIT_RISK`

when tests depend on arbitrary sleeps.

---

# Fixtures

Use fixtures for reusable test setup that represents coherent testing context.

Possible fixtures:

```text
authenticated user
API client
test data
project/context
feature-specific setup
```

Playwright fixtures are isolated/composable and should help avoid duplicated global setup.

Do not create giant fixtures that hide the test's real dependencies.

---

# Page Objects / Test Abstractions

Page objects or similar abstractions may be used when they reduce duplication and improve intent.

Do not force Page Object Model into every trivial test.

Good abstraction:

```text
encapsulates stable page behavior
improves readable test intent
centralizes reusable locator behavior
```

Bad abstraction:

```text
hides every Playwright call
mirrors the DOM mechanically
creates deep inheritance
makes failures difficult to diagnose
```

---

# Test Isolation

Tests should be independently executable when practical.

Avoid reliance on:

```text
test execution order
state left by previous test
shared mutable account without coordination
shared global database record
```

If test B requires test A to succeed first:

return:

`TEST_ISOLATION_RISK`

unless the suite is intentionally modeling a serial workflow and this is explicitly justified.

---

# Authentication State

Playwright can reuse authenticated browser state.

Authentication state may contain sensitive cookies/headers and must never be committed to source control.

Use approved temporary/auth state paths and secret processes.

If shared auth state is used, ensure parallel tests cannot corrupt each other's server-side state.

Possible strategies:

```text
shared read-only account
one account per worker
dedicated test accounts
API-assisted setup
```

Selection must reflect application behavior.

Return:

`TEST_AUTH_STATE_RISK`

when auth state is unsafe or non-isolated.

---

# Identity Flow Tests

For real OIDC/miBA login-flow testing:

coordinate with:

- `dev-openid-connect`
- `dev-miba`

The QA skill may automate the flow but must not invent provider behavior or credentials.

If authentication-provider test setup is unavailable:

return:

`AUTH_TEST_ENVIRONMENT_UNAVAILABLE`

---

# Test Data

Test data must be explicit.

Possible strategies:

```text
fixture-generated
API-created
database-seeded through approved mechanism
pre-created QA account/entity
provider sandbox object
```

Do not silently depend on unknown shared records.

Test data should be:

```text
predictable
isolated
cleanable
safe
environment-appropriate
```

---

# Cleanup

Tests that mutate state should define cleanup where appropriate.

Cleanup must not create more risk than leaving safe ephemeral test data.

Do not run destructive cleanup broadly.

If cleanup scope is unsafe:

return:

`TEST_DATA_CLEANUP_RISK`

---

# Parallelism

Playwright can run tests in parallel.

Parallelism should be used only when test data and shared-state isolation support it.

If tests collide on shared users/data:

reduce parallelism or isolate accounts/data.

Do not mark serial execution as the default fix for poor isolation.

Return:

`PARALLEL_TEST_COLLISION_RISK`

---

# Projects

Use Playwright projects when configuration dimensions need explicit grouping.

Examples:

```text
Chromium
Firefox
WebKit
desktop/mobile
authenticated/unauthenticated
different environments
setup dependencies
```

Do not multiply projects without an actual coverage requirement.

---

# Cross-Browser

Cross-browser validation should reflect project/browser support requirements.

Do not assume all projects require all Playwright browser engines.

Use project/standard/product evidence.

If required browser coverage is unknown:

return:

`BROWSER_SUPPORT_UNRESOLVED`

---

# Responsive Automation

When responsive behavior is applicable, coordinate with `dev-responsive`.

Playwright device/viewport projects may provide automation evidence.

Do not claim responsive correctness only because a page loads at a mobile viewport.

Validate behavior and functionality.

---

# Accessibility Automation

Playwright may support automated accessibility tooling through approved project integrations.

However:

```text
automated accessibility
≠
complete accessibility validation
```

Consume/coordinate with:

`dev-accessibility`

Do not replace manual keyboard/screen-reader evidence when required.

---

# Network Inspection

Use network inspection when it helps diagnose:

```text
failed API requests
unexpected status
redirects
missing calls
duplicate calls
provider failures
```

Do not over-couple test assertions to every internal request if the user-visible behavior is the real contract.

---

# Mocking

Mocking is allowed when it improves determinism or isolates a specific behavior.

Mocks must be explicit evidence.

Never report:

```text
real provider validated
```

when the provider was mocked.

Use real/sandbox integration evidence for integration claims where required.

---

# Smoke Suite Governance

A smoke suite should contain only critical, stable scenarios.

A candidate smoke test should generally satisfy:

```text
critical path
fast enough for deployment validation
stable test data
low destructive impact
clear failure meaning
```

Avoid adding every bug regression test to smoke.

---

# Regression Suite Governance

When a defect is fixed, consider adding a regression test when:

```text
failure could recur
behavior is automatable
test provides durable value
maintenance cost is reasonable
```

Do not create permanent brittle automation for one-off behavior without value.

---

# Retries

Playwright retries are a diagnostic/resilience mechanism, not a quality fix.

Playwright categorizes tests that fail first and pass on retry as flaky.

This skill must preserve that distinction.

```text
passed first attempt
→ PASS

failed then passed on retry
→ FLAKY

failed all attempts
→ FAIL
```

A flaky test must not be silently treated as clean PASS.

Return:

`FLAKY_TEST_DETECTED`

---

# Flakiness Diagnosis

Common sources:

```text
unstable selectors
shared mutable data
network/provider instability
fixed waits
race conditions
poor state cleanup
parallel collisions
environment instability
hidden dependency between tests
```

The QA skill should diagnose before increasing retries.

Do not use:

```text
retries = 5
```

as the primary fix.

---

# Flaky Test Quarantine

If project policy supports quarantine, it must be visible and temporary.

Quarantine requires:

```text
reason
owner
tracking issue
scope
date/evidence
```

Do not silently skip a failing test.

Return:

`QUARANTINED_TEST_RISK`

when quarantine accumulates or blocks meaningful regression evidence.

---

# Trace Viewer

Use Playwright traces for failure diagnosis according to project/CI configuration.

Official guidance supports strategies such as:

```text
trace on first retry
retain trace on failure
```

Do not collect traces indiscriminately if cost/storage is excessive.

Trace evidence may include:

```text
actions
locators
DOM snapshots
network
console
screenshots
timings
```

Do not expose sensitive data in retained traces.

---

# Screenshots and Videos

Screenshots/videos are supporting diagnostic evidence.

They are not sufficient test assertions by themselves.

Capture according to failure/debug policy.

Avoid exposing:

```text
personal data
tokens
sensitive screens
```

without appropriate handling.

---

# Failure Diagnosis

Automation must distinguish:

```text
APPLICATION_DEFECT
TEST_DEFECT
ENVIRONMENT_FAILURE
DEPENDENCY_FAILURE
DATA_FAILURE
FLAKY_TEST
UNKNOWN
```

Do not open a product defect automatically for every failed test.

Return structured diagnosis confidence/evidence.

---

# Test Defect

Examples:

```text
stale locator
incorrect assertion
invalid fixture
expired test data
bad timeout
parallel collision
```

A test defect should be fixed in the automation suite, not hidden through retries.

---

# Environment Failure

Examples:

```text
QA unavailable
provider sandbox down
database unavailable
deployment incomplete
DNS failure
```

Do not report functional regression when the environment cannot execute the scenario.

Return:

`TEST_ENVIRONMENT_UNAVAILABLE`

---

# CI Integration

Coordinate with:

`dev-ci-cd`

CI should be able to run appropriate suites such as:

```text
smoke
targeted regression
full regression
API
E2E
```

Suite selection depends on trigger and release stage.

Do not force the entire expensive suite on every developer action without evidence.

---

# Suggested Pipeline Position

Conceptual example:

```text
build
  ↓
unit/static checks
  ↓
deploy QA
  ↓
Playwright smoke
  ↓
integration/E2E/regression
  ↓
quality validation
  ↓
promotion decision
```

Actual ordering belongs to project/deployment design.

---

# Tags / Annotations

Tests may be categorized using the project's supported Playwright/tagging strategy.

Useful conceptual groups:

```text
@smoke
@regression
@critical
@e2e
@api
```

Do not create taxonomy that has no execution/maintenance value.

---

# Timeouts

Timeouts should reflect expected behavior and diagnostic value.

Do not solve slow application behavior by continuously increasing test timeouts.

If a test timeout reveals application/platform performance risk:

record it separately.

Return:

`AUTOMATION_TIMEOUT_RISK`

when timeout configuration hides a real problem.

---

# Test Reports

Automation should produce structured evidence consumable by `dev-quality-validation`.

Potential data:

```text
total
passed
failed
flaky
skipped
duration
environment
artifact/commit
browser/project
failure classification
trace/report references
```

Skipped tests must remain visible.

---

# Skipped Tests

A skipped test is not PASS.

If required behavior is skipped:

return:

`REQUIRED_TEST_SKIPPED`

Reasons should be explicit.

---

# Test Maintenance

Automation is production-quality code.

Apply:

```text
code review
naming clarity
reuse
type safety where project uses it
lint/static quality
dependency governance
secret safety
```

Do not accept an automation suite that becomes a second unmaintainable application.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

playwright.config.inspect
playwright.tests.inspect
playwright.tests.run
playwright.report.inspect

browser.automation.run
api.test.run

testdata.prepare
testdata.cleanup

pipeline.results.inspect
```

Optional:

```text
trace.inspect
screenshot.capture
network.inspect
browser.multi_project.run
accessibility.automated.run
```

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

```text
test/acceptance mapping
locator stability
no fixed waits
test isolation
auth-state secret safety
required smoke coverage
regression coverage
flaky test detection
required test skipped
real-vs-mocked evidence
test report provenance
```

If unavailable:

return:

`CHECK_GAP`

---

# Result Statuses

Supported statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

TEST_STRATEGY_UNRESOLVED
AUTOMATION_SCOPE_UNRESOLVED

FIXED_WAIT_RISK
TEST_ISOLATION_RISK
TEST_AUTH_STATE_RISK
TEST_DATA_CLEANUP_RISK
PARALLEL_TEST_COLLISION_RISK

AUTH_TEST_ENVIRONMENT_UNAVAILABLE
BROWSER_SUPPORT_UNRESOLVED

FLAKY_TEST_DETECTED
QUARANTINED_TEST_RISK
AUTOMATION_TIMEOUT_RISK

TEST_ENVIRONMENT_UNAVAILABLE
REQUIRED_TEST_SKIPPED

APPLICATION_DEFECT_DETECTED
TEST_DEFECT_DETECTED
DEPENDENCY_FAILURE_DETECTED
DATA_FAILURE_DETECTED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

```yaml
testAutomationResult:

  status: COMPLETE

  workUnit:
    id: WU-123

  framework:
    name: Playwright
    validated: true

  strategy:
    smoke: true
    functional: true
    regression: true
    e2e: true
    api: true

  environment:
    name: QA
    realApplication: true
    mockedDependencies:
      - payment-simulator

  artifact:
    commit: abc123
    version: 2.4.0

  execution:

    total: 42
    passedFirstAttempt: 41
    flaky: 1
    failed: 0
    skipped: 0

  browsers:
    - chromium

  smoke:
    total: 6
    result: PASS

  regression:
    total: 25
    result: PASS_WITH_FLAKY_FINDING

  e2e:
    total: 8
    result: PASS

  api:
    total: 3
    result: PASS

  flakiness:
    detected: true
    tests:
      - reservation-search.spec.ts

  evidence:
    report: playwright-report-123
    traces:
      - trace-reservation-search
    screenshots: []

  diagnosis:
    applicationDefects: []
    testDefects: []
    environmentFailures: []

  requiredChecks:
    - test-isolation
    - flaky-test
    - smoke-coverage

  risks:
    - "One flaky regression test requires correction."

  assumptions: []
```

---

# Model Routing Metadata

## STANDARD

Use for:

```text
normal Playwright test implementation
smoke/regression maintenance
locator improvements
API tests
fixtures
ordinary CI test diagnostics
```

## REASONING

Consider when:

```text
complex E2E workflow
multiple roles/auth states
parallel test collisions
flaky behavior is difficult to reproduce
multi-system integration
test-data lifecycle is complex
provider/identity flows interact
large legacy suite needs restructuring
```

## PREMIUM

Consider only when:

```text
critical QA architecture redesign
persistent high-impact flakiness
very large cross-system automation problem
lower tiers repeatedly fail
```

Premium execution must pass the Human Model Gate.

---

# Prohibited Behavior

This skill must not:

- treat retries as a fix for flaky tests
- treat flaky as clean PASS
- use arbitrary fixed sleeps as normal synchronization
- rely on brittle deep CSS/XPath selectors when stable alternatives exist
- commit authentication storage state/secrets
- share mutable test state unsafely
- report mocked integration as real integration
- skip required tests silently
- create false product defects from environment/test failures
- claim UI validation from API-only tests
- claim responsive/accessibility completion from page-load checks
- invent user/provider credentials
- execute destructive production test flows without approval
- self-approve quality readiness
- self-approve formal Checks
- create Tools directly
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- maps automation to real requirements/risks
- chooses the correct test level
- creates stable Playwright automation
- uses resilient locators and event/state-based synchronization
- isolates tests and test data
- handles authentication state safely
- produces smoke, regression, E2E, and API evidence where required
- distinguishes mocked from real integrations
- detects and reports flaky tests
- captures actionable traces/reports
- diagnoses application vs test vs environment failures
- integrates cleanly with CI/CD
- returns structured evidence to `dev-quality-validation`

---

# Source References

Playwright official documentation:

```text
Locators
→ https://playwright.dev/docs/locators

Fixtures
→ https://playwright.dev/docs/test-fixtures

Projects
→ https://playwright.dev/docs/test-projects

Retries
→ https://playwright.dev/docs/test-retries

Trace Viewer
→ https://playwright.dev/docs/trace-viewer

Authentication
→ https://playwright.dev/docs/auth

API Testing
→ https://playwright.dev/docs/api-testing
```

Normative GCBA quality context:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

This skill must not turn Playwright examples into project-specific requirements without repository/WorkUnit evidence.
