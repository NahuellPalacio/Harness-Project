# Principle 2: Operable

> User interface components and navigation must be operable.

Source: Web Content Accessibility Guidelines (WCAG) 2.2, W3C Recommendation 12 December 2024 — https://www.w3.org/TR/WCAG22/ . Normative text is quoted verbatim; sections marked *informative* are explanatory guidance derived from the W3C "Understanding" and "Techniques" documents and from practice.

## Contents

| Guideline | Success criterion | Level |
|---|---|---|
| 2.1 Keyboard Accessible | 2.1.1 Keyboard | A |
| | 2.1.2 No Keyboard Trap | A |
| | 2.1.3 Keyboard (No Exception) | AAA |
| | 2.1.4 Character Key Shortcuts | A |
| 2.2 Enough Time | 2.2.1 Timing Adjustable | A |
| | 2.2.2 Pause, Stop, Hide | A |
| | 2.2.3 No Timing | AAA |
| | 2.2.4 Interruptions | AAA |
| | 2.2.5 Re-authenticating | AAA |
| | 2.2.6 Timeouts | AAA |
| 2.3 Seizures and Physical Reactions | 2.3.1 Three Flashes or Below Threshold | A |
| | 2.3.2 Three Flashes | AAA |
| | 2.3.3 Animation from Interactions | AAA |
| 2.4 Navigable | 2.4.1 Bypass Blocks | A |
| | 2.4.2 Page Titled | A |
| | 2.4.3 Focus Order | A |
| | 2.4.4 Link Purpose (In Context) | A |
| | 2.4.5 Multiple Ways | AA |
| | 2.4.6 Headings and Labels | AA |
| | 2.4.7 Focus Visible | AA |
| | 2.4.8 Location | AAA |
| | 2.4.9 Link Purpose (Link Only) | AAA |
| | 2.4.10 Section Headings | AAA |
| | 2.4.11 Focus Not Obscured (Minimum) — **New in 2.2** | AA |
| | 2.4.12 Focus Not Obscured (Enhanced) — **New in 2.2** | AAA |
| | 2.4.13 Focus Appearance — **New in 2.2** | AAA |
| 2.5 Input Modalities | 2.5.1 Pointer Gestures | A |
| | 2.5.2 Pointer Cancellation | A |
| | 2.5.3 Label in Name | A |
| | 2.5.4 Motion Actuation | A |
| | 2.5.5 Target Size (Enhanced) | AAA |
| | 2.5.6 Concurrent Input Mechanisms | AAA |
| | 2.5.7 Dragging Movements — **New in 2.2** | AA |
| | 2.5.8 Target Size (Minimum) — **New in 2.2** | AA |

Numbering note: new WCAG 2.2 criteria were appended to the end of their guideline so that existing numbers did not change. Consequently criteria within a guideline are **not** ordered by conformance level (e.g. 2.4.7 Focus Visible is AA, 2.4.8–2.4.10 are AAA, 2.4.11 is AA again). Only the level indicator on each criterion is authoritative.

Non-interference reminder: 2.1.2 No Keyboard Trap, 2.2.2 Pause, Stop, Hide and 2.3.1 Three Flashes or Below Threshold apply to **all** content on the page, including content not otherwise relied upon for conformance (Conformance Requirement 5).

---

## Guideline 2.1 Keyboard Accessible

> Make all functionality available from a keyboard.

Key terms (short; full definitions in `glossary.md`):
- **keyboard interface** — interface used by software to obtain keystroke input. It covers keystrokes from a physical keyboard, an on-screen keyboard, speech-to-text "keyboard emulation", switch devices, etc. Operating a page through a keyboard-driven *mouse emulator* (MouseKeys) does **not** count.
- **functionality** — processes and outcomes achievable through user action.
- **keyboard shortcut** — alternative means of triggering an action by the pressing of one or more keys.

### 2.1.1 Keyboard (Level A)

**Normative text (verbatim):**
> All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes, except where the underlying function requires input that depends on the path of the user's movement and not just the endpoints.
>
> NOTE 1: This exception relates to the underlying function, not the input technique. For example, if using handwriting to enter text, the input technique (handwriting) requires path-dependent input but the underlying function (text input) does not.
>
> NOTE 2: This does not forbid and should not discourage providing mouse input or other input methods in addition to keyboard operation.

**Intent (informative):** Keyboard operability is the foundation of operability for people who are blind (screen reader users navigate by keyboard), people with motor impairments who use alternative keyboards, switches, or speech input that emulates keystrokes, and anyone who cannot use a pointing device precisely. If every function can be reached and triggered by keystrokes without timing requirements, those users can use the content. The only exception is functions that are intrinsically path-dependent (free-hand drawing, a signature pad); even then, note that providing a keyboard alternative is encouraged.

**How to test:**
1. Unplug or ignore the mouse. Starting from the address bar, press Tab (and Shift+Tab) through the whole page. Every interactive element — links, buttons, form fields, custom widgets (menus, tabs, sliders, date pickers, carousels, modals, drag-and-drop lists, map controls, media players) — must receive focus.
2. For each focused element, operate it with the expected keys: Enter for links, Enter/Space for buttons, Space for checkboxes, arrow keys for radio groups, selects, sliders, tabs and menus, Escape to close dialogs/menus. Confirm the same outcome a mouse user gets.
3. Check hover-only functionality: anything revealed or triggered on mouseover (mega-menus, tooltips with actions, row action icons) must also be reachable and triggerable from the keyboard.
4. Check for timing: no function should require holding a key, pressing keys within a time window, or pressing keys in rapid sequence.
5. In the DOM/DevTools, look for `onmousedown`, `onmouseover`, `onclick` on non-focusable `div`/`span` elements without `tabindex="0"` and key handlers — these are the usual culprits.
   Forms: be precise about HTML *implicit submission*. Pressing Enter in a text field submits the form only if the form has a submit button (`<button>`/`<input type="submit">`, even hidden) **or** it has exactly one field that blocks implicit submission (one text-like input). A form with two or more text fields and only a `<span onclick>`/`<div onclick>` "submit" cannot be submitted from the keyboard at all — report it as a 2.1.1 failure, and describe the mechanism correctly in the finding.
6. Decide whether any remaining pointer-only function is truly path-dependent (freehand drawing). If so, it is excepted; if the outcome only depends on endpoints (dragging a slider, moving a card to a column), it is not excepted and must have a keyboard means.
7. Pass only if every function is operable by keyboard alone without timing requirements, or falls under the path-dependent exception.

**Common failures:**
- F54 Failure of Success Criterion 2.1.1 due to using only pointing-device-specific event handlers (including gesture) for a function
- F55 Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
- F42 Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links
- Typical examples: a `<div onclick>` "Add to cart" button with no `tabindex` or key handler; a custom dropdown that only opens on click; a drag-and-drop Kanban board with no "Move to…" alternative; a carousel whose arrows are not focusable.

**Sufficient techniques:**
- G202 Ensuring keyboard control for all functionality
- Ensuring keyboard control using one of the following techniques:
  - H91 Using HTML form controls and links
  - PDF3 Ensuring correct tab and reading order in PDF documents
  - PDF11 Providing links and link text using the Link annotation and the /Link structure element in PDF documents
  - PDF23 Providing interactive form controls in PDF documents
- G90 Providing keyboard-triggered event handlers using one of the following techniques:
  - SCR20 Using both keyboard and other device-specific functions
  - SCR35 Making actions keyboard accessible by using the onclick event of anchors and buttons
  - SCR2 Using redundant keyboard and mouse event handlers

**Advisory techniques:**
- Using WAI-ARIA role, state, and value attributes if repurposing static elements as interactive user interface components (future link) AND SCR29 Adding keyboard-accessible actions to static HTML elements

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<!-- Correct: native elements are keyboard-operable for free -->
<button type="button" id="add">Add to cart</button>
<a href="/checkout">Checkout</a>

<!-- Incorrect: not focusable, no key handling -->
<div class="btn" onclick="addToCart()">Add to cart</div>

<!-- If a custom control is unavoidable: focusable + role + keys -->
<div role="button" tabindex="0" id="custom">Add to cart</div>
<script>
  const el = document.getElementById('custom');
  el.addEventListener('click', addToCart);
  el.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); addToCart(); }
  });
