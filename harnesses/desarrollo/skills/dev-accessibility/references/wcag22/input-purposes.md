# WCAG 2.2 Section 7 — Input Purposes for User Interface Components

Source: Web Content Accessibility Guidelines (WCAG) 2.2, W3C Recommendation 12 December 2024, https://www.w3.org/TR/WCAG22/#input-purposes. This section is **normative**: it is the list that Success Criterion 1.3.5 Identify Input Purpose (Level AA) refers to when it says "a purpose identified in the Input Purposes for user interface components section". The introduction, NOTE and all 53 purposes are reproduced verbatim. The mapping to HTML `autocomplete` at the end is informative guidance added for this skill.

---

## 7. Input Purposes for User Interface Components (verbatim)

This section contains a listing of common user interface component input purposes. The terms below are not keywords that must be used, but instead represent purposes that must be captured in the taxonomy adopted by a webpage. Where applicable, authors mark up controls with the chosen taxonomy to indicate the semantic purpose. This provides the potential for user agents and assistive technologies to apply personalized presentations that can enable more people to understand and use the content.

NOTE: The list of input type purposes is based on the control purposes defined in the HTML specification's Autofill section, but it is important to understand that a different technology may have some or all of the same concepts defined in its specification and only the concepts that are mapped to the meanings below are required.

The following input control purposes are intended to relate to the user of the content and pertain only to information related to that individual.

