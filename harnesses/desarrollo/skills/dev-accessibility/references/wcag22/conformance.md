# WCAG 2.2 Conformance (Section 5) — complete, verbatim

Source: Web Content Accessibility Guidelines (WCAG) 2.2, W3C Recommendation 12 December 2024, https://www.w3.org/TR/WCAG22/#conformance. Sections 5.1–5.5 are **normative** and reproduced verbatim. Sections 5.6 and 5.7 are non-normative in the specification. The three glossary definitions that the conformance requirements depend on are copied verbatim after section 5.7. The final section, "Applying conformance in an audit", is informative guidance added for this skill.

---

## 5. Conformance

This section lists requirements for conformance to WCAG 2.2. It also gives information about how to make conformance claims, which are optional. Finally, it describes what it means to be accessibility supported, since only accessibility-supported ways of using technologies can be relied upon for conformance. Understanding Conformance includes further explanation of the accessibility-supported concept.

### 5.1 Interpreting Normative Requirements

The main content of WCAG 2.2 is normative and defines requirements that impact conformance claims. Introductory material, appendices, sections marked as "non-normative", diagrams, examples, and notes are informative (non-normative). Non-normative material provides advisory information to help interpret the guidelines but does not create requirements that impact a conformance claim.

The key words MAY, MUST, MUST NOT, NOT RECOMMENDED, RECOMMENDED, SHOULD, and SHOULD NOT are to be interpreted as described in [RFC2119].

### 5.2 Conformance Requirements

In order for a web page to conform to WCAG 2.2, all of the following conformance requirements must be satisfied:

#### 5.2.1 Conformance Level

One of the following levels of conformance is met in full.

- For Level A conformance (the minimum level of conformance), the web page satisfies all the Level A success criteria, or a conforming alternate version is provided.
- For Level AA conformance, the web page satisfies all the Level A and Level AA success criteria, or a Level AA conforming alternate version is provided.
- For Level AAA conformance, the web page satisfies all the Level A, Level AA and Level AAA success criteria, or a Level AAA conforming alternate version is provided.

NOTE 1: Although conformance can only be achieved at the stated levels, authors are encouraged to report (in their claim) any progress toward meeting success criteria from all levels beyond the achieved level of conformance.

NOTE 2: It is not recommended that Level AAA conformance be required as a general policy for entire sites because it is not possible to satisfy all Level AAA success criteria for some content.

#### 5.2.2 Full pages

Conformance (and conformance level) is for full web page(s) only, and cannot be achieved if part of a web page is excluded.

NOTE 1: For the purpose of determining conformance, alternatives to part of a page's content are considered part of the page when the alternatives can be obtained directly from the page, e.g., a long description or an alternative presentation of a video.

NOTE 2: Authors of web pages that cannot conform due to content outside of the author's control may consider a Statement of Partial Conformance.

NOTE 3: A full page includes each variation of the page that is automatically presented by the page for various screen sizes (e.g. variations in a responsive web page). Each of these variations needs to conform (or needs to have a conforming alternate version) in order for the entire page to conform.

#### 5.2.3 Complete processes

When a web page is one of a series of web pages presenting a process (i.e., a sequence of steps that need to be completed in order to accomplish an activity), all web pages in the process conform at the specified level or better. (Conformance is not possible at a particular level if any page in the process does not conform at that level or better.)

EXAMPLE: An online store has a series of pages that are used to select and purchase products. All pages in the series from start to finish (checkout) conform in order for any page that is part of the process to conform.

#### 5.2.4 Only Accessibility-Supported Ways of Using Technologies

Only accessibility-supported ways of using technologies are relied upon to satisfy the success criteria. Any information or functionality that is provided in a way that is not accessibility supported is also available in a way that is accessibility supported. (See Understanding accessibility support.)

#### 5.2.5 Non-Interference

If technologies are used in a way that is not accessibility supported, or if they are used in a non-conforming way, then they do not block the ability of users to access the rest of the page. In addition, the web page as a whole continues to meet the conformance requirements under each of the following conditions:

