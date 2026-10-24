# Principle 1: Perceivable

> Information and user interface components must be presentable to users in ways they can perceive.

Source of normative text: WCAG 2.2, W3C Recommendation 12 December 2024 (https://www.w3.org/TR/WCAG22/). Technique and failure lists follow the W3C "How to Meet WCAG 2.2" Quick Reference. Sections marked *informative* are explanatory guidance, not normative requirements.

## Contents

| Guideline / Criterion | Level |
|---|---|
| **1.1 Text Alternatives** | |
| 1.1.1 Non-text Content | A |
| **1.2 Time-based Media** | |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A |
| 1.2.2 Captions (Prerecorded) | A |
| 1.2.3 Audio Description or Media Alternative (Prerecorded) | A |
| 1.2.4 Captions (Live) | AA |
| 1.2.5 Audio Description (Prerecorded) | AA |
| 1.2.6 Sign Language (Prerecorded) | AAA |
| 1.2.7 Extended Audio Description (Prerecorded) | AAA |
| 1.2.8 Media Alternative (Prerecorded) | AAA |
| 1.2.9 Audio-only (Live) | AAA |
| **1.3 Adaptable** | |
| 1.3.1 Info and Relationships | A |
| 1.3.2 Meaningful Sequence | A |
| 1.3.3 Sensory Characteristics | A |
| 1.3.4 Orientation | AA |
| 1.3.5 Identify Input Purpose | AA |
| 1.3.6 Identify Purpose | AAA |
| **1.4 Distinguishable** | |
| 1.4.1 Use of Color | A |
| 1.4.2 Audio Control | A |
| 1.4.3 Contrast (Minimum) | AA |
| 1.4.4 Resize Text | AA |
| 1.4.5 Images of Text | AA |
| 1.4.6 Contrast (Enhanced) | AAA |
| 1.4.7 Low or No Background Audio | AAA |
| 1.4.8 Visual Presentation | AAA |
| 1.4.9 Images of Text (No Exception) | AAA |
| 1.4.10 Reflow | AA |
| 1.4.11 Non-text Contrast | AA |
| 1.4.12 Text Spacing | AA |
| 1.4.13 Content on Hover or Focus | AA |

None of the Perceivable criteria are new in WCAG 2.2; 1.3.4, 1.3.5, 1.3.6, 1.4.10, 1.4.11, 1.4.12 and 1.4.13 were added in WCAG 2.1, the rest date from WCAG 2.0.

---

## Guideline 1.1 Text Alternatives

> Provide text alternatives for any non-text content so that it can be changed into other forms people need, such as large print, braille, speech, symbols or simpler language.

### 1.1.1 Non-text Content (Level A)

**Normative text (verbatim):**
> All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.
>
> **Controls, Input** — If non-text content is a control or accepts user input, then it has a name that describes its purpose. (Refer to Success Criterion 4.1.2 for additional requirements for controls and content that accepts user input.)
>
> **Time-Based Media** — If non-text content is time-based media, then text alternatives at least provide descriptive identification of the non-text content. (Refer to Guideline 1.2 for additional requirements for media.)
>
> **Test** — If non-text content is a test or exercise that would be invalid if presented in text, then text alternatives at least provide descriptive identification of the non-text content.
>
> **Sensory** — If non-text content is primarily intended to create a specific sensory experience, then text alternatives at least provide descriptive identification of the non-text content.
>
> **CAPTCHA** — If the purpose of non-text content is to confirm that content is being accessed by a person rather than a computer, then text alternatives that identify and describe the purpose of the non-text content are provided, and alternative forms of CAPTCHA using output modes for different types of sensory perception are provided to accommodate different disabilities.
>
> **Decoration, Formatting, Invisible** — If non-text content is pure decoration, is used only for visual formatting, or is not presented to users, then it is implemented in a way that it can be ignored by assistive technology.

**Key terms:** *non-text content* = any content that is not a sequence of characters that can be programmatically determined or where the sequence is not expressing something in human language (includes ASCII art, emoticons, leetspeak, images of text). *Text alternative* = text programmatically associated with the non-text content, or referred to from such text. *Pure decoration* = serving only an aesthetic purpose, providing no information, and having no functionality.

**Intent (informative):** Every image, icon, chart, audio file, video, applet or other non-text object needs a text equivalent so it can be rendered as speech, braille, large print or symbols. The primary beneficiaries are blind and low-vision screen reader users, deafblind users of braille displays, and people on text-only or image-disabled connections. The six exceptions do not remove the requirement; they lower it to "descriptive identification" (media, tests, sensory experiences), add a second-modality requirement (CAPTCHA), or say the object must be hidden from assistive technology (decoration).

**How to test:**
1. Inventory all non-text content: `<img>`, `<input type="image">`, `<area>`, `<svg>`, `<canvas>`, `<object>`, `<embed>`, `<video>`, `<audio>`, icon fonts, CSS background images that carry meaning, emoji, ASCII art.
2. For each `<img>`, confirm an `alt` attribute exists (absent `alt` is a failure, F65). Read the computed accessible name with the browser accessibility tree or axe/WAVE output.
3. Judge equivalence: would a sighted user and a screen reader user receive the same information or be able to perform the same function? Alt text that is a file name, "image", "photo", or placeholder text fails (F30). Charts and diagrams need a short alt plus a long description (adjacent text, `aria-describedby`, or a linked page).
4. Decorative images must have `alt=""` (no `title`), `role="presentation"`/`aria-hidden="true"`, or be CSS backgrounds. An informative image delivered only as CSS background fails (F3).
5. Functional images (image links, image buttons, icon buttons): the name must describe the action/destination, not the picture ("Search", not "magnifying glass").
6. Icon fonts and SVG icons: check for `aria-hidden="true"` when decorative, or `role="img"` + `aria-label`/`<title>` when meaningful.
7. CAPTCHA: verify (a) a text alternative explains its purpose and (b) an alternative CAPTCHA in a different modality (e.g. audio in addition to visual) exists.
8. Media: `<video>`/`<audio>` need at least a descriptive identification (accessible name, heading or adjacent text); full alternatives are checked under 1.2.x.
9. Dynamic content: if the image changes (carousel, status icon), confirm the alt updates too (F20).
Pass when every meaningful non-text item has an equivalent, every decorative item is hidden from AT, and every control has a purpose-describing name.

**Common failures:**
- F3 Failure of Success Criterion 1.1.1 due to conveying information exclusively using CSS background images
- F13 Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image
- F20 Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur
- F30 Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)
- F38 Failure of Success Criterion 1.1.1 due to not marking up decorative images in HTML in a way that allows assistive technology to ignore them
- F39 Failure of Success Criterion 1.1.1 due to providing a text alternative that is not null (e.g., alt="spacer" or alt="image") for images that should be ignored by assistive technology
- F65 Failure of Success Criterion 1.1.1 due to omitting the alt attribute or text alternative on img elements, area elements, and input elements of type "image"
- F67 Failure of Success Criterion 1.1.1 and 1.2.1 due to providing long descriptions for non-text content that does not serve the same purpose or does not present the same information
- F71 Failure of Success Criterion 1.1.1 due to using text look-alikes to represent text without providing a text alternative
- F72 Failure of Success Criterion 1.1.1 due to using ASCII art without providing a text alternative
- Typical examples: a hero banner with `alt="banner_final_v2.jpg"`; a "Delete" icon button with no accessible name; a bar chart with `alt="chart"` and no data table or description; a decorative divider image with `alt="divider"`.

**Sufficient techniques:**
- Situation A: If a short description can serve the same purpose and present the same information as the non-text content:
  - G94 Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content, using one technique from: ARIA6 Using aria-label to provide labels for objects; ARIA10 Using aria-labelledby to provide a text alternative for non-text content; G196 Using a text alternative on one item within a group of images that describes all items in the group; H2 Combining adjacent image and text links for the same resource; H37 Using alt attributes on img elements; H53 Using the body of the object element; H86 Providing text alternatives for emojis, emoticons, ASCII art, and leetspeak; PDF1 Applying text alternatives to images with the Alt entry in PDF documents
- Situation B: If a short description can not serve the same purpose and present the same information as the non-text content (e.g., a chart or diagram):
  - G95 Providing short text alternatives that provide a brief description of the non-text content, using one short-text technique (ARIA6, ARIA10, G196, H2, H37, H53, H86, PDF1) AND one long-text technique: ARIA15 Using aria-describedby to provide descriptions of images; G73 Providing a long description in another location with a link to it that is immediately adjacent to the non-text content; G74 Providing a long description in text near the non-text content, with a reference to the location of the long description in the short description; G92 Providing long description for non-text content that serves the same purpose and presents the same information; H53 Using the body of the object element
- Situation C: If non-text content is a control or accepts user input:
  - G82 Providing a text alternative that identifies the purpose of interactive non-text content, using one of: ARIA6 Using aria-label to provide labels for objects; ARIA9 Using aria-labelledby to concatenate a label from several text nodes; H24 Providing text alternatives for the area elements of image maps; H30 Providing link text that describes the purpose of a link for anchor elements; H36 Using alt attributes on images used as submit buttons; H44 Using label elements to associate text labels with form controls; H65 Using the title attribute to identify form controls when the label element cannot be used
- Situation D: If non-text content is time-based media (including live video-only and live audio-only); a test or exercise that would be invalid if presented in text; or primarily intended to create a specific sensory experience:
  - Providing a descriptive label: G68 Providing a short text alternative that describes the purpose of live audio-only and live video-only content; G100 Providing a short text alternative which is the accepted name or a descriptive name of the non-text content — each using one short-text technique (ARIA6, ARIA10, G196, H2, H37, H53, H86, PDF1)
- Situation E: If non-text content is a CAPTCHA:
  - G143 Providing a text alternative that describes the purpose of the CAPTCHA AND G144 Ensuring that the web page contains another CAPTCHA serving the same purpose using a different modality
- Situation F: If the non-text content should be ignored by assistive technology:
  - Implementing or marking the non-text content so that it will be ignored by assistive technology, using one of: C9 Using CSS to include decorative images; H67 Using null alt text and no title attribute on img elements for images that assistive technology should ignore; PDF4 Hiding decorative images with the Artifact tag in PDF documents

**Advisory techniques:** C18 Using CSS margin and padding rules instead of spacer images for layout design

**Implementation notes (HTML/CSS/ARIA):**
```html
<!-- Informative image -->
<img src="q3-sales.png" alt="Q3 sales rose 12% to $4.1M, led by the Southern region">

<!-- Decorative image: empty alt, no title -->
<img src="divider.png" alt="">

<!-- Icon button -->
<button type="button" aria-label="Search">
  <svg aria-hidden="true" focusable="false">…</svg>
</button>

<!-- Complex image with long description -->
<img src="org-chart.png" alt="Organisation chart; full description follows" aria-describedby="org-desc">
<div id="org-desc">The Director oversees three units: …</div>

<!-- Image map -->
<area shape="rect" coords="…" href="/sales" alt="Sales department">

<!-- Wrong: -->
<img src="hero.jpg">                 <!-- missing alt (F65) -->
<img src="spacer.gif" alt="spacer">  <!-- non-null alt on decorative image (F39) -->
```

