# Static coverage

What the static analysis reads, what it decides, and what it never will. The engine is `checks/lib/a11y.py`. It runs in two modes over the same rules: the **light check** (`dev-accesibilidad-html`, after every write) and the **full review** (`scripts/review.py`, when the scope of the task asks for it).

## What it reads

| Format | Files | How |
|---|---|---|
| HTML | `.html`, `.htm`, `.xhtml` | an HTML tree |
| Templates | `.blade.php`, `.component.html`, `.njk`, `.hbs`, `.handlebars`, `.twig`, `.ejs`, `.erb`, `.jinja`, `.jinja2`, `.j2` | the same tree, after masking `{{ }}`, `{% %}`, `{# #}`, `<?php ?>`, `<% %>` and Blade directives; Angular and Vue bindings (`[attr.x]`, `:x`, `(click)`, `@click`) count as «present, value unknown» |
| JSX / TSX | `.jsx`, `.tsx` | an own tokenizer: strings, template literals, comments, regex literals, `{ }` containers, fragments, `htmlFor` and the other camelCase names, TypeScript generics skipped |

Anything else is **not analysed**, and the full review says so by name: Vue, Svelte, Razor, `.js` and `.ts` with templates in strings, CSS-in-JS, Markdown, PDF. A file over 512 KB is skipped by the light check (and over 2 MB by the review).

## What it will not judge

| Construct | What the review does |
|---|---|
| A component of your own (`<TextField />`, `<app-field>`, `<x-button>`) | Lists it as not analysed, with its name and first line. Its labels, roles and attributes are not judged |
| An element with `{...props}` | Lists it; the attributes the spread could bring are not judged |
| A value that is an expression (`aria-label={t("x")}`, `alt="{{ a }}"`) | Counts as present with unknown value: it is not a failure and it is not a pass |
| A file that includes other files (`@include`, `{% include %}`, `<x-…>`) or has no `<html>` | An open world: a label, an id or a `<title>` may live elsewhere. A control with a static `id` and no `<label for>` in a file with no includes and no component around it is a **defect** (`control-label-missing-in-file`): the message says the label may live in another file. Inside a component of your own, with an `id` that is an expression, or in a file that includes others, it is `undeterminable` and only the full review lists it |
| A file the tokenizer cannot read | Silence in the light check; «not analysed» with the reason in the review |

## Rules

Kinds: `fail` fails a criterion of WCAG 2.2 by static evidence · `defect` is broken markup with a probable effect · `probable` is a heuristic to look at · `undeterminable` is what the file cannot decide · `recommendation` is a Harness rule WCAG 2.2 does not require.

| Rule | Criteria | Kind | Origin | Light check |
|---|---|---|---|---|
| `area-missing-alt` | 1.1.1 (A) | fail | wcag | yes |
| `button-no-accessible-name` | 4.1.2 (A) | fail | wcag | yes |
| `control-no-accessible-name` | 4.1.2 (A) | fail | wcag | yes |
| `document-missing-title` | 2.4.2 (A) | fail | wcag | yes |
| `html-invalid-lang` | 3.1.1 (A) | fail | wcag | yes |
| `html-missing-lang` | 3.1.1 (A) | fail | wcag | yes |
| `iframe-missing-title` | 4.1.2 (A) | fail | wcag | yes |
| `img-missing-alt` | 1.1.1 (A) | fail | wcag | yes |
| `input-image-missing-alt` | 1.1.1 (A) | fail | wcag | yes |
| `link-no-accessible-name` | 2.4.4 (A), 4.1.2 (A) | fail | wcag | yes |
| `autocomplete-invalid-token` | 1.3.5 (AA) | fail | wcag | no |
| `marquee-or-blink` | 2.2.2 (A) | fail | wcag | no |
| `meta-refresh-delay` | 2.2.1 (A) | fail | wcag | no |
| `password-blocks-paste` | 3.3.8 (AA) | fail | wcag | no |
| `viewport-blocks-zoom` | 1.4.4 (AA) | fail | wcag | no |
| `aria-reference-broken` | 4.1.2 (A) | defect | wcag | yes |
| `aria-reference-no-text` | 4.1.2 (A) | defect | wcag | yes |
| `control-label-missing-in-file` | 4.1.2 (A) | defect | wcag | yes |
| `duplicate-id-referenced` | 1.3.1 (A) | defect | wcag | yes |
| `label-for-broken` | 1.3.1 (A) | defect | wcag | yes |
| `aria-hidden-focusable` | 4.1.2 (A) | defect | wcag | no |
| `autocomplete-missing` | 1.3.5 (AA) | probable | wcag | no |
| `clickable-not-keyboard` | 2.1.1 (A) | probable | wcag | no |
| `control-placeholder-only` | 3.3.2 (A) | probable | obelisco | no |
| `heading-empty` | 2.4.6 (AA) | probable | wcag | no |
| `img-alt-filename` | 1.1.1 (A) | probable | wcag | no |
| `link-generic-text` | 2.4.4 (A) | probable | obelisco | no |
| `media-autoplay` | 1.4.2 (A) | probable | wcag | no |
| `password-autocomplete-off` | 3.3.8 (AA) | probable | wcag | no |
| `tabindex-positive` | 2.4.3 (A) | probable | wcag | no |
| `table-without-headers` | 1.3.1 (A) | probable | wcag | no |
| `video-no-captions` | 1.2.2 (A) | probable | wcag | no |
| `control-name-undeterminable` | 4.1.2 (A) | undeterminable | wcag | no |
| `duplicate-id` | none (Harness recommendation) | recommendation | harness | no |
| `heading-multiple-h1` | none (Harness recommendation) | recommendation | harness | no |
| `heading-no-h1` | none (Harness recommendation) | recommendation | harness | no |
| `heading-skipped-level` | none (Harness recommendation) | recommendation | harness | no |
| `landmark-missing-main` | none (Harness recommendation) | recommendation | harness | no |

## What a machine cannot decide

Contrast of rendered colours, focus order and focus visibility, keyboard operation of scripted widgets, whether an `alt` describes its image, whether a label or a heading is meaningful, reading order after CSS, reflow, text spacing, target size, announcements of a screen reader, timing, consistency across pages. A clean run says only that these rules found nothing: it is never `pass`. The register keeps those criteria `not_tested` until the manual pass that reaches them has been run.
