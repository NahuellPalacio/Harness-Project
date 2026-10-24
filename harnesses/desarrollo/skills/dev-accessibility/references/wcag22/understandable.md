# Principle 3: Understandable

> Information and the operation of the user interface must be understandable.

Source of normative text: W3C Recommendation *Web Content Accessibility Guidelines (WCAG) 2.2*, 12 December 2024, https://www.w3.org/TR/WCAG22/. Everything inside a blockquote under "Normative text (verbatim)" is copied from the Recommendation. Everything labeled *informative* (intent, test procedures, examples, code) is guidance derived from the Understanding documents and practice; it does not create requirements.

## Contents

| Guideline / Success Criterion | Level |
|---|---|
| **3.1 Readable** | |
| 3.1.1 Language of Page | A |
| 3.1.2 Language of Parts | AA |
| 3.1.3 Unusual Words | AAA |
| 3.1.4 Abbreviations | AAA |
| 3.1.5 Reading Level | AAA |
| 3.1.6 Pronunciation | AAA |
| **3.2 Predictable** | |
| 3.2.1 On Focus | A |
| 3.2.2 On Input | A |
| 3.2.3 Consistent Navigation | AA |
| 3.2.4 Consistent Identification | AA |
| 3.2.5 Change on Request | AAA |
| 3.2.6 Consistent Help — *New in 2.2* | A |
| **3.3 Input Assistance** | |
| 3.3.1 Error Identification | A |
| 3.3.2 Labels or Instructions | A |
| 3.3.3 Error Suggestion | AA |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA |
| 3.3.5 Help | AAA |
| 3.3.6 Error Prevention (All) | AAA |
| 3.3.7 Redundant Entry — *New in 2.2* | A |
| 3.3.8 Accessible Authentication (Minimum) — *New in 2.2* | AA |
| 3.3.9 Accessible Authentication (Enhanced) — *New in 2.2* | AAA |

Key glossary terms used in this principle (short forms; the full definitions are in `glossary.md`):

- **programmatically determined (programmatically determinable)** — determined by software from author-supplied data provided in a way that different user agents, including assistive technologies, can extract and present this information to users in different modalities.
- **changes of context** — major changes that, if made without user awareness, can disorient users who are not able to view the entire page simultaneously. Changes in context include changes of: user agent; viewport; focus; content that changes the meaning of the web page. A change of *content* (expanding outline, dynamic menu, tab control) is not always a change of *context*.
- **set of web pages** — collection of web pages that share a common purpose and that are created by the same author, group or organization. Different language versions are different sets.
- **same relative order** — same position relative to other items (items can be inserted or removed in between).
- **same functionality** — same result when used.
- **process** — series of user actions where each action is required in order to complete an activity.
- **input error** — information provided by the user that is not accepted, including required information omitted, and information outside the required format or values.
- **legal commitments** — transactions where the person incurs a legally binding obligation or benefit.
- **user-controllable** — data that is intended to be accessed by users (e.g., name and address fields of an account; not logs or analytics).
- **cognitive function test** — a task that requires the user to remember, manipulate, or transcribe information (full verbatim definition under 3.3.8).
- **mechanism** — process or technique for achieving a result; may be provided by the content, the platform or the user agent, and must itself meet the success criteria at the level claimed.
- **human language** — language that is spoken, written or signed (through visual or tactile means) to communicate with humans.

---

## Guideline 3.1 Readable

> Make text content readable and understandable.

### 3.1.1 Language of Page (Level A)

**Normative text (verbatim):**

> The default human language of each web page can be programmatically determined.

**Intent (informative):** Screen readers, braille translators and text-to-speech tools select pronunciation rules, voice and braille tables from the declared language; browsers use it for hyphenation, quotation marks, font selection and translation offers. A page with no language, or the wrong one, is read with the wrong phonetics and becomes unintelligible for blind users and hard for everyone relying on speech or translation.

**How to test:**
1. View source or inspect the DOM: the root `<html>` element must carry a `lang` attribute (in XHTML served as XML also `xml:lang`).
2. The value must be a valid BCP 47 language tag (`es`, `es-AR`, `en`, `pt-BR`); check it is not empty, not a country code alone (`AR`), not a made-up value (`spanish`).
3. The value must match the language of the *majority* of the page content (ignoring isolated foreign phrases, which belong to 3.1.2). A Spanish page with `lang="en"` fails.
4. For PDF, open Document Properties → Advanced → Language (the /Lang entry in the catalog) and check it is set and correct.
5. Pass: a correct, valid, non-empty language is declared on the document root. Fail: missing, invalid, or wrong language.

**Common failures:** No F-technique is listed by the Quick Reference for this criterion. Typical real-world failures (informative): `<html>` with no `lang`; template with `lang="en"` reused on a Spanish site; `lang="es_AR"` with underscore (invalid tag); `lang` set on `<body>` instead of `<html>`.

**Sufficient techniques:**
- H57 Using the language attribute on the HTML element
- PDF16 Setting the default language using the /Lang entry in the document catalog of a PDF document
- PDF19 Specifying the language for a passage or phrase with the Lang entry in PDF documents

**Advisory techniques:**
- SVR5 Specifying the default language in the HTTP header

**Implementation notes (HTML):**
```html
<!doctype html>
<html lang="es-AR">
```
Use the primary language subtag; add a region only when it matters for pronunciation or spelling (`es-AR`, `pt-BR`). Do not rely on `<meta http-equiv="content-language">`; it is not used by assistive technology.

**Related:** 3.1.2 Language of Parts (passages in another language), 1.3.1 (structure), 4.1.2.

---

### 3.1.2 Language of Parts (Level AA)

**Normative text (verbatim):**

> The human language of each passage or phrase in the content can be programmatically determined except for proper names, technical terms, words of indeterminate language, and words or phrases that have become part of the vernacular of the immediately surrounding text.

**Intent (informative):** When a passage switches language (a quotation, a navigation item in another language, a bilingual page), speech synthesizers must switch pronunciation rules or the passage becomes garbled; braille displays must switch contraction tables. Marking the change lets user agents do this automatically. Proper names, loanwords that are now part of the language ("software", "marketing" in Spanish) and technical terms are excepted.

**How to test:**
1. Read the page and list every passage or phrase in a language different from the page language (quotations, embedded content, language switcher links such as "English | Português", parallel translations).
2. Exclude the exceptions: proper names, technical terms, words of indeterminate language, vernacular loanwords.
3. For each remaining passage inspect the DOM: the element containing it, or a wrapping `<span>`/`<blockquote>`/`<p>`, must carry a correct `lang` attribute.
4. In PDF, check that the passage's structure element has a Lang entry.
5. Pass: every non-excepted foreign-language passage has a correct `lang` on an enclosing element. Fail: any passage is missing it or has a wrong tag.

