# Source of `references/wcag22/`

Imported on 2026-10-23 from the user's skill `wcag22.skill` (SHA-256 `1c5ae2ab9b757bd5738bd7a301e681f5b2019de6f8f70fa91ad82bef93506716`, a ZIP of 13 files). The normative text is the W3C Recommendation *Web Content Accessibility Guidelines (WCAG) 2.2*, 12 December 2024, <https://www.w3.org/TR/WCAG22/>, reproduced under the W3C Document License (copying with attribution). Everything marked *informative* in these files is practitioner guidance layered on top, not W3C text.

These files are **queried, never loaded whole**: `python scripts/wcag.py criterion <id>` prints one criterion's section and `python scripts/wcag.py term <word>` one glossary entry. Together they are about 400 KB.

| File | What it holds |
|---|---|
| `perceivable.md`, `operable.md`, `understandable.md`, `robust.md` | One section per criterion: normative text, intent, how to test, common failures, sufficient and advisory techniques, implementation notes, related criteria |
| `glossary.md` | The normative definitions the criteria depend on |
| `conformance.md` | Levels, full-page and complete-process rules, non-interference, claims, partial conformance, how to scope and sample an audit |
| `whats-new-in-2-2.md` | Differences from 2.1 and 2.0, the nine new criteria, the removal of 4.1.1 |
| `input-purposes.md` | The input purposes for 1.3.5 and the HTML `autocomplete` mapping |

## What was imported and what was not

- Imported unchanged: the eight files above. Their criterion levels were checked against the W3C data with `wcag.py levels` and no pair is wrong.
- Not imported, and replaced:
  - `SKILL.md` and `references/checklist.md` stated three incompatible totals for the same list: a grand total that counted the removed criterion, and two different level-A figures that counted it too and disagreed on how many were testable. WCAG 2.2 has 86 criteria with a level — A 31, AA 24, AAA 31 — and 4.1.1 has none. The list now lives in `../wcag22-criteria.json`, checked against the W3C's `wcag.json`.
  - `references/audit-report-template.md` became `../evidence-register.md`, with a validator.
  - `scripts/contrast_ratio.py` and `scripts/html_quick_check.py` were rewritten as `../../scripts/contrast.py` and `../../checks/lib/a11y.py`: the first did not run on Python 3.9 and discarded transparency; the second took an `aria-labelledby` to an empty element for a name and reported «no `<h1>`» as a level A failure.
- Technique and failure identifiers are those of the W3C data (`tests/fixtures/wcag22-w3c.json`). One the original scripts cited, F47, is not in the WCAG 2.2 technique data.
