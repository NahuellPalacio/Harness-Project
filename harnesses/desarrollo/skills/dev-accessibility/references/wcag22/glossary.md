# WCAG 2.2 Glossary (Section 6) — complete, verbatim

Source: Web Content Accessibility Guidelines (WCAG) 2.2, W3C Recommendation 12 December 2024, https://www.w3.org/TR/WCAG22/#glossary. The definitions below are **normative**: when a success criterion uses one of these terms, the term carries exactly this meaning. Terms marked **(New in 2.2)** were added to support the new success criteria. The appendix at the end is informative.

**Index:** abbreviation · accessibility supported · alternative for time-based media · ambiguous to users in general · ASCII art · assistive technology · audio · audio description · audio-only · blinking · blocks of text · CAPTCHA · captions · changes of context · cognitive function test · conformance · conforming alternate version · content (web content) · context-sensitive help · contrast ratio · correct reading sequence · CSS pixel · down-event · dragging movement · emergency · essential · extended audio description · flash · focus indicator · functionality · general flash and red flash thresholds · human language · idiom · image of text · informative · input error · jargon · keyboard interface · keyboard shortcut · label · large scale (text) · legal commitments · link purpose · live · lower secondary education level · mechanism · media alternative for text · motion animation · minimum bounding box · name · navigated sequentially · non-text content · normative · on a full-screen window · paused · perimeter · pointer input · prerecorded · presentation · primary education level · process · programmatically determined · programmatically determined link context · programmatically set · pure decoration · real-time event · region · relationships · relative luminance · relied upon · role · same functionality · same relative order · satisfies a success criterion · section · set of web pages · sign language · sign language interpretation · single pointer · specific sensory experience · state · status message · structure · style property · supplemental content · synchronized media · target · technology (web content) · text · text alternative · up-event · used in an unusual or restricted way · user agent · user-controllable · user interface component · user inactivity · video · video-only · viewport · visually customized · web page

---

### abbreviation

shortened form of a word, phrase, or name where the abbreviation has not become part of the language

NOTE 1: This includes initialisms and acronyms where:

- initialisms are shortened forms of a name or phrase made from the initial letters of words or syllables contained in that name or phrase
  - NOTE 2: Not defined in all languages.
  - EXAMPLE 1: SNCF is a French initialism that contains the initial letters of the Société Nationale des Chemins de Fer, the French national railroad.
  - EXAMPLE 2: ESP is an initialism for extrasensory perception.
- acronyms are abbreviated forms made from the initial letters or parts of other words (in a name or phrase) which may be pronounced as a word
  - EXAMPLE 3: NOAA is an acronym made from the initial letters of the National Oceanic and Atmospheric Administration in the United States.

NOTE 3: Some companies have adopted what used to be an initialism as their company name. In these cases, the new name of the company is the letters (for example, Ecma) and the word is no longer considered an abbreviation.

### accessibility supported

supported by users' assistive technologies as well as the accessibility features in browsers and other user agents

To qualify as an accessibility-supported use of a web content technology (or feature of a technology), both 1 and 2 must be satisfied for a web content technology (or feature):

1. The way that the web content technology is used must be supported by users' assistive technology (AT). This means that the way that the technology is used has been tested for interoperability with users' assistive technology in the human language(s) of the content,

   AND

2. The web content technology must have accessibility-supported user agents that are available to users. This means that at least one of the following four statements is true:
   1. The technology is supported natively in widely-distributed user agents that are also accessibility supported (such as HTML and CSS);
      OR
   2. The technology is supported in a widely-distributed plug-in that is also accessibility supported;
      OR
   3. The content is available in a closed environment, such as a university or corporate network, where the user agent required by the technology and used by the organization is also accessibility supported;
      OR
   4. The user agent(s) that support the technology are accessibility supported and are available for download or purchase in a way that:
      - does not cost a person with a disability any more than a person without a disability and
      - is as easy to find and obtain for a person with a disability as it is for a person without disabilities.

NOTE 1: The Accessibility Guidelines Working Group and the W3C do not specify which or how much support by assistive technologies there must be for a particular use of a web technology in order for it to be classified as accessibility supported. (See Level of Assistive Technology Support Needed for "Accessibility Support".)

NOTE 2: Web technologies can be used in ways that are not accessibility supported as long as they are not relied upon and the page as a whole meets the conformance requirements, including Conformance Requirement 4 and Conformance Requirement 5.

NOTE 3: When a web technology is used in a way that is "accessibility supported," it does not imply that the entire technology or all uses of the technology are supported. Most technologies, including HTML, lack support for at least one feature or use. Pages conform to WCAG only if the uses of the technology that are accessibility supported can be relied upon to meet WCAG requirements.

NOTE 4: When citing web content technologies that have multiple versions, the version(s) supported should be specified.

NOTE 5: One way for authors to locate uses of a technology that are accessibility supported would be to consult compilations of uses that are documented to be accessibility supported. (See Understanding Accessibility-Supported Web Technology Uses.) Authors, companies, technology vendors, or others may document accessibility-supported ways of using web content technologies. However, all ways of using technologies in the documentation would need to meet the definition of accessibility-supported Web content technologies above.

### alternative for time-based media

document including correctly sequenced text descriptions of time-based visual and auditory information and providing a means for achieving the outcomes of any time-based interaction

