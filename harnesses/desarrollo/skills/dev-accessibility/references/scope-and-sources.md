# Scope and sources

## The target

The Harness proposes **WCAG 2.2 level AA** as the base: every criterion of level A and AA. The numbers are not written here by hand: `python scripts/wcag.py count` derives them from `wcag22-criteria.json`, and the tests check that file against the W3C's own `wcag.json`. WCAG 2.2 has 86 criteria — A 31, AA 24, AAA 31 — so AA is 55.

- **4.1.1 Parsing** is not one of the 86. WCAG 2.2 marks it «obsolete and removed» and gives it no level. Record it as `not_applicable`. Markup defects that hurt someone are reported under 1.3.1 or 4.1.2.
- **Nine criteria are new in 2.2:** 2.4.11 (AA), 2.4.12 (AAA), 2.4.13 (AAA), 2.5.7 (AA), 2.5.8 (AA), 3.2.6 (A), 3.3.7 (A), 3.3.8 (AA), 3.3.9 (AAA).
- **The target is a proposal**, not a rule a document fixed. A project states its own in the register: `target.level` and `target.additional`.

## Three sources

| Source | Weight | Tag |
|---|---|---|
| **WCAG 2.2** — the W3C Recommendation | Decides what a criterion requires. The success criteria, the conformance section and the glossary are normative; notes, techniques and Understanding documents are informative | `wcag` |
| **Obelisco V2** — `https://gcba.github.io/Obelisco-V2/` | Decides how to build a documented component. Its adoption guide makes Obelisco the starting point, not an option. It is not WCAG, and it does not replace it | `obelisco` |
| **Harness and project** | A rule of this Harness or of the project, or a gap Obelisco leaves. Never presented as one of the other two | `harness` |

When two sources pull apart, record it; do not settle it silently. Example: Obelisco asks for an `aria-label` on a link, and WCAG 2.5.3 (Label in Name, A) requires the name to contain the visible text — so the label keeps the visible text.

## The AAA that Obelisco names

Obelisco's checklist asks for «WCAG 2.2 en los niveles AA-AAA» and does not define which AAA. The Harness reads it as AA plus the AAA criteria Obelisco **names**. They are additional, tracked only when `target.additional` lists them, and never presented as AA.

| Criterion | Level | Where Obelisco names it |
|---|---|---|
| 2.4.13 Focus Appearance | AAA | adoption guide, accessibility checklist, block 4 |
| 3.1.5 Reading Level | AAA | adoption guide, accessibility checklist, block 3 |
| 2.2.5 Re-authenticating | AAA | the form pattern |
| 2.4.8 Location | AAA | the breadcrumb component |
| 1.4.6 Contrast (Enhanced) | AAA | the colours page, without a level |

A 3:1 focus indicator is already required at AA by 1.4.11 when the author styles it; 2.4.13 adds a minimum size and a change-of-contrast rule.

## What Obelisco's text leaves open

- It does not say which AAA criteria apply (above).
- Its pages link most criteria to WCAG 2.1 Understanding pages; the criteria and levels they state are the same in 2.2.
- Its checklist cites 1.4.2 Audio Control for media that autoplay can be paused; pausing moving content is 2.2.2 (A).
- Several component pages have an Accessibility tab with no content: validation, tabs, tooltip, collapsible, carousel, switch, horizontal and vertical navigation, steps. The matrix marks them, and the requirements it gives for them are `wcag` or `harness`, never `obelisco`.
- Law 26.653, resolution 94/SECITD/23 and the ASI criteria are cited by Obelisco. The Harness quotes them as Obelisco does and does not interpret or certify them.

## What this skill never claims

That a page conforms. A conformance claim needs every criterion of the level on every page of a complete process, and the manual passes. See `evidence-register.md` for how that is recorded, and `wcag22/conformance.md` for the W3C rules.
