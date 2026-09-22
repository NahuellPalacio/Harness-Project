---
name: dev-accessibility
description: Use when frontend work has to stay accessible on a GCBA / DGISIS application — accessible structure and semantics, keyboard operability, focus behaviour, labels, status communication, colour and contrast intent, and the reflow the WorkUnit needs — on documented Obelisco components and on custom UI alike. It reviews and implements; it never self-certifies legal compliance, which stays with the configured checks and the review process. Owned by dev-frontend.
---

# Skill: dev-accessibility

## Purpose

Implement and review frontend accessibility behavior for GCBA applications across both documented Obelisco components and custom UI.

This skill belongs to the `dev-frontend` agent.

It is not limited to Obelisco components.

Its responsibility is to ensure that frontend implementation preserves accessible structure, keyboard operability, focus behavior, labels, semantics, status communication, color/contrast intent, and responsive reflow requirements applicable to the WorkUnit.

This skill does not self-certify legal or formal accessibility compliance.

Formal acceptance remains the responsibility of configured Checks and review processes.

---

## Owner

Primary owner:

`dev-frontend`

Related skills:

- `dev-ui`
- `dev-responsive`
- `dev-frontend-implementation`
- `dev-quality-validation`
- `dev-security-analysis` when accessibility behavior intersects authentication/session/security

---

# Source Model

Primary GCBA design-system references:

- https://gcba.github.io/Obelisco-V2/getting-started
- https://gcba.github.io/Obelisco-V2/components/colors
- https://gcba.github.io/Obelisco-V2/components/cards
- https://gcba.github.io/Obelisco-V2/components/table
- https://gcba.github.io/Obelisco-V2/components/grid
- https://gcba.github.io/Obelisco-V2/patterns
- https://gcba.github.io/Obelisco-V2/docs/Guía_de_adopción_de_Obelisco_v2.pdf

Obelisco V2 documents accessibility-oriented components and explicitly references WCAG 2.2 criteria in component/pattern guidance.

This skill operationalizes those concerns for the frontend WorkUnit.

It must not claim that this Markdown file replaces WCAG, applicable law, Obelisco documentation, or formal accessibility assessment.

---

# Core Principle

> If a person cannot understand, reach, operate, or perceive the UI through the supported accessible interaction modes, the frontend implementation is incomplete.

---

# Scope

This skill may analyze and implement:

```text
semantic HTML
keyboard navigation
focus visibility
focus order
keyboard traps
labels
headings
accessible names
alt text
form instructions
required/optional field communication
error communication
status messages
table semantics
color usage
contrast risks
non-text contrast
dynamic UI announcements
re-authentication continuity
reflow-related accessibility
```

---

# Obelisco and Custom UI

For documented Obelisco components:

- preserve documented semantic structure
- preserve accessibility attributes
- preserve keyboard behavior
- preserve focus behavior
- do not strip documented accessibility markup

For `CUSTOM_GCBA_UI`:

- derive accessible behavior explicitly
- do not assume visual similarity to Obelisco makes the component accessible
- require stronger validation for custom interactive behavior

---

# Mandatory Workflow

```text
1. Identify interactive and informational structure
2. Inspect semantic markup
3. Inspect keyboard reachability
4. Inspect focus visibility/order
5. Inspect accessible names and labels
6. Inspect form/error/status behavior
7. Inspect color/contrast usage
8. Inspect images/icons
9. Inspect dynamic interaction
10. Inspect table/list/navigation semantics
11. Inspect reflow/accessibility interaction
12. Run available accessibility tests
13. Declare formal checks still required
```

---

# Semantic Structure

Prefer semantic native HTML elements when they express the intended behavior.

Examples:

```text
navigation → nav / appropriate navigation structure
action → button
link/navigation → a
form field → native input/select/textarea where appropriate
table data → table/th/td
headings → ordered heading structure
```