**Common failures:** No F-technique listed. Typical failures (informative): a Spanish site whose language switcher reads "English" without `lang="en"`; a block quotation in Portuguese inside a Spanish article with no `lang`; a bilingual page where only the root language is set.

**Sufficient techniques:**
- H58 Using language attributes to identify changes in the human language
- PDF19 Specifying the language for a passage or phrase with the Lang entry in PDF documents

**Implementation notes (HTML):**
```html
<p>La cita original dice: <q lang="en">The medium is the message</q>.</p>
<ul class="lang-switch">
  <li><a href="/en/" lang="en" hreflang="en">English</a></li>
  <li><a href="/pt/" lang="pt" hreflang="pt">Português</a></li>
</ul>
```
`hreflang` describes the *destination*, not the link text; the `lang` attribute on the link is what makes the text itself pronounceable.

**Related:** 3.1.1 Language of Page, 3.1.6 Pronunciation.

---

### 3.1.3 Unusual Words (Level AAA)

**Normative text (verbatim):**

> A mechanism is available for identifying specific definitions of words or phrases used in an unusual or restricted way, including idioms and jargon.

**Intent (informative):** People with cognitive, language and learning disabilities, people reading in a second language, and people who are deaf and read sign language as a first language can be blocked by idioms, jargon and words used with a specialised meaning. Supplying a definition (inline, linked, or via a glossary) on the page removes the barrier. Glossary definitions relevant here: *idiom* — phrase whose meaning cannot be deduced from the meaning of the individual words; *jargon* — words used in a particular way by people in a particular field; *used in an unusual or restricted way* — words used in such a way that requires users to know exactly which definition to apply.

**How to test:**
1. Identify words and phrases used in an unusual or restricted way, idioms and jargon (domain terminology, legal/administrative terms, internal acronyms-as-words).
2. For each, check that a mechanism gives its definition: an inline definition, a `<dfn>`, a link to a definition or glossary, a description list, or a dictionary search function.
3. If a word has a unique meaning in the page, the definition is needed at least on the first occurrence (via G101 "first occurrence" set) or for every occurrence (via glossary/dictionary). If the same word means different things in the page, every occurrence needs its own definition.
4. Pass: every such term has a reachable definition. Fail: a term relies on prior specialised knowledge with no definition available.

**Common failures:** None listed in the Quick Reference. Typical failures (informative): a government procedure page using "expediente", "caratulación" without any glossary; an idiom in a help text with no explanation.

**Sufficient techniques:**
- Situation A: If the word or phrase has a unique meaning within the web page:
  - G101 Providing the definition of a word or phrase used in an unusual or restricted way — for the first occurrence of the word or phrase in a web page using one of: G55 Linking to definitions; H40 Using description lists; G112 Using inline definitions; H54 Using the dfn element to identify the defining instance of a word or phrase
  - G101 Providing the definition of a word or phrase used in an unusual or restricted way — for each occurrence of the word or phrase in a web page using one of: G55 Linking to definitions; H40 Using description lists; G62 Providing a glossary; G70 Providing a function to search an online dictionary
- Situation B: If the word or phrase means different things within the same web page:
  - G101 Providing the definition of a word or phrase used in an unusual or restricted way — for each occurrence of the word or phrase in a web page using one of: G55 Linking to definitions; H40 Using description lists; G112 Using inline definitions; H54 Using the dfn element to identify the defining instance of a word or phrase

**Implementation notes (HTML):**
```html
<p>El trámite requiere la <dfn id="def-caratulacion">caratulación</dfn>
(asignación de número y carátula al expediente) ...</p>
<!-- later occurrences -->
<a href="#def-caratulacion">caratulación</a>
```

**Related:** 3.1.4 Abbreviations, 3.1.5 Reading Level, 3.1.6 Pronunciation.

---

### 3.1.4 Abbreviations (Level AAA)

**Normative text (verbatim):**

> A mechanism for identifying the expanded form or meaning of abbreviations is available.

**Intent (informative):** Abbreviations, initialisms and acronyms are barriers for people with memory or decoding difficulties, screen-reader users (who hear letters or a mispronounced word) and screen-magnifier users (who cannot scan back to find the expansion). The glossary defines *abbreviation* as a shortened form of a word, phrase, or name where the abbreviation has not become part of the language (so "Ecma" or "laser" need not be expanded).

**How to test:**
1. List abbreviations, initialisms and acronyms on the page that have not become part of the language.
2. For each, check that the expanded form or meaning is available: expansion immediately before/after the first use, `<abbr title>`, a linked definition, a glossary, a dictionary search, or in PDF an E entry.
3. If an abbreviation has one meaning in the page, expansion on the first occurrence (G97/G55/PDF8) or for all occurrences via glossary/dictionary is sufficient. If it has different meanings in the page, each occurrence needs its expansion (G55/PDF8).
4. Pass: every abbreviation has an available expansion. Fail: any abbreviation is left unexplained.

**Common failures:** None listed. Typical (informative): "GCBA", "ASI", "DNI" used throughout a page with no expansion anywhere.

**Sufficient techniques:**
- Situation A: If the abbreviation has only one meaning within the web page:
  - G102 Providing the expansion or explanation of an abbreviation — for the first occurrence using one of: G97 Providing the first use of an abbreviation immediately before or after the expanded form; G55 Linking to definitions; PDF8 Providing definitions for abbreviations via an E entry for a structure element
  - G102 Providing the expansion or explanation of an abbreviation — for all occurrences using one of: G55 Linking to definitions; G62 Providing a glossary; G70 Providing a function to search an online dictionary; PDF8 Providing definitions for abbreviations via an E entry for a structure element
- Situation B: If the abbreviation means different things within the same web page:
  - G102 Providing the expansion or explanation of an abbreviation — for all occurrences using one of: G55 Linking to definitions; PDF8 Providing definitions for abbreviations via an E entry for a structure element

**Advisory techniques:**
- H28 Providing definitions for abbreviations by using the abbr element

**Implementation notes (HTML):**
```html
<p>La Agencia de Sistemas de Información (ASI) ...</p>
<abbr title="Agencia de Sistemas de Información">ASI</abbr>
```
`<abbr title>` alone is advisory because `title` is not reliably exposed on touch and keyboard; prefer the expansion in text on first use.

**Related:** 3.1.3 Unusual Words.

---

### 3.1.5 Reading Level (Level AAA)

**Normative text (verbatim):**

> When text requires reading ability more advanced than the lower secondary education level after removal of proper names and titles, supplemental content, or a version that does not require reading ability more advanced than the lower secondary education level, is available.

**Intent (informative):** Complex text excludes people with reading disabilities (dyslexia), cognitive disabilities, and many deaf readers. The criterion does not require simplifying all text; it requires that when text is harder than the lower secondary level (roughly 7–9 years of schooling, per the UNESCO ISCED definition in the glossary), an easier version or supplemental content (summary, illustrations, audio, sign language) is available.