**Related:** 4.1.2 Name, Role, Value (controls need a name), 1.2.x (media alternatives), 1.4.1 Use of Color (alt must carry colour-coded information, F13), 1.4.5 Images of Text, 2.4.4 Link Purpose (image links), 2.5.3 Label in Name.

---

## Guideline 1.2 Time-based Media

> Provide alternatives for time-based media.

**Key terms used across 1.2.x:** *prerecorded* = information that is not live. *Live* = information captured from a real-world event and transmitted with no more than a broadcast delay. *Audio-only* = a time-based presentation that contains only audio. *Video-only* = only video (no audio and no interaction). *Synchronized media* = audio or video synchronized with another format for presenting information and/or with time-based interactive components, unless the media is a media alternative for text that is clearly labeled as such. *Alternative for time-based media* = a document including correctly sequenced text descriptions of time-based visual and auditory information and providing a means for achieving the outcomes of any time-based interaction (i.e. a full transcript with descriptions). *Media alternative for text* = media that presents no more information than is already presented in text. *Captions* = synchronized visual and/or text alternative for both speech and non-speech audio information needed to understand the media content. *Audio description* = narration added to the soundtrack to describe important visual details that cannot be understood from the main soundtrack alone.

### 1.2.1 Audio-only and Video-only (Prerecorded) (Level A)

**Normative text (verbatim):**
> For prerecorded audio-only and prerecorded video-only media, the following are true, except when the audio or video is a media alternative for text and is clearly labeled as such:
>
> **Prerecorded Audio-only** — An alternative for time-based media is provided that presents equivalent information for prerecorded audio-only content.
>
> **Prerecorded Video-only** — Either an alternative for time-based media or an audio track is provided that presents equivalent information for prerecorded video-only content.

**Intent (informative):** Podcasts and audio clips are inaccessible to deaf and hard-of-hearing users; silent videos and animations are inaccessible to blind users. A transcript (for audio) or a transcript or audio track (for video) makes the information available in another modality. Transcripts also help people with cognitive disabilities and anyone who prefers to read.

**How to test:**
1. List every prerecorded audio-only resource (podcast players, `<audio>`, embedded players) and every video-only resource (silent product demos, animated GIF/MP4 explainers, background videos that carry information).
2. If the media is explicitly labeled as an alternative to text already on the page (e.g. "Audio version of this article"), it is exempt.
3. Audio-only: find a text transcript that contains all speech and meaningful sounds (speaker changes, laughter, alarms). It must be on the page or linked next to the player.
4. Video-only: find either a text transcript describing all visual information in sequence, or an audio track that narrates it.
5. Verify equivalence: the alternative must present the same information, not a summary (F67) and not a placeholder (F30).
Pass when each item has an equivalent alternative discoverable from the media.

**Common failures:**
- F30 Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)
- F67 Failure of Success Criterion 1.1.1 and 1.2.1 due to providing long descriptions for non-text content that does not serve the same purpose or does not present the same information
- Typical examples: a podcast page with only an episode title and a two-line teaser; a silent "how to assemble" video with no transcript.

**Sufficient techniques:**
- Situation A: If the content is prerecorded audio-only: G158 Providing an alternative for time-based media for audio-only content
- Situation B: If the content is prerecorded video-only: G159 Providing an alternative for time-based media for video-only content; G166 Providing audio that describes the important video content and describing it as such

**Advisory techniques:** H96 Using the track element to provide audio descriptions

**Implementation notes (HTML/CSS/ARIA):**
```html
<audio controls src="episode-12.mp3" aria-label="Episode 12: Budget planning"></audio>
<p><a href="episode-12-transcript.html">Read the transcript of Episode 12</a></p>

<!-- Video-only with a descriptive audio track -->
<video controls src="assembly.mp4">
  <track kind="descriptions" src="assembly-desc.vtt" srclang="en">
</video>
```

**Related:** 1.1.1 (descriptive identification of media), 1.2.2/1.2.3 (synchronized media), 1.2.8 (AAA media alternative).

### 1.2.2 Captions (Prerecorded) (Level A)

**Normative text (verbatim):**
> Captions are provided for all prerecorded audio content in synchronized media, except when the media is a media alternative for text and is clearly labeled as such.

**Intent (informative):** People who are deaf or hard of hearing need captions to follow dialogue and relevant sounds in video. Captions differ from subtitles: they include speaker identification, sound effects and music cues necessary to understand the content. They also benefit people in noisy or silent environments and non-native speakers.

**How to test:**
1. Identify every prerecorded video that has an audio track (synchronized media).
2. Exempt only media clearly labeled as an alternative to text on the page.
3. Play the video and enable captions (CC button, `<track kind="captions">`, or open/burned-in captions).
4. Check accuracy and completeness: all dialogue, speaker changes where ambiguous, and meaningful non-speech audio (e.g. "[door slams]", "[applause]"). Auto-generated captions that are uncorrected and inaccurate fail (F8).
5. Check synchronization with the audio.
Pass when every such video offers accurate, synchronized captions.

**Common failures:**
- F8 Failure of Success Criterion 1.2.2 due to captions omitting some dialogue or important sound effects
- F75 Failure of Success Criterion 1.2.2 by providing synchronized media without captions when the synchronized media presents more information than is presented on the page
- F74 Failure of Success Criterion 1.2.2 and 1.2.8 due to not labeling a synchronized media alternative to text as an alternative
- Typical examples: a YouTube embed relying on uncorrected auto-captions; a promotional video with no caption track; a "video version" of an article that adds extra interview content but has no captions.

**Sufficient techniques:**
- G93 Providing open (always visible) captions
- G87 Providing closed captions, using any of: SM11 Providing captions through synchronized text streams in SMIL 1.0; SM12 Providing captions through synchronized text streams in SMIL 2.0; H95 Using the track element to provide captions; using any readily available media format that has a video player that supports closed captioning

**Implementation notes (HTML/CSS/ARIA):**
```html
<video controls>
  <source src="townhall.mp4" type="video/mp4">
  <track kind="captions" src="townhall-en.vtt" srclang="en" label="English" default>
</video>
```
WebVTT caption example:
```
00:00:01.000 --> 00:00:04.000
[MAYOR] Good morning, everyone.

00:00:04.500 --> 00:00:06.000
[applause]
```

**Related:** 1.2.4 Captions (Live), 1.2.3/1.2.5 audio description, 1.2.8 media alternative, 1.4.4 (captions are excepted from resize).

### 1.2.3 Audio Description or Media Alternative (Prerecorded) (Level A)

**Normative text (verbatim):**
> An alternative for time-based media or audio description of the prerecorded video content is provided for synchronized media, except when the media is a media alternative for text and is clearly labeled as such.

**Intent (informative):** Blind and low-vision users cannot see on-screen text, actions, scene changes or charts in a video. At Level A, authors may choose either an audio description track or a full text alternative (descriptive transcript). Level AA (1.2.5) then requires audio description specifically.

**How to test:**
1. Identify prerecorded synchronized media (video with audio).
2. Watch with the sound off and list visual information that is not conveyed by the audio (on-screen text, demonstrations, gestures, charts, who is speaking when not introduced).
3. If nothing visual is missing from the audio (e.g. a talking-head video where the speaker says everything), the criterion is met without extra work (see G203 and audio description definition NOTE 3).
4. Otherwise confirm either (a) an audio description track/version, or (b) a descriptive transcript that includes both dialogue and descriptions of visual content, linked or placed next to the video.
Pass when one of the two is present and complete.

**Common failures:**
- No F-technique is specifically listed for 1.2.3; failures are judged on absence or inadequacy of the alternative.
- Typical examples: a tutorial video where the narrator says "click here" while the cursor moves, with no description and no transcript; a transcript that contains dialogue only.

**Sufficient techniques:**
- G69 Providing an alternative for time based media, using one of: G58 Placing a link to the alternative for time-based media immediately next to the non-text content; linking to the alternative for time-based media using H53 Using the body of the object element
- G78 Providing a second, user-selectable, audio track that includes audio descriptions
- G173 Providing a version of a movie with audio descriptions, using one or more of: SM6 Providing audio description in SMIL 1.0; SM7 Providing audio description in SMIL 2.0; G226 Providing audio descriptions by incorporating narration in the soundtrack
- G8 Providing a movie with extended audio descriptions, using one of: SM1 Adding extended audio description in SMIL 1.0; SM2 Adding extended audio description in SMIL 2.0
- G203 Using a static text alternative to describe a talking head video

**Advisory techniques:** H96 Using the track element to provide audio descriptions

**Implementation notes (HTML/CSS/ARIA):**
```html
<video controls>
  <source src="demo.mp4" type="video/mp4">
  <track kind="captions" src="demo-en.vtt" srclang="en" default>
  <track kind="descriptions" src="demo-desc-en.vtt" srclang="en">
</video>
<p><a href="demo-transcript.html">Descriptive transcript (dialogue and visual descriptions)</a></p>
```
Browser support for `kind="descriptions"` is limited; a separately described version of the video (G78/G173) or a descriptive transcript is the safer choice.

**Related:** 1.2.5 (AA audio description), 1.2.7 (AAA extended), 1.2.8 (AAA media alternative), 1.2.2 captions.

### 1.2.4 Captions (Live) (Level AA)

**Normative text (verbatim):**
> Captions are provided for all live audio content in synchronized media.

**Intent (informative):** Live broadcasts, webinars and streamed meetings must be captioned in real time (CART/stenography or high-quality live captioning) so deaf and hard-of-hearing people can participate at the same time as everyone else. Note the criterion applies to synchronized media (live video with audio); live audio-only is covered by 1.2.9 at AAA.

**How to test:**
1. Identify live streams with audio (council sessions, webinars, live events embedded in the page).
2. During the live event, confirm captions are available in the player or as a parallel caption stream, and that they are reasonably accurate and synchronized.
3. Check that captions cover speech and important non-speech sounds.
Pass when live captions are provided for all live synchronized media.

**Common failures:**
- No F-technique is listed; a live stream without captions, or with captions available only after the event, fails.
- Typical examples: a live-streamed public hearing with no captioning service; auto-captions turned off in the streaming platform.

**Sufficient techniques:**
- G9 Creating captions for live synchronized media AND G93 Providing open (always visible) captions
- G9 Creating captions for live synchronized media AND G87 Providing closed captions, using SM11 Providing captions through synchronized text streams in SMIL 1.0; SM12 Providing captions through synchronized text streams in SMIL 2.0; or any readily available media format that has a video player that supports closed captioning