Do not replace semantic native controls with generic clickable containers without a justified reason and equivalent accessible behavior.

---

# Keyboard Operability

Interactive functionality must be usable by keyboard where applicable.

Validate:

```text
Tab navigation
Enter/Space activation as appropriate
arrow-key behavior where required by the component pattern
escape/close behavior where applicable
ability to leave the component
```

Return:

`KEYBOARD_ACCESSIBILITY_RISK`

when required interaction cannot be completed by keyboard.

---

# Focus

Interactive UI must preserve visible focus.

Validate:

```text
focus indicator visible
logical focus order
focus not lost after dynamic action
focus returns appropriately after overlays/modals when applicable
no keyboard trap
```

Do not remove focus outlines without providing an equivalent accessible focus treatment.

Return:

`FOCUS_MANAGEMENT_RISK`

when behavior is unsafe or unclear.

---

# Forms

Forms must preserve accessible labeling and structure.

Obelisco form guidance explicitly emphasizes visible labels and understandable form structure.

Validate:

```text
visible label
programmatic label association
field purpose understandable
required/optional state understandable
instructions available before interaction where required
validation errors associated with the field
form-level error summary when appropriate
logical field order
no unexpected context change on input
```

For multi-step or irreversible flows, confirm whether review/confirmation behavior is required by the WorkUnit/pattern.

---

# Status and Dynamic Messages

Dynamic status messages should be available to assistive technologies when they convey relevant state changes without moving focus.

Examples:

```text
saved successfully
validation failed
search results updated
upload completed
operation unavailable
```

Do not rely solely on visual appearance.

Return:

`STATUS_MESSAGE_ACCESSIBILITY_RISK`

when important dynamic feedback is not programmatically available.

---

# Color and Contrast

Obelisco documents semantic color usage and WCAG-oriented contrast behavior.

Apply:

```text
do not use color as the only information channel
preserve semantic meaning of design-system colors
avoid arbitrary out-of-palette colors unless explicitly justified
preserve sufficient text/non-text contrast
```

Automated contrast tooling may be used when available.

Formal compliance remains a Check/review responsibility.

Return:

`COLOR_CONTRAST_RISK`

when evidence indicates a likely problem.

---

# Images and Icons

Determine whether an image/icon is:

```text
informative
functional
decorative
```

Informative content requires an accessible textual equivalent.

Decorative imagery should not create unnecessary assistive-technology noise.

Functional icons require an accessible name that describes the action.

Do not use an icon alone when the action becomes ambiguous.

---

# Tables

For real tabular data:

- use semantic table markup
- identify headers
- preserve header-to-cell relationships
- use native interactive elements inside cells
- provide clear accessible names for row-specific actions

Do not use tables only for layout.

Coordinate responsive overflow/reflow with:

`dev-responsive`

---

# Headings

Heading structure must communicate content hierarchy.

Do not choose heading levels only for visual size.

Visual styling and semantic hierarchy are separate concerns.

When a group requires a semantic heading for assistive navigation but visual repetition is undesirable, use an approved visually-hidden technique consistent with the design system/project.

---

# Session Expiration

When a frontend flow can lose user-entered data because an authenticated session expires, inspect the applicable product/identity behavior.

Obelisco form guidance recommends enabling re-authentication without unnecessary data loss and warning users when appropriate.

Do not invent authentication behavior from this skill.

Coordinate with the applicable identity/integration skill.

---

# Custom Components

Custom interactive components require explicit accessibility design.

At minimum define:

```text
role/semantics
accessible name
keyboard model
focus model
states
disabled behavior
error behavior
screen-reader relevant updates
```

If this cannot be proven:

return:

`CUSTOM_COMPONENT_ACCESSIBILITY_REVIEW_REQUIRED`

---

# Automated vs Manual Validation

Automated accessibility tools are useful but insufficient by themselves.

Evidence should distinguish:

