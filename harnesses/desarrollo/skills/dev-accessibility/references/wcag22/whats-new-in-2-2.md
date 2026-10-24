# What changed in WCAG 2.2 (vs 2.1 and 2.0)

WCAG 2.2 became a W3C Recommendation on 5 October 2023 and was republished with errata on 12 December 2024 (the current version, https://www.w3.org/TR/WCAG22/). It is a dot-release: everything in 2.1 is still there except one criterion, nine criteria were added, and the conformance model is unchanged.

## The spec's own summary (verbatim, informative)

> WCAG 2.2 builds on and is backwards compatible with WCAG 2.1, meaning web pages that conform to WCAG 2.2 are at least as accessible as pages that conform to WCAG 2.1. Requirements have been added that build on 2.1 and 2.0. WCAG 2.2 has removed one success criterion, 4.1.1 Parsing. Authors that are required by policy to conform with WCAG 2.0 or 2.1 will be able to update content to WCAG 2.2, but may need to continue to test and report 4.1.1.

> The Accessibility Guidelines Working Group recommends that sites adopt WCAG 2.2 as their new conformance target, even if formal obligations mention previous versions, to provide improved accessibility and to anticipate future policy changes.

## Nine new success criteria

| SC | Name | Level | User need it addresses | Full text and tests |
|---|---|---|---|---|
| 2.4.11 | Focus Not Obscured (Minimum) | AA | Keyboard users lose track of focus when sticky headers, footers, cookie banners or chat widgets cover the focused element entirely. | operable.md |
| 2.4.12 | Focus Not Obscured (Enhanced) | AAA | Same, but no part of the focused component may be hidden. | operable.md |
| 2.4.13 | Focus Appearance | AAA | Focus indicators that are too thin or too low-contrast to see: requires area ≥ 2 CSS px perimeter and ≥ 3:1 change between states. | operable.md |
| 2.5.7 | Dragging Movements | AA | People who cannot perform precise drag actions (tremor, switch access, some screen reader users) need a single-pointer alternative (click/tap buttons, arrows, input fields). | operable.md |
| 2.5.8 | Target Size (Minimum) | AA | Small or crowded targets are hard to hit; requires 24×24 CSS px or equivalent spacing (24 px circle test), with inline, equivalent, user-agent and essential exceptions. | operable.md |
| 3.2.6 | Consistent Help | A | People with cognitive disabilities need help mechanisms (contact details, contact form, chat, FAQ/self-help) in the same relative place across the set of pages. | understandable.md |
| 3.3.7 | Redundant Entry | A | Re-typing the same information in a multi-step process is a barrier; it must be auto-populated or selectable (security, essential and no-longer-valid exceptions). | understandable.md |
| 3.3.8 | Accessible Authentication (Minimum) | AA | Memorizing passwords, transcribing codes or solving puzzles are cognitive function tests; allow an alternative or a mechanism (password managers, copy/paste), or use object recognition / personal content. | understandable.md |
| 3.3.9 | Accessible Authentication (Enhanced) | AAA | Same, without the object-recognition and personal-content exceptions. | understandable.md |

New glossary terms that these criteria depend on (all normative): **cognitive function test**, **dragging movement**, **focus indicator**, **minimum bounding box**, **perimeter**. The definitions are in glossary.md.

## One criterion removed: 4.1.1 Parsing

The spec keeps the heading "4.1.1 Parsing (Obsolete and removed)" with this NOTE:

> This criterion was originally adopted to address problems that assistive technology had directly parsing HTML. Assistive technology no longer has any need to directly parse HTML. Consequently, these problems either no longer exist or are addressed by other criteria. This criterion no longer has utility and is removed.

Practical consequences:

- Under WCAG 2.2, do not report 4.1.1 failures. Duplicate `id`s, badly nested elements or missing end tags are reported only when they cause a real problem under another criterion (usually 1.3.1 Info and Relationships or 4.1.2 Name, Role, Value, e.g. a label whose `for` resolves to the wrong duplicate id).
- If a policy or contract still requires WCAG 2.0 or 2.1 (for example, procurement rules written before 2023), keep a row for 4.1.1 in the report. The W3C's guidance for 2.1 (since 2023) is that 4.1.1 should be considered always satisfied for HTML content, so the row normally reads "Supports / not applicable", and markup defects go to 1.3.1 / 4.1.2.

## Numbering

New criteria were appended at the end of their guideline so that existing numbers never change. The side effect is that criteria inside a guideline are **no longer sorted by level** (for example 2.4.7 Focus Visible is AA, 2.4.8–2.4.10 are AAA, then 2.4.11 is AA again). Always read the level from the criterion itself, never from its position.

## Other changes in 2.2

- New non-normative sections **5.6 Privacy Considerations** (flags 2.2.6 and 3.3.7) and **5.7 Security Considerations** (flags 1.1.1, 1.3.5, 1.4.7, 2.2.1, 2.2.5, 2.2.6, 2.5.6, 3.3.3, 3.3.7, 3.3.8, 3.3.9). See conformance.md.
- 2024-12-12 errata: refined definitions of *single pointer*, *used in an unusual or restricted way*, *motion animation* and *programmatically determined*; reformatted *changes of context*, *general flash and red flash thresholds*, *cognitive function test* and *structure*; removed the defunct *encloses* definition; editorial consistency in the terms "success criteria/criterion", "web", "website", "web page".
- Several errata from WCAG 2.1 were folded in (e.g. the relative luminance threshold 0.04045 instead of 0.03928, which has no practical effect).

## What 2.1 had already added over 2.0 (still fully in force)

Teams migrating from 2.0 straight to 2.2 also need these 17 criteria from 2.1: 1.3.4 Orientation (AA), 1.3.5 Identify Input Purpose (AA), 1.3.6 Identify Purpose (AAA), 1.4.10 Reflow (AA), 1.4.11 Non-text Contrast (AA), 1.4.12 Text Spacing (AA), 1.4.13 Content on Hover or Focus (AA), 2.1.4 Character Key Shortcuts (A), 2.2.6 Timeouts (AAA), 2.3.3 Animation from Interactions (AAA), 2.5.1 Pointer Gestures (A), 2.5.2 Pointer Cancellation (A), 2.5.3 Label in Name (A), 2.5.4 Motion Actuation (A), 2.5.5 Target Size (Enhanced) (AAA), 2.5.6 Concurrent Input Mechanisms (AAA), 4.1.3 Status Messages (AA).

## Migration checklist for an existing 2.1 AA site

1. Re-test keyboard focus against sticky/fixed UI (2.4.11).
2. Inventory every drag interaction: sliders, sortable lists, kanban boards, map panning, carousels, file-drop zones (2.5.7).
3. Measure clickable targets ≤ 24 px: icon buttons, pagination, close "×", table row actions, calendar days (2.5.8).
4. Check that help links / chat / contact appear in the same order on every page template (3.2.6).
5. Walk multi-step forms (checkout, registration, applications) for repeated fields (3.3.7).
6. Review login, 2FA, CAPTCHA and password-reset flows: paste allowed, password managers work, no puzzles without an alternative (3.3.8).
7. Drop 4.1.1 from the report unless a 2.0/2.1 policy requires it.