**Implementation notes (HTML/CSS/ARIA):** Live captioning is usually delivered through the streaming platform (CEA-608/708 or WebVTT live streams, or a captioner's web viewer). Ensure the player exposes a caption toggle that is keyboard operable and named (see 2.1.1, 4.1.2).

**Related:** 1.2.2 Captions (Prerecorded), 1.2.9 Audio-only (Live).

### 1.2.5 Audio Description (Prerecorded) (Level AA)

**Normative text (verbatim):**
> Audio description is provided for all prerecorded video content in synchronized media.

**Intent (informative):** At AA, a text alternative is no longer enough: blind users should be able to follow the video in real time through narration inserted in the natural pauses of the dialogue. Where the audio already conveys all visual information, no additional description is needed.

**How to test:**
1. Identify prerecorded synchronized media.
2. Determine whether visual information exists that the soundtrack does not convey (watch muted, as in 1.2.3).
3. If so, confirm an audio-described version or a selectable described audio track exists and that descriptions are inserted in dialogue pauses and cover the important visual content (F113 covers failing to use available pauses).
4. Where the video has no such visual information (talking head), note it as passing by design.
Pass when every video with un-narrated visual information has audio description.

**Common failures:**
- F113 Failure of Success Criterion 1.2.5 due to not using available pauses in dialogue to provide audio descriptions of important visual content
- Typical examples: a campaign video with on-screen statistics never spoken aloud; a procedure video with silent demonstrations.

**Sufficient techniques:**
- G78 Providing a second, user-selectable, audio track that includes audio descriptions
- G173 Providing a version of a movie with audio descriptions, using one or more of: SM6 Providing audio description in SMIL 1.0; SM7 Providing audio description in SMIL 2.0; G226 Providing audio descriptions by incorporating narration in the soundtrack
- G8 Providing a movie with extended audio descriptions, using one of: SM1 Adding extended audio description in SMIL 1.0; SM2 Adding extended audio description in SMIL 2.0
- G203 Using a static text alternative to describe a talking head video

**Advisory techniques:** H96 Using the track element to provide audio descriptions

**Implementation notes (HTML/CSS/ARIA):** Offer a clearly labeled "Audio described version" link or player menu entry; when producing video, script narration so the presenter reads on-screen text aloud (G226) — the cheapest way to satisfy the criterion.

**Related:** 1.2.3 (Level A alternative), 1.2.7 (extended description), 1.2.8.

### 1.2.6 Sign Language (Prerecorded) (Level AAA)

**Normative text (verbatim):**
> Sign language interpretation is provided for all prerecorded audio content in synchronized media.

**Intent (informative):** For many deaf people, sign language is their first language and written captions are a second language; interpretation conveys intonation, emotion and meaning more fully. Use the sign language of the audience (e.g. LSA in Argentina, ASL in the US, BSL in the UK).

**How to test:**
1. For each prerecorded video with audio, check for an interpreter in the video frame or a synchronized interpreter video (picture-in-picture or selectable overlay).
2. Confirm the interpreter is visible at a usable size throughout the speech content and in the appropriate sign language.
Pass when all such media offer sign language interpretation.

**Common failures:** None listed; absence of interpretation fails.

**Sufficient techniques:**
- G54 Including a sign language interpreter in the video stream
- G81 Providing a synchronized video of the sign language interpreter that can be displayed in a different viewport or overlaid on the image by the player, using one of: SM13 Providing sign language interpretation through synchronized video streams in SMIL 1.0; SM14 Providing sign language interpretation through synchronized video streams in SMIL 2.0

**Implementation notes (HTML/CSS/ARIA):** Simplest implementation is G54 (burn the interpreter into the frame, ≥ 1/4 of frame height). Alternatively provide a second `<video>` synchronized by script, or a separate "With sign language" version.

**Related:** 1.2.2 Captions, 3.1.5 Reading Level (G160 sign language versions).

### 1.2.7 Extended Audio Description (Prerecorded) (Level AAA)

**Normative text (verbatim):**
> Where pauses in foreground audio are insufficient to allow audio descriptions to convey the sense of the video, extended audio description is provided for all prerecorded video content in synchronized media.

**Key term:** *extended audio description* = audio description that is added to an audiovisual presentation by pausing the video so that there is time to add additional description.

**Intent (informative):** Fast-paced content (dense dialogue, rapid visual demonstrations) leaves no gaps for standard description. Extended description pauses the video to narrate, ensuring blind users get the full sense of the content.

**How to test:**
1. Identify videos where standard audio description cannot fit in the dialogue pauses (compare the visual information inventory with available gaps).
2. Confirm an extended-description version exists that pauses the video to describe.
Pass when such a version is provided for every applicable video.

**Common failures:** None listed.

**Sufficient techniques:**
- G8 Providing a movie with extended audio descriptions, using one of: SM1 Adding extended audio description in SMIL 1.0; SM2 Adding extended audio description in SMIL 2.0

**Advisory techniques:** H96 Using the track element to provide audio descriptions

**Implementation notes (HTML/CSS/ARIA):** Produce a separate rendition with inserted pauses, or use a player that supports `kind="descriptions"` with pause-on-cue behaviour (e.g. Able Player's extended descriptions).

**Related:** 1.2.3, 1.2.5.

### 1.2.8 Media Alternative (Prerecorded) (Level AAA)

**Normative text (verbatim):**
> An alternative for time-based media is provided for all prerecorded synchronized media and for all prerecorded video-only media.

**Intent (informative):** A full descriptive transcript (dialogue + visual description + any interaction outcomes) serves deafblind users, people who read braille, and people who cannot process audio or video at all. At AAA it is required in addition to captions and audio description.

**How to test:**
1. For every prerecorded synchronized media and video-only item, locate the text alternative.
2. Verify it includes all dialogue/sounds in sequence, descriptions of visual information, and a way to achieve the outcomes of any interaction in the media.
3. If the media is itself an alternative to text, verify it is labeled as such (F74).
Pass when a complete alternative is provided and discoverable.

**Common failures:**
- F74 Failure of Success Criterion 1.2.2 and 1.2.8 due to not labeling a synchronized media alternative to text as an alternative

**Sufficient techniques:**
- Situation A: If the content is prerecorded synchronized media: G69 Providing an alternative for time based media, using one of: G58 Placing a link to the alternative for time-based media immediately next to the non-text content; linking to the alternative for time-based media using H53 Using the body of the object element
- Situation B: If the content is prerecorded video-only: G159 Providing an alternative for time-based media for video-only content

**Implementation notes (HTML/CSS/ARIA):** Place the transcript directly below the player or link it immediately adjacent; use headings so it can be navigated.

**Related:** 1.2.1, 1.2.2, 1.2.3.

### 1.2.9 Audio-only (Live) (Level AAA)

**Normative text (verbatim):**
> An alternative for time-based media that presents equivalent information for live audio-only content is provided.

**Intent (informative):** Live radio-style streams, audio conferences and announcements need real-time text (live captioning service or, when a script is followed, the script) so deaf and hard-of-hearing users can follow in real time.

**How to test:**
1. Identify live audio-only streams.
2. Confirm a live text stream (captioning service output) or, for scripted content, a transcript/script link is available during the broadcast.
Pass when equivalent live text is provided.

**Common failures:** None listed.

**Sufficient techniques:**
- G151 Providing a link to a text transcript of a prepared statement or script if the script is followed
- G150 Providing text based alternatives for live audio-only content
- G157 Incorporating a live audio captioning service into a web page

**Implementation notes (HTML/CSS/ARIA):** Embed the captioner's live text viewer (`<iframe title="Live captions">`) next to the audio player.

**Related:** 1.2.4 Captions (Live), 1.2.1.

---

## Guideline 1.3 Adaptable

> Create content that can be presented in different ways (for example simpler layout) without losing information or structure.

### 1.3.1 Info and Relationships (Level A)

**Normative text (verbatim):**
> Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text.

**Key terms:** *programmatically determined* = determined by software from author-supplied data provided in a way that different user agents, including assistive technologies, can extract and present this information to users in different modalities. *Structure* = the way the parts of a web page are organized in relation to each other, and the way a collection of web pages is organized. *Relationships* = meaningful associations between distinct pieces of content.

**Intent (informative):** Sighted users infer structure from visual cues: bigger bold text is a heading, indented lines are a list, a grid is a table, a word next to a box is its label. Screen reader users, people using custom style sheets, and braille users only get that structure if it is expressed in markup (headings, lists, tables with header cells, `<label>`, `<fieldset>`, landmarks) or stated in text. This is the single most frequently cited criterion in audits.

**How to test:**
1. Headings: every visual heading uses `<h1>`–`<h6>` (or `role="heading"` + `aria-level`); nothing non-heading is marked as a heading; levels reflect nesting (skipped levels are a best-practice issue, not a strict failure). Use a headings outline tool.
2. Lists: visually listed items use `<ul>`/`<ol>`/`<dl>`; not `<br>`-separated lines or paragraphs with "•" characters.
3. Data tables: `<table>` with `<th>` header cells (with `scope`, or `headers`/`id` for complex tables), `<caption>` where a visible title exists; layout tables must not use `<th>`/`<caption>`/`summary` and should carry `role="presentation"`. Verify header associations using a screen reader or the accessibility tree.
4. Forms: each control has a programmatically associated label (`<label for>`, wrapping label, `aria-labelledby`, `aria-label`); related groups (radio/checkbox sets, address blocks) use `<fieldset>`/`<legend>` or `role="group"` + name; required state and error state are in markup or text, not only colour/asterisk styling.
5. Emphasis and meaning conveyed by styling (bold = required, red = overdue, strike-through = discontinued) is also available in markup (`<strong>`, `<em>`, `<del>`) or in text.
6. Regions: page areas identified by landmarks/semantic elements (`<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`) — not strictly required by 1.3.1 but the sufficient techniques list them.
7. Check for `role="presentation"`/`aria-hidden` wrongly applied to semantic content (F92), `<pre>` used for tables (F48), whitespace-formatted columns (F33/F34).
8. Confirm that custom components do not strip semantics (e.g. `<div>` links – F42).
Pass when all visually conveyed structure and relationships are exposed programmatically or stated in text.

**Common failures:**
- F2 Failure of Success Criterion 1.3.1 due to using changes in text presentation to convey information without using the appropriate markup or text
- F33 Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to create multiple columns in plain text content
- F34 Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to format tables in plain text content
- F42 Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links
- F43 Failure of Success Criterion 1.3.1 due to using structural markup in a way that does not represent relationships in the content
- F46 Failure of Success Criterion 1.3.1 due to using th elements, caption elements, or non-empty summary attributes in layout tables
- F48 Failure of Success Criterion 1.3.1 due to using the pre element to markup tabular information
- F90 Failure of Success Criterion 1.3.1 for incorrectly associating table headers and content via the headers and id attributes
- F91 Failure of Success Criterion 1.3.1 for not correctly marking up table headers
- F92 Failure of Success Criterion 1.3.1 due to the use of role presentation on content which conveys semantic information
- F111 Failure of Success Criteria 1.3.1, 2.5.3, and 4.1.2 due to a control with visible label text but no accessible name
- Typical examples: "headings" made with `<p class="title">`; a form where the label text sits in a `<span>` with no `for`/`id` association; a data table whose first row uses `<td>` in bold; a list of steps written as paragraphs starting with "1.", "2.".

**Sufficient techniques:**
- Situation A: The technology provides semantic structure to make information and relationships conveyed through presentation programmatically determinable:
  - ARIA11 Using ARIA landmarks to identify regions of a page; H101 Using semantic HTML elements to identify regions of a page; ARIA12 Using role=heading to identify headings; ARIA13 Using aria-labelledby to name regions and landmarks; ARIA16 Using aria-labelledby to provide a name for user interface controls; ARIA17 Using grouping roles to identify related form controls; ARIA20 Using the region role to identify a region of the page
  - G115 Using semantic elements to mark up structure AND H49 Using semantic markup to mark emphasized or special text
  - G117 Using text to convey information that is conveyed by variations in presentation of text
  - G140 Separating information and structure from presentation to enable different presentations
  - ARIA24 Semantically identifying a font icon with role="img"
  - Making information and relationships conveyed through presentation programmatically determinable, using: ARIA26 Using aria-current to identify the current item in a set; G138 Using semantic markup whenever color cues are used; H51 Using table markup to present tabular information; PDF6 Using table elements for table markup in PDF Documents; PDF20 Using Adobe Acrobat Pro's Table Editor to repair mistagged tables; H39 Using caption elements to associate data table captions with data tables; H63 Using the scope attribute to associate header cells with data cells in data tables; H43 Using id and headers attributes to associate data cells with header cells in data tables; H44 Using label elements to associate text labels with form controls; H65 Using the title attribute to identify form controls when the label element cannot be used; PDF10 Providing labels for interactive form controls in PDF documents; PDF12 Providing name, role, value information for form fields in PDF documents; H71 Providing a description for groups of form controls using fieldset and legend elements; H85 Using optgroup to group option elements inside a select; H48 Using ol, ul and dl for lists or groups of links; H42 Using h1-h6 to identify headings; PDF9 Providing headings by marking content with heading tags in PDF documents; PDF11 Providing links and link text using the Link annotation and the /Link structure element in PDF documents; PDF17 Specifying consistent page numbering for PDF documents; PDF21 Using List tags for lists in PDF documents; H97 Grouping related links using the nav element
- Situation B: The technology in use does NOT provide the semantic structure to make the information and relationships conveyed through presentation programmatically determinable:
  - G117 Using text to convey information that is conveyed by variations in presentation of text
  - Making information and relationships conveyed through presentation programmatically determinable or available in text, using: T1 Using standard text formatting conventions for paragraphs; T2 Using standard text formatting conventions for lists; T3 Using standard text formatting conventions for headings

**Advisory techniques:** C22 Using CSS to control visual presentation of text; G162 Positioning labels to maximize predictability of relationships; ARIA1 Using the aria-describedby property to provide a descriptive label for user interface controls; ARIA2 Identifying a required field with the aria-required property; G141 Organizing a page using headings

**Implementation notes (HTML/CSS/ARIA):**
```html
<h2>Opening hours</h2>
<table>
  <caption>Opening hours by day</caption>
  <thead><tr><th scope="col">Day</th><th scope="col">Hours</th></tr></thead>
  <tbody><tr><th scope="row">Monday</th><td>9:00–17:00</td></tr></tbody>
</table>

<label for="email">Email address <span aria-hidden="true">*</span></label>
<input id="email" type="email" required aria-required="true">

<fieldset>
  <legend>Preferred contact method</legend>
  <label><input type="radio" name="c" value="email"> Email</label>
  <label><input type="radio" name="c" value="phone"> Phone</label>
</fieldset>

<!-- Wrong -->
<p class="h2">Opening hours</p>          <!-- visual heading, no semantics -->
<div class="row"><b>Name</b> Ana</div>   <!-- table built with divs and bold -->
```

**Related:** 1.3.2 Meaningful Sequence, 1.4.1 Use of Color, 2.4.6 Headings and Labels (quality of headings), 3.3.2 Labels or Instructions, 4.1.2 Name, Role, Value, 2.4.1 Bypass Blocks (landmarks/headings).

### 1.3.2 Meaningful Sequence (Level A)

**Normative text (verbatim):**
> When the sequence in which content is presented affects its meaning, a correct reading sequence can be programmatically determined.

**Key term:** *correct reading sequence* = any sequence where words and paragraphs are presented in an order that does not change the meaning of the content.

**Intent (informative):** Screen readers and reflowed/linearized presentations follow the DOM order, not the visual layout. If CSS positioning, flexbox `order`, floats or layout tables rearrange content visually, a screen reader user may hear instructions after the field they apply to, or columns interleaved. The criterion requires that at least one programmatically determinable order preserves meaning.

**How to test:**
1. Disable CSS (or use a linearize/"reading order" tool, or read the DOM top-to-bottom in the accessibility tree) and read the page.
2. Compare with the visual order: do labels precede their fields, do steps appear in order, do multi-column layouts read column by column rather than row-interleaved?
3. Check for CSS `order`, `flex-direction: *-reverse`, `grid` placement, absolute positioning or `float` that reorders meaningful content.
4. Check inline tricks: words spaced with whitespace characters (F32), plain-text columns made with spaces (F33/F34), layout tables that make no sense when linearized (F49), CSS positioning that changes meaning (F1).
5. For PDF, inspect the tag/reading order.
Pass when the DOM/reading order yields the same meaning as the visual order.

**Common failures:**
- F34 Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to format tables in plain text content
- F33 Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to create multiple columns in plain text content
- F32 Failure of Success Criterion 1.3.2 due to using white space characters to control spacing within a word
- F49 Failure of Success Criterion 1.3.2 due to using an HTML layout table that does not make sense when linearized
- F1 Failure of Success Criterion 1.3.2 due to changing the meaning of content by positioning information with CSS
- Typical examples: a card grid where CSS `order` puts "Step 3" before "Step 1" in the DOM; a price "$ 1 9 9" letter-spaced with actual spaces, read as separate characters; a sidebar with "Important: read before applying" placed after the form in DOM.

**Sufficient techniques:**
- G57 Ordering the content in a meaningful sequence (for all the content in the web page)
- G57 Ordering the content in a meaningful sequence (for those sequences), using: H34 Using a Unicode right-to-left mark (RLM) or left-to-right mark (LRM) to mix text direction inline; H56 Using the dir attribute on an inline element to resolve problems with nested directional runs; C6 Positioning content based on structural markup; C8 Using CSS letter-spacing to control spacing within a word
- C27 Making the DOM order match the visual order
- PDF3 Ensuring correct tab and reading order in PDF documents

**Implementation notes (HTML/CSS/ARIA):**
```css
/* Prefer source order that matches meaning; avoid reordering with `order` */
.brand { letter-spacing: 0.3em; } /* instead of "B R A N D" with spaces (F32) */
```
```html
<!-- Mixed-direction text -->
<p>The Hebrew word <span dir="rtl" lang="he">שלום</span> means peace.</p>
```

**Related:** 1.3.1, 2.4.3 Focus Order (the interactive counterpart), 1.4.10 Reflow.

### 1.3.3 Sensory Characteristics (Level A)

**Normative text (verbatim):**
> Instructions provided for understanding and operating content do not rely solely on sensory characteristics of components such as shape, color, size, visual location, orientation, or sound.
>
> NOTE: For requirements related to color, refer to Guideline 1.4.

**Intent (informative):** "Click the round button", "see the box on the right", "wait for the beep" only work for people who can see the shape/position or hear the sound. Instructions must also identify the component by its name/label or in a way that survives linearization and non-visual presentation. Adding the sensory cue is fine; relying on it alone is not.

**How to test:**
1. Search instructional text (help text, form hints, error messages, onboarding) for references to shape, colour, size, position ("left", "right", "above", "below", "sidebar"), orientation, or sound.
2. For each, confirm an additional non-sensory identifier is present (the control's label, a heading name, a numbered step, "the Submit button").
3. References to things with the same visual-and-DOM order ("the next section", "above" when the content is also previous in the DOM) are generally acceptable; location-only references to a sidebar that lands elsewhere in reading order are not.
4. Icons used alone to convey instructions must have text (F26).
Pass when every instruction can be followed without perceiving the sensory characteristic.

**Common failures:**
- F14 Failure of Success Criterion 1.3.3 due to identifying content only by its shape or location
- F26 Failure of Success Criterion 1.3.3 due to using a graphical symbol alone to convey information
- Typical examples: "Press the green button to continue"; "Use the menu on the left to filter results"; "Fields marked with a ★ are required" with no textual indication.

**Sufficient techniques:**
- G96 Providing textual identification of items that otherwise rely only on sensory information to be understood

**Implementation notes (HTML/CSS/ARIA):**
```html
<!-- Instead of: "Click the round green button" -->
<p>Select <strong>Start application</strong> (the round green button) to continue.</p>
<!-- Instead of: "Required fields are marked with an asterisk" alone -->
<label for="dni">DNI (required)</label>
```

**Related:** 1.4.1 Use of Color, 1.3.1 Info and Relationships, 3.3.2 Labels or Instructions, 2.4.6.

### 1.3.4 Orientation (Level AA)

**Normative text (verbatim):**
> Content does not restrict its view and operation to a single display orientation, such as portrait or landscape, unless a specific display orientation is essential.
>
> NOTE: Examples where a particular display orientation may be essential are a bank check, a piano application, slides for a projector or television, or virtual reality content where content is not necessarily restricted to landscape or portrait display orientation.

**Intent (informative):** Some users have devices mounted in a fixed orientation on a wheelchair or bed; others cannot physically rotate a device. Content that only works in portrait (or forces landscape with a "please rotate" message) locks them out. Responsive layouts that adapt to both orientations satisfy the criterion.

**How to test:**
1. Open the content on a mobile device or emulator; rotate between portrait and landscape.
2. Confirm all content and functionality is available in both orientations (layout may differ).
3. Check for `screen.orientation.lock()`, manifest `"orientation"` restrictions in installed web apps, or CSS/JS that hides content or shows a "rotate your device" overlay (F100).
4. Where an orientation lock exists, assess whether it is essential (bank cheque imaging, piano keyboard, slides) — if essential, it passes; alternatively a control to switch orientation (G214) also passes.
Pass when content works in both orientations or the lock is essential.

**Common failures:**
- F97 Failure due to locking the orientation to landscape or portrait view
- F100 Failure of Success Criterion 1.3.4 due to showing a message asking to reorient device
- Typical examples: a dashboard that displays "Please rotate your device to landscape" in portrait; a PWA manifest with `"orientation": "portrait"` without an essential reason.

**Sufficient techniques:**
- G214 Using a control to allow access to content in different orientations which is otherwise restricted

**Implementation notes (HTML/CSS/ARIA):**
```css
/* Use orientation/width media queries to adapt, never to hide */
@media (orientation: landscape) { .toolbar { flex-direction: row; } }
```
Avoid `screen.orientation.lock("portrait")` and manifest `orientation` keys unless essential.

**Related:** 1.4.10 Reflow, 1.4.4 Resize Text.

### 1.3.5 Identify Input Purpose (Level AA)

**Normative text (verbatim):**
> The purpose of each input field collecting information about the user can be programmatically determined when:
>
> - The input field serves a purpose identified in the Input Purposes for user interface components section; and
> - The content is implemented using technologies with support for identifying the expected meaning for form input data.

**Intent (informative):** When fields that collect the user's own data (name, email, address, phone, credit card…) carry a machine-readable purpose, browsers can autofill them and assistive tools can add icons or familiar labels. This mainly helps people with cognitive and motor disabilities who struggle to type or remember their information. In HTML the technology with support is the `autocomplete` attribute, using the 53 token values listed in WCAG 2.2 section 7 (which mirror the HTML autofill field names).

**How to test:**
1. Identify form fields that collect information *about the user* (not about third parties, not search terms, not dates of events): name, given-name, family-name, email, tel, street-address, postal-code, country, bday, cc-number, username, new-password, current-password, organization, etc.
2. Check each has an `autocomplete` attribute with the correct token from the Input Purposes list (plus optional section/`shipping`/`billing` prefixes).
3. Verify tokens are valid and match the field (e.g. `autocomplete="email"` on an email field, not `autocomplete="on"` or a misspelled/mismatched value — F107).
4. Fields outside the list (e.g. "Pet's name") are out of scope.
Pass when every in-scope field carries the correct purpose token.

**Common failures:**
- F107 Failure of Success Criterion 1.3.5 due to incorrect autocomplete attribute values
- Typical examples: a registration form with no `autocomplete` attributes; `autocomplete="first-name"` (invalid; should be `given-name`); `autocomplete="off"` on the user's own email field in a profile form.

**Sufficient techniques:**
- H98 Using HTML autocomplete attributes

**Implementation notes (HTML/CSS/ARIA):**
```html
<label for="gn">First name</label>
<input id="gn" name="firstname" autocomplete="given-name">
<label for="em">Email</label>
<input id="em" type="email" autocomplete="email">
<label for="tel">Mobile phone</label>
<input id="tel" type="tel" autocomplete="tel">
<label for="ship">Shipping postal code</label>
<input id="ship" autocomplete="shipping postal-code">
<label for="pw">New password</label>
<input id="pw" type="password" autocomplete="new-password">
```
The full token list is in WCAG 2.2 §7 "Input Purposes for User Interface Components" (see the glossary/conformance reference file).

**Related:** 1.3.6 Identify Purpose (AAA, wider scope), 3.3.7 Redundant Entry, 3.3.8 Accessible Authentication (password managers rely on `autocomplete`).

### 1.3.6 Identify Purpose (Level AAA)

**Normative text (verbatim):**
> In content implemented using markup languages, the purpose of user interface components, icons, and regions can be programmatically determined.

**Intent (informative):** Extends 1.3.5 beyond user-data fields: when regions (landmarks), controls and icons expose their purpose in markup, user agents and personalization tools can swap in familiar symbols, simplify the interface or hide non-essential regions for people with cognitive disabilities.

**How to test:**
1. Check that page regions use landmarks/semantic elements (`<nav>`, `<main>`, `role="search"`, etc.) with names where there are several of a type.
2. Check that interactive components expose role and purpose (native elements, ARIA roles, `aria-label`), and that common buttons/links carry recognizable purposes.
3. Check that icons are identified (e.g. `role="img"` + name, or a recognized personalization vocabulary where used).
4. Where a personalization vocabulary (e.g. WAI-Adapt / `data-purpose`-style attributes) is used, verify consistency.
Pass when regions, components and icons expose purpose programmatically.

**Common failures:** None listed.

**Sufficient techniques:**
- Programmatically indicating the purpose of icons, regions and user interface components
- ARIA11 Using ARIA landmarks to identify regions of a page
- Using microdata to markup user interface components (future link)

**Advisory techniques:** Enabling user agents to find the version of the content that best fits their needs; Using semantics to identify important features (e.g., coga-simplification="simplest"); Using required, or the combination of aria-required and aria-invalid, to programmatically identify required fields and/or those with validation errors

**Implementation notes (HTML/CSS/ARIA):**
```html
<header>…</header>
<nav aria-label="Main">…</nav>
<main>…</main>
<form role="search" aria-label="Site search">…</form>
<footer>…</footer>
<button type="button"><svg role="img" aria-label="Help">…</svg></button>
```

**Related:** 1.3.5, 1.3.1, 4.1.2, 2.4.1 (landmarks).

---

## Guideline 1.4 Distinguishable

> Make it easier for users to see and hear content including separating foreground from background.

**Key terms used across 1.4.x:**
- *Contrast ratio* = (L1 + 0.05) / (L2 + 0.05), where L1 is the relative luminance of the lighter colour and L2 of the darker; ranges 1:1 to 21:1. Relative luminance for sRGB: L = 0.2126 R + 0.7152 G + 0.0722 B, where each channel c = c8bit/255 is linearized as c/12.92 if c ≤ 0.04045, else ((c + 0.055)/1.055)^2.4.
- *Large scale (text)* = at least 18 point, or 14 point bold (or equivalent size for CJK fonts). With the CSS 1pt = 1.333px conversion this is ≈ 24px regular or ≈ 18.67px bold (commonly rounded to 19px bold).
- *CSS pixel* = visual angle of about 0.0213 degrees; the density-independent canonical CSS unit.
- *Image of text* = text that has been rendered in a non-text form (e.g. an image) in order to achieve a particular visual effect (excludes text that is part of a picture with significant other visual content).
- *Blocks of text* = more than one sentence of text.
- *Essential* = if removed, would fundamentally change the information or functionality of the content, and information and functionality cannot be achieved in another way that would conform.
- *User interface component* = a part of the content that is perceived by users as a single control for a distinct function.

### 1.4.1 Use of Color (Level A)

**Normative text (verbatim):**
> Color is not used as the only visual means of conveying information, indicating an action, prompting a response, or distinguishing a visual element.
>
> NOTE: This success criterion addresses color perception specifically. Other forms of perception are covered in Guideline 1.3 including programmatic access to color and other visual presentation coding.

**Intent (informative):** Around 8% of men and 0.5% of women have a colour vision deficiency; many low-vision users view in high-contrast or monochrome modes. Colour may be used, but every piece of information it carries must also be available through another visual cue (text, icon, pattern, underline, border, shape) that does not depend on hue. Note this is a *visual* requirement — it is about sighted users, so "also in the DOM" is not enough on its own (that is 1.3.1).

**How to test:**
1. View the page in greyscale (browser/OS filter, or a colour-blindness simulator) and look for information that disappears: status indicators, chart series, required/error fields, selected tabs, links in body text.
2. Links inside paragraphs: if they are distinguished from surrounding text by colour alone, confirm either a non-colour cue (underline, bold, icon) or ≥3:1 contrast between link and body text plus a non-colour cue on hover/focus (G183). Otherwise F73.
3. Form errors/required fields: a red border or red label alone fails (F81); there must be text, an icon or another cue.
4. Charts/maps: series need labels, patterns, shapes or direct data labels in addition to colour (G111); image alt text must include the colour-coded information (F13).
5. Interactive states (selected, active, current): confirm a second cue (bold, underline, border, check icon).
Pass when no information, action prompt or distinction relies on colour alone.

**Common failures:**
- F13 Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image
- F73 Failure of Success Criterion 1.4.1 due to creating links that are not visually evident without color vision
- F81 Failure of Success Criterion 1.4.1 due to identifying required or error fields using color differences only
- Typical examples: a legend "green = available, red = booked" on a calendar with no symbols; invalid fields highlighted only with a red outline; a line chart with four coloured lines and a colour-only legend.

**Sufficient techniques:**
- Situation A: If the color of particular words, backgrounds, or other content is used to indicate information: G14 Ensuring that information conveyed by color differences is also available in text; G205 Including a text cue for colored form control labels; G182 Ensuring that additional visual cues are available when text color differences are used to convey information; G183 Using a contrast ratio of at least 3:1 to distinguish inline text links from surrounding text
- Situation B: If color is used within an image to convey information: G111 Using color and pattern; G14 Ensuring that information conveyed by color differences is also available in text

**Advisory techniques:** C15 Using CSS to change the presentation of a user interface component when it receives focus

**Implementation notes (HTML/CSS/ARIA):**
```html
<!-- Error: colour + icon + text -->
<label for="cuit">CUIT</label>
<input id="cuit" aria-invalid="true" aria-describedby="cuit-err" class="is-error">
<p id="cuit-err"><span aria-hidden="true">⚠</span> Error: CUIT must have 11 digits.</p>
```
```css
p a { color: #0645ad; text-decoration: underline; } /* don't remove underline on body links */
.status--ok::before { content: "✓ "; }           /* icon + text, not colour alone */
```

**Related:** 1.3.1 (programmatic equivalent), 1.3.3 Sensory Characteristics, 1.4.3 and 1.4.11 (contrast), 3.3.1 Error Identification.

### 1.4.2 Audio Control (Level A)

**Normative text (verbatim):**
> If any audio on a web page plays automatically for more than 3 seconds, either a mechanism is available to pause or stop the audio, or a mechanism is available to control audio volume independently from the overall system volume level.
>
> NOTE: Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether or not it is used to meet other success criteria) must meet this success criterion. See Conformance Requirement 5: Non-Interference.

**Intent (informative):** Screen reader users hear their synthesizer through the same speakers; auto-playing audio drowns it out and they may be unable to find the stop control. This is one of the four "non-interference" criteria: a single failure anywhere on the page blocks conformance of the whole page. The criterion also includes the audio of auto-playing video.

**How to test:**
1. Load each page and listen for audio that starts without user action (background music, video with sound, notification sounds, ads).
2. If any plays longer than 3 seconds, confirm there is a pause/stop control or an independent volume control, located near the start of the page (so a screen reader user reaches it first) and operable by keyboard and AT.
3. Check `<audio autoplay>`/`<video autoplay>` without `muted` and without visible controls (F93), and scripted playback on load.
4. Verify the control actually works and is discoverable.
Pass when no audio autoplays > 3 s, or a usable pause/stop/volume mechanism exists.

**Common failures:**
- F23 Failure of 1.4.2 due to playing a sound longer than 3 seconds where there is no mechanism to turn it off
- F93 Failure of Success Criterion 1.4.2 for absence of a way to pause or stop an HTML5 media element that autoplays
- Typical examples: a hero video that autoplays with sound and hides its controls; a landing page with looping background music and the mute button in the footer only.

**Sufficient techniques:**
- G60 Playing a sound that turns off automatically within three seconds
- G170 Providing a control near the beginning of the web page that turns off sounds that play automatically
- G171 Playing sounds only on user request

**Implementation notes (HTML/CSS/ARIA):**
```html
<!-- Autoplaying background video: muted, with a visible pause -->
<video autoplay muted loop playsinline aria-hidden="true" src="bg.mp4"></video>
<button type="button" id="pause-bg">Pause background video</button>
```
Best practice is G171 — never autoplay audio.

**Related:** 2.2.2 Pause, Stop, Hide (moving content), Conformance Requirement 5.2.5 Non-Interference, 1.4.7.

### 1.4.3 Contrast (Minimum) (Level AA)

**Normative text (verbatim):**
> The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:
>
> **Large Text** — Large-scale text and images of large-scale text have a contrast ratio of at least 3:1;
>
> **Incidental** — Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
>
> **Logotypes** — Text that is part of a logo or brand name has no contrast requirement.

**Intent (informative):** People with low vision, ageing eyes or colour deficiencies need enough luminance difference between text and background to read without assistive technology. 4.5:1 compensates for roughly 20/40 vision; large text (≥ 18pt or ≥ 14pt bold, ≈ 24px / 18.67px bold) is easier to read and so only needs 3:1. Placeholder text, text on images and disabled controls are frequent trouble spots (disabled controls are exempt, placeholders are not).

**How to test:**
1. Identify all text and images of text, including placeholders, links, buttons, labels, helper text, text over images/gradients, and every state (hover, focus, visited, selected).
2. Measure foreground vs. background colour with a contrast tool (browser devtools, axe, Colour Contrast Analyser). Use the colour actually rendered behind the text; for gradients/images measure the worst-case area (F83).
3. Thresholds: ≥ 4.5:1 for normal text; ≥ 3:1 for large-scale text (≥ 24px regular or ≥ 18.67px/≈19px bold). Font weight 700 counts as bold; very light fonts may need extra care.
4. Exempt: text in disabled (inactive) controls, purely decorative text, invisible text, text in photos with significant other content, logotypes.
5. Check that foreground and background are both specified in CSS (specifying only one is F24).
6. Check text with `opacity`, semi-transparent overlays, and dark-mode variants separately.
Pass when every in-scope text/background pair meets its threshold.

**Common failures:**
- F24 Failure of Success Criterion 1.4.3, 1.4.6 and 1.4.8 due to specifying foreground colors without specifying background colors or vice versa
- F83 Failure of Success Criterion 1.4.3 and 1.4.6 due to using background images that do not provide sufficient contrast with foreground text (or images of text)
- Typical examples: light grey placeholder text `#999` on white (2.8:1); white text over a light photo without an overlay; `#777` body text on `#fff` (4.48:1 — just below).

**Sufficient techniques:**
- Situation A: text is less than 18 point if not bold and less than 14 point if bold: G18 Ensuring that a contrast ratio of at least 4.5:1 exists between text (and images of text) and background behind the text; G148 Not specifying background color, not specifying text color, and not using technology features that change those defaults; G174 Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast
- Situation B: text is at least 18 point if not bold and at least 14 point if bold: G145 Ensuring that a contrast ratio of at least 3:1 exists between text (and images of text) and background behind the text; G148 Not specifying background color, not specifying text color, and not using technology features that change those defaults; G174 Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast

**Advisory techniques:** G156 Using a technology that has commonly-available user agents that can change the foreground and background of blocks of text

**Implementation notes (HTML/CSS/ARIA):**
```css
body { color: #1a1a1a; background: #fff; }   /* 17.4:1 */
::placeholder { color: #595959; opacity: 1; } /* 7:1 on white */
.hero { background: url(photo.jpg); }
.hero h1 { color: #fff; background: rgba(0,0,0,.6); } /* overlay to guarantee contrast */
```
Quick reference pairs on white: `#767676` = 4.54:1 (minimum normal text); `#949494` = 3:1 (large text only); `#595959` = 7:1 (AAA).

**Related:** 1.4.6 Contrast (Enhanced), 1.4.11 Non-text Contrast, 1.4.1 Use of Color, 1.4.5 Images of Text, 2.4.13 Focus Appearance.

### 1.4.4 Resize Text (Level AA)

**Normative text (verbatim):**
> Except for captions and images of text, text can be resized without assistive technology up to 200 percent without loss of content or functionality.

**Intent (informative):** Many people with low vision enlarge text with browser zoom or text-only scaling rather than screen magnifiers. Content must remain readable and operable at 200%: no clipping, no overlapping, no controls pushed off-screen, no truncated labels. Any user-agent mechanism counts (page zoom, text-size setting), but the author must not break it.

**How to test:**
1. Set the browser to 200% zoom (Ctrl/Cmd +) on a desktop viewport and review every page/state: all text visible, nothing overlapping or clipped, all functionality still operable.
2. Also test text-only scaling (Firefox "Zoom text only" at 200%, or minimum font size settings) because fixed-height containers and `px`-sized form fields often break here (F69, F80).
3. Check for `maximum-scale=1` / `user-scalable=no` in the viewport meta tag on mobile, which blocks pinch-zoom (treated as a failure of this criterion in most methodologies).
4. Check text sized in viewport units (`vw`) without a `calc()`/`clamp()` fallback, which does not scale with zoom (F94).
5. Verify in-page text-size widgets, if relied upon, reach 200% for all text (G178).
Pass when all text can be enlarged to 200% without loss of content or functionality.

**Common failures:**
- F69 Failure of Success Criterion 1.4.4 when resizing visually rendered text up to 200 percent causes the text, image or controls to be clipped, truncated or obscured
- F80 Failure of Success Criterion 1.4.4 when text-based form controls do not resize when visually rendered text is resized up to 200%
- F94 Failure of Success Criterion 1.4.4 due to incorrect use of viewport units to resize text
- Typical examples: a fixed-height card whose text overflows and is cut off at 200%; a navigation bar whose items overlap; `<meta name="viewport" content="… user-scalable=no">`.

**Sufficient techniques:**
- G142 Using a technology that has commonly-available user agents that support zoom
- Ensuring that text containers resize when the text resizes AND using measurements that are relative to other measurements in the content, using: C28 Specifying the size of text containers using em units; techniques for relative measurements (C12 Using percent for font sizes; C13 Using named font sizes; C14 Using em units for font sizes); techniques for text container resizing (SCR34 Calculating size and position in a way that scales with text size; G146 Using liquid layout)
- G178 Providing controls on the web page that allow users to incrementally change the size of all text on the page up to 200 percent
- G179 Ensuring that there is no loss of content or functionality when the text resizes and text containers do not change their width

**Advisory techniques:** C17 Scaling form elements which contain text; C20 Using relative measurements to set column widths so that lines can average 80 characters or less when the browser is resized; C22 Using CSS to control visual presentation of text

**Implementation notes (HTML/CSS/ARIA):**
```html
<meta name="viewport" content="width=device-width, initial-scale=1">  <!-- no maximum-scale / user-scalable=no -->
```
```css
html { font-size: 100%; }                 /* respect user default */
.card { min-height: 12rem; height: auto; } /* let containers grow */
h1 { font-size: clamp(1.5rem, 2vw + 1rem, 3rem); } /* vw only inside clamp/calc with rem */
input, button { font: inherit; }
```

**Related:** 1.4.10 Reflow (400% zoom / 320px), 1.4.12 Text Spacing, 1.4.8 Visual Presentation.

### 1.4.5 Images of Text (Level AA)

**Normative text (verbatim):**
> If the technologies being used can achieve the visual presentation, text is used to convey information rather than images of text except for the following:
>
> **Customizable** — The image of text can be visually customized to the user's requirements;
>
> **Essential** — A particular presentation of text is essential to the information being conveyed.
>
> NOTE: Logotypes (text that is part of a logo or brand name) are considered essential.

**Intent (informative):** Real text can be resized, recoloured, respaced, reflowed, read by screen readers and translated; text baked into images pixelates when zoomed and cannot be adapted. With web fonts and CSS, nearly any visual treatment is achievable in real text, so images of text should be reserved for logos and cases where the exact rendering is the point (e.g. a scanned historical letter, a font specimen).

**How to test:**
1. Find images that contain text (banners, buttons, headings as images, infographics, screenshots used as content, scanned PDFs).
2. For each, ask: could CSS/HTML reproduce the presentation? If yes, it should be real text.
3. Exceptions: logos/brand names; text that is essential in that exact presentation; images users can customize (font, size, colour, background).
4. Scanned documents without OCR text fail (PDF7 is the fix).
Pass when all non-essential, non-customizable text is real text.

**Common failures:**
- No F-technique listed; failures are judged by presence of avoidable images of text.
- Typical examples: a "Register now" button that is a PNG; a page heading rendered as a graphic in a brand font; a scanned notice published as an image with no text layer.

**Sufficient techniques:**
- C22 Using CSS to control visual presentation of text
- C30 Using CSS to replace text with images of text and providing user interface controls to switch
- G140 Separating information and structure from presentation to enable different presentations
- PDF7 Performing OCR on a scanned PDF document to provide actual text

**Advisory techniques:** C12 Using percent for font sizes; C13 Using named font sizes; C14 Using em units for font sizes; C8 Using CSS letter-spacing to control spacing within a word; C6 Positioning content based on structural markup

**Implementation notes (HTML/CSS/ARIA):**
```css
@font-face { font-family: "Brand"; src: url(brand.woff2) format("woff2"); font-display: swap; }
.hero-title { font-family: "Brand", sans-serif; letter-spacing: .05em; text-transform: uppercase; }
```
If an image of text is unavoidable, its `alt` must contain the same text (1.1.1) and it should still meet contrast (1.4.3).

**Related:** 1.4.9 (AAA, no exceptions), 1.1.1, 1.4.3, 1.4.4.

### 1.4.6 Contrast (Enhanced) (Level AAA)

**Normative text (verbatim):**
> The visual presentation of text and images of text has a contrast ratio of at least 7:1, except for the following:
>
> **Large Text** — Large-scale text and images of large-scale text have a contrast ratio of at least 4.5:1;
>
> **Incidental** — Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
>
> **Logotypes** — Text that is part of a logo or brand name has no contrast requirement.

**Intent (informative):** 7:1 compensates for roughly 20/80 vision, serving people with more significant low vision who do not use assistive technology. Same scope and exceptions as 1.4.3 with higher thresholds.

**How to test:** Same procedure as 1.4.3 with thresholds ≥ 7:1 for normal text and ≥ 4.5:1 for large-scale text.

**Common failures:**
- F24 Failure of Success Criterion 1.4.3, 1.4.6 and 1.4.8 due to specifying foreground colors without specifying background colors or vice versa
- F83 Failure of Success Criterion 1.4.3 and 1.4.6 due to using background images that do not provide sufficient contrast with foreground text (or images of text)

**Sufficient techniques:**
- Situation A: text is less than 18 point if not bold and less than 14 point if bold: G17 Ensuring that a contrast ratio of at least 7:1 exists between text (and images of text) and background behind the text; G148 Not specifying background color, not specifying text color, and not using technology features that change those defaults; G174 Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast
- Situation B: text is at least 18 point if not bold and at least 14 point if bold: G18 Ensuring that a contrast ratio of at least 4.5:1 exists between text (and images of text) and background behind the text; G148 Not specifying background color, not specifying text color, and not using technology features that change those defaults; G174 Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast

**Advisory techniques:** G156 Using a technology that has commonly-available user agents that can change the foreground and background of blocks of text

**Implementation notes (HTML/CSS/ARIA):** On white, `#595959` (7:1) is the lightest grey for normal text; `#767676` (4.54:1) is acceptable for large text only. A high-contrast theme toggle (G174) is a common way to meet AAA without changing the default design.

**Related:** 1.4.3, 1.4.11, 1.4.8.

### 1.4.7 Low or No Background Audio (Level AAA)

**Normative text (verbatim):**
> For prerecorded audio-only content that (1) contains primarily speech in the foreground, (2) is not an audio CAPTCHA or audio logo, and (3) is not vocalization intended to be primarily musical expression such as singing or rapping, at least one of the following is true:
>
> **No Background** — The audio does not contain background sounds.
>
> **Turn Off** — The background sounds can be turned off.
>
> **20 dB** — The background sounds are at least 20 decibels lower than the foreground speech content, with the exception of occasional sounds that last for only one or two seconds.
>
> NOTE: Per the definition of "decibel," background sound that meets this requirement will be approximately four times quieter than the foreground speech content.

**Intent (informative):** Hard-of-hearing listeners (and hearing-aid users) struggle to separate speech from background music or ambience. Keeping background at least 20 dB below speech, or allowing it to be switched off, keeps speech intelligible.

**How to test:**
1. Identify prerecorded audio-only content that is primarily speech (podcasts, audio guides, voice messages), excluding audio CAPTCHAs, audio logos and sung/rapped content.
2. Listen for background sounds. If present, check whether they can be turned off, or measure levels (audio editor/loudness meter): speech level minus background level ≥ 20 dB, ignoring occasional 1–2 second sounds.
Pass when one of the three conditions holds.

**Common failures:** None listed.

**Sufficient techniques:**
- G56 Mixing audio files so that non-speech sounds are at least 20 decibels lower than the speech audio content

**Implementation notes (HTML/CSS/ARIA):** Produce a "voice only" mix or provide a toggle between mixes; in production set the music bed at −20 dB (or lower) relative to dialogue.

**Related:** 1.2.1, 1.4.2.

### 1.4.8 Visual Presentation (Level AAA)

**Normative text (verbatim):**
> For the visual presentation of blocks of text, a mechanism is available to achieve the following:
>
> 1. Foreground and background colors can be selected by the user.
> 2. Width is no more than 80 characters or glyphs (40 if CJK).
> 3. Text is not justified (aligned to both the left and the right margins).
> 4. Line spacing (leading) is at least space-and-a-half within paragraphs, and paragraph spacing is at least 1.5 times larger than the line spacing.
> 5. Text can be resized without assistive technology up to 200 percent in a way that does not require the user to scroll horizontally to read a line of text on a full-screen window.
>
> NOTE 1: Content is not required to use these values. The requirement is that a mechanism is available for users to change these presentation aspects. The mechanism can be provided by the browser or other user agent. Content is not required to provide the mechanism.
>
> NOTE 2: Writing systems for some languages use different presentation aspects to improve readability and legibility. If a presentation aspect in this success criterion is not used in a writing system, content in that writing system does not need to use that presentation setting and can conform without it. Authors are encouraged to follow guidance for improving readability and legibility of text in their writing system.

**Intent (informative):** People with cognitive, language and learning disabilities (e.g. dyslexia) and some low-vision users read better with controllable colours, narrow measure, ragged-right alignment and generous spacing. The author need not ship these settings but must not block the browser/user from applying them (e.g. by using `!important` colours, fixed widths, or forced justification).

**How to test:**
1. Colours: apply a user style sheet or browser "override colours" setting; verify text and background change (no inline/`!important` colours or background images that block it).
2. Width: at a full-screen window with the user's chosen size, confirm text blocks can be narrowed to ≤ 80 characters (fluid layout or a width control).
3. Justification: `text-align: justify` is not applied, or a control removes it (F88).
4. Spacing: a mechanism (browser/user CSS or in-page control) can set line-height ≥ 1.5 and paragraph spacing ≥ 1.5 × line-height without breaking the layout.
5. Resize: at 200% text size, no horizontal scrolling is needed to read lines on a full-screen window.
Pass when all five aspects are achievable.

**Common failures:**
- F24 Failure of Success Criterion 1.4.3, 1.4.6 and 1.4.8 due to specifying foreground colors without specifying background colors or vice versa
- F88 Failure of Success Criterion 1.4.8 due to using text that is justified (aligned to both the left and the right margins)

**Sufficient techniques:**
- First Requirement: Techniques to ensure foreground and background colors can be selected by the user: C23 Specifying text and background colors of secondary content such as banners, features and navigation in CSS while not specifying text and background colors of the main content; C25 Specifying borders and layout in CSS to delineate areas of a web page while not specifying text and text-background colors; G156 Using a technology that has commonly-available user agents that can change the foreground and background of blocks of text; G148 Not specifying background color, not specifying text color, and not using technology features that change those defaults; G175 Providing a multi color selection tool on the page for foreground and background colors
- Second Requirement: Techniques to ensure width is no more than 80 characters or glyphs (40 if CJK): G204 Not interfering with the user agent's reflow of text as the viewing window is narrowed; C20 Using relative measurements to set column widths so that lines can average 80 characters or less when the browser is resized
- Third Requirement: Techniques to ensure text is not justified (aligned to both the left and the right margins): C19 Specifying alignment either to the left or right in CSS; G172 Providing a mechanism to remove full justification of text; G169 Aligning text on only one side
- Fourth Requirement: Techniques to ensure line spacing (leading) is at least space-and-a-half within paragraphs, and paragraph spacing is at least 1.5 times larger than the line spacing: G188 Providing a button on the page to increase line spaces and paragraph spaces; C21 Specifying line spacing in CSS
- Fifth Requirement: Techniques to ensure text can be resized without assistive technology up to 200 percent in a way that does not require the user to scroll horizontally to read a line of text on a full-screen window: G204 Not interfering with the user agent's reflow of text as the viewing window is narrowed, using C12 Using percent for font sizes; C13 Using named font sizes; C14 Using em units for font sizes; C24 Using percentage values in CSS for container sizes; SCR34 Calculating size and position in a way that scales with text size; and G146 Using liquid layout AND using measurements that are relative to other measurements in the content; G206 Providing options within the content to switch to a layout that does not require the user to scroll horizontally to read a line of text

**Implementation notes (HTML/CSS/ARIA):**
```css
.prose { max-width: 70ch; line-height: 1.5; text-align: left; }
.prose p + p { margin-top: 2.25em; } /* ≥ 1.5 × line-height (1.5em) */
```
Avoid `color: … !important` and text over background images in main content so user styles can override.

**Related:** 1.4.3/1.4.6, 1.4.4, 1.4.10, 1.4.12.

### 1.4.9 Images of Text (No Exception) (Level AAA)

**Normative text (verbatim):**
> Images of text are only used for pure decoration or where a particular presentation of text is essential to the information being conveyed.
>
> NOTE: Logotypes (text that is part of a logo or brand name) are considered essential.

**Intent (informative):** Removes the "customizable" exception from 1.4.5: at AAA, images of text appear only as decoration or when essential (logos, specimens, historical documents).

**How to test:** As for 1.4.5, but only the decoration and essential exceptions apply.

**Common failures:** None listed.

**Sufficient techniques:** C22 Using CSS to control visual presentation of text; C30 Using CSS to replace text with images of text and providing user interface controls to switch; G140 Separating information and structure from presentation to enable different presentations; PDF7 Performing OCR on a scanned PDF document to provide actual text

**Advisory techniques:** C12 Using percent for font sizes; C13 Using named font sizes; C14 Using em units for font sizes; C8 Using CSS letter-spacing to control spacing within a word; C6 Positioning content based on structural markup

**Implementation notes (HTML/CSS/ARIA):** Same as 1.4.5.

**Related:** 1.4.5, 1.1.1.

### 1.4.10 Reflow (Level AA)

**Normative text (verbatim):**
> Content can be presented without loss of information or functionality, and without requiring scrolling in two dimensions for:
>
> - Vertical scrolling content at a width equivalent to 320 CSS pixels;
> - Horizontal scrolling content at a height equivalent to 256 CSS pixels.
>
> Except for parts of the content which require two-dimensional layout for usage or meaning.
>
> NOTE 1: 320 CSS pixels is equivalent to a starting viewport width of 1280 CSS pixels wide at 400% zoom. For web content which is designed to scroll horizontally (e.g., with vertical text), 256 CSS pixels is equivalent to a starting viewport height of 1024 CSS pixels at 400% zoom.
>
> NOTE 2: Examples of content which requires two-dimensional layout are images required for understanding (such as maps and diagrams), video, games, presentations, data tables (not individual cells), and interfaces where it is necessary to keep toolbars in view while manipulating content. It is acceptable to provide two-dimensional scrolling for such parts of the content.

**Intent (informative):** Low-vision users who zoom to 400% should get a single-column, reflowed layout (like a phone) rather than having to scroll horizontally for every line. The 320 CSS px width is exactly 1280 px at 400%. Exceptions cover content that is inherently two-dimensional (maps, data tables, complex toolbars).

**How to test:**
1. Set the browser window to 1280 px wide and zoom to 400% (or use responsive mode at 320 px width with desktop zoom reset). For horizontally scrolling content, use 1024 px tall at 400% (256 px).
2. Scroll through every page and state (menus open, modals, expanded sections, forms with errors).
3. Fail if content requires horizontal *and* vertical scrolling to read a block of text, if content is clipped or disappears (F102), or if functionality is lost (e.g. a menu that cannot be opened).
4. Allowed exceptions: data tables, maps, diagrams, video, games, toolbars that must stay in view, and individual pre-formatted strings — but surrounding content must still reflow, and a horizontally scrolling table must be reachable and scrollable (keyboard too).
5. Check sticky headers/footers that consume most of the 256 px/320 px viewport.
Pass when all non-excepted content reflows into one dimension without loss.

**Common failures:**
- F102 Failure of Success Criterion 1.4.10 due to content disappearing and not being available when content has reflowed
- Typical examples: a fixed 1024 px layout that needs sideways scrolling at 400%; a mobile breakpoint that hides the "Apply" button; long unbroken URLs that force horizontal overflow.

**Sufficient techniques:**
- C32 Using media queries and grid CSS to reflow columns
- C31 Using CSS Flexbox to reflow content
- C33 Allowing for Reflow with Long URLs and Strings of Text
- C38 Using CSS width, max-width and flexbox to fit labels and inputs
- SCR34 Calculating size and position in a way that scales with text size
- G206 Providing options within the content to switch to a layout that does not require the user to scroll horizontally to read a line of text
- G224 Accounting for meaningful text indentation and Reflow
- G225 Section panels that scroll horizontally are designed to fit within a width of 320 CSS pixels on a vertically scrolling page
- Using PDF/UA when creating PDFs (Potential future technique)

**Advisory techniques:** C34 Using media queries to un-fixing sticky headers / footers; C37 Using CSS max-width and height to fit images; CSS, Reflowing simple data tables (Potential future technique); CSS, Fitting data cells within the width of the viewport (Potential future technique); Mechanism to allow mobile view at any time (Potential future technique); Alternate view supporting Reflow for otherwise excepted content (Potential future technique)

**Implementation notes (HTML/CSS/ARIA):**
```css
.layout { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr)); }
img, video { max-width: 100%; height: auto; }
.long-url { overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; } /* excepted data table, still reachable */
@media (max-width: 20rem), (max-height: 16rem) { .sticky-header { position: static; } }
```
The `.table-wrap` div should be keyboard focusable (`tabindex="0"` with a name) so keyboard users can scroll it (2.1.1).

**Related:** 1.4.4 Resize Text, 1.3.4 Orientation, 1.4.12, 2.4.11 Focus Not Obscured (sticky elements).

### 1.4.11 Non-text Contrast (Level AA)

**Normative text (verbatim):**
> The visual presentation of the following have a contrast ratio of at least 3:1 against adjacent color(s):
>
> **User Interface Components** — Visual information required to identify user interface components and states, except for inactive components or where the appearance of the component is determined by the user agent and not modified by the author;
>
> **Graphical Objects** — Parts of graphics required to understand the content, except when a particular presentation of graphics is essential to the information being conveyed.

**Intent (informative):** Low-vision users need to see where a text field is, whether a checkbox is checked, which tab is selected, where keyboard focus is, and what an icon or chart segment shows. Those visual cues need 3:1 against adjacent colours. Not every pixel of a component must contrast — only the information needed to *identify* it and its *state*. A button whose text already meets 1.4.3 does not also need a 3:1 border, because the text identifies it; but an input that is identified only by its border needs a 3:1 border.

**How to test:**
1. Inventory UI components: inputs, checkboxes, radios, switches, sliders, buttons (icon-only especially), tabs, links shown as icons, custom focus indicators.
2. For each, decide which visual information identifies the component (e.g. input border, checkbox box) and its states (checked, selected, focused, expanded, error). Measure those colours against adjacent colours (background, neighbouring fill) — threshold ≥ 3:1.
3. Exempt: disabled components; components rendered by the browser without author styling (default focus ring, default checkbox).
4. Focus indicators: the author-styled focus indicator must have ≥ 3:1 against adjacent colours (overlaps with 2.4.7 and F78).
5. Graphical objects: icons, chart lines/segments, map boundaries — the parts needed to understand them must be ≥ 3:1 against adjacent colours (adjacent chart segments against each other, or separated by a contrasting border). Exempt: essential presentations (brand colours in a logo, a photograph, a colour swatch).
Pass when identifying/state cues and meaningful graphic parts meet 3:1.

**Common failures:**
- F78 Failure of Success Criterion 1.4.11, 2.4.7 and 2.4.13 due to styling element outlines and borders in a way that removes or renders non-visible the visual focus indicator
- Typical examples: input borders in `#ddd` on white (1.3:1) with no other identification; a custom checkbox whose checked state is a pale fill; a light-blue focus ring on a white background; a pie chart with adjacent pastel slices and no borders.

**Sufficient techniques:**
- Situation A: Color is used to identify user interface components — Identifying user interface components, using: G174 Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast
- Situation B: Color is used to identify a user interface component's focus state — Identifying a user interface component's focus state, using: G195 Using an author-supplied, visible focus indicator; C40 Creating a two-color focus indicator to ensure sufficient contrast with all components
- Situation C: Color is required to understand graphical content — Making graphical content understandable, using: G207 Ensuring that a contrast ratio of 3:1 is provided for icons; G209 Provide sufficient contrast at the boundaries between adjoining colors

**Implementation notes (HTML/CSS/ARIA):**
```css
input, select, textarea { border: 1px solid #767676; }        /* 4.5:1 on white — identifies the field */
:focus-visible { outline: 2px solid #1a1a1a; outline-offset: 2px; } /* ≥3:1 vs background */
.btn-icon svg { fill: #333; }                                   /* icon ≥3:1 */
.chart .slice { stroke: #fff; stroke-width: 2; }                /* boundaries between adjacent colours */
```

**Related:** 1.4.3 (text contrast), 1.4.1 (colour alone), 2.4.7 Focus Visible, 2.4.13 Focus Appearance, 4.1.2 (states must also be programmatic).

### 1.4.12 Text Spacing (Level AA)

**Normative text (verbatim):**
> In content implemented using markup languages that support the following text style properties, no loss of content or functionality occurs by setting all of the following and by changing no other style property:
>
> - Line height (line spacing) to at least 1.5 times the font size;
> - Spacing following paragraphs to at least 2 times the font size;
> - Letter spacing (tracking) to at least 0.12 times the font size;
> - Word spacing to at least 0.16 times the font size.
>
> Exception: Human languages and scripts that do not make use of one or more of these text style properties in written text can conform using only the properties that exist for that combination of language and script.
>
> NOTE 1: Content is not required to use these text spacing values. The requirement is to ensure that when a user overrides the authored text spacing, content or functionality is not lost.
>
> NOTE 2: Writing systems for some languages use different text spacing settings, such as paragraph start indent. Authors are encouraged to follow locally available guidance for improving readability and legibility of text in their writing system.

**Intent (informative):** People with dyslexia and some low-vision users apply custom spacing via browser extensions or user style sheets. Authors are not required to use these values but must not break when they are applied — fixed-height boxes, `overflow: hidden`, absolutely sized buttons and tight tooltips are the usual culprits.

**How to test:**
1. Apply a user style sheet or bookmarklet that sets, with `!important`: `line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important;` and `p { margin-bottom: 2em !important; }` (the standard "text spacing bookmarklet").
2. Review every page/state: text must not be clipped, overlapped, truncated with ellipsis that hides content, or pushed out of its container; buttons/links must remain fully visible and operable (F104).
3. Exempt: languages/scripts where a property does not apply (e.g. letter-spacing in some CJK contexts), and content outside the markup's control (images of text, canvas, video).
Pass when applying all four values loses no content or functionality.

**Common failures:**
- F104 Failure of Success Criterion 1.4.12 due to clipped or overlapped content when text spacing is adjusted
- Typical examples: card titles in a fixed-height box with `overflow: hidden`; a navigation bar whose last items wrap behind a fixed-width logo; a button with fixed `height: 40px` whose label overflows.

**Sufficient techniques:**
- C36 Allowing for text spacing override
- C35 Allowing for text spacing without wrapping

**Advisory techniques:** C8 Using CSS letter-spacing to control spacing within a word; C21 Specifying line spacing in CSS; C28 Specifying the size of text containers using em units

**Implementation notes (HTML/CSS/ARIA):**
```css
.card { min-height: 10rem; height: auto; overflow: visible; }
.btn { padding: .5em 1em; min-height: 2.75rem; height: auto; white-space: normal; }
```
Test bookmarklet CSS:
```css
* { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; }
p { margin-bottom: 2em !important; }
```

**Related:** 1.4.4, 1.4.8, 1.4.10.

### 1.4.13 Content on Hover or Focus (Level AA)

**Normative text (verbatim):**
> Where receiving and then removing pointer hover or keyboard focus triggers additional content to become visible and then hidden, the following are true:
>
> **Dismissible** — A mechanism is available to dismiss the additional content without moving pointer hover or keyboard focus, unless the additional content communicates an input error or does not obscure or replace other content;
>
> **Hoverable** — If pointer hover can trigger the additional content, then the pointer can be moved over the additional content without the additional content disappearing;
>
> **Persistent** — The additional content remains visible until the hover or focus trigger is removed, the user dismisses it, or its information is no longer valid.
>
> Exception: The visual presentation of the additional content is controlled by the user agent and is not modified by the author.
>
> NOTE 1: Examples of additional content controlled by the user agent include browser tooltips created through use of the HTML title attribute [HTML].
>
> NOTE 2: Custom tooltips, sub-menus, and other nonmodal popups that display on hover and focus are examples of additional content covered by this criterion.
>
> NOTE 3: This criterion applies to content that appears in addition to the triggering component itself. Since hidden components that are made visible on keyboard focus (such as links used to skip to another part of a page) do not present additional content they are not covered by this criterion.

**Intent (informative):** Screen magnifier users see only a small part of the screen; a tooltip or mega-menu that pops up may cover what they are reading, vanish when they move the pointer toward it, or disappear before they can read it. The three conditions let users dismiss popups (typically with Escape), move the pointer into them, and read them at their own pace.

**How to test:**
1. Identify content that appears on hover or focus: custom tooltips, hover cards, dropdown/mega menus that open on hover, previews, info icons.
2. Dismissible: with the popup open, press Escape (or another documented method that does not move hover/focus) — it must close. Exempt if it conveys an input error or does not obscure/replace other content.
3. Hoverable: move the pointer from the trigger into the popup; it must not disappear in transit or while over it (F95).
4. Persistent: the popup stays until hover/focus leaves, the user dismisses it, or the information is no longer valid; timed auto-close fails.
5. Native `title` tooltips are exempt (user-agent controlled), though they are poor practice for important information.
Pass when all applicable popups meet the three conditions.

**Common failures:**
- F95 Failure of Success Criterion 1.4.13 due to content shown on hover not being hoverable
- Failure to make content dismissible without moving pointer hover or keyboard focus (Potential future technique)
- Failure to meet by content on hover or focus not remaining visible until dismissed or invalid (Potential future technique)
- Typical examples: a custom tooltip separated from its trigger by a gap, so it closes when the pointer crosses the gap; a hover menu with no Escape handling that covers page content; a "help" popover that auto-hides after 3 seconds.

**Sufficient techniques:**
- SCR39 Making content on focus or hover hoverable, dismissible, and persistent
- ARIA: Using role="tooltip" (Potential future technique)
- CSS: Using hover and focus pseudo classes (Potential future technique)

**Implementation notes (HTML/CSS/ARIA):**
```html
<button type="button" aria-describedby="tip1" class="has-tip">Rate</button>
<div id="tip1" role="tooltip" hidden>Annual percentage rate, including fees.</div>
```
```js
// Show on mouseenter/focus; keep open while pointer is over trigger OR tooltip; close on Escape
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideAllTooltips(); });
```
```css
.has-tip:hover + [role=tooltip], .has-tip:focus-visible + [role=tooltip], [role=tooltip]:hover { display: block; }
/* No gap between trigger and tooltip, or bridge it with padding */
```

**Related:** 2.1.1 Keyboard, 2.4.7 Focus Visible, 3.2.1 On Focus, 4.1.3 Status Messages, 2.2.2 (timed content).

---

## Quick cross-reference: Perceivable criteria by level

- **Level A:** 1.1.1, 1.2.1, 1.2.2, 1.2.3, 1.3.1, 1.3.2, 1.3.3, 1.4.1, 1.4.2
- **Level AA:** 1.2.4, 1.2.5, 1.3.4, 1.3.5, 1.4.3, 1.4.4, 1.4.5, 1.4.10, 1.4.11, 1.4.12, 1.4.13
- **Level AAA:** 1.2.6, 1.2.7, 1.2.8, 1.2.9, 1.3.6, 1.4.6, 1.4.7, 1.4.8, 1.4.9

Non-interference criterion in this principle (applies to all page content regardless of conformance scope): **1.4.2 Audio Control**.
