# WCAG 2.3.1 — three flashes or below threshold

- **Source:** W3C, Web Content Accessibility Guidelines 2.2, Success Criterion 2.3.1 (Level A) and its defining terms.
- **URL:** https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold (Understanding document: https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold)
- **Checked:** 2026-10-14.

## The passage

"Web pages do not contain anything that flashes more than three times in any one second period, or the flash is below the general flash and red flash thresholds."

A [flash](https://www.w3.org/TR/WCAG22/#dfn-flashes) is "a pair of opposing changes in relative luminance that can cause seizures in some people if it is large enough and in the right frequency range". The [thresholds](https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds) are met where "there are no more than three general flashes and / or no more than three red flashes within any one-second period; or the combined area of flashes occurring concurrently occupies no more than a total of .006 steradians within any 10 degree visual field on the screen (25% of any 10 degree visual field on the screen) at typical viewing distance". A general flash is "a pair of opposing changes in relative luminance of 10% or more of the maximum relative luminance (1.0) where the relative luminance of the darker image is below 0.80". "A transition is the change in relative luminance (or relative luminance/color for red flashing) between adjacent peaks and valleys in a plot of relative luminance (or relative luminance/color for red flashing) measurement against time. A flash consists of two opposing transitions."

From the Understanding document: "The combined area of flashes occurring concurrently and contiguously means the total area that is actually flashing at the same time. It is calculated by adding up the contiguous area that is flashing simultaneously within any 10 degree angle of view." And: "Content should be analyzed at the largest scale at which a user may view the content … with a video that may play in an area of a web page and also at full screen, the video should be analyzed for risks at full screen."

## Where it is relied on

[Accessibility and perception](../../knowledge/Accessibility%20and%20perception.md) builds its flash QA proxy directly on these definitions: the cell grid, the 10% and 0.80 relative-luminance limits, the 25%-of-field rule, and the count of three flashes per second. It cites the three-flash rule as the simple way to meet the criterion. The W3C media guide's advisory to "avoid more than three flashes in any one-second period" (https://www.w3.org/WAI/media/av/av-content/) summarizes the same criterion.