NOTE: A screenplay used to create the synchronized media content would meet this definition only if it was corrected to accurately represent the final synchronized media after editing.

### ambiguous to users in general

the purpose cannot be determined from the link and all information of the web page presented to the user simultaneously with the link (i.e., readers without disabilities would not know what a link would do until they activated it)

EXAMPLE: The word guava in the following sentence "One of the notable exports is guava" is a link. The link could lead to a definition of guava, a chart listing the quantity of guava exported or a photograph of people harvesting guava. Until the link is activated, all readers are unsure and the person with a disability is not at any disadvantage.

### ASCII art

picture created by a spatial arrangement of characters or glyphs (typically from the 95 printable characters defined by ASCII)

### assistive technology (as used in this document)

hardware and/or software that acts as a user agent, or along with a mainstream user agent, to provide functionality to meet the requirements of users with disabilities that go beyond those offered by mainstream user agents

NOTE 1: Functionality provided by assistive technology includes alternative presentations (e.g., as synthesized speech or magnified content), alternative input methods (e.g., voice), additional navigation or orientation mechanisms, and content transformations (e.g., to make tables more accessible).

NOTE 2: Assistive technologies often communicate data and messages with mainstream user agents by using and monitoring APIs.

NOTE 3: The distinction between mainstream user agents and assistive technologies is not absolute. Many mainstream user agents provide some features to assist individuals with disabilities. The basic difference is that mainstream user agents target broad and diverse audiences that usually include people with and without disabilities. Assistive technologies target narrowly defined populations of users with specific disabilities. The assistance provided by an assistive technology is more specific and appropriate to the needs of its target users. The mainstream user agent may provide important functionality to assistive technologies like retrieving web content from program objects or parsing markup into identifiable bundles.

EXAMPLE: Assistive technologies that are important in the context of this document include the following:

- screen magnifiers, and other visual reading assistants, which are used by people with visual, perceptual and physical print disabilities to change text font, size, spacing, color, synchronization with speech, etc. in order to improve the visual readability of rendered text and images;
- screen readers, which are used by people who are blind to read textual information through synthesized speech or braille;
- text-to-speech software, which is used by some people with cognitive, language, and learning disabilities to convert text into synthetic speech;
- speech recognition software, which may be used by people who have some physical disabilities;
- alternative keyboards, which are used by people with certain physical disabilities to simulate the keyboard (including alternate keyboards that use head pointers, single switches, sip/puff and other special input devices.);
- alternative pointing devices, which are used by people with certain physical disabilities to simulate mouse pointing and button activations.

### audio

the technology of sound reproduction

NOTE: Audio can be created synthetically (including speech synthesis), recorded from real world sounds, or both.

### audio description

narration added to the soundtrack to describe important visual details that cannot be understood from the main soundtrack alone

NOTE 1: Audio description of video provides information about actions, characters, scene changes, on-screen text, and other visual content.

NOTE 2: In standard audio description, narration is added during existing pauses in dialogue. (See also extended audio description.)

NOTE 3: Where all of the video information is already provided in existing audio, no additional audio description is necessary.

NOTE 4: Also called "video description" and "descriptive narration."

### audio-only

a time-based presentation that contains only audio (no video and no interaction)

### blinking

switch back and forth between two visual states in a way that is meant to draw attention

NOTE: See also flash. It is possible for something to be large enough and blink brightly enough at the right frequency to be also classified as a flash.

### blocks of text

more than one sentence of text

### CAPTCHA

initialism for "Completely Automated Public Turing test to tell Computers and Humans Apart"

NOTE 1: CAPTCHA tests often involve asking the user to type in text that is displayed in an obscured image or audio file.

NOTE 2: A Turing test is any system of tests designed to differentiate a human from a computer. It is named after famed computer scientist Alan Turing. The term was coined by researchers at Carnegie Mellon University.

### captions

synchronized visual and/or text alternative for both speech and non-speech audio information needed to understand the media content

NOTE 1: Captions are similar to dialogue-only subtitles except captions convey not only the content of spoken dialogue, but also equivalents for non-dialogue audio information needed to understand the program content, including sound effects, music, laughter, speaker identification and location.

NOTE 2: Closed Captions are equivalents that can be turned on and off with some players.

NOTE 3: Open Captions are any captions that cannot be turned off. For example, if the captions are visual equivalent images of text embedded in video.

NOTE 4: Captions should not obscure or obstruct relevant information in the video.

NOTE 5: In some countries, captions are called subtitles.

NOTE 6: Audio descriptions can be, but do not need to be, captioned since they are descriptions of information that is already presented visually.

### changes of context

major changes that, if made without user awareness, can disorient users who are not able to view the entire page simultaneously

Changes in context include changes of:

- user agent;
- viewport;
- focus;
- content that changes the meaning of the web page

NOTE: A change of content is not always a change of context. Changes in content, such as an expanding outline, dynamic menu, or a tab control do not necessarily change the context, unless they also change one of the above (e.g., focus).

EXAMPLE: Opening a new window, moving focus to a different component, going to a new page (including anything that would look to a user as if they had moved to a new page) or significantly re-arranging the content of a page are examples of changes of context.

### cognitive function test **(New in 2.2)**