```text
STATIC/AUTOMATED
KEYBOARD_MANUAL
SCREEN_READER_MANUAL
VISUAL_CONTRAST
FORM_FLOW
OTHER_MANUAL
```

Do not report formal accessibility completion solely because an automated scan passes.

---

# Required Capabilities

Typical capabilities:

```text
repository.read
repository.search
repository.write

frontend.components.inspect
accessibility.inspect
html.semantic.inspect
tests.run
```

Optional:

```text
accessibility.automated.run
contrast.inspect
browser.interaction.test
```

If unavailable:

return:

`CAPABILITY_GAP`

The skill must not create Tools directly.

---

# Required Checks

Potential Checks:

```text
semantic HTML
keyboard navigation
focus visibility/order
form labels
accessible names
image alt behavior
table semantics
status messages
color/contrast
responsive reflow
automated accessibility scan
manual accessibility review
```

If a required Check does not exist:

return:

`CHECK_GAP`

The skill must not self-approve formal accessibility compliance.

---

# Result Statuses

Supported statuses:

```text
COMPLETE
PARTIAL
MISSING_CONTEXT

KEYBOARD_ACCESSIBILITY_RISK
FOCUS_MANAGEMENT_RISK
FORM_ACCESSIBILITY_RISK
STATUS_MESSAGE_ACCESSIBILITY_RISK
COLOR_CONTRAST_RISK
SEMANTIC_STRUCTURE_RISK
TABLE_ACCESSIBILITY_RISK
CUSTOM_COMPONENT_ACCESSIBILITY_REVIEW_REQUIRED

CAPABILITY_GAP
CHECK_GAP
POLICY_BLOCKED
APPROVAL_REQUIRED
SECURITY_REVIEW_REQUIRED

FAILED
```

---

# Output Contract

Example:

```yaml
accessibilityResult:

  status: COMPLETE

  semantics:
    validated: true

  keyboard:
    validated: true
    trapsDetected: false

  focus:
    visible: true
    orderValidated: true
    customManagementRequired: false

  forms:
    labelsValidated: true
    errorAssociationValidated: true

  statusMessages:
    validated: true

  color:
    colorOnlyCommunicationDetected: false
    contrastRiskDetected: false

  media:
    altBehaviorValidated: true

  customComponents:
    reviewed: []

  validation:
    automated: PASS
    keyboardManual: PASS
    screenReaderManual: NOT_EXECUTED

  requiredChecks:
    - accessibility-automated
    - accessibility-manual

  risks: []
  assumptions: []
  evidence: []
```

---

# Model Routing Metadata

## STANDARD

Use for:

- semantic corrections
- labels
- standard keyboard/focus behavior
- Obelisco component accessibility preservation
- straightforward forms/tables

## REASONING

Consider when:

- custom interactive components exist
- focus management is complex
- dynamic UI has significant assistive-technology behavior
- multi-step forms/session recovery interact
- existing UI patterns conflict with accessibility requirements

## PREMIUM

Only for exceptional ambiguity/complexity after lower tiers are insufficient.

Premium execution requires the Human Model Gate.

---

# Prohibited Behavior

This skill must not:

- declare legal/formal compliance without configured validation
- rely only on automated scans
- remove semantic HTML for styling convenience
- create keyboard traps
- remove visible focus without equivalent replacement
- use color as the only critical information channel
- hide labels visually and programmatically when a field needs an accessible name
- use generic div/span controls when native controls solve the behavior
- invent authentication/session requirements
- silently rewrite product content
- self-approve Checks
- create Tools directly
- bypass Policies

---

# Success Criteria

This skill is successful when it:

- preserves understandable semantic structure
- supports keyboard operation
- preserves visible/logical focus
- provides labels and accessible names
- exposes relevant status/error information
- avoids color-only communication
- handles images/icons appropriately
- preserves table/form semantics
- identifies custom-component risks
- distinguishes automated from manual evidence
- declares formal accessibility Checks still required
