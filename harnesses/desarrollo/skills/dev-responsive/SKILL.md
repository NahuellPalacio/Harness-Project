---
name: dev-responsive
description: Use when frontend behaviour has to hold across viewport sizes on a GCBA / DGISIS application — layout and reflow, breakpoints, navigation and tables on small screens, touch targets — so information, interaction and capability survive the resize instead of being hidden. Applies to Obelisco-based UI and to custom GCBA UI. Owned by dev-frontend.
---

# Skill: dev-responsive

## Purpose

Implement and review responsive frontend behavior for GCBA applications so that information, interaction, and functionality remain usable across relevant viewport sizes without losing meaning or capability.

This skill belongs to the `dev-frontend` agent.

It applies to both Obelisco-based UI and custom GCBA UI.

---

## Owner

Primary owner:

`dev-frontend`

Related skills:

- `dev-ui`
- `dev-accessibility`
- `dev-frontend-implementation`

---

# Source Model

Primary GCBA design-system references:

- https://gcba.github.io/Obelisco-V2/components/grid
- https://gcba.github.io/Obelisco-V2/patterns
- https://gcba.github.io/Obelisco-V2/components/cards
- https://gcba.github.io/Obelisco-V2/components/table
- https://gcba.github.io/Obelisco-V2/getting-started

Current Obelisco V2 documentation defines responsive grid behavior and documents component/pattern behavior across desktop, tablet, and mobile.

The grid documentation explicitly connects responsive reflow with WCAG 2.2 Reflow requirements.

This skill uses that documentation as the default GCBA responsive reference while preserving existing project compatibility.

---

# Core Principle

> Responsive behavior is not "make everything smaller." It is preserving content, hierarchy, operability, and comprehension as available space changes.

---

# Required Context

Expected context:

- WorkUnit objective
- current layout/grid
- current Obelisco/project version
- relevant components
- target content density
- existing responsive behavior
- tables/forms/navigation involved
- custom UI involved
- screenshots/design references if available
- applicable accessibility requirements

Return `MISSING_CONTEXT` when the intended behavior cannot be determined safely.

---

# Obelisco Grid Reference

Current Obelisco V2 documentation defines these breakpoints:

```text
xs  < 576px
sm  >= 576px
md  >= 768px
lg  >= 992px
xl  >= 1200px
xxl >= 1400px
```

Its documented standard device/grid references include:

```text
Desktop → 12 columns
Tablet  → 6 columns
Mobile  → 2 columns
```

The skill must inspect the actual project version before assuming these values apply unchanged.

Do not silently migrate grid behavior between Obelisco versions.

---

# Mandatory Workflow

```text
1. Inspect current layout
2. Resolve project/design-system grid
3. Identify critical content/actions
4. Define desktop/tablet/mobile behavior
5. Evaluate reflow
6. Evaluate navigation/side sections
7. Evaluate forms
8. Evaluate cards/lists
9. Evaluate tables/dense data
10. Evaluate custom components
11. Validate no information/functionality loss
12. Validate with accessibility concerns
13. Return evidence
```

---

# Layout Behavior

Responsive adaptation may include:

```text
column count changes
stacking
container-width changes
spacing changes
navigation adaptation
content priority changes
horizontal overflow for data structures where appropriate
```

Do not hide essential functionality merely to make a layout fit.

If functionality disappears at a smaller viewport:

return:

`RESPONSIVE_FUNCTIONALITY_LOSS`

---

# Reflow

Responsive layouts must reflow without losing required information or functionality.

For custom UI, explicitly verify:

```text
content remains reachable
controls remain operable
reading order remains coherent
labels remain associated
no essential overlap
no clipped critical content
```

Return:

`REFLOW_RISK`

when the UI requires horizontal/vertical behavior that compromises comprehension or operation.

---

# Sidebars and Secondary Regions

Current Obelisco grid guidance states that tablet/mobile layouts place sections one below another and do not preserve desktop-style lateral sections in the same form.

When a desktop screen has:

```text
sidebar + main content
```

define how that sidebar content is represented on smaller screens.

Do not simply hide it if it contains required information/actions.

---

# Forms

Current Obelisco form patterns favor:

- readable field widths
- primarily vertical flow
- coherent grouping
- fewer fields per horizontal row
- mobile stacking

The skill should inspect:

```text
field grouping
label readability
button placement
section spacing
error visibility
keyboard viewport interaction
```

If a desktop multi-column form becomes unreadable on mobile:

return:

`FORM_RESPONSIVE_RISK`

---

# Cards and Collections

Current Obelisco card guidance documents responsive stacking and spacing behavior.

For card/list collections, define:

```text
number of columns by viewport
stacking order
gap/spacing
content truncation behavior
interactive target behavior
```

Do not preserve dense desktop card columns on narrow screens when the design system/project expects stacking.

---

# Tables and Dense Data

Current Obelisco table guidance permits horizontal scrolling on mobile when a table exceeds available width.

The skill must distinguish:

```text
real tabular data
vs
layout pretending to be a table
```

For real tables, evaluate:

```text
horizontal scroll
sticky context if project supports it
column priority
action reachability
keyboard access
focus visibility
```