A task that requires the user to remember, manipulate, or transcribe information. Examples include, but are not limited to:

- memorization, such as remembering a username, password, set of characters, images, or patterns. The common identifiers name, e-mail, and phone number are not considered cognitive function tests as they are personal to the user and consistent across websites;
- transcription, such as typing in characters;
- use of correct spelling;
- performance of calculations;
- solving of puzzles.

### conformance

satisfying all the requirements of a given standard, guideline or specification

### conforming alternate version

version that

1. conforms at the designated level, and
2. provides all of the same information and functionality in the same human language, and
3. is as up to date as the non-conforming content, and
4. for which at least one of the following is true:
   1. the conforming version can be reached from the non-conforming page via an accessibility-supported mechanism, or
   2. the non-conforming version can only be reached from the conforming version, or
   3. the non-conforming version can only be reached from a conforming page that also provides a mechanism to reach the conforming version

NOTE 1: In this definition, "can only be reached" means that there is some mechanism, such as a conditional redirect, that prevents a user from "reaching" (loading) the non-conforming page unless the user had just come from the conforming version.

NOTE 2: The alternate version does not need to be matched page for page with the original (e.g., the conforming alternate version may consist of multiple pages).

NOTE 3: If multiple language versions are available, then conforming alternate versions are required for each language offered.

NOTE 4: Alternate versions may be provided to accommodate different technology environments or user groups. Each version should be as conformant as possible. One version would need to be fully conformant in order to meet conformance requirement 1.

NOTE 5: The conforming alternative version does not need to reside within the scope of conformance, or even on the same website, as long as it is as freely available as the non-conforming version.

NOTE 6: Alternate versions should not be confused with supplementary content, which support the original page and enhance comprehension.

NOTE 7: Setting user preferences within the content to produce a conforming version is an acceptable mechanism for reaching another version as long as the method used to set the preferences is accessibility supported.

See Understanding Conforming Alternate Versions

### content (web content)

information and sensory experience to be communicated to the user by means of a user agent, including code or markup that defines the content's structure, presentation, and interactions

### context-sensitive help

help text that provides information related to the function currently being performed

NOTE: Clear labels can act as context-sensitive help.

### contrast ratio

(L1 + 0.05) / (L2 + 0.05), where

- L1 is the relative luminance of the lighter of the colors, and
- L2 is the relative luminance of the darker of the colors.

NOTE 1: Contrast ratios can range from 1 to 21 (commonly written 1:1 to 21:1).

NOTE 2: Because authors do not have control over user settings as to how text is rendered (for example font smoothing or anti-aliasing), the contrast ratio for text can be evaluated with anti-aliasing turned off.

NOTE 3: For the purpose of Success Criteria 1.4.3 and 1.4.6, contrast is measured with respect to the specified background over which the text is rendered in normal usage. If no background color is specified, then white is assumed.

NOTE 4: Background color is the specified color of content over which the text is to be rendered in normal usage. It is a failure if no background color is specified when the text color is specified, because the user's default background color is unknown and cannot be evaluated for sufficient contrast. For the same reason, it is a failure if no text color is specified when a background color is specified.

NOTE 5: When there is a border around the letter, the border can add contrast and would be used in calculating the contrast between the letter and its background. A narrow border around the letter would be used as the letter. A wide border around the letter that fills in the inner details of the letters acts as a halo and would be considered background.

NOTE 6: WCAG conformance should be evaluated for color pairs specified in the content that an author would expect to appear adjacent in typical presentation. Authors need not consider unusual presentations, such as color changes made by the user agent, except where caused by authors' code.

### correct reading sequence

any sequence where words and paragraphs are presented in an order that does not change the meaning of the content

### CSS pixel

visual angle of about 0.0213 degrees

A CSS pixel is the canonical unit of measure for all lengths and measurements in CSS. This unit is density-independent, and distinct from actual hardware pixels present in a display. User agents and operating systems should ensure that a CSS pixel is set as closely as possible to the CSS Values and Units Module Level 3 reference pixel [css3-values], which takes into account the physical dimensions of the display and the assumed viewing distance (factors that cannot be determined by content authors).

### down-event

platform event that occurs when the trigger stimulus of a pointer is depressed

The down-event may have different names on different platforms, such as "touchstart" or "mousedown".

### dragging movement **(New in 2.2)**

an operation where the pointer engages with an element on the down-event and the element (or a representation of its position) follows the pointer until an up-event

NOTE: Examples of draggable elements include list items, text elements, and images.

### emergency

a sudden, unexpected situation or occurrence that requires immediate action to preserve health, safety, or property

### essential

if removed, would fundamentally change the information or functionality of the content, and information and functionality cannot be achieved in another way that would conform

### extended audio description

audio description that is added to an audiovisual presentation by pausing the video so that there is time to add additional description

NOTE: This technique is only used when the sense of the video would be lost without the additional audio description and the pauses between dialogue/narration are too short.

### flash

a pair of opposing changes in relative luminance that can cause seizures in some people if it is large enough and in the right frequency range

NOTE 1: See general flash and red flash thresholds for information about types of flash that are not allowed.

NOTE 2: See also blinking.

### focus indicator **(New in 2.2)**

pixels that are changed to visually indicate when a user interface component is in a focused state

### functionality