| # | token | purpose |
|---|-------|---------|
| 1 | `name` | Full name |
| 2 | `honorific-prefix` | Prefix or title (e.g., "Mr.", "Ms.", "Dr.", "Mlle") |
| 3 | `given-name` | Given name (in some Western cultures, also known as the first name) |
| 4 | `additional-name` | Additional names (in some Western cultures, also known as middle names, forenames other than the first name) |
| 5 | `family-name` | Family name (in some Western cultures, also known as the last name or surname) |
| 6 | `honorific-suffix` | Suffix (e.g., "Jr.", "B.Sc.", "MBASW", "II") |
| 7 | `nickname` | Nickname, screen name, handle: a typically short name used instead of the full name |
| 8 | `organization-title` | Job title (e.g., "Software Engineer", "Senior Vice President", "Deputy Managing Director") |
| 9 | `username` | A username |
| 10 | `new-password` | A new password (e.g., when creating an account or changing a password) |
| 11 | `current-password` | The current password for the account identified by the username field (e.g., when logging in) |
| 12 | `organization` | Company name corresponding to the person, address, or contact information in the other fields associated with this field |
| 13 | `street-address` | Street address (multiple lines, newlines preserved) |
| 14 | `address-line1` | Street address (one line per field, line 1) |
| 15 | `address-line2` | Street address (one line per field, line 2) |
| 16 | `address-line3` | Street address (one line per field, line 3) |
| 17 | `address-level4` | The most fine-grained administrative level, in addresses with four administrative levels |
| 18 | `address-level3` | The third administrative level, in addresses with three or more administrative levels |
| 19 | `address-level2` | The second administrative level, in addresses with two or more administrative levels; in the countries with two administrative levels, this would typically be the city, town, village, or other locality within which the relevant street address is found |
| 20 | `address-level1` | The broadest administrative level in the address, i.e., the province within which the locality is found; for example, in the US, this would be the state; in Switzerland it would be the canton; in the UK, the post town |
| 21 | `country` | Country code |
| 22 | `country-name` | Country name |
| 23 | `postal-code` | Postal code, post code, ZIP code, CEDEX code (if CEDEX, append "CEDEX", and the arrondissement, if relevant, to the address-level2 field) |
| 24 | `cc-name` | Full name as given on the payment instrument |
| 25 | `cc-given-name` | Given name as given on the payment instrument (in some Western cultures, also known as the first name) |
| 26 | `cc-additional-name` | Additional names given on the payment instrument (in some Western cultures, also known as middle names, forenames other than the first name) |
| 27 | `cc-family-name` | Family name given on the payment instrument (in some Western cultures, also known as the last name or surname) |
| 28 | `cc-number` | Code identifying the payment instrument (e.g., the credit card number) |
| 29 | `cc-exp` | Expiration date of the payment instrument |
| 30 | `cc-exp-month` | Month component of the expiration date of the payment instrument |
| 31 | `cc-exp-year` | Year component of the expiration date of the payment instrument |
| 32 | `cc-csc` | Security code for the payment instrument (also known as the card security code (CSC), card validation code (CVC), card verification value (CVV), signature panel code (SPC), credit card ID (CCID), etc) |
| 33 | `cc-type` | Type of payment instrument |
| 34 | `transaction-currency` | The currency that the user would prefer the transaction to use |
| 35 | `transaction-amount` | The amount that the user would like for the transaction (e.g., when entering a bid or sale price) |
| 36 | `language` | Preferred language |
| 37 | `bday` | Birthday |
| 38 | `bday-day` | Day component of birthday |
| 39 | `bday-month` | Month component of birthday |
| 40 | `bday-year` | Year component of birthday |
| 41 | `sex` | Gender identity (e.g., Female, Fa'afafine) |
| 42 | `url` | Home page or other web page corresponding to the company, person, address, or contact information in the other fields associated with this field |
| 43 | `photo` | Photograph, icon, or other image corresponding to the company, person, address, or contact information in the other fields associated with this field |
| 44 | `tel` | Full telephone number, including country code |
| 45 | `tel-country-code` | Country code component of the telephone number |
| 46 | `tel-national` | Telephone number without the country code component, with a country-internal prefix applied if applicable |
| 47 | `tel-area-code` | Area code component of the telephone number, with a country-internal prefix applied if applicable |
| 48 | `tel-local` | Telephone number without the country code and area code components |
| 49 | `tel-local-prefix` | First part of the component of the telephone number that follows the area code, when that component is split into two components |
| 50 | `tel-local-suffix` | Second part of the component of the telephone number that follows the area code, when that component is split into two components |
| 51 | `tel-extension` | Telephone number internal extension code |
| 52 | `email` | E-mail address |
| 53 | `impp` | URL representing an instant messaging protocol endpoint (for example, "aim:goim?screenname=example" or "xmpp:fred@example.net") |

---

## Mapping to the HTML `autocomplete` attribute (informative)

### Scope of 1.3.5 — the two conditions

Success Criterion 1.3.5 only applies when **both** of these hold:

1. The field collects information **about the user** (the person filling in the form) and that information matches one of the 53 purposes above. A "Recipient's name" field on a gift form, an "Employee being reported" field on an HR form, or a search box are *not* about the user and are out of scope, even though they are names or free text. The list is deliberately limited to things that are personal to the user and stable across websites, which is what makes autofill and personalised icons useful.
2. The content is implemented in a technology that supports identifying the expected meaning of form input. In HTML that is the `autocomplete` attribute on `<input>`, `<select>` and `<textarea>`. (A native app or a PDF form may use a different taxonomy; only the concepts mapped to the meanings above are required.)

If either condition is not met, the criterion is not applicable to that field. A field that does meet both conditions and has no purpose token, or has a wrong one, fails.

### Sufficient technique H98 — Using HTML autocomplete attributes

The HTML autofill field names coincide one-to-one with the 53 tokens, so in HTML the implementation is simply:

```html
<label for="nombre">Full name</label>
<input id="nombre" name="nombre" type="text" autocomplete="name">

<label for="mail">Email</label>
<input id="mail" name="mail" type="email" autocomplete="email">

<label for="tel">Mobile phone</label>
<input id="tel" name="tel" type="tel" autocomplete="tel">

<label for="pass">Password</label>
<input id="pass" name="pass" type="password" autocomplete="current-password">
```

Points that matter when writing or auditing:

- The `name` and `id` attributes are irrelevant to 1.3.5. Only `autocomplete` carries the programmatic purpose; `name="email"` on its own does not satisfy the criterion.
- `autocomplete="on"` and `autocomplete="off"` do not identify a purpose. `on` is not a pass, and `off` on an in-scope field (a login form that disables autofill "for security") is a failure unless the field is genuinely out of scope. Password managers and the `current-password`/`new-password` tokens are also how 3.3.8 Accessible Authentication (Minimum) is commonly met, so removing them hurts twice.
- The token must match the field's actual purpose: `given-name` on a field that collects the full name, or `bday` on a field that collects the expiry date of a document, is a wrong purpose.
- Choose the granularity that matches the form. A single "Name" field takes `name`; separate first/last fields take `given-name` and `family-name`. A single "Date of birth" field takes `bday`; three selects take `bday-day`, `bday-month`, `bday-year`.
- `<select>` elements take tokens too (`country`, `address-level1`, `cc-exp-month`, `bday-month`, `sex`, `language`).

### Optional prefixes: sections, shipping/billing and contact type

HTML allows the token to be qualified so that two addresses or two phone numbers on the same form can be distinguished. The qualifiers go **before** the field token, in this order:

```
[section-*] [shipping | billing] [home | work | mobile | fax | pager] <field token>
```

- `section-*` groups a set of fields into a named section (any name after `section-`). Example: a form collecting the applicant and a guarantor.
- `shipping` and `billing` apply to address and contact fields.
- `home`, `work`, `mobile`, `fax`, `pager` apply only to the telephone tokens (`tel`, `tel-*`), `email` and `impp`.

```html
<!-- Two addresses on one checkout page -->
<input autocomplete="shipping street-address">
<input autocomplete="shipping postal-code">
<input autocomplete="billing street-address">
<input autocomplete="billing postal-code">

<!-- Two phone numbers -->
<input type="tel" autocomplete="home tel">
<input type="tel" autocomplete="work tel">
<input type="tel" autocomplete="mobile tel">

<!-- Two people on one form -->
<input autocomplete="section-applicant given-name">
<input autocomplete="section-applicant family-name">
<input autocomplete="section-guarantor given-name">
<input autocomplete="section-guarantor family-name">

<!-- Combined -->
<input autocomplete="section-applicant shipping mobile tel">
```

Note that `section-guarantor given-name` is about a *different person*, so strictly that field is out of scope for 1.3.5; the prefix is still valuable because it keeps the applicant's autofill from overwriting the guarantor's fields.

### Common failure F107 — incorrect autocomplete attribute values

F107 fails 1.3.5 when an in-scope field has an `autocomplete` value that is not a valid token for its purpose. Typical real-world instances:

| What was written | Why it fails | Fix |
|---|---|---|
| `autocomplete="first-name"`, `"lastname"`, `"surname"`, `"phone"`, `"zip"`, `"e-mail"` | Not tokens in the list; browsers ignore them | `given-name`, `family-name`, `family-name`, `tel`, `postal-code`, `email` |
| `autocomplete="name"` on a "First name" field | Wrong granularity: `name` is the full name | `given-name` |
| `autocomplete="tel"` on an extension field | Wrong purpose | `tel-extension` |
| `autocomplete="cc-number"` on a national ID / DNI field | Wrong purpose; also a security concern | No token exists for government IDs; leave `autocomplete` without a purpose token (the field is out of scope) |
| `autocomplete="bday"` on "Document expiry date" | Not about the user's birthday | Out of scope; remove the token |
| `autocomplete="username"` on an email login that is actually an email address | Acceptable only if the username *is* the email; prefer `email` when the account identifier is an email, or `username` when it is a handle | Pick the token that matches what the user types |
| `autocomplete="nope"` / `"new-whatever"` (hacks to defeat browser autofill) | Invalid token on an in-scope field; defeats the purpose of the criterion | Use the correct token; if autofill genuinely must be prevented, document why and expect a 1.3.5 failure |
| `autocomplete="tel home"` | Qualifier in the wrong position (must come before the field token) | `home tel` |

Fields with **no** `autocomplete` attribute at all are not F107 (that failure is specifically about incorrect values), but they still fail 1.3.5 if they are in scope, because the purpose cannot be programmatically determined.

### Quick audit procedure for 1.3.5

1. List every `<input>`, `<select>` and `<textarea>` in each form.
2. For each, ask: is this information *about the user* and does it match one of the 53 purposes? If not, mark N/A and move on.
3. For in-scope fields, read the `autocomplete` attribute: present, a valid token (with optional qualifiers in the right order), and matching the field's real purpose → pass; missing → fail 1.3.5; present but wrong → fail 1.3.5 (F107).
4. Confirm in a browser that autofill actually offers a value for the field (a quick functional check that the token is spelled correctly).
