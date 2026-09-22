---
name: dev-ui
description: Use when building or reviewing the user interface of a GCBA / DGISIS application — components, layout, patterns, visual states and the design-system decision behind them — with Obelisco V2 as the official reference. Prefers an existing project pattern, then a documented Obelisco component, then a composition of them, and allows custom GCBA UI only when the requirement is not covered, preserving the Obelisco foundations, accessibility, responsive behaviour and semantics. Deliberately broader than a catalog-only skill. Owned by dev-frontend, entered through dev-frontend-implementation.
---

# Skill: dev-ui

## Purpose

Design and implement frontend user interfaces for GCBA applications using Obelisco V2 as the official/default design-system reference while allowing well-justified composition and custom GCBA UI when the product requirement is not fully covered by the documented component catalog.

This skill belongs to the `dev-frontend` agent.

It is intentionally broader than an `dev-obelisco` skill.

The goal is not:

> "Only build what already exists as a named Obelisco component."

The goal is:

> "Build a coherent GCBA interface, preferring Obelisco components and patterns, composing them when possible, and creating custom UI only when necessary while preserving GCBA foundations, accessibility, responsive behavior, semantics, and project architecture."

---

## Owner

Primary owner:

`dev-frontend`

Primary implementation entry point:

`dev-frontend-implementation`

Related skills:

- `dev-accessibility`
- `dev-responsive`
- `dev-api`
- `dev-frontend-implementation`
- `dev-security-analysis` when UI handles sensitive/security-relevant behavior
- `dev-openid-connect` / `dev-miba` through the integration domain when identity behavior is involved

---

# Source Model

This skill distinguishes between:

## Official Design-System Evidence

Current Obelisco V2 documentation published by GCBA.

Primary references:

- https://gcba.github.io/Obelisco-V2/getting-started
- https://gcba.github.io/Obelisco-V2/getting-started/imports
- https://gcba.github.io/Obelisco-V2/components/grid
- https://gcba.github.io/Obelisco-V2/components/colors
- https://gcba.github.io/Obelisco-V2/patterns
- https://gcba.github.io/Obelisco-V2/components/cards
- https://gcba.github.io/Obelisco-V2/components/table
- https://gcba.github.io/Obelisco-V2/docs/Guía_de_adopción_de_Obelisco_v2.pdf

## Project Evidence

- current frontend framework
- current Obelisco version
- existing project components
- existing page/layout patterns
- existing UI conventions
- approved ADRs
- existing accessibility/responsive behavior

## Harness Operational Rules

Rules in this skill that explain how the agent should decide between reuse, composition, and custom UI.

Harness operational rules must not be presented as if they were official Obelisco component documentation.

---

# Official Obelisco Position

Obelisco is the GCBA design system.

Its current documentation describes:

- atomic and modular design
- responsive components
- accessibility-oriented components
- reusable foundations
- component usage guidance
- grid/layout behavior
- interaction states
- implementation classes
- patterns such as forms

The Obelisco adoption guide prioritizes Obelisco V2 components and classes over custom implementations when a documented component already solves the requirement.

This skill must preserve that preference.

---

# Core Principle

Use this decision order:

```text
1. Existing valid project pattern
2. Documented Obelisco component/pattern
3. Composition of documented Obelisco components
4. Custom GCBA UI when no suitable documented solution exists
```

This is not permission to bypass Obelisco.

It is a controlled extension model.

---

# UI Strategy Classification

Every meaningful UI implementation should be classified as one of:

```text
PROJECT_EXISTING_PATTERN
OBELISCO_COMPONENT
OBELISCO_COMPOSITION
CUSTOM_GCBA_UI
```

## PROJECT_EXISTING_PATTERN

Use when the project already has a valid reusable pattern consistent with the current design system and requirements.

## OBELISCO_COMPONENT

Use when one documented Obelisco component directly solves the need.

## OBELISCO_COMPOSITION

Use when multiple documented components/patterns can be composed to satisfy the need without inventing a new visual language.

## CUSTOM_GCBA_UI