**How to test:**
1. Determine the page language and remove proper names and titles from a representative sample of text.
2. Apply a readability measure appropriate to the language (for Spanish, e.g., Fernández Huerta / Szigriszt-Pazos; for English, Flesch-Kincaid grade) or expert judgement, to decide whether the text needs more than lower secondary reading ability.
3. If it does, check that one of the following exists: a text summary readable at lower secondary level, illustrations/symbols explaining the ideas, a spoken version, an easier-to-read version, or sign-language versions.
4. Pass: text is at or below lower secondary level, or supplemental/alternative content is available. Fail: complex text with no supplement.

**Common failures:** None listed. Typical (informative): legal/regulatory pages with long sentences and no plain-language summary.

**Sufficient techniques:**
- G86 Providing a text summary that can be understood by people with lower secondary education level reading ability
- G103 Providing visual illustrations, pictures, and symbols to help explain ideas, events, and processes
- G79 Providing a spoken version of the text
- G153 Making the text easier to read
- G160 Providing sign language versions of information, ideas, and processes that must be understood in order to use the content

**Implementation notes:** Put a plain-language summary ("En resumen") at the top of the page, marked up with a heading so it can be found; keep sentences short, one idea per sentence, active voice, common words, and lists for steps.

**Related:** 3.1.3, 3.1.4, 1.2.6 Sign Language, 2.4.6 Headings and Labels.

---

### 3.1.6 Pronunciation (Level AAA)

**Normative text (verbatim):**

> A mechanism is available for identifying specific pronunciation of words where meaning of the words, in context, is ambiguous without knowing the pronunciation.

**Intent (informative):** Some words are spelled identically but mean different things depending on pronunciation (heteronyms such as English "read"/"read", or kanji with multiple readings in Japanese). Screen readers and readers with cognitive disabilities may pick the wrong meaning. The criterion applies only where the meaning is ambiguous *in context*.

**How to test:**
1. Find words whose meaning in context depends on pronunciation and is not resolved by the surrounding text.
2. For each, verify a mechanism gives the pronunciation: pronunciation immediately after the word, a link to a pronunciation, a glossary with pronunciation, diacritics (that can be turned off), or `<ruby>` annotations.
3. Pass: all such words have a pronunciation mechanism. Fail otherwise.

**Common failures:** None listed.

**Sufficient techniques:**
- G120 Providing the pronunciation immediately following the word
- G121 Linking to pronunciations
- G62 Providing a glossary (that includes pronunciation information for words that have a unique pronunciation in the content and have meaning that depends on pronunciation)
- G163 Using standard diacritical marks that can be turned off
- H62 Using the ruby element

**Implementation notes (HTML):**
```html
<ruby>漢<rp>(</rp><rt>kan</rt><rp>)</rp>字<rp>(</rp><rt>ji</rt><rp>)</rp></ruby>
```

**Related:** 3.1.3, 3.1.4, 3.1.2 (correct language is a precondition for correct pronunciation).

---

## Guideline 3.2 Predictable

> Make web pages appear and operate in predictable ways.

### 3.2.1 On Focus (Level A)

**Normative text (verbatim):**

> When any user interface component receives focus, it does not initiate a change of context.

**Intent (informative):** Keyboard and screen-reader users move focus through a page to explore it; if merely landing on a control opens a window, submits a form, moves focus elsewhere or navigates, they lose their place and may be unable to reach the rest of the page. People with cognitive disabilities and low vision (who see only part of the screen) are also disoriented. A change of context must be triggered by activation (Enter, Space, click), not by focus.

**How to test:**
1. Using only the keyboard, Tab (and Shift+Tab) through every focusable component on the page, including custom widgets, and through components inside dialogs, menus and iframes.
2. Observe on each focus arrival: no new window/tab, no form submission, no navigation, no automatic move of focus to another element, no replacement of main content.
3. Also test focus arriving via screen reader virtual cursor / focus mode where custom scripting listens to `focus`/`focusin`.
4. Pass: focus never causes a change of context. Fail: any component triggers one on focus.

**Common failures:**
- F55 Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
- Typical (informative): a `<select>` that navigates on `focus`; a text field whose `onfocus` opens a help popup window; a script that blurs the element as soon as it receives focus.

**Sufficient techniques:**
- G107 Using "activate" rather than "focus" as a trigger for changes of context

**Implementation notes (JS):**
```js
// Wrong: context change on focus
input.addEventListener('focus', () => window.open('/help'));
// Right: on explicit activation
helpButton.addEventListener('click', () => window.open('/help'));
```
Showing a tooltip or a non-modal hint on focus is a change of *content*, not of context, and is allowed (see 1.4.13 for its behaviour).

**Related:** 3.2.2 On Input, 3.2.5 Change on Request, 2.4.3 Focus Order, 2.4.7 Focus Visible.

---

### 3.2.2 On Input (Level A)

**Normative text (verbatim):**

> Changing the setting of any user interface component does not automatically cause a change of context unless the user has been advised of the behavior before using the component.

**Intent (informative):** Selecting a radio button, ticking a checkbox, choosing an option in a select or typing into a field should not, by itself, submit the form, navigate or open a window. Screen-reader users change a `<select>` value with arrow keys while exploring options; an `onchange` navigation fires before they reach the intended option. If such behaviour is needed, the user must be told beforehand (text before the control), or a separate submit control must be used.

**How to test:**
1. For every form control (text inputs, checkboxes, radios, selects, sliders, custom controls), change its value with the keyboard (arrow keys in selects/radios, Space in checkboxes, typing in fields) and with the pointer.
2. Observe whether the change itself causes a change of context (navigation, submission, new window, focus moved elsewhere, main content replaced).
3. If it does, check whether the behaviour is described *before* the control in the reading order (instructions visible and programmatically associated).
4. Pass: no automatic change of context on input, or the user is advised beforehand. Fail: unannounced context change.

**Common failures:**
- F36 Failure of Success Criterion 3.2.2 due to automatically submitting a form and presenting new content without prior warning when the last field in the form is given a value
- F37 Failure of Success Criterion 3.2.2 due to launching a new window without prior warning when the selection of a radio button, check box or select list is changed
- Typical (informative): a "Jump to section" `<select>` that navigates on `change` with no button; a language `<select>` that reloads the page as soon as the value changes.

**Sufficient techniques:**
- G80 Providing a submit button to initiate a change of context — using one of: H32 Providing submit buttons; H84 Using a button with a select element to perform an action; PDF15 Providing submit buttons with the submit-form action in PDF forms
- G13 Describing what will happen before a change to a form control that causes a change of context to occur is made
- SCR19 Using an onchange event on a select element without causing a change of context