Do not remove required columns without product evidence.

Coordinate accessibility with:

`dev-accessibility`

---

# Navigation

Navigation must remain understandable and operable across viewports.

Do not copy desktop navigation behavior blindly to mobile.

Use documented Obelisco/project navigation patterns when available.

If no safe mobile navigation behavior exists:

return:

`RESPONSIVE_NAVIGATION_RISK`

---

# Custom GCBA UI

`CUSTOM_GCBA_UI` requires explicit responsive behavior.

For each custom component define:

```text
minimum usable width
layout changes
stacking behavior
overflow behavior
text wrapping
interactive target preservation
content priority
```

If not defined:

return:

`CUSTOM_UI_RESPONSIVE_REVIEW_REQUIRED`

---

# Breakpoint Rules

Prefer:

```text
existing project breakpoints
or
current compatible Obelisco breakpoints
```

Do not introduce arbitrary breakpoints because one screenshot happens to look better at a specific width.

A custom breakpoint requires evidence.

Possible evidence:

- real component usability threshold
- approved design
- existing project convention
- documented design-system need

---

# Spacing

Responsive spacing should follow current design-system/project conventions.

Do not scale every value proportionally.

Use documented component/pattern spacing where available.

Custom spacing must remain consistent with the design system.

---

# Text and Content

Validate:

```text
text wrapping
heading wrapping
button/action label wrapping
long names
error messages
dynamic values
localization/content length when relevant
```

Do not solve overflow by truncating meaningful content without product evidence.

---

# Images and Media

Responsive media must:

```text
fit available layout
preserve meaningful content
avoid layout overflow
maintain required alternative text behavior
```

Do not distort meaningful imagery to fit arbitrary dimensions.

---

# Validation Viewports

At minimum, validate the viewports relevant to the project and current design system.

Evidence should distinguish:

```text
DESKTOP
TABLET
MOBILE
```

When needed, include exact viewport sizes used by testing.

Do not claim responsive validation after testing only one viewport.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

frontend.styles.inspect
frontend.components.inspect
responsive.inspect

tests.run
```

Optional:

```text
browser.viewport.test
visual.regression.run
accessibility.inspect
```

If unavailable:

return:

`CAPABILITY_GAP`

---

# Required Checks

Potential Checks:

```text
responsive reflow
desktop/tablet/mobile viewport validation
no functionality loss
form responsive behavior
table overflow behavior
custom UI responsive behavior
visual regression
accessibility reflow
```

If unavailable:

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

REFLOW_RISK
RESPONSIVE_FUNCTIONALITY_LOSS
FORM_RESPONSIVE_RISK
TABLE_RESPONSIVE_RISK
RESPONSIVE_NAVIGATION_RISK
CUSTOM_UI_RESPONSIVE_REVIEW_REQUIRED
BREAKPOINT_DECISION_REQUIRED
DESIGN_SYSTEM_VERSION_RISK

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED

FAILED
```

---

# Output Contract

Example:

```yaml
responsiveResult:

  status: COMPLETE

  designSystem:
    name: Obelisco
    projectVersion: "..."

  layout:
    desktop: VERIFIED
    tablet: VERIFIED
    mobile: VERIFIED

  reflow:
    informationLossDetected: false
    functionalityLossDetected: false

  forms:
    reviewed: true
    stackingValidated: true

  tables:
    reviewed: true
    horizontalOverflowStrategy: RESPONSIVE_SCROLL

  customUI:
    reviewed:
      - domain-timeline

  breakpoints:
    source: PROJECT_OR_OBELISCO
    customBreakpointsAdded: false

  validation:
    viewports:
      - DESKTOP
      - TABLET
      - MOBILE

  requiredChecks:
    - responsive-reflow
    - visual-regression

  risks: []
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

## STANDARD

Use for:

- grid/layout adjustments
- standard form/card/table responsive behavior
- existing Obelisco component responsiveness
- minor breakpoint fixes

## REASONING

Consider when:

- dense administrative interfaces exist
- custom UI needs different structural behavior across viewports
- table/navigation behavior is complex
- information prioritization is ambiguous
- project and design-system conventions conflict

## PREMIUM

Only when responsive redesign becomes unusually complex after lower tiers are insufficient.

Premium execution requires the Human Model Gate.

---

# Prohibited Behavior

This skill must not:

- design only for desktop
- hide required functionality on mobile without approval
- introduce arbitrary breakpoints without evidence
- assume the latest Obelisco grid without checking project version
- use horizontal scrolling as a universal solution
- remove table columns silently
- truncate meaningful content arbitrarily
- break semantic/read order during visual rearrangement
- bypass accessibility
- self-approve formal Checks
- create Tools directly
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- preserves required information and functionality across viewports
- follows compatible project/Obelisco grid conventions
- handles side regions coherently
- preserves usable forms
- handles cards/collections appropriately
- handles dense tables safely
- defines custom UI responsive behavior
- avoids arbitrary breakpoints
- validates desktop/tablet/mobile behavior
- coordinates reflow accessibility
- returns structured evidence and required Checks