1. when any technology that is not relied upon is turned on in a user agent,
2. when any technology that is not relied upon is turned off in a user agent, and
3. when any technology that is not relied upon is not supported by a user agent

In addition, the following success criteria apply to all content on the page, including content that is not otherwise relied upon to meet conformance, because failure to meet them could interfere with any use of the page:

- 1.4.2 - Audio Control,
- 2.1.2 - No Keyboard Trap,
- 2.3.1 - Three Flashes or Below Threshold, and
- 2.2.2 - Pause, Stop, Hide.

NOTE: If a page cannot conform (for example, a conformance test page or an example page), it cannot be included in the scope of conformance or in a conformance claim.

For more information, including examples, see Understanding Conformance Requirements.

### 5.3 Conformance Claims (Optional)

Conformance is defined only for web pages. However, a conformance claim may be made to cover one page, a series of pages, or multiple related web pages.

#### 5.3.1 Required Components of a Conformance Claim

Conformance claims are not required. Authors can conform to WCAG 2.2 without making a claim. However, if a conformance claim is made, then the conformance claim must include the following information:

1. Date of the claim
2. Guidelines title, version and URI "Web Content Accessibility Guidelines 2.2 at https://www.w3.org/TR/WCAG22/"
3. Conformance level satisfied: (Level A, AA or AAA)
4. A concise description of the web pages, such as a list of URIs for which the claim is made, including whether subdomains are included in the claim.

   NOTE 1: The web pages may be described by list or by an expression that describes all of the URIs included in the claim.

   NOTE 2: Web-based products that do not have a URI prior to installation on the customer's website may have a statement that the product would conform when installed.

5. A list of the web content technologies relied upon.

NOTE 3: If a conformance logo is used, it would constitute a claim and must be accompanied by the required components of a conformance claim listed above.

#### 5.3.2 Optional Components of a Conformance Claim

In addition to the required components of a conformance claim above, consider providing additional information to assist users. Recommended additional information includes:

- A list of success criteria beyond the level of conformance claimed that have been met. This information should be provided in a form that users can use, preferably machine-readable metadata.
- A list of the specific technologies that are "used but not relied upon."
- A list of user agents, including assistive technologies that were used to test the content.
- A list of specific accessibility characteristics of the content, provided in machine-readable metadata.
- Information about any additional steps taken that go beyond the success criteria to enhance accessibility.
- A machine-readable metadata version of the list of specific technologies that are relied upon.
- A machine-readable metadata version of the conformance claim.

NOTE 1: Refer to Understanding Conformance Claims for more information and example conformance claims.

NOTE 2: Refer to Understanding Metadata for more information about the use of metadata in conformance claims.

### 5.4 Statement of Partial Conformance - Third Party Content

Web pages that will later have additional content added can use a 'statement of partial conformance'. For example, an email program, a blog, an article that allows users to add comments, or applications supporting user-contributed content. Another example would be a page, such as a portal or news site, composed of content aggregated from multiple contributors, or sites that automatically insert content from other sources over time, such as when advertisements are inserted dynamically.

In these cases, it is not possible to know at the time of original posting what the uncontrolled content of the pages will be. It is important to note that the uncontrolled content can affect the accessibility of the controlled content as well. Two options are available:

1. A determination of conformance can be made based on best knowledge. If a page of this type is monitored and repaired (non-conforming content is removed or brought into conformance) within two business days, then a determination or claim of conformance can be made since, except for errors in externally contributed content which are corrected or removed when encountered, the page conforms. No conformance claim can be made if it is not possible to monitor or correct non-conforming content;

   OR

2. A "statement of partial conformance" may be made that the page does not conform, but could conform if certain parts were removed. The form of that statement would be, "This page does not conform, but would conform to WCAG 2.2 at level X if the following parts from uncontrolled sources were removed." In addition, the following would also be true of uncontrolled content that is described in the statement of partial conformance:
   1. It is not content that is under the author's control.
   2. It is described in a way that users can identify (e.g., they cannot be described as "all parts that we do not control" unless they are clearly marked as such.)