</script>
```
Prefer `<button>`, `<a href>`, `<input>`, `<select>`, `<dialog>` and `<details>` over re-implemented widgets. For composite widgets (tabs, menus, grids, trees) follow the WAI-ARIA Authoring Practices keyboard patterns (roving `tabindex`, arrow-key navigation).

**Related:** 2.1.2 No Keyboard Trap, 2.1.3 Keyboard (No Exception), 2.4.3 Focus Order, 2.4.7 Focus Visible, 2.5.1 Pointer Gestures, 2.5.7 Dragging Movements, 4.1.2 Name, Role, Value.

### 2.1.2 No Keyboard Trap (Level A)

**Normative text (verbatim):**
> If keyboard focus can be moved to a component of the page using a keyboard interface, then focus can be moved away from that component using only a keyboard interface, and, if it requires more than unmodified arrow or tab keys or other standard exit methods, the user is advised of the method for moving focus away.
>
> NOTE: Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether it is used to meet other success criteria or not) must meet this success criterion. See Conformance Requirement 5: Non-Interference.

**Intent (informative):** A keyboard trap makes the entire page unusable for keyboard-only users: once focus enters the trapping component (an embedded player, a rich text editor, a plug-in, a badly built modal) it cannot leave, so the user cannot reach anything else and may have to close the browser. Because the harm is total, the criterion applies to every piece of content on the page, even content not relied upon for conformance.

**How to test:**
1. Tab through the whole page and keep tabbing after the last element; focus must cycle back to the browser chrome / top of page.
2. Enter every embedded or complex component (iframes, media players, code editors, canvas apps, chat widgets, cookie banners, modal dialogs). Tab and Shift+Tab inside it; confirm you can leave it in both directions.
3. Where a component legitimately captures Tab (e.g. a rich text editor that inserts a tab character, or a modal dialog that intentionally cycles focus), check that: a standard exit (Escape, or a close button reachable by Tab) exists, and if a non-standard key is required, on-screen or programmatically available instructions say so *before* the user is trapped.
4. A modal dialog that cycles focus inside itself is acceptable only if Escape or a focusable Close control returns focus to the page.
5. Fail if any component can be entered but not left with the keyboard, or if the required exit key is not advised.

**Common failures:**
- F10 Failure of Success Criterion 2.1.2 and Conformance Requirement 5 due to combining multiple content formats in a way that traps users inside one format type
- Typical examples: a third-party chat iframe that swallows Tab; a "focus guard" script that keeps re-focusing a field until it is valid; a modal with no Escape handling and a Close button that is not focusable.

**Sufficient techniques:**
- G21 Ensuring that users are not trapped in content

**Implementation notes (HTML/CSS/ARIA/JS):**
```js
// Modal focus management that is NOT a trap:
dialog.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeDialog(); triggerButton.focus(); }
});
// Prefer the native <dialog> element with showModal(): Escape closes it by default.
```
Never cancel the default action of Tab globally. If a widget must use Tab for its own purpose (e.g. indentation), provide and announce Escape or Ctrl+M as the exit.

**Related:** 2.1.1 Keyboard, 2.4.3 Focus Order, 3.2.1 On Focus, Conformance Requirement 5 (Non-Interference).

### 2.1.3 Keyboard (No Exception) (Level AAA)

**Normative text (verbatim):**
> All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes.

**Intent (informative):** The AAA version removes the path-dependent exception of 2.1.1: *every* function must be keyboard-operable. Functions whose nature is path-dependent (freehand drawing) cannot meet it, which is why it is AAA.

**How to test:**
1. Perform the full 2.1.1 keyboard walkthrough.
2. Any function that was accepted under the path-dependent exception in 2.1.1 now counts as a failure unless a keyboard equivalent exists (e.g. drawing by entering coordinates, or a text-entry alternative to a signature pad).
3. Pass only if there is no pointer-only functionality at all.

**Common failures:**
- F42 Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links
- Typical examples: a map that can only be panned by dragging; a signature canvas with no typed-name alternative; a colour picker operable only by dragging on a gradient.

**Sufficient techniques:**
- No additional techniques exist for this success criterion. Follow techniques for Success Criterion 2.1.1. If that is not possible because there is a requirement for path-dependent input, then it is not possible to meet this Level AAA success criterion.

**Implementation notes (HTML/CSS/ARIA/JS):** Offer numeric/text inputs alongside spatial controls (e.g. latitude/longitude fields for a map pin, hex input for a colour picker) so that the *result* can be reached without a path.

**Related:** 2.1.1 Keyboard, 2.5.1 Pointer Gestures, 2.5.7 Dragging Movements.

### 2.1.4 Character Key Shortcuts (Level A)

**Normative text (verbatim):**
> If a keyboard shortcut is implemented in content using only letter (including upper- and lower-case letters), punctuation, number, or symbol characters, then at least one of the following is true:
>
> Turn off: A mechanism is available to turn the shortcut off;
>
> Remap: A mechanism is available to remap the shortcut to include one or more non-printable keyboard keys (e.g., Ctrl, Alt);
>
> Active only on focus: The keyboard shortcut for a user interface component is only active when that component has focus.

**Intent (informative):** Single-character shortcuts (such as "e" to archive, "j/k" to move, "?" for help) are triggered accidentally by speech-recognition users, whose dictated words are converted into keystrokes, and by people with tremors or who mis-type. Requiring a modifier, allowing the shortcut to be turned off, or scoping it to a focused component prevents destructive surprises.

**How to test:**
1. Identify every keyboard shortcut implemented by the page's scripts (check help/"?" overlays, documentation, and `keydown`/`keypress` listeners on `document`/`window`).
2. For each shortcut that consists solely of printable characters (letters, digits, punctuation, symbols) with no modifier key (Ctrl, Alt, Cmd, Meta, Shift-only does not count as non-printable), check that at least one is true: there is a setting to turn it off; there is a setting to remap it to include a non-printable key; or it only works while a specific component has focus (e.g. arrow/letter keys inside a listbox).
3. Verify the exception by moving focus to the page body and pressing the character: nothing should happen if the shortcut is claimed to be "active only on focus".
4. Fail if any page-wide single-character shortcut cannot be disabled or remapped.

**Common failures:**
- F99 Failure of Success Criterion 2.1.4 due to implementing character key shortcuts that cannot be turned off or remapped
- Typical examples: a webmail client where "#" deletes the current message with no preference to disable it; a video player where "f" toggles full screen page-wide; a chat app where "/" focuses search without an opt-out.

**Sufficient techniques:**
- G217 Providing a mechanism to allow users to remap or turn off character key shortcuts

**Implementation notes (HTML/CSS/ARIA/JS):**
```js
// Scope the shortcut to the component, or require a modifier
listbox.addEventListener('keydown', e => { /* letter keys only act here */ });
document.addEventListener('keydown', e => {
  if (!settings.shortcutsEnabled) return;          // user can turn off
  if (e.altKey && e.key === 'a') archive();        // or require a modifier
});
```
Shortcuts that use a modifier (Ctrl+S) are out of scope of this criterion. Native browser/OS shortcuts are not "implemented in content".

**Related:** 2.1.1 Keyboard, 3.2.2 On Input, 3.3.4 Error Prevention (Legal, Financial, Data).

---

## Guideline 2.2 Enough Time

> Provide users enough time to read and use content.

Key terms (short): **real-time event** — event that a) occurs at the same time as the viewing and b) is not completely generated by the content. **essential** — if removed, would fundamentally change the information or functionality of the content, and information and functionality cannot be achieved in another way that would conform. **paused** — stopped by user request and not resumed until requested by user. **user inactivity** — any continuous period of time where no user actions occur. **emergency** — a sudden, unexpected situation or occurrence that requires immediate action to preserve health, safety, or property.

### 2.2.1 Timing Adjustable (Level A)

**Normative text (verbatim):**
> For each time limit that is set by the content, at least one of the following is true:
>
> Turn off: The user is allowed to turn off the time limit before encountering it; or
>
> Adjust: The user is allowed to adjust the time limit before encountering it over a wide range that is at least ten times the length of the default setting; or
>
> Extend: The user is warned before time expires and given at least 20 seconds to extend the time limit with a simple action (for example, "press the space bar"), and the user is allowed to extend the time limit at least ten times; or
>
> Real-time Exception: The time limit is a required part of a real-time event (for example, an auction), and no alternative to the time limit is possible; or
>
> Essential Exception: The time limit is essential and extending it would invalidate the activity; or
>
> 20 Hour Exception: The time limit is longer than 20 hours.
>
> NOTE: This success criterion helps ensure that users can complete tasks without unexpected changes in content or context that are a result of a time limit. This success criterion should be considered in conjunction with Success Criterion 3.2.1, which puts limits on changes of content or context as a result of user action.

**Intent (informative):** People who read slowly, use screen readers or magnifiers, have motor impairments or cognitive disabilities need more time than a designer assumes. Session timeouts, auto-advancing content, countdowns to submit, and timed redirects all cut tasks short. The criterion lets users turn the limit off, make it ten times longer, or extend it repeatedly with ample warning, except where the timing is a genuine part of the activity.

**How to test:**
1. Inventory every time limit set by the content: session expiry, idle logout, auto-redirect (`<meta http-equiv="refresh">`, JS timers), quiz/checkout countdowns, auto-advancing carousels or wizards, toast messages that vanish, ticket-reservation holds.
2. For each, check whether the user can turn it off or set it to ≥ 10× the default **before** encountering it (e.g. a "keep me signed in / extend session" option on the first page of a form).
3. If not, trigger the limit: a warning must appear **at least 20 seconds** before expiry, extending must be a simple action (one key/click), and it must be possible to extend at least **ten times**.
4. If none applies, decide whether an exception is valid: real-time event (live auction, live quiz), essential (timed exam where extra time invalidates the test — check that accommodations exist by policy), or the limit is longer than 20 hours.
5. Also check content that scrolls or auto-updates (ticker, rotating banners): the reading time limit must be pausable (ties to 2.2.2).
6. Fail if any content-set limit shorter than 20 hours cannot be turned off, adjusted ×10, or extended with ≥20 s warning, and no exception applies.

**Common failures:**
- F40 Failure due to using meta redirect with a time limit
- F41 Failure of Success Criterion 2.2.1, 2.2.4, and 3.2.5 due to using meta refresh to reload the page
- F58 Failure of Success Criterion 2.2.1 due to using server-side techniques to automatically redirect pages after a time-out
- Typical examples: a government form that silently logs the user out after 15 minutes and discards input; a "page moved, redirecting in 5 s" splash; an e-commerce cart with a 10-minute hold and no extend option.

**Sufficient techniques:**
- Situation A: If there are session time limits:
  - G133 Providing a checkbox on the first page of a multipart form that allows users to ask for longer session time limit or no session time limit
  - G198 Providing a way for the user to turn the time limit off
- Situation B: If a time limit is controlled by a script on the page:
  - G198 Providing a way for the user to turn the time limit off
  - G180 Providing the user with a means to set the time limit to 10 times the default time limit
  - SCR16 Providing a script that warns the user a time limit is about to expire AND SCR1 Allowing the user to extend the default time limit
- Situation C: If there are time limits on reading:
  - G4 Allowing the content to be paused and restarted from where it was paused
  - G198 Providing a way for the user to turn the time limit off
  - SCR33 Using script to scroll content, and providing a mechanism to pause it
  - SCR36 Providing a mechanism to allow users to display moving, scrolling, or auto-updating text in a static window or area

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<!-- Session warning dialog shown ≥ 20 s before expiry; Extend is one click -->
<dialog id="timeout" aria-labelledby="t-title">
  <h2 id="t-title">Your session will expire in <span id="secs">60</span> seconds</h2>
  <button type="button" id="extend">Stay signed in</button>
</dialog>
```
Avoid `<meta http-equiv="refresh" content="5;url=...">`; use an instant (0-second) redirect on the server or a user-triggered link instead. Save form state server-side so an expiry does not destroy data (see 2.2.5, 2.2.6).

**Related:** 2.2.2 Pause, Stop, Hide, 2.2.3 No Timing, 2.2.5 Re-authenticating, 2.2.6 Timeouts, 3.2.1 On Focus, 3.2.5 Change on Request.

### 2.2.2 Pause, Stop, Hide (Level A)

**Normative text (verbatim):**
> For moving, blinking, scrolling, or auto-updating information, all of the following are true:
>
> Moving, blinking, scrolling: For any moving, blinking or scrolling information that (1) starts automatically, (2) lasts more than five seconds, and (3) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it unless the movement, blinking, or scrolling is part of an activity where it is essential; and
>
> Auto-updating: For any auto-updating information that (1) starts automatically and (2) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it or to control the frequency of the update unless the auto-updating is part of an activity where it is essential.
>
> NOTE 1: For requirements related to flickering or flashing content, refer to Guideline 2.3.
>
> NOTE 2: Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether it is used to meet other success criteria or not) must meet this success criterion. See Conformance Requirement 5: Non-Interference.
>
> NOTE 3: Content that is updated periodically by software or that is streamed to the user agent is not required to preserve or present information that is generated or received between the initiation of the pause and resuming presentation, as this may not be technically possible, and in many situations could be misleading to do so.
>
> NOTE 4: An animation that occurs as part of a preload phase or similar situation can be considered essential if interaction cannot occur during that phase for all users and if not indicating progress could confuse users or cause them to think that content was frozen or broken.

**Intent (informative):** Moving or constantly changing content distracts people with attention deficits and cognitive disabilities, is hard to read for people with low vision or slow reading, and interferes with screen magnifiers and screen readers that re-announce changes. Giving the user a way to pause, stop, or hide it (or slow updates) restores control. It applies to all content on the page because an unstoppable animation can make the whole page unusable.

**How to test:**
1. Load the page and watch for 5+ seconds: carousels/sliders, auto-playing video/GIF backgrounds, news tickers, animated banners, "live" counters, stock/score feeds, chat streams, rotating testimonials, parallax/CSS animations, auto-refreshing dashboards.
2. For each item that starts automatically and runs > 5 seconds alongside other content: find a pause/stop/hide control. It must be keyboard-operable, visible (or at least discoverable at the start of the page), and actually stop the motion (not just hide one slide).
3. For auto-updating content started automatically: look for pause/stop/hide or a frequency control (e.g. "refresh every: off / 30 s / 5 min").
4. Browser-level mechanisms count only if commonly available (e.g. Escape stopping an animated GIF is not reliable in modern browsers — do not rely on it).
5. Check the essential exception narrowly: a loading spinner during a blocking preload, or an animation that *is* the activity (a game), may be essential. A decorative hero animation is not.
6. Fail if any auto-starting motion > 5 s or auto-update lacks a user control and is not essential.

**Common failures:**
- F16 Failure of Success Criterion 2.2.2 due to including scrolling content where movement is not essential to the activity without also including a mechanism to pause and restart the content
- F112 Failure of Success Criterion 2.2.2 due to using blinking content that lasts for more than five seconds without a mechanism to stop it
- F50 Failure of Success Criterion 2.2.2 due to a script that causes a blink effect without a mechanism to stop the blinking at 5 seconds or less
- F7 Failure of Success Criterion 2.2.2 due to an object or applet that has blinking content without a mechanism to pause the content that blinks for more than five seconds
- Typical examples: a home-page hero carousel that auto-rotates with no pause button; a muted looping background video with no stop control; a "breaking news" marquee; a dashboard that reloads every 10 s and resets scroll position.

