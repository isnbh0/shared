---
name: design-feedback
description: >-
  Build and iterate a local HTML design gallery with per-frame comments, screenshot
  attachments, and portable feedback ZIPs. Use only when explicitly requested.
disable-model-invocation: true
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Create a self-contained HTML gallery for design calibration. When a gallery or exported
feedback already exists, inspect it and iterate in place. Use the output location the user
gave or the project's artifact convention. Keep the gallery exploratory: carry settled
decisions into a specification or implementation only when requested.

## Gallery

When the project has a UI or design tokens, inspect them before choosing colors, typography,
spacing, or controls, and use its existing design language. Include supported light and dark
appearances when relevant. Describe any deliberate departure as a proposed alternative.

Arrange labeled frames on a browsable board. Show useful layout alternatives and the states
that could change the decision: empty, first use, loading, content, failure, or settings.
Choose them for the task rather than filling a fixed inventory. Use representative content
and enough interaction to assess the flow. Keep simulated actions local.

Add a left-hand sidebar for navigation. List the general comments, the open questions, every
frame by title and ID in board order, and any kept feedback for removed frames. Keep it visible
while the board scrolls, highlight the section in view, and mark entries that have feedback.
Land each jump below any sticky header. On narrow viewports, place the list above the board.

Write plain, descriptive copy. Omit slogans, metaphors, eyebrow headings, and explanations
of obvious controls. Use familiar compact controls with accessible names. Keep gallery
controls and feedback fields outside the product frames so they do not distort the design.

Give each frame a stable ID and a short title. Preserve IDs across iterations even when
titles or positions change. Use a gallery ID and revision to identify the reviewed version.

## Feedback

Provide a comment field for each frame and a general comment field. Let the user attach
screenshots to either by file selection, drag-and-drop, and paste. Show image previews and
allow removal. Keep attachments associated with their frame IDs, not their display order.

Export one ZIP containing readable `feedback.txt`, structured `feedback.json`, and the
original image files. The JSON records the gallery ID, revision, comments, and attachment
paths with their frame IDs, original filenames, and media types. Use unique archive paths
so duplicate filenames cannot overwrite each other.

Support importing that ZIP to resume a review. Preserve comments and image associations.
When revising an existing gallery, preserve import support for its prior feedback exports.
Keep feedback for removed frames accessible instead of dropping it. Parse and validate an import
before replacing current feedback; render imported strings as text. Show import/export
failures and retain current work on failure.

Keep the gallery usable offline, including ZIP support. If bundling a library, retain its
license. State whether reload preserves comments and attachments; show an export reminder
when it does not.

## Iteration and checks

Read exported comments and inspect their attached screenshots before changing the gallery.
Apply clear requests; identify unresolved design choices without treating mockups as approved
implementation requirements. List those choices in the gallery's open-questions section and
replace the list each revision. Preserve the feedback workflow through each revision.

Check the rendered frames at relevant sizes and appearances. Verify comment entry, screenshot
attachment and removal, ZIP export, and import into a fresh page. Confirm text, image bytes,
and frame associations survive the round trip. Check that malformed imports leave existing
work intact. Verify that each sidebar entry reaches its section and that the highlight follows
scrolling. Keep copies of the user's exported ZIPs alongside the gallery's checks, so later
revisions still prove they import. Use headless checks where available and follow the
project's conventions for opening UI.

Return a link to the gallery and a short account of the changes. Ask for the next design
judgment only when a concrete choice remains.