**Implementation notes (HTML):**
```html
<label for="lang">Idioma</label>
<select id="lang" name="lang"> ... </select>
<button type="submit">Cambiar idioma</button>
```
Filtering a results list in place (updating content without moving focus) on `change` is allowed; navigating away is not, unless announced first.

**Related:** 3.2.1 On Focus, 3.2.5 Change on Request, 3.3.2 Labels or Instructions.

---

### 3.2.3 Consistent Navigation (Level AA)

**Normative text (verbatim):**

> Navigational mechanisms that are repeated on multiple web pages within a set of web pages occur in the same relative order each time they are repeated, unless a change is initiated by the user.

**Intent (informative):** Users with low vision, cognitive disabilities and screen-reader users build a mental model of where things are; if the header menu, search box or footer links move around between pages, they must relearn the page each time. Items may be added or removed (e.g., a sub-menu appears) as long as the *relative order* of the repeated items stays the same. Users may themselves reorder (e.g., a personalisation setting).

**How to test:**
1. Identify the set of web pages (same purpose, same author/organisation — e.g., the whole site template) and the navigational mechanisms repeated across them: main menu, breadcrumb, utility links, search, footer navigation, skip links.
2. Open several pages of the set (including deep pages and different templates such as listing vs. detail) and compare the order of the repeated items visually and in the DOM/reading order.
3. Confirm that any difference is an insertion/removal (allowed) rather than a reordering, or was initiated by the user.
4. Pass: same relative order everywhere. Fail: repeated navigation in a different order on some pages.

**Common failures:**
- F66 Failure of Success Criterion 3.2.3 due to presenting navigation links in a different relative order on different pages
- Typical (informative): footer links alphabetised on one template and grouped by topic on another; search field before the menu on home and after it on inner pages.

**Sufficient techniques:**
- G61 Presenting repeated components in the same relative order each time they appear

**Advisory techniques:**
- PDF14 Providing running headers and footers in PDF documents
- PDF17 Specifying consistent page numbering for PDF documents

**Implementation notes:** Render navigation from a single shared component/template and keep the DOM order fixed; if CSS reorders items visually per breakpoint, ensure the order is the same for all pages at the same breakpoint.

**Related:** 3.2.4 Consistent Identification, 3.2.6 Consistent Help, 2.4.5 Multiple Ways, 2.4.1 Bypass Blocks.

---

### 3.2.4 Consistent Identification (Level AA)

**Normative text (verbatim):**

> Components that have the same functionality within a set of web pages are identified consistently.

**Intent (informative):** If the same function (search, print, download PDF, "next") is labelled "Buscar" on one page and "Search" or "Ir" on another, or the same icon has different alt text, users who rely on labels (screen-reader, cognitive disabilities, screen-magnifier users) cannot predict what a control does. Consistency covers text labels, accessible names and text alternatives for the same function; different functions may share a label only when their context clearly disambiguates (e.g., "Next" on each of several articles).

**How to test:**
1. Across the set of web pages, collect components with the same functionality: search submit buttons, "print" icons, "download" links, pagination, help/contact, close buttons, social share.
2. Compare their visible labels, accessible names (`alt`, `aria-label`, link text) and icons.
3. Pass: the same function is identified with the same (or consistently equivalent) label/name/icon. Fail: the same function has different labels or alternatives on different pages.

**Common failures:**
- F31 Failure of Success Criterion 3.2.4 due to using two different labels for the same function on different web pages within a set of web pages
- Typical (informative): a PDF icon with `alt="PDF"` on one page and `alt="Descargar"` on another; "Enviar" vs "Submit" on the same form action across pages.

**Sufficient techniques:**
- G197 Using labels, names, and text alternatives consistently for content that has the same functionality — AND following the sufficient techniques for Success Criterion 1.1.1 and sufficient techniques for Success Criterion 4.1.2 for providing labels, names, and text alternatives

**Implementation notes:** Centralise microcopy and icon alternatives (a design-system token or i18n key per function) so that every instance of a function pulls the same label.

**Related:** 3.2.3 Consistent Navigation, 1.1.1 Non-text Content, 4.1.2 Name, Role, Value, 2.4.6 Headings and Labels.

---

### 3.2.5 Change on Request (Level AAA)

**Normative text (verbatim):**

> Changes of context are initiated only by user request or a mechanism is available to turn off such changes.

**Intent (informative):** The AAA counterpart of 3.2.1/3.2.2: *all* changes of context (automatic redirects, auto-refresh, pop-up windows, automatic content replacement) happen only when the user asks for them, or the user can switch them off. This protects people who are easily disoriented and people using screen readers or magnifiers who cannot see that the page changed.

**How to test:**
1. Load pages and wait: no automatic redirect with delay, no auto-refresh, no auto-opening window, no automatic replacement of the main content.
2. Interact with forms and links: new windows open only from controls that say so; removing focus from a field does not change context; typing does not open windows.
3. Where automatic updates exist (news tickers, dashboards), check for a mechanism to turn them off or to request updates manually.
4. Pass: every change of context is user-initiated or can be disabled. Fail otherwise.

**Common failures:**
- F60 Failure of Success Criterion 3.2.5 due to launching a new window when a user enters text into an input field
- F61 Failure of Success Criterion 3.2.5 due to complete change of main content through an automatic update that the user cannot disable from within the content
- F9 Failure of Success Criterion 3.2.5 due to changing the context when the user removes focus from a form element
- F22 Failure of Success Criterion 3.2.5 due to opening windows that are not requested by the user
- F52 Failure of Success Criterion 3.2.5 due to opening a new window as soon as a new page is loaded
- F40 Failure due to using meta redirect with a time limit
- F41 Failure of Success Criterion 2.2.1, 2.2.4, and 3.2.5 due to using meta refresh to reload the page

**Sufficient techniques:**
- Situation A: If the web page allows automatic updates: G76 Providing a mechanism to request an update of the content instead of updating automatically
- Situation B: If automatic redirects are possible: SVR1 Implementing automatic redirects on the server side instead of on the client side; G110 Using an instant client-side redirect — using H76 Using meta refresh to create an instant client-side redirect
- Situation C: If the web page uses pop-up windows: Including pop-up windows — using one of: H83 Using the target attribute to open a new window on user request and indicating this in link text; SCR24 Using progressive enhancement to open new windows on user request
- Situation D: If using an onchange event on a select element: SCR19 Using an onchange event on a select element without causing a change of context

**Advisory techniques:**
- G200 Opening new windows and tabs from a link only when necessary
- G201 Giving users advanced warning when opening a new window

**Implementation notes (HTML):**
```html
<a href="https://ejemplo.gob.ar" target="_blank" rel="noopener">
  Portal de trámites <span class="visually-hidden">(se abre en una ventana nueva)</span>
</a>
```
Redirect on the server with HTTP 301/302, or `<meta http-equiv="refresh" content="0;url=...">` (instant, no delay) if server-side is impossible.