**Sufficient techniques:**
- G4 Allowing the content to be paused and restarted from where it was paused
- SCR33 Using script to scroll content, and providing a mechanism to pause it
- G11 Creating content that blinks for less than 5 seconds
- G152 Setting animated gif images to stop blinking after n cycles (within 5 seconds)
- SCR22 Using scripts to control blinking and stop it in five seconds or less
- G186 Using a control in the web page that stops moving, blinking, or auto-updating content
- G191 Providing a link, button, or other mechanism that reloads the page without any blinking content

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<section aria-roledescription="carousel" aria-label="Featured">
  <button type="button" aria-pressed="false" id="pause">Pause</button>
  …slides…
</section>
<video autoplay muted loop playsinline controls>…</video> <!-- controls expose Pause -->
```
```css
/* Respect user motion preference as a bonus (not a substitute for a control) */
@media (prefers-reduced-motion: reduce) { .ticker { animation: none; } }
```
Place the pause control before or at the start of the moving content in the focus order so keyboard users reach it quickly. Let the user's choice persist across pages.

**Related:** 2.2.1 Timing Adjustable, 2.2.4 Interruptions, 2.3.1 Three Flashes or Below Threshold, 2.3.3 Animation from Interactions, 1.4.2 Audio Control, Conformance Requirement 5.

### 2.2.3 No Timing (Level AAA)

**Normative text (verbatim):**
> Timing is not an essential part of the event or activity presented by the content, except for non-interactive synchronized media and real-time events.

**Intent (informative):** Removes time pressure entirely so that people who need much longer to read, think, or operate controls can complete every activity. Only prerecorded media that must play in time, and genuine real-time events, are excepted.

**How to test:**
1. Inventory every activity on the page (forms, quizzes, games, checkouts, bookings).
2. Confirm that none has a time limit that affects outcome or completion (no countdowns, no auto-expiring holds, no timed questions), other than video/audio playback and real-time events (live auction, live chat).
3. Fail if any interactive activity depends on timing.

**Sufficient techniques:**
- G5 Allowing users to complete an activity without any time limit

**Implementation notes (HTML/CSS/ARIA/JS):** Replace timed steps with explicit user-triggered progression ("Continue" buttons), persist state so that sessions never expire data, and offer untimed versions of assessments.

**Related:** 2.2.1 Timing Adjustable, 2.2.6 Timeouts.

### 2.2.4 Interruptions (Level AAA)

**Normative text (verbatim):**
> Interruptions can be postponed or suppressed by the user, except interruptions involving an emergency.

**Intent (informative):** Unexpected alerts, pop-ups, notification toasts, and auto-refreshes break concentration for people with attention or cognitive disabilities and disorient screen-reader users who lose their place. Letting users defer or turn off non-emergency interruptions preserves focus.

**How to test:**
1. Identify all content-initiated interruptions: chat invitations, newsletter pop-ups, "new version available" banners, live-update insertions that shift content, auto-reload.
2. Check that a user preference or control exists to postpone them (e.g. "remind me later") or suppress them (e.g. "do not disturb" setting, turning off auto-refresh), and that it works across the session/site.
3. Emergency messages (safety, security, data-loss warnings) are exempt.
4. Fail if non-emergency interruptions cannot be postponed or suppressed.

**Common failures:**
- F40 Failure due to using meta redirect with a time limit
- F41 Failure of Success Criterion 2.2.1, 2.2.4, and 3.2.5 due to using meta refresh to reload the page

**Sufficient techniques:**
- G75 Providing a mechanism to postpone any updating of content
- G76 Providing a mechanism to request an update of the content instead of updating automatically
- SCR14 Using scripts to make nonessential alerts optional

**Implementation notes (HTML/CSS/ARIA/JS):** Offer a "Notifications: on/off" setting stored in the user profile; use `aria-live="polite"` rather than `assertive` for non-urgent updates; replace automatic refresh with a "Refresh" button or a user-chosen interval.

**Related:** 2.2.2 Pause, Stop, Hide, 3.2.5 Change on Request, 4.1.3 Status Messages.

### 2.2.5 Re-authenticating (Level AAA)

**Normative text (verbatim):**
> When an authenticated session expires, the user can continue the activity without loss of data after re-authenticating.

**Intent (informative):** Slow users are the most likely to hit a session expiry mid-task. If logging back in discards everything typed, the cost of the expiry falls hardest on people with disabilities. Preserving the data (server-side or encoded in the re-authentication flow) makes expiry a minor inconvenience rather than a loss.

**How to test:**
1. Start a multi-step task (long form, cart, document edit). Let the session expire (or force expiry via DevTools/cookies).
2. Re-authenticate through the normal flow.
3. Verify that you are returned to the same step with all previously entered data intact (including file uploads and selections).
4. Fail if any data entered before expiry is lost.

**Common failures:**
- F12 Failure of Success Criterion 2.2.5 due to having a session time limit without a mechanism for saving user's input and re-establishing that information upon re-authentication

**Sufficient techniques:**
- Providing options to continue without loss of data using one of the following techniques:
  - G105 Saving data so that it can be used after a user re-authenticates
  - G181 Encoding user data as hidden or encrypted data in a re-authorization page

**Implementation notes (HTML/CSS/ARIA/JS):** Autosave drafts to the server keyed to the user; on 401/expiry, open an inline re-login dialog that retains the page state, then replay the pending request. Keep uploaded files referenced by token so they survive re-login.

**Related:** 2.2.1 Timing Adjustable, 2.2.6 Timeouts, 3.3.7 Redundant Entry.

### 2.2.6 Timeouts (Level AAA)

**Normative text (verbatim):**
> Users are warned of the duration of any user inactivity that could cause data loss, unless the data is preserved for more than 20 hours when the user does not take any actions.
>
> NOTE: Privacy regulations may require explicit user consent before user identification has been authenticated and before user data is preserved. In cases where the user is a minor, explicit consent may not be solicited in most jurisdictions, countries or regions. Consultation with privacy professionals and legal counsel is advised when considering data preservation as an approach to satisfy this success criterion.

**Intent (informative):** People with cognitive disabilities may need to pause and return to a task. Knowing *up front* how long they can be inactive before losing data lets them plan (save, take notes) instead of being surprised by a silent timeout.

**How to test:**
1. Determine the inactivity period after which data is lost (session expiry, cart hold, draft discard).
2. If it is ≤ 20 hours, confirm that the user is told the duration before they begin or early in the process (e.g. "Your session will time out after 30 minutes of inactivity" at the start of the form), in text.
3. If data is preserved for more than 20 hours of inactivity, the criterion is met without a warning.
4. Fail if a short inactivity limit exists and the duration is not disclosed.

**Sufficient techniques:**
- Setting a session timeout to occur following at least 20 hours of inactivity
- Storing user data for more than 20 hours
- Providing a warning of the duration of user inactivity at the start of a process

**Implementation notes (HTML/CSS/ARIA/JS):** Put a plain-text statement at the top of the first step: "You will be signed out after 20 minutes without activity; unsaved answers are lost." Pair with 2.2.1's extend mechanism.

**Related:** 2.2.1 Timing Adjustable, 2.2.5 Re-authenticating, 3.3.2 Labels or Instructions. Listed under Privacy and Security Considerations in WCAG 2.2 §5.6–5.7.

---

## Guideline 2.3 Seizures and Physical Reactions

> Do not design content in a way that is known to cause seizures or physical reactions.

Key terms (short): **flash** — a pair of opposing changes in relative luminance that can cause seizures in some people if it is large enough and in the right frequency range. **general flash and red flash thresholds** — content passes if there are no more than three general flashes and/or no more than three red flashes within any one-second period, or the combined flashing area is no more than 0.006 steradians within any 10-degree visual field (≈ 25% of a 10° field; a 341 × 256 px rectangle at 1024 × 768 is a practical estimate). A general flash is a pair of opposing changes in relative luminance of ≥ 10% of maximum where the darker image is below 0.80; a red flash is any pair of opposing transitions involving a saturated red. Fine balanced patterns (white noise, checkerboards with squares < 0.1°) are excepted. **motion animation** — addition of steps between conditions to create the illusion of movement or to give a sense of a smooth transition (changes of colour, blur or opacity that do not change perceived size, shape or position are not motion animation).

### 2.3.1 Three Flashes or Below Threshold (Level A)

**Normative text (verbatim):**
> Web pages do not contain anything that flashes more than three times in any one second period, or the flash is below the general flash and red flash thresholds.
>
> NOTE: Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether it is used to meet other success criteria or not) must meet this success criterion. See Conformance Requirement 5: Non-Interference.

**Intent (informative):** Flashing in the 3–50 Hz range can trigger seizures in people with photosensitive epilepsy, with large bright areas and saturated red being the most dangerous. Limiting flashes to three per second, or keeping flashing areas small/dim, protects them. Because a seizure can be caused by *any* content, the criterion applies to everything on the page, including ads and embedded media.

**How to test:**
1. Identify any flashing/strobing content: videos, GIFs, canvas/WebGL effects, CSS animations that toggle brightness, lightning/explosion effects, rapid image cycling, blinking alerts.
2. Count flashes: a flash is a pair of opposing luminance changes. More than 3 flashes in any 1-second window is a fail **unless** below threshold.
3. If > 3 flashes/second, measure the area: at 1024 × 768 the flashing region must stay within a 341 × 256 px rectangle (≈ 25% of a 10° field) — and it must not involve saturated red transitions.
4. For video, run an analysis tool (e.g. PEAT, Harding FPA) on a screen capture; tools are not required when flashing is ≤ 3 per second, which automatically passes.
5. Fail if any content exceeds 3 flashes/second above the general or red flash thresholds.

**Sufficient techniques:**
- G19 Ensuring that no component of the content flashes more than three times in any 1-second period
- G176 Keeping the flashing area small enough
- G15 Using a tool to ensure that content does not violate the general flash threshold or red flash threshold

**Implementation notes (HTML/CSS/ARIA/JS):** Avoid strobe effects altogether; if lightning/explosion effects are required in video, dim them, keep them small, and never use saturated red. For CSS, keep `@keyframes` that alternate brightness to ≤ 3 cycles/second or make them require user activation. Warn users before playing content that could not be remediated, but a warning does not satisfy the criterion.

**Related:** 2.3.2 Three Flashes, 2.2.2 Pause, Stop, Hide, Conformance Requirement 5.

### 2.3.2 Three Flashes (Level AAA)

**Normative text (verbatim):**
> Web pages do not contain anything that flashes more than three times in any one second period.

**Intent (informative):** The AAA version drops the "below threshold" allowance: no content may flash more than three times per second, regardless of size or colour, giving the most sensitive users full protection.

**How to test:**
1. As for 2.3.1, but any content with more than 3 flashes in any one-second period fails, even if small or dim.

**Sufficient techniques:**
- G19 Ensuring that no component of the content flashes more than three times in any 1-second period

**Implementation notes (HTML/CSS/ARIA/JS):** Design rule: nothing on the page may change luminance back and forth faster than three times per second — including small icons and cursors.

**Related:** 2.3.1 Three Flashes or Below Threshold.

### 2.3.3 Animation from Interactions (Level AAA)

**Normative text (verbatim):**
> Motion animation triggered by interaction can be disabled, unless the animation is essential to the functionality or the information being conveyed.

**Intent (informative):** Parallax scrolling, zooming transitions, and elements that fly in on scroll or click can cause nausea, dizziness, and migraine for people with vestibular disorders. Letting users disable interaction-triggered motion (for example by honouring the OS "reduce motion" setting or an in-page toggle) avoids this, except where the motion *is* the information.

**How to test:**
1. Interact with the page (scroll, hover, click, focus) and note motion animation: parallax, scroll-jacking, smooth scroll, elements sliding/scaling in, page-transition wipes, bouncing buttons.
2. Enable the OS/browser "reduce motion" setting (`prefers-reduced-motion: reduce`) or any in-page motion toggle; reload; repeat the interactions.
3. All non-essential motion animation must be disabled or replaced by non-motion changes (instant appearance, cross-fade). Colour/opacity changes are fine.
4. Fail if non-essential interaction-triggered motion cannot be turned off.

**Sufficient techniques:**
- C39 Using the CSS prefers-reduced-motion query to prevent motion
- SCR40 Using the CSS prefers-reduced-motion query in JavaScript to prevent motion
- Gx: Allowing users to set a preference that prevents animation

**Implementation notes (HTML/CSS/ARIA/JS):**
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
  .parallax { transform: none !important; }
}
```
```js
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches || settings.reduceMotion;
if (!reduce) initParallax();
```