### 5.5 Statement of Partial Conformance - Language

A "statement of partial conformance due to language" may be made when the page does not conform, but would conform if accessibility support existed for (all of) the language(s) used on the page. The form of that statement would be, "This page does not conform, but would conform to WCAG 2.2 at level X if accessibility support existed for the following language(s):"

### 5.6 Privacy Considerations

This section is non-normative.

Success criteria within this specification which the Working Group has identified possible implications for privacy, either by providing protections for end users or which are important for website providers to take in to consideration when implementing features designed to protect user privacy, are listed below. This list reflects the current understanding of the Working Group but other Success criteria may have privacy implications that the Working Group is not aware of at the time of publishing.

Success criteria within this specification that may relate to privacy are:

- 2.2.6 Timeouts (AAA)
- 3.3.7 Redundant Entry (A)

### 5.7 Security Considerations

This section is non-normative.

Success criteria within this specification which the Working Group has identified possible implications for security, either by providing protections for end users or which are important for website providers to take in to consideration when implementing features designed to protect user security, are listed below. This list reflects the current understanding of the Working Group but other Success criteria may have security implications that the Working Group is not aware of at the time of publishing.

Success criteria within this specification that may relate to security are:

- 1.1.1 Non-text Content (A)
- 1.3.5 Identify Input Purpose (AA)
- 1.4.7 Low or No Background Audio (AAA)
- 2.2.1 Timing Adjustable (A)
- 2.2.5 Re-authenticating (AAA)
- 2.2.6 Timeouts (AAA)
- 2.5.6 Concurrent Input Mechanisms (AAA)
- 3.3.3 Error Suggestion (AA)
- 3.3.7 Redundant Entry (A)
- 3.3.8 Accessible Authentication (Minimum) (AA)
- 3.3.9 Accessible Authentication (Enhanced) (AAA)

---

## Glossary definitions the conformance requirements depend on (verbatim, normative)

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

---

## Applying conformance in an audit (informative)

This section is not part of the specification. It translates the requirements above into decisions an auditor has to make.

### Scope: pages, variations and processes

Conformance is defined per web page, so the first job of an audit is to decide which pages are in scope and write that list down. For a site that cannot be tested exhaustively, choose a representative sample: the home page, each distinct template (article, listing, product, form, search results, error page), the pages with the most traffic, and pages that use unusual technologies (maps, charts, embedded video, PDF). State the sampling method in the report so a reader can judge what the result covers.

Two rules then expand the sample whether you like it or not. First, a *process* (5.2.3) is only as conformant as its weakest step: if the site offers registration, login, checkout, a benefits application or any other multi-step task, every page of that process must be tested at the target level, because a failure on step three makes the claim false for step one. Second, every *variation* of a page that the page itself presents for different screen sizes is part of the full page (5.2.2 NOTE 3). A responsive site must be checked at its breakpoints, including the narrow viewport that 1.4.10 Reflow demands (320 CSS px wide, equivalent to 1280 px at 400 % zoom); a hamburger menu that only exists on mobile is in scope just as much as the desktop navigation bar.

A page cannot be partially in scope. "The main content conforms but the footer is excluded" is not a valid result; the page either conforms or it does not. Alternatives that can be reached directly from the page (a transcript, a long description) count as part of the page when deciding whether it conforms.

### The four non-interference criteria

Even content that is not relied upon, such as a third-party widget with an accessible fallback, must not break the page for everyone. Check 1.4.2 Audio Control, 2.1.2 No Keyboard Trap, 2.2.2 Pause, Stop, Hide and 2.3.1 Three Flashes or Below Threshold on *all* content on the page, including advertising, embedded players and chat widgets. A single keyboard trap in an embedded iframe fails the whole page at Level A.

### Third-party and user-generated content