**Related:** 3.2.1, 3.2.2, 2.2.1 Timing Adjustable, 2.2.4 Interruptions.

---

### 3.2.6 Consistent Help (Level A) — New in WCAG 2.2

**Normative text (verbatim):**

> If a web page contains any of the following help mechanisms, and those mechanisms are repeated on multiple web pages within a set of web pages, they occur in the same order relative to other page content, unless a change is initiated by the user:
>
> - Human contact details;
> - Human contact mechanism;
> - Self-help option;
> - A fully automated contact mechanism.
>
> NOTE 1
>
> Help mechanisms may be provided directly on the page, or may be provided via a direct link to a different page containing the information.
>
> NOTE 2
>
> For this success criterion, "the same order relative to other page content" can be thought of as how the content is ordered when the page is serialized. The visual position of a help mechanism is likely to be consistent across pages for the same page variation (e.g., CSS break-point). The user can initiate a change, such as changing the page's zoom or orientation, which may trigger a different page variation. This criterion is concerned with relative order across pages displayed in the same page variation (e.g., same zoom level and orientation).

**Intent (informative):** People with cognitive disabilities, and anyone who gets stuck, need to find help quickly and in the same place every time. The criterion does *not* require that help be provided; it requires that when a help mechanism (phone number, email/contact form, chat with a human, FAQ or help page, chatbot) is present on several pages of a set, it is in the same relative position in each. Examples of the four types: human contact details (phone, email, hours); human contact mechanism (contact form, messaging, live chat with a person); self-help option (FAQ, help centre, how-to); fully automated contact mechanism (chatbot).

**How to test:**
1. Identify the set of web pages and any of the four help mechanism types present (directly on the page or as a link to a page with that information).
2. For each page in the set where a given mechanism is repeated, compare its location in the serialized (DOM/reading) order relative to other page content — e.g., "last item in the header utility bar", "first block in the footer".
3. Test at the same page variation (same breakpoint/zoom/orientation) across pages; a change the user initiated (zoom, orientation) that triggers a different variation is not a failure.
4. Pass: each repeated help mechanism keeps the same relative order across the set. Fail: a help link/widget appears in the header on some pages and in the footer on others, or its order among neighbouring content changes.

**Common failures:** The Quick Reference lists "Inconsistent Help Location" (no F-id yet). Typical (informative): a "Contacto" link in the top bar on the home page but only in the footer on inner pages; a chat widget launcher that is the last element on some pages and before the footer on others.

**Sufficient techniques:**
- G220 Provide a contact-us link in a consistent location

**Implementation notes:** Place help mechanisms in a shared layout component (site header or footer) rendered identically on every template; if a page type legitimately has no help, that is fine — the criterion only governs pages where the mechanism is repeated.

**Related:** 3.2.3 Consistent Navigation, 3.3.5 Help, 3.2.4 Consistent Identification.

---
## Guideline 3.3 Input Assistance

> Help users avoid and correct mistakes.

### 3.3.1 Error Identification (Level A)

**Normative text (verbatim):**

> If an input error is automatically detected, the item that is in error is identified and the error is described to the user in text.

**Intent (informative):** When validation finds a problem, users must be able to find *which* field is wrong and *what* is wrong, in text. Colour alone (a red border), an icon alone, or a generic "There are errors" message is not perceivable by screen-reader users, people with colour-vision deficiency or people with cognitive disabilities. "Input error" covers both required information that was omitted and information outside the required format or values.

**How to test:**
1. Submit forms empty and with invalid values (wrong format, out-of-range, not in the allowed list) to trigger every automatic validation, client-side and server-side.
2. For each detected error check: (a) the field in error is identified — by name in a message, by a message adjacent to and programmatically associated with the field, and/or by `aria-invalid="true"`; (b) the error is described in text (what is wrong, e.g., "El correo electrónico debe contener @"), not only by colour, icon or border.
3. With a screen reader, verify the error text is announced when focus moves to the field (via `aria-describedby`) or when the message appears (live region / focus move to summary).
4. Pass: every detected error identifies the item and describes the error in text. Fail: red outline only, generic "form invalid", or a message that does not say which field.

**Common failures:** No F-technique listed for 3.3.1 in the Quick Reference (colour-only indication fails 1.4.1 via F81). Typical (informative): only a red border around the field; a toast "Revise los datos" without naming the field; error text inserted visually but not associated to the field and not announced.

**Sufficient techniques:**
- Situation A: If a form contains fields for which information from the user is mandatory:
  - G83 Providing text descriptions to identify required fields that were not completed
  - ARIA21 Using aria-invalid to Indicate An Error Field
  - SCR18 Providing client-side validation and alert
  - PDF5 Indicating required form controls in PDF forms
- Situation B: If information provided by the user is required to be in a specific data format or of certain values:
  - ARIA18 Using aria-alertdialog to Identify Errors
  - ARIA19 Using ARIA role=alert or Live Regions to Identify Errors
  - ARIA21 Using aria-invalid to Indicate An Error Field
  - G84 Providing a text description when the user provides information that is not in the list of allowed values
  - G85 Providing a text description when user input falls outside the required format or values
  - SCR18 Providing client-side validation and alert
  - SCR32 Providing client-side validation and adding error text via the DOM
  - PDF22 Indicating when user input falls outside the required format or values in PDF forms

**Advisory techniques:**
- G139 Creating a mechanism that allows users to jump to errors
- G199 Providing success feedback when data is submitted successfully
- ARIA2 Identifying a required field with the aria-required property

**Implementation notes (HTML/ARIA):**
```html
<label for="email">Correo electrónico</label>
<input id="email" name="email" type="email" autocomplete="email"
       aria-invalid="true" aria-describedby="email-error">
<p id="email-error" class="error">Error: el correo electrónico debe incluir una @ (ejemplo: nombre@dominio.com).</p>
```
On submit with errors, either move focus to the first invalid field or to an error summary (`<div role="alert">` or a focusable heading) that lists each error as a link to the field.

**Related:** 3.3.3 Error Suggestion, 3.3.2 Labels or Instructions, 1.4.1 Use of Color, 4.1.3 Status Messages, 1.3.1.

---

### 3.3.2 Labels or Instructions (Level A)

**Normative text (verbatim):**

> Labels or instructions are provided when content requires user input.

**Intent (informative):** Every input needs a visible label or instruction that tells the user what to enter and in what format, before they make a mistake. This helps people with cognitive, language and memory disabilities and screen-reader users (who need the label programmatically associated — the association itself is tested under 1.3.1 and 4.1.2; this criterion requires that the label/instruction exists and is adequate). It does not require excessive instructions: a label such as "Fecha de nacimiento (DD/MM/AAAA)" is usually enough. *Label* (glossary): text or other component with a text alternative that is presented to a user to identify a component within web content.