**Related:** 2.2.2 Pause, Stop, Hide, 2.3.1 Three Flashes or Below Threshold.

---
## Guideline 2.4 Navigable

> Provide ways to help users navigate, find content, and determine where they are.

Key terms (short): **navigated sequentially** — navigated in the order defined for advancing focus (from one element to the next) using a keyboard interface. **programmatically determined link context** — additional information that can be programmatically determined from relationships with a link, combined with the link text, and presented to users in different modalities (same paragraph, list item, table cell, or associated header cell). **ambiguous to users in general** — the purpose cannot be determined from the link and all information of the web page presented to the user simultaneously with the link. **set of web pages** — collection of web pages that share a common purpose and that are created by the same author, group or organization. **process** — series of user actions where each action is required in order to complete an activity. **focus indicator** (new in 2.2) — pixels that are changed to visually indicate when a user interface component is in a focused state. **perimeter** (new in 2.2) — continuous line forming the boundary of a shape not including shared pixels, or the minimum bounding box, whichever is shortest; for a 2 CSS px perimeter around a rectangle the area is 4h + 4w, around a circle 4πr. **minimum bounding box** (new in 2.2) — the smallest enclosing rectangle aligned to the horizontal axis within which all the points of a shape lie (for components wrapping onto multiple lines, based on how they would appear on a single line). **section** — a self-contained portion of written content that deals with one or more related topics or thoughts.

### 2.4.1 Bypass Blocks (Level A)

**Normative text (verbatim):**
> A mechanism is available to bypass blocks of content that are repeated on multiple web pages.

**Intent (informative):** Sighted mouse users glance past headers, navigation bars and sidebars; keyboard and screen-reader users would otherwise have to tab or listen through dozens of links on every page before reaching the main content. A skip link, landmark regions, or headings let them jump straight to what changed.