Content the author does not control (comments, ads, syndicated feeds, embedded social posts) does not get an automatic exemption. The author has two choices under 5.4: either monitor and repair non-conforming third-party content within two business days and claim conformance on that basis, or publish a statement of partial conformance that identifies, in a way users can recognise, exactly which parts are uncontrolled. "Everything we didn't write" is not an acceptable description. When auditing, report third-party failures separately from first-party ones, but still report them: they block conformance until one of the two options is taken. Note that a vendor's component the author chose to embed (a cookie banner, a booking engine, a video player) is normally content the author *does* control in the sense that matters: they chose it and can replace it, so it should be treated as first-party for conformance purposes.

### Choosing a target level

Level AA is the level that laws, regulations and procurement rules almost universally reference, and it is the level this skill audits against by default. The specification itself says that requiring AAA across an entire site is not recommended, because some AAA criteria cannot be met for some content (sign language for all prerecorded media, a lower-secondary reading level for legal text, no timing at all for a live auction). Report AAA criteria when the client asks for them or when they are cheap wins that significantly help users (2.4.8 Location, 2.4.10 Section Headings, 3.2.5 Change on Request, 2.3.3 Animation from Interactions via `prefers-reduced-motion`), and present them as progress beyond the claimed level, which 5.2.1 NOTE 1 explicitly encourages.

### Relationship to WCAG 2.0 and 2.1

WCAG 2.2 is backwards compatible: content that conforms to 2.2 also conforms to 2.0 and 2.1 at the same level, with one caveat. Success Criterion 4.1.1 Parsing has been removed from 2.2 (it is marked "Obsolete and removed" and has no level). If a policy or contract still mandates WCAG 2.0 or 2.1, you may need to continue testing and reporting 4.1.1 for that policy; in practice, treat it as always satisfied for HTML content and note in the report that it is obsolete. Conversely, content that conforms only to 2.1 may fail the nine criteria added in 2.2 (2.4.11, 2.4.12, 2.4.13, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8, 3.3.9), so a 2.1 AA badge does not imply 2.2 AA. The W3C's advice is to adopt 2.2 as the target even where obligations cite an earlier version, since 2.2 satisfies those obligations and anticipates future policy changes.

### Template conformance claim

A claim is optional, but if one is made (including by displaying a conformance logo) it must contain the five required components. The following skeleton covers them and the most useful optional ones:

```
Conformance claim

Date of claim: 2026-10-23
Guidelines: Web Content Accessibility Guidelines 2.2 at https://www.w3.org/TR/WCAG22/
Conformance level: Level AA
Scope: All pages under https://www.example.gob.ar/ and https://tramites.example.gob.ar/,
       excluding subdomains not listed. Pages are described by the expression
       https://www.example.gob.ar/** and https://tramites.example.gob.ar/**.
Technologies relied upon: HTML (Living Standard), CSS, JavaScript (ECMAScript 2023),
       WAI-ARIA 1.2, SVG 1.1, PDF 1.7 (ISO 32000-1).

Optional information
Technologies used but not relied upon: WebGL (3D map viewer; an accessible list view is provided).
Success criteria beyond Level AA that are met: 2.4.8 Location, 2.4.10 Section Headings,
       2.3.3 Animation from Interactions, 3.2.5 Change on Request.
User agents and assistive technologies used in testing: Chrome 141 + NVDA 2025.3 (Windows 11),
       Safari 26 + VoiceOver (macOS 26 and iOS 26), Firefox 144 + JAWS 2026, Android 16 + TalkBack.
Additional measures: Accessibility statement and feedback mechanism at /accesibilidad.
```

Where a page cannot conform because of uncontrolled content or a language without accessibility support, use the exact wording from 5.4 or 5.5 instead of a conformance claim:

- "This page does not conform, but would conform to WCAG 2.2 at level AA if the following parts from uncontrolled sources were removed: [identify the parts]."
- "This page does not conform, but would conform to WCAG 2.2 at level AA if accessibility support existed for the following language(s): [list]."