**How to test:**
1. For each form control (including search boxes, filters, custom controls and each part of multi-part fields such as day/month/year or phone segments) check that a visible label or instruction identifies what the user must enter.
2. Where a format or constraint exists (date format, password rules, required fields, allowed values, units), check that it is stated in the label or instructions *before* the user enters data, and that required fields are indicated in text or a consistently explained symbol.
3. Check group controls (radio/checkbox groups) have a group label (legend or equivalent).
4. Placeholder text is not a sufficient label (disappears on input, low contrast); a `title` tooltip alone is weak. Prefer a visible persistent label.
5. Pass: every input has a visible label or instructions adequate to understand the required input. Fail: unlabelled fields, placeholder-only labels, constraints revealed only after error.

**Common failures:**
- F82 Failure of Success Criterion 3.3.2 by visually formatting a set of phone number fields but not including a text label
- Typical (informative): a search input with only a magnifier icon and no name; three date boxes with no label; a password field that reveals its rules only after rejection.

**Sufficient techniques:**
- G131 Providing descriptive labels — AND one of: ARIA1 Using the aria-describedby property to provide a descriptive label for user interface controls; ARIA9 Using aria-labelledby to concatenate a label from several text nodes; ARIA17 Using grouping roles to identify related form controls; G89 Providing expected data format and example; G184 Providing text instructions at the beginning of a form or set of fields that describes the necessary input; G162 Positioning labels to maximize predictability of relationships; G83 Providing text descriptions to identify required fields that were not completed; H90 Indicating required form controls using label or legend; PDF5 Indicating required form controls in PDF forms
- H44 Using label elements to associate text labels with form controls
- PDF10 Providing labels for interactive form controls in PDF documents
- H71 Providing a description for groups of form controls using fieldset and legend elements
- G167 Using an adjacent button to label the purpose of a field

**Advisory techniques:**
- G13 Describing what will happen before a change to a form control that causes a change of context to occur is made
- ARIA2 Identifying a required field with the aria-required property

**Implementation notes (HTML):**
```html
<p id="form-hint">Los campos marcados con * son obligatorios.</p>
<label for="dni">DNI * <span class="hint">(solo números, sin puntos)</span></label>
<input id="dni" name="dni" inputmode="numeric" required aria-describedby="form-hint">

<fieldset>
  <legend>Fecha de nacimiento (día, mes, año)</legend>
  <label for="d">Día</label><input id="d" ...>
  <label for="m">Mes</label><input id="m" ...>
  <label for="y">Año</label><input id="y" ...>
</fieldset>
```

**Related:** 1.3.1 Info and Relationships, 2.4.6 Headings and Labels, 2.5.3 Label in Name, 4.1.2 Name, Role, Value, 3.3.1, 3.3.5 Help.

---

### 3.3.3 Error Suggestion (Level AA)

**Normative text (verbatim):**

> If an input error is automatically detected and suggestions for correction are known, then the suggestions are provided to the user, unless it would jeopardize the security or purpose of the content.

**Intent (informative):** Knowing *that* a field is wrong (3.3.1) is not always enough; when the system knows how to fix it (expected format, allowed values, a close match), it should say so. This helps users with cognitive, learning and motor disabilities who otherwise retry repeatedly. The exception covers cases where suggestions would reveal security information (e.g., "the password is wrong, the username exists") or defeat the purpose (a quiz answer).

**How to test:**
1. Trigger each validation error where the system could know a correction: wrong date format, value outside a range, value not in an allowed list, misspelled city/province, wrong number of digits.
2. Check that the error text includes a suggestion: the expected format with an example, the allowed range or list, or the likely intended value.
3. Confirm no suggestion is given where it would compromise security or purpose (login, security questions, test answers) — that is allowed.
4. Pass: suggestions are provided whenever known and safe. Fail: "Valor inválido" with no hint when the expected format is known.

**Common failures:** None listed in the Quick Reference. Typical (informative): "Fecha inválida" instead of "Fecha inválida. Use el formato DD/MM/AAAA, por ejemplo 23/10/2026"; "Código postal incorrecto" without stating it must be 4 digits.

**Sufficient techniques:**
- Situation A: If information for a field is required to be in a specific data format: ARIA18 Using aria-alertdialog to Identify Errors; G85 Providing a text description when user input falls outside the required format or values; G177 Providing suggested correction text; PDF22 Indicating when user input falls outside the required format or values in PDF forms
- Situation B: Information provided by the user is required to be one of a limited set of values: ARIA18 Using aria-alertdialog to Identify Errors; G84 Providing a text description when the user provides information that is not in the list of allowed values; G177 Providing suggested correction text; PDF22 Indicating when user input falls outside the required format or values in PDF forms

**Advisory techniques:**
- G139 Creating a mechanism that allows users to jump to errors
- G199 Providing success feedback when data is submitted successfully
- SCR18 Providing client-side validation and alert
- SCR32 Providing client-side validation and adding error text via the DOM

**Implementation notes:** Write error messages as "what is wrong + how to fix it", e.g. `El CUIT debe tener 11 dígitos sin guiones (ejemplo: 20123456789).` Keep them in the same `aria-describedby` message as the identification.

**Related:** 3.3.1 Error Identification, 3.3.2, 3.3.4, 3.3.5 Help.

---

### 3.3.4 Error Prevention (Legal, Financial, Data) (Level AA)

**Normative text (verbatim):**

> For web pages that cause legal commitments or financial transactions for the user to occur, that modify or delete user-controllable data in data storage systems, or that submit user test responses, at least one of the following is true:
>
> Reversible
> Submissions are reversible.
>
> Checked
> Data entered by the user is checked for input errors and the user is provided an opportunity to correct them.
>
> Confirmed
> A mechanism is available for reviewing, confirming, and correcting information before finalizing the submission.

**Intent (informative):** Mistakes in high-stakes transactions (paying, signing, deleting an account, submitting an exam) can have serious consequences and may be hard to notice for people with disabilities. Pages that cause such actions must give a safety net: the action can be undone within a stated period, or the data is validated and correctable, or there is a review-and-confirm step. *Legal commitments* (glossary): transactions where the person incurs a legally binding obligation or benefit. *User-controllable* data: data intended to be accessed by users, such as account name and address.

**How to test:**
1. Identify pages/steps that: cause a legal commitment (sign, accept terms, file a declaration); make a financial transaction (pay, transfer); modify or delete user-controllable stored data (profile, saved records, account deletion); or submit test responses.
2. For each, verify at least one of: (Reversible) the submission can be undone/cancelled within a stated time; (Checked) input is validated for errors and the user can correct before finalising; (Confirmed) a review screen or confirmation dialog shows the data and allows correction before final submission.
3. For deletion, check for an undo/recover option or a confirmation step.
4. Pass: at least one of the three conditions holds for every such page. Fail: a one-click irreversible purchase, deletion without confirmation, or a test submitted with no review.