**How to test:**
1. Identify blocks repeated across pages: site header, primary/secondary navigation, cookie bar, sidebars, ad blocks.
2. Press Tab once from the top of the page: a "Skip to main content" link (visible, or visible on focus) is the most common mechanism. Activate it and confirm focus/scroll moves to the main content and the next Tab continues from there.
3. Alternatively, confirm that landmarks (`<main>`, `<nav>`, `<header>`) and/or a proper heading structure let screen-reader users jump past the repeated blocks (verify with a screen reader's landmark/heading list).
4. Each repeated block should be skippable; a single skip-to-main link generally suffices when all repeated content precedes `main`.
5. Fail if there is no skip mechanism and no landmark/heading structure that allows bypassing repeated content.

**Common failures:**
- No specific F-technique is listed; typical examples: a skip link that is permanently hidden with `display:none` (never focusable); a skip link whose target `id` does not exist so focus stays at the top; a page built entirely of `div`s with no landmarks or headings.

**Sufficient techniques:**
- Creating links to skip blocks of repeated material using one of the following techniques:
  - G1 Adding a link at the top of each page that goes directly to the main content area
  - G123 Adding a link at the beginning of a block of repeated content to go to the end of the block
  - G124 Adding links at the top of the page to each area of the content
- Grouping blocks of repeated material in a way that can be skipped using one of the following techniques:
  - ARIA11 Using ARIA landmarks to identify regions of a page
  - H69 Providing heading elements at the beginning of each section of content
  - PDF9 Providing headings by marking content with heading tags in PDF documents
  - H64 Using the title attribute of the iframe element
  - SCR28 Using an expandable and collapsible menu to bypass block of content

**Advisory techniques:**
- C6 Positioning content based on structural markup
- H97 Grouping related links using the nav element

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<a href="#main" class="skip-link">Skip to main content</a>
<header>…</header>
<nav aria-label="Primary">…</nav>
<main id="main" tabindex="-1">…</main>
```
```css
.skip-link { position:absolute; left:-999px; }
.skip-link:focus { left:1rem; top:1rem; }
```
`tabindex="-1"` on the target ensures focus actually moves in all browsers. Provide both a skip link and landmarks: the link serves sighted keyboard users, landmarks serve screen-reader users.

**Related:** 1.3.1 Info and Relationships, 2.4.3 Focus Order, 2.4.10 Section Headings, 3.2.3 Consistent Navigation.

### 2.4.2 Page Titled (Level A)

**Normative text (verbatim):**
> Web pages have titles that describe topic or purpose.

**Intent (informative):** The page title is the first thing a screen reader announces, what appears in browser tabs, history, bookmarks and search results. A descriptive, page-specific title lets users confirm they are on the right page and distinguish between open tabs without reading the content.

**How to test:**
1. Read the `<title>` element (DevTools or the browser tab). It must exist and be non-empty.
2. Check that it describes this page's topic or purpose, not just the site ("Home", "Untitled", the URL, or the same title on every page fail).
3. Best practice: the unique part first, then the site name ("Contact us – ASI GCBA"). Not strictly required but recommended.
4. For single-page applications, confirm that the title is updated when the view changes (`document.title`).
5. Fail if the title is missing, empty, or does not identify the page's contents.

**Common failures:**
- F25 Failure of Success Criterion 2.4.2 due to the title of a web page not identifying the contents
- Typical examples: every page titled with the company name only; a SPA whose title never changes; a title of "index.html".

**Sufficient techniques:**
- G88 Providing descriptive titles for web pages AND associating a title with a web page using one of the following techniques:
  - H25 Providing a title using the title element
  - PDF18 Specifying the document title using the Title entry in the document information dictionary of a PDF document

**Advisory techniques:**
- G127 Identifying a web page's relationship to a larger collection of web pages

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<title>Appointment booking – Step 2 of 4 – ASI GCBA</title>
```
```js
// SPA route change
document.title = `${routeTitle} – ${siteName}`;
```
Frames/iframes should also have a `title` attribute (see H64) though that is primarily 4.1.2/2.4.1 territory.

**Related:** 2.4.6 Headings and Labels, 2.4.8 Location, 3.2.3 Consistent Navigation.

### 2.4.3 Focus Order (Level A)

**Normative text (verbatim):**
> If a web page can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.

**Intent (informative):** Keyboard users build a mental model of the page from the order in which focus moves. If focus jumps unpredictably (because of positive `tabindex`, CSS reordering, or dialogs injected at the end of the DOM), the page becomes confusing or unusable for people who cannot see the whole layout, including screen-reader users and people with cognitive disabilities.

**How to test:**
1. Tab through the page and record the sequence. Compare with the visual/logical reading order: left-to-right, top-to-bottom in LTR languages, grouped by region, and following form field order.
2. Open menus, dialogs, disclosure panels and dynamically inserted content: focus should move into them when they open (dialogs) or they should be inserted right after their trigger in the sequence (dropdowns, inline expanders). On close, focus returns to the trigger.
3. Check that hidden/off-screen content (collapsed menus, inactive carousel slides, closed modals) is **not** in the tab order.
4. Inspect for `tabindex` values greater than 0 and CSS `order`/`flex-direction: row-reverse`/grid placement that make the visual order differ from DOM order.
5. Fail if the focus order changes meaning or makes operation confusing (e.g. "Submit" is focused before the fields it submits, a modal opens but focus stays behind it, focus lands on invisible elements).

**Common failures:**
- F44 Failure of Success Criterion 2.4.3 due to using tabindex to create a tab order that does not preserve meaning and operability
- F85 Failure of Success Criterion 2.4.3 due to using dialogs or menus that are not adjacent to their trigger control in the sequential navigation order
- Typical examples: a cookie dialog appended to the end of `<body>` so keyboard users tab through the whole page before reaching it; a two-column layout using `tabindex="1..n"` that zig-zags; a closed off-canvas menu whose links remain focusable.

**Sufficient techniques:**
- G59 Placing the interactive elements in an order that follows sequences and relationships within the content
- Giving focus to elements in an order that follows sequences and relationships within the content using one of the following techniques:
  - C27 Making the DOM order match the visual order
  - PDF3 Ensuring correct tab and reading order in PDF documents
- Changing a web page dynamically using one of the following techniques:
  - SCR26 Inserting dynamic content into the Document Object Model immediately following its trigger element
  - H102 Creating modal dialogs with the HTML dialog element
  - SCR27 Reordering page sections using the Document Object Model

**Implementation notes (HTML/CSS/ARIA/JS):**
```js
// Open modal: move focus in; close: restore focus
opener.addEventListener('click', () => { dialog.showModal(); dialog.querySelector('h2').focus(); });
dialog.addEventListener('close', () => opener.focus());
```
Use `tabindex="0"` / `-1` only; never positive values. Keep DOM order equal to visual order instead of using CSS `order` to rearrange interactive content. Hide inactive content with `hidden`/`display:none` or the `inert` attribute so it leaves the tab sequence.

**Related:** 1.3.2 Meaningful Sequence, 2.1.1 Keyboard, 2.1.2 No Keyboard Trap, 2.4.7 Focus Visible, 3.2.1 On Focus.

### 2.4.4 Link Purpose (In Context) (Level A)

**Normative text (verbatim):**
> The purpose of each link can be determined from the link text alone or from the link text together with its programmatically determined link context, except where the purpose of the link would be ambiguous to users in general.

**Intent (informative):** Screen-reader users often pull up a list of links or tab from link to link, hearing only the link text; people with cognitive or motor disabilities want to know where a link goes before activating it. Link text such as "click here" or "read more" repeated many times is meaningless out of context. The criterion allows the surrounding sentence, list item, table cell or associated header to supply the context, as long as that context is programmatically associated.

**How to test:**
1. List all links (screen reader links list, or `document.querySelectorAll('a[href]')`), including image links (use the image's alt / accessible name).
2. For each link, ask: is the purpose clear from the link text alone? If not, is it clear from the text in the *same* sentence, paragraph, list item, table cell, or the table header cell associated with that cell, or from `aria-label`/`aria-labelledby`?
3. Context in a preceding heading alone or in a different paragraph does **not** count (H80 is only advisory).
4. Image-only links must have an accessible name (alt text) that conveys the destination, not "image" or the file name.
5. Links with identical text that go to different destinations must be distinguishable via their programmatic context.
6. The only exception: links whose purpose is ambiguous to *everyone* (e.g. a single word "guava" in a sentence that could lead anywhere).
7. Fail if any link's purpose cannot be determined from its text plus programmatic context.

**Common failures:**
- F63 Failure of Success Criterion 2.4.4 due to providing link context only in content that is not related to the link
- F89 Failure of Success Criteria 2.4.4, 2.4.9 and 4.1.2 due to not providing an accessible name for an image which is the only content in a link
- Typical examples: a news list with ten "Read more" links where the article title is in a separate heading element not programmatically associated; a social icon link with an empty-alt image and no label; a "Download" link in a table where the file name is in another column with no header association.

**Sufficient techniques:**
- G91 Providing link text that describes the purpose of a link
- H30 Providing link text that describes the purpose of a link for anchor elements
- H24 Providing text alternatives for the area elements of image maps
- Allowing the user to choose short or long link text using one of the following techniques:
  - G189 Providing a control near the beginning of the web page that changes the link text
  - SCR30 Using scripts to change the link text
- G53 Identifying the purpose of a link using link text combined with the text of the enclosing sentence
- Providing a supplemental description of the purpose of a link using one of the following techniques:
  - H33 Supplementing link text with the title attribute
  - C7 Using CSS to hide a portion of the link text
- Identifying the purpose of a link using link text combined with programmatically determined link context using one of the following techniques:
  - ARIA7 Using aria-labelledby for link purpose
  - ARIA8 Using aria-label for link purpose
  - H77 Identifying the purpose of a link using link text combined with its enclosing list item
  - H78 Identifying the purpose of a link using link text combined with its enclosing paragraph
  - H79 Identifying the purpose of a link in a data table using the link text combined with its enclosing table cell and associated table header cells
  - H81 Identifying the purpose of a link in a nested list using link text combined with the parent list item under which the list is nested
  - PDF11 Providing links and link text using the Link annotation and the /Link structure element in PDF documents
  - PDF13 Providing replacement text using the /Alt entry for links in PDF documents
- G91 Providing link text that describes the purpose of a link AND semantically indicating links

**Advisory techniques:**
- H2 Combining adjacent image and text links for the same resource
- H80 Identifying the purpose of a link using link text combined with the preceding heading element
- G201 Giving users advanced warning when opening a new window
- SCR24 Using progressive enhancement to open new windows on user request

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<!-- Good: descriptive text -->
<a href="/report-2025.pdf">Download the 2025 annual report (PDF, 2 MB)</a>

<!-- Acceptable: visually "Read more", accessible name includes the title -->
<article>
  <h3 id="a1">Bike lanes expanded in Palermo</h3>
  <p>…</p>
  <a href="/news/1" aria-labelledby="rm1 a1"><span id="rm1">Read more</span></a>
</article>

<!-- Icon link must be named -->
<a href="https://x.com/gcba"><img src="x.svg" alt="GCBA on X"></a>
```
Remember 2.5.3 Label in Name: if you use `aria-label`, it must contain the visible text ("Read more: Bike lanes expanded…").

**Related:** 2.4.9 Link Purpose (Link Only), 1.1.1 Non-text Content, 2.5.3 Label in Name, 4.1.2 Name, Role, Value, 3.2.4 Consistent Identification.

### 2.4.5 Multiple Ways (Level AA)

**Normative text (verbatim):**
> More than one way is available to locate a web page within a set of web pages except where the web page is the result of, or a step in, a process.

**Intent (informative):** Different users find content in different ways: some navigate hierarchical menus, some search, some scan a site map or table of contents. Offering at least two of these helps people with cognitive disabilities who struggle with complex navigation and screen-reader users for whom search can be far faster than exploring menus. Pages that are steps in a process (checkout step 3) are excepted because they are only meaningful in sequence.

**How to test:**
1. Confirm the page belongs to a set of web pages (shared purpose, same author/organization).
2. Count the independent ways to reach this page: site-wide navigation menu, site search, site map, table of contents, list of related links, links from the home page to all pages, breadcrumb + hierarchy.
3. At least two must exist and work (search must actually index this page; site map must list it).
4. Pages that are the result of or a step in a process are exempt.
5. Fail if only one way exists (for example, only a navigation menu and no search or site map).

**Sufficient techniques:**
- Using two or more of the following techniques:
  - G125 Providing links to navigate to related web pages
  - G64 Providing a Table of Contents
  - G63 Providing a site map
  - G161 Providing a search function to help users find content
  - G126 Providing a list of links to all other web pages
  - G185 Linking to all of the pages on the site from the home page

**Advisory techniques:**
- PDF2 Creating bookmarks in PDF documents
- H99 Provide a page-selection mechanism

**Implementation notes (HTML/CSS/ARIA/JS):** Typical AA-compliant setup: global `<nav>` menu + a `<form role="search">` in the header + a `/sitemap` page linked from the footer. For small sites, a home page linking to every page plus a menu suffices.

**Related:** 2.4.8 Location, 3.2.3 Consistent Navigation, 2.4.1 Bypass Blocks.

### 2.4.6 Headings and Labels (Level AA)

**Normative text (verbatim):**
> Headings and labels describe topic or purpose.

**Intent (informative):** Clear headings let users (especially screen-reader users navigating by heading, and people with cognitive disabilities scanning a page) understand what each section contains; clear labels tell users what to enter in a field. The criterion is about *descriptiveness*, not about whether headings/labels exist or are programmatically associated (that is 1.3.1, 3.3.2, 4.1.2).

**How to test:**
1. List all headings (`h1`–`h6`, `role="heading"`) and all form labels/legends (visible text).
2. Check each heading describes the content of the section that follows it; generic headings ("Section 1", "More") or decorative taglines used as headings fail.
3. Check each label/legend describes the purpose of the control or group ("Email address", not "Field 3"); when several similar fields exist (three "Address" fields), each label must be distinguishable.
4. Headings do not need to be in a complete hierarchy for this criterion — only descriptive.
5. Fail if any heading or label is non-descriptive or misleading.

**Sufficient techniques:**
- G130 Providing descriptive headings
- G131 Providing descriptive labels

**Advisory techniques:**
- G201 Giving users advanced warning when opening a new window
- SCR24 Using progressive enhancement to open new windows on user request

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<h2>Opening hours</h2>            <!-- not "Information" -->
<label for="dob">Date of birth (DD/MM/YYYY)</label>
<fieldset><legend>Billing address</legend> … </fieldset>
```

**Related:** 1.3.1 Info and Relationships, 2.4.10 Section Headings, 3.3.2 Labels or Instructions, 2.5.3 Label in Name, 2.4.2 Page Titled.

### 2.4.7 Focus Visible (Level AA)

**Normative text (verbatim):**
> Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible.

**Intent (informative):** Sighted keyboard users (including people with motor disabilities and many low-vision users) need to see where focus is to know which element will respond to the next keystroke. Removing the browser's outline without a replacement makes keyboard navigation blind. The criterion requires that *some* visible indicator exists; its size and contrast are covered by 1.4.11 (indicator vs adjacent colours) and the AAA 2.4.13.

**How to test:**
1. Tab through every focusable element on the page, including custom widgets and elements inside iframes, in each page variation (desktop/mobile breakpoints, dark mode).
2. At every stop there must be a visible change that identifies the focused element: an outline, border, background change, underline, caret in a text field, etc.
3. Check CSS for `outline: none` / `outline: 0` / `:focus { outline: 0 }` without an alternative `:focus`/`:focus-visible` style; check that `box-shadow`-based indicators are not clipped by `overflow: hidden`.
4. Where the indicator is only visible on some backgrounds (e.g. a blue outline on a blue header) it is not visible — fail those instances (also 1.4.11).
5. Fail if any focusable element shows no visible focus indication.

**Common failures:**
- F55 Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
- F78 Failure of Success Criterion 1.4.11, 2.4.7 and 2.4.13 due to styling element outlines and borders in a way that removes or renders non-visible the visual focus indicator
- Typical examples: a CSS reset with `*:focus { outline: none; }`; cards that are focusable but only change on `:hover`; a focus ring clipped by `overflow:hidden` on the parent.

**Sufficient techniques:**
- G149 Using user interface components that are highlighted by the user agent when they receive focus
- C15 Using CSS to change the presentation of a user interface component when it receives focus
- G165 Using the default focus indicator for the platform so that high visibility default focus indicators will carry over
- G195 Using an author-supplied, visible focus indicator
- C40 Creating a two-color focus indicator to ensure sufficient contrast with all components
- C45 Using CSS :focus-visible to provide keyboard focus indication
- SCR31 Using script to change the background color or border of the element with focus

**Implementation notes (HTML/CSS/ARIA/JS):**
```css
/* Keep a strong, universal indicator; :focus-visible avoids rings on mouse click */
:focus-visible { outline: 3px solid #1a56db; outline-offset: 2px; }
/* Two-colour ring works on any background */
:focus-visible { outline: 2px solid #fff; box-shadow: 0 0 0 4px #1a56db; }
```
Never write `outline: none` without a replacement rule. Do not remove focus via `blur()` on focus.

**Related:** 2.4.11 Focus Not Obscured (Minimum), 2.4.13 Focus Appearance, 1.4.11 Non-text Contrast, 2.4.3 Focus Order, 2.1.1 Keyboard.

### 2.4.8 Location (Level AAA)

**Normative text (verbatim):**
> Information about the user's location within a set of web pages is available.

**Intent (informative):** Breadcrumbs, highlighted current navigation items, site maps and "step x of y" indicators help people with cognitive disabilities, short attention spans and screen-reader users understand where they are and how to get back.

**How to test:**
1. On pages belonging to a set, look for at least one location cue: breadcrumb trail, current item highlighted in navigation (and marked with `aria-current="page"`), site map showing the current page, page title that identifies its position in the hierarchy.
2. The cue must be available to assistive technology (not colour alone).
3. Fail if no location information is provided.

**Sufficient techniques:**
- G65 Providing a breadcrumb trail
- G63 Providing a site map
- G128 Indicating current location within navigation bars
- ARIA26 Using aria-current to identify the current item in a set
- G127 Identifying a web page's relationship to a larger collection of web pages

**Advisory techniques:**
- PDF14 Providing running headers and footers in PDF documents
- PDF17 Specifying consistent page numbering for PDF documents

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<nav aria-label="Breadcrumb">
  <ol><li><a href="/">Home</a></li><li><a href="/services">Services</a></li>
      <li><a href="/services/permits" aria-current="page">Permits</a></li></ol>
</nav>
```

**Related:** 2.4.2 Page Titled, 2.4.5 Multiple Ways, 3.2.3 Consistent Navigation.

### 2.4.9 Link Purpose (Link Only) (Level AAA)

**Normative text (verbatim):**
> A mechanism is available to allow the purpose of each link to be identified from link text alone, except where the purpose of the link would be ambiguous to users in general.

**Intent (informative):** The AAA version requires that link text alone (its accessible name) conveys the purpose, without depending on surrounding context, so that link lists and link-by-link navigation are fully meaningful. A mechanism (e.g. a toggle that expands link text) is acceptable.

**How to test:**
1. Pull the links list from a screen reader (or compute each link's accessible name).
2. Each name, read in isolation, must identify the destination/purpose: "Read more" / "Here" / "Download" alone fail unless a mechanism expands them.
3. If a mechanism exists (e.g. a "show full link text" control), activate it and re-check.
4. Fail if any link's accessible name alone does not convey its purpose and no mechanism is available.

**Common failures:**
- F84 Failure of Success Criterion 2.4.9 due to using a non-specific link such as "click here" or "more" without a mechanism to change the link text to specific text.
- F89 Failure of Success Criteria 2.4.4, 2.4.9 and 4.1.2 due to not providing an accessible name for an image which is the only content in a link

**Sufficient techniques:**
- ARIA8 Using aria-label for link purpose
- G91 Providing link text that describes the purpose of a link
- H30 Providing link text that describes the purpose of a link for anchor elements
- H24 Providing text alternatives for the area elements of image maps
- Allowing the user to choose short or long link text using one of the following techniques:
  - G189 Providing a control near the beginning of the web page that changes the link text
  - SCR30 Using scripts to change the link text
- Providing a supplemental description of the purpose of a link using one of the following techniques:
  - C7 Using CSS to hide a portion of the link text
- Semantically indicating links using one of the following techniques:
  - PDF11 Providing links and link text using the Link annotation and the /Link structure element in PDF documents
  - PDF13 Providing replacement text using the /Alt entry for links in PDF documents

**Advisory techniques:**
- H2 Combining adjacent image and text links for the same resource
- H33 Supplementing link text with the title attribute
- G201 Giving users advanced warning when opening a new window
- SCR24 Using progressive enhancement to open new windows on user request

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<a href="/news/1">Read more <span class="visually-hidden">about bike lanes expanded in Palermo</span></a>
```
Keep the visible words at the start of the name (2.5.3).

**Related:** 2.4.4 Link Purpose (In Context), 2.5.3 Label in Name.

### 2.4.10 Section Headings (Level AAA)

**Normative text (verbatim):**
> Section headings are used to organize the content.
>
> NOTE 1: "Heading" is used in its general sense and includes titles and other ways to add a heading to different types of content.
>
> NOTE 2: This success criterion covers sections within writing, not user interface components. User interface components are covered under Success Criterion 4.1.2.

**Intent (informative):** Long written content broken into sections with headings is easier to scan, navigate by heading (screen readers), and comprehend (cognitive disabilities). The criterion concerns prose/document sections, not UI chrome.

**How to test:**
1. Review written content: articles, policies, help pages, long forms.
2. Each distinct section/topic must start with a heading (marked up as a heading — see 1.3.1 — but this criterion checks presence/organisation).
3. Fail if long content is presented as undifferentiated blocks of text without section headings.

**Sufficient techniques:**
- G141 Organizing a page using headings
- H69 Providing heading elements at the beginning of each section of content

**Implementation notes (HTML/CSS/ARIA/JS):** Use a single `h1` and a nested `h2`/`h3` outline; one heading per section, before its content; do not use bold paragraphs as pseudo-headings.

**Related:** 1.3.1 Info and Relationships, 2.4.6 Headings and Labels, 2.4.1 Bypass Blocks.

### 2.4.11 Focus Not Obscured (Minimum) (Level AA) — New in 2.2

**Normative text (verbatim):**
> When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.
>
> NOTE 1: Where content in a configurable interface can be repositioned by the user, then only the initial positions of user-movable content are considered for testing and conformance of this success criterion.
>
> NOTE 2: Content opened by the user may obscure the component receiving focus. If the user can reveal the focused component without advancing the keyboard focus, the component with focus is not considered visually hidden due to author-created content.

**Intent (informative):** Sticky headers/footers, cookie banners, chat widgets and non-modal overlays frequently sit on top of the element that currently has keyboard focus, so a sighted keyboard user cannot see what they are about to activate. This criterion requires that the focused component is at least partially visible (not *entirely* hidden) by content the author placed on the page. It complements 2.4.7 (an indicator exists) by ensuring the indicator can actually be seen.

**How to test:**
1. Tab through the page on viewports where sticky/fixed elements exist (desktop and mobile breakpoints), with cookie banners, chat bubbles, toolbars and toasts in their initial state.
2. At each stop, check whether the focused component is **entirely** covered by author-created fixed/sticky/overlay content. Partially covered passes at AA (fails at 2.4.12 AAA).
3. Pay attention to the last few elements before a sticky footer and the first elements under a sticky header after a skip link or in-page anchor; also to focus moving into content behind an open non-modal panel.
4. Apply NOTE 2: if the obscuring content was opened by the user (e.g. a dropdown the user opened) and can be closed (Escape) without moving focus, it does not count as a failure.
5. Apply NOTE 1: for user-movable widgets (draggable chat window), test the initial position only.
6. Fail if any focused component is completely hidden by author content.

**Common failures:**
- F110 Failure of Success Criterion 2.4.11 Focus Not Obscured (Minimum) due to a sticky footer or header completely hiding focused elements
- Typical examples: a fixed cookie consent bar covering the footer links while tabbing; a sticky header that hides the first field after a skip link; a persistent chat panel covering a "Submit" button.

**Sufficient techniques:**
- C43 Using CSS scroll-padding to un-obscure content

**Implementation notes (HTML/CSS/ARIA/JS):**
```css
/* Reserve space so browsers scroll focused elements out from under sticky bars */
html { scroll-padding-top: 80px; scroll-padding-bottom: 120px; }
```
Alternatives: make banners `position: static` or modal (focus moves into them), size sticky bars small, or on `focusin` scroll the target into view with `scrollIntoView({block:'center'})`.

**Related:** 2.4.7 Focus Visible, 2.4.12 Focus Not Obscured (Enhanced), 2.4.13 Focus Appearance, 1.4.10 Reflow, 2.4.3 Focus Order.

### 2.4.12 Focus Not Obscured (Enhanced) (Level AAA) — New in 2.2

**Normative text (verbatim):**
> When a user interface component receives keyboard focus, no part of the component is hidden by author-created content.

**Intent (informative):** The AAA version requires the focused component to be fully visible: not even partially covered by sticky or overlay content, so the complete focus indicator and the whole control are seen.

**How to test:**
1. Repeat the 2.4.11 procedure.
2. Fail if **any part** of a focused component is covered by author-created content (including partial overlap with a sticky footer, header, or floating widget).

**Common failures (listed without IDs in the Quick Reference):**
- An interaction that causes content to appear over the component with keyboard focus, visually covering part of the focus indicator. This behavior might be encountered with advertising or promotional material meant to provide more information about a product as the user navigates through a catalogue.
- A page has a sticky footer (attached to the bottom of the viewport). When tabbing down the page, a focused item is partially obscured by the footer because content in the viewport scrolls without sufficient scroll padding.

**Sufficient techniques:**
- C43 Using CSS scroll-padding to un-obscure content

**Implementation notes (HTML/CSS/ARIA/JS):** Set `scroll-padding` equal to or larger than the full height of sticky bars plus the focus ring offset; avoid floating promotional overlays that react to navigation.

**Related:** 2.4.11 Focus Not Obscured (Minimum), 2.4.13 Focus Appearance.

### 2.4.13 Focus Appearance (Level AAA) — New in 2.2

**Normative text (verbatim):**
> When the keyboard focus indicator is visible, an area of the focus indicator meets all the following:
>
> - is at least as large as the area of a 2 CSS pixel thick perimeter of the unfocused component or sub-component, and
> - has a contrast ratio of at least 3:1 between the same pixels in the focused and unfocused states.
>
> Exceptions:
>
> - The focus indicator is determined by the user agent and cannot be adjusted by the author, or
> - The focus indicator and the indicator's background color are not modified by the author.
>
> NOTE 1: What is perceived as the user interface component or sub-component (to determine the perimeter) depends on its visual presentation. The visual presentation includes the component's visible content, border, and component-specific background. It does not include shadow and glow effects outside the component's content, background, or border.
>
> NOTE 2: Examples of sub-components that may receive a focus indicator are menu items in an opened drop-down menu, or focusable cells in a grid.
>
> NOTE 3: Contrast calculations can be based on colors defined within the technology (such as HTML, CSS, and SVG). Pixels modified by user agent resolution enhancements and anti-aliasing can be ignored.

**Intent (informative):** 2.4.7 only requires that *some* indicator exists; many indicators are a 1 px faint line that low-vision users cannot find. This criterion sets a minimum **size** (equivalent to a 2 px thick outline around the component) and a minimum **change** (3:1 contrast between the focused and unfocused state of the same pixels), so the indicator is reliably noticeable. The exceptions cover untouched browser-default indicators.

**How to test:**
1. For each focusable component with an author-styled focus indicator (if the author never styled focus or background, the exception applies), determine the component's perimeter: for a rectangle of width w and height h, a 2 CSS px perimeter has area 4h + 4w (for a circle 4πr); use the minimum bounding box if shorter.
2. Measure the area of pixels that change when focus is received (e.g. a 2 px solid outline all the way round = pass; a 1 px outline = half the area = fail unless something else changes; a 4 px underline only = 4w, usually less than 4h+4w = fail; a full background change of the component normally far exceeds the perimeter area = pass if contrast is met).
3. For those changed pixels, compute the contrast ratio between their colour in the unfocused state and in the focused state: must be ≥ 3:1 (e.g. white page → #1a56db outline ≈ 6:1 pass; light grey → white 1.3:1 fail).
4. Sub-components (menu items, grid cells, tabs) are measured against their own perimeter.
5. Shadows/glows outside the component do not count toward the component's perimeter but *can* be the indicator area if they meet the size and contrast change.
6. Fail if the indicator area is smaller than the 2 px perimeter area or the focused/unfocused change is < 3:1.

**Common failures:**
- F55 Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
- F78 Failure of Success Criterion 1.4.11, 2.4.7 and 2.4.13 due to styling element outlines and borders in a way that removes or renders non-visible the visual focus indicator
- Typical examples: `outline: 1px dotted`; a focus style that only changes text colour from #333 to #000; a thin 1 px underline on links as the sole indicator.

**Sufficient techniques:**
- G195 Using an author-supplied, visible focus indicator
- C40 Creating a two-color focus indicator to ensure sufficient contrast with all components
- C41 Creating a strong focus indicator within the component

**Implementation notes (HTML/CSS/ARIA/JS):**
```css
/* Meets size (≥ 2 px solid perimeter) and change contrast (outline colour vs page bg ≥ 3:1) */
:focus-visible { outline: 2px solid #0b4ea2; outline-offset: 2px; }
/* Dark/light-safe two-colour variant */
:focus-visible { outline: 2px solid #0b4ea2; box-shadow: 0 0 0 4px #fff; }
```
Avoid dotted/dashed outlines (they halve the area), 1 px rings, and colour-only text changes.

**Related:** 2.4.7 Focus Visible, 1.4.11 Non-text Contrast, 2.4.11 Focus Not Obscured (Minimum), 1.4.3 Contrast (Minimum).

---
## Guideline 2.5 Input Modalities

> Make it easier for users to operate functionality through various inputs beyond keyboard.

Key terms (short): **pointer input** — input from a device that can target a specific coordinate (or set of coordinates) on a screen, such as a mouse, pen, or touch contact. **single pointer** — an input modality that only targets a single point on the page/screen at a time – such as a mouse, single finger on a touch screen, or stylus (clicks, double clicks, taps, dragging motions and single-finger swipes are single-pointer interactions; two-finger gestures or simultaneous mouse+stylus are multipoint). **down-event** — platform event that occurs when the trigger stimulus of a pointer is depressed (touchstart, mousedown). **up-event** — platform event that occurs when the trigger stimulus of a pointer is released (touchend, mouseup). **dragging movement** (new in 2.2) — an operation where the pointer engages with an element on the down-event and the element (or a representation of its position) follows the pointer until an up-event. **target** — region of the display that will accept a pointer action, such as the interactive area of a user interface component (overlapping areas of different targets are not counted). **CSS pixel** — visual angle of about 0.0213 degrees; the density-independent CSS reference pixel. **label** — text or other component with a text alternative that is presented to a user to identify a component within web content. **name** — text by which software can identify a component within web content to the user (the accessible name; unrelated to the HTML `name` attribute).

### 2.5.1 Pointer Gestures (Level A)

**Normative text (verbatim):**
> All functionality that uses multipoint or path-based gestures for operation can be operated with a single pointer without a path-based gesture, unless a multipoint or path-based gesture is essential.
>
> NOTE: This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

**Intent (informative):** Pinch-to-zoom, two-finger rotate, swipe-to-dismiss and draw-a-shape gestures are impossible or unreliable for people with limited dexterity, tremor, or who use a head pointer, eye-gaze or a single-switch "mouse". Providing simple single-pointer alternatives (tap, click, double-click, press-and-hold) keeps the function available. Dragging is addressed separately in 2.5.7.

**How to test:**
1. On a touch device/emulator and with a mouse, list every function operated by multipoint gestures (pinch, two-finger scroll/rotate) or path-based gestures (swipe, flick, drawing a path, slide-to-unlock) that the *page's* scripts interpret (browser-native pinch zoom is out of scope).
2. For each, find an alternative that needs only single taps/clicks without a path: zoom +/- buttons, next/previous buttons for swipe carousels, a "dismiss" button for swipe-to-dismiss, incremental buttons instead of a drawn path.
3. The alternative must achieve the same result and be discoverable.
4. The essential exception is rare (e.g. a signature drawn in a signature app, a drawing in a freehand painting tool).
5. Fail if any multipoint or path-based gesture has no single-pointer, non-path alternative and is not essential.

**Common failures:**
- F105 Failure of Success Criterion 2.5.1 due to providing functionality via a path-based gesture without simple pointer alternative
- Typical examples: a map that only zooms via pinch; an image gallery navigable only by swipe; a swipe-to-delete list row with no other delete control.

**Sufficient techniques:**
- G215 Providing controls to achieve the same result as path based or multipoint gestures
- G216 Providing single point activation for a control slider

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<div class="map" …>
  <button type="button" aria-label="Zoom in">+</button>
  <button type="button" aria-label="Zoom out">−</button>
</div>
<div class="carousel">…<button type="button">Previous</button><button type="button">Next</button></div>
```
Keep gesture support as an enhancement; the buttons are the baseline.

**Related:** 2.5.7 Dragging Movements, 2.5.2 Pointer Cancellation, 2.1.1 Keyboard, 2.5.6 Concurrent Input Mechanisms.

### 2.5.2 Pointer Cancellation (Level A)

**Normative text (verbatim):**
> For functionality that can be operated using a single pointer, at least one of the following is true:
>
> No Down-Event: The down-event of the pointer is not used to execute any part of the function;
>
> Abort or Undo: Completion of the function is on the up-event, and a mechanism is available to abort the function before completion or to undo the function after completion;
>
> Up Reversal: The up-event reverses any outcome of the preceding down-event;
>
> Essential: Completing the function on the down-event is essential.
>
> NOTE 1: Functions that emulate a keyboard or numeric keypad key press are considered essential.
>
> NOTE 2: This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

**Intent (informative):** People with tremors or imprecise motor control often touch the wrong target; if the action fires on the down-event (touchstart/mousedown) they have no chance to correct. Firing on the up-event lets them slide off the target to cancel, which is the default behaviour of native `click`. On-screen piano keys or keyboard emulators legitimately need down-event activation.

**How to test:**
1. For each interactive control, press down (mouse button or finger) on it, then move the pointer **off** the control before releasing. The function must **not** execute (No Down-Event / native click behaviour).
2. If a function does execute on down (e.g. press-and-hold, drag start), check for an abort (release outside, Escape) before completion, or an undo after completion (Up Reversal or Abort/Undo).
3. Inspect code for `mousedown`, `touchstart`, `pointerdown` handlers that trigger actions directly.
4. Key-emulation controls (virtual keyboard, piano, game controls) are essential and excepted.
5. Fail if any single-pointer function completes on the down-event without abort/undo/reversal and is not essential.

**Common failures:**
- F101 Failure of Success Criterion 2.5.2 due to activating a control on the down-event
- Typical examples: a "Delete" icon bound to `touchstart` to feel faster; a custom button component firing on `pointerdown`; a game "fire" button (acceptable only if essential).

**Sufficient techniques:**
- G210 Ensuring that drag-and-drop actions can be cancelled
- G212 Using native controls to ensure functionality is triggered on the up-event.
- Touch events are only triggered when touch is removed from a control (Potential future technique)

**Implementation notes (HTML/CSS/ARIA/JS):**
```js
// Correct: 'click' fires on up-event and is cancelled by moving off the target
btn.addEventListener('click', doAction);
// Incorrect:
btn.addEventListener('pointerdown', doAction);
// Drag: allow Escape to abort and drop-outside to cancel
```

**Related:** 2.5.1 Pointer Gestures, 2.5.7 Dragging Movements, 3.3.4 Error Prevention (Legal, Financial, Data).

### 2.5.3 Label in Name (Level A)

**Normative text (verbatim):**
> For user interface components with labels that include text or images of text, the name contains the text that is presented visually.
>
> NOTE: A best practice is to have the text of the label at the start of the name.

**Intent (informative):** Speech-input users activate controls by saying their visible label ("click Search"). If the accessible name differs from the visible text (e.g. `aria-label="Find"` on a button that shows "Search"), the voice command fails. Screen-reader users who can also see the screen are equally confused when what is spoken differs from what is shown. The visible text must therefore be *contained* in the accessible name, ideally at its start.

**How to test:**
1. For every control with a visible text label (buttons, links, form fields with visible labels, tabs, menu items), including images of text used as labels (e.g. a "Submit" image button), compute the accessible name (DevTools Accessibility pane or a screen reader).
2. The accessible name must contain the visible label text as a whole string, in the same word order (case and punctuation differences are tolerated). Best practice: the visible text at the start of the name.
3. Watch for `aria-label`, `aria-labelledby`, `title`, and visually-hidden text that replace rather than extend the visible label; and for controls with visible text but no accessible name at all (F111).
4. Icon-only controls (no visible text) are out of scope of this criterion (but need a name for 4.1.2).
5. Fail if any control's accessible name does not include its visible label text.

**Common failures:**
- F96 Failure due to the accessible name not containing the visible label text
- F111 Failure of Success Criteria 1.3.1, 2.5.3, and 4.1.2 due to a control with visible label text but no accessible name
- Accessible name contains the visible label text, but the words of the visible label are not in the same order as they are in the visible label text (Potential future technique)
- Accessible name contains the visible label text, but one or more other words are interspersed in the label (Potential future technique)
- Typical examples: `<button aria-label="Submit form">Send</button>`; a link showing "Learn more" with `aria-label="Product details"`; a `<label>` reading "Email" while `aria-label="E-mail address (required)"` — acceptable only if "Email" matches; "E-mail" does not.

**Sufficient techniques:**
- G208 Including the text of the visible label as part of the accessible name
- G211 Matching the accessible name to the visible label

**Advisory techniques:**
- G162 Positioning labels to maximize predictability of relationships
- If an icon has no accompanying text, consider using its hover text as its accessible name (Potential future technique)

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<!-- Good: name == visible text -->
<button type="button">Search</button>
<!-- Good: name starts with visible text and extends it -->
<a href="/news/1" aria-label="Read more about bike lanes in Palermo">Read more</a>
<!-- Bad: name replaces visible text -->
<button type="button" aria-label="Find">Search</button>
```
Prefer no `aria-label` on controls that already have visible text; if you must extend the name, keep the visible text first.

**Related:** 4.1.2 Name, Role, Value, 1.3.1 Info and Relationships, 2.4.4 Link Purpose (In Context), 3.3.2 Labels or Instructions, 2.4.6 Headings and Labels.

### 2.5.4 Motion Actuation (Level A)

**Normative text (verbatim):**
> Functionality that can be operated by device motion or user motion can also be operated by user interface components and responding to the motion can be disabled to prevent accidental actuation, except when:
>
> Supported Interface: The motion is used to operate functionality through an accessibility supported interface;
>
> Essential: The motion is essential for the function and doing so would invalidate the activity.

**Intent (informative):** Shake-to-undo, tilt-to-scroll, or wave-at-camera controls cannot be performed by people whose device is mounted to a wheelchair, who have tremors (causing accidental triggers), or who have limited movement. The function must also be available through ordinary UI controls, and the motion response must be switchable off.

**How to test:**
1. Identify functionality triggered by device motion (accelerometer/gyroscope: shake, tilt, rotate) or user motion (camera/gesture detection) implemented by the content.
2. Verify an equivalent user interface control exists for each (e.g. an "Undo" button for shake-to-undo).
3. Verify a setting to disable motion response exists in the content, or that the content honours the OS-level motion-reduction/motion-actuation setting.
4. Exceptions: motion used through an accessibility-supported interface (e.g. OS-level switch control), or essential (a pedometer app, a motion-controlled game where motion *is* the activity).
5. Fail if motion-operated functionality lacks a UI alternative or cannot be disabled.

**Common failures:**
- F106 Failure due to inability to deactivate motion actuation
- FXXX: Failure of Success Criterion 2.5.4 due to disrupting or disabling system level features which allow the user to disable motion actuation
- Typical examples: a form that clears on shake with no setting to disable; a 360° viewer that pans only by tilting; a web app that re-enables motion input after the user turned it off at OS level.

**Sufficient techniques:**
- G213 Provide conventional controls and an application setting for motion activated input
- GXXX: Supporting system level features which allow the user to disable motion actuation

**Implementation notes (HTML/CSS/ARIA/JS):**
```js
if (settings.motionInput && !navigator.userAgentReducedMotion) {
  window.addEventListener('devicemotion', onShake);   // optional enhancement
}
undoButton.addEventListener('click', undo);           // always available
```
Provide the toggle in the app settings and default to honouring OS preferences.

**Related:** 2.1.1 Keyboard, 2.5.1 Pointer Gestures, 2.3.3 Animation from Interactions, 2.5.6 Concurrent Input Mechanisms.

### 2.5.5 Target Size (Enhanced) (Level AAA)

**Normative text (verbatim):**
> The size of the target for pointer inputs is at least 44 by 44 CSS pixels except when:
>
> Equivalent: The target is available through an equivalent link or control on the same page that is at least 44 by 44 CSS pixels;
>
> Inline: The target is in a sentence or block of text;
>
> User Agent Control: The size of the target is determined by the user agent and is not modified by the author;
>
> Essential: A particular presentation of the target is essential to the information being conveyed.

**Intent (informative):** Large targets are easier to hit for people with tremors, limited dexterity, large fingers on small touch screens, or who use a stylus/head pointer imprecisely. 44 × 44 CSS px roughly matches platform guidance for a comfortable touch target. Inline text links and unstyled native controls are excepted.

**How to test:**
1. For each pointer target (buttons, links, icons, form controls, custom controls, list rows that are clickable), measure the clickable area in CSS pixels (DevTools box model: padding and border count; margin does not, unless it is part of the hit area).
2. Both width and height must be ≥ 44 px, unless: an equivalent ≥ 44 px control for the same function exists on the page; the target is a link within a sentence/block of text; the size is the user agent's default and the author did not style it; or the presentation is essential (e.g. a pin on a map at true scale).
3. Overlapping areas between different targets are not counted.
4. Fail if any non-excepted target is smaller than 44 × 44 CSS px.

**Common failures (listed without ID in the Quick Reference):**
- Failure of Success Criterion 2.5.5 due to target being less than 44 by 44 CSS pixels
- Typical examples: 24 px icon buttons in a toolbar; pagination numbers 20 px wide; a 16 px checkbox styled by the author.

**Sufficient techniques:**
- C44 Using CSS to ensure targets are at least 44 by 44 CSS pixels

**Advisory techniques:**
- Ensuring inline links provide sufficiently large activation target

**Implementation notes (HTML/CSS/ARIA/JS):**
```css
.icon-button { min-width: 44px; min-height: 44px; display: inline-grid; place-items: center; }
```
Padding around a 24 px icon to reach 44 px is enough; the visible icon need not grow.

**Related:** 2.5.8 Target Size (Minimum), 1.4.4 Resize Text, 1.4.10 Reflow.

### 2.5.6 Concurrent Input Mechanisms (Level AAA)

**Normative text (verbatim):**
> Web content does not restrict use of input modalities available on a platform except where the restriction is essential, required to ensure the security of the content, or required to respect user settings.

**Intent (informative):** Users switch between mouse, touch, keyboard, stylus and speech — often within one session (e.g. a tablet with a keyboard, a laptop with a touch screen, an AT that emulates a different input). Content that assumes "touch device = no keyboard" or "desktop = mouse only" (e.g. by disabling keyboard handlers after detecting touch) locks those users out.

**How to test:**
1. Review input-handling code and behaviour: does the page detect a modality (touch, `pointer: coarse`, user agent) and then disable or ignore other modalities (e.g. removes keyboard support, hides hover-only UI, ignores mouse events after a touch)?
2. On a device with multiple inputs (touchscreen laptop, tablet with keyboard), use each input in turn on the same page; all should keep working.
3. Exceptions: essential (a drawing app requiring a stylus), security (a gesture-based challenge), or respecting an explicit user setting.
4. Fail if an available platform input modality is restricted without a valid exception.

**Common failures:**
- F98 Failure due to interactions being limited to touch-only on touchscreen devices
- Typical examples: `if ('ontouchstart' in window) { removeKeyboardHandlers() }`; a site that shows a mobile layout with no keyboard focus styles when a touchscreen is detected.

**Sufficient techniques:**
- Only using high-level, input-agnostic event handlers, such as focus, blur, click, in Javascript (Potential future technique)
- Registering event handlers for keyboard/keyboard-like and pointer inputs simultaneously in Javascript; see Example 1 in Pointer Events Level 2 (Potential future technique)

**Implementation notes (HTML/CSS/ARIA/JS):**
```js
// Input-agnostic: works for mouse, touch, pen, keyboard
el.addEventListener('click', activate);
el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') activate(); });
// Avoid branching on touch detection to disable other inputs.
```

**Related:** 2.1.1 Keyboard, 2.5.1 Pointer Gestures, 2.5.4 Motion Actuation.

### 2.5.7 Dragging Movements (Level AA) — New in 2.2

**Normative text (verbatim):**
> All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential or the functionality is determined by the user agent and not modified by the author.
>
> NOTE: This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

**Intent (informative):** Dragging (press, hold, move, release) demands sustained fine motor control that many people with tremors, arthritis, or who use head pointers, eye-gaze or speech-controlled mice cannot provide. 2.5.1 excluded dragging from "path-based gestures", so this criterion closes that gap: every drag-operated function needs a single-pointer alternative (click/tap sequences, buttons, menus). Keyboard alternatives are required by 2.1.1 but do **not** satisfy this criterion, which is about pointer users.

**How to test:**
1. List every function operated by dragging: sliders and range handles, drag-and-drop sorting/Kanban cards, file-drop zones, map panning, resizable panels/columns, colour pickers, swipe/drag carousels, drag-to-select, crop/rotate handles.
2. For each, find a way to achieve the same outcome with single pointer actions and no drag: e.g. click on the slider track or +/- buttons; "Move up/down" or "Move to column…" buttons/menus; a "Browse files" button next to the drop zone; pan arrows or click-to-centre for maps; click-to-select then click-to-place for reordering.
3. The alternative must be operable by pointer (not only keyboard) and achieve the same result.
4. Exceptions: dragging is essential (e.g. a drawing tool, a game where dragging is the activity) or the behaviour is the user agent's default untouched by the author (native `<input type="range">` can be clicked on the track and is user-agent-controlled).
5. Fail if any drag-only function lacks a non-dragging single-pointer alternative.

**Common failures:**
- F108 Failure of Success Criterion 2.5.7 Dragging Movements due to not providing a single pointer method that does not require a dragging movement
- Typical examples: a custom sortable list with drag handles only; a dashboard whose widgets can only be re-arranged by drag; a file uploader whose only mechanism is drag-and-drop; a custom slider that ignores clicks on the track.

**Sufficient techniques:**
- G219 Ensuring that an alternative is available for dragging movements that operate on content

**Implementation notes (HTML/CSS/ARIA/JS):**
```html
<li draggable="true">
  Task A
  <button type="button" aria-label="Move Task A up">↑</button>
  <button type="button" aria-label="Move Task A down">↓</button>
  <button type="button" aria-label="Move Task A to column…">Move to…</button>
</li>

<div class="dropzone">Drag files here or
  <label><input type="file" multiple hidden> <span class="btn">browse</span></label>
</div>
```
For sliders, either use native `<input type="range">` or make the custom track clickable and add stepper buttons.

**Related:** 2.5.1 Pointer Gestures, 2.5.2 Pointer Cancellation, 2.1.1 Keyboard, 2.5.8 Target Size (Minimum).

### 2.5.8 Target Size (Minimum) (Level AA) — New in 2.2

**Normative text (verbatim):**
> The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:
>
> Spacing: Undersized targets (those less than 24 by 24 CSS pixels) are positioned so that if a 24 CSS pixel diameter circle is centered on the bounding box of each, the circles do not intersect another target or the circle for another undersized target;
>
> Equivalent: The function can be achieved through a different control on the same page that meets this criterion;
>
> Inline: The target is in a sentence or its size is otherwise constrained by the line-height of non-target text;
>
> User Agent Control: The size of the target is determined by the user agent and is not modified by the author;
>
> Essential: A particular presentation of the target is essential or is legally required for the information being conveyed.
>
> NOTE 1: Targets that allow for values to be selected spatially based on position within the target are considered one target for the purpose of the success criterion. Examples include sliders, color pickers displaying a gradient of colors, or editable areas where you position the cursor.
>
> NOTE 2: For inline targets the line-height should be interpreted as perpendicular to the flow of text. For example, in a language displayed vertically, the line-height would be horizontal.

**Intent (informative):** Small, tightly packed targets cause mis-activation for people with tremors, limited dexterity, low vision, or on small touch screens. The AA minimum is 24 × 24 CSS px, **or** sufficient spacing: an undersized target is acceptable if a 24 px circle centred on it does not overlap any other target or another undersized target's circle. This lets dense toolbars pass by spacing icons apart instead of enlarging them.

**How to test:**
1. For every pointer target (links, buttons, icons, checkboxes/radios styled by the author, custom controls, pagination, list-row actions, close icons, calendar day cells), measure width and height of the clickable area in CSS px (DevTools). ≥ 24 × 24 → pass.
2. For undersized targets, apply the **spacing test**: imagine a 24 px diameter circle centred on the target's bounding box. Pass if that circle does not touch any other target and does not overlap the 24 px circle of another undersized target. Practical rule for a row of small targets: centre-to-centre distance ≥ 24 px (e.g. 16 px icons with ≥ 8 px gaps pass; 20 px icons touching each other fail).
3. Check the other exceptions: an equivalent conforming control for the same function on the page; the target is inline in a sentence or sized by the surrounding text's line-height (links in paragraphs, footnote markers); user-agent default size untouched by the author (unstyled native checkbox); essential/legally required presentation (e.g. a map pin at a legally mandated scale).
4. NOTE 1: a slider or colour gradient is one target; the criterion applies to the whole control, not each selectable value.
5. Test at the default zoom and at each responsive variation (mobile layouts often shrink targets).
6. Fail if any target is < 24 × 24 CSS px, fails the spacing test, and no exception applies.

**Common failures:**
- No F-technique is listed in the Quick Reference yet; typical examples: a 16 × 16 px "×" close icon abutting other icons; pagination numbers 18 px apart; adjacent 20 px social icons with no gap; a table of tiny edit/delete icons stacked with 2 px spacing; a 12 px date cell grid in a custom calendar.

**Sufficient techniques:**
- C42 Using min-height and min-width on target container to ensure sufficient target spacing

**Implementation notes (HTML/CSS/ARIA/JS):**
```css
/* Give every standalone control a 24 px hit box, or space small ones ≥ 24 px apart */
.icon-btn { min-width: 24px; min-height: 24px; }
.toolbar  { display: flex; gap: 8px; }          /* 16 px icons + 8 px gap = 24 px pitch */
```
Prefer 44 × 44 for primary touch targets (2.5.5 AAA and platform guidelines); 24 × 24 is the floor. Remember `padding` enlarges the hit area without enlarging the icon.

**Related:** 2.5.5 Target Size (Enhanced), 2.5.7 Dragging Movements, 1.4.4 Resize Text, 1.4.10 Reflow, 1.4.11 Non-text Contrast.

---

## Quick audit checklist for Principle 2 (informative)

| # | Criterion | Level | One-line check |
|---|---|---|---|
| 2.1.1 | Keyboard | A | Everything works with keyboard alone, no timing (path-dependent functions excepted) |
| 2.1.2 | No Keyboard Trap | A | Focus can always leave every component; non-standard exits are explained |
| 2.1.3 | Keyboard (No Exception) | AAA | As 2.1.1 with no path-dependent exception |
| 2.1.4 | Character Key Shortcuts | A | Single-character shortcuts can be turned off, remapped, or only work on focus |
| 2.2.1 | Timing Adjustable | A | Time limits can be turned off, adjusted ×10, or extended (≥ 20 s warning, ×10) |
| 2.2.2 | Pause, Stop, Hide | A | Auto-starting motion > 5 s and auto-updates have pause/stop/hide controls |
| 2.2.3 | No Timing | AAA | No timing in any activity except media and real-time events |
| 2.2.4 | Interruptions | AAA | Non-emergency interruptions can be postponed or suppressed |
| 2.2.5 | Re-authenticating | AAA | No data loss after session expiry and re-login |
| 2.2.6 | Timeouts | AAA | Users are told the inactivity duration that causes data loss (unless > 20 h) |
| 2.3.1 | Three Flashes or Below Threshold | A | ≤ 3 flashes/second or below general/red flash thresholds |
| 2.3.2 | Three Flashes | AAA | ≤ 3 flashes/second, no exceptions |
| 2.3.3 | Animation from Interactions | AAA | Interaction-triggered motion can be disabled unless essential |
| 2.4.1 | Bypass Blocks | A | Skip link and/or landmarks/headings to bypass repeated blocks |
| 2.4.2 | Page Titled | A | `<title>` describes topic or purpose |
| 2.4.3 | Focus Order | A | Tab order preserves meaning and operability |
| 2.4.4 | Link Purpose (In Context) | A | Link purpose clear from text + programmatic context |
| 2.4.5 | Multiple Ways | AA | ≥ 2 ways to find a page (nav, search, site map…) except process steps |
| 2.4.6 | Headings and Labels | AA | Headings and labels are descriptive |
| 2.4.7 | Focus Visible | AA | A visible focus indicator exists for all focusable elements |
| 2.4.8 | Location | AAA | Breadcrumb/current-page indication available |
| 2.4.9 | Link Purpose (Link Only) | AAA | Link text alone conveys purpose (or mechanism to expand it) |
| 2.4.10 | Section Headings | AAA | Written content organised with section headings |
| 2.4.11 | Focus Not Obscured (Minimum) | AA | Focused element is never entirely hidden by author content |
| 2.4.12 | Focus Not Obscured (Enhanced) | AAA | No part of the focused element is hidden |
| 2.4.13 | Focus Appearance | AAA | Indicator ≥ 2 px perimeter area and ≥ 3:1 focused/unfocused change |
| 2.5.1 | Pointer Gestures | A | Multipoint/path gestures have single-pointer alternatives |
| 2.5.2 | Pointer Cancellation | A | Actions complete on up-event, or can be aborted/undone |
| 2.5.3 | Label in Name | A | Accessible name contains the visible label text |
| 2.5.4 | Motion Actuation | A | Motion-operated functions have UI controls and can be disabled |
| 2.5.5 | Target Size (Enhanced) | AAA | Targets ≥ 44 × 44 CSS px (inline/UA/essential/equivalent excepted) |
| 2.5.6 | Concurrent Input Mechanisms | AAA | No input modality is blocked unless essential/security/user setting |
| 2.5.7 | Dragging Movements | AA | Every drag function has a non-drag single-pointer alternative |
| 2.5.8 | Target Size (Minimum) | AA | Targets ≥ 24 × 24 CSS px or spaced so 24 px circles do not overlap |
