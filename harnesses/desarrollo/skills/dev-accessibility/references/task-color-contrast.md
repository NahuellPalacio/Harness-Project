# Task: colour and contrast

Applies when a change introduces or alters colours, states (hover, focus, disabled, error, selected), text over backgrounds or images, icons, charts, or a theme. Criteria: `python scripts/wcag.py task color-contrast`. Components: `wcag.py component colors` (also `button`, `alert`, `link`).

## Requirements

| Criterion | Level | Origin | What to do |
|---|---|---|---|
| 1.4.1 Use of Color | A | wcag, obelisco | Colour is never the only way to convey information, indicate an action, prompt a response or distinguish an element: pair it with text, an icon or a pattern. Obelisco: colour is functional and semantic, not decoration |
| 1.4.3 Contrast (Minimum) | AA | wcag, obelisco | Text at least 4.5:1; large text at least 3:1. Large is 24 px (18 pt) or about 18.67 px (14 pt) bold. Exempt: inactive controls, decoration, logos |
| 1.4.11 Non-text Contrast | AA | wcag, obelisco | The boundary and the states of a UI component, and the graphics that carry meaning, at least 3:1 against what is next to them — an author-styled focus indicator included. A native control with no author style is exempt |
| 1.3.3 Sensory Characteristics | A | wcag, obelisco | Instructions do not rely only on colour, shape or position («click the green button») |
| 1.4.6 Contrast (Enhanced) | AAA | obelisco | Additional, not AA: 7:1, large text 4.5:1. Obelisco's colour page cites it without stating a level |

## Compute, do not estimate

```
python scripts/contrast.py "#767676" "#ffffff" --size 16
python scripts/contrast.py "rgba(0,0,0,0.6)" "#ffffff"
python scripts/contrast.py "#1a1a1a" "rgba(255,255,255,0.8)" --backdrop "#003366"
```

Transparency is composed over the background in sRGB, rounding each channel to 8 bits like a browser. A translucent background needs `--backdrop`, the opaque colour underneath; without it the script gives no ratio and says what is missing. `currentColor`, `var(--x)`, `inherit` and unknown colour names also get no answer: pass the computed value from the browser.

Test **every state**: default, hover, focus, active, error, selected. Disabled controls are exempt from 1.4.3, not from being understandable.

## Obelisco

Use the documented semantic colours before any out-of-palette colour. Obelisco's button page says the primary outlined button has low contrast on dark backgrounds and asks for the light outlined one there: that is official guidance, and the ratio still has to be measured.

## How it is verified

- **Static:** nothing decides a contrast ratio from markup. A colour pair read from source is only a candidate: the cascade, a gradient, an image or a theme can change it.
- **Computed:** `contrast.py` on explicit pairs, with the states of the component.
- **Manual — browser (required):** the rendered pairs, text over images and gradients (worst point), forced-colors mode, and non-colour cues.
- **Record** as `performed` only the browser pass that was run.

## Typical failures

`#777` on white (4.48:1); light-grey input borders; a placeholder in pale grey; red-only errors; a focus ring that disappears on a coloured button; text over an image with no scrim; a link distinguished from its text only by colour.