Use only when the requirement cannot be adequately satisfied through existing valid project patterns or documented Obelisco components/compositions.

Custom UI must not be represented as an official Obelisco component.

---

# Mandatory UI Decision Flow

```text
User requirement
      ↓
Inspect current project UI
      ↓
Does a valid existing project pattern solve it?
      ├── YES → PROJECT_EXISTING_PATTERN
      └── NO
            ↓
Does Obelisco document a suitable component/pattern?
      ├── YES → OBELISCO_COMPONENT
      └── NO
            ↓
Can documented Obelisco components be composed coherently?
      ├── YES → OBELISCO_COMPOSITION
      └── NO
            ↓
CUSTOM_GCBA_UI
      ↓
Preserve foundations + semantics + accessibility + responsive behavior
      ↓
Declare evidence and required review/checks
```

---

# Required Context

Expected context may include:

- WorkUnit objective
- acceptance criteria
- current frontend framework
- current Obelisco version
- relevant page/components
- screenshots/design references when available
- existing component library usage
- applicable Obelisco pages
- current navigation/layout pattern
- API states
- form behavior
- content hierarchy
- accessibility requirements
- responsive requirements
- applicable ADRs
- required checks

Return `MISSING_CONTEXT` when a safe UI decision cannot be made.

---

# Step 1 — Understand the User Task

Determine:

- what the person must accomplish
- primary action
- secondary actions
- information hierarchy
- interaction sequence
- required states
- expected data density
- whether the interface is transactional, informational, administrative, or navigational

Do not start by choosing visual components.

Start with the user task.

---

# Step 2 — Inspect Existing UI

Before introducing new UI:

inspect:

```text
page layout
existing components
design-system version
existing forms
navigation
tables
cards
alerts
filters
empty states
loading states
error states
spacing
typography
color usage
responsive behavior
```

Reuse consistent project patterns where they remain valid.

Do not redesign unrelated pages.

---

# Step 3 — Resolve Obelisco Version

Determine the Obelisco version used by the repository.

Do not assume that every repository is already on the latest version.

Obelisco documentation includes migration/update guidance and changed/deprecated classes between versions.

Therefore:

```text
current project version
      ↓
current official documentation
      ↓
compatibility analysis
```

Do not silently upgrade Obelisco during an unrelated WorkUnit.

If the current version is incompatible, deprecated, or uncertain:

return:

`DESIGN_SYSTEM_VERSION_RISK`

---

# Step 4 — Search Official Obelisco Documentation

For the required UI behavior, inspect relevant official documentation.

Examples:

```text
form
→ patterns + input components + buttons

data comparison
→ table

navigation
→ header / navigation components

grouped content
→ cards / lists / access components

layout
→ grid

visual states
→ component states + colors
```

Do not invent an "Obelisco component" that does not exist in the documentation.

If no documented component/pattern matches:

continue to composition/custom evaluation.

---

# Step 5 — Prefer Official Components

When a documented Obelisco component satisfies the requirement:

use it.

Preserve its documented:

- semantics
- structure
- variants
- states
- responsive behavior
- accessibility guidance
- implementation classes
- usage constraints

Do not recreate a documented Obelisco button, input, table, card, navigation pattern, or equivalent with arbitrary third-party UI libraries without explicit approval.

---

# Step 6 — Compose Before Creating

A requirement may not have a single named Obelisco component.

Before creating custom UI, evaluate whether the requirement can be solved by composing documented components.

Example:

```text
Administrative search screen
    ↓
page heading
+ search/filter form
+ action buttons
+ table
+ pagination
+ empty/error state
```

The screen itself may be custom as a composition, while its building blocks remain aligned with the design system.

Classification:

`OBELISCO_COMPOSITION`

---

# Step 7 — Controlled Custom UI

Use `CUSTOM_GCBA_UI` only when necessary.

Custom UI must:

- preserve the project's visual language
- use Obelisco foundations/tokens/classes where applicable
- use semantic HTML
- support keyboard interaction
- provide visible focus
- preserve color meaning
- avoid color-only communication
- support responsive reflow
- avoid introducing another UI design system
- avoid claiming official Obelisco status
- remain composable and maintainable
- include evidence explaining why Obelisco reuse/composition was insufficient

Example evidence:

```yaml
uiStrategy:
  classification: CUSTOM_GCBA_UI
  reason:
    "No documented Obelisco component or composition covers the required domain-specific timeline interaction."
  obeliscoReused:
    - typography
    - colors
    - grid
    - buttons
  customSurface:
    - domain-timeline
```

---

# Foundations

Custom and composed UI must remain aligned with documented foundations.

Relevant areas include:

```text
grid
color semantics
typography
spacing
interaction states
icons
focus
responsive behavior
```

Do not use arbitrary colors when documented semantic colors solve the need.

Obelisco documentation states that color is functional and semantic rather than decorative and should not be the only means of communicating information.

---

# Grid and Layout

Use the current documented Obelisco grid or the valid project adaptation.

Current Obelisco V2 documentation defines responsive breakpoints and a grid that changes across viewport sizes.

The grid should preserve:

```text
visual coherence
readability
usable hierarchy
reflow
responsive adaptation
```

Detailed responsive decisions belong to:

`dev-responsive`

---

# Forms

When implementing forms, use Obelisco form patterns and component guidance where applicable.

Current documented form guidance includes principles such as:

- request only necessary information
- avoid redundant data entry
- choose appropriate field types
- use logical order
- use visible labels
- group related fields coherently
- provide clear actions
- preserve readable sectioning
- support accessibility and assistive technologies

Complex form behavior may still require application-specific composition.

Do not create custom form controls when an appropriate documented control exists.

---

# Tables

Use tables for structured row/column information and comparison.

Do not use tables merely as a page-layout mechanism.

Preserve semantic table markup when a real table is required.

Detailed accessibility belongs to `dev-accessibility`.

Detailed responsive handling belongs to `dev-responsive`.

---

# Interaction States

Meaningful UI must consider relevant states.

Examples:

```text
default
hover
focus
active
disabled
loading
success
empty
validation error
business error
system error
unavailable
```

Obelisco component documentation explicitly models interaction states for documented components.

For custom UI, define equivalent behavior when relevant.

Do not leave focus or error behavior undefined for interactive custom components.

---

# Content and Action Clarity

UI actions should describe their purpose.

Avoid vague action wording when a more specific label is available.

Follow the terminology and content guidance of the project and relevant Obelisco patterns.

Do not invent product copy when the WorkUnit requires business-approved content.

Return `MISSING_CONTEXT` when essential labels/content require product clarification.

---

# Iconography

Use the iconography supported by the current Obelisco/project setup.

Do not introduce another icon library without evidence and approval.

When icons are decorative, accessibility behavior must reflect that.

When icons communicate meaning or perform actions, provide appropriate accessible semantics.

---

# Third-Party UI Libraries

Do not introduce another general-purpose UI component system merely because a required screen is not directly represented in Obelisco.

Before introducing any third-party UI package:

1. prove the requirement cannot be reasonably implemented with the existing stack
2. check approved technology/dependency policies
3. analyze design-system consistency
4. analyze accessibility
5. request approval when required

Return:

`APPROVAL_REQUIRED`

or:

`POLICY_BLOCKED`

when applicable.

---

# Relationship with Accessibility

`dev-ui` must design for accessibility but does not replace the specialized accessibility skill.

Use:

```text
dev-ui
→ chooses and composes UI

dev-accessibility
→ validates/implements accessibility behavior in depth
```

When UI contains:

- custom interactive controls
- complex forms
- dynamic status changes
- keyboard interactions
- tables
- modals
- navigation
- custom focus behavior

request `dev-accessibility` as needed.

---

# Relationship with Responsive

`dev-ui` must preserve responsive composition.

Use:

```text
dev-ui
→ defines layout intent

dev-responsive
→ validates and implements viewport/reflow behavior in depth
```

Custom UI must not be considered complete if its layout works only at one viewport.