**Common failures:** None listed in the Quick Reference. Typical (informative): "Eliminar cuenta" executes immediately on click; a payment form submits on the last field without a summary; a quiz auto-submits when the last answer is chosen.

**Sufficient techniques:**
- Situation A: If an application causes a legal transaction to occur, such as making a purchase or submitting an income tax return: G164 Providing a stated time within which an online request (or transaction) may be amended or canceled by the user after making the request; G98 Providing the ability for the user to review and correct answers before submitting; G155 Providing a checkbox in addition to a submit button
- Situation B: If an action causes information to be deleted: G99 Providing the ability to recover deleted information; G168 Requesting confirmation to continue with selected action; G155 Providing a checkbox in addition to a submit button
- Situation C: If the web page includes a testing application: G98 Providing the ability for the user to review and correct answers before submitting; G168 Requesting confirmation to continue with selected action

**Advisory techniques:**
- SCR18 Providing client-side validation and alert
- G199 Providing success feedback when data is submitted successfully

**Implementation notes (HTML):**
```html
<!-- Review step before final submission -->
<h2>Revise sus datos antes de confirmar</h2>
<dl> ... datos ingresados ... </dl>
<a href="/paso-1">Corregir</a>
<button type="submit">Confirmar y enviar</button>
```
For destructive actions use a modal confirmation dialog (`<dialog>` / `role="alertdialog"`) that names the item to delete, and/or offer undo for a stated period.

**Related:** 3.3.6 Error Prevention (All), 3.3.1, 3.3.3, 2.2.1 Timing Adjustable, 2.2.5 Re-authenticating.

---

### 3.3.5 Help (Level AAA)

**Normative text (verbatim):**

> Context-sensitive help is available.

**Intent (informative):** Help that relates to the task at hand (how to fill in this field, what this form is for, where to get assistance) reduces errors for people with cognitive, language and learning disabilities. *Context-sensitive help* (glossary): help text that provides information related to the function currently being performed; clear labels can act as context-sensitive help.

**How to test:**
1. For each form or task requiring text input, check whether help relevant to the current function is available: instructions at the start of the form, per-field hints, expected format with example, a help link on every page, an in-page assistant, spell checking for free text.
2. Help must be reachable without leaving the task (link, expandable hint, tooltip exposed to keyboard and AT).
3. Pass: context-sensitive help is available for the input being performed. Fail: no help beyond bare labels where the input is non-obvious.

**Common failures:** None listed.

**Sufficient techniques:**
- Situation A: If a form requires text input: G71 Providing a help link on every web page; G193 Providing help by an assistant in the web page; G194 Providing spell checking and suggestions for text input; G184 Providing text instructions at the beginning of a form or set of fields that describes the necessary input
- Situation B: If a form requires text input in an expected data format: G89 Providing expected data format and example; G184 Providing text instructions at the beginning of a form or set of fields that describes the necessary input

**Advisory techniques:**
- H89 Using the title attribute to provide context-sensitive help

**Implementation notes (HTML):**
```html
<label for="cuil">CUIL</label>
<input id="cuil" aria-describedby="cuil-help">
<p id="cuil-help">11 dígitos sin guiones. <a href="/ayuda/cuil">¿Dónde encuentro mi CUIL?</a></p>
```

**Related:** 3.3.2 Labels or Instructions, 3.2.6 Consistent Help, 3.3.3 Error Suggestion.

---

### 3.3.6 Error Prevention (All) (Level AAA)

**Normative text (verbatim):**

> For web pages that require the user to submit information, at least one of the following is true:
>
> Reversible
> Submissions are reversible.
>
> Checked
> Data entered by the user is checked for input errors and the user is provided an opportunity to correct them.
>
> Confirmed
> A mechanism is available for reviewing, confirming, and correcting information before finalizing the submission.

**Intent (informative):** Extends 3.3.4 from high-stakes transactions to *every* form that submits information: any submission should be reversible, validated with a chance to correct, or confirmable.

**How to test:**
1. Identify every page that requires the user to submit information (contact forms, comments, searches with side effects, settings).
2. Apply the 3.3.4 test (Reversible / Checked / Confirmed) to each.
3. Pass: one condition holds for all forms. Fail: any form submits without validation, confirmation or reversibility.

**Common failures:** None listed.

**Sufficient techniques:**
- Following the sufficient techniques for Success Criterion 3.3.4 for all forms that require the user to submit information

**Implementation notes:** Client-side validation with correctable errors (Checked) is the lightest way to satisfy this for low-risk forms.

**Related:** 3.3.4, 3.3.1, 3.3.3.

---

### 3.3.7 Redundant Entry (Level A) — New in WCAG 2.2

**Normative text (verbatim):**

> Information previously entered by or provided to the user that is required to be entered again in the same process is either:
>
> - auto-populated, or
> - available for the user to select.
>
> Except when:
>
> - re-entering the information is essential,
> - the information is required to ensure the security of the content, or
> - previously entered information is no longer valid.

**Intent (informative):** Re-typing information already given in the same process (name, address, email across steps of a form; billing address again as shipping address) is a memory and dexterity burden for people with cognitive disabilities, motor impairments and screen-reader users. Within a *process* (a sequence of steps required to complete an activity) the information must be pre-filled or offered for selection (e.g., "Usar la misma dirección"). Exceptions: when re-entry is essential (re-typing a new password to confirm it), security (re-entering a password before a sensitive action, a one-time code), or the earlier value is no longer valid. The criterion covers the *same process*; it does not require remembering data across separate sessions or processes (though doing so is good practice). The spec lists this criterion under Privacy and Security considerations.

**How to test:**
1. Walk every multi-step process (registration, checkout, application wizard, multi-page form) as a user, entering data in each step.
2. Note any field that asks for information already entered or provided earlier in the same process (including after navigating back and forward, or after a validation error returns the user to an earlier step — data must persist).
3. Check that such fields are auto-populated or that the previous value is available to select (checkbox "same as…", dropdown of previous entries).
4. Confirm that any required re-entry falls under an exception: essential (password confirmation, a signature, a declaration that must be typed), security (password/OTP re-entry), or the earlier value is no longer valid.
5. Pass: no non-excepted redundant entry. Fail: the user must re-type data from a previous step.

**Common failures:** No F-technique listed. Typical (informative): checkout asks for billing and shipping address with no "same as billing" option; a wizard loses entered data when the user goes back one step; an email entered in step 1 must be typed again in step 3.

**Sufficient techniques:**
- G221 Provide data from a previous step in a process
- Not requesting the same information twice (Potential future technique)