processes and outcomes achievable through user action

### general flash and red flash thresholds

a flash or rapidly changing image sequence is below the threshold (i.e., content passes) if any of the following are true:

1. there are no more than three general flashes and / or no more than three red flashes within any one-second period; or
2. the combined area of flashes occurring concurrently occupies no more than a total of .006 steradians within any 10 degree visual field on the screen (25% of any 10 degree visual field on the screen) at typical viewing distance

where:

- A general flash is defined as a pair of opposing changes in relative luminance of 10% or more of the maximum relative luminance (1.0) where the relative luminance of the darker image is below 0.80; and where "a pair of opposing changes" is an increase followed by a decrease, or a decrease followed by an increase, and
- A red flash is defined as any pair of opposing transitions involving a saturated red

Exception: Flashing that is a fine, balanced, pattern such as white noise or an alternating checkerboard pattern with "squares" smaller than 0.1 degree (of visual field at typical viewing distance) on a side does not violate the thresholds.

NOTE 1: For general software or web content, using a 341 x 256 pixel rectangle anywhere on the displayed screen area when the content is viewed at 1024 x 768 pixels will provide a good estimate of a 10 degree visual field for standard screen sizes and viewing distances (e.g., 15-17 inch screen at 22-26 inches). This resolution of 75 - 85 ppi is known to be lower, and thus more conservative than the nominal CSS pixel resolution of 96 ppi in CSS specifications. Higher resolutions displays showing the same rendering of the content yield smaller and safer images so it is lower resolutions that are used to define the thresholds.

NOTE 2: A transition is the change in relative luminance (or relative luminance/color for red flashing) between adjacent peaks and valleys in a plot of relative luminance (or relative luminance/color for red flashing) measurement against time. A flash consists of two opposing transitions.

NOTE 3: The new working definition in the field for "pair of opposing transitions involving a saturated red" (from WCAG 2.2) is a pair of opposing transitions where, one transition is either to or from a state with a value R/(R + G + B) that is greater than or equal to 0.8, and the difference between states is more than 0.2 (unitless) in the CIE 1976 UCS chromaticity diagram. [ISO_9241-391]