---

# Relationship with dev-frontend-implementation

```text
dev-frontend-implementation
→ owns the frontend WorkUnit implementation

dev-ui
→ owns UI selection, composition, visual-system alignment, and controlled custom UI
```

`dev-frontend-implementation` should invoke `dev-ui` when a WorkUnit creates or materially changes user-facing interface behavior.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

frontend.components.inspect
frontend.styles.inspect
frontend.routes.inspect

designsystem.version.inspect
designsystem.component.inspect

tests.run
accessibility.inspect
```

If a required capability does not exist:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential checks:

```text
design-system usage
Obelisco component correctness
Obelisco version compatibility
custom UI justification
semantic HTML
accessibility
responsive reflow
dependency approval
frontend regression
```

If a formal Check is missing:

return:

`CHECK_GAP`

The skill must not self-approve formal Checks.

---

# Result Statuses

Supported statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

UI_PATTERN_UNRESOLVED
DESIGN_SYSTEM_VERSION_RISK
OBELISCO_COMPONENT_MISMATCH
CUSTOM_UI_REQUIRED
CUSTOM_UI_JUSTIFICATION_MISSING

ACCESSIBILITY_REVIEW_REQUIRED
RESPONSIVE_REVIEW_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED
SCOPE_ESCALATION
ARCHITECTURE_REVIEW_REQUIRED

FAILED
```

`CUSTOM_UI_REQUIRED` is not automatically a failure.

It means the WorkUnit needs a custom GCBA UI surface because no appropriate documented component/composition was identified.

---

# Output Contract

Example:

```yaml
uiResult:

  status: COMPLETE

  strategy:
    classification: OBELISCO_COMPOSITION

  userTask:
    primaryGoal: "Search and manage appointments"

  designSystem:
    name: Obelisco
    projectVersion: "..."
    compatibilityValidated: true

  components:
    reused:
      - input
      - button
      - table
      - pagination

    custom:
      - none

  layout:
    gridAligned: true
    responsiveReviewRequired: true

  accessibility:
    specialistReviewRequired: true

  states:
    - default
    - loading
    - empty
    - error
    - success

  dependencies:
    added: []

  requiredChecks:
    - design-system
    - accessibility
    - responsive-reflow

  risks: []
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

This skill may provide complexity signals to `automatic-consumption`.

It does not choose the final model.

## STANDARD

Use for:

- documented Obelisco component selection
- simple component composition
- standard page/form/table layout
- small visual changes following existing patterns

## REASONING

Consider when:

- no direct Obelisco pattern exists
- custom UI is required
- multiple complex interaction states exist
- information architecture is ambiguous
- design-system/project patterns conflict
- dense administrative UI requires careful composition
- accessibility/responsive constraints interact significantly

## PREMIUM

Consider only when:

- UI complexity is exceptional
- major design-system migration is required
- repeated reasoning attempts fail
- accessibility/interaction risk is unusually high

Premium execution must pass the orchestrator's Human Model Gate.

---

# Prohibited Behavior

This skill must not:

- treat Obelisco as an exhaustive list of every possible GCBA interface
- ignore a documented Obelisco component and rebuild it arbitrarily
- invent non-existent Obelisco components
- label custom UI as official Obelisco
- introduce another design system without approval
- introduce arbitrary visual libraries
- use color as the only way to communicate critical meaning
- remove keyboard/focus behavior
- design only for desktop
- silently upgrade Obelisco
- silently change the project's frontend architecture
- invent product/business content
- bypass accessibility
- bypass responsive requirements
- self-approve Checks
- create Tools directly
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- understands the actual user task
- inspects existing project UI before creating new UI
- identifies the current design-system version
- uses documented Obelisco components when appropriate
- composes components before creating custom replacements
- allows justified custom GCBA UI when necessary
- keeps custom UI aligned with Obelisco foundations
- preserves semantic and accessible interaction
- preserves responsive behavior
- avoids unnecessary UI dependencies
- distinguishes official components from custom implementation
- produces structured evidence and required reviews/checks
