---
name: dev-performance-validation
description: Use when a WorkUnit or a non-functional requirement of a GCBA / DGISIS project needs objective performance evidence — performance, stress, scalability, availability, startup time, latency, throughput and resource usage — planned, executed, interpreted and documented. Deliberately tool-agnostic: it uses the tooling the project already approved and imposes none. It produces evidence for dev-quality-validation. Owned by dev-quality.
---

# Skill: dev-performance-validation

## Purpose

Plan, execute, interpret, and document performance, stress, scalability, availability, startup, latency, throughput, and resource-usage validation for GCBA applications when the WorkUnit or applicable non-functional requirements require objective performance evidence.

This skill belongs to the `dev-quality` agent.

It generates performance/NFR evidence consumed by:

`dev-quality-validation`

This skill is intentionally tool-agnostic.

It may use the project's approved performance tooling, but it must not impose JMeter, k6, Gatling, Playwright, or any other tool without project/technology evidence.

---

## Owner

Primary owner:

`dev-quality`

Primary consumer:

`dev-quality-validation`

Related skills:

- `dev-devops-implementation`
- `dev-openshift`
- `dev-deployment`
- `dev-backend-implementation`
- `dev-frontend-implementation`
- `dev-integration-implementation`
- `dev-data`
- `dev-persistence`
- `dev-observability`
- `dev-architecture-analysis`

---

# Core Principle

> Performance validation must compare measurable behavior against an explicit workload and an explicit requirement. "Feels fast" is not evidence.

The skill must answer:

> Under what load, with which data and environment, does the system meet or fail its relevant latency, throughput, scalability, availability, startup, and resource expectations?

---

# Normative Basis

Primary source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas include:

```text
Section 4
→ performance-quality process for software changes

Section 11
→ non-functional requirements
→ OpenShift request/service duration under 30 seconds
→ startup under 60 seconds
→ 24x7 availability where applicable
→ horizontal scalability
→ stateless/granjable application behavior
→ cache usage where required by project characteristics

Section 13
→ dynamic controls
→ CPU/RAM profiling
→ code/quality acceptance evidence

QA controls
→ performance
→ stress
→ scalability
→ availability
```

Project-specific NFRs override generic assumptions when stricter or more detailed.

---

# Scope

This skill may validate:

```text
LATENCY
THROUGHPUT
CONCURRENCY
LOAD
STRESS
SCALABILITY
AVAILABILITY
STARTUP
RESOURCE_USAGE
DATABASE_PERFORMANCE
INTEGRATION_LATENCY
BATCH_PERFORMANCE
CACHE_EFFECTIVENESS
```

Not every WorkUnit requires every dimension.

---

# Mandatory Workflow

```text
1. Resolve performance objective/NFR
2. Identify critical operation(s)
3. Identify representative environment
4. Define workload model
5. Define data model/volume
6. Define measurement metrics
7. Define pass/fail thresholds from evidence
8. Prepare monitoring/profiling
9. Establish baseline
10. Execute load/performance scenario
11. Observe latency/throughput/errors/resources
12. Increase load when stress/scalability required
13. Identify bottleneck evidence
14. Compare with baseline/NFR
15. Classify result
16. Return structured evidence
```

---

# Performance Requirement

Do not invent thresholds.

Threshold sources may include:

```text
ES0901
Ficha de Proyecto
PRD
ADR
NFR document
SLA/SLO
existing production baseline
platform constraint
provider contract
approved architecture decision
```

If no measurable requirement exists:

return:

`PERFORMANCE_REQUIREMENT_UNRESOLVED`

The skill may still establish a baseline, but must not call it PASS/FAIL against an invented target.

---

# Critical Operations

Identify the operations that matter.

Examples:

```text
citizen search
login callback
create transaction
large listing
file upload
report generation
batch execution
external service call
```

Do not benchmark only an easy endpoint if the WorkUnit affects a different critical path.

---

# Environment

Performance tests must state the environment.

Possible evidence levels:

```text
LOCAL
DEV
QA
HML
PERFORMANCE_ENVIRONMENT
PRD_OBSERVATION
```

Do not present local laptop results as representative production-capacity evidence.

Return:

`PERFORMANCE_ENVIRONMENT_NOT_REPRESENTATIVE`

when environment differences make conclusions unsafe.

---

# Workload Model

Define workload explicitly.

Possible dimensions:

```text
virtual/concurrent users
requests per second
arrival rate
operation mix
test duration
ramp-up
ramp-down
think time
payload sizes
data distribution
```

Do not use arbitrary "100 users" without workload evidence.

---

# Data Volume

Performance depends on realistic data volume.

Specify:

```text
record count
dataset size
pagination behavior
historical volume
file sizes
relationship density
```

Coordinate with:

`dev-data`

and:

`dev-persistence`

when data characteristics are uncertain.

Return:

`PERFORMANCE_DATASET_UNREPRESENTATIVE`

when test data invalidates the conclusion.

---

# Baseline

Capture a baseline before optimization or major performance-sensitive change when possible.

Baseline should identify:

```text
version
environment
workload
data volume
latency
throughput
error rate
CPU
memory
```

If regression comparison is required but no comparable baseline exists:

return:

`PERFORMANCE_BASELINE_MISSING`

---

# Latency

Measure distributions rather than only average where tooling supports it.

Useful evidence may include:

```text
median
p90
p95
p99
max
```

Do not require all percentiles when project/tooling does not support them.

Do not hide poor tail latency behind a good average.

---

# Throughput

Measure completed work per unit of time when relevant.

Examples:

```text
requests/second
transactions/minute
records/second
batch items/minute
messages/second
```

Throughput must be interpreted together with:

```text
latency
errors
resource saturation
```

---

# Error Rate

Performance success requires correctness.

A system that reaches high throughput by returning errors has failed the workload.

Track:

```text
success count
functional errors
timeouts
5xx
provider failures
connection errors
```

If errors invalidate the measurement:

return:

`PERFORMANCE_RUN_INVALID`

---

# Stress Testing

Stress testing asks:

> What happens beyond the expected operating load?

Observe:

```text
degradation point
failure mode
recovery
error behavior
resource saturation
queue buildup
dependency collapse
```

The goal is not simply to crash the system.

If stress testing could affect shared/production infrastructure, require explicit approval.

---

# Scalability

Scalability validation asks whether adding allowed resources/replicas produces the expected capacity behavior.

For horizontally scalable OpenShift applications, coordinate with:

`dev-openshift`

Possible comparisons:

```text
1 replica vs 2 replicas
load vs throughput
load vs latency
load vs CPU/memory
```

Do not scale blindly if the application is stateful.

Return:

`SCALABILITY_VALIDATION_BLOCKED`

when architecture/platform prevents safe testing.

---

# Statelessness

For horizontally scaled applications, inspect performance behavior for:

```text
session affinity assumptions
local state
duplicate processing
shared-cache behavior
race conditions
```

Functional correctness must remain intact under multiple replicas.

---

# Startup

Where ES0901 OpenShift requirements apply:

```text
application startup < 60 seconds
```

Measure real startup from platform/deployment evidence.

Do not infer startup performance from unit-test boot time.

Return:

`STARTUP_REQUIREMENT_FAILED`

when applicable.

---

# Platform Request Duration

Where the ES0901 OpenShift platform rule applies:

```text
exposed request/service < 30 seconds
```

If the application requires longer synchronous work:

return:

`PLATFORM_TIMEOUT_REQUIREMENT_FAILED`

and escalate to:

`dev-architecture-analysis`

for possible approved asynchronous design.

---

# Resource Profiling

Section 13 requires CPU/RAM profiling evidence in acceptance.

When applicable, capture:

```text
CPU utilization
memory usage
memory growth
GC/runtime indicators where available
container restart/OOM evidence
```

The skill must not invent CPU/RAM limits.

Compare against:

```text
platform limits
project NFRs
baseline
saturation behavior
```

---

# Memory Behavior

Distinguish:

```text
expected warm-up/cache growth
bounded memory use
unbounded growth/leak risk
OOM behavior
```

A short test may be insufficient for memory-leak conclusions.

Return:

`MEMORY_BEHAVIOR_REVIEW_REQUIRED`

when evidence is inconclusive.

---

# Database Performance

When database behavior dominates the WorkUnit, inspect:

```text
query latency
query count
N+1 behavior
index usage evidence
locking
transaction duration
connection pool pressure
```

Do not change indexes/schema directly from this skill.

Delegate implementation to:

- `dev-data`
- `dev-persistence`

---

# External Integration Performance

When an external/internal dependency affects latency:

separate:

```text
application processing time
network time
provider/service time
retry time
```

Do not attribute provider latency automatically to local application code.

Coordinate with:

- `dev-external-integration`
- `dev-service-integration`

---

# Cache

Evaluate cache only when project/NFR evidence makes it relevant.

Measure:

```text
hit rate
miss behavior
warm/cold latency
staleness correctness
source-of-truth behavior
```

Do not recommend caching solely because an endpoint is slow.

Caching is an architecture/data decision.

---

# Batch Performance

For batch jobs:

measure:

```text
items processed
total duration
items/second
failure count
restartability
memory
CPU
database impact
```

Respect parameterization/scalability requirements from applicable GCBA rules.

---

# Frontend Performance

When frontend performance is in scope, possible evidence includes:

```text
page load/navigation timing
resource size
critical interaction latency
API waterfall
rendering delay
```

Do not invent web-vitals thresholds unless the project has adopted them.

---

# Availability / Recovery

Availability testing may inspect:

```text
restart recovery
replica failure
dependency interruption
readiness behavior
rollout continuity
```

Do not simulate destructive failures in shared/production environments without approval.

---

# Load Generation Safety

Performance tools can generate harmful traffic.

Before execution identify:

```text
target environment
maximum load
provider dependencies
database impact
production impact
external provider quotas/cost
```

High-load or production tests may require Tool Risk Human Gate.

---

# External Provider Cost / Rate Limits

Do not load-test external providers without explicit permission.

Potential risks:

```text
cost
rate-limit bans
email/message delivery
real side effects
provider SLA violation
```

Use mocks/sandbox for load generation when appropriate, but state that provider capacity was not validated.

---

# Test Duration

Test duration must be sufficient for the target question.

Examples:

```text
short latency validation
steady-state load
long-running soak
stress ramp
```

Do not use a 30-second test to claim long-term stability.

---

# Warm-Up

Some runtimes/caches require warm-up.

If relevant:

separate warm-up from measurement.

Do not hide startup/cold-path problems if they matter to the requirement.

---

# Tool Selection

Use existing approved project tooling where possible.

Potential tools may include:

```text
JMeter
k6
Gatling
custom benchmark
platform metrics
APM/profiling tools
Playwright for limited user-flow timing
```

These are examples, not mandatory choices.

Tool choice should depend on:

```text
existing stack
approved dependencies
protocol
load model
metrics needed
CI/platform integration
```

---

# Playwright Boundary

Playwright is excellent for functional browser automation but is not the default high-load generator.

Use Playwright performance timing only for questions it can answer safely.

Do not use thousands of browser instances when protocol-level load tooling is more appropriate.

---

# Repeatability

Record:

```text
tool/version
test script version
artifact version
environment
dataset
load parameters
configuration
start/end time
```

A performance result without reproducibility metadata is weak evidence.

---

# Result Comparison

Compare:

```text
candidate vs requirement
candidate vs baseline
candidate vs prior version
```

Do not compare results from materially different environments/datasets without noting limitations.

Return:

`PERFORMANCE_COMPARISON_INVALID`

when comparison conditions are incompatible.

---

# Bottleneck Classification

Potential classifications:

```text
APPLICATION_CPU
APPLICATION_MEMORY
DATABASE
EXTERNAL_DEPENDENCY
NETWORK
LOCKING
THREAD/CONNECTION_POOL
PLATFORM_RESOURCE
UNKNOWN
```

Do not assert root cause without evidence.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
performance.scripts.inspect
performance.test.run
performance.results.inspect

metrics.cpu.inspect
metrics.memory.inspect
metrics.latency.inspect

deployment.state.inspect
environment.config.inspect
```

Depending on WorkUnit:

```text
database.performance.inspect
openshift.metrics.inspect
integration.metrics.inspect
network.metrics.inspect
```

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

```text
performance requirement defined
environment representativeness
dataset representativeness
baseline provenance
latency requirement
throughput requirement
error-rate validity
startup < applicable threshold
request duration < applicable platform threshold
CPU/RAM profiling
scalability
performance regression
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