NOTE 4: Tools are available that will carry out analysis from video screen capture. However, no tool is necessary to evaluate for this condition if flashing is less than or equal to 3 flashes in any one second. Content automatically passes (see #1 and #2 above).

### human language

language that is spoken, written or signed (through visual or tactile means) to communicate with humans

NOTE: See also sign language.

### idiom

phrase whose meaning cannot be deduced from the meaning of the individual words and the specific words cannot be changed without losing the meaning

NOTE: Idioms cannot be translated directly, word for word, without losing their (cultural or language-dependent) meaning.

EXAMPLE 1: In English, "spilling the beans" means "revealing a secret." However, "knocking over the beans" or "spilling the vegetables" does not mean the same thing.

EXAMPLE 2: In Japanese, the phrase "さじを投げる" literally translates into "he throws a spoon," but it means that there is nothing he can do and finally he gives up.

EXAMPLE 3: In Dutch, "Hij ging met de kippen op stok" literally translates into "He went to roost with the chickens," but it means that he went to bed early.

### image of text

text that has been rendered in a non-text form (e.g., an image) in order to achieve a particular visual effect

NOTE: This does not include text that is part of a picture that contains significant other visual content.

EXAMPLE: A person's name on a nametag in a photograph.

### informative

for information purposes and not required for conformance

NOTE: Content required for conformance is referred to as "normative."

### input error

information provided by the user that is not accepted

NOTE: This includes:

1. Information that is required by the web page but omitted by the user
2. Information that is provided by the user but that falls outside the required data format or values

### jargon

words used in a particular way by people in a particular field

EXAMPLE: The word StickyKeys is jargon from the field of assistive technology/accessibility.

### keyboard interface

interface used by software to obtain keystroke input

NOTE 1: A keyboard interface allows users to provide keystroke input to programs even if the native technology does not contain a keyboard.

EXAMPLE: A touchscreen PDA has a keyboard interface built into its operating system as well as a connector for external keyboards. Applications on the PDA can use the interface to obtain keyboard input either from an external keyboard or from other applications that provide simulated keyboard output, such as handwriting interpreters or speech-to-text applications with "keyboard emulation" functionality.

NOTE 2: Operation of the application (or parts of the application) through a keyboard-operated mouse emulator, such as MouseKeys, does not qualify as operation through a keyboard interface because operation of the program is through its pointing device interface, not through its keyboard interface.

### keyboard shortcut

alternative means of triggering an action by the pressing of one or more keys

### label

text or other component with a text alternative that is presented to a user to identify a component within web content

NOTE 1: A label is presented to all users whereas the name may be hidden and only exposed by assistive technology. In many (but not all) cases the name and the label are the same.

NOTE 2: The term label is not limited to the label element in HTML.

### large scale (text)

with at least 18 point or 14 point bold or font size that would yield equivalent size for Chinese, Japanese and Korean (CJK) fonts

NOTE 1: Fonts with extraordinarily thin strokes or unusual features and characteristics that reduce the familiarity of their letter forms are harder to read, especially at lower contrast levels.

NOTE 2: Font size is the size when the content is delivered. It does not include resizing that may be done by a user.

NOTE 3: The actual size of the character that a user sees is dependent both on the author-defined size and the user's display or user agent settings. For many mainstream body text fonts, 14 and 18 point is roughly equivalent to 1.2 and 1.5 em or to 120% or 150% of the default size for body text (assuming that the body font is 100%), but authors would need to check this for the particular fonts in use. When fonts are defined in relative units, the actual point size is calculated by the user agent for display. The point size should be obtained from the user agent, or calculated based on font metrics as the user agent does, when evaluating this success criterion. Users who have low vision would be responsible for choosing appropriate settings.

NOTE 4: When using text without specifying the font size, the smallest font size used on major browsers for unspecified text would be a reasonable size to assume for the font. If a level 1 heading is rendered in 14pt bold or higher on major browsers, then it would be reasonable to assume it is large text. Relative scaling can be calculated from the default sizes in a similar fashion.

NOTE 5: The 18 and 14 point sizes for roman texts are taken from the minimum size for large print (14pt) and the larger standard font size (18pt). For other fonts such as CJK languages, the "equivalent" sizes would be the minimum large print size used for those languages and the next larger standard large print size.

### legal commitments

transactions where the person incurs a legally binding obligation or benefit

EXAMPLE: A marriage license, a stock trade (financial and legal), a will, a loan, adoption, signing up for the army, a contract of any type, etc.

### link purpose

nature of the result obtained by activating a hyperlink

### live

information captured from a real-world event and transmitted to the receiver with no more than a broadcast delay

NOTE 1: A broadcast delay is a short (usually automated) delay, for example used in order to give the broadcaster time to cue or censor the audio (or video) feed, but not sufficient to allow significant editing.

NOTE 2: If information is completely computer generated, it is not live.

### lower secondary education level

the two or three year period of education that begins after completion of six years of school and ends nine years after the beginning of primary education

NOTE: This definition is based on the International Standard Classification of Education [UNESCO].

### mechanism

process or technique for achieving a result

NOTE 1: The mechanism may be explicitly provided in the content, or may be relied upon to be provided by either the platform or by user agents, including assistive technologies.

NOTE 2: The mechanism needs to meet all success criteria for the conformance level claimed.

### media alternative for text

media that presents no more information than is already presented in text (directly or via text alternatives)

NOTE: A media alternative for text is provided for those who benefit from alternate representations of text. Media alternatives for text may be audio-only, video-only (including sign-language video), or audio-video.

### motion animation

addition of steps between conditions to create the illusion of movement or to give a sense of a smooth transition

EXAMPLE: For example, an element which moves into place or changes size while appearing is considered to be animated. An element which appears instantly without transitioning is not using animation. Motion animation does not include changes of color, blurring, or opacity which do not change the perceived size, shape, or position of the element.

### minimum bounding box **(New in 2.2)**

the smallest enclosing rectangle aligned to the horizontal axis within which all the points of a shape lie. For components which wrap onto multiple lines as part of a sentence or block of text (such as hypertext links), the bounding box is based on how the component would appear on a single line.

### name

text by which software can identify a component within web content to the user

NOTE 1: The name may be hidden and only exposed by assistive technology, whereas a label is presented to all users. In many (but not all) cases, the label and the name are the same.

NOTE 2: This is unrelated to the name attribute in HTML.

### navigated sequentially

navigated in the order defined for advancing focus (from one element to the next) using a keyboard interface

### non-text content

any content that is not a sequence of characters that can be programmatically determined or where the sequence is not expressing something in human language

NOTE: This includes ASCII art (which is a pattern of characters), emoticons, leetspeak (which uses character substitution), and images representing text

### normative

required for conformance

NOTE 1: One may conform in a variety of well-defined ways to this document.

NOTE 2: Content identified as "informative" or "non-normative" is never required for conformance.

### on a full-screen window

on the most common sized desktop/laptop display with the viewport maximized

NOTE: Since people generally keep their computers for several years, it is best not to rely on the latest desktop/laptop display resolutions but to consider the common desktop/laptop display resolutions over the course of several years when making this evaluation.

### paused

stopped by user request and not resumed until requested by user

### perimeter **(New in 2.2)**

continuous line forming the boundary of a shape not including shared pixels, or the minimum bounding box, whichever is shortest.

EXAMPLE: The perimeter calculation for a 2 CSS pixel perimeter around a rectangle is 4h+4w, where h is the height and w is the width. For a 2 CSS pixel perimeter around a circle it is 4𝜋r.

### pointer input

input from a device that can target a specific coordinate (or set of coordinates) on a screen, such as a mouse, pen, or touch contact

NOTE: See the Pointer Events definition for "pointer" [pointerevents].

### prerecorded

information that is not live

### presentation

rendering of the content in a form to be perceived by users

### primary education level

six year time period that begins between the ages of five and seven, possibly without any previous education

NOTE: This definition is based on the International Standard Classification of Education [UNESCO].

### process

series of user actions where each action is required in order to complete an activity

EXAMPLE 1: Successful use of a series of web pages on a shopping site requires users to view alternative products, prices and offers, select products, submit an order, provide shipping information and provide payment information.

EXAMPLE 2: An account registration page requires successful completion of a Turing test before the registration form can be accessed.

### programmatically determined (programmatically determinable)

determined by software from author-supplied data provided in a way that different user agents, including assistive technologies, can extract and present this information to users in different modalities

EXAMPLE 1: Determined in a markup language from elements and attributes that are accessed directly by commonly available assistive technology.

EXAMPLE 2: Determined from technology-specific data structures in a non-markup language and exposed to assistive technology via an accessibility API that is supported by commonly available assistive technology.

### programmatically determined link context

additional information that can be programmatically determined from relationships with a link, combined with the link text, and presented to users in different modalities

EXAMPLE: In HTML, information that is programmatically determinable from a link in English includes text that is in the same paragraph, list item, or table cell as the link or in a table header cell that is associated with the table cell that contains the link.

NOTE: Since screen readers interpret punctuation, they can also provide the context from the current sentence, when the focus is on a link in that sentence.

### programmatically set

set by software using methods that are supported by user agents, including assistive technologies

### pure decoration

serving only an aesthetic purpose, providing no information, and having no functionality

NOTE: Text is only purely decorative if the words can be rearranged or substituted without changing their purpose.

EXAMPLE: The cover page of a dictionary has random words in very light text in the background.

### real-time event

event that a) occurs at the same time as the viewing and b) is not completely generated by the content

