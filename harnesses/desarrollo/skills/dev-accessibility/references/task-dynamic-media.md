# Task: dynamic content, media and motion

Applies when a change shows messages or results without a page load, adds loading states, alerts, auto-updating or moving content (carousels, tickers), timeouts, audio or video. Criteria: `python scripts/wcag.py task dynamic-media`. Components: `wcag.py component alert` (also `status-message`, `spinner`, `progress-bar`, `carousel`, `tooltip`).

## Requirements

| Criterion | Level | Origin | What to do |
|---|---|---|---|
| 4.1.3 Status Messages | AA | wcag, obelisco | A message that does not take focus — saved, results updated, error count, loading — is exposed through `role="status"`, `role="alert"` or `aria-live`, in a region that already exists before the update |
| 2.2.1 Timing Adjustable | A | wcag | A time limit can be turned off, adjusted or extended, unless an exception applies |
| 2.2.2 Pause, Stop, Hide | A | wcag | Moving, blinking or scrolling content that starts by itself, lasts more than 5 s and runs beside other content has a control to pause, stop or hide it. It applies to the whole page |
| 2.3.1 Three Flashes or Below Threshold | A | wcag | Nothing flashes more than three times a second. It applies to the whole page |
| 1.4.2 Audio Control | A | wcag | Audio that plays by itself for more than 3 s can be paused or its volume controlled apart from the system's |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | wcag | A transcript, or an audio track for video-only |
| 1.2.2 Captions (Prerecorded) | A | wcag | Synchronized captions on prerecorded video with audio |
| 1.2.3 Audio Description or Media Alternative (Prerecorded) | A | wcag | Audio description, or a full text alternative |
| 1.2.4 Captions (Live) | AA | wcag | Captions on live video with audio |
| 1.2.5 Audio Description (Prerecorded) | AA | wcag | Audio description on prerecorded video |
| 1.4.13 Content on Hover or Focus | AA | wcag | Dismissible with Escape, hoverable, persistent |

## Patterns

- **Urgent message:** `role="alert"` announces at once, as Obelisco's alert asks. Reserve it for what needs immediate attention; use `role="status"` (polite) for the rest.
- **Loading:** a status region with visually hidden text («Cargando…»). Obelisco's spinner asks for `role="status"` together with `aria-live="assertive"`; an explicit `aria-live` overrides the implicit `polite`, so the interruption is Obelisco's choice and not something WCAG requires.
- **Progress:** state it in text («Paso 2 de 5»), not only visually; use `role="progressbar"` with value attributes when it is dynamic and announce changes the user did not start.
- **Carousel:** no automatic rotation, or a pause control that is the first thing reachable; controls with names and key operation; a single-pointer alternative to swipe. Obelisco publishes no accessibility section for it.
- **Do not** move focus just to announce a message, and do not insert a live region and its text in the same update.

## How it is verified

- **Static:** `media-autoplay`, `video-no-captions`, `marquee-or-blink`, `meta-refresh-delay` (full review). Whether a region is announced is not in the markup alone.
- **Manual — screen reader (required):** each message is announced once, at the right moment, without moving focus.
- **Manual — browser:** autoplay, flashing, pause controls, captions and timeouts do what the page claims.

## Typical failures

A success message that appears and is never announced; a live region created together with its message; `role="alert"` on every toast; a video with autoplay and sound; a carousel that rotates with no pause; `<meta http-equiv="refresh" content="60">`; a session that ends with no warning.