PERFORMANCE_REQUIREMENT_UNRESOLVED
PERFORMANCE_ENVIRONMENT_NOT_REPRESENTATIVE
PERFORMANCE_DATASET_UNREPRESENTATIVE
PERFORMANCE_BASELINE_MISSING

PERFORMANCE_RUN_INVALID
PERFORMANCE_COMPARISON_INVALID
PERFORMANCE_REGRESSION_DETECTED

STARTUP_REQUIREMENT_FAILED
PLATFORM_TIMEOUT_REQUIREMENT_FAILED

RESOURCE_SATURATION_RISK
RESOURCE_PROFILING_INCOMPLETE
MEMORY_BEHAVIOR_REVIEW_REQUIRED

SCALABILITY_VALIDATION_BLOCKED
SCALABILITY_REQUIREMENT_FAILED

DATABASE_PERFORMANCE_RISK
EXTERNAL_DEPENDENCY_PERFORMANCE_RISK
BATCH_PERFORMANCE_RISK

LOAD_TEST_APPROVAL_REQUIRED

ARCHITECTURE_REVIEW_REQUIRED
DEVOPS_CHANGE_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

```yaml
performanceResult:

  status: COMPLETE

  workUnit:
    id: WU-123

  target:
    operation: GET /api/reservations
    environment: QA
    artifact: sha256:...

  requirement:
    source: PROJECT_NFR
    latencyP95Ms: 800
    throughputRps: 50

  workload:
    durationSeconds: 900
    concurrentUsers: 100
    targetRps: 50

  dataset:
    representative: true
    records: 500000

  baseline:
    available: true
    artifact: previous-version

  metrics:

    latency:
      p50Ms: 180
      p95Ms: 620
      p99Ms: 760

    throughput:
      achievedRps: 52

    errors:
      percentage: 0.1

    resources:
      cpuPeakPercent: 68
      memoryPeakMb: 920

  scalability:
    required: true
    result: PASS

  platform:
    startupSeconds: 34
    startupRequirementSatisfied: true
    platformTimeoutRisk: false

  comparison:
    baselineRegressionDetected: false

  findings: []

  risks: []

  evidence:
    - performance-run-123
    - platform-metrics-456

  assumptions: []
```

---

# Model Routing Metadata

## STANDARD

Use for:

```text
existing performance script execution
baseline comparison
simple NFR validation
startup/runtime measurement
standard profiling interpretation
```

## REASONING

Consider when:

```text
workload must be designed
multiple bottleneck candidates exist
database/provider/platform interactions matter
scalability is non-linear
results conflict across runs
resource behavior is ambiguous
```

## PREMIUM

Consider only when:

```text
critical high-scale architecture
complex multi-system bottleneck
major production capacity decision
repeated lower-tier analysis fails
```

Premium execution must pass the Human Model Gate.

High-load/production execution may independently require Tool Risk approval.

---

# Prohibited Behavior

This skill must not:

- invent performance thresholds
- claim production capacity from local tests
- ignore dataset/environment differences
- report high throughput when error rate invalidates the run
- load-test third parties without approval
- cause production load without required approval
- assume average latency proves tail latency
- use Playwright as a high-load tool by default
- change database indexes/schema directly
- introduce caching as an automatic fix
- claim root cause without evidence
- claim long-term stability from short tests
- self-approve quality readiness
- self-approve formal Checks
- create Tools directly
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- resolves measurable NFRs
- defines representative workload/data/environment
- captures reproducible baseline evidence
- measures latency, throughput, errors, and resources appropriately
- validates startup/platform constraints when applicable
- evaluates scalability when required
- distinguishes application vs dependency bottlenecks
- protects external providers/production from unsafe load
- detects regressions using comparable evidence
- returns structured performance evidence to `dev-quality-validation`

---

# Source References

Primary GCBA source:

`ES0901 - Estándar de Desarrollo ASI - Version 6.3`

Relevant areas:

```text
Section 4
Section 11
Section 13
QA performance/stress/scalability/availability controls
```

Tooling remains project-specific and must not be invented from generic examples.