EXAMPLE 1: A Webcast of a live performance (occurs at the same time as the viewing and is not prerecorded).

EXAMPLE 2: An on-line auction with people bidding (occurs at the same time as the viewing).

EXAMPLE 3: Live humans interacting in a virtual world using avatars (is not completely generated by the content and occurs at the same time as the viewing).

### region

perceivable, programmatically determined section of content

NOTE: In HTML, any area designated with a landmark role would be a region.

### relationships

meaningful associations between distinct pieces of content

### relative luminance

the relative brightness of any point in a colorspace, normalized to 0 for darkest black and 1 for lightest white

NOTE 1: For the sRGB colorspace, the relative luminance of a color is defined as L = 0.2126 * R + 0.7152 * G + 0.0722 * B where R, G and B are defined as:

- if RsRGB <= 0.04045 then R = RsRGB/12.92 else R = ((RsRGB+0.055)/1.055) ^ 2.4
- if GsRGB <= 0.04045 then G = GsRGB/12.92 else G = ((GsRGB+0.055)/1.055) ^ 2.4
- if BsRGB <= 0.04045 then B = BsRGB/12.92 else B = ((BsRGB+0.055)/1.055) ^ 2.4

and RsRGB, GsRGB, and BsRGB are defined as:

- RsRGB = R8bit/255
- GsRGB = G8bit/255
- BsRGB = B8bit/255

The "^" character is the exponentiation operator. (Formula taken from [SRGB].)

NOTE 2: Before May 2021 the value of 0.04045 in the definition was different (0.03928). It was taken from an older version of the specification and has been updated. It has no practical effect on the calculations in the context of these guidelines.

NOTE 3: Almost all systems used today to view web content assume sRGB encoding. Unless it is known that another color space will be used to process and display the content, authors should evaluate using sRGB colorspace. If using other color spaces, see Understanding Success Criterion 1.4.3.

NOTE 4: If dithering occurs after delivery, then the source color value is used. For colors that are dithered at the source, the average values of the colors that are dithered should be used (average R, average G, and average B).

NOTE 5: Tools are available that automatically do the calculations when testing contrast and flash.

NOTE 6: A separate page giving the relative luminance definition using MathML to display the formulas is available.

### relied upon (technologies that are)

the content would not conform if that technology is turned off or is not supported

### role

text or number by which software can identify the function of a component within Web content

EXAMPLE: A number that indicates whether an image functions as a hyperlink, command button, or check box.

### same functionality

same result when used

EXAMPLE: A submit "search" button on one web page and a "find" button on another web page may both have a field to enter a term and list topics in the website related to the term submitted. In this case, they would have the same functionality but would not be labeled consistently.

### same relative order

same position relative to other items

NOTE: Items are considered to be in the same relative order even if other items are inserted or removed from the original order. For example, expanding navigation menus may insert an additional level of detail or a secondary navigation section may be inserted into the reading order.

### satisfies a success criterion

the success criterion does not evaluate to 'false' when applied to the page

### section

a self-contained portion of written content that deals with one or more related topics or thoughts

NOTE: A section may consist of one or more paragraphs and include graphics, tables, lists and sub-sections.

### set of web pages

collection of web pages that share a common purpose and that are created by the same author, group or organization

EXAMPLE: Examples include:

- a publication which is split across multiple web pages, where each page contains one chapter or other significant section of the work. The publication is logically a single contiguous unit, and contains navigation features that enable access to the full set of pages.
- an e-commerce website shows products in a set of web pages that all share the same navigation and identification. However, when progressing to the checkout process, the template changes; the navigation and other elements are removed, so the pages in that process are functionally and visually different. The checkout pages are not part of the set of product pages.
- a blog on a sub-domain (e.g. blog.example.com) which has a different navigation and is authored by a distinct set of people from the pages on the primary domain (example.com).

NOTE: Different language versions would be considered different sets of web pages.

### sign language

a language using combinations of movements of the hands and arms, facial expressions, or body positions to convey meaning

### sign language interpretation

translation of one language, generally a spoken language, into a sign language

