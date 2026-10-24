# Task: keyboard and focus

Applies when a change adds or modifies anything operable: buttons, links, dialogs, menus, dropdowns, tabs, custom widgets, shortcuts, sticky headers or footers. Criteria: `python scripts/wcag.py task keyboard-focus`. Components: `wcag.py component modal` (also `dropdown-nav`, `dropdown-sel`, `tabs`, `tooltip`, `header`, `custom`).

## Requirements

| Criterion | Level | Origin | What to do |
|---|---|---|---|
| 2.1.1 Keyboard | A | wcag, obelisco | Everything is operable by keyboard. Native `<button>`, `<a href>`, `<input>` first; a custom control needs role, `tabindex="0"` and its key handlers |
| 2.1.2 No Keyboard Trap | A | wcag, obelisco | A dialog keeps focus inside while open and always has a keyboard exit: Escape or a close button. Obelisco states Escape closes the modal and returns focus |
| 2.1.4 Character Key Shortcuts | A | wcag | A single-character shortcut can be turned off, remapped, or only works while its component has focus |
| 2.4.1 Bypass Blocks | A | wcag, obelisco | A skip link to the main content (Obelisco header: «Saltar al contenido principal») |
| 2.4.3 Focus Order | A | wcag, obelisco | Order follows meaning. On open, focus goes to the first element that accepts input (the primary button if there is no field); on close it returns to the trigger |
| 2.4.7 Focus Visible | AA | wcag, obelisco | A visible indicator on every focusable element; never `outline: none` without an equal replacement |
| 2.4.11 Focus Not Obscured (Minimum) | AA | wcag | A sticky header, footer, banner or toast never hides the focused element completely: reserve `scroll-padding-top` and `scroll-padding-bottom` |
| 3.2.1 On Focus | A | wcag | Receiving focus never changes context |
| 3.2.2 On Input | A | wcag, obelisco | Choosing or typing never navigates or submits without warning |
| 1.4.13 Content on Hover or Focus | AA | wcag | A tooltip or popover appears on focus as well as hover, closes with Escape, and stays while the pointer is over it |
| 1.4.11 Non-text Contrast | AA | wcag | An author-styled focus indicator is at least 3:1 against its neighbours (failure F78 covers 1.4.11, 2.4.7 and 2.4.13) |
| 2.4.13 Focus Appearance | AAA | obelisco | Additional, not AA: the indicator has at least a 2 CSS px perimeter and changes by at least 3:1 between focused and unfocused. Obelisco's checklist names it with its 3:1 |

## Patterns

- **Dialog:** a native `<dialog>` opened with `showModal()` makes the background inert, closes on Escape and gives the focus back; label it with `aria-labelledby`.
- **Menu or dropdown:** a `<button>` with `aria-expanded` (and `aria-haspopup` as Obelisco asks), arrow keys between items, Escape closes and returns focus to the button.
- **Tabs:** `tablist` / `tab` / `tabpanel`, arrow keys move between tabs, one tab in the tab order. Obelisco publishes no accessibility section for tabs: design and test it.
- **Sticky header:** `html { scroll-padding-top: <header height>; }` (technique C43).

## How it is verified

- **Static:** `clickable-not-keyboard`, `tabindex-positive`, `aria-hidden-focusable` (full review only). Nothing else here is reachable by a machine.
- **Manual — keyboard (required):** Tab and Shift+Tab through everything; Enter and Space; Escape; arrows in composite widgets; no trap; focus never lost after a dynamic change.
- **Manual — browser:** focus not obscured by sticky content at desktop and mobile widths; indicator contrast; hover and focus content.
- **Record** the keyboard pass as `performed` only if somebody ran it.

## Typical failures

`<div onclick>` with no role or `tabindex`; `outline: none` with nothing in its place; a modal without Escape; focus that lands on `<body>` after closing a dialog; a positive `tabindex`; a sticky footer over the last field; a tooltip only on hover.
