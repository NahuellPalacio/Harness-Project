# Task: structure and semantics

Applies when a change adds or modifies a page or a template, headings, landmarks, lists, tables, images, icons, links, navigation, or the language of the content. Criteria: `python scripts/wcag.py task structure-semantics`. Components: `wcag.py component table` (also `cards`, `header`, `footer`, `breadcrumb`, `link`, `nav-horizontal`, `nav-vertical`).

## Requirements

| Criterion | Level | Origin | What to do |
|---|---|---|---|
| 1.1.1 Non-text Content | A | wcag, obelisco | An informative image has an `alt` that does the same job; a decorative one has `alt=""`; an icon that acts has an accessible name. Obelisco cards: informative image or icon gets `alt`, decorative gets it empty. Header logo: `alt` includes «Inicio» |
| 1.3.1 Info and Relationships | A | wcag, obelisco | Headings, lists, tables (`<th scope>`), landmarks and groups are real elements. Obelisco: footer blocks and card groups get an `sr-only` heading when none is visible |
| 1.3.2 Meaningful Sequence | A | wcag | The DOM order is the reading order; CSS reordering does not change the meaning |
| 1.4.5 Images of Text | AA | wcag | Real text, not an image of text, except a logo |
| 2.4.1 Bypass Blocks | A | wcag, obelisco | A skip link or landmarks to jump over repeated blocks |
| 2.4.2 Page Titled | A | wcag | A `<title>` that describes the page |
| 2.4.4 Link Purpose (In Context) | A | wcag, obelisco | The link text says where it goes: not «click aquí» nor «más info». Obelisco asks for an `aria-label` that explains the link |
| 2.4.5 Multiple Ways | AA | wcag | Two or more ways to find a page, except inside a process (applies to the set of pages) |
| 2.4.6 Headings and Labels | AA | wcag, obelisco | Headings and labels describe the topic or purpose. Obelisco's checklist asks for a logical heading hierarchy under this criterion |
| 3.1.1 Language of Page | A | wcag, obelisco | `<html lang="es">` with a valid code |
| 3.1.2 Language of Parts | AA | wcag | A passage in another language carries its own `lang` |
| 4.1.2 Name, Role, Value | A | wcag, obelisco | Native elements first; ARIA only where HTML falls short, and then with its states |
| 2.4.8 Location | AAA | obelisco | Additional, not AA: breadcrumbs or an equivalent say where the user is. Obelisco's breadcrumb page cites it |
| 3.1.5 Reading Level | AAA | obelisco | Additional, not AA: plain language. Obelisco's checklist names it; it is a content judgement, not a markup property |

If an `aria-label` replaces visible text, it must contain that text (2.5.3 Label in Name, Level A).

## Recommendations, not criteria

These are rules of the Harness. WCAG 2.2 does not require them and they are never reported as failures: one `<h1>` per page, a `<main>` landmark, heading levels that do not skip. The full review lists them as `recommendation`, with no criterion.

## How it is verified

- **Static:** `html-missing-lang`, `html-invalid-lang`, `document-missing-title`, `img-missing-alt`, `input-image-missing-alt`, `area-missing-alt`, `button-no-accessible-name`, `link-no-accessible-name`, `iframe-missing-title`; in the full review `img-alt-filename`, `link-generic-text`, `table-without-headers`, `heading-empty`, and the three recommendations above.
- **Manual — screen reader (required):** the page is announced with a sensible title, the heading list reads as an outline, every image and icon is announced or skipped on purpose, links make sense out of context.
- **No machine reaches:** whether an `alt` describes the image, whether a heading describes its section, the reading level.

## Typical failures

`<img>` with no `alt` or with a file name as `alt`; an icon-only button without a name; `<div>` styled as a heading; a table of data without `<th>`; a layout table without `role="presentation"`; «Ver más» ×12 on one page; `<html>` with no `lang`.