NOTE: True sign languages are independent languages that are unrelated to the spoken language(s) of the same country or region.

### single pointer

an input modality that only targets a single point on the page/screen at a time – such as a mouse, single finger on a touch screen, or stylus.

NOTE: Single pointer interactions include clicks, double clicks, taps, dragging motions, and single-finger swipe gestures. In contrast, multipoint interactions involve the use of two or more pointers at the same time, such as two-finger interactions on a touchscreen, or the simultaneous use of a mouse and stylus.

### specific sensory experience

a sensory experience that is not purely decorative and does not primarily convey important information or perform a function

EXAMPLE: Examples include a performance of a flute solo, works of visual art etc.

### state

dynamic property expressing characteristics of a user interface component that may change in response to user action or automated processes

States do not affect the nature of the component, but represent data associated with the component or user interaction possibilities. Examples include focus, hover, select, press, check, visited/unvisited, and expand/collapse.

### status message

change in content that is not a change of context, and that provides information to the user on the success or results of an action, on the waiting state of an application, on the progress of a process, or on the existence of errors

### structure

1. The way the parts of a web page are organized in relation to each other; and
2. The way a collection of web pages is organized

### style property

property whose value determines the presentation (e.g. font, color, size, location, padding, volume, synthesized speech prosody) of content elements as they are rendered (e.g. onscreen, via loudspeaker, via braille display) by user agents

Style properties can have several origins:

- User agent default styles: The default style property values applied in the absence of any author or user styles. Some web content technologies specify a default rendering, others do not;
- Author styles: Style property values that are set by the author as part of the content (e.g. in-line styles, author style sheets);
- User styles: Style property values that are set by the user (e.g. via user agent interface settings, user style sheets)

### supplemental content

additional content that illustrates or clarifies the primary content

EXAMPLE 1: An audio version of a web page.

EXAMPLE 2: An illustration of a complex process.

EXAMPLE 3: A paragraph summarizing the major outcomes and recommendations made in a research study.

### synchronized media

audio or video synchronized with another format for presenting information and/or with time-based interactive components, unless the media is a media alternative for text that is clearly labeled as such

### target

region of the display that will accept a pointer action, such as the interactive area of a user interface component

NOTE: If two or more targets are overlapping, the overlapping area should not be included in the measurement of the target size, except when the overlapping targets perform the same action or open the same page.

### technology (web content)

mechanism for encoding instructions to be rendered, played or executed by user agents

NOTE 1: As used in these guidelines "web technology" and the word "technology" (when used alone) both refer to web content technologies.

NOTE 2: Web content technologies may include markup languages, data formats, or programming languages that authors may use alone or in combination to create end-user experiences that range from static web pages to synchronized media presentations to dynamic Web applications.

EXAMPLE: Some common examples of web content technologies include HTML, CSS, SVG, PNG, PDF, Flash, and JavaScript.

### text

sequence of characters that can be programmatically determined, where the sequence is expressing something in human language

### text alternative

Text that is programmatically associated with non-text content or referred to from text that is programmatically associated with non-text content. Programmatically associated text is text whose location can be programmatically determined from the non-text content.

EXAMPLE: An image of a chart is described in text in the paragraph after the chart. The short text alternative for the chart indicates that a description follows.

NOTE: Refer to Understanding Text Alternatives for more information.

### up-event

platform event that occurs when the trigger stimulus of a pointer is released

The up-event may have different names on different platforms, such as "touchend" or "mouseup".

### used in an unusual or restricted way

words used in such a way that requires users to know exactly which definition to apply in order to understand the content correctly

EXAMPLE: The term "gig" means something different if it occurs in a discussion of music concerts than it does in article about computer hard drive space, but the appropriate definition can be determined from context. By contrast, the word "text" is used in a very specific way in WCAG 2, so a definition is supplied in the glossary.

### user agent

any software that retrieves and presents web content for users

EXAMPLE: Web browsers, media players, plug-ins, and other programs — including assistive technologies — that help in retrieving, rendering, and interacting with web content.

### user-controllable

data that is intended to be accessed by users

NOTE: This does not refer to such things as Internet logs and search engine monitoring data.

EXAMPLE: Name and address fields for a user's account.

### user interface component

a part of the content that is perceived by users as a single control for a distinct function

NOTE 1: Multiple user interface components may be implemented as a single programmatic element. "Components" here is not tied to programming techniques, but rather to what the user perceives as separate controls.

NOTE 2: User interface components include form elements and links as well as components generated by scripts.

NOTE 3: What is meant by "component" or "user interface component" here is also sometimes called "user interface element".

EXAMPLE: An applet has a "control" that can be used to move through content by line or page or random access. Since each of these would need to have a name and be settable independently, they would each be a "user interface component."

### user inactivity

any continuous period of time where no user actions occur

The method of tracking will be determined by the website or application.

### video

the technology of moving or sequenced pictures or images

NOTE: Video can be made up of animated or photographic images, or both.

### video-only

a time-based presentation that contains only video (no audio and no interaction)

### viewport

object in which the user agent presents content

NOTE 1: The user agent presents content through one or more viewports. Viewports include windows, frames, loudspeakers, and virtual magnifying glasses. A viewport may contain another viewport (e.g., nested frames). Interface components created by the user agent such as prompts, menus, and alerts are not viewports.