**Implementation notes (HTML/JS):**
```html
<label><input type="checkbox" id="same-as-billing"> La dirección de envío es igual a la de facturación</label>
```
Persist step data in session/state and prefill fields (`value="..."`) on later steps; keep data when the user navigates back.

**Related:** 3.3.8 Accessible Authentication (both reduce cognitive load), 1.3.5 Identify Input Purpose (browser autofill), 2.2.5 Re-authenticating.

---

### 3.3.8 Accessible Authentication (Minimum) (Level AA) — New in WCAG 2.2

**Normative text (verbatim):**

> A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:
>
> Alternative
> Another authentication method that does not rely on a cognitive function test.
>
> Mechanism
> A mechanism is available to assist the user in completing the cognitive function test.
>
> Object Recognition
> The cognitive function test is to recognize objects.
>
> Personal Content
> The cognitive function test is to identify non-text content the user provided to the website.
>
> NOTE 1
>
> "Object recognition" and "Personal content" may be represented by images, video, or audio.
>
> NOTE 2
>
> Examples of mechanisms that satisfy this criterion include:
>
> - support for password entry by password managers to reduce memory need, and
> - copy and paste to reduce the cognitive burden of re-typing.

Glossary — **cognitive function test** (verbatim):

> A task that requires the user to remember, manipulate, or transcribe information. Examples include, but are not limited to:
>
> - memorization, such as remembering a username, password, set of characters, images, or patterns. The common identifiers name, e-mail, and phone number are not considered cognitive function tests as they are personal to the user and consistent across websites;
> - transcription, such as typing in characters;
> - use of correct spelling;
> - performance of calculations;
> - solving of puzzles.

**Intent (informative):** Logging in must not depend on memorising or transcribing information, or solving puzzles, because that excludes people with cognitive disabilities (memory, dyslexia, dyscalculia, attention). Remembering a password *is* a cognitive function test; it becomes acceptable when a mechanism helps (password managers can fill it, copy-paste is allowed) or an alternative exists (email magic link, passkey/WebAuthn, OAuth third-party login, device biometrics). Transcribing a code sent by SMS/email is a cognitive function test unless it can be pasted or auto-filled. Object-recognition CAPTCHAs ("select the images with buses") and personal-content checks (identify the photo you uploaded) are allowed at AA; text-distortion CAPTCHAs and arithmetic puzzles are not (unless an alternative or assisting mechanism exists). Listed in the spec's Security considerations.

**How to test:**
1. Map every step of each authentication process (login, re-authentication, 2FA/MFA, password reset, account recovery, "verify you are human" steps).
2. For each step determine whether it requires a cognitive function test: remembering a username/password/PIN/pattern, transcribing characters or codes, correct spelling, calculations, puzzles. (Name, email and phone number do not count.)
3. For each step that does, verify at least one of: **Alternative** (another method without a cognitive function test — passkey, magic link, OAuth, biometric); **Mechanism** (password manager can fill the fields — correct `autocomplete` values, no blocking of paste, no custom fields that defeat autofill; copy-paste is allowed into password/OTP fields); **Object Recognition** (the test is to recognise objects); **Personal Content** (the test identifies non-text content the user provided).
4. Concretely: attempt to paste into the password and code fields; check `autocomplete="username"`, `"current-password"`, `"new-password"`, `"one-time-code"`; check that the username field is not a custom widget; check CAPTCHA type.
5. Pass: every step with a cognitive function test satisfies one of the four conditions. Fail: paste blocked on password/OTP fields, a text-distortion or arithmetic CAPTCHA with no alternative, a required pattern/memory game with no alternative.

**Common failures:**
- F109 Failure of Success Criterion 3.3.8 and 3.3.9 due to preventing password or code re-entry in the same format
- Typical (informative): `onpaste="return false"` on the password field; a one-time code split into six boxes that reject paste; a distorted-text CAPTCHA as the only path; `autocomplete="off"` on login fields combined with autofill-breaking markup.

**Sufficient techniques:**
- G218 Email link authentication
- H100 Providing properly marked up email and password inputs
- Providing WebAuthn as an alternative to username/password (Potential future technique)
- Providing a third-party login using OAuth (Potential future technique)
- Using two techniques to provide two-factor authentication (Potential future technique)

**Implementation notes (HTML):**
```html
<form action="/login" method="post">
  <label for="user">Correo electrónico</label>
  <input id="user" name="user" type="email" autocomplete="username" required>
  <label for="pass">Contraseña</label>
  <input id="pass" name="pass" type="password" autocomplete="current-password" required>
  <button type="submit">Ingresar</button>
  <p><a href="/login/enlace">Recibir un enlace de acceso por correo</a></p>
</form>
<!-- One-time code: a single field that accepts paste and autofill -->
<input name="otp" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}">
```
Never block paste or drag-and-drop; do not use `autocomplete="off"` on credential fields; if a CAPTCHA is unavoidable use an object-recognition one or provide an alternative path.

**Related:** 3.3.9 Accessible Authentication (Enhanced), 1.1.1 (CAPTCHA alternatives), 1.3.5 Identify Input Purpose, 2.2.5 Re-authenticating, 3.3.7 Redundant Entry.

---

### 3.3.9 Accessible Authentication (Enhanced) (Level AAA) — New in WCAG 2.2

**Normative text (verbatim):**

> A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:
>
> Alternative
> Another authentication method that does not rely on a cognitive function test.
>
> Mechanism
> A mechanism is available to assist the user in completing the cognitive function test.

**Intent (informative):** Same as 3.3.8 but without the Object Recognition and Personal Content exceptions: at AAA, even image-recognition CAPTCHAs and "pick your uploaded photo" checks are not acceptable unless an alternative method or an assisting mechanism exists. Listed in the spec's Security considerations.

**How to test:**
1. Repeat the 3.3.8 procedure for every authentication step.
2. For each cognitive function test, accept only **Alternative** or **Mechanism**; object-recognition and personal-content tests do not pass on their own.
3. Pass: every step offers an alternative without a cognitive function test, or a mechanism that assists (password manager support, copy-paste). Fail: any CAPTCHA (including image recognition) or memory test as the only path.

**Common failures:**
- F109 Failure of Success Criterion 3.3.8 and 3.3.9 due to preventing password or code re-entry in the same format

**Sufficient techniques:**
- G218 Email link authentication
- H100 Providing properly marked up email and password inputs
- Providing WebAuthn as an alternative to username/password (Potential future technique)
- Providing a third-party login using OAuth (Potential future technique)
- Using two techniques to provide two-factor authentication (Potential future technique)

**Implementation notes:** Offer passkeys (WebAuthn) or a magic link as a first-class option alongside password login; keep all password and code fields paste-friendly and autofill-friendly.

**Related:** 3.3.8 Accessible Authentication (Minimum), 1.1.1, 2.2.5.
