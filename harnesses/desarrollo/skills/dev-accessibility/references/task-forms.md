# Task: forms

Applies when a change adds or modifies a form, a field, validation, an authentication step or a multi-step process. Criteria of this task: `python scripts/wcag.py task forms`. Components: `wcag.py component form-text` (also `form-select`, `form-check`, `form-radio`, `form-file`, `form-search`, `form-validation`, `form-pattern`, `steps-form`).

## Requirements

| Criterion | Level | Origin | What to do |
|---|---|---|---|
| 1.3.1 Info and Relationships | A | wcag | Every control has a programmatic label; related controls sit in a `fieldset` with a `legend`; `required` and `aria-invalid` are set, not only drawn |
| 3.3.2 Labels or Instructions | A | wcag, obelisco | A visible `<label>` on every field; instructions go before the form; mark required fields with text, not colour alone |
| 2.5.3 Label in Name | A | wcag | The accessible name contains the visible label text — it matters when `aria-label` replaces the label |
| 1.3.5 Identify Input Purpose | AA | wcag | `autocomplete` token on fields that collect data about the user |
| 3.3.1 Error Identification | A | wcag | The error says in text which field and what is wrong |
| 3.3.3 Error Suggestion | AA | wcag, obelisco | Say how to fix it when it is known ("PDF or JPG up to 5 MB", not "invalid format") |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | wcag, obelisco | Review and confirm before a legal, financial or data-changing submission, or make it reversible |
| 3.3.7 Redundant Entry | A | wcag, obelisco | Do not ask again for what the process already has: prefill it or let the user select it |
| 3.3.8 Accessible Authentication (Minimum) | AA | wcag | No cognitive function test without an alternative; allow paste and password managers |
| 3.2.2 On Input | A | wcag, obelisco | Changing a field never changes context (navigates, submits) without warning |
| 4.1.2 Name, Role, Value | A | wcag | A custom control exposes name, role, state and value |
| 4.1.3 Status Messages | AA | wcag | Success and error messages reach the screen reader without taking focus |
| 1.4.1 Use of Color | A | wcag | Errors and required marks are not conveyed by colour only |
| 2.4.6 Headings and Labels | AA | wcag, obelisco | Labels and headings describe the purpose |
| 2.2.1 Timing Adjustable | A | wcag | A session timeout warns and can be extended, unless an exception applies |
| 2.2.5 Re-authenticating | AAA | obelisco | Additional, not AA: after the session expires the user continues without losing data |

## Pattern

```html
<label for="email">Correo electrónico</label>
<input id="email" name="email" type="email" autocomplete="email" required
       aria-describedby="email-help email-error" aria-invalid="true">
<p id="email-help">Como figura en tu DNI digital.</p>
<p id="email-error">Ingresá una dirección con @.</p>
```

On submit with errors, move focus to the first invalid field or to an error summary, or announce through a live region that already exists. Do not rely on a placeholder as a label: Obelisco says it does not replace one.

## How it is verified

- **Static** (light check, `review.py`): `control-no-accessible-name`, `control-label-missing-in-file`, `label-for-broken`, `aria-reference-broken`, `aria-reference-no-text`, `duplicate-id-referenced`, and in the full review `control-placeholder-only`, `autocomplete-invalid-token`, `autocomplete-missing`, `password-blocks-paste`, `password-autocomplete-off`.
- **Manual — keyboard:** tab order follows the reading order, Enter submits, nothing changes context on input.
- **Manual — screen reader:** each field is announced with its label, state and instructions; errors and status messages are announced.
- **Manual — browser:** the label is visible, contrast of text and borders (1.4.3, 1.4.11), and errors are not colour only.
- **No machine reaches:** whether a label's wording is meaningful, whether an error helps, how a timeout behaves.

## Typical failures

A control with an `id` and no `<label for>`; `aria-labelledby` pointing to a missing or empty element; `placeholder` as the only label; an `aria-label` that drops the visible text; an error shown in red only; a CAPTCHA with no alternative; `autocomplete="off"` on a password field.