NOTE 2: This definition is based on User Agent Accessibility Guidelines 1.0 Glossary [UAAG10].

### visually customized

the font, size, color, and background can be set

### web page

a non-embedded resource obtained from a single URI using HTTP plus any other resources that are used in the rendering or intended to be rendered together with it by a user agent

NOTE 1: Although any "other resources" would be rendered together with the primary resource, they would not necessarily be rendered simultaneously with each other.

NOTE 2: For the purposes of conformance with these guidelines, a resource must be "non-embedded" within the scope of conformance to be considered a web page.

EXAMPLE 1: A web resource including all embedded images and media.

EXAMPLE 2: A web mail program built using Asynchronous JavaScript and XML (AJAX). The program lives entirely at http://example.com/mail, but includes an inbox, a contacts area and a calendar. Links or buttons are provided that cause the inbox, contacts, or calendar to display, but do not change the URI of the page as a whole.

EXAMPLE 3: A customizable portal site, where users can choose content to display from a set of different content modules.

EXAMPLE 4: When you enter "http://shopping.example.com/" in your browser, you enter a movie-like interactive shopping environment where you visually move around in a store dragging products off of the shelves around you and into a visual shopping cart in front of you. Clicking on a product causes it to be demonstrated with a specification sheet floating alongside. This might be a single-page website or just one page within a website.

---

## Appendix (informative): Terms auditors confuse most

This appendix is not part of the specification. It exists because most disputed audit findings come from applying the everyday meaning of a word where WCAG uses a defined one.

**label vs. name.** A *label* is what every user sees or hears next to a control (visible text, an icon with a text alternative). A *name* is what software exposes to assistive technology (the accessible name, computed from `<label>`, `aria-label`, `aria-labelledby`, `alt`, text content, `title`). They are often identical, but 2.5.3 Label in Name exists precisely because they can diverge: a button whose visible label says "Search" but whose `aria-label` says "Submit query" fails. "Name" here has nothing to do with the HTML `name` attribute.

**captions vs. subtitles vs. transcript vs. audio description.** *Captions* are synchronized text for everything in the audio that matters: dialogue, speaker identification, sound effects, music cues. *Subtitles* (dialogue only, often a translation) do not satisfy 1.2.2 or 1.2.4 on their own. A *transcript* is an "alternative for time-based media": a document, not synchronized, that covers both the visual and auditory information; it satisfies 1.2.1 for audio-only and is an option in 1.2.3 and 1.2.8, but never substitutes for captions on synchronized media. *Audio description* is narration added to the soundtrack describing visuals that the audio does not already convey; if the dialogue already says everything the picture shows, no additional description is needed.

**change of context vs. change of content.** A *change of context* is one of four things: a new user agent (e.g., a new window), a new viewport, a moved focus, or content that changes the meaning of the page (e.g., navigating to another page or substantially re-arranging it). Expanding an accordion, opening a menu, switching a tab panel or showing an inline error is a change of *content*, which 3.2.1 and 3.2.2 do not restrict unless it also moves focus or does one of the other three things.

**set of web pages vs. process.** A *set of web pages* shares a common purpose, author and (in practice) template, which is what 2.4.5, 3.2.3, 3.2.4 and 3.2.6 are measured across. A *process* is a sequence of steps that must all be completed to achieve something (checkout, registration). Processes are exempt from 2.4.5 Multiple Ways, but every page in a process must conform for any page in it to conform (Conformance Requirement 5.2.3), and the pages of a checkout are typically not part of the product-page set.

**essential.** An exception for "essential" content is narrow: removing the feature would *fundamentally change* the information or functionality *and* there is no other conforming way to achieve it. "Our designer wants it this way" or "the brand guideline says so" is never essential. A piano app locked to landscape, a signature pad that needs path-based input, or a timed exam are the kinds of cases the exception was written for.

**accessibility supported vs. relied upon.** A technology is *relied upon* if turning it off would make the page non-conforming (HTML, CSS and JavaScript on almost every modern page). Everything relied upon must be used in an *accessibility-supported* way: supported by users' assistive technologies and by available, accessibility-supported user agents. A technology that is used but not relied upon (an optional 3D viewer with a conforming fallback) may be unsupported, provided it does not interfere (5.2.5).

**large scale text in CSS pixels.** WCAG defines large text in points: at least 18pt, or 14pt bold. At the CSS reference of 96 px per inch, 18pt ≈ 24px and 14pt ≈ 18.67px (commonly treated as 18.5px or 19px). So text at 24px regular or at least ~18.67px bold needs 3:1 under 1.4.3; everything smaller needs 4.5:1. Font size is the size as delivered, before any user zoom, and "bold" means a weight that the font renders as bold (700 for most families).

**status message vs. alert / change of context.** A *status message* informs the user about the outcome of an action, a waiting state, progress, or the existence of errors *without* being a change of context (it does not receive focus). "3 results found", "Saving…", "Added to cart" are status messages and must be exposed through a role or property (`role="status"`, `role="alert"`, `role="log"`, `aria-live`) under 4.1.3. An error dialog that takes focus, or a page that reloads, is a change of context and is outside 4.1.3 (it is judged under 3.2.x, 3.3.1 and 2.4.3 instead).
