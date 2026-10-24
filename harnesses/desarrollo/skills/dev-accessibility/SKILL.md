---
name: dev-accessibility
description: Use when frontend work has to stay accessible on a GCBA / DGISIS application — WCAG 2.2 AA criteria (and the AAA ones Obelisco names), accessible names and semantics, keyboard and focus, forms, status messages, contrast — on documented Obelisco components and on custom UI alike. It reviews, implements and records evidence per criterion; it never self-certifies conformance. Owned by dev-frontend.
---

# Skill: dev-accessibility

Implements and reviews accessibility for GCBA frontend work, on documented Obelisco components and on custom UI. Owned by `dev-frontend`. Related: `dev-ui` (which component), `dev-responsive` (zoom, reflow, target size), `dev-frontend-implementation`, `dev-quality-validation`, `dev-security-analysis` when authentication or session behaviour is involved.

It never self-certifies conformance. A clean static analysis is not conformance.

## Three sources, never mixed

| Source | What it is | Tag |
|---|---|---|
| WCAG 2.2 | The normative requirement (W3C Recommendation) | `wcag` |
| Obelisco V2 | What the design system publishes for that component | `obelisco` |
| Harness / project | A rule of the Harness or of the project, or a gap Obelisco does not document | `harness` |

Say which one a requirement comes from. Detail: `references/scope-and-sources.md`.

## Target

- Base: **WCAG 2.2 AA** = A + AA. It is a proposal of the Harness, not a rule a document fixed.
- Additional: the AAA criteria Obelisco names (2.4.13, 3.1.5, 2.2.5, 2.4.8, 1.4.6) are extra, tracked only when the project's target lists them. Never present one as AA.
- 4.1.1 Parsing was removed in WCAG 2.2: record it as not applicable. Markup defects with user impact go under 1.3.1 or 4.1.2.
- Counts and levels come from `scripts/wcag.py` (`count`, `list`, `criterion`), never from memory. A wrong level is the commonest factual error: 1.3.4 Orientation is AA, 2.4.13 Focus Appearance is AAA.

## Workflow — deterministic first, the model last

1. **Link the change to its requirements.** For each component or pattern the change uses, run `python scripts/wcag.py component <id>` (or `custom`). It prints the criteria Obelisco declares, the extra requirements with their origin, and how each is verified. The `dev-ui` result carries them as `accessibilityLinks`.
2. **The light check runs by itself** after every write of HTML, a template or JSX/TSX (`dev-accesibilidad-html`). It reports only failures and defects the file decides alone. Silence means nothing more than that.
3. **Full review when the scope asks for it** — a new or changed page, form, dialog, navigation or custom component:
   `python scripts/review.py <paths> --register evidence.json --components <ids>`
   It adds heuristics, recommendations and what a file cannot decide, and states what it could not analyse.
4. **Contrast** of explicit pairs: `python scripts/contrast.py <fg> <bg> [--backdrop <color>] [--size <px>]`. Transparency is composed; a translucent background with no backdrop gets no number, only the missing piece.
5. **Manual passes** — browser (zoom, reflow, target size, rendered contrast, focus not obscured), keyboard, screen reader. Mark one `performed` in the register only if it was run; otherwise it stays `not_performed`.
6. **Record evidence per criterion** (`references/evidence-register.md`) and validate it: `python scripts/wcag.py register validate evidence.json`. Before delivering any text that cites criteria: `python scripts/wcag.py levels <file>`.

## Where to read — by task

Read one row, not all. `python scripts/wcag.py task <id>` prints the criteria of a row.

| Task | Read |
|---|---|
| `forms` | `references/task-forms.md` |
| `keyboard-focus` | `references/task-keyboard-focus.md` |
| `color-contrast` | `references/task-color-contrast.md` |
| `structure-semantics` | `references/task-structure-semantics.md` |
| `dynamic-media` | `references/task-dynamic-media.md` |
| `responsive` | the `dev-responsive` skill |

| Need | Ask |
|---|---|
| One criterion: level, tests it needs, normative text | `wcag.py criterion 2.4.11` |
| An Obelisco component or pattern | `wcag.py component form-text` |
| A defined term (target, essential, change of context) | `wcag.py term target` |
| What the sources are and how they are weighed | `references/scope-and-sources.md` |
| The register format and its rules | `references/evidence-register.md` |
| What static analysis covers and what it never will | `references/static-coverage.md` |
| The 86 criteria, one source of truth (levels, names, the manual tests each needs) | `references/wcag22-criteria.json` |
| Component → requirements → verification, as Obelisco and WCAG state them | `references/obelisco-matrix.json` |

Normative text, test procedures and techniques: `references/wcag22/`, read through `wcag.py`, never whole.

## Custom components

Obelisco covers many components; a custom one is not accessible because it looks like one. Define, at minimum: role or native element, accessible name, states, keyboard model, focus model, disabled and error behaviour, and which updates a screen reader must hear. If any is unproven, return `CUSTOM_COMPONENT_ACCESSIBILITY_REVIEW_REQUIRED`. The matrix row `custom` lists the floor, and all three manual passes apply.

## Result

```yaml
accessibilityResult:
  status: PARTIAL
  target: { wcag: "2.2", level: AA, additional: [] }
  register: { path: evidence.json, validated: true, pass: 0, fail: 2, not_applicable: 1, not_tested: 52 }
  tests: { browser: not_performed, keyboard: not_performed, screen_reader: not_performed }
  staticAnalysis: { run: true, filesAnalyzed: 3, notAnalyzed: 1 }
  links: []            # the accessibilityLinks of dev-ui
  requiredChecks: [accessibility-automated, accessibility-manual]
  risks: []
  assumptions: []
```

`COMPLETE` needs a validated register with no `fail` and every `pass` backed by the manual passes it requires. Anything less is `PARTIAL`.

## Statuses

`COMPLETE` · `PARTIAL` · `MISSING_CONTEXT` · `KEYBOARD_ACCESSIBILITY_RISK` · `FOCUS_MANAGEMENT_RISK` · `FORM_ACCESSIBILITY_RISK` · `STATUS_MESSAGE_ACCESSIBILITY_RISK` · `COLOR_CONTRAST_RISK` · `SEMANTIC_STRUCTURE_RISK` · `TABLE_ACCESSIBILITY_RISK` · `CUSTOM_COMPONENT_ACCESSIBILITY_REVIEW_REQUIRED` · `CAPABILITY_GAP` · `CHECK_GAP` · `POLICY_BLOCKED` · `APPROVAL_REQUIRED` · `SECURITY_REVIEW_REQUIRED` · `FAILED`

Return a `CAPABILITY_GAP` or `CHECK_GAP` when a tool or a formal Check is missing. Never create Tools.

## Model routing

STANDARD: semantic fixes, labels, standard keyboard and focus, preserving Obelisco accessibility, plain forms and tables. REASONING: custom interactive components, complex focus, dynamic updates, multi-step forms with session recovery, conflicts between the project and the criteria. PREMIUM: exceptional ambiguity only, behind the Human Model Gate.

## Prohibited

- Declaring legal or formal conformance, or relying on an automated scan alone.
- Writing a criterion's level, a count, or a technique id from memory.
- Presenting an AAA criterion as AA, or an Obelisco guideline as WCAG, or a Harness rule as either.
- Reporting a recommendation (one `<h1>`, a `<main>`) as a WCAG failure.
- Replacing native controls with `div` or `span`; removing visible focus without an equal replacement; creating keyboard traps.
- Using colour as the only channel; hiding a label both visually and programmatically.
- Inventing authentication or session requirements; rewriting product content; self-approving Checks; bypassing Policies.
